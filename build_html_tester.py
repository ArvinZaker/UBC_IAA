#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import quote
import html
import re

from build_anki_deck import (
    IMAGE_DIR,
    INPUT_DIR,
    IMAGE_EXTS,
    course_name,
    image_key,
    lab_name,
    row_is_empty,
    value,
    workbook_rows,
)


OUTPUT_DIR = Path("html_tests")


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


def variant_key(path):
    stem = path.stem
    if stem.endswith("_P"):
        return stem[:-2]
    return re.sub(r"_\d+$", "", stem)


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


def index_image_variants(image_root):
    images = {}
    for path in image_root.rglob("*"):
        if path.suffix.lower() in IMAGE_EXTS:
            images.setdefault(variant_key(path), []).append(path)

    for paths in images.values():
        paths.sort(key=lambda path: (not path.stem.endswith("_P"), path.stem))

    return images


def collect_decks():
    images = index_image_variants(IMAGE_DIR)
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
            key = image_key(file_name) if file_name else ""
            image_paths = images.get(key, [])

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
            page["qa"].append((question, answer))
            merge_metadata(page, row_metadata(row, headers))

    return decks, skipped


def image_gallery(image_paths):
    images = "\n".join(
        f'<img src="{image_src(path)}" alt="{html.escape(path.stem)}">' for path in image_paths
    )
    return f'<figure class="images">{images}</figure>'


def question_html(question, answer):
    return f"""
    <form class="qa" data-answer="{html.escape(answer, quote=True)}">
      <label>
        <span class="question">{html.escape(question)}</span>
        <textarea rows="2" autocomplete="off" spellcheck="false"></textarea>
      </label>
      <button type="submit">Submit</button>
      <div class="result" hidden></div>
      <div class="answer" hidden>
        <strong>Answer:</strong> {html.escape(answer)}
      </div>
    </form>
    """


def page_html(course, sheet, page, index):
    questions = "\n".join(question_html(question, answer) for question, answer in page["qa"])
    attribution = "; ".join(page["metadata"]["Attribution"])
    footer = metadata_line(
        page["metadata"],
        ["Image author", "Attribution author", "Reviewer", "Final approval", "Comment"],
    )
    return f"""
    <section class="slide" data-station="{index}">
      <div class="brand">
        <strong>UBC-IAA</strong>
        <span>{html.escape(course)} - {html.escape(lab_name(sheet))}</span>
      </div>
      <div class="qa-list">
        {questions}
      </div>
      {image_gallery(page["images"])}
      <aside class="attribution">
        <strong>Attribution</strong>
        <p>{html.escape(attribution)}</p>
      </aside>
      <footer class="credits">{html.escape(footer)}</footer>
    </section>
    """


