import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from mni_7t_dicom_to_bids.args import Args, SkipErrorsArg, SkipUnknownsArg
from mni_7t_dicom_to_bids.dataclass import ConversionResult, ConvertedScan
from mni_7t_dicom_to_bids.patch_files import patch_file_path, patch_magnitude_counterparts
from mni_7t_dicom_to_bids.pipeline import mni_7t_dicom_to_bids


def write_scan(root: Path, name: str, image_type: list[str], acquisition_time: str | None = None) -> ConvertedScan:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'image')
    metadata = {
        'ImageType': image_type,
        'ManufacturersModelName': 'MAGNETOM Terra',
    }
    if acquisition_time is not None:
        metadata['AcquisitionTime'] = acquisition_time
    path.with_name(path.name.removesuffix('.gz')).with_suffix('.json').write_text(json.dumps(metadata))
    return ConvertedScan(path)


@pytest.mark.parametrize('extension', ['nii', 'nii.gz'])
@pytest.mark.parametrize('suffix', ['mt-on_MTR', 'T1w', 'echo-2_T2starw', 'dwi'])
def test_matching_magnitude_is_renamed(tmp_path: Path, extension: str, suffix: str):
    magnitude = write_scan(tmp_path, f'sub-01_{suffix}.{extension}', ['ORIGINAL', 'PRIMARY', 'M'])
    phase_name = magnitude.image_path.name.replace('_' + suffix.split('_')[-1], '_part-phase_' + suffix.split('_')[-1])
    phase = write_scan(tmp_path, phase_name, ['ORIGINAL', 'PRIMARY', 'P'])
    expected = phase.image_path.with_name(phase.image_path.name.replace('part-phase', 'part-mag'))
    if suffix == 'dwi':
        (tmp_path / 'sub-01_dwi.bval').write_text('0')

    # The series conversion order does not matter.
    renames = patch_magnitude_counterparts([phase, magnitude])

    assert renames == {magnitude.image_path: expected}
    assert not magnitude.image_path.exists()
    assert expected.read_bytes() == b'image'
    assert not list(tmp_path.glob(f'sub-01_{suffix}.json'))
    sidecar = expected.with_name(expected.name.removesuffix('.gz')).with_suffix('.json')
    assert json.loads(sidecar.read_text())['ImageType'][-1] == 'M'
    assert phase.image_path.exists()
    assert patch_magnitude_counterparts([phase, ConvertedScan(expected)]) == {}
    if suffix == 'dwi':
        assert (tmp_path / 'sub-01_part-mag_dwi.bval').read_text() == '0'
        assert not (tmp_path / 'sub-01_dwi.bval').exists()


@pytest.mark.parametrize('other_name', [
    'sub-01_run-2_part-phase_T1w.nii.gz',
    'sub-01_echo-2_part-phase_T1w.nii.gz',
    'sub-01_acq-other_part-phase_T1w.nii.gz',
    'other-dataset/sub-01_part-phase_T1w.nii.gz',
])
def test_different_entities_or_directories_do_not_pair(tmp_path: Path, other_name: str):
    magnitude = write_scan(tmp_path, 'sub-01_T1w.nii.gz', ['M'])
    phase = write_scan(tmp_path, other_name, ['P'])
    assert patch_magnitude_counterparts([magnitude, phase]) == {}
    assert magnitude.image_path.exists()


@pytest.mark.parametrize('image_type', [[], ['P'], ['DERIVED', 'PRIMARY']])
def test_unlabeled_image_must_be_identified_as_magnitude(tmp_path: Path, image_type: list[str]):
    unlabeled = write_scan(tmp_path, 'sub-01_T1w.nii.gz', image_type)
    phase = write_scan(tmp_path, 'sub-01_part-phase_T1w.nii.gz', ['P'])
    assert patch_magnitude_counterparts([unlabeled, phase]) == {}
    assert unlabeled.image_path.exists()


