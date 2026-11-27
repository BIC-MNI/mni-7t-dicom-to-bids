# BIDS naming dictionary

The default MNI 7T DICOM to BIDS dictionary uses the following mapping.

The BIDS column omits subject, session, run labels, and file extensions. `echo-X` denotes an
echo index starting at 1; `part-Y` denotes `part-mag` or `part-phase` when available.

## Anatomical

| **N** | **7T Terra Siemens acquisition pattern** | **BIDS** | **Directory** |
|:-----:|:------------------------------------------|:---------|:-------------:|
| 1 | `anat-flair_acq-0*7iso_UPAdia` | `acq-UPAdia07_FLAIR` | `anat` |
| 2 | `anat-flair_acq-0*7mm_UPAdia` | `acq-UPAdia07_FLAIR` | `anat` |
| 3 | `anat-flair_acq-0*7iso_dev3_5SD_UP` | `acq-5SDUP07_FLAIR` | `anat` |
| 4 | `*anat-T1w_acq-mp2rage_0*7mm_CSptx_UNI_Images` | `acq-mp2rageCSPtx07_UNIT1` | `anat` |
| 5 | `*anat-T1w_acq-mp2rage_0*7mm_CSptx_UNI-DEN` | `acq-mp2rageCSPtx07_rec-denoised_UNIT1` | `anat` |
| 6 | `*anat-T1w_acq-mp2rage_0*7mm_CSptx_T1_Images` | `acq-mp2rageCSPtx07_T1map` | `anat` |
| 7 | `anat-T1w_acq_mprage_0*8mm_CSptx` | `acq-mprageCSPtx08_T1w` | `anat` |
| 8 | `anat-T1w_acq_mprage_0*8mm_CSx_ND` | `acq-mprageCSPtx08_T1w` | `anat` |
| 9 | `*anat-T1w_acq-mprage_0*7mm_UP` | `acq-mprageUP07_T1w` | `anat` |
| 10 | `*CLEAR-SWI_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-megre07_rec-CLEARSWI_swi` | `anat` |
| 11 | `*Romeo_P_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-megre07_rec-romeo_echo-X_part-phase_desc-phaseunwrap_t2starw` | `romeo` |
| 12 | `*Romeo_Mask_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-megre07_rec-romeo_desc-mask_t2starw` | `romeo` |
| 13 | `*Romeo_B0_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-megre07_rec-romeo_desc-B0_t2starw` | `romeo` |
| 14 | `Aspire_M_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-megre07_rec-aspire_part-mag_MEGRE` | `anat` |
| 15 | `Aspire_P_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-megre07_rec-aspire_part-phase_MEGRE` | `anat` |
| 16 | `*T2star_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-megre07_rec-aspire_T2starmap` | `anat` |
| 17 | `*EchoCombined_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-megre07_rec-aspire_desc-combined_T2starw` | `aspire` |
| 18 | `*sensitivity_corrected_mag_anat-T2star_acq-me_gre_0*7iso_ASPIRE` | `acq-megre07_rec-aspire_desc-combinedsenscor_T2starw` | `aspire` |
| 19 | `*T2Star_Images` | `acq-me_T2starmap` | `anat` |
| 20 | `*anat-T2star_acq-me_gre_07mm*` | `acq-me_echo-X_part-Y_T2starw` | `anat` |
| 21 | `*anat-T1w_acq-mp2rage_0*7mm_CSptx_INV1` | `acq-mp2rageCSPtx07_inv-1_MP2RAGE` | `anat` |
| 22 | `*anat-T1w_acq-mp2rage_0*7mm_CSptx_INV2` | `acq-mp2rageCSPtx07_inv-2_MP2RAGE` | `anat` |
| 23 | `*anat-T1w_acq-mp2rage_05mm_UP*_INV1*` | `acq-mp2rage05_inv-1_MP2RAGE` | `anat` |
| 24 | `*anat-T1w_acq-mp2rage_05mm_UP*_INV2*` | `acq-mp2rage05_inv-2_MP2RAGE` | `anat` |
| 25 | `*anat-T1w_acq-mp2rage_05mm_UP*_T1_Images*` | `acq-mp2rage05_T1map` | `anat` |
| 26 | `*anat-T1w_acq-mp2rage_05mm_UP*_UNI_Images*` | `acq-mp2rage05_UNIT1` | `anat` |
| 27 | `*cstfl-mp2rage-05mm_INV1` | `acq-cstfl_inv-1_MP2RAGE` | `anat` |
| 28 | `*cstfl-mp2rage-05mm_INV2` | `acq-cstfl_inv-2_MP2RAGE` | `anat` |
| 29 | `*cstfl-mp2rage-05mm_T1_Images` | `acq-cstfl_T1map` | `anat` |
| 30 | `*cstfl-mp2rage-05mm_UNI_Images` | `acq-cstfl_UNIT1` | `anat` |
| 31 | `*cstfl-mp2rage-05mm_UNI-DEN` | `acq-cstfl_rec-denoised_UNIT1` | `anat` |
| 32 | `*anat-mtw_acq-T1w_07mm` | `acq-mtw07_part-Y_T1w` | `anat` |
| 33 | `*anat-mtw_acq-MTON_07mm` | `acq-mtw07_mt-on_part-Y_MTR` | `anat` |
| 34 | `*anat-mtw_acq-MTOFF_07mm` | `acq-mtw07_mt-off_part-Y_MTR` | `anat` |
| 35 | `*_T1W` | `acq-MTR_T1w` | `anat` |
| 36 | `anat-nm_acq-MTboost_sag_0.55mm` | `acq-neuromelaninMTw_T1w` | `anat` |
| 37 | `CR_tfl_MTboost_sag7deg_0.55mm` | `acq-neuromelaninMTw_T1w` | `anat` |
| 38 | `*anat-angio_acq-tof_03mm_inplane` | `acq-tof03_angio` | `anat` |
| 39 | `*anat-angio_acq-tof_03mm_inplane_MIP_COR` | `acq-tof03_rec-MIPcor_angio` | `anat` |
| 40 | `*anat-angio_acq-tof_03mm_inplane_MIP_SAG` | `acq-tof03_rec-MIPsag_angio` | `anat` |
| 41 | `*anat-angio_acq-tof_03mm_inplane_MIP_TRA` | `acq-tof03_rec-MIPtra_angio` | `anat` |

