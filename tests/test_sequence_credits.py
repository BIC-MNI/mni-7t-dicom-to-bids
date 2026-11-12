import json
from pathlib import Path

import pytest
from mni_7t_dicom_to_bids.args import Args, SkipErrorsArg, SkipUnknownsArg
from mni_7t_dicom_to_bids.convert_dicom_series import convert_dicom_series
from mni_7t_dicom_to_bids.dataclass import (
    BidsSessionInfo,
    Citation,
    ConvertedScan,
    DicomSeriesInfo,
    SequenceCredit,
)
from mni_7t_dicom_to_bids.dictionary import DicomDictionaryError, load_dicom_dictionary
from mni_7t_dicom_to_bids.map_dicom_series import create_conversion_plan
from mni_7t_dicom_to_bids.metadata.credits import patch_dataset_credits
from mni_7t_dicom_to_bids.pipeline import mni_7t_dicom_to_bids


def test_protocol_credits_and_unrelated_variants():
    dictionary = load_dicom_dictionary()
    descriptions = [
        "func-cloudy_acq-ep2d_MJC_19mm",
        "fmap-b1_tra_p2",
        "anat-T1w_acq-mp2rage_0.7mm_CSptx_INV1",
        "anat-T1w_acq_mprage_0.8mm_CSptx",
        "dwi_acq_multib_38dir_AP_acc9",
        "dwi_acq_multib_70dir_AP_acc9_SBRef",
        "anat-T1w_acq-mp2rage_05mm_UP_UNI_Images",
        "anat-flair_acq-0.7iso_UPAdia",
        "Aspire_M_anat-T2star_acq-me_gre_0.7iso_ASPIRE",
        "anat-mtw_acq-MTON_07mm",
        "anat-mtw_acq-MTOFF_07mm",
        "anat-nm_acq-MTboost_sag_0.55mm",
        "anat-angio_acq-tof_03mm_inplane",
    ]
    plan = create_conversion_plan([DicomSeriesInfo(name, i, []) for i, name in enumerate(descriptions)], dictionary)
    assert not plan.unknown_series
    assert len(descriptions) == sum(len(a.series) for a in plan.acquisitions)
    assert all(s.credit for a in plan.acquisitions for s in a.series)
    unrelated = create_conversion_plan([DicomSeriesInfo("dwi_acq_multib_108dir_AP_acc9", 1, [])], dictionary)
    assert unrelated.acquisitions[0].series[0].credit is None


def test_merge_preserves_metadata_and_readme_and_is_idempotent(tmp_path: Path):
    root = tmp_path
    description = {
        "Name": "Existing",
        "Acknowledgements": "Original credit",
        "ReferencesAndLinks": ["Original reference"],
        "HowToAcknowledge": "Original instructions",
    }
    path = root / "dataset_description.json"
    path.write_text(json.dumps(description))
    readme = root / "README.rst"
    readme.write_text("Original README\n")
    credit = SequenceCredit("Sequence A: provider.", (Citation("Paper A", "https://doi.org/example"),))
    scans = [ConvertedScan(root / "scan.nii.gz", credit=credit)] * 2
    patch_dataset_credits(root, scans)
    first = (path.read_text(), readme.read_text())
    patch_dataset_credits(root, scans)
    assert first == (path.read_text(), readme.read_text())
    updated = json.loads(path.read_text())
    assert updated["HowToAcknowledge"] == "Original instructions"
    assert updated["ReferencesAndLinks"] == ["Original reference", "Paper A https://doi.org/example"]
    assert "Original credit" in updated["Acknowledgements"]
    assert readme.read_text() == "Original README\n"
    assert not (root / "README.md").exists()
    patch_dataset_credits(root, [])
    assert first == (path.read_text(), readme.read_text())


@pytest.mark.parametrize(
    "credit",
    [
        pytest.param({"acknowledgement": ""}, id="empty-acknowledgement"),
        pytest.param({"acknowledgement": "A", "references": [3]}, id="numeric-reference"),
        pytest.param({"acknowledgement": "A", "references": ["Legacy string"]}, id="legacy-reference"),
        pytest.param({"acknowledgement": "A", "references": [{"text": "Paper"}]}, id="missing-url"),
        pytest.param(
            {"acknowledgement": "A", "references": [{"text": "", "url": "https://example.org"}]},
            id="empty-reference-text",
        ),
        pytest.param({"acknowledgement": "A", "references": [{"text": "Paper", "url": "not a URL"}]}, id="invalid-url"),
        pytest.param({"acknowledgement": "A", "unexpected": True}, id="unexpected-field"),
    ],
)
def test_invalid_credit_rejected_and_omitted_credit_supported(tmp_path: Path, credit):
    path = tmp_path / "dictionary.json"
    mapping = {"series": "example", "datatype": "anat", "filename": "T1w"}
    value = {"ignored-series": [], "trim-series-suffixes": [], "mappings": [mapping]}
    path.write_text(json.dumps(value))
    assert load_dicom_dictionary(path).mappings[0].credit is None
    mapping["credit"] = credit
    path.write_text(json.dumps(value))
    with pytest.raises(DicomDictionaryError):
        load_dicom_dictionary(path)


