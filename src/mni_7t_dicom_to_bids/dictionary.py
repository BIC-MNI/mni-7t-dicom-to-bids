import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from importlib.abc import Traversable
from importlib.resources import files
from pathlib import Path
from re import Pattern
from typing import cast

import json5

from mni_7t_dicom_to_bids.dataclass import RAW_BIDS_DATASET, BidsDatasetInfo

SUPPORTED_DATATYPES = {'anat', 'dwi', 'fmap', 'func'}


class DicomDictionaryError(ValueError):
    """
    Error raised when a DICOM dictionary cannot be loaded safely.
    """


@dataclass(frozen=True)
class SeriesMapping:
    series: str
    series_regex: Pattern[str]
    datatype: str
    filename: str
    merge_images: bool
    dataset: BidsDatasetInfo


@dataclass(frozen=True)
class DicomDictionary:
    ignored_series: list[Pattern[str]]
    trim_series_suffixes: list[str]
    mappings: list[SeriesMapping]


def load_dicom_dictionary(file_path: Path | None = None) -> DicomDictionary:
    """
    Load a user-provided DICOM dictionary, or the packaged default when no path is provided.
    """

    if file_path is None:
        resource = files('mni_7t_dicom_to_bids').joinpath('assets/dictionary.json5')
        try:
            with resource.open(encoding='utf-8') as file:
                value: object = json5.load(file, allow_duplicate_keys=False)  # pyright: ignore[reportUnknownMemberType]
        except (OSError, ValueError) as error:
            raise DicomDictionaryError(f"Cannot read valid JSON5 from dictionary '{resource}': {error}") from error

        asset_root = files('mni_7t_dicom_to_bids').joinpath('assets')
        return _parse_dicom_dictionary(
            value,
            lambda path: _read_package_template(asset_root.joinpath(path)),
        )
    return _load_dicom_dictionary(file_path)


def _load_dicom_dictionary(file_path: Path) -> DicomDictionary:
    try:
        with file_path.open(encoding='utf-8') as file:
            value: object = json5.load(file, allow_duplicate_keys=False)  # pyright: ignore[reportUnknownMemberType]
    except (OSError, ValueError) as error:
        raise DicomDictionaryError(f"Cannot read valid JSON5 from dictionary '{file_path}': {error}") from error

    return _parse_dicom_dictionary(
        value,
        lambda path: _read_file_template(Path(path) if Path(path).is_absolute() else file_path.parent / path),
    )


def _parse_dicom_dictionary(
    value: object,
    read_template: Callable[[str], tuple[object, str]],
) -> DicomDictionary:
    root = _require_object(value, 'dictionary')
    _require_properties(root, {'ignored-series', 'trim-series-suffixes', 'mappings'}, 'dictionary')

    ignored_values = _require_array(root['ignored-series'], 'ignored-series')
    suffix_values = _require_array(root['trim-series-suffixes'], 'trim-series-suffixes')
    mapping_values = _require_array(root['mappings'], 'mappings')

    ignored_patterns: list[Pattern[str]] = []
    ignored_strings: set[str] = set()
    for index, value in enumerate(ignored_values):
        location = f'ignored-series[{index}]'
        pattern = _require_string(value, location)
        _require_unique(pattern, ignored_strings, location)
        ignored_patterns.append(_compile_regex(pattern, location))

    suffixes: list[str] = []
    suffix_set: set[str] = set()
    for index, value in enumerate(suffix_values):
        location = f'trim-series-suffixes[{index}]'
        suffix = _require_string(value, location)
        _require_unique(suffix, suffix_set, location)
        suffixes.append(suffix)

    mappings: list[SeriesMapping] = []
    mapping_patterns: set[str] = set()
    derivatives: dict[str, dict[str, object]] = {}
    for index, value in enumerate(mapping_values):
        location = f'mappings[{index}]'
        mapping = _require_object(value, location)
        _require_properties(mapping, {'series', 'datatype', 'filename'}, location, {'merge-images', 'derivative'})
        series = _require_string(mapping['series'], f'{location}.series')
        datatype = _require_string(mapping['datatype'], f'{location}.datatype')
        filename = _require_string(mapping['filename'], f'{location}.filename')
        merge_images = _require_bool(mapping.get('merge-images', False), f'{location}.merge-images')
        dataset = _load_derivative(mapping.get('derivative'), f'{location}.derivative', read_template)
        if dataset.is_derivative:
            existing_template = derivatives.setdefault(dataset.name, dataset.dataset_description or {})
            if existing_template != dataset.dataset_description:
                raise DicomDictionaryError(
                    f"{location}.derivative conflicts with another definition of derivative '{dataset.name}'."
                )
        _require_unique(series, mapping_patterns, f'{location}.series')

        if datatype not in SUPPORTED_DATATYPES:
            raise DicomDictionaryError(
                f"{location}.datatype must be one of {sorted(SUPPORTED_DATATYPES)}, found '{datatype}'."
            )
        if re.fullmatch(r'[A-Za-z0-9_-]+', filename) is None:
            raise DicomDictionaryError(f"{location}.filename is not a valid BIDS basename: '{filename}'.")

        mappings.append(SeriesMapping(
            series,
            _compile_regex(series, f'{location}.series'),
            datatype,
            filename,
            merge_images,
            dataset,
        ))

    return DicomDictionary(ignored_patterns, suffixes, mappings)


