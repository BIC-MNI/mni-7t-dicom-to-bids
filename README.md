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

## Target software version

| **Software**       | **Version**     |
|--------------------|-----------------|
| BIDS Specification | `v1.11.1`       |
| BIDS Validator     | `v2.4.1`        |
| dcm2niix           | `v1.0.20260416` |

## BIDS naming dictionary

### Anatomical: MPRAGE, MP2RAGE and FLAIR

| **N** | **7T Terra Siemens acquisition**                   | **BIDS**                              | **Directory** |
|:-----:|:--------------------------------------------------:|:-------------------------------------:|:-------------:|
|   1   |  anat-T1w_acq_mprage_0.8mm_CSptx                   | acq-mprage08CS_T1w                    | anat          |
|   2   |  anat-T1w_acq-mp2rage_0.7mm_CSptx_INV1             | acq-mp2rage07CSptx_inv-1_MP2RAGE      | anat          |
|   3   |  anat-T1w_acq-mp2rage_0.7mm_CSptx_INV2             | acq-mp2rage07CSptx_inv-2_MP2RAGE      | anat          |
|   4   |  anat-T1w_acq-mp2rage_0.7mm_CSptx_T1_Images        | acq-mp2rage07CSptx_T1map              | anat          |
|   5   |  anat-T1w_acq-mp2rage_0.7mm_CSptx_UNI_Images       | acq-mp2rage07CSptx_UNIT1              | anat          |
|   6   |  anat-T1w_acq-mp2rage_0.7mm_CSptx_UNI-DEN          | acq-mp2rage07CSptx_rec-denoised_UNIT1 | anat          |
|   7   |  anat-T1w_acq-mp2rage_05mm_UP*_INV1	             | acq-mp2rage05UP_inv-1_MP2RAGE         | anat          |
|   8   |  anat-T1w_acq-mp2rage_05mm_UP*_INV2	             | acq-mp2rage05UP_inv-2_MP2RAGE         | anat          |
|   9   |  anat-T1w_acq-mp2rage_05mm_UP*_T1_Images	         | acq-mp2rage05UP_T1map                 | anat          |
|   10  |  anat-T1w_acq-mp2rage_05mm_UP*_UNI_Images	         | acq-mp2rage05UP_UNIT1                 | anat          |
|   11  |  anat-flair_acq-0p7iso_UPAdia                      | FLAIR                                 | anat          |

### Anatomical: MEGRE
| **N** | **7T Terra Siemens acquisition**    | **BIDS**                  | **Directory** |
|:-----:|:-----------------------------------:|:-------------------------:|:-------------:|
|  12   |  CLEAR-SWI_anat-T2star_acq-me_gre_0\*7iso_ASPIRE    | acq-megre07_rec-CLEARSWI_T2starw                      | anat          |
|  13   |  Aspire_M_anat-T2star_acq-me_gre_0\*7iso_ASPIRE     | acq-megre07_rec-ASPIRE_echo-[1:5]_part-mag_MEGRE      | anat          |
|  14   |  Aspire_P_anat-T2star_acq-me_gre_0\*7iso_ASPIRE     | acq-megre07_rec-ASPIRE_echo-[1:5]_part-phase_MEGRE    | anat          |
|  15   |  EchoCombined_anat-T2star_acq-me_gre_0\*7iso_ASPIRE | acq-megre07_rec-ASPIRE_desc-EchoCombined_T2starw      | anat          |
|  16   |  sensitivity_corrected_mag_anat-T2star_acq-me_gre_0\*7iso_ASPIRE | acq-megre07_rec-ASPIRE_desc-EchoCombinedSensCorr_T2starw | anat |
|  17   |  T2star_anat-T2star_acq-me_gre_0\*7iso_ASPIRE       | acq-megre07_rec-ASPIRE_[T2starw,T2starmap]                            | anat |
|  18   |  Romeo_P_anat-T2star_acq-me_gre_0\*7iso_ASPIRE      | acq-megre07_rec-ROMEO_echo-[1:5]_T2starw              | anat          |
|  19   |  Romeo_B0_anat-T2star_acq-me_gre_0\*7iso_ASPIRE     | acq-megre07_rec-ROMEO_desc-unwrapped_T2starw          | anat          |
|  20   |  Romeo_Mask_anat-T2star_acq-me_gre_0\*7iso_ASPIRE   | acq-megre07_rec-ROMEO_desc-mask_T2starw               | anat          |


### Anatomical: Magnetic Transfer weighted, Neuromelanin and time of flight
| **N** | **7T Terra Siemens acquisition**    | **BIDS**                  | **Directory** |
|:-----:|:-----------------------------------:|:-------------------------:|:-------------:|
|  21   |  anat-mtw_acq-MTON_07mm                            | acq-mtw_mt-on_MTR                   | anat          |
|  22   |  anat-mtw_acq-MTOFF_07mm                           | acq-mtw_mt-off_MTR                  | anat          |
|  23   |  anat-mtw_acq-T1w_07mm                             | acq-mtw_T1w                         | anat          |
|  24   |  anat-nm_acq-MTboost_sag_0.55mm                    | acq-neuromelaninMTw_T1w             | anat          |
|  25   |  anat-angio_acq-tof_03mm_inplane                   | acq-tof_angio                       | anat          |
|  26   |  anat-angio_acq-tof_03mm_inplane_MIP_SAG           | acq-tof_rec-mipsag_angio            | anat          |
|  27   |  anat-angio_acq-tof_03mm_inplane_MIP_COR           | acq-tof_rec-mipcor_angio            | anat          |
|  28   |  anat-angio_acq-tof_03mm_inplane_MIP_TRA           | acq-tof_rec-miptra_angio            | anat          |

