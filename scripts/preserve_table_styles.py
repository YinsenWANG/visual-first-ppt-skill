#!/usr/bin/env python3
"""Transplant native table styles while preserving every non-table package byte.

Scope: same-order, same-size, same-text native tables without relationship
dependencies. The styled deck must come from a native presentation editor.
This helper does not render slides or validate their visual appearance.
"""

import argparse
import copy
import hashlib
import json
import posixpath
import re
import sys
from urllib.parse import unquote, urlsplit
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import xml.etree.ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}
TABLE = re.compile(rb"<a:tbl(?:\s[^>]*)?>.*?</a:tbl>", re.S)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def xml(zip_file, part):
    return ET.fromstring(zip_file.read(part))


def resolve_target(owner, target):
    uri = urlsplit(target)
    require(not uri.scheme and not uri.netloc and not uri.query and not uri.fragment,
            "Unsupported internal relationship target: " + target)
    path = unquote(uri.path)
    require(path and "\\" not in path, "Invalid internal relationship target")
    part = (posixpath.normpath(path.lstrip("/")) if path.startswith("/") else
            posixpath.normpath(posixpath.join(posixpath.dirname(owner), path)))
    require(part not in (".", "..") and not part.startswith("../"),
            "Relationship escapes package")
    return part


def relationships(zip_file, owner):
    part = posixpath.join(posixpath.dirname(owner), "_rels",
                          posixpath.basename(owner) + ".rels")
    if part not in zip_file.namelist():
        return {}
    result = {}
    for rel in xml(zip_file, part):
        key = rel.attrib["Id"]
        require(key not in result, "Duplicate relationship ID: " + part)
        result[key] = rel
    return result


def slide_parts(zip_file):
    rels = relationships(zip_file, "ppt/presentation.xml")
    parts = []
    for item in xml(zip_file, "ppt/presentation.xml").findall("p:sldIdLst/p:sldId", NS):
        rel = rels[item.attrib["{" + NS["r"] + "}id"]]
        require(rel.get("TargetMode") != "External", "External slide relationship")
        require(rel.get("Type", "").endswith("/slide"), "Invalid slide relationship")
        part = resolve_target("ppt/presentation.xml", rel.attrib["Target"])
        require(part.startswith("ppt/") and part in zip_file.namelist(), "Invalid slide part")
        parts.append(part)
    require(len(parts) == len(set(parts)), "Duplicate slide parts are unsupported")
    return parts


def structural_value(element):
    return (element.tag, tuple(sorted(element.attrib.items())),
            (element.text or "").strip(),
            tuple(structural_value(c) for c in element))


def styles(zip_file):
    part = "ppt/tableStyles.xml"
    if part not in zip_file.namelist():
        return {}
    result = {}
    for style in xml(zip_file, part).findall("a:tblStyle", NS):
        key = style.attrib["styleId"].upper()
        require(key not in result, "Duplicate table style ID")
        check_relationship_dependencies(style)
        result[key] = structural_value(style)
    return result


def style_default(zip_file):
    part = "ppt/tableStyles.xml"
    return xml(zip_file, part).get("def", "").upper() if part in zip_file.namelist() else ""


def theme_context(zip_file, slide):
    """Compare the actual inheritance chain, not filenames or theme IDs."""
    result, seen = [], set()
    current = slide
    for relation in ("slideLayout", "slideMaster", "theme", None):
        require(current not in seen, "Cyclic layout/theme relationship")
        seen.add(current)
        root = xml(zip_file, current)
        if relation is None:
            result.append(structural_value(root))
            break
        result.append(tuple(structural_value(child) for child in root
                            if child.tag in {"{" + NS["p"] + "}" + name
                                             for name in ("clrMap", "clrMapOvr", "txStyles")}))
        links = [r for r in relationships(zip_file, current).values()
                 if r.get("Type", "").endswith("/" + relation)]
        require(len(links) <= 1, "Ambiguous layout/theme relationship")
        if not links:
            break
        require(links[0].get("TargetMode") != "External", "External layout/theme")
        current = resolve_target(current, links[0].attrib["Target"])
    return tuple(result)


