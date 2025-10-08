import math
import re
from pathlib import Path

import pydicom
from bic_util.fs import rename_file
from bic_util.json import update_json
from bic_util.print import print_warning

from mni_7t_dicom_to_bids.dataclass import BidsName, DicomSeriesInfo


def patch_files(acquisition_dir_path: Path, dicom_series: DicomSeriesInfo):
    """
    Patch the output BIDS files with the following:
    - Rename files to match the MNI 7T BIDS naming.
    - Delete superfluous files.
    - Add missing information to the JSON sidecar file.
    """

    for file_path in acquisition_dir_path.iterdir():
        patch_file_path(file_path)

    patch_json(acquisition_dir_path, dicom_series)


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
        and not bids_name.has('desc') and not bids_name.has('part')
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


def patch_json(acquisition_path: Path, dicom_series: DicomSeriesInfo):
    """
    Patch the generated BIDS JSON sidercar files with additional information.
    """

    # Add 'Units' to 'part-phase' scans.
    for json_path in acquisition_path.rglob('*part-phase*.json'):
        update_json(json_path, {
            'Units': 'rad',
        })

    # Add 'MTState' to 'mt-off' scans.
    for json_path in acquisition_path.rglob('*mt-off*.json'):
        update_json(json_path, {
            'MTState': False
        })

    # Add 'MTState' to 'mt-on' scans.
    for json_path in acquisition_path.rglob('*mt-on*.json'):
        update_json(json_path, {
            'MTState': True,
        })

    # Add 'MTFlipAngle' to the neuromelanin scans.
    for json_path in acquisition_path.rglob('*neuromelaninMTw*.json'):
        mt_flip_angle = get_mt_flip_angle(dicom_series)
        if mt_flip_angle is not None:
            update_json(json_path, {
                'MTFlipAngle': mt_flip_angle,
            })


def get_mt_flip_angle(dicom_series: DicomSeriesInfo) -> float | None:
    """
    Get the MT flip angle from a DICOM file of the series if it is present.
    """

    # Read a DICOM file from the DICOM series.
    dicom = pydicom.dcmread(dicom_series.file_paths[0])  # type: ignore

    # Get the Siemens CSA header of the DICOM file.
    csa_header = dicom.get((0x0029, 0x1020))
    if csa_header is None:  # type: ignore
        return

    # Get the MT flip angle attribute from the Siemens CSA header.
    mt_flip_angle_match = re.search(r'sWipMemBlock\.adFree\[2\]\\t = \\t(.+?)\\n', str(csa_header.value))
    if mt_flip_angle_match is None:
        return

    # Convert the MT flip angle from a string to a number.
    try:
        return float(mt_flip_angle_match[1])
    except ValueError:
        print_warning(f"Expected numeric MT flip angle but found value '{mt_flip_angle_match[1]}'.")
        return
