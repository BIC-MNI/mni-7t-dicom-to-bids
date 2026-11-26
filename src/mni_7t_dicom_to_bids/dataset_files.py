import filecmp
import getpass
import os
import shutil
from datetime import datetime
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path

from bic_util.bids.name import BidsName
from bic_util.print import print_error_exit, print_warning
from bic_util.tsv import upsert_tsv_row

from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo, ConvertedScan


def add_dataset_files(bids_dataset_path: Path, bids_session: BidsSessionInfo, dicom_study_path: Path, overwrite: bool):
    """
    Add the auxiliary dataset files to the output BIDS directory.
    """

    print("Creating auxiliary files...")

    add_participants_7t_to_bids_json_file(bids_dataset_path, bids_session, dicom_study_path)

    add_static_dataset_files(bids_dataset_path, overwrite)


def add_static_dataset_files(bids_dir_path: Path, overwrite: bool):
    """
    Copy the static dataset files into the BIDS directory. The files are copied only if they do not
    exist in the BIDS directory, or if they exist and are changed but can be overwritten. Exit the
    program with an error if some file exists and is changed but cannot be overwritten.
    """

    # Ignore rules are append-only, including when overwriting conversion outputs.
    ensure_bidsignore(bids_dir_path)

    file_name = 'participants.json'
    with as_file(_resolve_asset_file_path(file_name)) as new_file_path:
        old_file_path = bids_dir_path / file_name

        if not old_file_path.exists():
            print(f"File '{file_name}' does not exist in the BIDS directory. Creating...")
        else:
            if filecmp.cmp(old_file_path, new_file_path, shallow=False):
                print(f"File '{file_name}' already exists in the BIDS directory and is unchanged. Skipping.")
                return

            if overwrite:
                print_warning(
                    f"File '{file_name}' already exists in the BIDS directory and is changed. Overwriting..."
                )
            else:
                print_error_exit(
                    f"File '{file_name}' already exists in the BIDS directory and is changed, use the option"
                    " '--overwrite' to overwrite it."
                )

        shutil.copyfile(new_file_path, old_file_path)


def ensure_bidsignore(dataset_path: Path) -> Path:
    """Initialize ignore rules from the packaged template without replacing existing content."""
    path = dataset_path / '.bidsignore'
    if not path.exists():
        with as_file(_resolve_asset_file_path('.bidsignore')) as template:
            shutil.copyfile(template, path)
    return path


def update_bidsignore(dataset_path: Path, scans: list[ConvertedScan]):
    """Append exact final paths for flagged scans and their associated files."""
    entries: set[str] = set()
    for scan in scans:
        if not scan.bidsignore:
            continue
        name = BidsName.from_string(scan.image_path.name)
        name.extension = None
        prefix = str(name) + '.'
        for path in scan.image_path.parent.iterdir():
            if path.is_file() and path.name.startswith(prefix):
                entries.add(path.relative_to(dataset_path).as_posix())

    if not entries:
        return

    path = ensure_bidsignore(dataset_path)
    content = path.read_text(encoding='utf-8')
    existing = {line.strip() for line in content.splitlines()}
    missing = sorted(entries - existing)
    if missing:
        with path.open('a', encoding='utf-8') as file:
            if content and not content.endswith('\n'):
                file.write('\n')
            file.write('\n'.join(missing) + '\n')


def add_participants_7t_to_bids_json_file(
    bids_dataset_path: Path,
    bids_session: BidsSessionInfo,
    dicom_study_path: Path,
):
    """
    Create or update the `participants_7t_to_bids.tsv` file.
    """

    file_path = bids_dataset_path / 'participants_7t_to_bids.tsv'
    anat_count = _count_nifti_files(bids_dataset_path, bids_session, 'anat')
    dwi_count  = _count_nifti_files(bids_dataset_path, bids_session, 'dwi')
    func_count = _count_nifti_files(bids_dataset_path, bids_session, 'func')
    fmap_count = _count_nifti_files(bids_dataset_path, bids_session, 'fmap')

    print("Updating participants_7t_to_bids.tsv metadata...")

    time = bids_dataset_path.stat().st_mtime
    date_string = datetime.fromtimestamp(time).strftime('%Y-%m-%d')

    upsert_tsv_row(file_path, ('sub', 'ses'), {
        'sub': bids_session.subject,
        'ses': bids_session.session,
        'date': date_string,
        'N.anat': str(anat_count),
        'N.dwi': str(dwi_count),
        'N.func': str(func_count),
        'N.fmap': str(fmap_count),
        'dicoms': str(dicom_study_path),
        'user': getpass.getuser(),
    })


def _resolve_asset_file_path(file_name: str) -> Traversable:
    """
    Resolve a package static asset file path.
    """

    rel_file_path = Path('assets') / file_name
    return files('mni_7t_dicom_to_bids').joinpath(rel_file_path)


def _count_nifti_files(bids_dataset_path: Path, bids_session: BidsSessionInfo, scan_type_name: str) -> int:
    """
    Count the NIfTI files in a directory.
    """

    bids_scan_type_path = (
        bids_dataset_path
        / f'sub-{bids_session.subject}'
        / f'ses-{bids_session.session}'
        / scan_type_name
    )

    if not bids_scan_type_path.exists():
        return 0

    count = 0

    for file in os.scandir(bids_scan_type_path):
        if file.name.endswith('.nii.gz'):
            count += 1

    return count