def test_magnitude_only_and_explicit_pairs_are_unchanged(tmp_path: Path):
    scans = [
        write_scan(tmp_path, 'sub-01_T1w.nii.gz', ['M']),
        write_scan(tmp_path, 'sub-01_part-mag_MEGRE.nii.gz', ['M']),
        write_scan(tmp_path, 'sub-01_part-phase_MEGRE.nii.gz', ['P']),
        write_scan(tmp_path, 'sub-01_part-phase_T2starw.nii.gz', ['P']),
    ]
    assert patch_magnitude_counterparts(scans) == {}
    assert all(scan.image_path.exists() for scan in scans)


def test_existing_destination_requires_overwrite(tmp_path: Path):
    magnitude = write_scan(tmp_path, 'sub-01_T1w.nii.gz', ['M'])
    phase = write_scan(tmp_path, 'sub-01_part-phase_T1w.nii.gz', ['P'])
    previous = write_scan(tmp_path, 'sub-01_part-mag_T1w.nii.gz', ['M'])
    previous.image_path.write_bytes(b'previous')
    with pytest.raises(Exception, match='Files already exist'):
        patch_magnitude_counterparts([magnitude, phase])
    assert magnitude.image_path.exists()
    assert previous.image_path.read_bytes() == b'previous'
    patch_magnitude_counterparts([magnitude, phase], overwrite=True)
    assert previous.image_path.read_bytes() == b'image'


@pytest.mark.parametrize('suffix', ['echo-3_bold', 'sbref'])
@pytest.mark.parametrize('magnitude_part', ['', '_part-mag'])
def test_runs_align_by_acquisition_time(tmp_path: Path, suffix: str, magnitude_part: str):
    entities, contrast = suffix.rsplit('_', 1) if '_' in suffix else ('', suffix)
    echo = '_' + entities if entities else ''
    magnitude = write_scan(
        tmp_path, f'sub-01_run-1{echo}{magnitude_part}_{contrast}.nii.gz', ['M'], '10:27:20.002500'
    )
    phase = write_scan(
        tmp_path, f'sub-01_run-2{echo}_part-phase_{contrast}.nii.gz', ['P'], '10:27:20.002500'
    )
    final_magnitude = tmp_path / f'sub-01_run-1{echo}_part-mag_{contrast}.nii.gz'
    final_phase = tmp_path / f'sub-01_run-1{echo}_part-phase_{contrast}.nii.gz'

    renames = patch_magnitude_counterparts([phase, magnitude])

    assert renames[phase.image_path] == final_phase
    assert final_magnitude.exists() and final_phase.exists()
    assert final_phase.with_suffix('').with_suffix('.json').exists()
    assert not phase.image_path.exists()
    assert patch_magnitude_counterparts([ConvertedScan(final_phase), ConvertedScan(final_magnitude)]) == {}


def test_repeated_acquisitions_keep_separate_magnitude_runs(tmp_path: Path):
    scans = []
    for mag_run, phase_run, time in [(1, 2, '10:00:00'), (3, 4, '11:00:00')]:
        scans.extend([
            write_scan(tmp_path, f'sub-01_task-rest_run-{mag_run}_echo-1_bold.nii.gz', ['M'], time),
            write_scan(tmp_path, f'sub-01_task-rest_run-{phase_run}_echo-1_part-phase_bold.nii.gz', ['P'], time),
        ])
    renames = patch_magnitude_counterparts(scans)
    assert len(renames) == 4
    for run in [1, 3]:
        for part in ['mag', 'phase']:
            assert (tmp_path / f'sub-01_task-rest_run-{run}_echo-1_part-{part}_bold.nii.gz').exists()


def test_different_acquisition_times_do_not_pair(tmp_path: Path):
    magnitude = write_scan(tmp_path, 'sub-01_run-1_bold.nii.gz', ['M'], '10:00:00')
    phase = write_scan(tmp_path, 'sub-01_run-2_part-phase_bold.nii.gz', ['P'], '11:00:00')
    assert patch_magnitude_counterparts([magnitude, phase]) == {}


