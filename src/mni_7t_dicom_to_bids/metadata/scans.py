import json
from pathlib import Path

from bic_util.bids.scans import BidsScansTsvFile, BidsScanTsvRow
from bic_util.print import print_warning

from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo, ConvertedScan


def get_scanner(json_path: Path) -> str:
    """Identify the scanner from the converted scan's JSON sidecar."""

    with json_path.open() as file:
        metadata: dict[str, object] = json.load(file)

    model = metadata.get('ManufacturersModelName')
    software = metadata.get('SoftwareVersions')

    match model, software:
        case 'MAGNETOM Terra', _:
            return 'Terra'
        case 'MAGNETOM Terra.X', _:
            return 'Terra.X'
        case 'Investigational_Device_7T', 'syngo MR E12':
            return 'Terra'
        case _, _:
            print_warning(
                f"Cannot identify scanner for '{json_path}': ManufacturersModelName={model!r},"
                f" SoftwareVersions={software!r}; using n/a."
            )

            return 'n/a'


def update_scans_tsv(
    bids_dataset_path: Path,
    bids_session: BidsSessionInfo,
    converted_scans: list[ConvertedScan],
    renamed_images: dict[Path, Path] | None = None,
):
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

    # Perform renamings if any.
    if renamed_images is not None:
        for source, target in renamed_images.items():
            if not source.is_relative_to(session_path):
                continue

            row = scans.get_row(source.relative_to(session_path).as_posix())
            if row is not None:
                row.set_file_name(target.name)

    # Add Terra / Terra.X scanner metadata.
    for scan in converted_scans:
        filename = scan.image_path.relative_to(session_path).as_posix()
        print(f"Updating scans.tsv metadata for '{filename}'...")
        row = scans.get_row(filename) or BidsScanTsvRow({'filename': filename})
        json_path = scan.image_path.with_name(scan.image_path.name.removesuffix('.gz')).with_suffix('.json')
        row.data['scanner'] = get_scanner(json_path)
        scans.set_row(row)

    scans.write()
