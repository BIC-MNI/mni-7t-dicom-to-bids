from pathlib import Path

from bic_util.bids.scans import BidsScansTsvFile
from bic_util.bids.sessions import BidsSessionsTsvFile, BidsSessionTsvRow
from bic_util.print import print_warning

from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo
from mni_7t_dicom_to_bids.metadata.scanner import get_scanner
from mni_7t_dicom_to_bids.metadata.sidecars import update_json_from_asset


def update_sessions_tsv(bids_dataset_path: Path, bids_session: BidsSessionInfo):
    """Summarize scanner information from all registered scans at the session level."""

    participant_id = f'sub-{bids_session.subject}'
    session_id = f'ses-{bids_session.session}'
    file_path = bids_dataset_path / participant_id / f'{participant_id}_sessions.tsv'
    session_path = file_path.parent / session_id
    scans_path = session_path / f'{participant_id}_{session_id}_scans.tsv'
    scans = BidsScansTsvFile.read_or_create(scans_path)

    scanners: set[str] = set()
    for scan_row in scans.rows:
        image_path = session_path / scan_row.file_path
        json_path = image_path.with_name(image_path.name.removesuffix('.gz')).with_suffix('.json')
        if json_path.exists():
            scanner = get_scanner(json_path)
        else:
            scanner = None
            print_warning(f"Cannot identify scanner: missing '{json_path}'; using n/a.")
        scanners.add(scanner or 'n/a')

    print(f"Updating sessions.tsv metadata for '{file_path.name}'...")
    sessions = BidsSessionsTsvFile.read_or_create(file_path)
    row = sessions.get_row(session_id) or BidsSessionTsvRow({'session_id': session_id})
    row.data['scanner'] = ','.join(sorted(scanners)) or 'n/a'
    sessions.set_row(row)
    sessions.write()
    update_json_from_asset(bids_dataset_path, 'sessions.json')
