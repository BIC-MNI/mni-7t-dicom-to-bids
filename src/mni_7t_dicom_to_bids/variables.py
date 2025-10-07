# MNI (MPN,MICA,JBL 7T Series) DICOM2BIDS DICTIONARY
# Mapping DICOM series to BIDS information.
# The first key if the BIDS data type name.
# The second key is the BIDS acquisition name.
# The value is a DICOM series description or a list of DICOM series descriptions
# for that BIDS data type and acquisition.
# Current series: MPN, MICA-lab, JBL.

bids_dicom_mappings: dict[str, dict[str, list[str] | str]] = {
    'anat': {
        # FLAIR
        'FLAIR': [
            'anat-flair_acq-0*7iso_UPAdia',
            'anat-flair_acq-0*7mm_UPAdia',
            'anat-flair_acq-0*7iso_dev3_5SD_UP',
        ],

        # UNIT1
        'UNIT1'               : '*anat-T1w_acq-mp2rage_0*7mm_CSptx_UNI_Images',
        'desc-denoised_UNIT1' : '*anat-T1w_acq-mp2rage_0*7mm_CSptx_UNI-DEN',

        # T1
        'T1map' : '*anat-T1w_acq-mp2rage_0*7mm_CSptx_T1_Images',
        'T1w'   : [
            'anat-T1w_acq_mprage_0*8mm_CSptx',
            'anat-T1w_acq_mprage_0*8mm_CSx_ND',
            '*anat-T1w_acq-mprage_0*7mm_UP',
        ],

        # T2
        'acq-SWI_T2starw'                      : '*CLEAR-SWI_anat-T2star_acq-me_gre_0*7iso_ASPIRE',
        'acq-romeo_T2starw'                    : '*Romeo_P_anat-T2star_acq-me_gre_0*7iso_ASPIRE',
        'acq-romeo_desc-mask_T2starw'          : '*Romeo_Mask_anat-T2star_acq-me_gre_0*7iso_ASPIRE',
        'acq-romeo_desc-unwrapped_T2starw'     : '*Romeo_B0_anat-T2star_acq-me_gre_0*7iso_ASPIRE',
        'acq-aspire_T2starw': [
            'Aspire_M_anat-T2star_acq-me_gre_0*7iso_ASPIRE',
            'Aspire_P_anat-T2star_acq-me_gre_0*7iso_ASPIRE',
            '*T2star_anat-T2star_acq-me_gre_0*7iso_ASPIRE',
        ],
        'acq-aspire_desc-echoCombined_T2starw' : '*EchoCombined_anat-T2star_acq-me_gre_0*7iso_ASPIRE',
        'acq-aspire_desc-echoCombinedSensitivityCorrected_T2starw':
            '*sensitivity_corrected_mag_anat-T2star_acq-me_gre_0*7iso_ASPIRE',
        'T2map': '*T2Star_Images',
        'acq-me_T2starw': '*anat-T2star_acq-me_gre_07mm*',

        # 0.7mm MP2RAGE
        'inv-1_MP2RAGE': '*anat-T1w_acq-mp2rage_0*7mm_CSptx_INV1',
        'inv-2_MP2RAGE': '*anat-T1w_acq-mp2rage_0*7mm_CSptx_INV2',

        # 0.5mm MP2RAGE
        'acq-05mm_inv-1_MP2RAGE': '*anat-T1w_acq-mp2rage_05mm_UP*_INV1*',
        'acq-05mm_inv-2_MP2RAGE': '*anat-T1w_acq-mp2rage_05mm_UP*_INV2*',
        'acq-05mm_T1map': '*anat-T1w_acq-mp2rage_05mm_UP*_T1_Images*',
        'acq-05mm_UNIT1': '*anat-T1w_acq-mp2rage_05mm_UP*_UNI_Images*',

        # High-resolution MP2RAGE - CSTFL - Compressed sensing turboflash
        'acq-cstfl_inv-1_MP2RAGE': '*cstfl-mp2rage-05mm_INV1',
        'acq-cstfl_inv-2_MP2RAGE': '*cstfl-mp2rage-05mm_INV2',
        'acq-cstfl_T1map': '*cstfl-mp2rage-05mm_T1_Images',
        'acq-cstfl_UNIT1': '*cstfl-mp2rage-05mm_UNI_Images',
        'acq-cstflDenoised_UNIT1': '*cstfl-mp2rage-05mm_UNI-DEN',

        # MTW
        'acq-mtw_T1w'        : '*anat-mtw_acq-T1w_07mm',
        'acq-mtw_mt-on_MTR'  : '*anat-mtw_acq-MTON_07mm',
        'acq-mtw_mt-off_MTR' : '*anat-mtw_acq-MTOFF_07mm',
        'acq-MTR_T1w': '*_T1W',

        # NEUROMELANIN
        'acq-neuromelaninMTw_T1w': [
            'anat-nm_acq-MTboost_sag_0.55mm',
            'CR_tfl_MTboost_sag7deg_0.55mm',
        ],

        # ANGIO
        'angio'         : '*anat-angio_acq-tof_03mm_inplane',
        'acq-cor_angio' : '*anat-angio_acq-tof_03mm_inplane_MIP_COR',
        'acq-sag_angio' : '*anat-angio_acq-tof_03mm_inplane_MIP_SAG',
        'acq-tra_angio' : '*anat-angio_acq-tof_03mm_inplane_MIP_TRA',
    },
    'dwi': {
        # B0
        'acq-b0_dir-PA_sbref': [
            'dwi_acq_b0_PA_SBRef',
            'dwi_acq_b0_PA_acc9_SBRef',
            '*dwi_acq_b0*_PA_SBRef',
        ],
        'acq-b0_dir-PA_dwi': [
            '*dwi_acq_b0*_PA',
            'dwi_acq_b0_PA_acc9',
        ],
        'acq-b01p5_dir-PA_sbref': '*dwi_acq_b0_PA_1p5iso_SBRef',
        'acq-b01p5_dir-PA_dwi': '*dwi_acq_b0_PA_1p5iso',

        # SBREF
        'acq-multib38_dir-AP_sbref': '*dwi_acq_multib_38dir_AP_acc9_SBRef',
        'acq-multib38Test_dir-AP_sbref': '*dwi_acq_multib_38dir_AP_acc9_test_SBRef',
        'acq-multib381p5_dir-AP_sbref': '*dwi_acq_multib_38dir_AP_acc9_1p5iso_SBRef',
        'acq-multib70_dir-AP_sbref': '*dwi_acq_multib_70dir_AP_acc9_SBRef',
        'acq-multib108_dir-AP_sbref': 'dwi_acq_multib_108dir_AP_acc9_SBRef',
        'acq-multib701p5_dir-AP_sbref': '*dwi_acq_multib_70dir_AP_acc9_1p5iso_SBRef',
        'acq-b300_dir-AP_sbref': '*dwi_acq_b300_10d-dir_AP_SBRef',
        'acq-b700_dir-AP_sbref': '*dwi_acq_b700_40d-dir_AP_SBRef',
        'acq-b2000_dir-AP_sbref': '*dwi_acq_b2000_90d-dir_AP_SBRef',

        # DWI
        'acq-multib38_dir-AP_dwi': '*dwi_acq_multib_38dir_AP_acc9',
        'acq-multib381p5_dir-AP_dwi': '*dwi_acq_multib_38dir_AP_acc9_1p5iso',
        'acq-multib38Test_dir-AP_dwi': '*dwi_acq_multib_38dir_AP_acc9_test',
        'acq-multib70_dir-AP_dwi': '*dwi_acq_multib_70dir_AP_acc9',
        'acq-multib701p5_dir-AP_dwi': '*dwi_acq_multib_70dir_AP_acc9_1p5iso',
        'acq-multib108_dir-AP_dwi': 'dwi_acq_multib_108dir_AP_acc9',
        'acq-b300_dir-AP_dwi': '*dwi_acq_b300_10d-dir_AP',
        'acq-b700_dir-AP_dwi': '*dwi_acq_b700_40d-dir_AP',
        'acq-b2000_dir-AP_dwi': '*dwi_acq_b2000_90d-dir_AP',
    },
    'fmap': {
        # TB1TFL
        'acq-anat_TB1TFL': [
            'fmap-b1_tra_p2',
            'fmap-b1_acq-sag_p2',
            '*fmap-b1_acq-*_p2',
        ],

        # EPI
        'acq-fmri_dir-AP_epi': '*fmap-fmri_acq-mbep2d_SE_19mm_dir-AP',
        'acq-fmri_dir-PA_epi': '*fmap-fmri_acq-mbep2d_SE_19mm_dir-PA',
        'acq-fmriQ1K_dir-AP_epi': '*fmap-fmri_acq-mbep2d_SE_19mm_dir-AP_Q1K',
        'acq-fmriQ1K_dir-PA_epi': '*fmap-fmri_acq-mbep2d_SE_19mm_dir-PA_Q1K',
    },
    'func': {
        # BOLD
        'task-cloudy_bold'   : 'func-cloudy_acq-ep2d_MJC_19mm',
        'task-present_bold'  : 'func-present_acq-ep2d_MJC_19mm',
        'task-semphon1_bold' : '*func-semphon1_acq-mbep2d_ME_19mm',
        'task-semphon2_bold' : '*func-semphon2_acq-mbep2d_ME_19mm',
        'task-rest_bold': [
            'func-cross_acq-ep2d_MJC_19mm',
            'func-rsfmri_acq-multiE_1.9mm',
            '*func-rsfmri_acq-mbep2d_ME_19mm',
        ],
        'task-rest_acq-singleE_bold' : '*func-rsfmri_acq-singleE_1*',
        'task-rest_acq-Q1K_bold'     : '*func-rsfmri_acq-mbep2d_ME_19mm_Q1K',
        'task-epiencode_bold'        : '*func-epiencode_acq-mbep2d_ME_19mm*',
        'task-epiretrieve_bold'      : '*func-epiretrieve_acq-mbep2d_ME_19mm',
        'task-patternsep1_bold'      : '*func-pattersep1_acq-mbep2d_ME_19mm',
        'task-patternsep2_bold'      : '*func-patter*sep2_acq-mbep2d_ME_19mm',
        'task-semantic1_bold'        : '*func-semantic1_acq-mbep2d_ME_19mm',
        'task-semantic2_bold'        : '*func-semantic2_acq-mbep2d_ME_19mm',
        'task-spatial1_bold'         : '*func-spatial1_acq-mbep2d_ME_19mm',
        'task-spatial2_bold'         : '*func-spatial2_acq-mbep2d_ME_19mm',
        'task-movies1_bold'          : '*func-movie*1_acq-mbep2d_ME_19mm',
        'task-movies2_bold'          : '*func-movie*2_acq-mbep2d_ME_19mm',
        'task-movies3_bold'          : '*func-movies3_acq-mbep2d_ME_19mm',
        'task-movies4_bold'          : '*func-movies4_acq-mbep2d_ME_19mm',
        'task-caddy_bold'            : '*func-caddy_acq-mbep2d_ME_19mm',
        'task-harsh_bold'            : '*func-harsh_acq-mbep2d_ME_19mm',
        'task-pines_bold'            : '*func-pines_acq-mbep2d_ME_19mm',
        'task-bathroom_bold'         : '*func-bathroom_acq-mbep2d_ME_19mm',
        'task-audiobook1_bold'       : '*func-audiobook1_acq-mbep2d_ME_19mm',
        'task-audiobook2_bold'       : '*func-audiobook2_acq-mbep2d_ME_19mm',
        'task-oceans11_bold'         : '*func-oceans11_acq-mbep2d_ME_19mm',
        'task-social_bold'           : '*func-social_acq-mbep2d_ME_19mm',
        'task-sens2_bold'            : '*func-sens1_acq-mbep2d_ME_19mm',
        'task-sens1_bold'            : '*func-sens2_acq-mbep2d_ME_19mm',
        'task-salient_bold'          : '*func-slient1_acq-mbep2d_ME_19mm',
    }
}

# List of DICOM series descriptions that are ignored in the BIDS conversion.
bids_dicom_ignores: list[str] = [
    'AAHead_Scout_32ch-head-coil',
    'AAHead_Scout_32ch-head-coil_MPR_sag',
    'AAHead_Scout_32ch-head-coil_MPR_tra',
    'AAHead_Scout_32ch-head-coil_MPR_cor',
    'ADD_RUN1-4',
    'PhoenixZIPReport',
]

# The order in which the BIDS entities should appear in a BIDS file name.
# This order is taken from the BIDS specification entity table:
# https://bids-specification.readthedocs.io/en/stable/appendices/entity-table.html
bids_label_order = [
    'sub',
    'ses',
    'task',
    'acq',
    'ce',
    'rec',
    'inv',
    'mt',
    'dir',
    'run',
    'echo',
    'part',
    'chunk',
    'desc',  # Note that 'desc' is not in the entity table.
]
