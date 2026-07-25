#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile
import csv
import hashlib
import html
import re
import tempfile
import xml.etree.ElementTree as ET

import genanki


NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
ATLAS_ROOT = "UBC-IAA"
SOURCE_ROOT = Path(".")
OUTPUT_FILE = Path("UBC-IAA.apkg")
ERROR_FILE = Path("error.csv")
IMAGE_MAX_EDGE = 1800
IMAGE_JPEG_QUALITY = 82
EXTRA_FIELDS = [
    ("Attribution", ("attribution",)),
    ("Authors", ("authors", "author")),
    ("Attribution author", ("attribution_author",)),
    ("Reviewer", ("reviewer",)),
    ("Final approval", ("final approval",)),
    ("Comment", ("comment",)),
]


def xlsx_strings(zip_file):
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return []

    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    strings = []
    for item in root.findall("x:si", NS):
        strings.append("".join(t.text or "" for t in item.iter(f"{{{NS['x']}}}t")))
    return strings


def xlsx_sheets(zip_file):
    workbook = ET.fromstring(zip_file.read("xl/workbook.xml"))
    rels = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))
    relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}

    for sheet in workbook.find("x:sheets", NS):
        target = relmap[sheet.attrib[RID]].lstrip("/")
        yield sheet.attrib["name"], f"xl/{target}"


def col_number(ref):
    number = 0
    for char in re.match(r"[A-Z]+", ref).group(0):
        number = number * 26 + ord(char) - 64
    return number - 1


def cell_text(cell, strings):
    if cell.attrib.get("t") == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(f"{{{NS['x']}}}t")).strip()

    value = cell.find("x:v", NS)
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        return strings[int(value.text)].strip()
    return value.text.strip()


def read_sheet(zip_file, sheet_path, strings):
    root = ET.fromstring(zip_file.read(sheet_path))
    rows = []
    for row in root.findall(".//x:sheetData/x:row", NS):
        values = []
        for cell in row.findall("x:c", NS):
            index = col_number(cell.attrib["r"])
            while len(values) <= index:
                values.append("")
            values[index] = cell_text(cell, strings)
        rows.append(values)
    return rows


def workbook_rows(xlsx_path):
    with ZipFile(xlsx_path) as zip_file:
        strings = xlsx_strings(zip_file)
        for sheet_name, sheet_path in xlsx_sheets(zip_file):
            if sheet_name.lower() == "sample":
                continue

            rows = read_sheet(zip_file, sheet_path, strings)
            if not rows:
                continue

            headers = {name.strip().lower(): i for i, name in enumerate(rows[0])}
            for row_number, values in enumerate(rows[1:], start=2):
                yield sheet_name, row_number, headers, values


def value(row, headers, *names):
    for name in names:
        index = headers.get(name)
        if index is not None and index < len(row):
            return row[index].strip()
    return ""


def display_name(identifier):
    words = identifier.replace("_", " ").strip().split()
    return " ".join(word if word.isupper() else word.capitalize() for word in words)


def course_name(xlsx_path):
    identifier = re.sub(r"_content$", "", xlsx_path.stem, flags=re.I)
    match = re.fullmatch(r"MEDD[_ ]?(\d+)", identifier, re.I)
    return f"MEDD {match.group(1)}" if match else display_name(identifier)


def modality_name(xlsx_path):
    identifier = re.sub(r"\s+drive$", "", xlsx_path.parent.name, flags=re.I)
    return display_name(identifier)


def image_dir_for_workbook(xlsx_path):
    identifier = re.sub(r"_content$", "", xlsx_path.stem, flags=re.I)
    return xlsx_path.parent / f"{identifier}_images"


def content_workbooks(source_root=SOURCE_ROOT):
    workbooks = []
    for drive_dir in source_root.iterdir():
        if not drive_dir.is_dir() or not drive_dir.name.lower().endswith(" drive"):
            continue
        workbooks.extend(
            path
            for path in drive_dir.glob("*_content.xlsx")
            if not path.name.startswith("~$")
        )
    return sorted(workbooks)


def lab_name(sheet_name):
    name = sheet_name.replace("_", " ").strip()
    name = re.sub(r"\bLab\s*(\d+)", r"Lab \1", name, flags=re.I)
    return name.title()


def clean_tag(text):
    return re.sub(r"[^A-Za-z0-9_:-]+", "_", text.strip()).strip("_")


def split_people(text):
    return [name.strip() for name in text.split(";") if name.strip()]


def row_tags(tag_text, modality, course, sheet):
    tags = []
    for raw_tag in re.split(r"[;,]", tag_text):
        tag = clean_tag(raw_tag.lower())
        if tag:
            tags.append(tag)

    tags += [
        clean_tag(modality.replace(" ", "_")),
        clean_tag(course.replace(" ", "_")),
        clean_tag(sheet),
    ]
    return sorted(set(tags))


def review_tags(row, headers):
    reviewer_tag = "reviewed" if value(row, headers, "reviewer") else "unreviewed"
    approval_tag = "approved" if value(row, headers, "final approval") else "unapproved"
    return [reviewer_tag, approval_tag]