def _load_derivative(
    value: object | None,
    location: str,
    read_template: Callable[[str], tuple[object, str]],
) -> BidsDatasetInfo:
    if value is None:
        return RAW_BIDS_DATASET

    derivative = _require_object(value, location)
    _require_properties(derivative, {'name', 'dataset-description'}, location)
    name = _require_string(derivative['name'], f'{location}.name')
    template_path = _require_string(derivative['dataset-description'], f'{location}.dataset-description')

    if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*', name) is None:
        raise DicomDictionaryError(f"{location}.name is not a valid derivative dataset name: '{name}'.")

    template_value, template_source = read_template(template_path)
    template = _require_object(template_value, f"dataset description template '{template_source}'")
    if template.get('DatasetType') != 'derivative':
        raise DicomDictionaryError(
            f"DatasetType in dataset description template '{template_source}' must be 'derivative'."
        )
    generated_by = template.get('GeneratedBy')
    if not isinstance(generated_by, list) or not generated_by or not isinstance(generated_by[0], dict):
        raise DicomDictionaryError(
            f"GeneratedBy in dataset description template '{template_source}' must be a non-empty array of objects."
        )
    first_generated_by = cast(dict[object, object], generated_by[0])
    generated_by_name = first_generated_by.get('Name')
    if not isinstance(generated_by_name, str) or generated_by_name not in name:
        raise DicomDictionaryError(
            f"The first GeneratedBy.Name in dataset description template '{template_source}' must be a substring"
            f" of derivative name '{name}'."
        )

    return BidsDatasetInfo(name, template)


def _read_file_template(file_path: Path) -> tuple[object, str]:
    try:
        with file_path.open(encoding='utf-8') as file:
            return json.load(file), str(file_path)
    except (OSError, json.JSONDecodeError) as error:
        raise DicomDictionaryError(
            f"Cannot read valid JSON from dataset description template '{file_path}': {error}"
        ) from error


def _read_package_template(resource: Traversable) -> tuple[object, str]:
    # `Traversable` is intentionally consumed immediately: packaged assets need not have stable paths.
    try:
        with resource.open(encoding='utf-8') as file:
            return json.load(file), str(resource)
    except (OSError, json.JSONDecodeError) as error:
        raise DicomDictionaryError(
            f"Cannot read valid JSON from dataset description template '{resource}': {error}"
        ) from error


def _require_object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise DicomDictionaryError(f'{location} must be an object.')
    return cast(dict[str, object], value)


def _require_array(value: object, location: str) -> list[object]:
    if not isinstance(value, list):
        raise DicomDictionaryError(f'{location} must be an array.')
    return cast(list[object], value)


def _require_string(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise DicomDictionaryError(f'{location} must be a non-empty string.')
    return value


def _require_bool(value: object, location: str) -> bool:
    if not isinstance(value, bool):
        raise DicomDictionaryError(f'{location} must be a boolean.')
    return value


def _require_properties(
    value: dict[str, object],
    required: set[str],
    location: str,
    optional: set[str] | None = None,
):
    optional = optional or set()
    properties = set(value)
    allowed = required | optional
    if not required <= properties or not properties <= allowed:
        missing = sorted(required - properties)
        unknown = sorted(properties - allowed)
        details: list[str] = []
        if missing:
            details.append(f'missing {missing}')
        if unknown:
            details.append(f'unknown {unknown}')
        raise DicomDictionaryError(f"{location} has invalid properties: {', '.join(details)}.")


def _require_unique(value: str, seen: set[str], location: str):
    if value in seen:
        raise DicomDictionaryError(f"{location} duplicates value '{value}'.")
    seen.add(value)


def _compile_regex(value: str, location: str) -> Pattern[str]:
    try:
        return re.compile(value)
    except re.error as error:
        raise DicomDictionaryError(f"{location} is not a valid regular expression: {error}.") from error
