import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from re import Pattern
from typing import cast

import json5

from mni_7t_dicom_to_bids.dataclass import RAW_BIDS_DATASET, BidsDatasetInfo, Citation, SequenceCredit

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
    sidecar: dict[str, object] = field(default_factory=dict[str, object])
    credit: SequenceCredit | None = None


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
    _require_properties(
        root, {'ignored-series', 'trim-series-suffixes', 'mappings'}, 'dictionary', {'references', 'derivatives'}
    )

    ignored_values = _require_array(root['ignored-series'], 'ignored-series')
    suffix_values = _require_array(root['trim-series-suffixes'], 'trim-series-suffixes')
    mapping_values = _require_array(root['mappings'], 'mappings')
    reference_values = _require_object(root.get('references', {}), 'references')
    derivative_values = _require_object(root.get('derivatives', {}), 'derivatives')
    references: dict[str, Citation] = {}
    for name, definition in reference_values.items():
        _require_string(name, 'reference definition name')
        references[name] = _parse_citation(definition, f'references.{name}')

    derivative_definitions: dict[str, BidsDatasetInfo] = {}
    derivatives: dict[str, dict[str, object]] = {}
    for name, definition in derivative_values.items():
        _require_string(name, 'derivative definition name')
        location = f'derivatives.{name}'
        # Definitions must describe a derivative, rather than an alias or raw dataset.
        _require_object(definition, location)
        dataset = _load_derivative(definition, location, read_template)
        _check_derivative_consistency(dataset, derivatives, location)
        derivative_definitions[name] = dataset

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
    for index, value in enumerate(mapping_values):
        location = f'mappings[{index}]'
        mapping = _require_object(value, location)
        _require_properties(
            mapping, {'series', 'datatype', 'filename'}, location, {'merge-images', 'derivative', 'sidecar', 'credit'}
        )
        series = _require_string(mapping['series'], f'{location}.series')
        datatype = _require_string(mapping['datatype'], f'{location}.datatype')
        filename = _require_string(mapping['filename'], f'{location}.filename')
        merge_images = _require_bool(mapping.get('merge-images', False), f'{location}.merge-images')
        sidecar = _require_object(mapping.get('sidecar', {}), f'{location}.sidecar')
        credit = _parse_credit(mapping.get('credit'), f'{location}.credit', references)
        try:
            json.dumps(sidecar, allow_nan=False)
        except (TypeError, ValueError) as error:
            raise DicomDictionaryError(f'{location}.sidecar must contain valid JSON values: {error}') from error
        derivative = mapping.get('derivative')
        if isinstance(derivative, str):
            if derivative not in derivative_definitions:
                raise DicomDictionaryError(f"{location}.derivative uses undefined derivative '{derivative}'.")
            dataset = derivative_definitions[derivative]
        else:
            dataset = _load_derivative(derivative, f'{location}.derivative', read_template)
        _check_derivative_consistency(dataset, derivatives, f'{location}.derivative')
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
            sidecar,
            credit,
        ))

    return DicomDictionary(ignored_patterns, suffixes, mappings)


def _parse_credit(
    value: object,
    location: str,
    definitions: dict[str, Citation] | None = None,
) -> SequenceCredit | None:
    if value is None:
        return None
    credit = _require_object(value, location)
    _require_properties(credit, {'acknowledgement'}, location, {'references'})
    acknowledgement = _require_string(credit['acknowledgement'], f'{location}.acknowledgement')
    references = _require_array(credit.get('references', []), f'{location}.references')
    citations: dict[str, Citation] = {}
    for index, reference in enumerate(references):
        reference_location = f'{location}.references[{index}]'
        if isinstance(reference, str):
            if definitions is None or reference not in definitions:
                raise DicomDictionaryError(f"{reference_location} uses undefined reference '{reference}'.")
            citation = definitions[reference]
        else:
            citation = _parse_citation(reference, reference_location)
        citations.setdefault(citation.url, citation)
    return SequenceCredit(acknowledgement, tuple(citations.values()))


def _parse_citation(value: object, location: str) -> Citation:
    citation = _require_object(value, location)
    _require_properties(citation, {'text', 'url'}, location)
    citation_text = _require_string(citation['text'], f'{location}.text')
    url = _require_string(citation['url'], f'{location}.url')
    if re.fullmatch(r'https?://[^\s/]+(?:/[^\s]*)?', url) is None:
        raise DicomDictionaryError(f'{location}.url must be an HTTP(S) URL.')
    return Citation(citation_text, url)


def _check_derivative_consistency(
    dataset: BidsDatasetInfo,
    derivatives: dict[str, dict[str, object]],
    location: str,
):
    if dataset.is_derivative:
        existing_template = derivatives.setdefault(dataset.name, dataset.dataset_description or {})
        if existing_template != dataset.dataset_description:
            raise DicomDictionaryError(
                f"{location} conflicts with another definition of derivative '{dataset.name}'."
            )


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
    generated_by = _require_array(
        template.get('GeneratedBy'),
        f"GeneratedBy in dataset description template '{template_source}'",
    )
    if not generated_by:
        raise DicomDictionaryError(
            f"GeneratedBy in dataset description template '{template_source}' must be a non-empty array of objects."
        )
    for index, value in enumerate(generated_by):
        generator = _require_object(
            value,
            f"GeneratedBy[{index}] in dataset description template '{template_source}'",
        )
        _require_string(
            generator.get('Name'),
            f"GeneratedBy[{index}].Name in dataset description template '{template_source}'",
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
