import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from shlex import quote

from bic_util.print import print_error, print_error_exit, print_warning, with_print_subscript

from mni_7t_dicom_to_bids.args import Args, ConvertUnknownsArg, IncludeErrorsArg, SkipErrorsArg
from mni_7t_dicom_to_bids.dataclass import (
    BidsAcquisitionInfo,
    BidsName,
    BidsSessionInfo,
    ConversionPlan,
    ConversionResult,
    ConvertedScan,
    DicomSeriesConversionsCounter,
    DicomSeriesInfo,
)
from mni_7t_dicom_to_bids.patch_files import patch_files
from mni_7t_dicom_to_bids.print import print_existing_bids_files


def check_dicom_to_niix():
    """
    Check that the `dcm2niix` command is accessible, or exit the program with an error if that is
    not the case.
    """

    print("Checking `dcm2niix` availability...")

    if shutil.which('dcm2niix') is None:
        print_error_exit(
            "`dcm2niix` does not look installed or accessible on this machine. Please install"
            " `dcm2niix` before running the MNI 7T DICOM to BIDS converter."
        )


def convert_dicom_series(
    bids_session: BidsSessionInfo,
    conversion_plan: ConversionPlan,
    args: Args,
) -> ConversionResult:
    """
    Convert the mapped BIDS acquisitions and DICOM series to NIfTI.
    """

    print('Converting DICOM series to NIfTI...')

    counter = get_conversions_counter(conversion_plan, args)
    result = ConversionResult()

    for planned_acquisition in conversion_plan.acquisitions:
        bids_acquisition = planned_acquisition.bids
        for run_number, planned_series in enumerate(planned_acquisition.series, 1):
            dicom_series = planned_series.source
            print(
                f"Processing BIDS acquisition '{bids_acquisition.scan_type}/{bids_acquisition.file_name}'"
                f" ({counter.count} / {counter.total})."
            )

            if len(planned_acquisition.series) == 1:
                run_number = None

            bids_data_type_path = get_bids_data_type_dir_path(args.bids_dataset_path, bids_session, bids_acquisition)

            image_paths = run_conversion_function(
                dicom_series,
                bids_data_type_path,
                counter,
                lambda tmp_dicom_dir_path, tmp_output_path: convert_bids_dicom_series(
                    dicom_series,
                    bids_session,
                    bids_acquisition,
                    bids_data_type_path,
                    run_number,
                    args,
                    tmp_dicom_dir_path,
                    tmp_output_path,
                    merge_images=planned_series.merge_images,
                )
            )

            result.scans.extend(
                ConvertedScan(path)
                for path in image_paths
                if path.name.endswith(('.nii', '.nii.gz'))
            )

    if isinstance(args.unknowns, ConvertUnknownsArg):
        for unknown_dicom_series in conversion_plan.unknown_series:
            print(
                f"Processing unknown DICOM series '{unknown_dicom_series.description}'"
                f" ({counter.count} / {counter.total})."
            )

            run_conversion_function(
                unknown_dicom_series,
                args.unknowns.dir_path,
                counter,
                lambda tmp_dicom_dir_path, tmp_output_dir_path: convert_unknown_dicom_series(
                    unknown_dicom_series, tmp_dicom_dir_path, tmp_output_dir_path, args
                ),
            )

    print(
        f"Processed {counter.total} DICOM series, including {counter.successes} successful conversions to BIDS and"
        f" {counter.errors} errors."
    )

    return result


def get_conversions_counter(conversion_plan: ConversionPlan, args: Args) -> DicomSeriesConversionsCounter:
    """
    Get the total number of conversions needed to convert the BIDS acquisitions to NIfTI.
    """

    total = 0

    # Add the count of DICOM series for each BIDS acquisition.
    for planned_acquisition in conversion_plan.acquisitions:
        total += len(planned_acquisition.series)

    # Add the unrecognized DICOM series if the script is configured to convert them.
    if isinstance(args.unknowns, ConvertUnknownsArg):
        total += len(conversion_plan.unknown_series)

    return DicomSeriesConversionsCounter(total)


def convert_bids_dicom_series(
    dicom_series: DicomSeriesInfo,
    bids_session: BidsSessionInfo,
    bids_acquisition: BidsAcquisitionInfo,
    bids_data_type_path: Path,
    run_number: int | None,
    args: Args,
    tmp_dicom_dir_path: Path,
    tmp_output_dir_path: Path,
    *,
    merge_images: bool = False,
):
    """
    Convert an unknown DICOM series to NIfTI.
    """

    file_name = get_bids_acquisition_file_name(bids_session, bids_acquisition.file_name, run_number)

    run_dicom_to_niix(
        tmp_dicom_dir_path,
        tmp_output_dir_path,
        file_name,
        args,
        merge_images=merge_images,
    )

    patch_files(Path(tmp_output_dir_path), dicom_series)

    # Check if the files already exist in the target directory.

    existing_file_paths = get_existing_bids_file_paths(tmp_output_dir_path, bids_data_type_path)

    print_existing_bids_files(existing_file_paths, bids_data_type_path, args.overwrite)

    for existing_file_path in existing_file_paths:
        existing_file_path.unlink()


