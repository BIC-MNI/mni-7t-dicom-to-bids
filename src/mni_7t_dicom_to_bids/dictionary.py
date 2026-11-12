import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from re import Pattern

import json5
from pydantic import ValidationError

from mni_7t_dicom_to_bids.dataclass import RAW_BIDS_DATASET, BidsDatasetInfo, Citation, SequenceCredit
from mni_7t_dicom_to_bids.dictionary_config import (
    CreditConfig,
    DatasetDescriptionConfig,
    DerivativeConfig,
    DictionaryConfig,
)


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
    try:
        config = DictionaryConfig.model_validate(value)
    except ValidationError as error:
        raise _configuration_error(error, 'dictionary') from error

    references = {name: Citation(citation.text, citation.url) for name, citation in config.references.items()}
    derivatives: dict[str, dict[str, object]] = {}
    derivative_definitions: dict[str, BidsDatasetInfo] = {}
    for name, definition in config.derivatives.items():
        location = f'derivatives.{name}'
        dataset = _load_derivative(definition, location, read_template)
        _check_derivative_consistency(dataset, derivatives, location)
        derivative_definitions[name] = dataset

    ignored_patterns: list[Pattern[str]] = []
    ignored_strings: set[str] = set()
    for index, pattern in enumerate(config.ignored_series):
        location = f'ignored-series[{index}]'
        _require_unique(pattern, ignored_strings, location)
        ignored_patterns.append(_compile_regex(pattern, location))

    suffixes: set[str] = set()
    for index, suffix in enumerate(config.trim_series_suffixes):
        _require_unique(suffix, suffixes, f'trim-series-suffixes[{index}]')

    mappings: list[SeriesMapping] = []
    mapping_patterns: set[str] = set()
    for index, mapping in enumerate(config.mappings):
        location = f'mappings[{index}]'
        derivative = mapping.derivative
        if isinstance(derivative, str):
            if derivative not in derivative_definitions:
                raise DicomDictionaryError(f"{location}.derivative uses undefined derivative '{derivative}'.")
            dataset = derivative_definitions[derivative]
        else:
            dataset = _load_derivative(derivative, f'{location}.derivative', read_template)
        _check_derivative_consistency(dataset, derivatives, f'{location}.derivative')
        _require_unique(mapping.series, mapping_patterns, f'{location}.series')

        mappings.append(SeriesMapping(
            series=mapping.series,
            series_regex=_compile_regex(mapping.series, f'{location}.series'),
            datatype=mapping.datatype,
            filename=mapping.filename,
            merge_images=mapping.merge_images,
            dataset=dataset,
            sidecar=dict(mapping.sidecar),
            credit=_resolve_credit(mapping.credit, f'{location}.credit', references),
        ))

    return DicomDictionary(ignored_patterns, config.trim_series_suffixes, mappings)


def _resolve_credit(
    credit: CreditConfig | None,
    location: str,
    definitions: dict[str, Citation],
) -> SequenceCredit | None:
    if credit is None:
        return None
    citations: dict[str, Citation] = {}
    for index, reference in enumerate(credit.references):
        if isinstance(reference, str):
            if reference not in definitions:
                raise DicomDictionaryError(f"{location}.references[{index}] uses undefined reference '{reference}'.")
            citation = definitions[reference]
        else:
            citation = Citation(reference.text, reference.url)
        citations.setdefault(citation.url, citation)
    return SequenceCredit(credit.acknowledgement, tuple(citations.values()))


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
    derivative: DerivativeConfig | None,
    location: str,
    read_template: Callable[[str], tuple[object, str]],
) -> BidsDatasetInfo:
    if derivative is None:
        return RAW_BIDS_DATASET

    template_value, template_source = read_template(derivative.dataset_description)
    try:
        template = DatasetDescriptionConfig.model_validate(template_value)
    except ValidationError as error:
        raise _configuration_error(error, f"{location}: dataset description template '{template_source}'") from error
    return BidsDatasetInfo(derivative.name, template.model_dump(by_alias=True))


def _configuration_error(error: ValidationError, source: str) -> DicomDictionaryError:
    """Keep validation errors readable at the CLI, including array indices."""
    messages: list[str] = []
    for detail in error.errors(include_url=False):
        location = ''
        for part in detail['loc']:
            if isinstance(part, int):
                location += f'[{part}]'
            else:
                location += f'.{part}' if location else part
        messages.append(f"{location or source}: {detail['msg']}")
    return DicomDictionaryError(f"Invalid {source}:\n" + '\n'.join(messages))


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


def _require_unique(value: str, seen: set[str], location: str):
    if value in seen:
        raise DicomDictionaryError(f"{location} duplicates value '{value}'.")
    seen.add(value)


def _compile_regex(value: str, location: str) -> Pattern[str]:
    try:
        return re.compile(value)
    except re.error as error:
        raise DicomDictionaryError(f"{location} is not a valid regular expression: {error}.") from error
