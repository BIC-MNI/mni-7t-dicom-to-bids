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

### Anatomical

| **N** | **7T Terra Siemens acquisition pattern** | **BIDS** | **Directory** |
|:-----:|:------------------------------------------|:---------|:-------------:|
| 1 | `anat-flair_acq-0*7iso_UPAdia` | `FLAIR` | `anat` |
| 2 | `anat-flair_acq-0*7mm_UPAdia` | `FLAIR` | `anat` |
| 3 | `anat-flair_acq-0*7iso_dev3_5SD_UP` | `FLAIR` | `anat` |
| 4 | `*anat-T1w_acq-mp2rage_0*7mm_CSptx_UNI_Images` | `acq-07mm_UNIT1` | `anat` |
| 5 | `*anat-T1w_acq-mp2rage_0*7mm_CSptx_UNI-DEN` | `desc-denoised_UNIT1` | `anat` |
| 6 | `*anat-T1w_acq-mp2rage_0*7mm_CSptx_T1_Images` | `acq-07mm_T1map` | `anat` |
| 7 | `anat-T1w_acq_mprage_0*8mm_CSptx` | `T1w` | `anat` |
| 8 | `anat-T1w_acq_mprage_0*8mm_CSx_ND` | `T1w` | `anat` |
| 9 | `*anat-T1w_acq-mprage_0*7mm_UP` | `T1w` | `anat` |
| 10 | `*CLEAR-SWI_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-SWI_T2starw` | `anat` |
| 11 | `*Romeo_P_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-romeo_T2starw` | `anat` |
| 12 | `*Romeo_Mask_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-romeo_rec-mask_T2starw` | `anat` |
| 13 | `*Romeo_B0_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-romeo_rec-unwrapped_T2starw` | `anat` |
| 14 | `Aspire_M_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-aspire_T2starw` | `anat` |
| 15 | `Aspire_P_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-aspire_T2starw` | `anat` |
| 16 | `*T2star_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-aspire_T2starw` | `anat` |
| 17 | `*EchoCombined_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-aspire_rec-echoCombined_T2starw` | `anat` |
| 18 | `*sensitivity_corrected_mag_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-aspire_rec-echoCombinedSensitivityCorrected_T2starw` | `anat` |
| 19 | `*T2Star_Images` | `T2map` | `anat` |
| 20 | `*anat-T2star_acq-me_gre_07mm*` | `acq-me_T2starw` | `anat` |
| 21 | `*anat-T1w_acq-mp2rage_0*7mm_CSptx_INV1` | `acq-07mm_inv-1_MP2RAGE` | `anat` |
| 22 | `*anat-T1w_acq-mp2rage_0*7mm_CSptx_INV2` | `acq-07mm_inv-2_MP2RAGE` | `anat` |
| 23 | `*anat-T1w_acq-mp2rage_05mm_UP*_INV1*` | `acq-05mm_inv-1_MP2RAGE` | `anat` |
| 24 | `*anat-T1w_acq-mp2rage_05mm_UP*_INV2*` | `acq-05mm_inv-2_MP2RAGE` | `anat` |
| 25 | `*anat-T1w_acq-mp2rage_05mm_UP*_T1_Images*` | `acq-05mm_T1map` | `anat` |
| 26 | `*anat-T1w_acq-mp2rage_05mm_UP*_UNI_Images*` | `acq-05mm_UNIT1` | `anat` |
| 27 | `*cstfl-mp2rage-05mm_INV1` | `acq-cstfl_inv-1_MP2RAGE` | `anat` |
| 28 | `*cstfl-mp2rage-05mm_INV2` | `acq-cstfl_inv-2_MP2RAGE` | `anat` |
| 29 | `*cstfl-mp2rage-05mm_T1_Images` | `acq-cstfl_T1map` | `anat` |
| 30 | `*cstfl-mp2rage-05mm_UNI_Images` | `acq-cstfl_UNIT1` | `anat` |
| 31 | `*cstfl-mp2rage-05mm_UNI-DEN` | `acq-cstflDenoised_UNIT1` | `anat` |
| 32 | `*anat-mtw_acq-T1w_07mm` | `acq-mtw_T1w` | `anat` |
| 33 | `*anat-mtw_acq-MTON_07mm` | `acq-mtw_mt-on_MTR` | `anat` |
| 34 | `*anat-mtw_acq-MTOFF_07mm` | `acq-mtw_mt-off_MTR` | `anat` |
| 35 | `*_T1W` | `acq-MTR_T1w` | `anat` |
| 36 | `anat-nm_acq-MTboost_sag_0.55mm` | `acq-neuromelaninMTw_T1w` | `anat` |
| 37 | `CR_tfl_MTboost_sag7deg_0.55mm` | `acq-neuromelaninMTw_T1w` | `anat` |
| 38 | `*anat-angio_acq-tof_03mm_inplane` | `angio` | `anat` |
| 39 | `*anat-angio_acq-tof_03mm_inplane_MIP_COR` | `acq-cor_angio` | `anat` |
| 40 | `*anat-angio_acq-tof_03mm_inplane_MIP_SAG` | `acq-sag_angio` | `anat` |
| 41 | `*anat-angio_acq-tof_03mm_inplane_MIP_TRA` | `acq-tra_angio` | `anat` |

