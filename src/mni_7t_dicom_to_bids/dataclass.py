import re
from collections import defaultdict
from dataclasses import dataclass, field
from re import Match, Pattern

from mni_7t_dicom_to_bids.variables import bids_label_order


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

    file_paths: list[str] = field(compare=False)
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


@dataclass
class DicomBidsMapping:
    """
    A mapping between a set of DICOM series and their BIDS acquisitions.
    """

    bids_dicom_series_dict: dict[BidsAcquisitionInfo, list[DicomSeriesInfo]] = field(
        default_factory=lambda: defaultdict(list)
    )
    """
    A mapping between the BIDS acquisitions and their DICOM series. Note that the BIDS acquisitions
    are mapped to their DICOM series and not the opposite because all the DICOM series of a BIDS
    acquisition need to be processed together in the conversion process.
    """

    ignored_dicom_series_list: list[DicomSeriesInfo] = field(default_factory=list[DicomSeriesInfo])
    """
    The ignored DICOM series.
    """

    unknown_dicom_series_list: list[DicomSeriesInfo] = field(default_factory=list[DicomSeriesInfo])
    """
    The unrecognized DICOM series.
    """


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


@dataclass
class BidsName:
    """
    Information about a BIDS file name.
    """

    entries: dict[str, str | None]
    """
    The labels and values of the BIDS name.
    """

    extension: str | None
    """
    The file extension of the BIDS name if there is one.
    """

    @staticmethod
    def from_string(name_string: str) -> 'BidsName':
        """
        Create a BIDS name object from a string.
        """

        # Get the BIDS name file extension if there is one.
        extension_index = name_string.find('.')
        if extension_index != -1:
            extension = name_string[extension_index + 1:]
            name_string = name_string[:extension_index]
        else:
            extension = None

        # Parse the BIDS name labels and values.
        entry_strings = name_string.split('_')
        entries: dict[str, str | None] = {}
        for entry_string in entry_strings:
            label_value = entry_string.split('-')
            label = label_value[0]
            try:
                value = label_value[1]
            except IndexError:
                value = None

            entries[label] = value

        return BidsName(entries, extension)

    def __str__(self) -> str:
        """
        Serialize the BIDS name object into a string.
        """

        # Get the BIDS labels and values and sort them according to the BIDS label order.
        entries = list(self.entries.items())
        entries.sort(key=lambda entry: _bids_label_key(entry[0]))

        # Serialize the BIDS labels and values in pairs.
        entry_strings: list[str] = []
        for label, value in entries:
            entry_string = label
            if value is not None:
                entry_string += f'-{value}'

            entry_strings.append(entry_string)

        # Combine the BIDS labels and values in a string.
        name_string = '_'.join(entry_strings)

        # Add the BIDS file extension if there is one.
        if self.extension is not None:
            name_string += f'.{self.extension}'

        return name_string

    def has(self, label: str) -> bool:
        """
        Check if the BIDS name has a given label.
        """

        return label in self.entries

    def has_value(self, label: str, value: str | None) -> bool:
        """
        Check if the BIDS name has a given label and value.
        """

        return label in self.entries and self.entries[label] == value

    def get(self, label: str) -> str | None:
        """
        Get the value associated with a label in the BIDS name.
        """

        return self.entries[label]

    def match(self, pattern: str | Pattern[str]) -> Match[str] | None:
        """
        Check if one of the BIDS name label matches a given regular expression.
        """

        for label in self.entries.keys():
            match = re.match(pattern, label)
            if match is not None:
                return match

        return None

    def add(self, label: str, value: str | None = None):
        """
        Add a label and its value in the BIDS name.
        """

        self.entries[label] = value

    def remove(self, label: str):
        """
        Remove a label and its value from the BIDS name.
        """

        self.entries.pop(label)


# A function to sort BIDS parts according to the BIDS label order.
def _bids_label_key(label: str):
    return _bids_label_order_map.get(label, len(_bids_label_order_map))


# Utility map to sort BIDS parts according to the BIDS label order.
_bids_label_order_map = {label: index for index, label in enumerate(bids_label_order)}
