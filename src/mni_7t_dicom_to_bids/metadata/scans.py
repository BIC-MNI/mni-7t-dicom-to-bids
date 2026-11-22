from pathlib import Path

from bic_util.bids.scans import BidsScansTsvFile, BidsScanTsvRow

from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo, ConvertedScan


def update_scans_tsv(bids_dataset_path: Path, bids_session: BidsSessionInfo, converted_scans: list[ConvertedScan]):
    """
    Create or update the session-level scans TSV with successfully converted images.
    """

    participant_id = f'sub-{bids_session.subject}'
    session_id = f'ses-{bids_session.session}'
    session_path = bids_dataset_path / participant_id / session_id
    file_path = session_path / f'{participant_id}_{session_id}_scans.tsv'

    if not converted_scans:
        return

    scans = BidsScansTsvFile.read_or_create(file_path)
    for scan in converted_scans:
        filename = scan.image_path.relative_to(session_path).as_posix()
        print(f"Updating scans.tsv metadata for '{filename}'...")
        scans.upsert_row(BidsScanTsvRow({'filename': filename}))
    scans.write()
