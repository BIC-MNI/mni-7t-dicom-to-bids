import filecmp
import getpass
import os
import shutil
from datetime import datetime
from importlib.abc import Traversable
from importlib.resources import as_file, files
from pathlib import Path

from bic_util.print import print_error_exit, print_warning

from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo


def add_dataset_files(bids_dataset_path: Path, bids_session: BidsSessionInfo, dicom_study_path: Path, overwrite: bool):
    """
    Add the auxiliary dataset files to the output BIDS directory.
    """

    print("Creating auxiliary files...")

    add_static_dataset_files(bids_dataset_path, overwrite)

    add_participants_7t_to_bids_json_file(bids_dataset_path, bids_session, dicom_study_path)

    add_participants_tsv_file(bids_dataset_path, bids_session)

    add_sessions_tsv_file(bids_dataset_path, bids_session)


def add_static_dataset_files(bids_dir_path: Path, overwrite: bool):
    """
    Copy the static dataset files into the BIDS directory. The files are copied only if they do not
    exist in the BIDS directory, or if they exist and are changed but can be overwritten. Exit the
    program with an error if some file exists and is changed but cannot be overwritten.
    """

    # Copy the static dataset files.
    for file_name in ['.bidsignore', 'participants.json']:
        with as_file(_resolve_asset_file_path(file_name)) as new_file_path:
            old_file_path = bids_dir_path / file_name

            if not old_file_path.exists():
                print(f"File '{file_name}' does not exist in the BIDS directory. Creating...")
            else:
                if filecmp.cmp(old_file_path, new_file_path, shallow=False):
                    print(f"File '{file_name}' already exists in the BIDS directory and is unchanged. Skipping.")
                    continue

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


def add_participants_7t_to_bids_json_file(
    bids_dataset_path: Path,
    bids_session: BidsSessionInfo,
    dicom_study_path: Path,
):
    """
    Create or update the `participants_7t_to_bids.tsv` file.
    """

    file_path = bids_dataset_path / 'participants_7t_to_bids.tsv'
    if file_path.exists():
        print("File 'participants_7t_to_bids.tsv' already exists.")
    else:
        print("Creating file 'participants_7t_to_bids.tsv'...")
        with file_path.open('w') as file:
            file.write("sub\tses\tdate\tN.anat\tN.dwi\tN.func\tN.fmap\tdicoms\tuser\n")

    anat_count = _count_nifti_files(bids_dataset_path, bids_session, 'anat')
    dwi_count  = _count_nifti_files(bids_dataset_path, bids_session, 'dwi')
    func_count = _count_nifti_files(bids_dataset_path, bids_session, 'func')
    fmap_count = _count_nifti_files(bids_dataset_path, bids_session, 'fmap')

    print("Appending session to file 'participants_7t_to_bids.tsv'...")

    time = bids_dataset_path.stat().st_mtime
    date_string = datetime.fromtimestamp(time).strftime('%Y-%m-%d')

    with file_path.open('a') as file:
        file.write(
            f"{bids_session.subject}\t{bids_session.session}\t{date_string}\t"
            f"{anat_count}\t{dwi_count}\t{func_count}\t{fmap_count}\t{dicom_study_path}\t{getpass.getuser()}\n"
        )


def add_participants_tsv_file(bids_dataset_path: Path, bids_session: BidsSessionInfo):
    """
    Create or update the `participants.tsv` BIDS file.
    """

    file_path = bids_dataset_path / 'participants.tsv'
    if file_path.exists():
        print("File 'participants.tsv' already exists.")
    else:
        print("Creating file 'participants.tsv'...")
        with file_path.open('w') as file:
            file.write("participant_id\tsite\n")

    print("Appending session to file 'participants.tsv'...")

    with file_path.open('a') as file:
        file.write(f"sub-{bids_session.subject}\tMontreal_SiemmensTerra7T\n")


def add_sessions_tsv_file(bids_dataset_path: Path, bids_session: BidsSessionInfo):
    """
    Create or update the `sub-XXX_sessions.tsv` BIDS file.
    """

    file_name = f'sub-{bids_session.subject}_sessions.tsv'
    file_path = bids_dataset_path / f'sub-{bids_session.subject}' / file_name

    if file_path.exists():
        print(f"File '{file_name}' already exists.")
    else:
        print(f"Creating file '{file_name}'...")
        with file_path.open('w') as file:
            file.write('session_id\n')

    print(f"Appending session to file '{file_name}'...")

    with file_path.open('a') as file:
        file.write(f'ses-{bids_session.session}\n')


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
