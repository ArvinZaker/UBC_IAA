#!/usr/bin/env python3
from pathlib import Path
import html
import re

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable, KeepInFrame, Paragraph, Spacer

from build_anki_deck import (
    IMAGE_DIR,
    INPUT_DIR,
    course_name,
    image_key,
    index_images,
    lab_name,
    row_is_empty,
    value,
    workbook_rows,
)


OUTPUT_DIR = Path("pdfs")
PAGE_SIZE = landscape(letter)
MARGIN = 36
GUTTER = 28
HEADER_HEIGHT = 42
ATTRIBUTION_HEIGHT = 48
FOOTER_HEIGHT = 42


METADATA_FIELDS = [
    ("Attribution", ("attribution",)),
    ("Image author", ("image_author", "author")),
    ("Attribution author", ("attribution_author",)),
    ("Reviewer", ("reviewer",)),
    ("Final approval", ("final approval",)),
    ("Comment", ("comment",)),
]


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")


def fit_box(width, height, max_width, max_height):
    scale = min(max_width / width, max_height / height)
    return width * scale, height * scale


def row_metadata(row, headers):
    return {label: value(row, headers, *names) for label, names in METADATA_FIELDS}


def merge_metadata(page, metadata):
    for label, text in metadata.items():
        if text and text not in page["metadata"][label]:
            page["metadata"][label].append(text)


def metadata_text(metadata, labels):
    parts = []
    for label in labels:
        text = "; ".join(metadata[label])
        parts.append(f"{label}: {text}")
    return " | ".join(parts)


class Separator(Flowable):
    def __init__(self, width):
        super().__init__()
        self.width = width
        self.height = 12

    def draw(self):
        self.canv.setStrokeColorRGB(0.78, 0.78, 0.74)
        self.canv.setLineWidth(0.7)
        self.canv.line(0, 6, self.width, 6)


def draw_text(pdf, qa_pairs, x, y, width, height):
    question_style = ParagraphStyle("Question", fontName="Helvetica-Bold", fontSize=18, leading=22)
    answer_style = ParagraphStyle("Answer", fontName="Helvetica", fontSize=15, leading=19)
    story = []

    for index, (question, answer) in enumerate(qa_pairs):
        if index:
            story.append(Separator(width))
        story.append(Paragraph(html.escape(question), question_style))
        story.append(Paragraph(html.escape(answer), answer_style))
        story.append(Spacer(1, 14))

    text_box = KeepInFrame(width, height, story, mode="shrink")
    text_height = text_box.wrapOn(pdf, width, height)[1]
    text_box.drawOn(pdf, x, y + height - text_height)


def draw_image(pdf, image_path, x, y, width, height):
    image = ImageReader(str(image_path))
    image_width, image_height = image.getSize()
    draw_width, draw_height = fit_box(image_width, image_height, width, height)
    draw_x = x + (width - draw_width) / 2
    draw_y = y + (height - draw_height) / 2
    pdf.drawImage(image, draw_x, draw_y, draw_width, draw_height)


def draw_header(pdf, course, sheet, page_width, page_height):
    pdf.setFillColorRGB(0, 0, 0)
    pdf.rect(0, page_height - HEADER_HEIGHT, page_width, HEADER_HEIGHT, stroke=0, fill=1)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(MARGIN, page_height - 27, "UBC-IAA")
    pdf.setFont("Helvetica", 11)
    pdf.drawRightString(page_width - MARGIN, page_height - 25, f"{course} - {lab_name(sheet)}")
    pdf.setFillColorRGB(0, 0, 0)


def draw_metadata_panel(pdf, page, x, y, width):
    pdf.setFillColorRGB(0.96, 0.96, 0.93)
    pdf.rect(x, y, width, ATTRIBUTION_HEIGHT, stroke=1, fill=1)
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(x + 8, y + ATTRIBUTION_HEIGHT - 15, "Attribution")
    text = "; ".join(page["metadata"]["Attribution"])
    paragraph = Paragraph(html.escape(text), ParagraphStyle("Meta", fontName="Helvetica", fontSize=8, leading=10))
    paragraph.wrapOn(pdf, width - 16, ATTRIBUTION_HEIGHT - 20)
    paragraph.drawOn(pdf, x + 8, y + 7)


def draw_footer(pdf, page, x, y, width):
    text = metadata_text(
        page["metadata"],
        ["Image author", "Attribution author", "Reviewer", "Final approval", "Comment"],
    )
    paragraph = Paragraph(html.escape(text), ParagraphStyle("Footer", fontName="Helvetica", fontSize=7, leading=9))
    paragraph.wrapOn(pdf, width, FOOTER_HEIGHT)
    paragraph.drawOn(pdf, x, y)


def collect_cards():
    images = index_images(IMAGE_DIR)
    decks = {}
    skipped = 0

    for xlsx_path in sorted(INPUT_DIR.glob("MEDD_*_content.xlsx")):
        course = course_name(xlsx_path)
        for sheet, _row_number, headers, row in workbook_rows(xlsx_path):
            if row_is_empty(row):
                continue

            file_name = value(row, headers, "file name", "filename", "image", "image link")
            question = value(row, headers, "question")
            answer = value(row, headers, "answer")
            image_path = images.get(image_key(file_name)) if file_name else None

            if not file_name or not question or not answer or image_path is None:
                skipped += 1
                continue

            pages = decks.setdefault((course, sheet), {})
            page = pages.setdefault(
                image_path,
                {
                    "qa": [],
                    "metadata": {label: [] for label, _names in METADATA_FIELDS},
                },
            )
            page["qa"].append((question, answer))
            merge_metadata(page, row_metadata(row, headers))

    return decks, skipped


def write_pdf(course, sheet, pages):
    path = OUTPUT_DIR / f"{safe_name(course)}_{safe_name(lab_name(sheet))}.pdf"
    pdf = canvas.Canvas(str(path), pagesize=PAGE_SIZE)
    page_width, page_height = PAGE_SIZE
    content_width = page_width - (MARGIN * 2)
    content_y = MARGIN + FOOTER_HEIGHT + ATTRIBUTION_HEIGHT + 14
    content_height = page_height - HEADER_HEIGHT - MARGIN - content_y
    left_width = (content_width - GUTTER) / 2
    right_x = MARGIN + left_width + GUTTER

    for image_path, page in pages.items():
        draw_header(pdf, course, sheet, page_width, page_height)
        draw_text(pdf, page["qa"], MARGIN, content_y, left_width, content_height)
        draw_image(pdf, image_path, right_x, content_y, left_width, content_height)
        draw_metadata_panel(pdf, page, MARGIN, MARGIN + FOOTER_HEIGHT, content_width)
        draw_footer(pdf, page, MARGIN, MARGIN - 6, content_width)
        pdf.showPage()

    pdf.save()
    return path


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    decks, skipped = collect_cards()

    written = []
    for (course, sheet), pages in sorted(decks.items()):
        written.append(write_pdf(course, sheet, pages))

    print(f"Wrote {len(written)} PDF file(s) to {OUTPUT_DIR}")
    print(f"Pages: {sum(len(pages) for pages in decks.values())}")
    print(f"Q/A rows: {sum(len(page['qa']) for pages in decks.values() for page in pages.values())}")
    print(f"Skipped rows: {skipped}")
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
