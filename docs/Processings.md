# Processing on top of dcm2niix

The converter applies the following built-in processing to mapped BIDS acquisitions after running dcm2niix. Unknown series converted outside the BIDS dataset do not receive these corrections.

## Filenames and file cleanup

| Condition | Processing |
|-----------|------------|
| dcm2niix adds an `eN` component (a single digit). | Replace it with `echo-N`. |
| dcm2niix adds a `ph` component. | Replace it with `part-phase`. |
| An `acq-aspire_T2starw` image has no `echo`, `desc`, `part`, or `rec` entity. | Replace the `T2starw` suffix with `T2starmap`. |
| A `dwi` image has provisional `run-2`. | Identify it as `part-phase`, before magnitude/phase pairing. This is a built-in assumption about the ordering of the 7T DWI series. |
| An image has the `TB1TFL` suffix. | Decode alternating series into `acq-anat` (odd provisional runs) and `acq-sfam` (even provisional runs). Each pair shares a provisional run number: series 1/2 become run 1, series 3/4 become run 2, and so on. |
| A `.bval` or `.bvec` file has the `MP2RAGE` suffix. | Delete the file. |
| A filename contains a standalone `ROI1` component. | Delete the file. |

After all mapped series have been converted, the converter applies these steps in order:

1. **Frequency maps:** remove `part-phase` when the final JSON sidecar has `Units: Hz`.
2. **Magnitude/phase pairing:** add `part-mag` to magnitude counterparts and give the phase image the magnitude image's run label. Pairing uses the directory, filename entities other than `part` and `run`, and `AcquisitionTime`. If acquisition time is missing, run labels must also match. Ambiguous pairs raise an error. Magnitude is identified by `M` in `ImageType`; DWI images containing `DIFFUSION` but no `P` are also accepted as magnitude counterparts. Unpaired magnitude images keep their filenames.
3. **Singleton runs:** remove `run` when an acquisition group has only one distinct run label across all components and echoes. Groups share a directory and filename entities other than `run`, `part`, and `echo`. Existing images in affected groups participate in this check. Groups with multiple runs retain their labels, including gaps in numbering.

Renames include associated JSON sidecars and gradient files, and are reflected in `scans.tsv` while retaining existing custom metadata.

## Acquisition metadata

| Condition | Processing |
|-----------|------------|
| An image has `part-phase`. | Set `Units` to `rad` if the JSON sidecar does not already specify units. |
| A filename has a `task` entity. | Set `TaskName` to its value. |
| A filename has `acq-neuromelaninMTw`. | Read `MTFlipAngle` from `sWipMemBlock.adFree[2]` in the Siemens CSA header, when available. |
| An image has the `MP2RAGE` suffix. | Populate missing `RepetitionTimePreparation`, `RepetitionTimeExcitation`, `SlicesPerSlab`, and `NumberShots` as described below. |

For MP2RAGE, existing values of these four fields are preserved. Missing values are obtained as follows:

| Field | Source |
|-------|--------|
| `RepetitionTimePreparation` | The sidecar's `RepetitionTime`. |
| `RepetitionTimeExcitation` | A built-in lookup by `ProtocolName`, and for some protocols `EchoTime`; only recognized protocols are supported. |
| `SlicesPerSlab` | `sKSpace.lImagesPerSlab` in the Siemens CSA header. |
| `NumberShots` | `[SlicesPerSlab × (PartialFourier − 0.5), SlicesPerSlab × 0.5]`, using the sidecar's `PartialFourier`. |

Missing or unrecognized MP2RAGE source values produce warnings, and the corresponding fields remain unset. Dictionary `sidecar` overrides are applied after these metadata corrections.

## Dataset metadata

The converter also maintains metadata for successfully converted scans in each affected raw or derivative dataset:

- Add the subject to `participants.tsv`, preserving existing rows and columns.
- Register final image paths in the session's `scans.tsv`.
- Update the subject's `sessions.tsv` with scanner information from registered scans, and write the column definition to `sessions.json`. Unrecognized scanners are recorded as `n/a`, with a warning; multiple scanner values are sorted and comma-separated. See the [scanner identification table](../README.md#scan-metadata).
- Create or update `dataset_description.json` with the target BIDS version and converter/dcm2niix provenance in `GeneratedBy`, preserving unrelated metadata. A conflicting existing BIDS version raises an error before conversion.

When auxiliary dataset files are enabled, the converter also initializes `.bidsignore` from its packaged template, merges participant column definitions into `participants.json`, and updates `participants_7t_to_bids.tsv` with scan counts and conversion information.

Dictionary-controlled operations, such as merging images, adding credits, selecting derivative datasets, and adding acquisition-specific ignore rules or sidecar values, are described in [Configuration](./Configuration.md).
