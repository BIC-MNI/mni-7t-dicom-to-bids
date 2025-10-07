import fnmatch

from mni_7t_dicom_to_bids.dataclass import BidsAcquisitionInfo, DicomBidsMapping, DicomSeriesInfo
from mni_7t_dicom_to_bids.variables import bids_dicom_ignores, bids_dicom_mappings


def map_bids_dicom_series(dicom_series_list: list[DicomSeriesInfo]) -> DicomBidsMapping:
    """
    Map the DICOM series of a DICOM study to BIDS acquisition mappings and unknown DICOM series
    according to the MNI 7T DICOM to BIDS converter configuration.
    """

    dicom_bids_mapping = DicomBidsMapping()

    for dicom_series in dicom_series_list:
        if ignore_dicom_series(dicom_series):
            dicom_bids_mapping.ignored_dicom_series_list.append(dicom_series)
            continue

        bids_acquisition = get_bids_acquisition_info(dicom_series)
        if bids_acquisition is not None:
            dicom_bids_mapping.bids_dicom_series_dict[bids_acquisition].append(dicom_series)
            continue

        dicom_bids_mapping.unknown_dicom_series_list.append(dicom_series)

    sort_dicom_bids_mapping(dicom_bids_mapping)

    return dicom_bids_mapping


def ignore_dicom_series(dicom_series: DicomSeriesInfo) -> bool:
    """
    Check if a DICOM series should be ignored as per the MNI 7T DICOM to BIDS converter parameters.
    """

    for bids_dicom_ignore in bids_dicom_ignores:
        if dicom_series.description == bids_dicom_ignore:
            return True

    return False


def get_bids_acquisition_info(dicom_series: DicomSeriesInfo) -> BidsAcquisitionInfo | None:
    """
    Return the BIDS parameters of a DICOM series as per the MNI 7T DICOM to BIDS converter
    conversion parameters.
    """

    for bids_scan_type, bids_dicom_mapping in bids_dicom_mappings.items():
        for bids_file_name, bids_dicom_series_descriptions in bids_dicom_mapping.items():
            if isinstance(bids_dicom_series_descriptions, str):
                bids_dicom_series_descriptions = [bids_dicom_series_descriptions]

            for bids_dicom_series_description in bids_dicom_series_descriptions:
                if fnmatch.fnmatch(dicom_series.description, bids_dicom_series_description):
                    return BidsAcquisitionInfo(
                        scan_type = bids_scan_type,
                        file_name = bids_file_name,
                    )

    return None


def sort_dicom_bids_mapping(dicom_bids_mapping: DicomBidsMapping):
    """
    Sort the DICOM series mappings gotten from the DICOM a study.
    """

    dicom_bids_mapping.bids_dicom_series_dict = {
        bids_acquisition: dicom_bids_mapping.bids_dicom_series_dict[bids_acquisition]
        for bids_acquisition
        in sorted(dicom_bids_mapping.bids_dicom_series_dict)
    }

    dicom_bids_mapping.ignored_dicom_series_list.sort()
    dicom_bids_mapping.unknown_dicom_series_list.sort()