## Diffusion-weighted images

| **N** | **7T Terra Siemens acquisition pattern** | **BIDS** | **Directory** |
|:-----:|:------------------------------------------|:---------|:-------------:|
| 1 | `dwi_acq_b0_PA_SBRef` | `acq-b0_dir-PA_part-Y_sbref` | `dwi` |
| 2 | `dwi_acq_b0_PA_acc9_SBRef` | `acq-b0_dir-PA_part-Y_sbref` | `dwi` |
| 3 | `*dwi_acq_b0*_PA_SBRef` | `acq-b0_dir-PA_part-Y_sbref` | `dwi` |
| 4 | `*dwi_acq_b0*_PA` | `acq-b0_dir-PA_part-Y_dwi` | `dwi` |
| 5 | `dwi_acq_b0_PA_acc9` | `acq-b0_dir-PA_part-Y_dwi` | `dwi` |
| 6 | `*dwi_acq_b0_PA_1p5iso_SBRef` | `acq-b01p5_dir-PA_part-Y_sbref` | `dwi` |
| 7 | `*dwi_acq_b0_PA_1p5iso` | `acq-b01p5_dir-PA_part-Y_dwi` | `dwi` |
| 8 | `*dwi_acq_multib_38dir_AP_acc9_SBRef` | `acq-multib38_dir-AP_part-Y_sbref` | `dwi` |
| 9 | `*dwi_acq_multib_38dir_AP_acc9_test_SBRef` | `acq-multib38Test_dir-AP_part-Y_sbref` | `dwi` |
| 10 | `*dwi_acq_multib_38dir_AP_acc9_1p5iso_SBRef` | `acq-multib381p5_dir-AP_part-Y_sbref` | `dwi` |
| 11 | `*dwi_acq_multib_70dir_AP_acc9_SBRef` | `acq-multib70_dir-AP_part-Y_sbref` | `dwi` |
| 12 | `dwi_acq_multib_108dir_AP_acc9_SBRef` | `acq-multib108_dir-AP_part-Y_sbref` | `dwi` |
| 13 | `*dwi_acq_multib_70dir_AP_acc9_1p5iso_SBRef` | `acq-multib701p5_dir-AP_part-Y_sbref` | `dwi` |
| 14 | `*dwi_acq_b300_10d-dir_AP_SBRef` | `acq-b300_dir-AP_part-Y_sbref` | `dwi` |
| 15 | `*dwi_acq_b700_40d-dir_AP_SBRef` | `acq-b700_dir-AP_part-Y_sbref` | `dwi` |
| 16 | `*dwi_acq_b2000_90d-dir_AP_SBRef` | `acq-b2000_dir-AP_part-Y_sbref` | `dwi` |
| 17 | `*dwi_acq_multib_38dir_AP_acc9` | `acq-multib38_dir-AP_part-Y_dwi` | `dwi` |
| 18 | `*dwi_acq_multib_38dir_AP_acc9_1p5iso` | `acq-multib381p5_dir-AP_part-Y_dwi` | `dwi` |
| 19 | `*dwi_acq_multib_38dir_AP_acc9_test` | `acq-multib38Test_dir-AP_part-Y_dwi` | `dwi` |
| 20 | `*dwi_acq_multib_70dir_AP_acc9` | `acq-multib70_dir-AP_part-Y_dwi` | `dwi` |
| 21 | `*dwi_acq_multib_70dir_AP_acc9_1p5iso` | `acq-multib701p5_dir-AP_part-Y_dwi` | `dwi` |
| 22 | `dwi_acq_multib_108dir_AP_acc9` | `acq-multib108_dir-AP_part-Y_dwi` | `dwi` |
| 23 | `*dwi_acq_b300_10d-dir_AP` | `acq-b300_dir-AP_part-Y_dwi` | `dwi` |
| 24 | `*dwi_acq_b700_40d-dir_AP` | `acq-b700_dir-AP_part-Y_dwi` | `dwi` |
| 25 | `*dwi_acq_b2000_90d-dir_AP` | `acq-b2000_dir-AP_part-Y_dwi` | `dwi` |

