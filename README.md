# UBC_IAA_pipeline

![UBC IAA anatomy deck project status](project_status.png)

## For users

[Download the latest UBC IAA Anki deck](https://drive.google.com/drive/folders/16NqVKhlYowYreh6T2Xh8ZqJlWgYB9zbg?usp=sharing).

Download `UBC-IAA.apkg`, then open the file to import it into Anki. Updates are
not installed automatically; download and import the newest package when a new
version is released.

## For contributors

Read [CONTRIBUTING.md](CONTRIBUTING.md) before editing course spreadsheets or
adding images. It explains the folder structure, required spreadsheet columns,
image naming, card tags, and review workflow.

After updating the source material, use the technical instructions below to
rebuild the deck and project-status image.

## Technical setup

### Install Python

Download and install Python from [python.org/downloads](https://www.python.org/downloads/).
On Windows, select **Add Python to PATH** during installation.

### Open the project in a terminal

Open Terminal on macOS/Linux or PowerShell on Windows. Move into the downloaded
project folder:

```bash
cd path/to/UBC_IAA_pipeline
```

Confirm that Python works:

```bash
python --version
```

### Create the project environment

Run:

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Or activate it in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Install the required packages

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The setup is complete. Keep this terminal open and run the commands below.

### Build the Anki deck

```bash
python build_anki_deck.py
```

The script writes `UBC-IAA.apkg` and `error.csv` in the repo root.

### Build the HTML study decks

```bash
python build_html_decks.py
```

The script writes clickable hide/show study decks into `htmls/`.

### Build the HTML testers

```bash
python build_html_tester.py
```

The script writes type-your-answer tester pages into `html_tests/`.

### Regenerate the project-status image

```bash
python generate_project_status.py
```

### Build everything

```bash
python run_all.py
```

The script runs the Anki, HTML study deck, and HTML tester builders.
Use `--continue-on-error` to keep going after a failed builder.

### Archived tools

The old PDF deck builder lives at `archive/build_pdf_decks.py`.
