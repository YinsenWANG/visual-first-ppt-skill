#!/usr/bin/env python3
"""Check a PPTX package and explicit preservation requirements, without rendering.

inventory: record a known input before editing. check: validate the final file.
Standard library only. Does not execute macros, fetch links, or extract ZIP files.
"""

import argparse
from collections import Counter
import hashlib
import json
import posixpath
import sys
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import xml.etree.ElementTree as ET

from preserve_table_styles import NS, relationships, resolve_target, slide_parts


SCHEMA = "visual-first-ppt.inventory.v1"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def paragraphs(root):
    return ["".join("\n" if node.tag == "{" + NS["a"] + "}br" else (node.text or "")
                    for node in paragraph.iter()
                    if node.tag in ("{" + NS["a"] + "}t", "{" + NS["a"] + "}br"))
            for paragraph in root.findall(".//a:p", NS)]


def table_content(table):
    return {"columns": len(table.findall("a:tblGrid/a:gridCol", NS)), "rows": [
        [{"text": "\n".join(paragraphs(cell)),
          "gridSpan": cell.get("gridSpan", "1"), "rowSpan": cell.get("rowSpan", "1"),
          "hMerge": cell.get("hMerge", "0") in ("1", "true"),
          "vMerge": cell.get("vMerge", "0") in ("1", "true")}
         for cell in row.findall("a:tc", NS)] for row in table.findall("a:tr", NS)]}


def inspect(path):
    path = Path(path)
    with ZipFile(path) as package:
        names = package.namelist()
        require(len(names) == len(set(names)), "Duplicate ZIP members")
        require(package.testzip() is None, "Corrupt ZIP member")
        require("[Content_Types].xml" in names and "_rels/.rels" in names,
                "Missing package content types or root relationships")
        roots = {}
        media = {}
        for name in names:
            if name.endswith((".xml", ".rels")):
                roots[name] = ET.fromstring(package.read(name))
            if name.startswith("ppt/media/") and not name.endswith("/"):
                data = package.read(name)
                require(data, "Empty media payload: " + name)
                media[name] = digest(data)

        # Check every relationship and each r:id/r:embed/r:link reference, including
        # notes and charts. Internal targets are URI paths relative to their owner.
        for name, root in roots.items():
            if not name.endswith(".rels"):
                continue
            if name == "_rels/.rels":
                owner = ""
            else:
                parent = posixpath.dirname(name)
                require(posixpath.basename(parent) == "_rels", "Invalid relationship part")
                owner = posixpath.join(posixpath.dirname(parent), posixpath.basename(name)[:-5])
                require(owner in names, "Relationship owner missing: " + owner)
            ids = set()
            for rel in root:
                key = rel.attrib["Id"]
                require(key not in ids, "Duplicate relationship ID: " + name)
                ids.add(key)
                if rel.get("TargetMode") != "External":
                    target = resolve_target(owner, rel.attrib["Target"])
                    require(target in names, "Broken relationship: " + name + " -> " + target)
            if owner in roots:
                for node in roots[owner].iter():
                    for key, value in node.attrib.items():
                        if key.startswith("{" + NS["r"] + "}"):
                            require(value in ids, "Unresolved relationship ID: " + owner + " -> " + value)
        for name, root in roots.items():
            if name.endswith(".xml"):
                refs = relationships(package, name)
                for node in root.iter():
                    for key, value in node.attrib.items():
                        if key.startswith("{" + NS["r"] + "}"):
                            require(value in refs, "Unresolved relationship ID: " + name + " -> " + value)

        documents = [rel for rel in roots["_rels/.rels"]
                     if rel.get("Type", "").endswith("/officeDocument")]
        require(len(documents) == 1 and documents[0].get("TargetMode") != "External" and
                resolve_target("", documents[0].attrib["Target"]) == "ppt/presentation.xml",
                "Unsupported or missing presentation root relationship")
        require(roots["ppt/presentation.xml"].tag == "{" + NS["p"] + "}presentation",
                "Unsupported presentation XML namespace")

        slides = []
        for number, part in enumerate(slide_parts(package), 1):
            root, rels = roots[part], relationships(package, part)
            notes_links = [r for r in rels.values() if r.get("Type", "").endswith("/notesSlide")]
            require(len(notes_links) <= 1, "Multiple notes parts on slide " + str(number))
            notes = []
            if notes_links:
                rel = notes_links[0]
                require(rel.get("TargetMode") != "External", "External notes slide")
                note_root = roots[resolve_target(part, rel.attrib["Target"])]
                for shape in note_root.findall(".//p:sp", NS):
                    placeholder = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
                    if placeholder is not None and placeholder.get("type") in ("sldImg", "sldNum", "hdr", "ftr", "dt"):
                        continue
                    notes.extend(paragraphs(shape))
            images, external_images = [], []
            for blip in root.findall(".//a:blip", NS):
                for key in ("embed", "link"):
                    rid = blip.get("{" + NS["r"] + "}" + key)
                    if not rid:
                        continue
                    rel = rels[rid]
                    if rel.get("TargetMode") == "External":
                        external_images.append(rel.attrib["Target"])
                    else:
                        target = resolve_target(part, rel.attrib["Target"])
                        payload = package.read(target)
                        require(payload, "Empty image payload: " + target)
                        images.append(digest(payload))
            require(not external_images, "Slide %d has linked images; embed for a standalone PPTX" % number)
            slides.append({"slide": number, "part": part,
                           "text": [t for t in paragraphs(root) if t],
                           "notes": "\n".join(notes),
                           "tables": [table_content(t) for t in root.findall(".//a:tbl", NS)],
                           "images": images})
        require(slides, "No slides in presentation order")
        size = roots["ppt/presentation.xml"].find("p:sldSz", NS)
        require(size is not None and int(size.get("cx", "0")) > 0 and int(size.get("cy", "0")) > 0,
                "Missing or invalid slide dimensions")
        return {"schema": SCHEMA, "sha256": digest(path.read_bytes()),
                "slide_count": len(slides), "size_emu": [int(size.get("cx")), int(size.get("cy"))],
                "slides": slides, "media": media}


