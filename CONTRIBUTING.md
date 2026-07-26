# How to Contribute Cards

Thanks for helping build the UBC IAA Anki deck. The short version is:

1. Add your card rows to the right Excel file.
2. Add the matching images to the matching image folder.
3. Review other's work to make sure we make the best ANKI deck that exists!

This guide explains the details.

## Getting Access

Contact Arvin Zaker to get access to the project material:

- `arvzaker@student.ubc.ca`
- `arv.zaker@gmail.com`

## Where Things Go

Content is organized by modality in folders whose names end in ` drive`, such
as:

```text
Anatomy drive/
Radio drive/
Ophtho drive/
```

Each course or rotation needs a workbook named `<course>_content.xlsx` and a
matching image folder named `<course>_images/` in the same modality folder.
Course names are flexible and do not need to use a `MEDD_4xx` code:

```text
Anatomy drive/MEDD_411_content.xlsx
Anatomy drive/MEDD_411_images/
Radio drive/Radiology_rotation_content.xlsx
Radio drive/Radiology_rotation_images/
Ophtho drive/Ophthalmology_content.xlsx
Ophtho drive/Ophthalmology_images/
```

The part before `_content.xlsx` must exactly match the part before `_images`.
The builder uses the drive name as the modality and the workbook name as the
course name in Anki.

Inside each workbook, each lab, block, or rotation section gets its own sheet.
For example:

```text
Lab2_spine
Lab1_Cranial_Cavity
```

The `SAMPLE` sheet is just an example. The deck builder ignores it.

## Adding a Card

Each row in a lab sheet becomes one Anki card. Images are optional. Leave the
`file name` cell blank to create a text-only cloze card. If `file name` is
filled, the matching image is required.

Fill in these columns:

| Column | What to put there |
| --- | --------- |
| `file name` | The image name, without `_P` and without `.jpg`/`.png`. Leave blank for a text-only cloze card. |
| `Question` | The prompt, like `Identify` or `What passes through this opening?`, keep the questions similiar to what is asked on a bellringer. |
| `Answer` | The answer students should recall. |
| `Tag` | Usually `primary` or `secondary`. Separate multiple tags with a semicolon (`;`), for example `secondary; clinical`. |
| `Attribution` | Etimology, references, etc, if needed. |
| `Authors` | The card author or authors. Separate multiple authors with a semicolon (`;`). |
| `Reviewer` | The reviewer or reviewers. Separate multiple reviewers with a semicolon (`;`). |
| `Comment` | Notes for other contributors or reviewers. This does not show up on the card. |

Example:

| file name | Question | Answer | Tag | Attribution |
| --- | --- | --- | --- | --- |
| `anterior_ramus` | `Identify` | `anterior ramus` | `primary` | |
| `anterior_ramus` | `What nerve modalities are carried by this structure?` | `general sensory, visceral sensory, general motor, visceral motor` | `secondary` | |

Cards with one or more names in the `Reviewer` cell are tagged `reviewed`;
cards without one are tagged `unreviewed`. Cards with a filled `Final approval`
cell are tagged `approved`; cards without one are tagged `unapproved`.

## Adding the Image

The builder finds images by name. This is the easiest place to mess up, so check
this carefully.

Use underscores instead of spaces in file names.

Good:

```text
middle_meningeal_artery
```

Bad:

```text
middle meningeal artery
```

If your spreadsheet says:

```text
anterior_ramus
```

then the image file should be named:

```text
anterior_ramus_P.jpg
```

The `_P` matters. The spreadsheet does not include `_P`, but the image file does.

Good:

```text
file name column: anterior_ramus
image file:       anterior_ramus_P.jpg
```

Bad:

```text
file name column: anterior_ramus_P
image file:       anterior_ramus.jpg
```

Supported image types are `.jpg`, `.jpeg`, `.png`, `.gif`, and `.webp`.

If you have multiple images for the same structure, number the extra files with
`_1`, `_2`, and so on:

```text
filum_terminale_P.jpg
filum_terminale_1.jpg
filum_terminale_2.jpg
```

Use the main `_P` image for the spreadsheet row. The numbered images can stay in
the folder as extra/reference images or to be used for mock bellringer exams.

Keeping images inside the right course and lab folder makes life easier but its not neceessary:

```text
Anatomy drive/MEDD_411_images/Lab2_spine/anterior_ramus_P.jpg
```

When adding a pre-annotated or agentically annotated image, place it in the
matching `MEDD_xxx_images/Lab.../` folder for the workbook and sheet that use
it. Do not place a structure in a different course or lab merely because the
filename matches.

## Tags and Decks

If a row has the tag `primary`, it goes into the `Primary` deck.

Everything else goes into the `Secondary` deck.

So this:

```text
Tag: primary
```

goes here:

```text
UBC-IAA::Anatomy::MEDD 411::Lab 2 Spine::Primary
```

And this:

```text
Tag: secondary
```

goes here:

```text
UBC-IAA::Anatomy::MEDD 411::Lab 2 Spine::Secondary
```

Use `primary` for basic identification cards. Use `secondary` for follow-up,
clinical, explanation, or integration questions.


Use a semicolon (`;`) to separate multiple tags, authors, or reviewers:

```text
Tag:      secondary; clinical
Authors:  Alex Chen; Sam Lee
Reviewer: Priya Shah; Taylor Wong
```

## Building the Deck

First install the Python dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Then build the deck:

```bash
.venv/bin/python build_anki_deck.py
```

This creates:

```text
UBC-IAA-all.apkg
UBC-IAA-anatomy.apkg
error.csv
```

Import `UBC-IAA-all.apkg` to test the complete atlas or the relevant
`UBC-IAA-<modality>.apkg` subset. All packages use the same card identifiers
and deck hierarchy, so importing a subset and the complete atlas does not
duplicate shared cards.

If `.venv/bin/python` does not work, recreate the virtual environment on your
own computer. Virtual environments often break when a project folder gets moved
between machines.

## Checking for Problems

Always open `error.csv` after building.

Rows with errors were skipped. Rows reporting a fallback image are warnings;
those cards were created with the named fallback image.

Common fixes:

| Error | Fix |
| --- | --- |
| `no question specified` | Add a question. |
| `no answer specified` | Add an answer. |
| `image could not be found` | Check that the image file exists and ends in `_P`. |

## Before You Submit

Quick checklist:

- [ ] Your rows are in the correct course workbook.
- [ ] Your rows are in the correct lab sheet.
- [ ] Every finished row has `Question` and `Answer`.
- [ ] File names use underscores instead of spaces.
- [ ] Every image used by a card ends in `_P`.
- [ ] Extra images for the same structure are named with `_1`, `_2`, etc.
- [ ] If `file name` is filled, it matches the image file name.
- [ ] Primary ID cards are tagged `primary`.
- [ ] Clinical or follow-up cards are tagged clearly.
- [ ] Multiple tags, authors, or reviewers are separated with a semicolon (`;`).
- [ ] You ran `build_anki_deck.py`.
- [ ] You checked `error.csv`.
- [ ] You imported the deck into Anki and made sure the images show up.

That is it. If the deck builds, `error.csv` looks expected, and the cards look
right in Anki, you are good.
