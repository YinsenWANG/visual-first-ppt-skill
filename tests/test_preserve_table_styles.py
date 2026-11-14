"""Exercise preservation and refusal rules with synthetic OOXML packages.

These are package-level fixtures, not a substitute for rendering a real PPTX.
Run from the repository root: python3 -m unittest discover -s tests -v
"""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from zipfile import ZipFile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/preserve_table_styles.py"
SPEC = importlib.util.spec_from_file_location("preserve_table_styles", SCRIPT)
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)
A = HELPER.NS["a"]
P = HELPER.NS["p"]
R = HELPER.NS["r"]
PR = HELPER.NS["pr"]
STYLE = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"


def table_xml(label, fill):
    cells = "".join(
        f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>{text}</a:t>'
        f'</a:r></a:p></a:txBody><a:tcPr><a:solidFill><a:srgbClr val="{fill}"/>'
        '</a:solidFill></a:tcPr></a:tc>'
        for text in [label, "Ready"]
    )
    return (f'<a:tbl><a:tblPr><a:tableStyleId>{STYLE}</a:tableStyleId></a:tblPr>'
            '<a:tblGrid><a:gridCol w="1000000"/><a:gridCol w="2000000"/></a:tblGrid>'
            f'<a:tr h="400000">{cells}</a:tr></a:tbl>')


def slide_xml(label, fill):
    return (f'<p:sld xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"><p:cSld><p:spTree>'
            f'<p:sp><p:txBody><a:p><a:r><a:t>Unchanged {label}</a:t></a:r></a:p>'
            '</p:txBody></p:sp><p:graphicFrame><p:xfrm><a:off x="100" y="200"/>'
            '<a:ext cx="3000000" cy="400000"/></p:xfrm><a:graphic>'
            f'<a:graphicData uri="{A}/table">{table_xml(label, fill)}</a:graphicData>'
            '</a:graphic></p:graphicFrame></p:spTree></p:cSld></p:sld>').encode()


def make_deck(path, fill="FFFFFF", reversed_order=False):
    order = (2, 1) if reversed_order else (1, 2)
    slides = "".join(f'<p:sldId id="{255 + n}" r:id="rId{n}"/>' for n in order)
    presentation = (f'<p:presentation xmlns:p="{P}" xmlns:r="{R}">'
                    f'<p:sldIdLst>{slides}</p:sldIdLst></p:presentation>')
    rels = (f'<Relationships xmlns="{PR}">' + "".join(
        f'<Relationship Id="rId{n}" Type="{R}/slide" Target="slides/slide{n}.xml"/>'
        for n in (1, 2)) + '</Relationships>')
    members = {
        "ppt/presentation.xml": presentation.encode(),
        "ppt/_rels/presentation.xml.rels": rels.encode(),
        "ppt/tableStyles.xml": (f'<a:tblStyleLst xmlns:a="{A}" def="{STYLE}">'
                                f'<a:tblStyle styleId="{STYLE}" styleName="Neutral"/>'
                                '</a:tblStyleLst>').encode(),
        "ppt/slides/slide1.xml": slide_xml("A", fill),
        "ppt/slides/slide2.xml": slide_xml("B", fill),
        "ppt/notesSlides/notesSlide1.xml": b'<notes>Keep teaching details</notes>',
        "ppt/media/illustration.bin": b'original illustration bytes',
    }
    with ZipFile(path, "x") as out:
        out.comment = b"preserve package comment"
        for name, value in members.items():
            out.writestr(name, value)


def rewrite_deck(source, target, part, edit):
    with ZipFile(source) as before, ZipFile(target, "x") as after:
        for info in before.infolist():
            value = before.read(info.filename)
            after.writestr(copy.copy(info), edit(value) if info.filename == part else value)


class PreserveTableStylesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.pptx"
        self.donor = self.root / "styled.pptx"
        self.output = self.root / "output.pptx"
        make_deck(self.source)
        make_deck(self.donor, fill="F2F6FF")

    def test_only_selected_table_changes_and_report_is_honest(self):
        report = self.root / "report.json"
        HELPER.transplant(self.source, self.donor, [1], self.output, report)
        with ZipFile(self.source) as source, ZipFile(self.output) as output:
            self.assertEqual(source.namelist(), output.namelist())
            self.assertEqual(source.comment, output.comment)
            for part in source.namelist():
                before, after = source.read(part), output.read(part)
                if part == "ppt/slides/slide1.xml":
                    self.assertNotEqual(before, after)
                    self.assertEqual(HELPER.TABLE.sub(b"", before), HELPER.TABLE.sub(b"", after))
                    self.assertIn(b'val="F2F6FF"', after)
                else:
                    self.assertEqual(before, after, part)
        self.assertFalse(json.loads(report.read_text())["render_check_performed"])

    def test_display_order_is_resolved_through_relationships(self):
        source, donor = self.root / "reversed-source.pptx", self.root / "reversed-donor.pptx"
        make_deck(source, reversed_order=True)
        make_deck(donor, fill="F2F6FF", reversed_order=True)
        evidence = HELPER.transplant(source, donor, [1], self.output)
        self.assertEqual(evidence["selected"][0]["part"], "ppt/slides/slide2.xml")
        with ZipFile(source) as before, ZipFile(self.output) as after:
            self.assertEqual(before.read("ppt/slides/slide1.xml"), after.read("ppt/slides/slide1.xml"))

    def test_content_and_structure_changes_are_rejected(self):
        edits = {
            "text": lambda b: b.replace(b'<a:t>Ready</a:t>', b'<a:t>Changed</a:t>'),
            "column": lambda b: b.replace(b'w="1000000"', b'w="1000001"'),
            "row": lambda b: b.replace(b'h="400000"', b'h="400001"'),
            "merge": lambda b: b.replace(b'<a:tc>', b'<a:tc gridSpan="2">', 1),
            "table_count": lambda b: HELPER.TABLE.sub(b"", b),
        }
        for name, edit in edits.items():
            with self.subTest(name=name):
                donor = self.root / (name + ".pptx")
                rewrite_deck(self.donor, donor, "ppt/slides/slide1.xml", edit)
                with self.assertRaises(ValueError):
                    HELPER.transplant(self.source, donor, [1], self.output)
                self.assertFalse(self.output.exists())

    def test_external_relationships_are_rejected(self):
        donor = self.root / "hyperlink.pptx"
        rewrite_deck(self.donor, donor, "ppt/slides/slide1.xml", lambda b: b.replace(
            b'<a:r><a:t>A</a:t>', b'<a:r><a:rPr><a:hlinkClick r:id="externalLink"/></a:rPr><a:t>A</a:t>'))
        with self.assertRaisesRegex(ValueError, "relationship"):
            HELPER.transplant(self.source, donor, [1], self.output)
        self.assertFalse(self.output.exists())

    def test_changed_style_definition_is_rejected(self):
        donor = self.root / "different-style.pptx"
        rewrite_deck(self.donor, donor, "ppt/tableStyles.xml", lambda b: b.replace(
            b'styleName="Neutral"', b'styleName="Different"'))
        with self.assertRaisesRegex(ValueError, "definitions differ"):
            HELPER.transplant(self.source, donor, [1], self.output)

    def test_missing_style_definition_is_rejected(self):
        donor = self.root / "missing-style.pptx"
        rewrite_deck(self.donor, donor, "ppt/slides/slide1.xml", lambda b: b.replace(
            STYLE.encode(), b'{00000000-0000-0000-0000-000000000000}'))
        with self.assertRaisesRegex(ValueError, "definition missing"):
            HELPER.transplant(self.source, donor, [1], self.output)

    def test_all_selected_slides_preflight_before_writing(self):
        donor = self.root / "second-invalid.pptx"
        rewrite_deck(self.donor, donor, "ppt/slides/slide2.xml", lambda b: b.replace(
            b'<a:t>Ready</a:t>', b'<a:t>Changed</a:t>'))
        with self.assertRaises(ValueError):
            HELPER.transplant(self.source, donor, [1, 2], self.output)
        self.assertFalse(self.output.exists())

    def test_existing_output_and_report_are_preserved(self):
        self.output.write_bytes(b'keep output')
        with self.assertRaisesRegex(ValueError, "overwrite"):
            HELPER.transplant(self.source, self.donor, [1], self.output)
        self.assertEqual(self.output.read_bytes(), b'keep output')
        report = self.root / "report.json"
        report.write_bytes(b'keep report')
        with self.assertRaisesRegex(ValueError, "overwrite"):
            HELPER.transplant(self.source, self.donor, [1], self.root / "new.pptx", report)
        self.assertEqual(report.read_bytes(), b'keep report')
        self.assertFalse((self.root / "new.pptx").exists())

    def test_invalid_slide_number_is_rejected(self):
        for slides in ([], [0], [3]):
            with self.subTest(slides=slides), self.assertRaises(ValueError):
                HELPER.transplant(self.source, self.donor, slides, self.output)
        self.assertFalse(self.output.exists())

    def test_corrupt_input_cli_exits_cleanly(self):
        invalid = self.root / "invalid.pptx"
        invalid.write_bytes(b'not a zip')
        result = subprocess.run([sys.executable, str(SCRIPT), "--source", str(invalid),
                                 "--styled", str(self.donor), "--slides", "1", "--output",
                                 str(self.output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Refused:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(self.output.exists())

    def test_dynamic_field_with_same_cached_text_is_rejected(self):
        donor = self.root / "field.pptx"
        rewrite_deck(self.donor, donor, "ppt/slides/slide1.xml", lambda b: b.replace(
            b'<a:r><a:t>A</a:t></a:r>', b'<a:fld id="x" type="datetime"><a:t>A</a:t></a:fld>'))
        with self.assertRaisesRegex(ValueError, "Dynamic"):
            HELPER.transplant(self.source, donor, [1], self.output)
        self.assertFalse(self.output.exists())

    def test_inherited_namespace_cannot_silently_change_meaning(self):
        # The same prefix resolves differently in the two slide roots. Copying
        # only a:tbl is syntactically valid but would reinterpret donor markup.
        source = self.root / "ns-source.pptx"
        donor = self.root / "ns-donor.pptx"
        rewrite_deck(self.source, source, "ppt/slides/slide1.xml", lambda b: b.replace(
            b'<p:sld ', b'<p:sld xmlns:x="urn:old" '))
        rewrite_deck(self.donor, donor, "ppt/slides/slide1.xml", lambda b: b.replace(
            b'<p:sld ', b'<p:sld xmlns:x="urn:new" ').replace(b'<a:tblPr>', b'<a:tblPr x:mode="1">'))
        with self.assertRaisesRegex(ValueError, "Namespace"):
            HELPER.transplant(source, donor, [1], self.output)
        self.assertFalse(self.output.exists())

    def test_changed_color_map_is_rejected(self):
        donor = self.root / "color-map.pptx"
        rewrite_deck(self.donor, donor, "ppt/slides/slide1.xml", lambda b: b.replace(
            b'</p:sld>', b'<p:clrMapOvr><a:overrideClrMapping accent1="accent2"/></p:clrMapOvr></p:sld>'))
        with self.assertRaisesRegex(ValueError, "inheritance"):
            HELPER.transplant(self.source, donor, [1], self.output)

    def test_implicit_default_style_is_checked(self):
        source = self.root / "implicit-source.pptx"
        donor = self.root / "implicit-donor.pptx"
        changed = self.root / "changed-default.pptx"
        remove = lambda b: b.replace(f'<a:tableStyleId>{STYLE}</a:tableStyleId>'.encode(), b'')
        rewrite_deck(self.source, source, "ppt/slides/slide1.xml", remove)
        rewrite_deck(self.donor, donor, "ppt/slides/slide1.xml", remove)
        rewrite_deck(donor, changed, "ppt/tableStyles.xml", lambda b: b.replace(
            ('def="' + STYLE + '"').encode(), b'def="other"'))
        with self.assertRaisesRegex(ValueError, "Default table style"):
            HELPER.transplant(source, changed, [1], self.output)

    def test_style_definition_relationships_are_rejected(self):
        donor = self.root / "style-link.pptx"
        rewrite_deck(self.donor, donor, "ppt/tableStyles.xml", lambda b: b.replace(
            b'<a:tblStyleLst ', f'<a:tblStyleLst xmlns:r="{R}" '.encode()).replace(
            b'styleName="Neutral"', b'styleName="Neutral" r:embed="image"'))
        with self.assertRaisesRegex(ValueError, "relationship"):
            HELPER.transplant(self.source, donor, [1], self.output)

    def test_invalid_merge_boolean_is_rejected(self):
        donor = self.root / "invalid-merge.pptx"
        rewrite_deck(self.donor, donor, "ppt/slides/slide1.xml", lambda b: b.replace(
            b'<a:tc>', b'<a:tc hMerge="invalid">', 1))
        with self.assertRaisesRegex(ValueError, "merge boolean"):
            HELPER.transplant(self.source, donor, [1], self.output)

    def test_report_write_failure_cleans_partial_outputs(self):
        report = self.root / "failed-report.json"
        with patch.object(HELPER.json, 'dump', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                HELPER.transplant(self.source, self.donor, [1], self.output, report)
        self.assertFalse(report.exists())
        self.assertFalse(self.output.exists())
        self.assertTrue(self.source.exists())
        self.assertTrue(self.donor.exists())

    def test_theme_chain_is_compared_by_content_not_part_names(self):
        def with_theme(base, target, suffix, color):
            with ZipFile(base) as src, ZipFile(target, 'x') as out:
                for info in src.infolist():
                    out.writestr(copy.copy(info), src.read(info.filename))
                owner = 'ppt/slides/slide1.xml'
                for name, next_part, kind in [
                    (owner, 'ppt/slideLayouts/layout'+suffix+'.xml', 'slideLayout'),
                    ('ppt/slideLayouts/layout'+suffix+'.xml', 'ppt/slideMasters/master'+suffix+'.xml', 'slideMaster'),
                    ('ppt/slideMasters/master'+suffix+'.xml', 'ppt/theme/theme'+suffix+'.xml', 'theme'),
                ]:
                    relpath = HELPER.posixpath.join(HELPER.posixpath.dirname(name), '_rels', HELPER.posixpath.basename(name)+'.rels')
                    out.writestr(relpath, f'<Relationships xmlns="{PR}"><Relationship Id="r1" Type="{R}/{kind}" Target="/{next_part}"/></Relationships>')
                    if kind != 'theme':
                        out.writestr(next_part, f'<p:holder xmlns:p="{P}"/>')
                    else:
                        out.writestr(next_part, f'<a:theme xmlns:a="{A}"><a:themeElements><a:clrScheme><a:accent1><a:srgbClr val="{color}"/></a:accent1></a:clrScheme></a:themeElements></a:theme>')
        source, donor, bad = [self.root / n for n in ('theme-source.pptx', 'theme-donor.pptx', 'theme-bad.pptx')]
        with_theme(self.source, source, '1', '123456')
        with_theme(self.donor, donor, '2', '123456')
        with_theme(self.donor, bad, '3', 'ABCDEF')
        with self.assertRaisesRegex(ValueError, 'inheritance'):
            HELPER.transplant(source, bad, [1], self.output)
        HELPER.transplant(source, donor, [1], self.output)


if __name__ == "__main__":
    unittest.main()
