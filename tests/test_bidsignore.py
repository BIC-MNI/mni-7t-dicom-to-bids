import json
from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock

import pytest

from mni_7t_dicom_to_bids.args import Args, SkipErrorsArg, SkipUnknownsArg
from mni_7t_dicom_to_bids.dataclass import (
    RAW_BIDS_DATASET,
    BidsDatasetInfo,
    ConvertedScan,
    DicomSeriesConversionsCounter,
    DicomSeriesInfo,
)
from mni_7t_dicom_to_bids.dataset_files import add_static_dataset_files, update_bidsignore
from mni_7t_dicom_to_bids.dictionary import DicomDictionaryError, load_dicom_dictionary
from mni_7t_dicom_to_bids.pipeline import mni_7t_dicom_to_bids


def write_scan(root: Path, name: str = 'sub-01_ses-01_acq-custom_run-1_swi', *, bidsignore: bool = True):
    directory = root / 'sub-01/ses-01/anat'
    directory.mkdir(parents=True, exist_ok=True)
    for extension in ['nii.gz', 'json', 'bval', 'bvec']:
        path = directory / f'{name}.{extension}'
        path.write_text('{}' if extension == 'json' else 'data')
    return ConvertedScan(directory / f'{name}.nii.gz', bidsignore=bidsignore)


def test_initializes_template_and_appends_all_companions_once(tmp_path: Path):
    scan = write_scan(tmp_path)
    unrelated = scan.image_path.with_name('sub-01_ses-01_acq-other_swi.json')
    unrelated.write_text('{}')
    update_bidsignore(tmp_path, [scan])
    path = tmp_path / '.bidsignore'
    content = path.read_text()
    assert 'bids_validator_output.txt\n' in content
    assert 'participants_7t_to_bids.tsv\n' in content
    assert {line for line in content.splitlines() if line.startswith('sub-')} == {
        file.relative_to(tmp_path).as_posix()
        for file in scan.image_path.parent.iterdir() if file != unrelated
    }
    update_bidsignore(tmp_path, [scan])
    assert path.read_text() == content


@pytest.mark.parametrize('overwrite', [False, True])
def test_existing_content_and_entries_survive_static_file_copy(tmp_path: Path, overwrite: bool):
    scan = write_scan(tmp_path)
    relative = scan.image_path.relative_to(tmp_path).as_posix()
    original = f'# manual rules\ncustom/\n{relative}'  # No trailing newline.
    path = tmp_path / '.bidsignore'
    path.write_text(original)
    add_static_dataset_files(tmp_path, overwrite)
    assert path.read_text() == original
    update_bidsignore(tmp_path, [scan])
    content = path.read_text()
    assert content.startswith(original + '\n')
    assert content.splitlines().count(relative) == 1
    add_static_dataset_files(tmp_path, overwrite)
    assert path.read_text() == content
    # Switching the flag off preserves previous entries.
    update_bidsignore(tmp_path, [ConvertedScan(scan.image_path)])
    assert path.read_text() == content


def test_unflagged_scans_do_not_create_ignore_file(tmp_path: Path):
    update_bidsignore(tmp_path, [write_scan(tmp_path, bidsignore=False)])
    assert not (tmp_path / '.bidsignore').exists()


@pytest.mark.parametrize('value', [None, False, True, 'true', 1])
def test_dictionary_bidsignore_is_strict_and_defaults_false(tmp_path: Path, value: object):
    mapping: dict[str, object] = {'series': 'custom', 'datatype': 'anat', 'filename': 'swi'}
    if value is not None:
        mapping['bidsignore'] = value
    dictionary = tmp_path / 'dictionary.json'
    dictionary.write_text(json.dumps({
        'bids-version': '1.11.2', 'ignored-series': [], 'trim-series-suffixes': [],
        'mappings': [mapping],
    }))
    if isinstance(value, str) or type(value) is int:
        with pytest.raises(DicomDictionaryError, match='bidsignore'):
            load_dicom_dictionary(dictionary)
    else:
        assert load_dicom_dictionary(dictionary).mappings[0].bidsignore is (value is True)


def test_default_dictionary_flags_only_swi_and_merged_megre():
    mappings = load_dicom_dictionary().mappings
    assert {mapping.filename for mapping in mappings if mapping.bidsignore} == {
        'acq-megre07_rec-CLEARSWI_swi',
        'acq-megre07_rec-aspire_part-mag_MEGRE',
        'acq-megre07_rec-aspire_part-phase_MEGRE',
    }


def test_pipeline_propagates_flag_and_ignores_final_names_in_each_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    template = tmp_path / 'description.json'
    template.write_text(json.dumps({'DatasetType': 'derivative', 'GeneratedBy': [{'Name': 'custom'}]}))
    dictionary = tmp_path / 'dictionary.json'
    dictionary.write_text(json.dumps({
        'bids-version': '1.11.2', 'ignored-series': [], 'trim-series-suffixes': [],
        'mappings': [
            {'series': 'raw', 'datatype': 'anat', 'filename': 'acq-custom_swi', 'bidsignore': True},
            {'series': 'derived', 'datatype': 'anat', 'filename': 'acq-custom_swi', 'bidsignore': True,
             'derivative': {'name': 'custom', 'dataset-description': str(template)}},
            {'series': 'regular', 'datatype': 'anat', 'filename': 'T1w'},
        ],
    }))
    sources = [DicomSeriesInfo(description, number, [])
               for number, description in enumerate(['raw', 'derived', 'regular'], 1)]
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.check_dicom_to_niix', lambda: None)
    monkeypatch.setattr('mni_7t_dicom_to_bids.pipeline.group_dicom_series', Mock(return_value=sources))

    # Keep mapping and conversion-result construction real, replacing only the external conversion.
    def fake_run(
        source: DicomSeriesInfo, directory: Path, counter: DicomSeriesConversionsCounter,
        convert: Callable[[Path, Path], None],
    ) -> list[Path]:
        name = 'sub-01_ses-01_run-1_T1w' if source.description == 'regular' else (
            'sub-01_ses-01_acq-custom_run-1_swi'
        )
        paths: list[Path] = []
        for extension in ['nii.gz', 'json']:
            path = directory / f'{name}.{extension}'
            path.write_text('{}' if extension == 'json' else 'image')
            paths.append(path)
        counter.successes += 1
        return paths

    monkeypatch.setattr('mni_7t_dicom_to_bids.convert_dicom_series.run_conversion_function', fake_run)
    args = Args(tmp_path, tmp_path, '01', '01', dictionary, SkipUnknownsArg(), SkipErrorsArg(), False, False)
    mni_7t_dicom_to_bids(args)
    for dataset in [RAW_BIDS_DATASET, BidsDatasetInfo('custom')]:
        root = tmp_path / 'derivatives/custom' if dataset.is_derivative else tmp_path
        content = (root / '.bidsignore').read_text()
        assert {line for line in content.splitlines() if line.startswith('sub-')} == {
            f'sub-01/ses-01/anat/sub-01_ses-01_acq-custom_swi.{extension}'
            for extension in ['nii.gz', 'json']
        }
        assert 'run-' not in content
        assert 'T1w' not in content
