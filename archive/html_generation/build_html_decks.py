#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import quote
import html
import re

from build_anki_deck import (
    IMAGE_DIR,
    INPUT_DIR,
    IMAGE_EXTS,
    card_group,
    course_name,
    image_key,
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


def image_edition_key(path):
    stem = path.stem
    if stem.endswith("_P"):
        return stem[:-2]
    return re.sub(r"_\d+$", "", stem)


def index_image_editions(image_root):
    images = {}
    for path in image_root.rglob("*"):
        if path.suffix.lower() in IMAGE_EXTS:
            images.setdefault(image_edition_key(path), []).append(path)

    for paths in images.values():
        paths.sort(key=lambda path: (not path.stem.endswith("_P"), path.stem))

    return images


def row_metadata(row, headers):
    return {label: value(row, headers, *names) for label, names in METADATA_FIELDS}


def merge_metadata(page, metadata):
    for label, text in metadata.items():
        if text and text not in page["metadata"][label]:
            page["metadata"][label].append(text)


def metadata_line(metadata, labels):
    return " | ".join(f"{label}: {'; '.join(metadata[label])}" for label in labels)


def collect_decks():
    image_editions = index_image_editions(IMAGE_DIR)
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
            tag_text = value(row, headers, "tax", "tag")
            key = image_key(file_name) if file_name else ""
            image_paths = image_editions.get(key, [])

            if not file_name or not question or not answer or not image_paths:
                skipped += 1
                continue

            pages = decks.setdefault((course, sheet), {})
            page = pages.setdefault(
                key,
                {
                    "images": image_paths,
                    "qa": [],
                    "metadata": {label: [] for label, _names in METADATA_FIELDS},
                },
            )
            page["qa"].append((question, answer, card_group(tag_text).lower()))
            merge_metadata(page, row_metadata(row, headers))

    return decks, skipped


def image_carousel(image_paths):
    images = []
    for index, path in enumerate(image_paths):
        is_active = index == 0
        active_class = "active" if is_active else ""
        aria_hidden = "false" if is_active else "true"
        images.append(
            f"""
        <img
          class="{active_class}"
          src="{image_src(path)}"
          alt="{html.escape(path.stem)}"
          aria-hidden="{aria_hidden}"
        >
        """
        )

    controls = ""
    if len(image_paths) > 1:
        controls = f"""
        <div class="image-controls" aria-label="Image edition controls">
          <button type="button" class="image-prev" aria-label="Previous image edition">&larr;</button>
          <span class="image-count">1 / {len(image_paths)}</span>
          <button type="button" class="image-next" aria-label="Next image edition">&rarr;</button>
        </div>
        """

    return f"""
    <figure class="image-review" data-current="0">
      {controls}
      <div class="image-stage">
        {''.join(images)}
      </div>
      <div class="zoom-lens" aria-hidden="true"></div>
      <div class="zoom-pane" aria-hidden="true"></div>
    </figure>
    """


def page_html(page):
    rows = []
    for question, answer, group in page["qa"]:
        rows.append(
            f"""
            <article class="qa" data-group="{html.escape(group)}">
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
      <div class="qa-list">
        {''.join(rows)}
      </div>
      {image_carousel(page["images"])}
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
    slides = "\n".join(page_html(page) for page in pages.values())

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
      background: #f6f6f3;
      color: #171717;
      --border: #d8d8d2;
      --muted: #62625b;
      --surface: #ffffff;
      --surface-soft: #f7f7f3;
      --accent: #1f6f68;
    }}
    body {{
      margin: 0;
      background: #f6f6f3;
    }}
    .app-header {{
      position: sticky;
      top: 0;
      z-index: 5;
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      align-items: center;
      gap: 16px;
      padding: 10px 18px;
      background: rgba(255, 255, 255, 0.96);
      border-bottom: 1px solid var(--border);
      box-shadow: 0 1px 0 rgba(0, 0, 0, 0.02);
      backdrop-filter: blur(10px);
    }}
    h1 {{
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      line-height: 1.2;
    }}
    .title-block {{
      min-width: 0;
    }}
    .eyebrow {{
      margin: 0 0 2px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.2;
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      justify-content: flex-end;
    }}
    .toolbar-label {{
      color: var(--muted);
      font-size: 13px;
    }}
    .deck-link {{
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      border: 1px solid #bbbbB2;
      border-radius: 6px;
      padding: 0 10px;
      background: var(--surface);
      color: #171717;
      font: inherit;
      font-size: 14px;
      text-decoration: none;
      cursor: pointer;
    }}
    .answer-control {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-height: 32px;
      padding: 0 8px;
      background: var(--surface-soft);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: #171717;
      font-size: 14px;
      cursor: pointer;
      user-select: none;
    }}
    .answer-control input {{
      width: 16px;
      height: 16px;
      margin: 0;
      accent-color: var(--accent);
      cursor: pointer;
    }}
    .answer-control input:disabled,
    .answer-control input:disabled + span {{
      cursor: not-allowed;
      opacity: 0.45;
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
        "qa image"
        "attribution attribution"
        "credits credits";
      gap: 24px 28px;
      min-height: calc(100vh - 94px);
      padding: 24px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
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
    .image-review {{
      grid-area: image;
      position: relative;
      display: grid;
      place-items: center;
      margin: 0;
      min-width: 0;
    }}
    .image-stage {{
      position: relative;
      display: grid;
      place-items: center;
      width: 100%;
      cursor: zoom-in;
    }}
    .image-stage img {{
      display: none;
      max-width: 100%;
      max-height: calc(100vh - 126px);
      object-fit: contain;
    }}
    .image-stage img.active {{
      display: block;
    }}
    .image-controls {{
      position: absolute;
      top: 10px;
      right: 10px;
      z-index: 1;
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px;
      background: rgba(255, 255, 255, 0.94);
      border: 1px solid #d8d8d2;
      border-radius: 6px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    }}
    .image-controls button {{
      width: 32px;
      height: 32px;
      padding: 0;
      border: 1px solid #bbbbB2;
      border-radius: 6px;
      background: #ffffff;
      color: #171717;
      font: inherit;
      font-size: 18px;
      line-height: 1;
      cursor: pointer;
    }}
    .zoom-lens {{
      position: absolute;
      top: 0;
      left: 0;
      z-index: 2;
      display: none;
      width: 120px;
      height: 120px;
      background: rgba(255, 255, 255, 0.28);
      border: 1px solid rgba(31, 111, 104, 0.9);
      border-radius: 6px;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.45);
      pointer-events: none;
    }}
    .zoom-pane {{
      position: absolute;
      top: 56px;
      right: 10px;
      z-index: 3;
      display: none;
      width: min(320px, 44%);
      aspect-ratio: 1;
      background-color: #ffffff;
      background-repeat: no-repeat;
      border: 1px solid var(--border);
      border-radius: 8px;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
      pointer-events: none;
    }}
    .image-review.zooming .zoom-lens,
    .image-review.zooming .zoom-pane {{
      display: block;
    }}
    .image-count {{
      min-width: 42px;
      color: #55554f;
      font-size: 13px;
      text-align: center;
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
          "qa"
          "image"
          "attribution"
          "credits";
      }}
      .app-header {{
        grid-template-columns: auto minmax(0, 1fr);
      }}
      .toolbar {{
        grid-column: 1 / -1;
        justify-content: flex-start;
      }}
      h1 {{
        font-size: 16px;
      }}
      .zoom-lens,
      .zoom-pane {{
        display: none !important;
      }}
      .image-stage {{
        cursor: default;
      }}
    }}
    @media (hover: none) {{
      .zoom-lens,
      .zoom-pane {{
        display: none !important;
      }}
      .image-stage {{
        cursor: default;
      }}
    }}
  </style>
</head>
<body>
  <header class="app-header">
    <a class="deck-link" href="index.html">Decks</a>
    <div class="title-block">
      <p class="eyebrow">UBC-IAA</p>
      <h1>{html.escape(title)}</h1>
    </div>
    <nav class="toolbar" aria-label="Review controls">
      <span class="toolbar-label">Answers</span>
      <label class="answer-control">
        <input type="checkbox" id="toggle-primary" data-group="primary" checked>
        <span>Primary</span>
      </label>
      <label class="answer-control">
        <input type="checkbox" id="toggle-secondary" data-group="secondary" checked>
        <span>Secondary</span>
      </label>
      <label class="answer-control">
        <input type="checkbox" id="toggle-all" data-group="all" checked>
        <span>All</span>
      </label>
    </nav>
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

    const primaryToggle = document.getElementById("toggle-primary");
    const secondaryToggle = document.getElementById("toggle-secondary");
    const allToggle = document.getElementById("toggle-all");

    function cardsFor(group) {{
      if (group === "all") return Array.from(document.querySelectorAll(".qa"));
      return Array.from(document.querySelectorAll(`.qa[data-group="${{group}}"]`));
    }}

    function setToggleState(toggle, cards) {{
      const visible = cards.filter((card) => !card.classList.contains("hidden")).length;
      toggle.disabled = cards.length === 0;
      toggle.checked = cards.length > 0 && visible === cards.length;
      toggle.indeterminate = visible > 0 && visible < cards.length;
    }}

    function syncAnswerControls() {{
      setToggleState(primaryToggle, cardsFor("primary"));
      setToggleState(secondaryToggle, cardsFor("secondary"));
      setToggleState(allToggle, cardsFor("all"));
    }}

    primaryToggle.addEventListener("change", () => {{
      cardsFor("primary").forEach((card) => setPanel(card, !primaryToggle.checked));
      syncAnswerControls();
    }});

    secondaryToggle.addEventListener("change", () => {{
      cardsFor("secondary").forEach((card) => setPanel(card, !secondaryToggle.checked));
      syncAnswerControls();
    }});

    allToggle.addEventListener("change", () => {{
      cardsFor("all").forEach((card) => setPanel(card, !allToggle.checked));
      syncAnswerControls();
    }});

    document.querySelectorAll(".answer-toggle").forEach((button) => {{
      button.addEventListener("click", (event) => {{
        event.stopPropagation();
        const card = button.closest(".qa");
        setPanel(card, !card.classList.contains("hidden"));
        syncAnswerControls();
      }});
    }});

    document.querySelectorAll(".qa").forEach((card) => {{
      card.addEventListener("click", () => {{
        setPanel(card, !card.classList.contains("hidden"));
        syncAnswerControls();
      }});
    }});

    syncAnswerControls();

    function hideZoom(figure) {{
      figure.classList.remove("zooming");
    }}

    function updateZoom(figure, event) {{
      if (!window.matchMedia("(hover: hover)").matches) {{
        hideZoom(figure);
        return;
      }}

      const image = figure.querySelector(".image-stage img.active");
      const lens = figure.querySelector(".zoom-lens");
      const pane = figure.querySelector(".zoom-pane");
      if (!image || !lens || !pane) return;

      const imageRect = image.getBoundingClientRect();
      const x = event.clientX - imageRect.left;
      const y = event.clientY - imageRect.top;
      if (x < 0 || y < 0 || x > imageRect.width || y > imageRect.height) {{
        hideZoom(figure);
        return;
      }}

      const zoom = 2.5;
      figure.classList.add("zooming");

      const figureRect = figure.getBoundingClientRect();
      const paneRect = pane.getBoundingClientRect();
      const clamp = (value, min, max) => Math.max(min, Math.min(value, max));
      const lensWidth = Math.min(imageRect.width, paneRect.width / zoom);
      const lensHeight = Math.min(imageRect.height, paneRect.height / zoom);
      const lensX = imageRect.left - figureRect.left + clamp(x - lensWidth / 2, 0, imageRect.width - lensWidth);
      const lensY = imageRect.top - figureRect.top + clamp(y - lensHeight / 2, 0, imageRect.height - lensHeight);

      lens.style.width = `${{lensWidth}}px`;
      lens.style.height = `${{lensHeight}}px`;
      lens.style.transform = `translate3d(${{lensX}}px, ${{lensY}}px, 0)`;

      const backgroundWidth = imageRect.width * zoom;
      const backgroundHeight = imageRect.height * zoom;
      const backgroundX = clamp(paneRect.width / 2 - x * zoom, paneRect.width - backgroundWidth, 0);
      const backgroundY = clamp(paneRect.height / 2 - y * zoom, paneRect.height - backgroundHeight, 0);

      pane.style.backgroundImage = `url("${{image.currentSrc || image.src}}")`;
      pane.style.backgroundSize = `${{backgroundWidth}}px ${{backgroundHeight}}px`;
      pane.style.backgroundPosition = `${{backgroundX}}px ${{backgroundY}}px`;
    }}

    function setImage(figure, index) {{
      const images = Array.from(figure.querySelectorAll(".image-stage img"));
      if (!images.length) return;

      hideZoom(figure);
      const nextIndex = (index + images.length) % images.length;
      figure.dataset.current = String(nextIndex);
      images.forEach((image, imageIndex) => {{
        const active = imageIndex === nextIndex;
        image.classList.toggle("active", active);
        image.setAttribute("aria-hidden", active ? "false" : "true");
      }});

      const counter = figure.querySelector(".image-count");
      if (counter) {{
        counter.textContent = `${{nextIndex + 1}} / ${{images.length}}`;
      }}
    }}

    document.querySelectorAll(".image-review").forEach((figure) => {{
      setImage(figure, Number(figure.dataset.current || 0));
      const stage = figure.querySelector(".image-stage");

      figure.querySelector(".image-prev")?.addEventListener("click", () => {{
        setImage(figure, Number(figure.dataset.current || 0) - 1);
      }});

      figure.querySelector(".image-next")?.addEventListener("click", () => {{
        setImage(figure, Number(figure.dataset.current || 0) + 1);
      }});

      stage?.addEventListener("pointermove", (event) => updateZoom(figure, event));
      stage?.addEventListener("pointerleave", () => hideZoom(figure));
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
