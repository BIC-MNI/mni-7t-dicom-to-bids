from mni_7t_dicom_to_bids.dataclass import BidsAcquisitionInfo, DicomBidsMapping, DicomSeriesInfo
from mni_7t_dicom_to_bids.dictionary import DicomDictionary


def map_bids_dicom_series(
    dicom_series_list: list[DicomSeriesInfo],
    dictionary: DicomDictionary,
) -> DicomBidsMapping:
    """
    Map the DICOM series of a DICOM study to BIDS acquisition mappings and unknown DICOM series
    according to the MNI 7T DICOM to BIDS converter configuration.
    """

    dicom_bids_mapping = DicomBidsMapping()

    for dicom_series in dicom_series_list:
        if ignore_dicom_series(dicom_series, dictionary):
            dicom_bids_mapping.ignored_dicom_series_list.append(dicom_series)
            continue

        bids_acquisition = get_bids_acquisition_info(dicom_series, dictionary)
        if bids_acquisition is not None:
            dicom_bids_mapping.bids_dicom_series_dict[bids_acquisition].append(dicom_series)
            continue

        dicom_bids_mapping.unknown_dicom_series_list.append(dicom_series)

    sort_dicom_bids_mapping(dicom_bids_mapping)

    return dicom_bids_mapping


def ignore_dicom_series(dicom_series: DicomSeriesInfo, dictionary: DicomDictionary) -> bool:
    """
    Check if a DICOM series should be ignored as per the MNI 7T DICOM to BIDS converter parameters.
    """

    for ignored_series_regex in dictionary.ignored_series:
        if ignored_series_regex.fullmatch(dicom_series.description) is not None:
            return True

    return False


def get_bids_acquisition_info(
    dicom_series: DicomSeriesInfo,
    dictionary: DicomDictionary,
) -> BidsAcquisitionInfo | None:
    """
    Return the BIDS parameters of a DICOM series as per the MNI 7T DICOM to BIDS converter
    conversion parameters.
    """

    # Remove the ignored suffix from the DICOM series description if there is any.
    trimmed_series_description = trim_series_description_suffix(dicom_series.description, dictionary)

    for mapping in dictionary.mappings:
        if mapping.series_regex.fullmatch(trimmed_series_description) is not None:
            return BidsAcquisitionInfo(
                scan_type = mapping.datatype,
                file_name = mapping.filename,
            )

    return None


def trim_series_description_suffix(series_description: str, dictionary: DicomDictionary) -> str:
    """
    Trim a DICOM series description by removing an ignored suffix if any is found. The trimming is
    only applied once.
    """

    for ignored_suffix in dictionary.trim_series_suffixes:
        if series_description.endswith(ignored_suffix):
            return series_description.removesuffix(ignored_suffix)

    return series_description


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
