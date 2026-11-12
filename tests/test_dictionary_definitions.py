import copy
import json
from pathlib import Path

import pytest
from mni_7t_dicom_to_bids.dictionary import DicomDictionaryError, load_dicom_dictionary


@pytest.fixture
def dictionary_value(tmp_path: Path):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates/example.json").write_text(
        json.dumps(
            {
                "DatasetType": "derivative",
                "GeneratedBy": [{"Name": "example"}],
            }
        )
    )
    return {
        "ignored-series": [],
        "trim-series-suffixes": [],
        "references": {"paper": {"text": "Example paper.", "url": "https://example.org/paper"}},
        "derivatives": {"processed": {"name": "example", "dataset-description": "templates/example.json"}},
        "mappings": [
            {
                "series": "example",
                "datatype": "anat",
                "filename": "T1w",
                "derivative": "processed",
                "credit": {"acknowledgement": "Provider", "references": ["paper"]},
            }
        ],
    }


@pytest.fixture
def load_dictionary(tmp_path: Path):
    def load(value):
        path = tmp_path / "dictionary.json"
        path.write_text(json.dumps(value))
        return load_dicom_dictionary(path)

    return load


def test_named_definitions_match_inline_values_and_resolve_relative_templates(dictionary_value, load_dictionary):
    named = load_dictionary(dictionary_value)
    inline = copy.deepcopy(dictionary_value)
    inline.pop("references")
    inline.pop("derivatives")
    inline["mappings"][0]["derivative"] = dictionary_value["derivatives"]["processed"]
    inline["mappings"][0]["credit"]["references"] = [dictionary_value["references"]["paper"]]
    assert named == load_dictionary(inline)
    assert named.mappings[0].dataset.name == "example"
    assert named.mappings[0].dataset.dataset_description["DatasetType"] == "derivative"
    assert named.mappings[0].credit.references[0].url == dictionary_value["references"]["paper"]["url"]


def test_mixed_references_deduplicate_by_url_and_default_to_empty(dictionary_value, load_dictionary):
    mapping = dictionary_value["mappings"][0]
    mapping["credit"]["references"] = ["paper", dictionary_value["references"]["paper"]]
    assert len(load_dictionary(dictionary_value).mappings[0].credit.references) == 1
    mapping["credit"].pop("references")
    assert load_dictionary(dictionary_value).mappings[0].credit.references == ()
    mapping.pop("derivative")
    assert not load_dictionary(dictionary_value).mappings[0].dataset.is_derivative


@pytest.mark.parametrize(
    ("field", "pattern"),
    [
        ("references", r"mappings\[0\].credit.references\[0\].*undefined reference 'paper'"),
        ("derivatives", r"mappings\[0\].derivative.*undefined derivative 'processed'"),
    ],
)
def test_undefined_names_report_mapping_location(dictionary_value, load_dictionary, field, pattern):
    dictionary_value[field] = {}
    with pytest.raises(DicomDictionaryError, match=pattern):
        load_dictionary(dictionary_value)


@pytest.mark.parametrize(
    ("section", "definition"),
    [
        pytest.param("references", {"text": "Missing URL"}, id="missing-url"),
        pytest.param("references", {"text": "Invalid URL", "url": "file:///paper"}, id="invalid-url"),
        pytest.param("references", "paper", id="reference-alias"),
        pytest.param(
            "derivatives", {"name": "invalid name", "dataset-description": "templates/example.json"}, id="invalid-name"
        ),
        pytest.param("derivatives", None, id="null-derivative"),
        pytest.param("derivatives", "processed", id="derivative-alias"),
    ],
)
def test_invalid_unused_definitions_are_rejected(dictionary_value, load_dictionary, section, definition):
    dictionary_value[section]["unused"] = definition
    with pytest.raises(DicomDictionaryError, match=section + r"\.unused"):
        load_dictionary(dictionary_value)


@pytest.mark.parametrize("section", ["references", "derivatives"])
def test_invalid_definition_sections_are_rejected(dictionary_value, load_dictionary, section):
    dictionary_value[section] = []
    with pytest.raises(DicomDictionaryError):
        load_dictionary(dictionary_value)


def test_conflicting_named_and_inline_derivatives_are_rejected(tmp_path: Path, dictionary_value, load_dictionary):
    (tmp_path / "templates/other.json").write_text(
        json.dumps(
            {
                "DatasetType": "derivative",
                "GeneratedBy": [{"Name": "different"}],
            }
        )
    )
    other = {"name": "example", "dataset-description": "templates/other.json"}
    dictionary_value["mappings"][0]["derivative"] = other
    with pytest.raises(DicomDictionaryError, match=r"mappings\[0\].derivative conflicts"):
        load_dictionary(dictionary_value)
    dictionary_value["mappings"][0]["derivative"] = "processed"
    dictionary_value["derivatives"]["unused"] = other
    with pytest.raises(DicomDictionaryError, match=r"derivatives\.unused conflicts"):
        load_dictionary(dictionary_value)


def test_duplicate_definition_keys_are_rejected(tmp_path: Path):
    path = tmp_path / "dictionary.json5"
    path.write_text("""{
      "ignored-series": [], "trim-series-suffixes": [], "mappings": [],
      "references": {
        "paper": {"text": "First", "url": "https://example.org/first"},
        "paper": {"text": "Second", "url": "https://example.org/second"}
      }
    }""")
    with pytest.raises(DicomDictionaryError):
        load_dicom_dictionary(path)