def test_structured_references_deduplicate_by_url(tmp_path: Path):
    root = tmp_path
    url = "https://doi.org/10.1002/mrm.26963"
    value = {
        "ignored-series": [],
        "trim-series-suffixes": [],
        "mappings": [
            {
                "series": "example",
                "datatype": "anat",
                "filename": "T1w",
                "credit": {
                    "acknowledgement": "Credit",
                    "references": [{"text": "Paper A", "url": url}, {"text": "Alternate text", "url": url}],
                },
            }
        ],
    }
    dictionary_path = root / "dictionary.json"
    dictionary_path.write_text(json.dumps(value))
    credit = load_dicom_dictionary(dictionary_path).mappings[0].credit
    assert credit.references == (Citation("Paper A", url),)
    description_path = root / "dataset_description.json"
    for existing in (url, "Existing citation " + url):
        description_path.write_text(json.dumps({"ReferencesAndLinks": [existing]}))
        patch_dataset_credits(root, [ConvertedScan(root / "scan.nii.gz", credit=credit)])
        assert json.loads(description_path.read_text())["ReferencesAndLinks"] == [existing]


def test_sidecar_credit_and_successful_scan_propagation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    source = root / "input.dcm"
    source.write_bytes(b"fixture")
    plan = create_conversion_plan(
        [DicomSeriesInfo("anat-angio_acq-tof_03mm_inplane", 1, [source])], load_dicom_dictionary()
    )
    planned = plan.acquisitions[0].series[0]
    planned.sidecar["Description"] = "Configured description."
    args = Args(root, root / "bids", "01", "01", None, SkipUnknownsArg(), SkipErrorsArg(), False, True)

    def fake_niix(dicom_path, output_path, filename, args, **kwargs):
        (output_path / (filename + ".nii.gz")).write_bytes(b"fixture")
        (output_path / (filename + ".json")).write_text('{"Manufacturer": "Siemens"}')

    monkeypatch.setattr("mni_7t_dicom_to_bids.convert_dicom_series.run_dicom_to_niix", fake_niix)
    result = convert_dicom_series(BidsSessionInfo("01", "01"), plan, args)
    assert len(result.scans) == 1
    assert result.scans[0].credit == planned.credit
    sidecar = next((root / "bids").rglob("*.json"))
    metadata = json.loads(sidecar.read_text())
    assert metadata["Manufacturer"] == "Siemens"
    assert metadata["Description"].startswith("Configured description.")
    assert "Siemens product sequence" in metadata["Description"]

    def failed_niix(*args, **kwargs):
        raise RuntimeError("Simulated failed conversion")

    monkeypatch.setattr("mni_7t_dicom_to_bids.convert_dicom_series.run_dicom_to_niix", failed_niix)
    failed = convert_dicom_series(BidsSessionInfo("01", "01"), plan, args)
    assert not failed.scans


def test_pipeline_routes_derivative_credits_and_honors_no_dataset_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    root = tmp_path
    sources = [
        DicomSeriesInfo("anat-angio_acq-tof_03mm_inplane", 1, []),
        DicomSeriesInfo("EchoCombined_anat-T2star_acq-me_gre_0.7iso_ASPIRE", 2, []),
        DicomSeriesInfo("CLEAR-SWI_anat-T2star_acq-me_gre_0.7iso_ASPIRE", 3, []),
    ]
    args = Args(root, root, "01", "01", None, SkipUnknownsArg(), SkipErrorsArg(), False, False)

    def fake_niix(dicom_path, output_path, filename, args, **kwargs):
        (output_path / (filename + ".nii.gz")).write_bytes(b"fixture")
        (output_path / (filename + ".json")).write_text("{}")

    monkeypatch.setattr("mni_7t_dicom_to_bids.pipeline.check_dicom_to_niix", lambda: None)
    monkeypatch.setattr("mni_7t_dicom_to_bids.pipeline.group_dicom_series", lambda *args: sources)
    monkeypatch.setattr("mni_7t_dicom_to_bids.convert_dicom_series.run_dicom_to_niix", fake_niix)
    mni_7t_dicom_to_bids(args)
    raw = json.loads((root / "dataset_description.json").read_text())
    derivative = json.loads((root / "derivatives/aspire/dataset_description.json").read_text())
    assert "Siemens product sequence" in raw["Acknowledgements"]
    assert "Simon Robinson" in raw["Acknowledgements"]
    assert "Simon Robinson" in derivative["Acknowledgements"]
    assert any("10.1002/mrm.26963" in ref for ref in derivative["ReferencesAndLinks"])
    sidecar = next((root / "derivatives/aspire").rglob("*T2starw.json"))
    assert "10.1002/mrm.26963" in json.loads(sidecar.read_text())["Description"]
    clear_sidecar = next(root.rglob("*rec-CLEARSWI_swi.json"))
    clear_description = json.loads(clear_sidecar.read_text())["Description"]
    assert clear_description.count("10.1016/j.neuroimage.2021.118175") == 1
    assert "Eckstein K, Bachrata B" in clear_description
    assert "Susceptibility-weighted image reconstructed using CLEAR-SWI" in clear_description
    assert sum("10.1016/j.neuroimage.2021.118175" in ref for ref in raw["ReferencesAndLinks"]) == 1
    assert "Siemens product sequence" not in derivative["Acknowledgements"]
    assert not list(root.rglob("README*"))