def get_existing_bids_file_paths(tmp_output_dir_path: Path, bids_data_type_path: Path) -> list[Path]:
    """
    Get the paths of the files from a completedDICOM series conversion that already exist in the
    BIDS dataset.
    """

    existing_file_paths: list[Path] = []

    for file in os.scandir(tmp_output_dir_path):
        output_file_path = bids_data_type_path / file.name
        if output_file_path.exists():
            existing_file_paths.append(output_file_path)

    return existing_file_paths


def convert_unknown_dicom_series(
    unknown_dicom_series: DicomSeriesInfo,
    tmp_dicom_dir_path: Path,
    tmp_output_dir_path: Path,
    args: Args,
):
    """
    Convert an unknown DICOM series to NIfTI.
    """

    file_name = unknown_dicom_series.description

    # Remove invalid characters.
    file_name = re.sub(r'[^\w\s-]', '', file_name)
    # Replace whitespaces.
    file_name = re.sub(r'[-\s]+', '_', file_name)
    # Prepend series number to disambiguate series runs.
    file_name = f'{unknown_dicom_series.number}_{file_name}'

    run_dicom_to_niix(tmp_dicom_dir_path, tmp_output_dir_path, file_name, args)


def run_conversion_function(
    dicom_series: DicomSeriesInfo,
    output_dir_path: Path,
    counter: DicomSeriesConversionsCounter,
    convert: Callable[[Path, Path], None],
) -> list[Path]:
    """
    Run the DICOM to NIfTI conversion function with temporary input and output directories, handle
    file copies, and recover from errors.
    """

    try:
        with tempfile.TemporaryDirectory() as tmp_dicom_dir_path:
            # Copy the DICOM files of the DICOM series in the temporary input directory.
            for dicom_file_path in dicom_series.file_paths:
                shutil.copy(dicom_file_path, tmp_dicom_dir_path)

            with tempfile.TemporaryDirectory() as tmp_output_dir_path:
                convert(Path(tmp_dicom_dir_path), Path(tmp_output_dir_path))

                # Move the output files to their final directory.
                image_paths: list[Path] = []
                for file in os.scandir(tmp_output_dir_path):
                    image_path = output_dir_path / file.name
                    shutil.move(file.path, image_path)
                    image_paths.append(image_path)

            counter.successes += 1
            return image_paths
    except Exception as error:
        print_error(str(error))
        counter.errors += 1
        return []


def run_dicom_to_niix(
    dicom_dir_path: Path,
    output_dir_path: Path,
    file_name: str,
    args: Args,
    *,
    merge_images: bool = False,
):
    """
    Run `dcm2niix` on a DICOM series run the post-processings on the result.
    """

    command = [
        'dcm2niix',
        '-z', 'y', '-b', 'y',
    ]

    if merge_images:
        command.extend(('-m', 'y'))

    command.extend((
        '-o', str(output_dir_path),
        '-f', file_name,
        str(dicom_dir_path),
    ))

    print(f"Running dcm2niix with command: '{' '.join(command)}'.")

    process = with_print_subscript(lambda: subprocess.run(command))

    if process.returncode != 0:
        match args.errors:
            case SkipErrorsArg():
                raise Exception(
                    f"dcm2niix exited with the non-zero exit code {process.returncode}. Files will not be copied to the"
                    " BIDS dataset."
                )
            case IncludeErrorsArg():
                print_warning(
                    f"dcm2niix exited with the non-zero exit code {process.returncode}. Files will nonetheless be"
                    " copied to the BIDS dataset."
                )

    print("Generated the following files for this series:")

    for file in os.scandir(output_dir_path):
        print(f"- {quote(file.name)}")


def get_bids_data_type_dir_path(
    bids_dataset_path: Path,
    bids_session: BidsSessionInfo,
    bids_acquisition: BidsAcquisitionInfo,
) -> Path:
    """
    Get the path of a BIDS data type directory, and create this directory if it does not already
    exist.
    """

    bids_data_type_path = (
        bids_dataset_path
        / f'sub-{bids_session.subject}'
        / f'ses-{bids_session.session}'
        / bids_acquisition.scan_type
    )

    bids_data_type_path.mkdir(parents=True, exist_ok=True)
    return bids_data_type_path


def get_bids_acquisition_file_name(bids_session: BidsSessionInfo, base_name: str, run_number: int | None) -> str:
    """
    Get the full BIDS file name of a BIDS acquisition.
    """

    bids_name = BidsName.from_string(base_name)

    # Add the subject and session labels.
    bids_name.add('sub', bids_session.subject)
    bids_name.add('ses', bids_session.session)

    # Add a run number if there are several DICOM series for the BIDS acquisition.
    if run_number is not None:
        bids_name.add('run', str(run_number))

    return str(bids_name)
