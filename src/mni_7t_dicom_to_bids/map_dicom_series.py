import fnmatch

from mni_7t_dicom_to_bids.dataclass import BidsAcquisitionInfo, DicomBidsMapping, DicomSeriesInfo
from mni_7t_dicom_to_bids.dictionary import bids_dicom_mappings, ignored_dicom_series, ignored_dicom_series_suffixes


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

    for bids_dicom_ignore in ignored_dicom_series:
        if dicom_series.description == bids_dicom_ignore:
            return True

    return False


def get_bids_acquisition_info(dicom_series: DicomSeriesInfo) -> BidsAcquisitionInfo | None:
    """
    Return the BIDS parameters of a DICOM series as per the MNI 7T DICOM to BIDS converter
    conversion parameters.
    """

    # Remove the ignored suffix from the DICOM series description if there is any.
    trimmed_series_description = trim_series_description_suffix(dicom_series.description)

    for bids_scan_type, bids_dicom_mapping in bids_dicom_mappings.items():
        for bids_file_name, dicom_series_patterns in bids_dicom_mapping.items():
            # Convert the pattern to a list if there is a single pattern.
            if isinstance(dicom_series_patterns, str):
                dicom_series_patterns = [dicom_series_patterns]

            for dicom_series_pattern in dicom_series_patterns:
                if fnmatch.fnmatch(trimmed_series_description, dicom_series_pattern):
                    return BidsAcquisitionInfo(
                        scan_type = bids_scan_type,
                        file_name = bids_file_name,
                    )

    return None


def trim_series_description_suffix(series_descripton: str) -> str:
    """
    Trim a DICOM series description by removing an ignored suffix if any is found. The trimming is
    only applied once.
    """

    for ignored_suffix in ignored_dicom_series_suffixes:
        if series_descripton.endswith(ignored_suffix):
            return series_descripton.removesuffix(ignored_suffix)

    return series_descripton


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
