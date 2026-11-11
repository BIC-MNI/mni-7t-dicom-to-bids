import re
from pathlib import Path
from typing import cast

from bic_util.bids.dataset_description import read_dataset_description, write_dataset_description

from mni_7t_dicom_to_bids.dataclass import ConvertedScan


def patch_dataset_credits(dataset_path: Path, scans: list[ConvertedScan]):
    """Accumulate credits from successful conversions without replacing existing dataset metadata."""

    credits = list(dict.fromkeys(scan.credit for scan in scans if scan.credit is not None))
    if not credits:
        return

    description_path = dataset_path / 'dataset_description.json'
    description = read_dataset_description(description_path)
    acknowledgements = description.get('Acknowledgements', '')
    reference_value = description.get('ReferencesAndLinks', [])
    if not isinstance(acknowledgements, str):
        raise ValueError('Acknowledgements must be a string to merge sequence credits.')
    if not isinstance(reference_value, list):
        raise ValueError('ReferencesAndLinks must be an array of strings to merge sequence references.')
    references = cast(list[object], reference_value)
    if not all(isinstance(item, str) for item in references):
        raise ValueError('ReferencesAndLinks must be an array of strings to merge sequence references.')
    reference_urls = {
        url.rstrip('.,;')
        for item in references if isinstance(item, str)
        for url in re.findall(r'https?://\S+', item)
    }

    for credit in credits:
        if credit.acknowledgement not in acknowledgements.split('\n\n'):
            acknowledgements = '\n\n'.join(filter(None, (acknowledgements, credit.acknowledgement)))
        for reference in credit.references:
            if reference.url not in reference_urls:
                references.append(reference.render())
                reference_urls.add(reference.url)

    description['Acknowledgements'] = acknowledgements
    if references:
        description['ReferencesAndLinks'] = references
    write_dataset_description(description_path, description)
