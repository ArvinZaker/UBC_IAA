#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import quote
import html
import re

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


OUTPUT_DIR = Path("htmls")


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


def image_src(image_path):
    return quote(f"../{image_path.as_posix()}", safe="/")


def row_metadata(row, headers):
    return {label: value(row, headers, *names) for label, names in METADATA_FIELDS}


def merge_metadata(page, metadata):
    for label, text in metadata.items():
        if text and text not in page["metadata"][label]:
            page["metadata"][label].append(text)


def metadata_line(metadata, labels):
    return " | ".join(f"{label}: {'; '.join(metadata[label])}" for label in labels)


def collect_decks():
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


def page_html(course, sheet, image_path, page):
    rows = []
    for question, answer in page["qa"]:
        rows.append(
            f"""
            <article class="qa">
              <div class="question">{html.escape(question)}</div>
              <button class="answer-toggle" type="button" aria-expanded="true">click to hide</button>
              <div class="answer">{html.escape(answer)}</div>
            </article>
            """
        )

    attribution = "; ".join(page["metadata"]["Attribution"])
    footer = metadata_line(
        page["metadata"],
        ["Image author", "Attribution author", "Reviewer", "Final approval", "Comment"],
    )

    return f"""
    <section class="slide">
      <div class="brand">
        <strong>UBC-IAA</strong>
        <span>{html.escape(course)} - {html.escape(lab_name(sheet))}</span>
      </div>
      <div class="qa-list">
        {''.join(rows)}
      </div>
      <figure>
        <img src="{image_src(image_path)}" alt="{html.escape(image_path.stem)}">
      </figure>
      <aside class="attribution">
        <strong>Attribution</strong>
        <p>{html.escape(attribution)}</p>
      </aside>
      <footer class="credits">{html.escape(footer)}</footer>
    </section>
    """


