import json
import math
import re
from pathlib import Path

import pydicom
from bic_util.json import update_json
from bic_util.print import print_warning

from mni_7t_dicom_to_bids.dataclass import BidsName, DicomSeriesInfo

MP2RAGE_REPETITION_TIME_EXCITATION: dict[str, dict[float | None, float]] = {
    'anat-T1w_acq-mp2rage_0.7mm_CSptx': {None: 0.0078},
    'anat-T1w_acq-mp2rage_07mm_CSptx': {None: 0.0078},
    'anat-T1w_acq-mp2rage_05mm_UP': {0.00281: 0.0089, 0.00244: 0.0078},
    'anat-T1w_acq-mp2rage_05mm_UP_Repeat': {0.00281: 0.0089, 0.00244: 0.0078},
    'cstfl-mp2rage-05mm': {None: 0.0078},
}

MP2RAGE_PATCHED_FIELDS = (
    'RepetitionTimePreparation',
    'RepetitionTimeExcitation',
    'SlicesPerSlab',
    'NumberShots',
)


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

        if bids_name.has('MP2RAGE'):
            metadata.update(get_mp2rage_metadata(json_path, dicom_series))

        if metadata:
            update_json(json_path, metadata)


def get_mt_flip_angle(dicom_series: DicomSeriesInfo) -> float | None:
    """
    Get the MT flip angle from a DICOM file of the series if it is present.
    """

    csa_header = get_siemens_csa_header(dicom_series)
    if csa_header is None:
        return

    # Get the MT flip angle attribute from the Siemens CSA header.
    mt_flip_angle_match = re.search(r'sWipMemBlock\.adFree\[2\]\s*=\s*([^\r\n]+)', csa_header)
    if mt_flip_angle_match is None:
        return

    # Convert the MT flip angle from a string to a number.
    try:
        return float(mt_flip_angle_match[1])
    except ValueError:
        print_warning(f"Expected numeric MT flip angle but found value '{mt_flip_angle_match[1]}'.")
        return


def get_mp2rage_metadata(json_path: Path, dicom_series: DicomSeriesInfo) -> dict[str, object]:
    """
    Get MP2RAGE metadata that dcm2niix does not populate.

    Existing values are preserved because they may have been supplied by a newer dcm2niix release
    or an earlier processing step.
    """

    with json_path.open() as json_file:
        sidecar = json.load(json_file)

    metadata: dict[str, object] = {}

    for key in MP2RAGE_PATCHED_FIELDS:
        if key in sidecar:
            print_warning(
                f"Unexpected existing MP2RAGE metadata field '{key}' in '{json_path.name}'; preserving its value."
            )

    repetition_time = sidecar.get('RepetitionTime')
    if isinstance(repetition_time, int | float) and not isinstance(repetition_time, bool):
        metadata['RepetitionTimePreparation'] = repetition_time
    else:
        print_warning(f"Cannot populate RepetitionTimePreparation in '{json_path.name}': RepetitionTime is missing.")

    repetition_time_excitation = get_mp2rage_repetition_time_excitation(sidecar)
    if repetition_time_excitation is not None:
        metadata['RepetitionTimeExcitation'] = repetition_time_excitation
    else:
        print_warning(
            f"Cannot populate RepetitionTimeExcitation in '{json_path.name}' for ProtocolName "
            f"'{sidecar.get('ProtocolName')}' and EchoTime '{sidecar.get('EchoTime')}'."
        )

    slices_per_slab = get_slices_per_slab(dicom_series)
    if slices_per_slab is not None:
        metadata['SlicesPerSlab'] = slices_per_slab
    else:
        print_warning(f"Cannot populate SlicesPerSlab in '{json_path.name}' from the Siemens CSA header.")

    partial_fourier = sidecar.get('PartialFourier')
    if (
        slices_per_slab is not None
        and isinstance(partial_fourier, int | float)
        and not isinstance(partial_fourier, bool)
    ):
        metadata['NumberShots'] = [
            slices_per_slab * (partial_fourier - 0.5),
            slices_per_slab * 0.5,
        ]
    elif slices_per_slab is not None:
        print_warning(f"Cannot populate NumberShots in '{json_path.name}': PartialFourier is missing.")

    return {key: value for key, value in metadata.items() if key not in sidecar}


def get_mp2rage_repetition_time_excitation(sidecar: dict[str, object]) -> float | None:
    """
    Get RepetitionTimeExcitation from the acquisition protocol lookup table.
    """

    protocol_name = sidecar.get('ProtocolName')
    if not isinstance(protocol_name, str):
        return None

    protocol_values = MP2RAGE_REPETITION_TIME_EXCITATION.get(protocol_name)
    if protocol_values is None:
        return None

    fixed_value = protocol_values.get(None)
    if fixed_value is not None:
        return fixed_value

    echo_time = sidecar.get('EchoTime')
    if not isinstance(echo_time, int | float) or isinstance(echo_time, bool):
        return None

    for expected_echo_time, repetition_time_excitation in protocol_values.items():
        if expected_echo_time is not None and math.isclose(echo_time, expected_echo_time, abs_tol=0.000005):
            return repetition_time_excitation

    return None


def get_slices_per_slab(dicom_series: DicomSeriesInfo) -> int | None:
    """
    Get SlicesPerSlab from the Siemens CSA header of a DICOM file in the series.
    """

    csa_header = get_siemens_csa_header(dicom_series)
    if csa_header is None:
        return None

    match = re.search(r'sKSpace\.lImagesPerSlab\s*=\s*(\d+)', csa_header)
    if match is None:
        return None

    return int(match[1])


def get_siemens_csa_header(dicom_series: DicomSeriesInfo) -> str | None:
    """
    Read the Siemens CSA header from a DICOM file in the series.
    """

    dicom = pydicom.dcmread(dicom_series.file_paths[0], stop_before_pixels=True)  # type: ignore
    csa_header = dicom.get((0x0029, 0x1020))
    if csa_header is None:  # type: ignore
        return None

    value = csa_header.value
    if isinstance(value, bytes):
        return value.decode('latin-1')

    return str(value)
