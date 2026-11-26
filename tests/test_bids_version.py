import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from bic_util.bids.dataset_description import DatasetDescriptionError

from mni_7t_dicom_to_bids.args import Args, SkipErrorsArg, SkipUnknownsArg
from mni_7t_dicom_to_bids.dataclass import DicomSeriesInfo
from mni_7t_dicom_to_bids.dictionary import load_dicom_dictionary
from mni_7t_dicom_to_bids.metadata.dataset_description import (
    patch_dataset_description,
    patch_derivative_dataset_description,
    read_or_create_dataset_description,
)
from mni_7t_dicom_to_bids.pipeline import mni_7t_dicom_to_bids


@pytest.mark.parametrize('existing', [None, {'Name': 'Existing'}, {'Name': 'Existing', 'BIDSVersion': '1.10.0'}])
def test_description_uses_dictionary_version_and_preserves_metadata(tmp_path: Path, existing: dict[str, str] | None):
    path = tmp_path / 'dataset_description.json'
    if existing is not None:
        path.write_text(json.dumps(existing))
    read_or_create_dataset_description(tmp_path, '1.10.0')
    patch_dataset_description(tmp_path, '1.10.0')
    description = json.loads(path.read_text())
    assert description['BIDSVersion'] == '1.10.0'
    if existing is not None:
        assert description['Name'] == 'Existing'
    first = path.read_text()
    patch_dataset_description(tmp_path, '1.10.0')
    assert path.read_text() == first


def test_derivative_description_uses_dictionary_version(tmp_path: Path):
    dictionary = load_dicom_dictionary()
    dataset = next(mapping.dataset for mapping in dictionary.mappings if mapping.dataset.is_derivative)
    patch_derivative_dataset_description(tmp_path, dataset, dictionary.bids_version)
    path = tmp_path / 'derivatives' / dataset.name / 'dataset_description.json'
    description = json.loads(path.read_text())
    assert description['BIDSVersion'] == dictionary.bids_version
    description['Name'] = 'Existing derivative'
    path.write_text(json.dumps(description))
    patch_derivative_dataset_description(tmp_path, dataset, dictionary.bids_version)
    assert json.loads(path.read_text())['Name'] == 'Existing derivative'


@pytest.mark.parametrize('source', ['raw', 'derivative', 'template'])
def test_pipeline_rejects_version_conflict_before_conversion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str
):
    root = tmp_path / 'bids'
    description_path = root / 'dataset_description.json'
    if source == 'derivative':
        description_path = root / 'derivatives/aspire/dataset_description.json'
    description_path.parent.mkdir(parents=True)
    if source == 'template':
        dictionary = replace(load_dicom_dictionary(), bids_version='1.10.0')
        monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.load_dicom_dictionary', Mock(return_value=dictionary))
    else:
        description_path.write_text(json.dumps({'BIDSVersion': '1.10.0'}))
    original = description_path.read_text() if description_path.exists() else None
    original_paths = sorted(root.rglob('*'))
    sources = [DicomSeriesInfo('EchoCombined_anat-T2star_acq-me_gre_0.7iso_ASPIRE', 1, [])]
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.check_dicom_to_niix', lambda: None)
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.group_dicom_series', Mock(return_value=sources))

    def unexpected_conversion(*args: object):
        pytest.fail('Conversion started despite a conflicting BIDS version')

    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.convert_dicom_series', unexpected_conversion)
    args = Args(tmp_path, root, '01', '01', None, SkipUnknownsArg(), SkipErrorsArg(), False, False)
    with pytest.raises(DatasetDescriptionError, match=r'declares BIDSVersion.*dictionary targets'):
        mni_7t_dicom_to_bids(args)
    if original is not None:
        assert description_path.read_text() == original
    assert sorted(root.rglob('*')) == original_paths


def test_existing_description_takes_precedence_over_template(tmp_path: Path):
    dictionary = load_dicom_dictionary()
    dataset = next(mapping.dataset for mapping in dictionary.mappings if mapping.dataset.is_derivative)
    path = tmp_path / 'derivatives' / dataset.name / 'dataset_description.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'Name': 'Existing', 'BIDSVersion': '1.10.0'}))
    patch_derivative_dataset_description(tmp_path, dataset, '1.10.0')
    description = json.loads(path.read_text())
    assert description['BIDSVersion'] == '1.10.0'
    assert description['Name'] == 'Existing'
    assert dataset.dataset_description is not None
    assert dataset.dataset_description['BIDSVersion'] == dictionary.bids_version


@pytest.mark.parametrize('derivative', [False, True])
def test_patching_rejects_conflicts_without_overwriting_description(tmp_path: Path, derivative: bool):
    dictionary = load_dicom_dictionary()
    dataset = next(mapping.dataset for mapping in dictionary.mappings if mapping.dataset.is_derivative)
    root = tmp_path / 'derivatives' / dataset.name if derivative else tmp_path
    root.mkdir(parents=True, exist_ok=True)
    path = root / 'dataset_description.json'
    original = json.dumps({'BIDSVersion': '1.10.0'})
    path.write_text(original)
    with pytest.raises(DatasetDescriptionError, match='declares BIDSVersion'):
        if derivative:
            patch_derivative_dataset_description(tmp_path, dataset, dictionary.bids_version)
        else:
            patch_dataset_description(tmp_path, dictionary.bids_version)
    assert path.read_text() == original


def test_pipeline_passes_dictionary_version_to_raw_and_derivative_descriptions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    dictionary = replace(load_dicom_dictionary(), bids_version='1.10.0')
    for mapping in dictionary.mappings:
        if mapping.dataset.dataset_description is not None:
            mapping.dataset.dataset_description['BIDSVersion'] = dictionary.bids_version
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.load_dicom_dictionary', Mock(return_value=dictionary))
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.check_dicom_to_niix', lambda: None)
    sources = [DicomSeriesInfo('EchoCombined_anat-T2star_acq-me_gre_0.7iso_ASPIRE', 1, [])]
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.group_dicom_series', Mock(return_value=sources))

    def fake_niix(dicom_path: Path, output_path: Path, filename: str, args: object, **kwargs: object):
        (output_path / (filename + '.nii.gz')).write_bytes(b'fixture')
        (output_path / (filename + '.json')).write_text('{"ManufacturersModelName": "MAGNETOM Terra"}')

    monkeypatch.setattr('mni_7t_dicom_to_bids.convert_dicom_series.run_dicom_to_niix', fake_niix)
    args = Args(tmp_path, tmp_path, '01', '01', None, SkipUnknownsArg(), SkipErrorsArg(), False, False)
    mni_7t_dicom_to_bids(args)
    for path in [tmp_path / 'dataset_description.json', tmp_path / 'derivatives/aspire/dataset_description.json']:
        assert json.loads(path.read_text())['BIDSVersion'] == '1.10.0'
