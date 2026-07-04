from pathlib import Path

import pydicom
from bic_util.fs import count_all_dir_files, iter_all_dir_files
from bic_util.print import get_progress_printer, print_error_exit
from bic_util.util import find
from pydicom.errors import InvalidDicomError

from mni_7t_dicom_to_bids.dataclass import DicomSeriesInfo


def group_dicom_series(dicom_dir_path: Path) -> list[DicomSeriesInfo]:
    """
    Read a DICOM directory and group all the DICOM files according to their series description and
    series number.
    """

    print("Grouping DICOMs by DICOM series...")

    files_count = count_all_dir_files(dicom_dir_path)

    progress = get_progress_printer(files_count)

    dicom_series_entries: list[DicomSeriesInfo] = []

    for dicom_file_rel_path in iter_all_dir_files(dicom_dir_path):
        next(progress)

        dicom_file_path = dicom_dir_path / dicom_file_rel_path

        try:
            dicom = pydicom.dcmread(dicom_file_path)  # type: ignore
        except InvalidDicomError:
            print_error_exit(f"Could not read file '{dicom_file_path}', this file may not be a DICOM file.")

        try:
            series_description = dicom.SeriesDescription
        except AttributeError:
            print_error_exit(
                f"Could not read series description of DICOM file '{dicom_file_path}', this file may be incorrect."
            )

        try:
            series_number = dicom.SeriesNumber
        except AttributeError:
            print_error_exit(
                f"Could not read series number of DICOM file '{dicom_file_path}', this file may be incorrect."
            )

        dicom_series = find(
            lambda dicom_series: (
                dicom_series.description == series_description
                and dicom_series.number == series_number
            ),
            dicom_series_entries,
        )

        if dicom_series is None:
            dicom_series = DicomSeriesInfo(
                description = series_description,
                number      = series_number,
                file_paths  = [],
            )

            dicom_series_entries.append(dicom_series)

        dicom_series.file_paths.append(dicom_file_path)

        # TODO: Handle session numbers.

    dicom_series_entries.sort()

    return dicom_series_entries
