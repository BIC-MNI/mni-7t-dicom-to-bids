import copy
import json
import tempfile
import unittest
from pathlib import Path

from mni_7t_dicom_to_bids.dictionary import DicomDictionaryError, load_dicom_dictionary


class DictionaryDefinitionsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'templates').mkdir()
        (self.root / 'templates/example.json').write_text(json.dumps({
            'DatasetType': 'derivative', 'GeneratedBy': [{'Name': 'example'}],
        }))
        self.citation = {'text': 'Example paper.', 'url': 'https://example.org/paper'}
        self.derivative = {'name': 'example', 'dataset-description': 'templates/example.json'}
        self.mapping = {
            'series': 'example', 'datatype': 'anat', 'filename': 'T1w',
            'derivative': 'processed',
            'credit': {'acknowledgement': 'Provider', 'references': ['paper']},
        }
        self.value = {
            'ignored-series': [], 'trim-series-suffixes': [],
            'references': {'paper': self.citation},
            'derivatives': {'processed': self.derivative},
            'mappings': [self.mapping],
        }

    def load(self, value):
        path = self.root / 'dictionary.json'
        path.write_text(json.dumps(value))
        return load_dicom_dictionary(path)

    def test_named_definitions_match_inline_values_and_resolve_relative_templates(self):
        named = self.load(self.value)
        inline = copy.deepcopy(self.value)
        inline.pop('references')
        inline.pop('derivatives')
        inline['mappings'][0]['derivative'] = self.derivative
        inline['mappings'][0]['credit']['references'] = [self.citation]
        self.assertEqual(named, self.load(inline))
        self.assertEqual(named.mappings[0].dataset.name, 'example')
        self.assertEqual(named.mappings[0].dataset.dataset_description['DatasetType'], 'derivative')
        self.assertEqual(named.mappings[0].credit.references[0].url, self.citation['url'])

    def test_mixed_references_deduplicate_by_url_and_default_to_empty(self):
        self.mapping['credit']['references'] = ['paper', self.citation]
        self.assertEqual(len(self.load(self.value).mappings[0].credit.references), 1)
        self.mapping['credit'].pop('references')
        self.assertEqual(self.load(self.value).mappings[0].credit.references, ())
        self.mapping.pop('derivative')
        self.assertFalse(self.load(self.value).mappings[0].dataset.is_derivative)

    def test_undefined_names_report_mapping_location(self):
        for field, pattern in [('references', r"mappings\[0\].credit.references\[0\].*undefined reference 'paper'"),
                               ('derivatives', r"mappings\[0\].derivative.*undefined derivative 'processed'")]:
            value = copy.deepcopy(self.value)
            value[field] = {}
            with self.subTest(field=field), self.assertRaisesRegex(DicomDictionaryError, pattern):
                self.load(value)

    def test_invalid_unused_definitions_are_rejected(self):
        for section, definition in [
            ('references', {'text': 'Missing URL'}),
            ('references', {'text': 'Invalid URL', 'url': 'file:///paper'}),
            ('references', 'paper'),
            ('derivatives', {'name': 'invalid name', 'dataset-description': 'templates/example.json'}),
            ('derivatives', None),
            ('derivatives', 'processed'),
        ]:
            value = copy.deepcopy(self.value)
            value[section]['unused'] = definition
            with self.subTest(section=section, definition=definition):
                with self.assertRaisesRegex(DicomDictionaryError, section + r'.unused'):
                    self.load(value)
        for section in ('references', 'derivatives'):
            value = copy.deepcopy(self.value)
            value[section] = []
            with self.subTest(section=section), self.assertRaises(DicomDictionaryError):
                self.load(value)

    def test_conflicting_named_and_inline_derivatives_are_rejected(self):
        (self.root / 'templates/other.json').write_text(json.dumps({
            'DatasetType': 'derivative', 'GeneratedBy': [{'Name': 'different'}],
        }))
        other = {'name': 'example', 'dataset-description': 'templates/other.json'}
        self.mapping['derivative'] = other
        with self.assertRaisesRegex(DicomDictionaryError, r'mappings\[0\].derivative conflicts'):
            self.load(self.value)
        self.mapping['derivative'] = 'processed'
        self.value['derivatives']['unused'] = other
        with self.assertRaisesRegex(DicomDictionaryError, 'derivatives.unused conflicts'):
            self.load(self.value)

    def test_duplicate_definition_keys_are_rejected(self):
        path = self.root / 'dictionary.json5'
        path.write_text('''{
          "ignored-series": [], "trim-series-suffixes": [], "mappings": [],
          "references": {
            "paper": {"text": "First", "url": "https://example.org/first"},
            "paper": {"text": "Second", "url": "https://example.org/second"}
          }
        }''')
        with self.assertRaises(DicomDictionaryError):
            load_dicom_dictionary(path)


if __name__ == '__main__':
    unittest.main()