def write_deck(course, sheet, pages):
    file_name = f"{safe_name(course)}_{safe_name(lab_name(sheet))}_Tester.html"
    path = OUTPUT_DIR / file_name
    title = f"{course} - {lab_name(sheet)} Tester"
    slides = "\n".join(page_html(course, sheet, page, index) for index, page in enumerate(pages.values()))

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
      z-index: 2;
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
    a, button {{
      border: 1px solid #bbbbB2;
      border-radius: 6px;
      padding: 8px 10px;
      background: #ffffff;
      color: #171717;
      font: inherit;
      text-decoration: none;
      cursor: pointer;
    }}
    button:disabled {{
      cursor: not-allowed;
      opacity: 0.45;
    }}
    .station-controls {{
      display: none;
      align-items: center;
      gap: 8px;
    }}
    body.testing .station-controls {{
      display: flex;
    }}
    body.results .station-controls {{
      display: none;
    }}
    #station-progress {{
      min-width: 92px;
      color: #55554f;
      text-align: center;
    }}
    #timer {{
      display: none;
      min-width: 70px;
      padding: 8px 10px;
      background: #171717;
      color: #ffffff;
      border-radius: 6px;
      text-align: center;
      font-weight: 700;
    }}
    body.testing #timer {{
      display: inline-block;
    }}
    .intro {{
      max-width: 720px;
      margin: 28px;
      padding: 22px;
      background: #ffffff;
      border: 1px solid #d8d8d2;
      border-radius: 8px;
    }}
    .intro h2 {{
      margin: 0 0 8px;
      font-size: 24px;
    }}
    .intro p {{
      margin: 0 0 18px;
      color: #55554f;
    }}
    .mode-options {{
      display: grid;
      gap: 10px;
      margin-bottom: 18px;
    }}
    .mode-options label {{
      display: flex;
      gap: 9px;
      align-items: center;
      padding: 10px;
      background: #fafaf7;
      border: 1px solid #d2d2ca;
      border-radius: 8px;
    }}
    main {{
      display: none;
      gap: 18px;
      padding: 18px;
    }}
    body.testing main {{
      display: grid;
    }}
    body.testing .intro {{
      display: none;
    }}
    body.results .intro, body.results main {{
      display: none;
    }}
    .slide {{
      display: none;
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
    .slide.active {{
      display: grid;
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
      padding: 14px;
      background: #fafaf7;
      border: 1px solid #d2d2ca;
      border-radius: 8px;
    }}
    label, .question {{
      display: block;
    }}
    .question {{
      margin-bottom: 9px;
      font-size: 18px;
      font-weight: 700;
      line-height: 1.35;
    }}
    textarea {{
      box-sizing: border-box;
      width: 100%;
      min-height: 64px;
      margin-bottom: 10px;
      padding: 10px;
      border: 1px solid #bbbbB2;
      border-radius: 6px;
      font: inherit;
      resize: vertical;
    }}
    .answer {{
      margin-top: 10px;
      padding: 10px;
      background: #eef3e9;
      border: 1px solid #c9d8c0;
      border-radius: 6px;
      line-height: 1.4;
    }}
    .result {{
      display: inline-block;
      margin-left: 8px;
      padding: 8px 10px;
      border-radius: 6px;
      font-weight: 700;
    }}
    .result.correct {{
      background: #e3f1df;
      color: #1e5a22;
    }}
    .result.close {{
      background: #fff2c8;
      color: #6a4a00;
    }}
    .result.missed {{
      background: #f7dddd;
      color: #7a1e1e;
    }}
    .images {{
      grid-area: image;
      display: grid;
      place-items: center;
      gap: 12px;
      margin: 0;
      min-width: 0;
    }}
    img {{
      max-width: 100%;
      max-height: 42vh;
      object-fit: contain;
    }}
    .images img:only-child {{
      max-height: calc(100vh - 150px);
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
    .results-page {{
      display: none;
      padding: 18px;
    }}
    body.results .results-page {{
      display: block;
    }}
    .score {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
    }}
    .score span {{
      padding: 8px 10px;
      background: #ffffff;
      border: 1px solid #d8d8d2;
      border-radius: 6px;
    }}
    .review-card {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 20px;
      margin-bottom: 18px;
      padding: 18px;
      background: #ffffff;
      border: 1px solid #d8d8d2;
      border-radius: 8px;
    }}
    .review-card .images {{
      align-content: start;
    }}
    .review-item {{
      margin-bottom: 14px;
      padding-bottom: 14px;
      border-bottom: 1px solid #e4e4dd;
    }}
    .review-item:last-child {{
      border-bottom: 0;
    }}
    .student-answer {{
      white-space: pre-wrap;
    }}
    @media (max-width: 800px) {{
      .slide, .review-card {{
        grid-template-columns: 1fr;
      }}
      .slide {{
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
    <a href="index.html">All testers</a>
    <h1>{html.escape(title)}</h1>
    <div class="station-controls">
      <button type="button" id="prev-station">Previous</button>
      <span id="station-progress"></span>
      <button type="button" id="next-station">Next</button>
    </div>
    <span id="timer">--:--</span>
    <button type="button" id="reset-test">Reset</button>
  </header>
  <section class="intro">
    <h2>{html.escape(title)}</h2>
    <p>Choose a bellringer length, move station by station, and submit answers for a rough grade.</p>
    <div class="mode-options">
      <label><input type="radio" name="test-mode" value="ten" checked> Random 10 stations</label>
      <label><input type="radio" name="test-mode" value="all"> All stations</label>
    </div>
    <button type="button" id="start-test-intro">Start test</button>
  </section>
  <main>
    {slides}
  </main>
  <section class="results-page">
    <h2>Results</h2>
    <div class="score" id="score"></div>
    <div id="review"></div>
    <button type="button" id="restart-test">Restart</button>
  </section>
  <script>
    const slides = Array.from(document.querySelectorAll(".slide"));
    const timer = document.getElementById("timer");
    let activeSlides = [];
    let currentStation = 0;
    let timerId = null;
    let secondsLeft = 0;

    function shuffle(items) {{
      const shuffled = [...items];
      for (let index = shuffled.length - 1; index > 0; index -= 1) {{
        const swapIndex = Math.floor(Math.random() * (index + 1));
        [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
      }}
      return shuffled;
    }}

    function formatTime(totalSeconds) {{
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = String(totalSeconds % 60).padStart(2, "0");
      return `${{minutes}}:${{seconds}}`;
    }}

    function stopTimer() {{
      if (timerId) clearInterval(timerId);
      timerId = null;
    }}

    function startTimerFor(slide) {{
      stopTimer();
      secondsLeft = slide.querySelectorAll(".qa").length * 60;
      timer.textContent = formatTime(secondsLeft);
      timerId = setInterval(() => {{
        secondsLeft -= 1;
        timer.textContent = formatTime(Math.max(0, secondsLeft));
        if (secondsLeft <= 0) {{
          stopTimer();
          finalizeStation(slide);
          goNext();
        }}
      }}, 1000);
    }}

    function showStation(index) {{
      currentStation = Math.max(0, Math.min(index, activeSlides.length - 1));
      slides.forEach((slide) => {{
        slide.classList.toggle("active", slide === activeSlides[currentStation]);
      }});
      document.getElementById("prev-station").disabled = currentStation === 0;
      document.getElementById("next-station").textContent = currentStation === activeSlides.length - 1 ? "Finish" : "Next";
      document.getElementById("station-progress").textContent = `Station ${{currentStation + 1}} / ${{activeSlides.length}}`;
      activeSlides[currentStation]?.querySelector("textarea")?.focus();
      startTimerFor(activeSlides[currentStation]);
    }}

    function startTest() {{
      const mode = document.querySelector('input[name="test-mode"]:checked').value;
      activeSlides = mode === "ten" ? shuffle(slides).slice(0, Math.min(10, slides.length)) : [...slides];
      currentStation = 0;
      slides.forEach((slide) => slide.classList.remove("active"));
      document.body.classList.remove("results");
      document.body.classList.add("testing");
      showStation(currentStation);
    }}

    function resetTest() {{
      stopTimer();
      document.querySelectorAll(".qa").forEach((form) => {{
        form.reset();
        form.dataset.graded = "";
        form.dataset.grade = "";
        form.dataset.gradeLabel = "";
        form.querySelector(".result").hidden = true;
        form.querySelector(".answer").hidden = true;
      }});
      slides.forEach((slide) => slide.classList.remove("active"));
      activeSlides = [];
      document.body.classList.remove("testing");
      document.body.classList.remove("results");
      currentStation = 0;
      window.scrollTo(0, 0);
    }}

    function normalize(text) {{
      return text
        .toLowerCase()
        .replace(/&/g, " and ")
        .replace(/[()]/g, " ")
        .replace(/[^a-z0-9]+/g, " ")
        .trim()
        .replace(/\\s+/g, " ");
    }}

    function editDistance(a, b) {{
      const previous = Array.from({{ length: b.length + 1 }}, (_, index) => index);
      for (let i = 1; i <= a.length; i += 1) {{
        let last = previous[0];
        previous[0] = i;
        for (let j = 1; j <= b.length; j += 1) {{
          const old = previous[j];
          previous[j] = Math.min(
            previous[j] + 1,
            previous[j - 1] + 1,
            last + (a[i - 1] === b[j - 1] ? 0 : 1)
          );
          last = old;
        }}
      }}
      return previous[b.length];
    }}

    function tokenScore(student, expected) {{
      const studentTokens = new Set(student.split(" ").filter(Boolean));
      const expectedTokens = expected.split(" ").filter(Boolean);
      if (!studentTokens.size || !expectedTokens.length) return 0;
      const matched = expectedTokens.filter((token) => studentTokens.has(token)).length;
      return matched / expectedTokens.length;
    }}

    function gradeAnswer(studentRaw, expectedRaw) {{
      const student = normalize(studentRaw);
      const expected = normalize(expectedRaw);
      if (!student) return ["missed", "No answer"];
      if (student === expected) {{
        return ["correct", "Correct"];
      }}
      if (student.length >= 5 && (expected.includes(student) || student.includes(expected))) {{
        return ["correct", "Correct"];
      }}

      const maxLength = Math.max(student.length, expected.length);
      const similarity = maxLength ? 1 - editDistance(student, expected) / maxLength : 0;
      const overlap = tokenScore(student, expected);

      if (similarity >= 0.84 || overlap >= 0.8) return ["correct", "Correct"];
      if (similarity >= 0.65 || overlap >= 0.5) return ["close", "Close"];
      return ["missed", "Check answer"];
    }}

    function escapeHtml(text) {{
      return text.replace(/[&<>"']/g, (char) => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }}[char]));
    }}

    function gradeForm(form) {{
      const result = form.querySelector(".result");
      const [grade, label] = gradeAnswer(form.querySelector("textarea").value, form.dataset.answer);
      result.className = `result ${{grade}}`;
      result.textContent = label;
      result.hidden = false;
      form.querySelector(".answer").hidden = false;
      form.dataset.graded = "true";
      form.dataset.grade = grade;
      form.dataset.gradeLabel = label;
      return grade;
    }}

    function finalizeStation(slide) {{
      slide.querySelectorAll(".qa").forEach((form) => gradeForm(form));
    }}

    function goNext() {{
      if (!activeSlides.length) return;
      finalizeStation(activeSlides[currentStation]);
      if (currentStation >= activeSlides.length - 1) {{
        showResults();
      }} else {{
        showStation(currentStation + 1);
      }}
    }}

    function resultImages(slide) {{
      return slide.querySelector(".images").innerHTML;
    }}

    function resultAttribution(slide) {{
      return slide.querySelector(".attribution").innerHTML;
    }}

    function resultCredits(slide) {{
      return slide.querySelector(".credits").innerHTML;
    }}

    function showResults() {{
      stopTimer();
      document.body.classList.remove("testing");
      document.body.classList.add("results");
      slides.forEach((slide) => slide.classList.remove("active"));

      const totals = {{ correct: 0, close: 0, missed: 0, blank: 0 }};
      const review = activeSlides.map((slide, index) => {{
        const items = Array.from(slide.querySelectorAll(".qa")).map((form) => {{
          const student = form.querySelector("textarea").value.trim();
          const grade = form.dataset.grade || "missed";
          totals[grade] = (totals[grade] || 0) + 1;
          if (!student) totals.blank += 1;
          return `
            <div class="review-item">
              <p><strong>Question:</strong> ${{escapeHtml(form.querySelector(".question").textContent)}}</p>
              <p><strong>Your answer:</strong> <span class="student-answer">${{escapeHtml(student || "(blank)")}}</span></p>
              <p><strong>Correct answer:</strong> ${{escapeHtml(form.dataset.answer)}}</p>
              <p><strong>Grade:</strong> ${{escapeHtml(form.dataset.gradeLabel || "Check answer")}}</p>
            </div>
          `;
        }}).join("");

        return `
          <article class="review-card">
            <div>
              <h3>Station ${{index + 1}}</h3>
              ${{items}}
              <aside class="attribution">${{resultAttribution(slide)}}</aside>
              <footer class="credits">${{resultCredits(slide)}}</footer>
            </div>
            <figure class="images">${{resultImages(slide)}}</figure>
          </article>
        `;
      }}).join("");

      document.getElementById("score").innerHTML = `
        <span>Correct: ${{totals.correct}}</span>
        <span>Close: ${{totals.close}}</span>
        <span>Missed/check: ${{totals.missed}}</span>
        <span>Blank: ${{totals.blank}}</span>
      `;
      document.getElementById("review").innerHTML = review;
      window.scrollTo(0, 0);
    }}

    document.getElementById("start-test-intro").addEventListener("click", startTest);
    document.getElementById("reset-test").addEventListener("click", resetTest);
    document.getElementById("restart-test").addEventListener("click", resetTest);
    document.getElementById("prev-station").addEventListener("click", () => {{
      finalizeStation(activeSlides[currentStation]);
      showStation(currentStation - 1);
    }});
    document.getElementById("next-station").addEventListener("click", goNext);

    document.querySelectorAll(".qa").forEach((form) => {{
      form.addEventListener("submit", (event) => {{
        event.preventDefault();
        gradeForm(form);
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
          <span>{page_count} image page(s), {qa_count} question(s)</span>
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
  <title>UBC IAA Testers</title>
  <style>
    body {{
      margin: 0;
      padding: 28px;
      background: #f4f4f1;
      color: #171717;
      font-family: Arial, sans-serif;
    }}
    h1 {{
      margin: 0 0 22px;
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
  <h1>UBC IAA Testers</h1>
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
        title = f"{course} - {lab_name(sheet)} Tester"
        qa_count = sum(len(page["qa"]) for page in pages.values())
        deck_links.append((title, path, len(pages), qa_count))

    write_index(deck_links, skipped)

    print(f"Wrote {len(deck_links)} tester deck(s) to {OUTPUT_DIR}")
    print(f"Pages: {sum(page_count for _title, _path, page_count, _qa_count in deck_links)}")
    print(f"Questions: {sum(qa_count for _title, _path, _page_count, qa_count in deck_links)}")
    print(f"Skipped rows: {skipped}")
    print(OUTPUT_DIR / "index.html")


if __name__ == "__main__":
    main()
