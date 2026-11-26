import json
import math
from pathlib import Path

from bic_util.bids.name import BidsName
from bic_util.fs import rename_file

from mni_7t_dicom_to_bids.dataclass import ConvertedScan, DicomSeriesInfo
from mni_7t_dicom_to_bids.metadata.sidecar import patch_sidecar_metadata
from mni_7t_dicom_to_bids.print import print_existing_bids_files


def get_magnitude_phase_renames(scans: list[ConvertedScan]) -> dict[Path, Path]:
    """Pair components by filename entities and acquisition time, retaining magnitude run labels."""

    groups: dict[tuple[Path, str, str | None], tuple[list[Path], list[Path]]] = {}
    for scan in scans:
        path = scan.image_path
        name = BidsName.from_string(path.name)
        part = name.entries.pop('part', None)
        if part not in (None, 'mag', 'phase'):
            continue

        json_path = path.with_name(path.name.removesuffix('.gz')).with_suffix('.json')
        with json_path.open() as file:
            metadata: dict[str, object] = json.load(file)

        image_type = metadata.get('ImageType', [])
        if part != 'phase':
            if not isinstance(image_type, list):
                continue
            # Siemens diffusion sidecars may omit M/P; the matching part-phase identifies the other component.
            diffusion = name.has('dwi') and 'DIFFUSION' in image_type and 'P' not in image_type
            if 'M' not in image_type and not diffusion:
                continue

        acquisition_time = metadata.get('AcquisitionTime')
        if isinstance(acquisition_time, str):
            name.entries.pop('run', None)
        else:
            acquisition_time = None
        magnitudes, phases = groups.setdefault((path.parent, str(name), acquisition_time), ([], []))
        (phases if part == 'phase' else magnitudes).append(path)

    renames: dict[Path, Path] = {}
    for magnitudes, phases in groups.values():
        if not magnitudes or not phases:
            continue
        if len(magnitudes) != 1 or len(phases) != 1:
            raise ValueError(f"Ambiguous magnitude/phase pairing: {magnitudes}, {phases}")

        name = BidsName.from_string(magnitudes[0].name)
        for source, part in [(magnitudes[0], 'mag'), (phases[0], 'phase')]:
            name.add('part', part)
            target = source.with_name(str(name))
            if source != target:
                renames[source] = target
    return renames


def patch_frequency_maps(scans: list[ConvertedScan], *, overwrite: bool = False) -> dict[Path, Path]:
    """Remove part-phase from frequency maps using their final JSON sidecar units."""

    renamed_images: dict[Path, Path] = {}
    for scan in scans:
        path = scan.image_path
        name = BidsName.from_string(path.name)
        if not name.has_value('part', 'phase'):
            continue

        json_path = path.with_name(path.name.removesuffix('.gz')).with_suffix('.json')
        with json_path.open() as file:
            metadata: dict[str, object] = json.load(file)
        if metadata.get('Units') == 'Hz':
            name.remove('part')
            renamed_images[path] = path.with_name(str(name))

    rename_image_files(renamed_images, overwrite=overwrite)
    return renamed_images


def patch_magnitude_counterparts(scans: list[ConvertedScan], *, overwrite: bool = False) -> dict[Path, Path]:
    """Label magnitude counterparts and align phase run labels; return the renamed image paths."""

    renamed_images = get_magnitude_phase_renames(scans)
    rename_image_files(renamed_images, overwrite=overwrite)
    return renamed_images


def patch_singleton_runs(scans: list[ConvertedScan], *, overwrite: bool = False) -> dict[Path, Path]:
    """Remove singleton run labels across components and echoes of affected acquisition groups.

    Include existing images in the same directories, so partial conversions neither strip real
    repeat labels nor leave other components of a singleton run behind. Runless destinations
    are handled by the usual collision checks, including overwrite on repeated conversions.
    """

    def group_key(path: Path) -> tuple[Path, str]:
        name = BidsName.from_string(path.name)
        for entity in ('run', 'part', 'echo'):
            name.entries.pop(entity, None)
        name.extension = None
        return path.parent, str(name)

    affected_groups = {group_key(scan.image_path) for scan in scans}
    groups: dict[tuple[Path, str], list[Path]] = {}
    for directory in sorted({scan.image_path.parent for scan in scans}):
        for path in sorted(directory.iterdir()):
            if not path.name.endswith(('.nii', '.nii.gz')) or not path.is_file():
                continue
            key = group_key(path)
            if key in affected_groups:
                groups.setdefault(key, []).append(path)

    renamed_images: dict[Path, Path] = {}
    for paths in groups.values():
        runs = {BidsName.from_string(path.name).entries.get('run') for path in paths}
        runs.discard(None)
        if len(runs) != 1:
            continue
        for path in paths:
            name = BidsName.from_string(path.name)
            if name.has('run'):
                name.remove('run')
                renamed_images[path] = path.with_name(str(name))

    rename_image_files(renamed_images, overwrite=overwrite)
    return renamed_images


