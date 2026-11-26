import json
from pathlib import Path

import pytest

from mni_7t_dicom_to_bids.args import Args, SkipErrorsArg, SkipUnknownsArg
from mni_7t_dicom_to_bids.convert_dicom_series import get_bids_acquisition_file_name
from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo, ConversionResult, ConvertedScan
from mni_7t_dicom_to_bids.patch_files import patch_file_path, patch_magnitude_counterparts, patch_singleton_runs
from mni_7t_dicom_to_bids.pipeline import mni_7t_dicom_to_bids


def write_image(root: Path, name: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'image')
    return path


@pytest.mark.parametrize('extension', ['nii', 'nii.gz'])
@pytest.mark.parametrize('suffix', ['task-rest_bold', 'acq-multib70_dir-AP_sbref', 'acq-anat_TB1TFL'])
def test_singleton_components_and_echoes_are_renamed_together(tmp_path: Path, extension: str, suffix: str):
    entities, contrast = suffix.rsplit('_', 1)
    paths = [
        write_image(tmp_path, f'sub-01_{entities}_run-3_echo-{echo}_part-{part}_{contrast}.{extension}')
        for echo in [1, 2, 3]
        for part in ['mag', 'phase']
    ]
    expected = {path: path.with_name(path.name.replace('_run-3', '')) for path in paths}

    assert patch_singleton_runs([ConvertedScan(path) for path in paths]) == expected
    assert all(target.read_bytes() == b'image' for target in expected.values())
    assert all(not source.exists() for source in expected)
    assert patch_singleton_runs([ConvertedScan(path) for path in expected.values()]) == {}


def test_repeated_runs_keep_labels_with_missing_components_and_echoes(tmp_path: Path):
    paths = [
        write_image(tmp_path, 'sub-01_task-rest_run-1_echo-1_part-mag_bold.nii.gz'),
        write_image(tmp_path, 'sub-01_task-rest_run-1_echo-1_part-phase_bold.nii.gz'),
        write_image(tmp_path, 'sub-01_task-rest_run-3_echo-2_part-mag_bold.nii.gz'),
    ]
    assert patch_singleton_runs([ConvertedScan(path) for path in paths]) == {}
    assert all(path.exists() for path in paths)


@pytest.mark.parametrize('other', [
    'sub-02_run-2_T1w.nii.gz',
    'sub-01_ses-02_run-2_T1w.nii.gz',
    'sub-01_task-rest_run-2_T1w.nii.gz',
    'sub-01_acq-other_run-2_T1w.nii.gz',
    'sub-01_dir-PA_run-2_T1w.nii.gz',
    'sub-01_rec-other_run-2_T1w.nii.gz',
    'sub-01_inv-2_run-2_T1w.nii.gz',
    'sub-01_mt-on_run-2_T1w.nii.gz',
    'sub-01_run-2_desc-other_T1w.nii.gz',
    'sub-01_run-2_T2w.nii.gz',
    'derivatives/sub-01_run-2_T1w.nii.gz',
])
def test_other_acquisition_groups_do_not_prevent_cleanup_or_get_renamed(tmp_path: Path, other: str):
    image = write_image(tmp_path, 'sub-01_run-1_T1w.nii.gz')
    unrelated = write_image(tmp_path, other)
    target = tmp_path / 'sub-01_T1w.nii.gz'

    assert patch_singleton_runs([ConvertedScan(image)]) == {image: target}
    assert target.exists() and unrelated.exists()


def test_existing_run_prevents_cleanup_during_partial_conversion(tmp_path: Path):
    image = write_image(tmp_path, 'sub-01_run-1_echo-1_part-mag_bold.nii.gz')
    existing = write_image(tmp_path, 'sub-01_run-3_echo-2_part-phase_bold.nii')

    assert patch_singleton_runs([ConvertedScan(image)]) == {}
    assert image.exists() and existing.exists()


def test_existing_components_of_singleton_are_also_renamed(tmp_path: Path):
    image = write_image(tmp_path, 'sub-01_run-1_echo-1_part-mag_bold.nii.gz')
    existing = write_image(tmp_path, 'sub-01_run-1_echo-2_part-phase_bold.nii')
    expected = {path: path.with_name(path.name.replace('_run-1', '')) for path in [image, existing]}

    assert patch_singleton_runs([ConvertedScan(image)]) == expected
    assert all(target.exists() for target in expected.values())


