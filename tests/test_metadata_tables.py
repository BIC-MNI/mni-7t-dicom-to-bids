import json
from pathlib import Path

import pytest

from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo, ConvertedScan
from mni_7t_dicom_to_bids.dataset_files import add_static_dataset_files
from mni_7t_dicom_to_bids.metadata.participants import update_participants_tsv
from mni_7t_dicom_to_bids.metadata.scanner import get_scanner
from mni_7t_dicom_to_bids.metadata.scans import update_scans_tsv
from mni_7t_dicom_to_bids.metadata.sessions import update_sessions_tsv


def test_converter_preserves_existing_metadata_and_is_idempotent(tmp_path: Path):
    scans_json_path = tmp_path / 'scans.json'
    acquisition_time_definition = {'Description': 'Time of scan acquisition'}
    scans_json_path.write_text(json.dumps({
        'acq_time': acquisition_time_definition,
    }))
    sessions_json_path = tmp_path / 'sessions.json'
    sessions_json_path.write_text(json.dumps({'note': {'Description': 'Session note'}}))
    participant_path = tmp_path / 'participants.tsv'
    participant_path.write_text('participant_id\tsex\nsub-01\tF\n')
    session_path = tmp_path / 'sub-01/sub-01_sessions.tsv'
    session_path.parent.mkdir()
    session_path.write_text('session_id\tnote\nses-01\tbaseline\n')
    scan_path = tmp_path / 'sub-01/ses-01/sub-01_ses-01_scans.tsv'
    scan_path.parent.mkdir()
    scan_path.write_text('filename\tacq_time\nanat/old.nii.gz\t2020-01-01T10:00:00\n')
    session = BidsSessionInfo('01', '01')
    scans = [
        ConvertedScan(scan_path.parent / 'anat/old.nii.gz'),
        ConvertedScan(scan_path.parent / 'anat/new.nii.gz'),
    ]

    (scan_path.parent / 'anat').mkdir()
    (scan_path.parent / 'anat/old.json').write_text(json.dumps({'ManufacturersModelName': 'MAGNETOM Terra'}))
    (scan_path.parent / 'anat/new.json').write_text(json.dumps({'ManufacturersModelName': 'MAGNETOM Terra.X'}))

    for _ in range(2):
        update_participants_tsv(tmp_path, '01')
        update_participants_tsv(tmp_path, '02')
        update_scans_tsv(tmp_path, session, scans)
        update_sessions_tsv(tmp_path, session)
        update_sessions_tsv(tmp_path, BidsSessionInfo('01', '02'))
        assert participant_path.read_text() == 'participant_id\tsex\nsub-01\tF\nsub-02\tn/a\n'
        assert session_path.read_text() == (
            'session_id\tnote\tscanner\n'
            'ses-01\tbaseline\tSiemens Terra 7T,Siemens Terra.X 7T\n'
            'ses-02\tn/a\tn/a\n'
        )
        sessions_metadata = json.loads(sessions_json_path.read_text())
        assert sessions_metadata['note'] == {'Description': 'Session note'}
        assert sessions_metadata['scanner']['Delimiter'] == ','
        assert scan_path.read_text() == (
            'filename\tacq_time\n'
            'anat/new.nii.gz\tn/a\n'
            'anat/old.nii.gz\t2020-01-01T10:00:00\n'
        )
        scans_metadata = json.loads(scans_json_path.read_text())
        assert scans_metadata['acq_time'] == acquisition_time_definition
        assert 'scanner' not in scans_metadata


@pytest.mark.parametrize('overwrite', [False, True])
def test_participants_sidecar_merges_asset_and_preserves_custom_columns(tmp_path: Path, overwrite: bool):
    path = tmp_path / 'participants.json'
    custom_definition = {'Description': 'Study-specific participant metadata'}
    participant_definition = {'Description': 'Study-specific participant identifier'}
    path.write_text(json.dumps({'custom': custom_definition, 'participant_id': participant_definition}))

    add_static_dataset_files(tmp_path, overwrite)

    content = path.read_text()
    metadata = json.loads(content)
    assert metadata['custom'] == custom_definition
    assert set(metadata) == {'participant_id', 'custom'}
    if overwrite:
        assert metadata['participant_id']['LongName'] == 'Participant identification label sub-'
    else:
        assert metadata['participant_id'] == participant_definition

    add_static_dataset_files(tmp_path, overwrite)
    assert path.read_text() == content


@pytest.mark.parametrize('dataset_name', ['', 'derivatives/romeo'])
def test_scanner_definition_is_created_in_each_dataset(tmp_path: Path, dataset_name: str):
    dataset_path = tmp_path / dataset_name
    session_path = dataset_path / 'sub-01/ses-01'
    image_path = session_path / 'anat/scan.nii.gz'
    image_path.parent.mkdir(parents=True)
    image_path.with_name('scan.json').write_text(json.dumps({'ManufacturersModelName': 'MAGNETOM Terra'}))

    update_scans_tsv(dataset_path, BidsSessionInfo('01', '01'), [ConvertedScan(image_path)])

    update_sessions_tsv(dataset_path, BidsSessionInfo('01', '01'))
    assert not (dataset_path / 'scans.json').exists()
    assert (session_path / 'sub-01_ses-01_scans.tsv').read_text() == 'filename\nanat/scan.nii.gz\n'
    metadata_path = dataset_path / 'sessions.json'
    first_content = metadata_path.read_text()
    metadata = json.loads(first_content)
    assert metadata['scanner']['LongName'] == 'MRI scanner'
    assert metadata['scanner']['Levels']['Siemens Terra 7T'] == 'Siemens Terra 7T'

    update_scans_tsv(dataset_path, BidsSessionInfo('01', '01'), [ConvertedScan(image_path)])
    update_sessions_tsv(dataset_path, BidsSessionInfo('01', '01'))
    assert metadata_path.read_text() == first_content


