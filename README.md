# UBC Integrated Anatomy Atlas (UBC IAA)

![UBC IAA anatomy deck project status](project_status.png)

## Introduction

The UBC Integrated Anatomy Atlas (UBC IAA) is a student-led educational resource developed in collaboration with UBC anatomy faculty to support anatomy learning throughout the preclinical MD curriculum. The project combines high-quality anatomy images with curriculum-aligned questions to create a standardized study resource available in multiple formats.

This repository contains the automated pipeline used to generate the UBC IAA
Anki deck and project progress report while maintaining a consistent structure
across all outputs.

By centralizing content generation, contributors can update course spreadsheets and images once, then automatically regenerate every learning resource. This reduces manual work, improves consistency, and simplifies maintenance as the atlas continues to expand.

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

Complete these steps once before running the project:

- [ ] Step 1: Install Python.
- [ ] Step 2: Open the project folder in a terminal.
- [ ] Step 3: Confirm that Python works.
- [ ] Step 4: Create the project environment.
- [ ] Step 5: Activate the project environment.
- [ ] Step 6: Install the required packages.
- [ ] Step 7: Build the Anki deck.

When the instructions show a command in a box, copy the command, paste it into
the terminal, and press Enter. Wait for the terminal prompt to return before
entering the next command. Do not type the word `bash` or `powershell` shown
above a command box.

### Step 1: Install Python

Download and install Python from [python.org/downloads](https://www.python.org/downloads/).
On Windows, select **Add Python to PATH** during installation.

### Step 2: Open the project folder in a terminal

First, find the downloaded `UBC_IAA_pipeline` folder on your computer. If it was
downloaded as a ZIP file, extract the ZIP before continuing.

**Windows**

1. Open the `UBC_IAA_pipeline` folder in File Explorer.
2. Click the address bar at the top of File Explorer.
3. Type `powershell` and press Enter.
4. A PowerShell window will open in the correct folder.

**macOS or Linux**

1. Open the Terminal application.
2. Type `cd `, including the space after `cd`.
3. Drag the `UBC_IAA_pipeline` folder from Finder or your file manager into the
   Terminal window.
4. Press Enter.

The terminal is now open in the project folder. Leave it open for all remaining
steps.

### Step 3: Confirm that Python works

Copy, paste, and run:

```bash
python --version
```

The command should print a Python version. If it says that Python cannot be
found, reinstall Python and ensure it is added to PATH.

### Step 4: Create the project environment

Copy, paste, and run:

```bash
python -m venv .venv
```

Wait for the command to finish. It creates a hidden `.venv` folder containing
the project environment.

### Step 5: Activate the project environment

On macOS or Linux, copy, paste, and run:

```bash
source .venv/bin/activate
```

On Windows PowerShell, copy, paste, and run:

```powershell
.venv\Scripts\Activate.ps1
```

After activation, the terminal prompt should begin with `(.venv)`.

### Step 6: Install the required packages

Run these commands one at a time. The installation may take several minutes:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Wait until the terminal prompt returns before continuing.

### Step 7: Build the Anki deck

Copy, paste, and run:

```bash
python build_anki_deck.py
```

When the build finishes, the project folder will contain `UBC-IAA.apkg` and
`error.csv`. The Anki deck is now ready to import and test.

## Optional technical commands

### Regenerate the project-status image

```bash
python generate_project_status.py
```

### Build everything

```bash
python run_all.py
```

The script runs the Anki deck and project-status builders.
Use `--continue-on-error` to keep going after a failed builder.
