# UBC_IAA_pipeline

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Build Anki Deck

```bash
.venv/bin/python build_anki_deck.py
```

The script writes `UBC-IAA.apkg` and `error.csv` in the repo root.

## Build PDF Decks

```bash
.venv/bin/python build_pdf_decks.py
```

The script writes one PDF per course/lab combo into `pdfs/`.

## Build HTML Study Decks

```bash
.venv/bin/python build_html_decks.py
```

The script writes clickable hide/show study decks into `htmls/`.

## Build HTML Testers

```bash
.venv/bin/python build_html_tester.py
```

The script writes type-your-answer tester pages into `html_tests/`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the spreadsheet, image naming, and
review workflow used by deck contributors.