## Field maps

| **N** | **7T Terra Siemens acquisition pattern** | **BIDS** | **Directory** |
|:-----:|:------------------------------------------|:---------|:-------------:|
| 1 | `fmap-b1_tra_p2` | `acq-anat_TB1TFL`, `acq-sfam_TB1TFL` | `fmap` |
| 2 | `fmap-b1_acq-sag_p2` | `acq-anat_TB1TFL`, `acq-sfam_TB1TFL` | `fmap` |
| 3 | `*fmap-b1_acq-*_p2` | `acq-anat_TB1TFL`, `acq-sfam_TB1TFL` | `fmap` |
| 4 | `*fmap-fmri_acq-mbep2d_SE_19mm_dir-AP` | `acq-fmri_dir-AP_epi` | `fmap` |
| 5 | `*fmap-fmri_acq-mbep2d_SE_19mm_dir-PA` | `acq-fmri_dir-PA_epi` | `fmap` |
| 6 | `*fmap-fmri_acq-mbep2d_SE_19mm_dir-AP_Q1K` | `acq-fmriQ1K_dir-AP_epi` | `fmap` |
| 7 | `*fmap-fmri_acq-mbep2d_SE_19mm_dir-PA_Q1K` | `acq-fmriQ1K_dir-PA_epi` | `fmap` |

