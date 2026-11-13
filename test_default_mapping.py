"""Public default-table contract; no private review inputs or GUI required."""
import csv
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from word_clean_core import W, load_mapping, process_txt, transform_xml

BASE = Path(__file__).parent
RETAINED = '晉戩為偽媯溈蒍羨盜茲孶縁敻粵晩鄕袞殼'
SHA256 = '05b2cd07ce887d74da0ffe36389dde22a655b120db71c53cb70d18fb7aedd4a4'


class DefaultMappingTests(unittest.TestCase):
    def setUp(self):
        self.path = BASE / '默认字表_新旧字形_v6.csv'
        self.mapping = load_mapping(self.path)

    def test_manifest_schema_hash_and_baseline(self):
        manifest = json.loads((BASE / 'mapping_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['file'], self.path.name)
        self.assertEqual(manifest['count'], 160)
        self.assertEqual(manifest['sha256'], SHA256)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), SHA256)
        with self.path.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[0], ['旧字型', '新字形'])
        self.assertEqual(len(rows) - 1, 160)
        self.assertEqual(len(self.mapping), 160)
        self.assertTrue(all(len(row) == 2 and all(len(c) == 1 for c in row) for row in rows[1:]))
        baseline = BASE / manifest['baseline']['file']
        self.assertEqual(hashlib.sha256(baseline.read_bytes()).hexdigest(), manifest['baseline']['sha256'])
        old = load_mapping(baseline)
        self.assertEqual(len(old), 122)
        self.assertEqual({a: self.mapping[a] for a in old}, old)
        self.assertEqual(len(self.mapping.keys() - old.keys()), 38)

    def test_latest_addition_and_editorial_choices(self):
        self.assertEqual(self.mapping['舎'], '舍')
        before_last_addition = dict(self.mapping)
        del before_last_addition['舎']
        self.assertEqual(len(before_last_addition), 159)
        for old, new in [('敎', '教'), ('吿', '告'), ('漑', '溉'), ('嚔', '嚏')]:
            self.assertEqual(self.mapping[old], new)
        self.assertEqual(len(RETAINED), 18)
        for char in RETAINED:
            self.assertNotIn(char, self.mapping)
        xml = f'<w:document xmlns:w="{W}"><w:t>{RETAINED}</w:t></w:document>'.encode()
        result, counts = transform_xml(xml, self.mapping)
        self.assertEqual(result, xml)
        self.assertFalse(counts)

    def test_every_pair_no_self_conflicts_chains_or_cycles(self):
        for old, new in self.mapping.items():
            with self.subTest(old=old):
                self.assertNotEqual(old, new)
                self.assertNotIn(new, self.mapping)
                xml = f'<w:document xmlns:w="{W}"><w:t>{old}</w:t></w:document>'.encode()
                result, counts = transform_xml(xml, self.mapping)
                self.assertEqual(ET.fromstring(result).find('{' + W + '}t').text, new)
                self.assertEqual(counts, {old: 1})
                self.assertEqual(transform_xml(result, self.mapping)[0], result)

    def test_supplementary_codepoints_and_txt_encodings(self):
        original = '𣙜𦨼寏愌瑍𠀀😀舎' + RETAINED
        expected = '榷𦨳𡨡𢚾𤥺𠀀😀舍' + RETAINED
        with tempfile.TemporaryDirectory() as directory:
            for encoding in ('utf-8', 'utf-8-sig', 'utf-16'):
                with self.subTest(encoding=encoding):
                    source = Path(directory) / (encoding + '.txt')
                    output = Path(directory) / (encoding + '-out.txt')
                    source.write_bytes((original + '\r\n').encode(encoding))
                    before = source.read_bytes()
                    counts = process_txt(source, self.mapping, output)
                    self.assertEqual(output.read_bytes().decode(encoding), expected + '\r\n')
                    self.assertEqual(source.read_bytes(), before)
                    self.assertEqual(sum(counts.values()), 6)

    def test_gui_default_metadata_and_tamper_detection_without_display(self):
        loader = importlib.machinery.SourceFileLoader('default160_gui', str(BASE / 'word_clean_gui.pyw'))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        gui = importlib.util.module_from_spec(spec)
        loader.exec_module(gui)
        self.assertEqual(gui.DEFAULT_PATH, self.path)
        self.assertEqual(gui.DEFAULT_SHA256, SHA256)
        self.assertTrue(gui.is_reviewed_default(self.path))
        self.assertEqual(gui.mapping_label(self.path), '新旧字形160条（项目逐项审阅）')
        with tempfile.TemporaryDirectory() as directory:
            custom = Path(directory) / 'custom.csv'
            custom.write_bytes(self.path.read_bytes())
            self.assertFalse(gui.is_reviewed_default(custom))
            gui.DEFAULT_PATH = custom
            self.assertTrue(gui.is_reviewed_default(custom))
            custom.write_bytes(custom.read_bytes() + b'\n')
            self.assertFalse(gui.is_reviewed_default(custom))


if __name__ == '__main__':
    unittest.main(verbosity=2)
