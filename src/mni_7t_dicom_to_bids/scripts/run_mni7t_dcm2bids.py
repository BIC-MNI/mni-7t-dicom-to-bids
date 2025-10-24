#!/usr/bin/env python

import argparse

from bic_util.fs import require_empty_directory, require_output_directory, require_readable_directory

from mni_7t_dicom_to_bids.args import ConvertUnknownsArg, process_args
from mni_7t_dicom_to_bids.pipeline import mni_7t_dicom_to_bids
from mni_7t_dicom_to_bids.print import get_version


def main():
    # Parse CLI arguments.

    parser = argparse.ArgumentParser(
        prog='mni7t_dcm2bids',
        description="Convert a DICOM study to BIDS using the MNI 7T conversion configuration.",
    )

    parser.add_argument('--version',
        action='version',
        version=get_version(),
        help="Print the MNI 7T DICOM to BIDS converter version number and exit.")

    parser.add_argument('dicom_study_path',
        help="Path of the input DICOM study directory.")

    parser.add_argument('bids_dataset_path',
        help="Path of the output BIDS dataset directory.")

    parser.add_argument('--subject',
        required=True,
        help="The BIDS subject label of that study.")

    parser.add_argument('--session',
        required=True,
        help="The BIDS session label of that study.")

    parser.add_argument('--skip-unknowns',
        action='store_true',
        help="Skip unrecognized DICOM series if there are some. Cannot be used with --convert-unkowns.")

    parser.add_argument('--convert-unknowns',
        help=(
            "Convert unrecognized DICOM series to this directory path if there are some. Cannot be used with"
            " --skip-unknowns."
        ))

    parser.add_argument('--include-errors',
        action='store_true',
        help="Include BIDS files even if dcm2niix returned an error during the conversion.")

    parser.add_argument('--dataset-files',
        action='store_true',
        help="Generate some static dataset files for the BIDS dataset.")

    parser.add_argument('--overwrite',
        action='store_true',
        help="Overwrite files in the BIDS dataset if they already exist.")

    # Process CLI arguments.

    args = process_args(parser.parse_args())

    require_readable_directory(args.dicom_study_path)
    require_output_directory(args.bids_dataset_path)

    if isinstance(args.unknowns, ConvertUnknownsArg):
        require_output_directory(args.unknowns.dir_path)
        require_empty_directory(args.unknowns.dir_path)

    # Run the script.

    mni_7t_dicom_to_bids(args)

    print('Success !')


if __name__ == '__main__':
    main()