def test_associated_files_are_renamed_and_all_collisions_checked_before_changes(tmp_path: Path):
    paths = [write_image(tmp_path, f'sub-01_run-1_part-{part}_dwi.nii.gz') for part in ['mag', 'phase']]
    for part in ['mag', 'phase']:
        stem = f'sub-01_run-1_part-{part}_dwi'
        (tmp_path / f'{stem}.json').write_text(json.dumps({'note': part}))
        for extension in ['bval', 'bvec']:
            (tmp_path / f'{stem}.{extension}').write_text(extension)
    collision = tmp_path / 'sub-01_part-phase_dwi.bvec'
    collision.write_text('previous')

    with pytest.raises(Exception, match='Files already exist'):
        patch_singleton_runs([ConvertedScan(path) for path in paths])
    assert all(path.exists() for path in paths)
    assert not (tmp_path / 'sub-01_part-mag_dwi.nii.gz').exists()
    assert collision.read_text() == 'previous'

    patch_singleton_runs([ConvertedScan(path) for path in paths], overwrite=True)
    for part in ['mag', 'phase']:
        stem = f'sub-01_part-{part}_dwi'
        assert (tmp_path / f'{stem}.nii.gz').read_bytes() == b'image'
        assert json.loads((tmp_path / f'{stem}.json').read_text()) == {'note': part}
        for extension in ['bval', 'bvec']:
            assert (tmp_path / f'{stem}.{extension}').read_text() == extension


def test_existing_runless_image_requires_overwrite(tmp_path: Path):
    image = write_image(tmp_path, 'sub-01_run-1_T1w.nii.gz')
    target = write_image(tmp_path, 'sub-01_T1w.nii.gz')
    target.write_bytes(b'previous')

    with pytest.raises(Exception, match='Files already exist'):
        patch_singleton_runs([ConvertedScan(image)])
    assert image.exists() and target.read_bytes() == b'previous'
    assert patch_singleton_runs([ConvertedScan(image)], overwrite=True) == {image: target}
    assert target.read_bytes() == b'image'


def test_runless_and_empty_inputs_are_unchanged(tmp_path: Path):
    image = write_image(tmp_path, 'sub-01_T1w.nii.gz')
    assert patch_singleton_runs([]) == {}
    assert patch_singleton_runs([ConvertedScan(image)]) == {}
    assert image.exists()


def test_single_series_gets_provisional_run():
    assert get_bids_acquisition_file_name(BidsSessionInfo('01', '01'), 'T1w', 1) == (
        'sub-01_ses-01_run-1_T1w'
    )


@pytest.mark.parametrize('source, normalized', [
    ('task-cloudy_run-{run}_bold_e1', 'task-cloudy_run-{run}_echo-1_bold'),
    ('acq-me_run-{run}_T2starw_e1', 'acq-me_run-{run}_echo-1_T2starw'),
    ('acq-mtw07_run-{run}_mt-on_MTR', 'acq-mtw07_mt-on_run-{run}_MTR'),
    ('acq-aspire_run-{run}_T2starw', 'acq-aspire_run-{run}_T2starmap'),
])
@pytest.mark.parametrize('run_count', [1, 2])
def test_sequence_cleanup_preserves_runs_until_shared_pass(
    tmp_path: Path, source: str, normalized: str, run_count: int
):
    scans = []
    for run in range(1, run_count + 1):
        original = write_image(tmp_path, 'sub-01_' + source.format(run=run) + '.nii.gz')
        patch_file_path(original)
        expected = tmp_path / ('sub-01_' + normalized.format(run=run) + '.nii.gz')
        assert expected.exists()
        scans.append(ConvertedScan(expected))

    renames = patch_singleton_runs(scans)
    if run_count == 1:
        original = scans[0].image_path
        assert renames == {original: original.with_name(original.name.replace('_run-1', ''))}
    else:
        assert renames == {}
        assert all(scan.image_path.exists() for scan in scans)