def rename_image_files(renamed_images: dict[Path, Path], *, overwrite: bool = False):
    """Apply image renames to all associated files, checking destinations first."""

    renamed_files: dict[Path, Path] = {}
    for source, target in renamed_images.items():
        json_path = source.with_name(source.name.removesuffix('.gz')).with_suffix('.json')
        for file_path in source.parent.glob(json_path.stem + '.*'):
            name = BidsName.from_string(target.name)
            name.extension = BidsName.from_string(file_path.name).extension
            renamed_files[file_path] = file_path.with_name(str(name))

    # Check all destinations before renaming any files.
    for target in renamed_files.values():
        if target.exists():
            print_existing_bids_files([target], target.parent, overwrite)

    for source, target in renamed_files.items():
        print(f"Renaming '{source.name}' to '{target.name}'.")
        source.rename(target)


def patch_files(
    acquisition_dir_path: Path,
    dicom_series: DicomSeriesInfo,
    *,
    merge_images: bool = False,
    sidecar: dict[str, object] | None = None,
):
    """
    Patch the output BIDS files with the following:
    - Rename files to match the MNI 7T BIDS naming.
    - Delete superfluous files.
    - Add missing information to the JSON sidecar file.
    """

    for file_path in acquisition_dir_path.iterdir():
        patch_file_path(file_path)

    patch_sidecar_metadata(acquisition_dir_path, dicom_series, merge_images=merge_images, sidecar=sidecar)


def patch_file_path(file_path: Path):
    """
    Rename an output BIDS file to match the MNI 7T BIDS naming, or delete it if it is superfluous.
    """

    bids_name = BidsName.from_string(file_path.name)

    # Delete the bval and bvec files from MP2RAGE acquisitions.
    if bids_name.has('MP2RAGE') and (bids_name.extension == 'bval' or bids_name.extension == 'bvec'):
        print(f"Remove MP2RAGE bval/bvec file '{file_path.name}'")
        file_path.unlink()
        return

    # Delete the 'ROI1' files.
    if bids_name.has('ROI1'):
        print(f"Remove ROI file '{file_path.name}'")
        file_path.unlink()
        return

    # Replace 'e?' by 'echo-?'
    echo_match = bids_name.match(r'e(\d)')
    if echo_match is not None:
        bids_name.remove(echo_match.group(0))
        bids_name.add('echo', echo_match.group(1))

    # Remove 'run-?' from echo files (there can be several 'task-rest' runs per acquisition).
    if bids_name.has('echo') and bids_name.has('run') and not bids_name.has_value('task', 'rest'):
        bids_name.remove('run')

    # Remove 'run-?' from MTR files.
    if bids_name.has_value('acq', 'mtw07') and bids_name.has('run'):
        bids_name.remove('run')

    # Replace 'ph' with 'part-phase'.
    if bids_name.has('ph'):
        bids_name.remove('ph')
        bids_name.add('part', 'phase')

    # Replace standalone 'T2starw' with 'T2starmap'.
    if (bids_name.has_value('acq', 'aspire') and bids_name.has('T2starw')
        and not bids_name.has('echo') and not bids_name.has('desc')
        and not bids_name.has('part') and not bids_name.has('rec')
    ):
        bids_name.remove('run')
        bids_name.remove('T2starw')
        bids_name.add('T2starmap')

    # Remove 'run-1' in 7T DWI acquisitions.
    if bids_name.has('dwi') and bids_name.has_value('run', '1'):
        bids_name.remove('run')

    # Replace 'run-2' with 'part-phase' in 7T DWI acquisitions.
    if bids_name.has('dwi') and bids_name.has_value('run', '2'):
        bids_name.remove('run')
        bids_name.add('part', 'phase')

    # Apply the TB1TFL-specific post processing.
    if bids_name.has('TB1TFL'):
        run_number = int(bids_name.get('run') or 0)
        acquisition_name = 'anat' if run_number % 2 == 1 else 'sfam'
        bids_name.add('acq', acquisition_name)
        bids_name.add('run', str(math.ceil(run_number / 2)))

    new_file_name = str(bids_name)

    # Rename the file on the system.
    if new_file_name != file_path.name:
        print(f"Renaming '{file_path.name}' to '{new_file_name}'.")
        rename_file(file_path, new_file_name)