def test_no_scans_does_not_create_metadata(tmp_path: Path):
    update_scans_tsv(tmp_path, BidsSessionInfo('01', '01'), [])
    assert not list(tmp_path.rglob('*'))


def test_unknown_scanner_replaces_previous_classification(tmp_path: Path):
    path = tmp_path / 'sub-01/ses-01/sub-01_ses-01_scans.tsv'
    path.parent.mkdir(parents=True)
    path.write_text('filename\tnote\nanat/scan.nii\tkeep\n')
    sessions_path = tmp_path / 'sub-01/sub-01_sessions.tsv'
    sessions_path.write_text('session_id\tscanner\nses-01\tSiemens Terra 7T\n')
    (path.parent / 'anat').mkdir()
    (path.parent / 'anat/scan.json').write_text('{}')
    update_scans_tsv(tmp_path, BidsSessionInfo('01', '01'), [ConvertedScan(path.parent / 'anat/scan.nii')])
    update_sessions_tsv(tmp_path, BidsSessionInfo('01', '01'))
    assert path.read_text() == 'filename\tnote\nanat/scan.nii\tkeep\n'
    assert (tmp_path / 'sub-01/sub-01_sessions.tsv').read_text() == 'session_id\tscanner\nses-01\tn/a\n'


@pytest.mark.parametrize(
    'model, software, expected',
    [
        ('MAGNETOM Terra', None, 'Siemens Terra 7T'),
        ('MAGNETOM Terra.X', 'syngo MR XA60', 'Siemens Terra.X 7T'),
        ('Investigational_Device_7T', 'syngo MR E12', 'Siemens Terra 7T'),
        ('Investigational_Device_7T', 'syngo MR XA60', None),
        ('Investigational_Device_7T', None, None),
        ('Other scanner', 'syngo MR E12', None),
        (None, None, None),
    ],
)
def test_scanner_classification(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], model: str | None, software: str | None, expected: str | None
):
    metadata = {}
    if model is not None:
        metadata['ManufacturersModelName'] = model
    if software is not None:
        metadata['SoftwareVersions'] = software
    path = tmp_path / 'scan.json'
    path.write_text(json.dumps(metadata))

    assert get_scanner(path) == expected
    warning = capsys.readouterr().err
    if expected is None:
        assert 'WARNING' in warning
        assert str(path) in warning
        assert 'ManufacturersModelName=' in warning
        assert 'SoftwareVersions=' in warning
    else:
        assert not warning


def test_incremental_conversion_summarizes_existing_scans_and_refreshes_assignments(tmp_path: Path):
    session = BidsSessionInfo('01', '01')
    directory = tmp_path / 'sub-01/ses-01/anat'
    directory.mkdir(parents=True)
    first = directory / 'first.nii.gz'
    second = directory / 'second.nii.gz'
    first.with_name('first.json').write_text(json.dumps({'ManufacturersModelName': 'MAGNETOM Terra'}))
    second.with_name('second.json').write_text(json.dumps({'ManufacturersModelName': 'MAGNETOM Terra.X'}))
    sessions_path = tmp_path / 'sub-01/sub-01_sessions.tsv'
    sessions_path.write_text('session_id\tscanner\tnote\nses-02\tSiemens Terra.X 7T\tfollow-up\n')
    scans_path = directory.parent / 'sub-01_ses-01_scans.tsv'
    scans_path.write_text('filename\tnote\nanat/first.nii.gz\tbaseline\n')
    update_sessions_tsv(tmp_path, session)
    assert scans_path.read_text() == 'filename\tnote\nanat/first.nii.gz\tbaseline\n'

    # Only the new acquisition is returned by this conversion.
    for _ in range(2):
        update_scans_tsv(tmp_path, session, [ConvertedScan(second)])
        update_sessions_tsv(tmp_path, session)
        assert sessions_path.read_text() == (
            'session_id\tscanner\tnote\n'
            'ses-01\tSiemens Terra 7T,Siemens Terra.X 7T\tn/a\n'
            'ses-02\tSiemens Terra.X 7T\tfollow-up\n'
        )
        assert not (tmp_path / 'scans.json').exists()
        assert scans_path.read_text() == (
            'filename\tnote\n'
            'anat/first.nii.gz\tbaseline\n'
            'anat/second.nii.gz\tn/a\n'
        )

    # Refresh from the sidecars rather than accumulating stale classifications.
    second.with_name('second.json').write_text(json.dumps({'ManufacturersModelName': 'MAGNETOM Terra'}))
    update_sessions_tsv(tmp_path, session)
    assert scans_path.read_text() == 'filename\tnote\nanat/first.nii.gz\tbaseline\nanat/second.nii.gz\tn/a\n'
    assert 'ses-01\tSiemens Terra 7T\tn/a\n' in sessions_path.read_text()


def test_missing_sidecar_records_unknown_scanner(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    session = BidsSessionInfo('01', '01')
    scans_path = tmp_path / 'sub-01/ses-01/sub-01_ses-01_scans.tsv'
    scans_path.parent.mkdir(parents=True)
    scans_path.write_text('filename\nanat/scan.nii.gz\n')
    update_sessions_tsv(tmp_path, session)
    assert (tmp_path / 'sub-01/sub-01_sessions.tsv').read_text() == 'session_id\tscanner\nses-01\tn/a\n'
    assert scans_path.read_text() == 'filename\nanat/scan.nii.gz\n'
    assert 'missing' in capsys.readouterr().err
