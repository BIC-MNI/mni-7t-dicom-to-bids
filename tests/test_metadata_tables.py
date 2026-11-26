import json
from pathlib import Path

import pytest

from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo, ConvertedScan
from mni_7t_dicom_to_bids.metadata.participants import update_participants_tsv
from mni_7t_dicom_to_bids.metadata.scans import get_scanner, update_scans_tsv
from mni_7t_dicom_to_bids.metadata.sessions import update_sessions_tsv


def test_converter_preserves_existing_metadata_and_is_idempotent(tmp_path: Path):
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
        update_sessions_tsv(tmp_path, session)
        update_sessions_tsv(tmp_path, BidsSessionInfo('01', '02'))
        update_scans_tsv(tmp_path, session, scans)
        assert participant_path.read_text() == 'participant_id\tsex\nsub-01\tF\nsub-02\tn/a\n'
        assert session_path.read_text() == 'session_id\tnote\nses-01\tbaseline\nses-02\tn/a\n'
        assert scan_path.read_text() == (
            'filename\tacq_time\tscanner\n'
            'anat/new.nii.gz\tn/a\tTerra.X\n'
            'anat/old.nii.gz\t2020-01-01T10:00:00\tTerra\n'
        )


def test_no_scans_does_not_create_metadata(tmp_path: Path):
    update_scans_tsv(tmp_path, BidsSessionInfo('01', '01'), [])
    assert not list(tmp_path.rglob('*'))


def test_unknown_scanner_replaces_previous_classification(tmp_path: Path):
    path = tmp_path / 'sub-01/ses-01/sub-01_ses-01_scans.tsv'
    path.parent.mkdir(parents=True)
    path.write_text('filename\tscanner\tnote\nanat/scan.nii\tTerra\tkeep\n')
    (path.parent / 'anat').mkdir()
    (path.parent / 'anat/scan.json').write_text('{}')
    update_scans_tsv(tmp_path, BidsSessionInfo('01', '01'), [ConvertedScan(path.parent / 'anat/scan.nii')])
    assert path.read_text() == 'filename\tscanner\tnote\nanat/scan.nii\tn/a\tkeep\n'


@pytest.mark.parametrize(
    'model, software, expected',
    [
        ('MAGNETOM Terra', None, 'Terra'),
        ('MAGNETOM Terra.X', 'syngo MR XA60', 'Terra.X'),
        ('Investigational_Device_7T', 'syngo MR E12', 'Terra'),
        ('Investigational_Device_7T', 'syngo MR XA60', 'n/a'),
        ('Investigational_Device_7T', None, 'n/a'),
        ('Other scanner', 'syngo MR E12', 'n/a'),
        (None, None, 'n/a'),
    ],
)
def test_scanner_classification(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], model: str | None, software: str | None, expected: str
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
    if expected == 'n/a':
        assert 'WARNING' in warning
        assert str(path) in warning
        assert 'ManufacturersModelName=' in warning
        assert 'SoftwareVersions=' in warning
    else:
        assert not warning
