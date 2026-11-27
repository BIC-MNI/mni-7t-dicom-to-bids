# MNI 7T DICOM to BIDS converter

This project is the MNI 7T DICOM to BIDS converter, which is used at the Montreal Neurological Institute-Hospital to convert 7 Tesla DICOM scans to BIDS.

## Contributing

If you want to contribute to the MNI 7T DICOM to BIDS converter, read the contribution guide [here](./CONTRIBUTING.md).

## Usage

### Executable

You can download the latest version of the converter as an executable [here](https://github.com/bic-mni/mni-7t-dicom-to-bids/releases/tag/latest). This executable should work on all Debian-based machines (including Ubuntu) from Debian 11 or newer.

To run the executable, use the following command:

```sh
mni7t_dcm2bids <dicom_study_path> <bids_dataset_path> --subject <subject_label> --session <session_label>
```

The input DICOM directory must contain the DICOM files of a single session. The output BIDS directory can either be an empty directory (which can be created by the script) or be an existing BIDS directory (in which case the converted session is added to the existing BIDS).

### Docker

You can run the latest version of the converter as a Docker image using the following command:

```sh
docker run ghcr.io/bic-mni/mni-7t-dicom-to-bids <dicom_study_path> <bids_dataset_path> --subject <subject_label> --session <session_label>
```

You can find more information about the converter Docker image [here](https://github.com/bic-mni/mni-7t-dicom-to-bids/pkgs/container/mni-7t-dicom-to-bids). You might need to add bind mounts (`--mount` option) to link the input and output directories of the converter to the host.

### Apptainer

You can also use the aforementioned Docker image of the converter with Apptainer using the following command:

```sh
apptainer run docker://ghcr.io/bic-mni/mni-7t-dicom-to-bids <dicom_study_path> <bids_dataset_path> --subject <subject_label> --session <session_label>
```

Similarly, you might need to use bind paths (`--bind` option) to link the input and output directories of the converter to the host.

### Python

Finally, you can also install the converter as a Python package. To do so, run the following command in the relevant Python environment:

```sh
pip install git+https://github.com/bic-mni/mni-7t-dicom-to-bids
```

This command also installs the recommended version of [dcm2niix](https://github.com/rordenlab/dcm2niix).

To also the recommended version of the BIDS validator, use the `validator` extra:

```sh
pip install "mni_7t_dicom_to_bids[validator] @ git+https://github.com/bic-mni/mni-7t-dicom-to-bids"
```

## Scan metadata

See [processing on top of dcm2niix](./docs/Processings.md) for the built-in filename corrections, file cleanup, and metadata updates.

Before magnitude/phase pairing, images whose final JSON sidecar has `Units: Hz` lose any `part-phase`
label. This applies whether the units came from dcm2niix or a dictionary override.

After conversion, magnitude images with matching `part-phase` images receive `part-mag` in their
filenames. Components are paired by directory, filename entities other than `part`/`run`, and the JSON
sidecar's `AcquisitionTime`. The phase image takes the magnitude image's run label; repeated acquisitions
retain separate magnitude run labels. When acquisition time is missing, run labels must also match.
Ambiguous pairs raise an error.

Magnitude is identified by `M` in `ImageType`. Siemens DWI sidecars can omit `M`/`P`; an unlabeled `dwi`
image with `DIFFUSION` in `ImageType` is also accepted when it has a matching `part-phase` counterpart.
Magnitude-only images keep their filenames. Renames include sidecars and gradient files and are
reflected in `scans.tsv`, retaining existing custom metadata.

After frequency-map correction and magnitude/phase pairing, singleton `run` labels are removed.
Conversion assigns provisional run numbers to every mapped series; echo images, MTR, T2* maps,
and DWI all use this final cleanup instead of removing runs during individual series conversion.
DWI phase identification and TB1TFL anat/sfam pair decoding retain provisional runs for that cleanup.
Acquisition groups share a directory and all filename entities other than `run`, `part`, and `echo`
(ignoring the image extension). A group with only one distinct run label loses that label across
all components and echoes; groups with multiple runs retain their labels, including gaps in numbering
and incomplete component/echo sets. Existing images in affected groups participate in this check and
are renamed consistently; unrelated groups are left alone. Existing runless destinations use the
normal overwrite checks. Sidecars, gradients, and `scans.tsv` follow the final filenames.

The subject-level `sub-<label>_sessions.tsv` includes a `scanner` column, documented
in a dataset-root `sessions.json`, for both raw and derivative datasets.

Scanners are identified during post-processing from each scan's JSON sidecar:

| ManufacturersModelName | SoftwareVersions | scanner |
|---|---|---|
| `MAGNETOM Terra` | Any | `Siemens Terra 7T` |
| `MAGNETOM Terra.X` | Any | `Siemens Terra.X 7T` |
| `Investigational_Device_7T` | `syngo MR E12` | `Siemens Terra 7T` |
| Otherwise (including missing metadata) | | `n/a`, with a warning |

## Target software version

| **Software**       | **Version**     |
|--------------------|-----------------|
| BIDS Specification | `v1.11.2`       |
| BIDS Validator     | `v2.4.1`        |
| dcm2niix           | `v1.0.20260416` |

## Configuration

This converter can be configured to work with any DICOM series or BIDS naming convention by providing it with a custom dictionary JSON or JSON5 file.

```sh
mni7t_dcm2bids --dictionary dictionary.json ...
```

See the [configuration documentation](./docs/Configuration.md) for more information about the configuration file format.

## Default dictionary

This converter can be used with any DICOM to BIDS dictionary, but comes with a default dictionary aimed at the MNI BIC MRI acquisitions. See the the [default DICOM to BIDS dictionary documentation](./docs/Dictionary.md) for more information.

## Compilation

This converter can be compiled and distributed as an executable using PyInstaller. See the
[`Compilation documentation`](./docs/Compilation.md) for more information.

## Related repositories

This DICOM to BIDS converter is a rewrite of Raul Cruces' [MPN 7T pipeline DICOM to BIDS converter](https://github.com/rcruces/MPN_7T_pipeline). The present converter aims to provide a similar behavior (up to versions) with enhanced safety checks, portability, performance, and maintainability.