def test_ambiguous_acquisition_is_rejected_before_renaming(tmp_path: Path):
    scans = [
        write_scan(tmp_path, 'sub-01_run-1_bold.nii.gz', ['M'], '10:00:00'),
        write_scan(tmp_path, 'sub-01_run-2_bold.nii.gz', ['M'], '10:00:00'),
        write_scan(tmp_path, 'sub-01_run-3_part-phase_bold.nii.gz', ['P'], '10:00:00'),
    ]
    with pytest.raises(ValueError, match='Ambiguous magnitude/phase pairing'):
        patch_magnitude_counterparts(scans)
    assert all(scan.image_path.exists() for scan in scans)


def test_diffusion_without_component_metadata_pairs_and_keeps_gradients(tmp_path: Path):
    image_type = ['ORIGINAL', 'PRIMARY', 'DIFFUSION', 'NONE', 'MB', 'ND', 'MOSAIC']
    magnitude = write_scan(tmp_path, 'sub-01_acq-multib70_dir-AP_dwi.nii.gz', image_type, '10:51:27.605000')
    phase = write_scan(tmp_path, 'sub-01_acq-multib70_dir-AP_part-phase_dwi.nii.gz', image_type, '10:51:27.605000')
    alone = write_scan(tmp_path, 'sub-01_acq-b0_dir-PA_dwi.nii.gz', image_type, '11:00:00')
    for ext in ['bval', 'bvec']:
        (tmp_path / f'sub-01_acq-multib70_dir-AP_dwi.{ext}').write_text(ext)

    renames = patch_magnitude_counterparts([magnitude, phase, alone])

    assert renames == {magnitude.image_path: tmp_path / 'sub-01_acq-multib70_dir-AP_part-mag_dwi.nii.gz'}
    for ext in ['bval', 'bvec']:
        assert (tmp_path / f'sub-01_acq-multib70_dir-AP_part-mag_dwi.{ext}').read_text() == ext
        assert not (tmp_path / f'sub-01_acq-multib70_dir-AP_dwi.{ext}').exists()
    assert alone.image_path.exists()


def test_multi_echo_magnitude_keeps_contrast_until_pairing(tmp_path: Path):
    path = tmp_path / 'sub-01_acq-aspire_T2starw_e1.nii.gz'
    path.touch()
    patch_file_path(path)
    assert (tmp_path / 'sub-01_acq-aspire_echo-1_T2starw.nii.gz').exists()


@pytest.mark.parametrize('with_runs', [False, True])
def test_pipeline_records_final_paths_and_preserves_existing_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, with_runs: bool
):
    session_path = tmp_path / 'sub-01/ses-01'
    anat = session_path / 'anat'
    anat.mkdir(parents=True)
    scans_path = session_path / 'sub-01_ses-01_scans.tsv'
    mag_run, phase_run = ('_run-1', '_run-2') if with_runs else ('', '')
    old_name = f'sub-01_ses-01{mag_run}_T1w.nii.gz'
    new_name = 'sub-01_ses-01_part-mag_T1w.nii.gz'
    old_phase = f'sub-01_ses-01{phase_run}_part-phase_T1w.nii.gz'
    new_phase = 'sub-01_ses-01_part-phase_T1w.nii.gz'
    scans_path.write_text(f'filename\tnote\nanat/{old_name}\tkeep\nanat/{old_phase}\tphase note\n')
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.check_dicom_to_niix', lambda: None)
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.group_dicom_series', Mock(return_value=[]))

    def fake_conversion(*args: object):
        return ConversionResult([
            write_scan(anat, old_name, ['M'], '10:00:00'),
            write_scan(anat, old_phase, ['P'], '10:00:00'),
        ])

    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.convert_dicom_series', fake_conversion)
    args = Args(tmp_path, tmp_path, '01', '01', None, SkipUnknownsArg(), SkipErrorsArg(), True, False)
    for _ in range(2):
        mni_7t_dicom_to_bids(args)
        assert scans_path.read_text() == (
            'filename\tnote\tscanner\n'
            f'anat/{new_name}\tkeep\tTerra\n'
            f'anat/{new_phase}\tphase note\tTerra\n'
        )
        assert not (anat / old_name).exists()
        assert (anat / new_name).exists()
