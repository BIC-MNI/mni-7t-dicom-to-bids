from pathlib import Path

from bic_util.bids.sessions import BidsSessionsTsvFile, BidsSessionTsvRow

from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo


def update_sessions_tsv(bids_dataset_path: Path, bids_session: BidsSessionInfo):
    """
    Create or update the subject-level sessions TSV file.
    """

    participant_id = f'sub-{bids_session.subject}'
    session_id = f'ses-{bids_session.session}'
    file_path = bids_dataset_path / participant_id / f'{participant_id}_sessions.tsv'
    print(f"Updating sessions.tsv metadata for '{file_path.name}'...")
    sessions = BidsSessionsTsvFile.read_or_create(file_path)
    sessions.upsert_row(BidsSessionTsvRow({'session_id': session_id}))
    sessions.write()