@pytest.mark.parametrize('run_count', [1, 2])
def test_dwi_component_identification_defers_run_cleanup(tmp_path: Path, run_count: int):
    scans = []
    for acquisition in range(run_count):
        for component, run in [('M', acquisition * 2 + 1), ('P', acquisition * 2 + 2)]:
            # The first phase series uses the legacy run-2 fallback; later phases use dcm2niix's ph token.
            phase_token = '_ph' if component == 'P' and run > 2 else ''
            stem = f'sub-01_acq-test_dir-AP_run-{run}_dwi'
            metadata = {'ImageType': [component], 'AcquisitionTime': f'10:0{acquisition}:00'}
            image = write_image(tmp_path, stem + phase_token + '.nii.gz')
            sidecar = tmp_path / (stem + phase_token + '.json')
            sidecar.write_text(json.dumps(metadata))
            patch_file_path(image)
            patch_file_path(sidecar)
            part = '_part-phase' if component == 'P' else ''
            image = tmp_path / f'sub-01_acq-test_dir-AP_run-{run}{part}_dwi.nii.gz'
            assert image.exists()
            scans.append(ConvertedScan(image))

    paired = patch_magnitude_counterparts(scans)
    scans = [ConvertedScan(paired.get(scan.image_path, scan.image_path)) for scan in scans]
    patch_singleton_runs(scans)
    for acquisition in range(run_count):
        run = f'_run-{acquisition * 2 + 1}' if run_count > 1 else ''
        for part in ['mag', 'phase']:
            stem = f'sub-01_acq-test_dir-AP{run}_part-{part}_dwi'
            assert (tmp_path / (stem + '.nii.gz')).exists()
            assert (tmp_path / (stem + '.json')).exists()


@pytest.mark.parametrize('pair_count', [1, 2])
def test_tb1tfl_pair_decoding_defers_singleton_cleanup(tmp_path: Path, pair_count: int):
    scans = []
    for run in range(1, pair_count * 2 + 1):
        original = write_image(tmp_path, f'sub-01_acq-anat_run-{run}_TB1TFL.nii.gz')
        patch_file_path(original)
        acquisition = 'anat' if run % 2 else 'sfam'
        image = tmp_path / f'sub-01_acq-{acquisition}_run-{(run + 1) // 2}_TB1TFL.nii.gz'
        assert image.exists()
        scans.append(ConvertedScan(image))

    patch_singleton_runs(scans)
    for pair in range(1, pair_count + 1):
        run = f'_run-{pair}' if pair_count > 1 else ''
        for acquisition in ['anat', 'sfam']:
            assert (tmp_path / f'sub-01_acq-{acquisition}{run}_TB1TFL.nii.gz').exists()


@pytest.mark.parametrize('contrast', ['bold', 'sbref'])
def test_pipeline_preserves_metadata_through_pairing_and_cleanup_of_existing_echo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contrast: str
):
    session = tmp_path / 'sub-01/ses-01'
    directory = session / 'func'
    prefix = 'sub-01_ses-01_task-rest'
    original_mag = f'{prefix}_run-1_echo-1_{contrast}.nii.gz'
    original_phase = f'{prefix}_run-2_echo-1_part-phase_{contrast}.nii.gz'
    existing_echo = f'{prefix}_run-1_echo-2_part-mag_{contrast}.nii.gz'
    write_image(directory, existing_echo)
    scans_path = session / 'sub-01_ses-01_scans.tsv'
    scans_path.write_text(
        'filename\tnote\n'
        f'func/{original_mag}\tmag note\n'
        f'func/{original_phase}\tphase note\n'
        f'func/{existing_echo}\texisting echo note\n'
    )

    def fake_conversion(*args):
        scans = []
        for filename, component in [(original_mag, 'M'), (original_phase, 'P')]:
            image = write_image(directory, filename)
            image.with_name(image.name.removesuffix('.nii.gz') + '.json').write_text(json.dumps({
                'ImageType': [component], 'AcquisitionTime': '10:00:00',
                'ManufacturersModelName': 'MAGNETOM Terra',
            }))
            scans.append(ConvertedScan(image))
        return ConversionResult(scans)

    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.check_dicom_to_niix', lambda: None)
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.group_dicom_series', lambda *args: [])
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.convert_dicom_series', fake_conversion)
    args = Args(tmp_path, tmp_path, '01', '01', None, SkipUnknownsArg(), SkipErrorsArg(), True, False)
    mni_7t_dicom_to_bids(args)

    assert scans_path.read_text() == (
        'filename\tnote\tscanner\n'
        f'func/{prefix}_echo-1_part-mag_{contrast}.nii.gz\tmag note\tTerra\n'
        f'func/{prefix}_echo-1_part-phase_{contrast}.nii.gz\tphase note\tTerra\n'
        f'func/{prefix}_echo-2_part-mag_{contrast}.nii.gz\texisting echo note\tn/a\n'
    )
    assert not list(directory.glob('*run-*'))
    assert len(list(directory.glob('*.nii.gz'))) == 3
