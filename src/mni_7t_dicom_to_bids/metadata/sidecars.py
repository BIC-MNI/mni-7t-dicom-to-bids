"""Merge packaged column definitions into dataset-level JSON sidecars."""

import json
from importlib.resources import files
from pathlib import Path


def update_json_from_asset(dataset_path: Path, file_name: str, *, overwrite: bool = True):
    """Merge asset definitions, preserving unrelated columns and optionally existing definitions."""

    asset = files('mni_7t_dicom_to_bids').joinpath('assets').joinpath(file_name)
    with asset.open(encoding='utf-8') as file:
        definitions: dict[str, object] = json.load(file)

    json_path = dataset_path / file_name
    metadata: dict[str, object] = {}
    if json_path.exists():
        with json_path.open(encoding='utf-8') as file:
            metadata = json.load(file)

    for column, definition in definitions.items():
        if overwrite or column not in metadata:
            metadata[column] = definition

    with json_path.open('w', encoding='utf-8') as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)
        file.write('\n')