### Field maps

| **N** | **7T Terra Siemens acquisition**    | **BIDS**               | **Directory** |
|:-----:|:-----------------------------------:|:----------------------:|:-------------:|
|  1    | fmap-b1_tra_p2                      | acq-[anat,sfam]_TB1TFL | fmap          |
|  2    | fmap-b1_acq-sag_p2                  | acq-[anat,sfam]_TB1TFL | fmap          |
|  3    | fmap-fmri_acq-mbep2d_SE_19mm_dir-AP | acq-fmri_dir-AP_epi    | fmap          |
|  4    | fmap-fmri_acq-mbep2d_SE_19mm_dir-PA | acq-fmri_dir-PA_epi    | fmap          |

### Functional

| **N** | **7T Terra Siemens acquisition** | **BIDS**           | **Directory** |
|:-----:|:--------------------------------:|:------------------:|:-------------:|
|  1    | func-cross_acq-ep2d_MJC_19mm     | task-rest_bold     | func          |
|  2    | func-cloudy_acq-ep2d_MJC_19mm    | task-cloudy_bold   | func          |
|  3    | func-present_acq-mbep2d_ME_19mm  | task-present_bold  | func          |

> Each functional MRI acquisition includes three echoes and a phase. The final string will contain the identifier `echo-` followed by the echo number (e.g., `task-rest_echo-1_bold`). Additionally, the string `part-phase` will be included to identify the phase (e.g., `task-rest_echo-1_part-phase_bold`).

### Diffusion weighted images

| **N** | **7T Terra Siemens acquisition**    | **BIDS**                  | **Directory** |
|:-----:|:-----------------------------------:|:-------------------------:|:-------------:|
|  1    | *dwi_acq_b0_PA                      | acq-b0_dir-PA_dwi         | dwi           |
|  2    | *dwi_acq_b0_PA_SBRef                | acq-b0_dir-PA_sbref       | dwi           |
|  3    | *dwi_acq_multib_38dir_AP_acc9       | acq-multib38_dir-AP_dwi   | dwi           |
|  4    | *dwi_acq_multib_38dir_AP_acc9_SBRef | acq-multib38_dir-AP_sbref | dwi           |
|  5    | *dwi_acq_multib_70dir_AP_acc9       | acq-multib70_dir-AP_dwi   | dwi           |
|  6    | *dwi_acq_multib_70dir_AP_acc9_SBRef | acq-multib70_dir-AP_sbref | dwi           |

> The string `part-phase` will be included to identify the phase acquisitions (e.g., `acq-multib38_dir-AP_part-phase_dwi`).

### Abbreviation Glossary

| **Abbreviation** | **Description**                                               |
|------------------|---------------------------------------------------------------|
| **AP**           | Anterio-Posterior                                             |
| **PA**           | Postero-anterior                                              |
| **CS**           | Compressed SENSE                                              |
| **ptx**          | Parallel transmission                                         |
| **UP**           | Universal Pulse                                               |
| **megre**        | Multi-Echo Gradient Echo.                                     |
| **mip**          | Maximum intensity projection                                  |
| **cor**          | Coronal                                                       |
| **sag**          | Sagittal                                                      |
| **tra**          | Transverse (Axial)                                            |
| **mtw**          | Magnetization Transfer Weighted                               |
| **sfmap**        | Scaled flip angle map                                         |
| **tof**          | Time-of-flight                                                |
| **multib**       | Multi shell DWI                                               |
| **semphon**      | Semantic-phonetic                                             |
| **ASPIRE**       | Combination of multi-channel phase data from multi-echo acquisitions |
| **ROMEO**        | Rapid opensource minimum spanning tree algorithm              |

### References

1. Eckstein K, Dymerska B, Bachrata B, Bogner W, Poljanc K, Trattnig S, Robinson SD. Computationally efficient combination of multi‐channel phase data from multi‐echo acquisitions (ASPIRE). Magnetic resonance in medicine. 2018 Jun;79(6):2996-3006. https://doi.org/10.1002/mrm.26963

2. Dymerska B, Eckstein K, Bachrata B, Siow B, Trattnig S, Shmueli K, Robinson SD. Phase unwrapping with a rapid opensource minimum spanning tree algorithm (ROMEO). Magnetic resonance in medicine. 2021 Apr;85(4):2294-308. https://doi.org/10.1002/mrm.28563

3. Sasaki M, Shibata E, Tohyama K, Takahashi J, Otsuka K, Tsuchiya K, Takahashi S, Ehara S, Terayama Y, Sakai A. Neuromelanin magnetic resonance imaging of locus ceruleus and substantia nigra in Parkinson's disease. Neuroreport. 2006 Jul 31;17(11):1215-8. https://doi.org/10.1097/01.wnr.0000227984.84927.a7

## Compilation

This project can be compiled and distributed as an executable using PyInstaller, the compilation process is described in the [`COMPILATION.md`](./COMPILATION.md) file.

## Related repositories

This DICOM to BIDS converter is a rewrite of Raul Cruces' [MPN 7T pipeline DICOM to BIDS converter](https://github.com/rcruces/MPN_7T_pipeline). The present converter aims to provide a similar behavior (up to versions) with enhanced safety checks, portability, performance, and maintainability.