def card_group(tag_text):
    tags = [tag.strip().lower() for tag in re.split(r"[;,]", tag_text)]
    return "Primary" if "primary" in tags else "Secondary"


def image_key(file_name):
    stem = Path(file_name).stem.strip()
    if stem.endswith("_P"):
        stem = stem[:-2]
    return stem


def index_images(image_root):
    images = {}
    for path in image_root.rglob("*"):
        if path.suffix.lower() in IMAGE_EXTS and path.stem.endswith("_P"):
            images.setdefault(path.stem[:-2], path)
    return images


def index_lowercase_primary_images(image_root):
    images = {}
    for path in image_root.rglob("*"):
        if path.suffix.lower() in IMAGE_EXTS and path.stem.endswith("_p"):
            images.setdefault(path.stem[:-2], path)
    return images


def variant_image_key(path):
    match = re.match(r"(.+)_[^_]+$", path.stem)
    return match.group(1) if match else ""


def index_variant_images(image_root):
    images = {}
    for path in sorted(image_root.rglob("*")):
        if path.suffix.lower() in IMAGE_EXTS and not path.stem.endswith(("_P", "_p")):
            key = variant_image_key(path)
            if key:
                images.setdefault(key, path)
    return images


def optimize_image_for_anki(source_path, output_dir):
    """Write a smaller JPEG copy for Anki and return that new media path.

    Parameters to tune:
    - IMAGE_MAX_EDGE: caps the longest image side in pixels. Smaller values make
      the deck smaller, but labels and fine anatomy details can become harder to
      read. 1600-2000 px is a reasonable range for Anki review.
    - IMAGE_JPEG_QUALITY: controls JPEG compression quality from 1-95. Lower
      values shrink the deck more, but can create visible artifacts. 80-85 is a
      reasonable range for anatomy photos.

    This does not edit the source image. Opening and re-saving with Pillow also
    strips metadata because EXIF/ICC data are not copied into the output file.
    PNGs, JPEGs, and other readable image formats are all converted to JPEG for
    smaller Anki media. Transparent images are flattened onto white.
    """
    from PIL import Image, ImageOps

    output_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(str(source_path).encode("utf-8")).hexdigest()[:10]
    output_path = output_dir / f"{source_path.stem}_{digest}.jpg"

    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail((IMAGE_MAX_EDGE, IMAGE_MAX_EDGE), Image.Resampling.LANCZOS)

        if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
            transparent = image.convert("RGBA")
            background = Image.new("RGB", transparent.size, "white")
            background.paste(transparent, mask=transparent.getchannel("A"))
            image = background
        else:
            image = image.convert("RGB")

        image.save(
            output_path,
            "JPEG",
            quality=IMAGE_JPEG_QUALITY,
            optimize=True,
            progressive=True,
        )

    return output_path


def deck_id(deck_name):
    digest = hashlib.sha1(deck_name.encode("utf-8")).hexdigest()
    return 1_000_000_000 + int(digest[:8], 16)


def note_guid(modality, course, sheet, file_name, question, answer):
    fields = (course, sheet, file_name, question, answer)
    if modality.lower() == "anatomy":
        return genanki.guid_for(*fields)
    return genanki.guid_for(modality, *fields)


def row_is_empty(row):
    return not any(cell.strip() for cell in row)


def row_extras(row, headers):
    items = []
    for label, names in EXTRA_FIELDS:
        text = value(row, headers, *names)
        if text or label == "Attribution":
            items.append(f"<b>{html.escape(label)}:</b> {html.escape(text)}")

    return "<b>Extras</b><br>" + "<br>".join(items)


def error_row(xlsx_path, sheet, row_number, file_name, question, answer, tag_text, reason):
    return {
        "workbook": xlsx_path.as_posix(),
        "sheet": sheet,
        "row": row_number,
        "file_name": file_name,
        "question": question,
        "answer": answer,
        "tax": tag_text,
        "reason": reason,
    }


def make_model():
    return genanki.Model(
        1607392319,
        "MEDD Anatomy Cloze",
        model_type=genanki.Model.CLOZE,
        fields=[
            {"name": "Question"},
            {"name": "Answer"},
            {"name": "Image"},
            {"name": "Attribution"},
            {"name": "Extras"},
        ],
        templates=[
            {
                "name": "Cloze",
                "qfmt": """
<div class="question">{{Question}}</div>
<div class="answer">{{cloze:Answer}}</div>
<div class="image">{{Image}}</div>
""",
                "afmt": """
<div class="question">{{Question}}</div>
<div class="answer">{{cloze:Answer}}</div>
<div class="image">{{Image}}</div>
<hr>
{{Extras}}
""",
            }
        ],
        css="""
.card { font-family: Arial, sans-serif; font-size: 20px; text-align: left; }
.question { font-weight: 700; margin-bottom: 0.8rem; }
.answer { margin-bottom: 0.8rem; }
.image img { display: block; max-width: 100%; max-height: 70vh; margin-top: 0.8rem; }
""",
    )