def write_deck(course, sheet, pages):
    file_name = f"{safe_name(course)}_{safe_name(lab_name(sheet))}.html"
    path = OUTPUT_DIR / file_name
    title = f"{course} - {lab_name(sheet)}"
    slides = "\n".join(page_html(course, sheet, image_path, page) for image_path, page in pages.items())

    path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Arial, sans-serif;
      background: #f4f4f1;
      color: #171717;
    }}
    body {{
      margin: 0;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 1;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 18px;
      background: #ffffff;
      border-bottom: 1px solid #d8d8d2;
    }}
    h1 {{
      flex: 1;
      margin: 0;
      font-size: 18px;
      font-weight: 700;
    }}
    a, header button {{
      border: 1px solid #bbbbB2;
      border-radius: 6px;
      padding: 8px 10px;
      background: #ffffff;
      color: #171717;
      font: inherit;
      text-decoration: none;
      cursor: pointer;
    }}
    main {{
      display: grid;
      gap: 18px;
      padding: 18px;
    }}
    .slide {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      grid-template-areas:
        "brand brand"
        "qa image"
        "attribution attribution"
        "credits credits";
      gap: 28px;
      min-height: calc(100vh - 94px);
      padding: 24px;
      background: #ffffff;
      border: 1px solid #d8d8d2;
      border-radius: 8px;
    }}
    .brand {{
      grid-area: brand;
      display: flex;
      justify-content: space-between;
      gap: 18px;
      padding-bottom: 12px;
      border-bottom: 1px solid #d8d8d2;
    }}
    .brand strong {{
      font-size: 20px;
    }}
    .qa-list {{
      grid-area: qa;
      display: flex;
      flex-direction: column;
      gap: 12px;
      align-self: start;
    }}
    .qa {{
      display: block;
      width: 100%;
      padding: 14px;
      text-align: left;
      background: #fafaf7;
      border: 1px solid #d2d2ca;
      border-radius: 8px;
      cursor: pointer;
    }}
    .question {{
      display: block;
      font-size: 18px;
      font-weight: 700;
      line-height: 1.35;
    }}
    .answer-toggle {{
      margin-top: 10px;
      padding: 0;
      border: 0;
      background: transparent;
      color: #77776f;
      font: inherit;
      font-size: 14px;
      font-style: italic;
      cursor: pointer;
    }}
    .answer {{
      display: block;
      margin-top: 9px;
      font-size: 17px;
      font-weight: 400;
      line-height: 1.4;
    }}
    .qa.hidden .answer {{
      display: none;
    }}
    figure {{
      grid-area: image;
      display: grid;
      place-items: center;
      margin: 0;
      min-width: 0;
    }}
    img {{
      max-width: 100%;
      max-height: calc(100vh - 150px);
      object-fit: contain;
    }}
    .attribution {{
      grid-area: attribution;
      padding: 12px;
      background: #f2f2ed;
      border: 1px solid #d8d8d2;
      border-radius: 8px;
    }}
    .attribution p {{
      min-height: 1.2em;
      margin: 6px 0 0;
    }}
    .credits {{
      grid-area: credits;
      color: #55554f;
      font-size: 13px;
      line-height: 1.4;
    }}
    @media (max-width: 800px) {{
      .slide {{
        grid-template-columns: 1fr;
        grid-template-areas:
          "brand"
          "qa"
          "image"
          "attribution"
          "credits";
      }}
      header {{
        flex-wrap: wrap;
      }}
      h1 {{
        flex-basis: 100%;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <a href="index.html">All decks</a>
    <h1>{html.escape(title)}</h1>
    <button type="button" id="hide-all">Hide all panels</button>
    <button type="button" id="show-all">Show all panels</button>
  </header>
  <main>
    {slides}
  </main>
  <script>
    function setPanel(card, hidden) {{
      const button = card.querySelector(".answer-toggle");
      card.classList.toggle("hidden", hidden);
      button.textContent = hidden ? "click to reveal" : "click to hide";
      button.setAttribute("aria-expanded", hidden ? "false" : "true");
    }}

    document.getElementById("hide-all").addEventListener("click", () => {{
      document.querySelectorAll(".qa").forEach((card) => setPanel(card, true));
    }});

    document.getElementById("show-all").addEventListener("click", () => {{
      document.querySelectorAll(".qa").forEach((card) => setPanel(card, false));
    }});

    document.querySelectorAll(".answer-toggle").forEach((button) => {{
      button.addEventListener("click", (event) => {{
        event.stopPropagation();
        const card = button.closest(".qa");
        setPanel(card, !card.classList.contains("hidden"));
      }});
    }});

    document.querySelectorAll(".qa").forEach((card) => {{
      card.addEventListener("click", () => {{
        setPanel(card, !card.classList.contains("hidden"));
      }});
    }});
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )
    return path


def write_index(deck_links, skipped):
    links = "\n".join(
        f"""
        <a class="deck" href="{html.escape(path.name)}">
          <strong>{html.escape(title)}</strong>
          <span>{page_count} image page(s), {qa_count} Q/A row(s)</span>
        </a>
        """
        for title, path, page_count, qa_count in deck_links
    )

    (OUTPUT_DIR / "index.html").write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>UBC IAA Study Decks</title>
  <style>
    body {{
      margin: 0;
      padding: 28px;
      background: #f4f4f1;
      color: #171717;
      font-family: Arial, sans-serif;
    }}
    header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 22px;
    }}
    h1 {{
      flex: 1;
      margin: 0;
      font-size: 28px;
    }}
    main {{
      display: grid;
      gap: 12px;
      max-width: 820px;
    }}
    .deck {{
      display: flex;
      justify-content: space-between;
      gap: 18px;
      padding: 16px;
      color: inherit;
      text-decoration: none;
      background: #ffffff;
      border: 1px solid #d8d8d2;
      border-radius: 8px;
    }}
    .deck span {{
      color: #55554f;
      text-align: right;
    }}
    footer {{
      margin-top: 18px;
      color: #55554f;
      font-size: 14px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>UBC IAA Study Decks</h1>
  </header>
  <main>
    {links}
  </main>
  <footer>{skipped} skipped row(s)</footer>
</body>
</html>
""",
        encoding="utf-8",
    )


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    decks, skipped = collect_decks()
    deck_links = []

    for (course, sheet), pages in sorted(decks.items()):
        path = write_deck(course, sheet, pages)
        title = f"{course} - {lab_name(sheet)}"
        qa_count = sum(len(page["qa"]) for page in pages.values())
        deck_links.append((title, path, len(pages), qa_count))

    write_index(deck_links, skipped)

    print(f"Wrote {len(deck_links)} HTML deck(s) to {OUTPUT_DIR}")
    print(f"Pages: {sum(page_count for _title, _path, page_count, _qa_count in deck_links)}")
    print(f"Q/A rows: {sum(qa_count for _title, _path, _page_count, qa_count in deck_links)}")
    print(f"Skipped rows: {skipped}")
    print(OUTPUT_DIR / "index.html")


if __name__ == "__main__":
    main()