def validate_inventory(value):
    require(value.get("schema") == SCHEMA, "Unsupported baseline schema")
    require(isinstance(value.get("slides"), list) and value["slide_count"] == len(value["slides"]),
            "Invalid baseline slide count")
    require([s["slide"] for s in value["slides"]] == list(range(1, value["slide_count"] + 1)),
            "Invalid baseline slide order")


def check(actual, expected_slides=None, baseline=None, preserve=None, slide_map=None, requirements=None):
    findings = []
    if expected_slides is not None and actual["slide_count"] != expected_slides:
        findings.append("Slide count differs: expected %s, found %s" % (expected_slides, actual["slide_count"]))
    if baseline is not None:
        validate_inventory(baseline)
        if actual["size_emu"] != baseline["size_emu"]:
            findings.append("Slide dimensions changed from baseline")
        preserve = preserve or ["text", "notes", "tables", "images"]
        require(set(preserve) <= {"text", "notes", "tables", "images"}, "Unknown preservation field")
        if slide_map is None:
            require(actual["slide_count"] == baseline["slide_count"],
                    "Slide count changed; provide an explicit one-to-one slide map")
            slide_map = [[n, n] for n in range(1, baseline["slide_count"] + 1)]
        require(isinstance(slide_map, list) and all(isinstance(pair, list) and len(pair) == 2 and
                all(type(n) is int for n in pair) for pair in slide_map), "Invalid slide map")
        require(sorted(pair[0] for pair in slide_map) == list(range(1, baseline["slide_count"] + 1)),
                "Slide map must cover every source slide exactly once")
        targets = [pair[1] for pair in slide_map]
        require(len(set(targets)) == len(targets) and all(1 <= n <= actual["slide_count"] for n in targets),
                "Slide map targets must be unique and in range")
        for old_n, new_n in slide_map:
            old, new = baseline["slides"][old_n - 1], actual["slides"][new_n - 1]
            for field in preserve:
                a, b = old[field], new[field]
                # Shape order can change without dropping or duplicating text/images.
                if field in ("text", "images"):
                    a, b = Counter(a), Counter(b)
                if a != b:
                    findings.append("Preserved %s changed: source slide %d -> output slide %d" % (field, old_n, new_n))
    else:
        require(slide_map is None and not preserve, "--preserve/--slide-map requires --baseline")
    if requirements is not None:
        require(isinstance(requirements, dict) and set(requirements) <= {"slide_count", "slides"},
                "Unknown requirements keys")
        if "slide_count" in requirements:
            require(type(requirements["slide_count"]) is int and requirements["slide_count"] > 0,
                    "Invalid required slide_count")
            if requirements["slide_count"] != actual["slide_count"]:
                findings.append("Required slide count differs")
        require(isinstance(requirements.get("slides", []), list), "Requirements slides must be a list")
        seen = set()
        for rule in requirements.get("slides", []):
            require(isinstance(rule, dict) and set(rule) <= {"slide", "text_contains", "notes_contains", "tables", "image_sha256"},
                    "Unknown slide requirement keys")
            n = rule["slide"]
            require(type(n) is int and 1 <= n <= actual["slide_count"] and n not in seen,
                    "Invalid or duplicate required slide")
            seen.add(n)
            slide = actual["slides"][n - 1]
            for field, haystack in (("text_contains", "\n".join(slide["text"])), ("notes_contains", slide["notes"])):
                needles = rule.get(field, [])
                require(isinstance(needles, list) and all(isinstance(t, str) and t for t in needles),
                        "Required text must be nonempty strings")
                for index, needle in enumerate(needles):
                    if needle not in haystack:
                        findings.append("Missing %s item %d on slide %d" % (field, index + 1, n))
            if "tables" in rule:
                tables = rule["tables"]
                require(isinstance(tables, list) and all(isinstance(t, list) and
                        all(isinstance(row, list) and all(isinstance(c, str) for c in row) for row in t) for t in tables),
                        "Tables must contain matrices of exact strings")
                values = [[[cell["text"] for cell in row] for row in t["rows"]] for t in slide["tables"]]
                if values != tables:
                    findings.append("Native table content/count differs on slide %d" % n)
            required_images = rule.get("image_sha256", [])
            require(isinstance(required_images, list) and all(isinstance(h, str) and len(h) == 64 and
                    all(c in "0123456789abcdef" for c in h) for h in required_images), "Invalid image SHA-256")
            if Counter(required_images) - Counter(slide["images"]):
                findings.append("Required image bytes missing from slide %d" % n)
    return {"status": "fail" if findings else "pass", "sha256": actual["sha256"],
            "slide_count": actual["slide_count"], "media_count": len(actual["media"]),
            "native_table_count": sum(len(s["tables"]) for s in actual["slides"]),
            "findings": findings, "render_check_performed": False,
            "limitations": "Checks XML relationships, nonempty media and declared content only; does not decode images, render slides, evaluate formulas or verify PowerPoint behavior."}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else None


