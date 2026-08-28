from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, order=True)
class DicomSeriesInfo:
    """
    Information about a DICOM series and its DICOM files found within a DICOM directory.
    """

    description: str
    """
    The DICOM series description.
    """

    number: int
    """
    The DICOM series number.
    """

    file_paths: list[Path] = field(compare=False)
    """
    The paths of the DICOM files of the series.
    """


@dataclass(frozen=True, order=True)
class BidsSessionInfo:
    """
    Information about a BIDS session directory.
    """

    subject: str
    """
    The BIDS subject label.
    """

    session: str
    """
    The BIDS session label.
    """


@dataclass(frozen=True, order=True)
class ConvertedScan:
    """
    A successfully converted scan.
    """

    image_path: Path


@dataclass
class ConversionResult:
    """
    A list of successfully converted scans.
    """

    scans: list[ConvertedScan] = field(default_factory=list[ConvertedScan])


@dataclass(frozen=True, order=True)
class BidsAcquisitionInfo:
    """
    Information about a BIDS acquisition directory.
    """

    scan_type: str
    """
    Name of the BIDS scan type of the acquisition.
    """

    file_name: str
    """
    Base name of the BIDS files of the acquisition.
    """


@dataclass(frozen=True, order=True)
class PlannedDicomSeries:
    """
    A DICOM series and its per-series conversion settings.
    """

    source: DicomSeriesInfo
    """
    The source DICOM series.
    """

    merge_images: bool = False
    """
    Whether dcm2niix should merge the images of the series into a single output.
    """


@dataclass
class PlannedAcquisition:
    """
    A BIDS acquisition and the DICOM series that will produce it.
    """

    bids: BidsAcquisitionInfo
    series: list[PlannedDicomSeries] = field(default_factory=list[PlannedDicomSeries])


@dataclass
class ConversionPlan:
    """
    The complete result of mapping discovered DICOM series to conversion work.
    """

    acquisitions: list[PlannedAcquisition] = field(default_factory=list[PlannedAcquisition])
    ignored_series: list[DicomSeriesInfo] = field(default_factory=list[DicomSeriesInfo])
    unknown_series: list[DicomSeriesInfo] = field(default_factory=list[DicomSeriesInfo])


@dataclass
class DicomSeriesConversionsCounter:
    """
    Counters about the DICOM series BIDS conversion process.
    """

    total: int
    """
    The total number of DICOM series to convert to BIDS.
    """

    successes: int = 0
    """
    The number of DICOM series that were successfully converted to BIDS.
    """

    errors: int = 0
    """
    The number of DICOM series that were not successfully converted to BIDS.
    """

    @property
    def count(self) -> int:
        """
        The number of the current DICOM series to convert to BIDS.
        """

        return self.successes + self.errors + 1
