import json
from importlib.metadata import version
from pathlib import Path
from typing import cast

from bic_util.util import find_index

BIDS_VERSION = '1.11.1'


class DatasetDescriptionError(ValueError):
    """
    Error raised when `dataset_description.json` cannot be safely patched.
    """


def patch_dataset_description(bids_dataset_path: Path):
    """
    Patch an existing `dataset_description.json` with the BIDS version and conversion
    software provenance.

    Do nothing if the file does not exist and preserve metadata not managed by the converter.
    """

    dataset_description_path = bids_dataset_path / 'dataset_description.json'
    if not dataset_description_path.exists():
        return

    print("Patching 'dataset_description.json'...")

    dataset_description = _read_dataset_description(dataset_description_path)
    dataset_description['BIDSVersion'] = BIDS_VERSION
    dataset_description['GeneratedBy'] = _patch_generated_by(dataset_description.get('GeneratedBy'))

    try:
        with dataset_description_path.open('w', encoding='utf-8') as file:
            json.dump(dataset_description, file, indent=4, ensure_ascii=False)
            file.write('\n')
    except OSError as error:
        raise DatasetDescriptionError(f"Cannot write '{dataset_description_path}': {error}") from error


def _read_dataset_description(file_path: Path) -> dict[str, object]:
    """
    Read and validate the structure of `dataset_description.json`.
    """

    try:
        with file_path.open(encoding='utf-8') as file:
            value: object = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise DatasetDescriptionError(f"Cannot read valid JSON from '{file_path}': {error}") from error

    if not isinstance(value, dict):
        raise DatasetDescriptionError(f"Expected the root of '{file_path}' to be a JSON object.")

    return cast(dict[str, object], value)


def _patch_generated_by(value: object | None) -> list[object]:
    """
    Add or update converter-managed entries in a `GeneratedBy` array.
    """

    if value is None:
        generated_by: list[object] = []
    elif isinstance(value, list):
        generated_by = cast(list[object], value)
    else:
        raise DatasetDescriptionError("Expected 'GeneratedBy' in 'dataset_description.json' to be an array.")

    validated_entries: list[dict[str, object]] = []
    for entry in generated_by:
        if not isinstance(entry, dict):
            raise DatasetDescriptionError(
                "Expected every entry in 'GeneratedBy' in 'dataset_description.json' to be an object."
            )
        validated_entries.append(cast(dict[str, object], entry))

    _patch_generated_by_entry(
        validated_entries,
        name='mni_7t_dicom_to_bids',
        software_version=version('mni_7t_dicom_to_bids'),
        code_url='https://github.com/bic-mni/mni-7t-dicom-to-bids',
    )
    _patch_generated_by_entry(
        validated_entries,
        name='dcm2niix',
        software_version=version('dcm2niix'),
        code_url='https://github.com/rordenlab/dcm2niix',
    )

    return cast(list[object], validated_entries)


def _patch_generated_by_entry(
    generated_by: list[dict[str, object]],
    name: str,
    software_version: str,
    code_url: str,
):
    """
    Add or update one converter-managed entry.
    """

    entry_index = find_index(lambda entry: entry.get('Name') == name, generated_by)
    managed_values: dict[str, object] = {
        'Name': name,
        'Version': software_version,
        'CodeURL': code_url,
    }

    if entry_index is None:
        generated_by.append(managed_values)
        return

    generated_by[entry_index].update(managed_values)