## Functional

| **N** | **7T Terra Siemens acquisition pattern** | **BIDS** | **Directory** |
|:-----:|:------------------------------------------|:---------|:-------------:|
| 1 | `func-cloudy_acq-ep2d_MJC_19mm` | `task-cloudy_echo-X_bold` | `func` |
| 2 | `func-present_acq-ep2d_MJC_19mm` | `task-present_echo-X_bold` | `func` |
| 3 | `*func-semphon1_acq-mbep2d_ME_19mm` | `task-semphon1_echo-X_part-Y_bold` | `func` |
| 4 | `*func-semphon2_acq-mbep2d_ME_19mm` | `task-semphon2_echo-X_part-Y_bold` | `func` |
| 5 | `func-cross_acq-ep2d_MJC_19mm` | `task-rest_echo-X_part-Y_bold` | `func` |
| 6 | `func-rsfmri_acq-multiE_1.9mm` | `task-rest_echo-X_part-Y_bold` | `func` |
| 7 | `*func-rsfmri_acq-mbep2d_ME_19mm` | `task-rest_echo-X_part-Y_bold` | `func` |
| 8 | `*func-rsfmri_acq-singleE_1*` | `task-rest_acq-singleE_bold` | `func` |
| 9 | `*func-rsfmri_acq-mbep2d_ME_19mm_Q1K` | `task-rest_acq-Q1K_echo-X_part-Y_bold` | `func` |
| 10 | `*func-epiencode_acq-mbep2d_ME_19mm*` | `task-epiencode_echo-X_part-Y_bold` | `func` |
| 11 | `*func-epiretrieve_acq-mbep2d_ME_19mm` | `task-epiretrieve_echo-X_part-Y_bold` | `func` |
| 12 | `*func-pattersep1_acq-mbep2d_ME_19mm` | `task-patternsep1_echo-X_part-Y_bold` | `func` |
| 13 | `*func-patter*sep2_acq-mbep2d_ME_19mm` | `task-patternsep2_echo-X_part-Y_bold` | `func` |
| 14 | `*func-semantic1_acq-mbep2d_ME_19mm` | `task-semantic1_echo-X_part-Y_bold` | `func` |
| 15 | `*func-semantic2_acq-mbep2d_ME_19mm` | `task-semantic2_echo-X_part-Y_bold` | `func` |
| 16 | `*func-spatial1_acq-mbep2d_ME_19mm` | `task-spatial1_echo-X_part-Y_bold` | `func` |
| 17 | `*func-spatial2_acq-mbep2d_ME_19mm` | `task-spatial2_echo-X_part-Y_bold` | `func` |
| 18 | `*func-movie*1_acq-mbep2d_ME_19mm` | `task-movies1_echo-X_part-Y_bold` | `func` |
| 19 | `*func-movie*2_acq-mbep2d_ME_19mm` | `task-movies2_echo-X_part-Y_bold` | `func` |
| 20 | `*func-movies3_acq-mbep2d_ME_19mm` | `task-movies3_echo-X_part-Y_bold` | `func` |
| 21 | `*func-movies4_acq-mbep2d_ME_19mm` | `task-movies4_echo-X_part-Y_bold` | `func` |
| 22 | `*func-caddy_acq-mbep2d_ME_19mm` | `task-caddy_echo-X_part-Y_bold` | `func` |
| 23 | `*func-harsh_acq-mbep2d_ME_19mm` | `task-harsh_echo-X_part-Y_bold` | `func` |
| 24 | `*func-pines_acq-mbep2d_ME_19mm` | `task-pines_echo-X_part-Y_bold` | `func` |
| 25 | `*func-bathroom_acq-mbep2d_ME_19mm` | `task-bathroom_echo-X_part-Y_bold` | `func` |
| 26 | `*func-audiobook1_acq-mbep2d_ME_19mm` | `task-audiobook1_echo-X_part-Y_bold` | `func` |
| 27 | `*func-audiobook2_acq-mbep2d_ME_19mm` | `task-audiobook2_echo-X_part-Y_bold` | `func` |
| 28 | `*func-oceans11_acq-mbep2d_ME_19mm` | `task-oceans11_echo-X_part-Y_bold` | `func` |
| 29 | `*func-social_acq-mbep2d_ME_19mm` | `task-social_echo-X_part-Y_bold` | `func` |
| 30 | `*func-sens1_acq-mbep2d_ME_19mm` | `task-sens2_echo-X_part-Y_bold` | `func` |
| 31 | `*func-sens2_acq-mbep2d_ME_19mm` | `task-sens1_echo-X_part-Y_bold` | `func` |
| 32 | `*func-slient1_acq-mbep2d_ME_19mm` | `task-salient_echo-X_part-Y_bold` | `func` |

