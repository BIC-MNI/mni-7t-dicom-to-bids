"""Identify MRI scanners from acquisition metadata."""

import json
from pathlib import Path

from bic_util.print import print_warning


def get_scanner(json_path: Path) -> str | None:
    """Identify the scanner from its JSON sidecar, or return None if unidentified."""

    with json_path.open() as file:
        metadata: dict[str, object] = json.load(file)

    model = metadata.get('ManufacturersModelName')
    software = metadata.get('SoftwareVersions')

    match model, software:
        case 'MAGNETOM Terra', _:
            return 'Siemens Terra 7T'
        case 'MAGNETOM Terra.X', _:
            return 'Siemens Terra.X 7T'
        case 'Investigational_Device_7T', 'syngo MR E12':
            return 'Siemens Terra 7T'
        case _, _:
            print_warning(
                f"Cannot identify scanner for '{json_path}': ManufacturersModelName={model!r},"
                f" SoftwareVersions={software!r}."
            )

            return None
