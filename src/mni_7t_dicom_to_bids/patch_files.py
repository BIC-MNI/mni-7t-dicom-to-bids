import math
from pathlib import Path

from bic_util.fs import rename_file

from mni_7t_dicom_to_bids.dataclass import BidsName, DicomSeriesInfo
from mni_7t_dicom_to_bids.metadata.sidecar import patch_sidecar_metadata


def patch_files(acquisition_dir_path: Path, dicom_series: DicomSeriesInfo):
    """
    Patch the output BIDS files with the following:
    - Rename files to match the MNI 7T BIDS naming.
    - Delete superfluous files.
    - Add missing information to the JSON sidecar file.
    """

    for file_path in acquisition_dir_path.iterdir():
        patch_file_path(file_path)

    patch_sidecar_metadata(acquisition_dir_path, dicom_series)


def patch_file_path(file_path: Path):
    """
    Rename an output BIDS file to match the MNI 7T BIDS naming, or delete it if it is superfluous.
    """

    bids_name = BidsName.from_string(file_path.name)

    # Delete the bval and bvec files from MP2RAGE acquisitions.
    if bids_name.has('MP2RAGE') and (bids_name.extension == 'bval' or bids_name.extension == 'bvec'):
        print(f"Remove MP2RAGE bval/bvec file '{file_path.name}'")
        file_path.unlink()
        return

    # Delete the 'ROI1' files.
    if bids_name.has('ROI1'):
        print(f"Remove ROI file '{file_path.name}'")
        file_path.unlink()
        return

    # Replace 'e?' by 'echo-?'
    echo_match = bids_name.match(r'e(\d)')
    if echo_match is not None:
        bids_name.remove(echo_match.group(0))
        bids_name.add('echo', echo_match.group(1))

    # Remove 'run-?' from echo files (there can be several 'task-rest' runs per acquisition).
    if bids_name.has('echo') and bids_name.has('run') and not bids_name.has_value('task', 'rest'):
        bids_name.remove('run')

    # Remove 'run-?' from MTR files.
    if bids_name.has_value('acq', 'mtw') and bids_name.has('run'):
        bids_name.remove('run')

    # Replace 'ph' with 'part-phase'.
    if bids_name.has('ph'):
        bids_name.remove('ph')
        bids_name.add('part', 'phase')

    # Add 'part-mag' to T2 files with echo
    if bids_name.has('T2starw') and bids_name.has('echo') and not bids_name.has('part'):
        bids_name.add('part', 'mag')

    # Replace standalone 'T2starw' with 'T2starmap'.
    if (bids_name.has_value('acq', 'aspire') and bids_name.has('T2starw')
        and not bids_name.has('desc') and not bids_name.has('part') and not bids_name.has('rec')
    ):
        bids_name.remove('run')
        bids_name.remove('T2starw')
        bids_name.add('T2starmap')

    # Remove 'run-1' in 7T DWI acquisitions.
    if bids_name.has('dwi') and bids_name.has_value('run', '1'):
        bids_name.remove('run')

    # Replace 'run-2' with 'part-phase' in 7T DWI acquisitions.
    if bids_name.has('dwi') and bids_name.has_value('run', '2'):
        bids_name.remove('run')
        bids_name.add('part', 'phase')

    # Apply the TB1TFL-specific post processing.
    if bids_name.has('TB1TFL'):
        run_number = int(bids_name.get('run') or 0)
        acquisition_name = 'anat' if run_number % 2 == 1 else 'sfam'
        bids_name.add('acq', acquisition_name)
        bids_name.add('run', str(math.ceil(run_number / 2)))

    new_file_name = str(bids_name)

    # Rename the file on the system.
    if new_file_name != file_path.name:
        print(f"Renaming '{file_path.name}' to '{new_file_name}'.")
        rename_file(file_path, new_file_name)
