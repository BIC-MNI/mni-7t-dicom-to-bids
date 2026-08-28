from importlib.metadata import version
from pathlib import Path

from bic_util.bids.dataset_description import (
    get_generated_by,
    read_dataset_description,
    upsert_generated_by_entry,
    write_dataset_description,
)


def patch_dataset_description(bids_dataset_path: Path):
    """
    Create or patch `dataset_description.json` with the BIDS version and conversion provenance.

    A newly created file describes a raw dataset and uses a generic name. When patching an existing
    file, preserve metadata not managed by the converter and do not infer its dataset type.
    """

    dataset_description_path = bids_dataset_path / 'dataset_description.json'
    dataset_description: dict[str, object]
    if dataset_description_path.exists():
        print("Patching 'dataset_description.json'...")
        dataset_description = read_dataset_description(dataset_description_path)
    else:
        print("File 'dataset_description.json' does not exist in the BIDS directory. Creating...")
        dataset_description = {
            'Name': 'MNI 7T BIDS dataset',
            'BIDSVersion': '1.11.1',
            'DatasetType': 'raw',
        }

    dataset_description['GeneratedBy'] = _patch_generated_by(dataset_description.get('GeneratedBy'))

    write_dataset_description(dataset_description_path, dataset_description)


def _patch_generated_by(value: object | None) -> list[object]:
    """
    Add or update converter-managed entries in a `GeneratedBy` array.
    """

    validated_entries = get_generated_by(value)

    _patch_generated_by_entry(
        validated_entries,
        name='mni-7t-dicom-to-bids',
        software_version=version('mni-7t-dicom-to-bids'),
        code_url='https://github.com/bic-mni/mni-7t-dicom-to-bids',
    )
    _patch_generated_by_entry(
        validated_entries,
        name='dcm2niix',
        software_version=version('dcm2niix'),
        code_url='https://github.com/rordenlab/dcm2niix',
    )

    return list(validated_entries)


def _patch_generated_by_entry(
    generated_by: list[dict[str, object]],
    name: str,
    software_version: str,
    code_url: str,
):
    """
    Add or update one converter-managed entry.
    """

    managed_values: dict[str, object] = {
        'Name': name,
        'Version': software_version,
        'CodeURL': code_url,
    }

    upsert_generated_by_entry(generated_by, managed_values)