## Abbreviation Glossary

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

## References

1. Eckstein K, Dymerska B, Bachrata B, Bogner W, Poljanc K, Trattnig S, Robinson SD. Computationally efficient combination of multi‐channel phase data from multi‐echo acquisitions (ASPIRE). Magnetic resonance in medicine. 2018 Jun;79(6):2996-3006. https://doi.org/10.1002/mrm.26963

2. Dymerska B, Eckstein K, Bachrata B, Siow B, Trattnig S, Shmueli K, Robinson SD. Phase unwrapping with a rapid opensource minimum spanning tree algorithm (ROMEO). Magnetic resonance in medicine. 2021 Apr;85(4):2294-308. https://doi.org/10.1002/mrm.28563

3. Sasaki M, Shibata E, Tohyama K, Takahashi J, Otsuka K, Tsuchiya K, Takahashi S, Ehara S, Terayama Y, Sakai A. Neuromelanin magnetic resonance imaging of locus ceruleus and substantia nigra in Parkinson's disease. Neuroreport. 2006 Jul 31;17(11):1215-8. https://doi.org/10.1097/01.wnr.0000227984.84927.a7

4. Gras et al. (2017). Homogeneous non-selective and slice-selective parallel-transmit excitations at 7 Tesla with universal pulses: A validation study on two commercial RF coils. https://doi.org/10.1371/journal.pone.0183562

5. Gras et al. (2018). Design of universal parallel-transmit refocusing kT-point pulses and application to 3D T2-weighted imaging at 7T. https://doi.org/10.1002/mrm.27001

6. Gras et al. (2019). Robust nonadiabatic T2 preparation using universal parallel-transmit kT-point pulses for 3D FLAIR imaging at 7 T. https://doi.org/10.1002/mrm.27645

7. Gras et al. (2017). Universal pulses: A new concept for calibration-free parallel transmission. https://doi.org/10.1002/mrm.26148

8. Van Damme et al. (2021). Universal nonselective excitation and refocusing pulses with improved robustness to off-resonance for Magnetic Resonance Imaging at 7 Tesla with parallel transmission. https://doi.org/10.1002/mrm.28441

9. Wu et al. (2018). The travelling pulses: multicenter evaluation of universal pulses at 7T. ISMRM abstract 1133. https://archive.ismrm.org/2018/1133.html

10. Eckstein K, Bachrata B, Hangel G, Widhalm G, Enzinger C, Barth M, Trattnig S, Robinson SD. Improved susceptibility weighted imaging at ultra-high field using bipolar multi-echo acquisition and optimized image processing: CLEAR-SWI. NeuroImage. 2021;237:118175. https://doi.org/10.1016/j.neuroimage.2021.118175

11. Hagberg et al. (2002). Real-time quantification of T(2)(*) changes using multiecho planar imaging and numerical methods. https://doi.org/10.1002/mrm.10283