### Diffusion-weighted images

| **N** | **7T Terra Siemens acquisition pattern** | **BIDS** | **Directory** |
|:-----:|:------------------------------------------|:---------|:-------------:|
| 1 | `dwi_acq_b0_PA_SBRef` | `acq-b0_dir-PA_sbref` | `dwi` |
| 2 | `dwi_acq_b0_PA_acc9_SBRef` | `acq-b0_dir-PA_sbref` | `dwi` |
| 3 | `*dwi_acq_b0*_PA_SBRef` | `acq-b0_dir-PA_sbref` | `dwi` |
| 4 | `*dwi_acq_b0*_PA` | `acq-b0_dir-PA_dwi` | `dwi` |
| 5 | `dwi_acq_b0_PA_acc9` | `acq-b0_dir-PA_dwi` | `dwi` |
| 6 | `*dwi_acq_b0_PA_1p5iso_SBRef` | `acq-b01p5_dir-PA_sbref` | `dwi` |
| 7 | `*dwi_acq_b0_PA_1p5iso` | `acq-b01p5_dir-PA_dwi` | `dwi` |
| 8 | `*dwi_acq_multib_38dir_AP_acc9_SBRef` | `acq-multib38_dir-AP_sbref` | `dwi` |
| 9 | `*dwi_acq_multib_38dir_AP_acc9_test_SBRef` | `acq-multib38Test_dir-AP_sbref` | `dwi` |
| 10 | `*dwi_acq_multib_38dir_AP_acc9_1p5iso_SBRef` | `acq-multib381p5_dir-AP_sbref` | `dwi` |
| 11 | `*dwi_acq_multib_70dir_AP_acc9_SBRef` | `acq-multib70_dir-AP_sbref` | `dwi` |
| 12 | `dwi_acq_multib_108dir_AP_acc9_SBRef` | `acq-multib108_dir-AP_sbref` | `dwi` |
| 13 | `*dwi_acq_multib_70dir_AP_acc9_1p5iso_SBRef` | `acq-multib701p5_dir-AP_sbref` | `dwi` |
| 14 | `*dwi_acq_b300_10d-dir_AP_SBRef` | `acq-b300_dir-AP_sbref` | `dwi` |
| 15 | `*dwi_acq_b700_40d-dir_AP_SBRef` | `acq-b700_dir-AP_sbref` | `dwi` |
| 16 | `*dwi_acq_b2000_90d-dir_AP_SBRef` | `acq-b2000_dir-AP_sbref` | `dwi` |
| 17 | `*dwi_acq_multib_38dir_AP_acc9` | `acq-multib38_dir-AP_dwi` | `dwi` |
| 18 | `*dwi_acq_multib_38dir_AP_acc9_1p5iso` | `acq-multib381p5_dir-AP_dwi` | `dwi` |
| 19 | `*dwi_acq_multib_38dir_AP_acc9_test` | `acq-multib38Test_dir-AP_dwi` | `dwi` |
| 20 | `*dwi_acq_multib_70dir_AP_acc9` | `acq-multib70_dir-AP_dwi` | `dwi` |
| 21 | `*dwi_acq_multib_70dir_AP_acc9_1p5iso` | `acq-multib701p5_dir-AP_dwi` | `dwi` |
| 22 | `dwi_acq_multib_108dir_AP_acc9` | `acq-multib108_dir-AP_dwi` | `dwi` |
| 23 | `*dwi_acq_b300_10d-dir_AP` | `acq-b300_dir-AP_dwi` | `dwi` |
| 24 | `*dwi_acq_b700_40d-dir_AP` | `acq-b700_dir-AP_dwi` | `dwi` |
| 25 | `*dwi_acq_b2000_90d-dir_AP` | `acq-b2000_dir-AP_dwi` | `dwi` |

