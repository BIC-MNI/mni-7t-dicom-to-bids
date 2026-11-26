import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from mni_7t_dicom_to_bids.args import Args, SkipErrorsArg, SkipUnknownsArg
from mni_7t_dicom_to_bids.dataclass import ConvertedScan, DicomSeriesInfo
from mni_7t_dicom_to_bids.patch_files import patch_frequency_maps
from mni_7t_dicom_to_bids.pipeline import mni_7t_dicom_to_bids


@pytest.mark.parametrize('extension', ['nii', 'nii.gz'])
def test_frequency_map_renames_image_and_sidecar(tmp_path: Path, extension: str):
    image = tmp_path / f'sub-01_part-phase_desc-frequency_T2starw.{extension}'
    sidecar = tmp_path / 'sub-01_part-phase_desc-frequency_T2starw.json'
    image.write_bytes(b'image')
    metadata = {'Units': 'Hz', 'ImageType': ['P'], 'note': 'keep'}
    sidecar.write_text(json.dumps(metadata))
    target = tmp_path / f'sub-01_desc-frequency_T2starw.{extension}'

    assert patch_frequency_maps([ConvertedScan(image)]) == {image: target}
    assert target.read_bytes() == b'image'
    assert json.loads((tmp_path / 'sub-01_desc-frequency_T2starw.json').read_text()) == metadata
    assert not image.exists() and not sidecar.exists()
    assert patch_frequency_maps([ConvertedScan(target)]) == {}


@pytest.mark.parametrize('part, units', [('phase', 'rad'), ('phase', 'arbitrary'), ('phase', None), ('mag', 'Hz')])
def test_other_components_and_units_are_unchanged(tmp_path: Path, part: str, units: str | None):
    image = tmp_path / f'sub-01_part-{part}_T2starw.nii.gz'
    image.write_bytes(b'image')
    sidecar = tmp_path / f'sub-01_part-{part}_T2starw.json'
    sidecar.write_text(json.dumps({'Units': units} if units is not None else {}))
    assert patch_frequency_maps([ConvertedScan(image)]) == {}
    assert image.exists() and sidecar.exists()


def test_frequency_map_respects_overwrite(tmp_path: Path):
    image = tmp_path / 'sub-01_part-phase_T2starw.nii.gz'
    image.write_bytes(b'new')
    sidecar = tmp_path / 'sub-01_part-phase_T2starw.json'
    sidecar.write_text('{"Units": "Hz"}')
    target = tmp_path / 'sub-01_T2starw.nii.gz'
    target.write_bytes(b'old')
    with pytest.raises(Exception, match='Files already exist'):
        patch_frequency_maps([ConvertedScan(image)])
    assert image.exists() and sidecar.exists()
    assert target.read_bytes() == b'old'
    patch_frequency_maps([ConvertedScan(image)], overwrite=True)
    assert target.read_bytes() == b'new'


@pytest.mark.parametrize('units_from_override', [False, True])
def test_pipeline_corrects_final_units_before_pairing_and_retains_scan_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, units_from_override: bool
):
    dictionary = tmp_path / 'dictionary.json'
    frequency_mapping: dict[str, object] = {
        'series': 'frequency', 'datatype': 'anat', 'filename': 'desc-frequency_T2starw',
    }
    if units_from_override:
        frequency_mapping['sidecar'] = {'Units': 'Hz'}
    dictionary.write_text(json.dumps({
        'bids-version': '1.11.1', 'ignored-series': [], 'trim-series-suffixes': [],
        'mappings': [
            {'series': 'magnitude', 'datatype': 'anat', 'filename': 'desc-frequency_T2starw'},
            frequency_mapping,
            {'series': 'phase', 'datatype': 'anat', 'filename': 'desc-unwrapped_T2starw'},
        ],
    }))
    sources = [DicomSeriesInfo(name, i, []) for i, name in enumerate(['magnitude', 'frequency', 'phase'])]
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.check_dicom_to_niix', lambda: None)
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.group_dicom_series', Mock(return_value=sources))

    def fake_niix(dicom_path: Path, output_path: Path, filename: str, args: object, **kwargs: object):
        phase = '_run-2_' in filename or 'desc-unwrapped' in filename
        metadata = {
            'ManufacturersModelName': 'MAGNETOM Terra',
            'ImageType': ['P' if phase else 'M'],
            'AcquisitionTime': '10:00:00',
        }
        if 'desc-unwrapped' in filename:
            metadata['Units'] = 'arbitrary'
        elif '_run-2_' in filename and not units_from_override:
            metadata['Units'] = 'Hz'
        name = filename + ('_ph' if phase else '')
        (output_path / (name + '.nii.gz')).write_bytes(b'image')
        (output_path / (name + '.json')).write_text(json.dumps(metadata))

    monkeypatch.setattr('mni_7t_dicom_to_bids.convert_dicom_series.run_dicom_to_niix', fake_niix)
    root = tmp_path / 'bids'
    session = root / 'sub-01/ses-01'
    session.mkdir(parents=True)
    scans_path = session / 'sub-01_ses-01_scans.tsv'
    old = 'sub-01_ses-01_run-2_part-phase_desc-frequency_T2starw'
    final = 'sub-01_ses-01_run-2_desc-frequency_T2starw'
    scans_path.write_text(f'filename\tnote\nanat/{old}.nii.gz\tkeep\n')
    args = Args(tmp_path, root, '01', '01', dictionary, SkipUnknownsArg(), SkipErrorsArg(), True, False)
    for _ in range(2):
        mni_7t_dicom_to_bids(args)
        assert not (session / 'anat' / (old + '.nii.gz')).exists()
        assert (session / 'anat' / (final + '.nii.gz')).exists()
        frequency = json.loads((session / 'anat' / (final + '.json')).read_text())
        assert frequency['Units'] == 'Hz'
        phase = json.loads(next(session.rglob('*part-phase_desc-unwrapped*.json')).read_text())
        assert phase['Units'] == 'arbitrary'
        # A frequency map must not cause a magnitude image to receive part-mag or change runs.
        assert (session / 'anat/sub-01_ses-01_run-1_desc-frequency_T2starw.nii.gz').exists()
        assert not list(session.rglob('*part-mag*'))
        assert f'anat/{final}.nii.gz\tkeep\n' in scans_path.read_text()
        assert old not in scans_path.read_text()