def table_signature(table):
    grid = tuple(int(c.attrib["w"]) for c in table.findall("a:tblGrid/a:gridCol", NS))
    rows = []
    for row in table.findall("a:tr", NS):
        cells = []
        for cell in row.findall("a:tc", NS):
            require(all(cell.get(key, "0") in ("0", "1", "false", "true")
                        for key in ("hMerge", "vMerge")), "Invalid merge boolean")
            paragraphs = []
            for paragraph in cell.findall("a:txBody/a:p", NS):
                pieces = []
                for part in paragraph.iter():
                    if part.tag == "{" + NS["a"] + "}t":
                        pieces.append(part.text or "")
                    elif part.tag == "{" + NS["a"] + "}br":
                        pieces.append("\n")
                paragraphs.append("".join(pieces))
            merge = (int(cell.get("gridSpan", "1")), int(cell.get("rowSpan", "1")),
                     cell.get("hMerge", "0") in ("1", "true"),
                     cell.get("vMerge", "0") in ("1", "true"))
            cells.append((tuple(paragraphs), merge))
        rows.append((int(row.attrib["h"]), tuple(cells)))
    return grid, tuple(rows)


def check_relationship_dependencies(table):
    for element in table.iter():
        require(not any(key.startswith("{" + NS["r"] + "}") for key in element.attrib),
                "Table has relationship dependencies; use a relationship-aware editor")
        require(element.tag != "{" + NS["a"] + "}blip", "Picture table is unsupported")
        require(element.tag != "{" + NS["a"] + "}fld",
                "Dynamic table fields are unsupported; cached text is not field semantics")


def check_dependencies(table, source_styles, donor_styles):
    check_relationship_dependencies(table)
    for style in table.findall("a:tblPr/a:tableStyleId", NS):
        key = (style.text or "").strip().upper()
        require(key in source_styles and key in donor_styles,
                "Table style definition missing from a package: " + key)
        require(source_styles[key] == donor_styles[key],
                "Table style definitions differ; transplant would change meaning: " + key)