### Field maps

| **N** | **7T Terra Siemens acquisition pattern** | **BIDS** | **Directory** |
|:-----:|:------------------------------------------|:---------|:-------------:|
| 1 | `fmap-b1_tra_p2` | `acq-anat_TB1TFL` | `fmap` |
| 2 | `fmap-b1_acq-sag_p2` | `acq-anat_TB1TFL` | `fmap` |
| 3 | `*fmap-b1_acq-*_p2` | `acq-anat_TB1TFL` | `fmap` |
| 4 | `*fmap-fmri_acq-mbep2d_SE_19mm_dir-AP` | `acq-fmri_dir-AP_epi` | `fmap` |
| 5 | `*fmap-fmri_acq-mbep2d_SE_19mm_dir-PA` | `acq-fmri_dir-PA_epi` | `fmap` |
| 6 | `*fmap-fmri_acq-mbep2d_SE_19mm_dir-AP_Q1K` | `acq-fmriQ1K_dir-AP_epi` | `fmap` |
| 7 | `*fmap-fmri_acq-mbep2d_SE_19mm_dir-PA_Q1K` | `acq-fmriQ1K_dir-PA_epi` | `fmap` |

### Functional

| **N** | **7T Terra Siemens acquisition pattern** | **BIDS** | **Directory** |
|:-----:|:------------------------------------------|:---------|:-------------:|
| 1 | `func-cloudy_acq-ep2d_MJC_19mm` | `task-cloudy_bold` | `func` |
| 2 | `func-present_acq-ep2d_MJC_19mm` | `task-present_bold` | `func` |
| 3 | `*func-semphon1_acq-mbep2d_ME_19mm` | `task-semphon1_bold` | `func` |
| 4 | `*func-semphon2_acq-mbep2d_ME_19mm` | `task-semphon2_bold` | `func` |
| 5 | `func-cross_acq-ep2d_MJC_19mm` | `task-rest_bold` | `func` |
| 6 | `func-rsfmri_acq-multiE_1.9mm` | `task-rest_bold` | `func` |
| 7 | `*func-rsfmri_acq-mbep2d_ME_19mm` | `task-rest_bold` | `func` |
| 8 | `*func-rsfmri_acq-singleE_1*` | `task-rest_acq-singleE_bold` | `func` |
| 9 | `*func-rsfmri_acq-mbep2d_ME_19mm_Q1K` | `task-rest_acq-Q1K_bold` | `func` |
| 10 | `*func-epiencode_acq-mbep2d_ME_19mm*` | `task-epiencode_bold` | `func` |
| 11 | `*func-epiretrieve_acq-mbep2d_ME_19mm` | `task-epiretrieve_bold` | `func` |
| 12 | `*func-pattersep1_acq-mbep2d_ME_19mm` | `task-patternsep1_bold` | `func` |
| 13 | `*func-patter*sep2_acq-mbep2d_ME_19mm` | `task-patternsep2_bold` | `func` |
| 14 | `*func-semantic1_acq-mbep2d_ME_19mm` | `task-semantic1_bold` | `func` |
| 15 | `*func-semantic2_acq-mbep2d_ME_19mm` | `task-semantic2_bold` | `func` |
| 16 | `*func-spatial1_acq-mbep2d_ME_19mm` | `task-spatial1_bold` | `func` |
| 17 | `*func-spatial2_acq-mbep2d_ME_19mm` | `task-spatial2_bold` | `func` |
| 18 | `*func-movie*1_acq-mbep2d_ME_19mm` | `task-movies1_bold` | `func` |
| 19 | `*func-movie*2_acq-mbep2d_ME_19mm` | `task-movies2_bold` | `func` |
| 20 | `*func-movies3_acq-mbep2d_ME_19mm` | `task-movies3_bold` | `func` |
| 21 | `*func-movies4_acq-mbep2d_ME_19mm` | `task-movies4_bold` | `func` |
| 22 | `*func-caddy_acq-mbep2d_ME_19mm` | `task-caddy_bold` | `func` |
| 23 | `*func-harsh_acq-mbep2d_ME_19mm` | `task-harsh_bold` | `func` |
| 24 | `*func-pines_acq-mbep2d_ME_19mm` | `task-pines_bold` | `func` |
| 25 | `*func-bathroom_acq-mbep2d_ME_19mm` | `task-bathroom_bold` | `func` |
| 26 | `*func-audiobook1_acq-mbep2d_ME_19mm` | `task-audiobook1_bold` | `func` |
| 27 | `*func-audiobook2_acq-mbep2d_ME_19mm` | `task-audiobook2_bold` | `func` |
| 28 | `*func-oceans11_acq-mbep2d_ME_19mm` | `task-oceans11_bold` | `func` |
| 29 | `*func-social_acq-mbep2d_ME_19mm` | `task-social_bold` | `func` |
| 30 | `*func-sens1_acq-mbep2d_ME_19mm` | `task-sens2_bold` | `func` |
| 31 | `*func-sens2_acq-mbep2d_ME_19mm` | `task-sens1_bold` | `func` |
| 32 | `*func-slient1_acq-mbep2d_ME_19mm` | `task-salient_bold` | `func` |

