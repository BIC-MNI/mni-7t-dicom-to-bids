import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mni_7t_dicom_to_bids.args import Args, SkipErrorsArg, SkipUnknownsArg
from mni_7t_dicom_to_bids.convert_dicom_series import convert_dicom_series
from mni_7t_dicom_to_bids.dataclass import (
    BidsSessionInfo, Citation, ConvertedScan, DicomSeriesInfo, SequenceCredit,
)
from mni_7t_dicom_to_bids.dictionary import DicomDictionaryError, load_dicom_dictionary
from mni_7t_dicom_to_bids.map_dicom_series import create_conversion_plan
from mni_7t_dicom_to_bids.metadata.credits import patch_dataset_credits
from mni_7t_dicom_to_bids.pipeline import mni_7t_dicom_to_bids


class SequenceCreditsTests(unittest.TestCase):
    def test_protocol_credits_and_unrelated_variants(self):
        dictionary = load_dicom_dictionary()
        descriptions = [
            'func-cloudy_acq-ep2d_MJC_19mm', 'fmap-b1_tra_p2',
            'anat-T1w_acq-mp2rage_0.7mm_CSptx_INV1',
            'anat-T1w_acq_mprage_0.8mm_CSptx',
            'dwi_acq_multib_38dir_AP_acc9', 'dwi_acq_multib_70dir_AP_acc9_SBRef',
            'anat-T1w_acq-mp2rage_05mm_UP_UNI_Images',
            'anat-flair_acq-0.7iso_UPAdia',
            'Aspire_M_anat-T2star_acq-me_gre_0.7iso_ASPIRE',
            'anat-mtw_acq-MTON_07mm', 'anat-mtw_acq-MTOFF_07mm',
            'anat-nm_acq-MTboost_sag_0.55mm', 'anat-angio_acq-tof_03mm_inplane',
        ]
        plan = create_conversion_plan(
            [DicomSeriesInfo(name, i, []) for i, name in enumerate(descriptions)], dictionary,
        )
        self.assertFalse(plan.unknown_series)
        self.assertEqual(len(descriptions), sum(len(a.series) for a in plan.acquisitions))
        self.assertTrue(all(s.credit for a in plan.acquisitions for s in a.series))
        unrelated = create_conversion_plan(
            [DicomSeriesInfo('dwi_acq_multib_108dir_AP_acc9', 1, [])], dictionary,
        )
        self.assertIsNone(unrelated.acquisitions[0].series[0].credit)

    def test_merge_preserves_metadata_and_readme_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            description = {'Name': 'Existing', 'Acknowledgements': 'Original credit',
                           'ReferencesAndLinks': ['Original reference'],
                           'HowToAcknowledge': 'Original instructions'}
            path = root / 'dataset_description.json'
            path.write_text(json.dumps(description))
            readme = root / 'README.rst'
            readme.write_text('Original README\n')
            credit = SequenceCredit('Sequence A: provider.',
                                    (Citation('Paper A', 'https://doi.org/example'),))
            scans = [ConvertedScan(root / 'scan.nii.gz', credit=credit)] * 2
            patch_dataset_credits(root, scans)
            first = (path.read_text(), readme.read_text())
            patch_dataset_credits(root, scans)
            self.assertEqual(first, (path.read_text(), readme.read_text()))
            updated = json.loads(path.read_text())
            self.assertEqual(updated['HowToAcknowledge'], 'Original instructions')
            self.assertEqual(updated['ReferencesAndLinks'],
                             ['Original reference', 'Paper A https://doi.org/example'])
            self.assertIn('Original credit', updated['Acknowledgements'])
            self.assertEqual(readme.read_text(), 'Original README\n')
            self.assertFalse((root / 'README.md').exists())
            patch_dataset_credits(root, [])
            self.assertEqual(first, (path.read_text(), readme.read_text()))

    def test_invalid_credit_rejected_and_omitted_credit_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dictionary.json'
            mapping = {'series': 'example', 'datatype': 'anat', 'filename': 'T1w'}
            value = {'ignored-series': [], 'trim-series-suffixes': [], 'mappings': [mapping]}
            path.write_text(json.dumps(value))
            self.assertIsNone(load_dicom_dictionary(path).mappings[0].credit)
            for credit in ({'acknowledgement': ''}, {'acknowledgement': 'A', 'references': [3]},
                           {'acknowledgement': 'A', 'references': ['Legacy string']},
                           {'acknowledgement': 'A', 'references': [{'text': 'Paper'}]},
                           {'acknowledgement': 'A', 'references': [{'text': '', 'url': 'https://example.org'}]},
                           {'acknowledgement': 'A', 'references': [{'text': 'Paper', 'url': 'not a URL'}]},
                           {'acknowledgement': 'A', 'unexpected': True}):
                mapping['credit'] = credit
                path.write_text(json.dumps(value))
                with self.assertRaises(DicomDictionaryError):
                    load_dicom_dictionary(path)

    def test_structured_references_deduplicate_by_url(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            url = 'https://doi.org/10.1002/mrm.26963'
            value = {'ignored-series': [], 'trim-series-suffixes': [], 'mappings': [{
                'series': 'example', 'datatype': 'anat', 'filename': 'T1w',
                'credit': {'acknowledgement': 'Credit', 'references': [
                    {'text': 'Paper A', 'url': url}, {'text': 'Alternate text', 'url': url},
                ]},
            }]}
            dictionary_path = root / 'dictionary.json'
            dictionary_path.write_text(json.dumps(value))
            credit = load_dicom_dictionary(dictionary_path).mappings[0].credit
            self.assertEqual(credit.references, (Citation('Paper A', url),))
            description_path = root / 'dataset_description.json'
            for existing in (url, 'Existing citation ' + url):
                description_path.write_text(json.dumps({'ReferencesAndLinks': [existing]}))
                patch_dataset_credits(root, [ConvertedScan(root / 'scan.nii.gz', credit=credit)])
                self.assertEqual(json.loads(description_path.read_text())['ReferencesAndLinks'], [existing])

    def test_sidecar_credit_and_successful_scan_propagation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.dcm'
            source.write_bytes(b'fixture')
            plan = create_conversion_plan(
                [DicomSeriesInfo('anat-angio_acq-tof_03mm_inplane', 1, [source])],
                load_dicom_dictionary(),
            )
            planned = plan.acquisitions[0].series[0]
            planned.sidecar['Description'] = 'Configured description.'
            args = Args(root, root / 'bids', '01', '01', None,
                        SkipUnknownsArg(), SkipErrorsArg(), False, True)

            def fake_niix(dicom_path, output_path, filename, args, **kwargs):
                (output_path / (filename + '.nii.gz')).write_bytes(b'fixture')
                (output_path / (filename + '.json')).write_text('{"Manufacturer": "Siemens"}')

            with patch('mni_7t_dicom_to_bids.convert_dicom_series.run_dicom_to_niix', fake_niix):
                result = convert_dicom_series(BidsSessionInfo('01', '01'), plan, args)
            self.assertEqual(len(result.scans), 1)
            self.assertEqual(result.scans[0].credit, planned.credit)
            sidecar = next((root / 'bids').rglob('*.json'))
            metadata = json.loads(sidecar.read_text())
            self.assertEqual(metadata['Manufacturer'], 'Siemens')
            self.assertTrue(metadata['Description'].startswith('Configured description.'))
            self.assertIn('Siemens product sequence', metadata['Description'])
            with patch('mni_7t_dicom_to_bids.convert_dicom_series.run_dicom_to_niix',
                       side_effect=RuntimeError('Simulated failed conversion')):
                failed = convert_dicom_series(BidsSessionInfo('01', '01'), plan, args)
            self.assertFalse(failed.scans)

    def test_pipeline_routes_derivative_credits_and_honors_no_dataset_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [
                DicomSeriesInfo('anat-angio_acq-tof_03mm_inplane', 1, []),
                DicomSeriesInfo('EchoCombined_anat-T2star_acq-me_gre_0.7iso_ASPIRE', 2, []),
                DicomSeriesInfo('CLEAR-SWI_anat-T2star_acq-me_gre_0.7iso_ASPIRE', 3, []),
            ]
            args = Args(root, root, '01', '01', None,
                        SkipUnknownsArg(), SkipErrorsArg(), False, False)

            def fake_niix(dicom_path, output_path, filename, args, **kwargs):
                (output_path / (filename + '.nii.gz')).write_bytes(b'fixture')
                (output_path / (filename + '.json')).write_text('{}')

            with patch('mni_7t_dicom_to_bids.pipeline.check_dicom_to_niix'), \
                 patch('mni_7t_dicom_to_bids.pipeline.group_dicom_series', return_value=sources), \
                 patch('mni_7t_dicom_to_bids.convert_dicom_series.run_dicom_to_niix', fake_niix):
                mni_7t_dicom_to_bids(args)
            raw = json.loads((root / 'dataset_description.json').read_text())
            derivative = json.loads((root / 'derivatives/aspire/dataset_description.json').read_text())
            self.assertIn('Siemens product sequence', raw['Acknowledgements'])
            self.assertIn('Simon Robinson', raw['Acknowledgements'])
            self.assertIn('Simon Robinson', derivative['Acknowledgements'])
            self.assertTrue(any('10.1002/mrm.26963' in ref for ref in derivative['ReferencesAndLinks']))
            sidecar = next((root / 'derivatives/aspire').rglob('*T2starw.json'))
            self.assertIn('10.1002/mrm.26963', json.loads(sidecar.read_text())['Description'])
            clear_sidecar = next(root.rglob('*rec-CLEARSWI_swi.json'))
            clear_description = json.loads(clear_sidecar.read_text())['Description']
            self.assertEqual(clear_description.count('10.1016/j.neuroimage.2021.118175'), 1)
            self.assertIn('Eckstein K, Bachrata B', clear_description)
            self.assertIn('Susceptibility-weighted image reconstructed using CLEAR-SWI', clear_description)
            self.assertEqual(sum('10.1016/j.neuroimage.2021.118175' in ref
                                 for ref in raw['ReferencesAndLinks']), 1)
            self.assertNotIn('Siemens product sequence', derivative['Acknowledgements'])
            self.assertFalse(list(root.rglob('README*')))


if __name__ == '__main__':
    unittest.main()