def write_json(path, value):
    # No overwrite: preserve the baseline and reports tied to previous candidates.
    with Path(path).open("x", encoding="utf-8") as stream:
        try:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        except Exception:
            # Close first for Windows; only remove the file this call created.
            stream.close()
            Path(path).unlink(missing_ok=True)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inventory = sub.add_parser("inventory")
    inventory.add_argument("pptx")
    inventory.add_argument("--output", required=True)
    checker = sub.add_parser("check")
    checker.add_argument("pptx")
    checker.add_argument("--expected-slides", type=int)
    checker.add_argument("--baseline")
    checker.add_argument("--preserve", nargs="+", choices=["text", "notes", "tables", "images"])
    checker.add_argument("--slide-map")
    checker.add_argument("--requirements")
    checker.add_argument("--report")
    args = parser.parse_args()
    try:
        actual = inspect(args.pptx)
        if args.command == "inventory":
            write_json(args.output, actual)
            print(json.dumps({"status": "recorded", "slide_count": actual["slide_count"], "sha256": actual["sha256"]}))
            return 0
        require(args.expected_slides is None or args.expected_slides > 0, "Expected slides must be positive")
        result = check(actual, args.expected_slides, read_json(args.baseline), args.preserve,
                       read_json(args.slide_map), read_json(args.requirements))
        if args.report:
            write_json(args.report, result)
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result["findings"] else 0
    except (ValueError, KeyError, TypeError, AttributeError, OSError, ET.ParseError, BadZipFile) as error:
        print("Validation refused: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
