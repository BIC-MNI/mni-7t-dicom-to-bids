from pathlib import Path

from bic_util.tsv import upsert_tsv_row

from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo, ConvertedScan


def update_scans_tsv(bids_dataset_path: Path, bids_session: BidsSessionInfo, scans: list[ConvertedScan]):
    """
    Create or update the session-level scans TSV with successfully converted images.
    """

    participant_id = f'sub-{bids_session.subject}'
    session_id = f'ses-{bids_session.session}'
    session_path = bids_dataset_path / participant_id / session_id
    file_path = session_path / f'{participant_id}_{session_id}_scans.tsv'

    for scan in scans:
        filename = scan.image_path.relative_to(session_path).as_posix()
        print(f"Updating scans.tsv metadata for '{filename}'...")
        upsert_tsv_row(file_path, 'filename', {'filename': filename})
