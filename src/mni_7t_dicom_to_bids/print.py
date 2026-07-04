import os
from importlib.metadata import version
from pathlib import Path
from shlex import quote

from bic_util.print import print_error_exit, print_warning

from mni_7t_dicom_to_bids.args import AbortUnknownsArg, ConvertUnknownsArg, SkipUnknownsArg, UnknownsArg
from mni_7t_dicom_to_bids.dataclass import DicomBidsMapping, DicomSeriesInfo


def get_version() -> str:
    """
    Get the version of the current MNI 7T DICOM to BIDS package.
    """

    return version('mni_7t_dicom_to_bids')


def print_version():
    """
    Print the version of the current MNI 7T DICOM to BIDS package.
    """

    print(f"Running the MNI 7T DICOM to BIDS converter version {get_version()}.")


def print_found_dicom_series(dicom_series_list: list[DicomSeriesInfo]):
    """
    Print the DICOM series found in the DICOM study to the user.
    """

    print(f"Found {len(dicom_series_list)} DICOM series:")

    for dicom_series in dicom_series_list:
        print(
            f"- {quote(dicom_series.description)}"
            f" (series number: {dicom_series.number})"
            f" ({len(dicom_series.file_paths)} files)"
        )


def print_found_mapped_bids_acquisitions(dicom_bids_mapping: DicomBidsMapping):
    """
    Print the BIDS acquisition mappings found in the DICOM study to the user.
    """

    print(f"Found {len(dicom_bids_mapping.bids_dicom_series_dict)} BIDS acquisitions:")

    for bids_acquisition, dicom_series_list in dicom_bids_mapping.bids_dicom_series_dict.items():
        acquisition_name = f"{bids_acquisition.scan_type}/{bids_acquisition.file_name}"
        print(
            f"- {quote(acquisition_name)}"
            f" ({len(dicom_series_list)} DICOM series)"
        )


def print_found_ignored_dicom_series(dicom_bids_mapping: DicomBidsMapping):
    """
    Print the ignored DICOM series found in the DICOM study to the user.
    """

    ignored_dicom_series_list = dicom_bids_mapping.ignored_dicom_series_list
    if ignored_dicom_series_list == []:
        return

    dicom_series_list_string = ""
    for dicom_series in ignored_dicom_series_list:
        dicom_series_list_string += (
            "\n"
            f"- {quote(dicom_series.description)}"
            f" (series number: {dicom_series.number})"
            f" ({len(dicom_series.file_paths)} files)"
        )

    print(
        f"Found {len(ignored_dicom_series_list)} ignored DICOM series. Ignored DICOM series:{dicom_series_list_string}"
    )


def print_found_unknown_dicom_series(dicom_bids_mapping: DicomBidsMapping, unknowns_arg: UnknownsArg):
    """
    Print the unknown DICOM series found in the DICOM study to the user.
    """

    unknown_dicom_series_list = dicom_bids_mapping.unknown_dicom_series_list
    if unknown_dicom_series_list == []:
        return

    dicom_series_count_string = f"Found {len(unknown_dicom_series_list)} unknown DICOM series"
    dicom_series_list_string = "Unknown DICOM series:"
    for dicom_series in unknown_dicom_series_list:
        dicom_series_list_string += (
            "\n"
            f"- {quote(dicom_series.description)}"
            f" (series number: {dicom_series.number})"
            f" ({len(dicom_series.file_paths)} files)"
        )

    match unknowns_arg:
        case AbortUnknownsArg():
            print_error_exit(
                f"{dicom_series_count_string}, use option --skip-unknowns or --convert-unknowns to proceed"
                f" nonetheless.\n{dicom_series_list_string}"
            )
        case SkipUnknownsArg():
            print_warning(
                f"{dicom_series_count_string}, these series will be ignored.\n{dicom_series_list_string}"
            )
        case ConvertUnknownsArg():
            print_warning(
                f"{dicom_series_count_string}, these series will be converted in '{unknowns_arg.dir_path}'.\n"
                f"{dicom_series_list_string}"
            )


def print_existing_bids_files(existing_file_paths: list[Path], bids_data_type_path: Path, overwrite: bool):
    """
    Print the paths of existing BIDS files to the user if there are some, either directly if these
    files will be overwritten, or by throwing an exception with the appropriate message if this is
    an error.
    """

    if existing_file_paths == []:
        return

    existing_files_string = ""
    for existing_file_path in existing_file_paths:
        rel_file_path = os.path.relpath(existing_file_path, bids_data_type_path)
        existing_files_string += (
            "\n"
            f"- {quote(rel_file_path)}"
        )

    if overwrite:
        print_warning(
            f"Files already present in the BIDS directory, they will be overwritten.\nOverwritten BIDS files:"
            f"{existing_files_string}"
        )
    else:
        raise Exception(f"Files already exist in directory:{existing_files_string}")
