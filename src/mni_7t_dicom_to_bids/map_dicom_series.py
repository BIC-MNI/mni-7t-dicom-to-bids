from collections import defaultdict

from mni_7t_dicom_to_bids.dataclass import (
    BidsAcquisitionInfo,
    ConversionPlan,
    DicomSeriesInfo,
    PlannedAcquisition,
    PlannedDicomSeries,
)
from mni_7t_dicom_to_bids.dictionary import DicomDictionary, SeriesMapping


def create_conversion_plan(
    dicom_series_list: list[DicomSeriesInfo],
    dictionary: DicomDictionary,
) -> ConversionPlan:
    """
    Map the DICOM series of a DICOM study to BIDS acquisition mappings and unknown DICOM series
    according to the MNI 7T DICOM to BIDS converter configuration.
    """

    acquisition_series: dict[BidsAcquisitionInfo, list[PlannedDicomSeries]] = defaultdict(list)
    ignored_series: list[DicomSeriesInfo] = []
    unknown_series: list[DicomSeriesInfo] = []

    for dicom_series in dicom_series_list:
        if ignore_dicom_series(dicom_series, dictionary):
            ignored_series.append(dicom_series)
            continue

        series_mapping = get_series_mapping(dicom_series, dictionary)
        if series_mapping is not None:
            bids_acquisition = BidsAcquisitionInfo(
                scan_type = series_mapping.datatype,
                file_name = series_mapping.filename,
            )

            acquisition_series[bids_acquisition].append(
                PlannedDicomSeries(source=dicom_series, merge_images=series_mapping.merge_images)
            )

            continue

        unknown_series.append(dicom_series)

    return ConversionPlan(
        acquisitions=[
            PlannedAcquisition(bids=bids_acquisition, series=acquisition_series[bids_acquisition])
            for bids_acquisition in sorted(acquisition_series)
        ],
        ignored_series=sorted(ignored_series),
        unknown_series=sorted(unknown_series),
    )


def ignore_dicom_series(dicom_series: DicomSeriesInfo, dictionary: DicomDictionary) -> bool:
    """
    Check if a DICOM series should be ignored as per the MNI 7T DICOM to BIDS converter parameters.
    """

    for ignored_series_regex in dictionary.ignored_series:
        if ignored_series_regex.fullmatch(dicom_series.description) is not None:
            return True

    return False


def get_series_mapping(
    dicom_series: DicomSeriesInfo,
    dictionary: DicomDictionary,
) -> SeriesMapping | None:
    """Return the dictionary mapping matching a DICOM series, if one exists."""

    # Remove the ignored suffix from the DICOM series description if there is any.
    trimmed_series_description = trim_series_description_suffix(dicom_series.description, dictionary)

    for mapping in dictionary.mappings:
        if mapping.series_regex.fullmatch(trimmed_series_description) is not None:
            return mapping

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
