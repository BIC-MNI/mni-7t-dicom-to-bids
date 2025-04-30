# Dictionary mapping the DICOM series to BIDS information.
# The first key if the BIDS data type name.
# The second key is the BIDS acquisition name.
# The value is a DICOM series description or a list of DICOM series descriptions
# for that BIDS data type and acquisition.

bids_dicom_mappings: dict[str, dict[str, list[str] | str]] = {
    'anat': {
        # FLAIR
        'FLAIR': 'anat-flair_acq-0p7iso_UPAdia',
        # UNIT1
        'UNIT1'              : 'anat-T1w_acq-mp2rage_0.7mm_CSptx_UNI_Images',
        'desc-denoised_UNIT1' : 'anat-T1w_acq-mp2rage_0.7mm_CSptx_UNI-DEN',
        # T1
        'T1map' : 'anat-T1w_acq-mp2rage_0.7mm_CSptx_T1_Images',
        'T1w'   : 'anat-T1w_acq_mprage_0.8mm_CSptx',
        # T2
        'acq-aspire_desc-echoCombined_T2starw' : 'EchoCombined_anat-T2star_acq-me_gre_0.7iso_ASPIRE',
        'acq-SWI_T2starw'                      : 'CLEAR-SWI_anat-T2star_acq-me_gre_0.7iso_ASPIRE',
        'acq-romeo_desc-mask_T2starw'          : 'Romeo_Mask_anat-T2star_acq-me_gre_0.7iso_ASPIRE',
        'acq-romeo_T2starw'                    : 'Romeo_P_anat-T2star_acq-me_gre_0.7iso_ASPIRE',
        'acq-romeo_desc-unwrapped_T2starw'     : 'Romeo_B0_anat-T2star_acq-me_gre_0.7iso_ASPIRE',
        'acq-aspire_T2starw': [
            'Aspire_M_anat-T2star_acq-me_gre_0.7iso_ASPIRE',
            'Aspire_P_anat-T2star_acq-me_gre_0.7iso_ASPIRE',
            'T2star_anat-T2star_acq-me_gre_0.7iso_ASPIRE',
        ],
        'acq-aspire_desc-echoCombinedSensitivityCorrected_T2starw': [
            'sensitivity_corrected_mag_anat-T2star_acq-me_gre_0.7iso_ASPIRE',
        ],
        # 0.7mm MP2RAGE
        'inv-1_MP2RAGE': 'anat-T1w_acq-mp2rage_0.7mm_CSptx_INV1',
        'inv-2_MP2RAGE': 'anat-T1w_acq-mp2rage_0.7mm_CSptx_INV2',
        # 0.5mm MP2RAGE
        'acq-05mm_inv-1_MP2RAGE': 'anat-T1w_acq-mp2rage_05mm_UP_INV1',
        'acq-05mm_inv-2_MP2RAGE': 'anat-T1w_acq-mp2rage_05mm_UP_INV2',
        'acq-05mm_T1map': 'anat-T1w_acq-mp2rage_05mm_UP_T1_Images',
        'acq-05mm_UNIT1': 'anat-T1w_acq-mp2rage_05mm_UP_UNI_Images',
        # MTW
        'acq-mtw_T1w'        : 'anat-mtw_acq-T1w_07mm',
        'acq-mtw_mt-on_MTR'  : 'anat-mtw_acq-MTON_07mm',
        'acq-mtw_mt-off_MTR' : 'anat-mtw_acq-MTOFF_07mm',
        # NEUROMELANIN
        'acq-neuromelaninMTw_T1w': 'anat-nm_acq-MTboost_sag_0.55mm',
        # ANGIO
        'angio'         : 'anat-angio_acq-tof_03mm_inplane',
        'acq-cor_angio' : 'anat-angio_acq-tof_03mm_inplane_MIP_COR',
        'acq-sag_angio' : 'anat-angio_acq-tof_03mm_inplane_MIP_SAG',
        'acq-tra_angio' : 'anat-angio_acq-tof_03mm_inplane_MIP_TRA',
    },
    'dwi': {
        # B0
        'acq-b0_dir-PA_sbref' : 'dwi_acq_b0_PA_SBRef',
        'acq-b0_dir-PA_dwi'   : 'dwi_acq_b0_PA',
        # SBREF
        'acq-multib38_dir-AP_sbref': 'dwi_acq_multib_38dir_AP_acc9_SBRef',
        'acq-multib70_dir-AP_sbref': 'dwi_acq_multib_70dir_AP_acc9_SBRef',
        # DWI
        'acq-multib38_dir-AP_dwi': 'dwi_acq_multib_38dir_AP_acc9',
        'acq-multib70_dir-AP_dwi': 'dwi_acq_multib_70dir_AP_acc9',
    },
    'fmap': {
        # TB1TFL
        'acq-anat_TB1TFL': [
            'fmap-b1_tra_p2',
            'fmap-b1_acq-sag_p2'
        ],
        # EPI
        'acq-fmri_dir-AP_epi': 'fmap-fmri_acq-mbep2d_SE_19mm_dir-AP',
        'acq-fmri_dir-PA_epi': 'fmap-fmri_acq-mbep2d_SE_19mm_dir-PA',
    },
    'func': {
        # BOLD
        'task-cloudy_bold'   : 'func-cloudy_acq-ep2d_MJC_19mm',
        'task-present_bold'  : 'func-present_acq-ep2d_MJC_19mm',
        'task-semphon1_bold' : 'func-semphon1_acq-mbep2d_ME_19mm',
        'task-semphon2_bold' : 'func-semphon2_acq-mbep2d_ME_19mm',
        'task-rest_bold': [
            'func-cross_acq-ep2d_MJC_19mm',
            'func-rsfmri_acq-multiE_1.9mm',
            'func-rsfmri_acq-mbep2d_ME_19mm',
        ],
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
    # Paris non-diagnostic files
    'anat-mtw_acq-MTON_07mm_ND',
    'anat-mtw_acq-MTOFF_07mm_ND',
    'anat-mtw_acq-T1w_07mm_ND',
    'anat-nm_acq-MTboost_sag_0.55mm_ND',
    # TODO: How to map this one ?
    'fmap-b1_tra_p2_B1',
]

# The order in which the BIDS labels should appear in a BIDS acquisition name.
bids_label_order = ['sub', 'ses', 'acq', 'desc', 'task', 'inv', 'run', 'echo', 'mt', 'dir', 'part']
