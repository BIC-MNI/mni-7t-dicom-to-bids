from copy import deepcopy
from importlib.metadata import version
from pathlib import Path

from bic_util.bids.dataset_description import (
    get_generated_by,
    read_dataset_description,
    upsert_generated_by_entry,
    write_dataset_description,
)

from mni_7t_dicom_to_bids.dataclass import BidsDatasetInfo


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


def patch_derivative_dataset_description(bids_dataset_path: Path, dataset: BidsDatasetInfo):
    """Create or patch the description of a named derivative dataset."""

    if not dataset.is_derivative or dataset.dataset_description is None:
        raise ValueError('Expected a derivative BIDS dataset with a dataset description template.')

    derivative_path = bids_dataset_path / 'derivatives' / dataset.name
    derivative_path.mkdir(parents=True, exist_ok=True)
    dataset_description_path = derivative_path / 'dataset_description.json'

    if dataset_description_path.exists():
        print(f"Patching 'derivatives/{dataset.name}/dataset_description.json'...")
        dataset_description = read_dataset_description(dataset_description_path)
    else:
        print(f"Creating 'derivatives/{dataset.name}/dataset_description.json'...")
        dataset_description = deepcopy(dataset.dataset_description)

    dataset_description['GeneratedBy'] = _patch_derivative_generated_by(
        dataset_description.get('GeneratedBy'),
        dataset.dataset_description['GeneratedBy'],
    )
    write_dataset_description(dataset_description_path, dataset_description)


def _patch_derivative_generated_by(value: object | None, template_value: object) -> list[object]:
    """Keep the template's derivative generator first and add converter provenance."""

    generated_by = get_generated_by(value)
    template_generated_by = get_generated_by(template_value)
    template_generator = deepcopy(template_generated_by[0])
    template_name = template_generator.get('Name')

    for index, entry in enumerate(generated_by):
        if entry.get('Name') == template_name:
            template_generator.update(entry)
            generated_by.pop(index)
            break

    generated_by.insert(0, template_generator)
    return _patch_generated_by(generated_by)


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
