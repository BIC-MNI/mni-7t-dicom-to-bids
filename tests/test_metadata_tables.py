from pathlib import Path

from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo, ConvertedScan
from mni_7t_dicom_to_bids.metadata.participants import update_participants_tsv
from mni_7t_dicom_to_bids.metadata.scans import update_scans_tsv
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
    scans = [ConvertedScan(scan_path.parent / 'anat/old.nii.gz'), ConvertedScan(scan_path.parent / 'anat/new.nii.gz')]

    for _ in range(2):
        update_participants_tsv(tmp_path, '01')
        update_participants_tsv(tmp_path, '02')
        update_sessions_tsv(tmp_path, session)
        update_sessions_tsv(tmp_path, BidsSessionInfo('01', '02'))
        update_scans_tsv(tmp_path, session, scans)
        assert participant_path.read_text() == 'participant_id\tsex\nsub-01\tF\nsub-02\tn/a\n'
        assert session_path.read_text() == 'session_id\tnote\nses-01\tbaseline\nses-02\tn/a\n'
        assert scan_path.read_text() == (
            'filename\tacq_time\nanat/new.nii.gz\tn/a\nanat/old.nii.gz\t2020-01-01T10:00:00\n'
        )


def test_no_scans_does_not_create_metadata(tmp_path: Path):
    update_scans_tsv(tmp_path, BidsSessionInfo('01', '01'), [])
    assert not list(tmp_path.rglob('*'))
