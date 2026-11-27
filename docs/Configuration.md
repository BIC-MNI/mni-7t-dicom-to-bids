# Configuration

The converter can be supplied a custom DICOM to BIDS dictionary file using the `--dictionary <path>` CLI argument, which tells it how to convert each acquisition from DICOM to BIDS based on their DICOM series description.

A dictionary is a JSON or JSON5 file that has the following structure:

```json
{
  "bids-version": "1.11.2",
  "ignored-series": ["AAHead_Scout.*"],
  "trim-series-suffixes": ["_Pha", "_Motion"],
  "references": {
    "example-method": {
      "text": "Example method reference.",
      "url": "https://example.org/method"
    }
  },
  "derivatives": {
    "example": {
      "name": "example",
      "dataset-description": "dataset_descriptions/example.json"
    }
  },
  "mappings": [
    {
      "series": "anat-T1w_acq-mprage_.*",
      "datatype": "anat",
      "filename": "T1w",
      "merge-images": true,
      "sidecar": {
        "Description": "An anatomical image processed by the example pipeline."
      },
      "derivative": "example",
      "credit": {
        "acknowledgement": "Sequence and reconstruction attribution.",
        "references": ["example-method"]
      }
    }
  ]
}
```

Both JSON and JSON5 files are supported; JSON5 notably supports comments. In the tables below,
“Required” in the Default column means that the attribute must be supplied, even when its value
is an empty array. Otherwise, the column gives the value used when the attribute is omitted.

## Dictionary

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `bids-version` | string | Required | Target BIDS specification version. |
| `ignored-series` | array of strings | Required | Regular expressions identifying DICOM series to ignore. |
| `trim-series-suffixes` | array of strings | Required | Literal suffixes removed from the series description before matching. |
| `mappings` | array of [acquisition objects](#acquisitions) | Required | Conversion rules, evaluated in order. The first entry whose `series` pattern matches is used. |
| `references` | object of [reference objects](#references) | `{}` | Citation definitions that can be reused as acquisition references using their name. |
| `derivatives` | object of [derivative objects](#derivatives) | `{}` | Derivative dataset definitions that can be reused as acquisition derivative dataset using their name. |

## Derivatives

Each definition in the top-level `derivatives` object accepts the following attributes.

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | string | Required | Output directory label. Must begin with a letter or digit and contain only letters, digits, and hyphens. Conflicting dataset descriptions for the same output directory are rejected. |
| `dataset-description` | string | Required | Path to a JSON dataset description template. Relative paths are resolved from the dictionary directory, including for named definitions. |

## References

Each definition in the top-level `references` object accepts the following attributes.

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `text` | string | Required | Citation text. |
| `url` | string | Required | HTTPS URL for the reference. |

## Acquisitions

Each entry in `mappings` accepts the following attributes.

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `series` | string | Required | Regular expression matched against the series description and used to identify the acquisition. |
| `datatype` | string | Required | BIDS datatype: `anat`, `dwi`, `fmap`, or `func`. |
| `filename` | string | Required | BIDS filename of this acquisition, before modification by `dcm2niix` or the converter. |
| `merge-images` | boolean | `false` | Whether to merge the produced images in a single file using `dcm2niix` `-m y` argument. Echo times of multi-echo series are appropriately registered in the JSON sidecar. |
| `bidsignore` | boolean or string | `false` | Whether to include the acquisition outputs to the dataset's `.bidsignore` file. `false` adds nothing. `true` appends the output acquisition file paths to the `.bidsignore` file. A string is interpreted as a pattern that is appended to the `.bidsignore` file if not already present, for example `"**/*_desc-example_*.*"`. |
| `sidecar` | object | `{}` | Metadata to add or replace in the output JSON sidecar. |
| `derivative` | string or null | `null` | Move the acquisition to a derivative dataset from the [derivatives](#derivatives) section. |
| `credit` | [credit object](#credits) or null | `null` | Sequence attribution and citations. |

## Credits

A mapping's `credit` object accepts the following attributes.

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `acknowledgement` | string | Required | Sequence and reconstruction attribution text. |
| `references` | array of [strings](#references) | `[]` | Names of definitions in the top-level `references` object. |