def transplant(source, styled, selected, output, report=None):
    source, styled, output = map(Path, (source, styled, output))
    require(source.is_file() and styled.is_file(), "Both input PPTX files must exist")
    require(not output.exists(), "Refusing to overwrite output: " + str(output))
    require(output.parent.is_dir(), "Output directory must already exist")
    if report:
        report = Path(report)
        require(not report.exists(), "Refusing to overwrite report")
        require(report.parent.is_dir(), "Report directory must already exist")
        require(report.resolve() not in {source.resolve(), styled.resolve(), output.resolve()},
                "Report path must be distinct from PPTX paths")
    selected = sorted(set(selected))
    require(selected and selected[0] >= 1, "Use positive one-based slide numbers")
    patches = {}
    counts = []
    with ZipFile(source) as original, ZipFile(styled) as donor:
        require(len(original.namelist()) == len(set(original.namelist())),
                "Duplicate ZIP members are unsupported")
        require(len(donor.namelist()) == len(set(donor.namelist())),
                "Duplicate donor ZIP members are unsupported")
        require(original.testzip() is None and donor.testzip() is None, "Corrupt input ZIP")
        before_parts, after_parts = slide_parts(original), slide_parts(donor)
        require(len(before_parts) == len(after_parts), "Slide count changed")
        require(selected[-1] <= len(before_parts), "Selected slide out of range")
        source_styles, donor_styles = styles(original), styles(donor)
        for index in selected:
            part, donor_part = before_parts[index - 1], after_parts[index - 1]
            before, after = original.read(part), donor.read(donor_part)
            old_tables = ET.fromstring(before).findall(".//a:tbl", NS)
            new_tables = ET.fromstring(after).findall(".//a:tbl", NS)
            old_raw, new_raw = TABLE.findall(before), TABLE.findall(after)
            require(len(old_tables) > 0, f"No native table on slide {index}")
            require(len(old_tables) == len(new_tables) == len(old_raw) == len(new_raw),
                    f"Table count or XML prefix mismatch on slide {index}; expected a:tbl")
            require(theme_context(original, part) == theme_context(donor, donor_part),
                    f"Theme or color-map inheritance changed on slide {index}")
            for number, (old, new) in enumerate(zip(old_tables, new_tables), 1):
                require(table_signature(old) == table_signature(new),
                        f"Text, merge, row/column geometry changed: slide {index}, table {number}")
                check_dependencies(old, source_styles, source_styles)
                check_dependencies(new, source_styles, donor_styles)
                if new.find("a:tblPr/a:tableStyleId", NS) is None:
                    key = style_default(donor)
                    require(key == style_default(original), "Default table style changed")
                    if key:
                        require(key in source_styles and key in donor_styles and
                                source_styles[key] == donor_styles[key],
                                "Default table style definition missing or changed")
            replacements = iter(new_raw)
            patched = TABLE.sub(lambda _: next(replacements), before)
            parsed_tables = ET.fromstring(patched).findall(".//a:tbl", NS)
            require([structural_value(t) for t in parsed_tables] ==
                    [structural_value(t) for t in new_tables],
                    "Namespace context changed donor table semantics")
            require(TABLE.sub(b"<TABLE/>", before) == TABLE.sub(b"<TABLE/>", patched),
                    "Non-table content changed")
            patches[part] = patched
            counts.append({"slide": index, "tables": len(old_tables), "part": part})
        # Write only after all selected slides have passed preflight.
        created = False
        try:
            with ZipFile(output, "x") as result:
                created = True
                result.comment = original.comment
                for info in original.infolist():
                    result.writestr(copy.copy(info), patches.get(info.filename, original.read(info.filename)))
            with ZipFile(output) as result:
                require(result.testzip() is None, "Output ZIP failed integrity check")
                require(original.namelist() == result.namelist(), "Package members changed")
                for part in original.namelist():
                    before, after = original.read(part), result.read(part)
                    if part in patches:
                        require(TABLE.sub(b"<TABLE/>", before) == TABLE.sub(b"<TABLE/>", after),
                                "Unexpected non-table slide change")
                        require([table_signature(t) for t in ET.fromstring(before).findall(".//a:tbl", NS)]
                                == [table_signature(t) for t in ET.fromstring(after).findall(".//a:tbl", NS)],
                                "Output table content changed")
                    else:
                        require(before == after, "Unexpected package change: " + part)
        except Exception:
            if created:
                output.unlink(missing_ok=True)
            raise
    evidence = {"source": str(source), "styled": str(styled), "output": str(output),
                "slide_count": len(before_parts), "selected": counts,
                "table_text_and_geometry_preserved": True,
                "other_slide_objects_and_package_parts_byte_identical": True,
                "render_check_performed": False,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
    if report:
        report_created = False
        try:
            with report.open("x", encoding="utf-8") as stream:
                report_created = True
                json.dump(evidence, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        except Exception:
            # Do not leave a success-looking deliverable after a failed run, or
            # remove a report another process created after preflight.
            if report_created:
                report.unlink(missing_ok=True)
            output.unlink(missing_ok=True)
            raise
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--styled", required=True)
    parser.add_argument("--slides", required=True, help="One-based slide numbers, e.g. 5,10,17")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    try:
        selected = [int(value.strip()) for value in args.slides.split(",")]
        result = transplant(args.source, args.styled, selected, args.output, args.report)
    except (ValueError, KeyError, OSError, ET.ParseError, BadZipFile) as error:
        print("Refused: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
