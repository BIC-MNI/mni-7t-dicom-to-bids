import re
from pathlib import Path

import pydicom
from bic_util.json import update_json
from bic_util.print import print_warning

from mni_7t_dicom_to_bids.dataclass import BidsName, DicomSeriesInfo


def patch_sidecar_metadata(acquisition_path: Path, dicom_series: DicomSeriesInfo):
    """
    Patch generated BIDS JSON sidecars with additional metadata.
    """

    for json_path in acquisition_path.rglob('*.json'):
        bids_name = BidsName.from_string(json_path.name)
        metadata: dict[str, object] = {}

        if bids_name.has_value('part', 'phase'):
            metadata['Units'] = 'rad'

        if bids_name.has_value('mt', 'off'):
            metadata['MTState'] = False

        if bids_name.has_value('mt', 'on'):
            metadata['MTState'] = True

        if bids_name.has_value('acq', 'neuromelaninMTw'):
            mt_flip_angle = get_mt_flip_angle(dicom_series)
            if mt_flip_angle is not None:
                metadata['MTFlipAngle'] = mt_flip_angle

        if bids_name.has('task'):
            task_name = bids_name.get('task')
            if task_name is not None:
                metadata['TaskName'] = task_name

        if metadata:
            update_json(json_path, metadata)


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
