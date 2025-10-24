from mni_7t_dicom_to_bids.args import Args
from mni_7t_dicom_to_bids.convert_dicom_series import check_dicom_to_niix, convert_dicom_series
from mni_7t_dicom_to_bids.dataclass import BidsSessionInfo
from mni_7t_dicom_to_bids.dataset_files import add_dataset_files
from mni_7t_dicom_to_bids.group_dicom_series import group_dicom_series
from mni_7t_dicom_to_bids.map_dicom_series import map_bids_dicom_series
from mni_7t_dicom_to_bids.print import (
    print_found_dicom_series,
    print_found_ignored_dicom_series,
    print_found_mapped_bids_acquisitions,
    print_found_unknown_dicom_series,
    print_version,
)


def mni_7t_dicom_to_bids(args: Args):
    print_version()

    check_dicom_to_niix()

    dicom_series_list = group_dicom_series(args.dicom_study_path)

    print_found_dicom_series(dicom_series_list)

    dicom_bids_mapping = map_bids_dicom_series(dicom_series_list)

    print_found_mapped_bids_acquisitions(dicom_bids_mapping)

    print_found_ignored_dicom_series(dicom_bids_mapping)

    print_found_unknown_dicom_series(dicom_bids_mapping, args.unknowns)

    bids_session = BidsSessionInfo(
        subject = args.subject,
        session = args.session,
    )

    convert_dicom_series(bids_session, dicom_bids_mapping, args)

    if args.dataset_files:
        add_dataset_files(args.bids_dataset_path, bids_session, args.dicom_study_path, args.overwrite)
