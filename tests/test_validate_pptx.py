"""Regression cases for lost image bytes, notes, tables, order and false passes."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_pptx as gate
from test_preserve_table_styles import make_deck, rewrite_deck, A, P, R, PR


def fixture(path):
    draft = path.with_suffix(".draft")
    make_deck(draft)
    with ZipFile(draft) as src, ZipFile(path, "x") as out:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "ppt/presentation.xml":
                data = data.replace(b'</p:presentation>', b'<p:sldSz cx="12192000" cy="6858000"/></p:presentation>')
            elif item.filename == "ppt/slides/slide1.xml":
                data = data.replace(b'</p:spTree>', b'<p:pic><p:blipFill><a:blip r:embed="pic"/></p:blipFill></p:pic></p:spTree>')
            elif item.filename == "ppt/notesSlides/notesSlide1.xml":
                data = (f'<p:notes xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree>'
                        '<p:sp><p:nvSpPr><p:nvPr><p:ph type="body"/></p:nvPr></p:nvSpPr>'
                        '<p:txBody><a:p><a:r><a:t>Keep teaching details</a:t></a:r></a:p></p:txBody>'
                        '</p:sp></p:spTree></p:cSld></p:notes>').encode()
            out.writestr(item, data)
        out.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        out.writestr('_rels/.rels', f'<Relationships xmlns="{PR}"><Relationship Id="doc" Type="{R}/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
        out.writestr('ppt/slides/_rels/slide1.xml.rels', f'<Relationships xmlns="{PR}">'
                     f'<Relationship Id="pic" Type="{R}/image" Target="../media/illustration.bin"/>'
                     f'<Relationship Id="notes" Type="{R}/notesSlide" Target="../notesSlides/notesSlide1.xml"/>'
                     '</Relationships>')


class PptxGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.pptx'
        fixture(self.source)
        self.base = gate.inspect(self.source)

    def changed(self, part, edit):
        target = self.root / ('change-%d.pptx' % len(list(self.root.iterdir())))
        rewrite_deck(self.source, target, part, edit)
        return target

    def test_known_valid_and_requirements(self):
        result = gate.check(self.base, 2, self.base)
        self.assertEqual(result['status'], 'pass')
        self.assertFalse(result['render_check_performed'])
        rule = {'slide_count': 2, 'slides': [{'slide': 1, 'text_contains': ['Ready'],
                'notes_contains': ['Keep teaching details'], 'tables': [[['A', 'Ready']]],
                'image_sha256': self.base['slides'][0]['images']}]}
        self.assertEqual(gate.check(self.base, requirements=rule)['status'], 'pass')

    def test_empty_embedded_image_is_blocked_even_when_zip_and_xml_are_valid(self):
        path = self.changed('ppt/media/illustration.bin', lambda b: b'')
        with self.assertRaisesRegex(ValueError, 'Empty media'):
            gate.inspect(path)
        result = subprocess.run([sys.executable, gate.__file__, 'check', str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)

    def test_replaced_nonempty_image_is_blocked_by_baseline(self):
        path = self.changed('ppt/media/illustration.bin', lambda b: b'wrong image')
        result = gate.check(gate.inspect(path), baseline=self.base, preserve=['images'])
        self.assertEqual(result['status'], 'fail')

    def test_notes_loss_and_table_number_change_are_blocked(self):
        for part, edit, field in [
            ('ppt/notesSlides/notesSlide1.xml', lambda b: b.replace(b'Keep teaching details', b''), 'notes'),
            ('ppt/slides/slide1.xml', lambda b: b.replace(b'<a:t>Ready</a:t>', b'<a:t>99%</a:t>'), 'tables'),
        ]:
            with self.subTest(field=field):
                actual = gate.inspect(self.changed(part, edit))
                result = gate.check(actual, baseline=self.base, preserve=[field])
                self.assertIn('Preserved '+field+' changed', result['findings'][0])

    def test_same_slide_count_does_not_hide_reordering(self):
        path = self.changed('ppt/presentation.xml', lambda b: b.replace(
            b'<p:sldId id="256" r:id="rId1"/><p:sldId id="257" r:id="rId2"/>',
            b'<p:sldId id="257" r:id="rId2"/><p:sldId id="256" r:id="rId1"/>'))
        actual = gate.inspect(path)
        self.assertEqual(gate.check(actual, baseline=self.base)['status'], 'fail')
        self.assertEqual(gate.check(actual, baseline=self.base, slide_map=[[1, 2], [2, 1]])['status'], 'pass')

    def test_broken_and_unresolved_relationships_are_blocked(self):
        for part, edit in [
            ('ppt/slides/_rels/slide1.xml.rels', lambda b: b.replace(b'illustration.bin', b'missing.bin')),
            ('ppt/slides/slide1.xml', lambda b: b.replace(b'r:embed="pic"', b'r:embed="missing"')),
        ]:
            with self.subTest(part=part), self.assertRaisesRegex(ValueError, 'relationship'):
                gate.inspect(self.changed(part, edit))

    def test_external_image_is_not_offline_delivery(self):
        path = self.changed('ppt/slides/_rels/slide1.xml.rels', lambda b: b.replace(
            b'Target="../media/illustration.bin"', b'Target="https://example.invalid/image.png" TargetMode="External"'))
        with self.assertRaisesRegex(ValueError, 'linked images'):
            gate.inspect(path)

    def test_invalid_contract_cannot_pass_silently(self):
        for rule in ({'slids': []}, {'slides': [{'slide': 1, 'notes_contain': ['x']}]},
                     {'slides': [{'slide': 1, 'tables': 'not a table'}]}):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                gate.check(self.base, requirements=rule)
        for mapping in ([[1, 1]], [[1, 1], [2, 1]], [[1, 1], [2, 3]]):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                gate.check(self.base, baseline=self.base, slide_map=mapping)

    def test_counts_and_missing_anchor_fail(self):
        self.assertEqual(gate.check(self.base, 3)['status'], 'fail')
        self.assertEqual(gate.check(self.base, requirements={'slides': [
            {'slide': 1, 'text_contains': ['not present']} ]})['status'], 'fail')

    def test_existing_report_is_not_overwritten(self):
        report = self.root / 'report.json'
        report.write_text('keep')
        result = subprocess.run([sys.executable, gate.__file__, 'check', str(self.source),
                                 '--report', str(report)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report.read_text(), 'keep')

    def test_size_change_is_not_a_preserving_edit(self):
        path = self.changed('ppt/presentation.xml', lambda b: b.replace(b'cx="12192000"', b'cx="9144000"'))
        self.assertIn('Slide dimensions changed from baseline',
                      gate.check(gate.inspect(path), baseline=self.base)['findings'])

    def test_missing_presentation_relationship_is_blocked(self):
        path = self.changed('_rels/.rels', lambda b: b.replace(b'/officeDocument', b'/other'))
        with self.assertRaisesRegex(ValueError, 'root relationship'):
            gate.inspect(path)

    def test_failed_inventory_write_removes_partial_json(self):
        report = self.root / 'failed.json'
        with patch.object(gate.json, 'dump', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                gate.write_json(report, self.base)
        self.assertFalse(report.exists())


if __name__ == '__main__':
    unittest.main()