### Abbreviation Glossary

| **Abbreviation** | **Description**                                               |
|------------------|---------------------------------------------------------------|
| **AP**           | Anterio-Posterior                                             |
| **PA**           | Postero-anterior                                              |
| **mtw**          | Magnetic transfer weighted                                    |
| **sfmap**        | Scaled flip angle map                                         |
| **tof**          | Time of flight                                                |
| **multib**       | Multi shell N directions                                      |
| **semphon**      | Semantic-phonetic                                             |
| **romeo**        | Rapid opensource minimum spanning tree algorithm              |
| **aspire**       | Combination of multi-channel phase data from multi-echo acquisitions |

### References

1. Eckstein K, Dymerska B, Bachrata B, Bogner W, Poljanc K, Trattnig S, Robinson SD. Computationally efficient combination of multi‐channel phase data from multi‐echo acquisitions (ASPIRE). Magnetic resonance in medicine. 2018 Jun;79(6):2996-3006. https://doi.org/10.1002/mrm.26963

2. Dymerska B, Eckstein K, Bachrata B, Siow B, Trattnig S, Shmueli K, Robinson SD. Phase unwrapping with a rapid opensource minimum spanning tree algorithm (ROMEO). Magnetic resonance in medicine. 2021 Apr;85(4):2294-308. https://doi.org/10.1002/mrm.28563

3. Sasaki M, Shibata E, Tohyama K, Takahashi J, Otsuka K, Tsuchiya K, Takahashi S, Ehara S, Terayama Y, Sakai A. Neuromelanin magnetic resonance imaging of locus ceruleus and substantia nigra in Parkinson's disease. Neuroreport. 2006 Jul 31;17(11):1215-8. https://doi.org/10.1097/01.wnr.0000227984.84927.a7

## Compilation

This project can be compiled and distributed as an executable using PyInstaller, the compilation process is described in the [`COMPILATION.md`](./COMPILATION.md) file.

## Related repositories

This DICOM to BIDS converter is a rewrite of Raul Cruces' [MPN 7T pipeline DICOM to BIDS converter](https://github.com/rcruces/MPN_7T_pipeline). The present converter aims to provide a similar behavior (up to versions) with enhanced safety checks, portability, performance, and maintainability.