def build_package():
    model = make_model()
    decks = {ATLAS_ROOT: genanki.Deck(deck_id(ATLAS_ROOT), ATLAS_ROOT)}
    errors = []
    media_files = set()
    optimized_images = {}
    original_media_bytes = 0
    optimized_media_bytes = 0
    added = 0

    with tempfile.TemporaryDirectory() as temp_dir:
        optimized_media_dir = Path(temp_dir) / "anki_media"

        for xlsx_path in content_workbooks():
            modality = modality_name(xlsx_path)
            course = course_name(xlsx_path)
            modality_deck_name = f"{ATLAS_ROOT}::{modality}"
            decks.setdefault(
                modality_deck_name,
                genanki.Deck(deck_id(modality_deck_name), modality_deck_name),
            )
            course_deck_name = f"{modality_deck_name}::{course}"
            decks.setdefault(
                course_deck_name,
                genanki.Deck(deck_id(course_deck_name), course_deck_name),
            )
            course_image_dir = image_dir_for_workbook(xlsx_path)
            images = index_images(course_image_dir)
            lowercase_primary_images = index_lowercase_primary_images(course_image_dir)
            variant_images = index_variant_images(course_image_dir)
            for sheet, row_number, headers, row in workbook_rows(xlsx_path):
                if row_is_empty(row):
                    continue

                file_name = value(row, headers, "file name", "filename", "image", "image link")
                question = value(row, headers, "question")
                answer = value(row, headers, "answer")
                tag_text = value(row, headers, "tax", "tag")

                reasons = []
                if not file_name:
                    reasons.append("no file name specified")
                if not question:
                    reasons.append("no question specified")
                if not answer:
                    reasons.append("no answer specified")
                key = image_key(file_name) if file_name else ""
                image_path = images.get(key) if file_name else None
                fallback_reason = ""
                if file_name and image_path is None:
                    image_path = variant_images.get(key)
                    if image_path is not None:
                        fallback_reason = f"no uppercase _P image found; using fallback image: {image_path.name}"
                if file_name and image_path is None:
                    lowercase_path = lowercase_primary_images.get(key)
                    if lowercase_path is not None:
                        reasons.append(
                            f"image uses lowercase _p; rename to uppercase _P: {lowercase_path.name}"
                        )
                    else:
                        reasons.append("image could not be found")

                if reasons:
                    errors.append(
                        error_row(
                            xlsx_path,
                            sheet,
                            row_number,
                            file_name,
                            question,
                            answer,
                            tag_text,
                            "; ".join(reasons),
                        )
                    )
                    continue

                if fallback_reason:
                    errors.append(
                        error_row(
                            xlsx_path,
                            sheet,
                            row_number,
                            file_name,
                            question,
                            answer,
                            tag_text,
                            fallback_reason,
                        )
                    )

                if image_path not in optimized_images:
                    optimized_path = optimize_image_for_anki(image_path, optimized_media_dir)
                    optimized_images[image_path] = optimized_path
                    original_media_bytes += image_path.stat().st_size
                    optimized_media_bytes += optimized_path.stat().st_size

                media_path = optimized_images[image_path]
                group = card_group(tag_text)
                deck_name = (
                    f"{ATLAS_ROOT}::{modality}::{course}::{lab_name(sheet)}::{group}"
                )
                deck = decks.setdefault(
                    deck_name,
                    genanki.Deck(deck_id(deck_name), deck_name),
                )

                image_html = f'<img src="{html.escape(media_path.name)}">'
                attribution = value(row, headers, "attribution")
                extras = row_extras(row, headers)
                note = genanki.Note(
                    model=model,
                    fields=[
                        html.escape(question),
                        f"{{{{c1::{html.escape(answer)}}}}}",
                        image_html,
                        html.escape(attribution),
                        extras,
                    ],
                    tags=sorted(
                        set(
                            row_tags(tag_text, modality, course, sheet)
                            + review_tags(row, headers)
                        )
                    ),
                    guid=note_guid(
                        modality, course, sheet, file_name, question, answer
                    ),
                )
                deck.add_note(note)
                media_files.add(str(media_path))
                added += 1

        with ERROR_FILE.open("w", newline="") as file:
            fieldnames = ["workbook", "sheet", "row", "file_name", "question", "answer", "tax", "reason"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(errors)

        genanki.Package(list(decks.values()), media_files=sorted(media_files)).write_to_file(OUTPUT_FILE)

    saved_media_bytes = original_media_bytes - optimized_media_bytes
    print(f"Wrote {OUTPUT_FILE}")
    print(f"Wrote {ERROR_FILE}")
    print(f"Cards: {added}")
    print(f"Skipped rows: {len(errors)}")
    print(f"Images linked once in package media: {len(media_files)}")
    print(f"Original media: {original_media_bytes / 1_000_000:.1f} MB")
    print(f"Optimized media: {optimized_media_bytes / 1_000_000:.1f} MB")
    print(f"Media saved: {saved_media_bytes / 1_000_000:.1f} MB")


def main():
    build_package()


if __name__ == "__main__":
    main()
