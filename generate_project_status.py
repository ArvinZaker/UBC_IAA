#!/usr/bin/env python3
from collections import Counter
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

from build_anki_deck import (
    card_group,
    content_workbooks,
    course_name,
    image_dir_for_workbook,
    image_key,
    index_images,
    index_lowercase_primary_images,
    index_variant_images,
    modality_name,
    row_is_empty,
    value,
    workbook_rows,
)


OUTPUT_FILE = Path("project_status.png")
BACKGROUND = "#F5F2EB"
DARK_BLUE = "#17324D"
BLUE = "#3A6EA5"
ORANGE = "#D98E32"
TEXT = "#243447"
MUTED = "#66727F"
MODALITY_COLORS = ["#2A9D8F", "#3A6EA5", "#D98E32", "#8C6BB1", "#C45A67"]


def lighter(color, amount):
    rgb = mcolors.to_rgb(color)
    return tuple(channel + (1 - channel) * amount for channel in rgb)


cards = []
courses = set()
sections = set()

for workbook in content_workbooks():
    modality = modality_name(workbook)
    course = course_name(workbook)
    courses.add((modality, course))
    image_dir = image_dir_for_workbook(workbook)
    images = index_images(image_dir)
    lowercase_images = index_lowercase_primary_images(image_dir)
    variant_images = index_variant_images(image_dir)

    for sheet, _row_number, headers, row in workbook_rows(workbook):
        if sheet.lower() != "master list":
            sections.add((modality, course, sheet))
        if row_is_empty(row):
            continue

        file_name = value(
            row, headers, "file name", "filename", "image", "image link"
        )
        question = value(row, headers, "question")
        answer = value(row, headers, "answer")
        key = image_key(file_name) if file_name else ""
        image = images.get(key) or variant_images.get(key) or lowercase_images.get(key)
        if question and answer and (not file_name or image):
            cards.append(
                {
                    "modality": modality,
                    "course": course,
                    "group": card_group(value(row, headers, "tax", "tag")),
                }
            )

if not cards:
    raise SystemExit("No build-ready cards found")

groups = Counter(card["group"] for card in cards)
modality_counts = Counter(card["modality"] for card in cards)
course_counts = Counter((card["modality"], card["course"]) for card in cards)
modalities = sorted(modality_counts)

plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TEXT})
fig = plt.figure(figsize=(14, 8), facecolor=BACKGROUND)
fig.suptitle(
    "UBC IAA  |  ATLAS DECK OVERVIEW",
    x=0.06,
    y=0.95,
    ha="left",
    fontsize=30,
    fontweight="bold",
    color=DARK_BLUE,
)

overview = fig.add_axes((0.06, 0.16, 0.22, 0.68))
overview.set_facecolor(DARK_BLUE)
overview.set_xticks([])
overview.set_yticks([])
for spine in overview.spines.values():
    spine.set_visible(False)
overview.text(
    0.10, 0.90, "DECK OVERVIEW", transform=overview.transAxes,
    fontsize=14, fontweight="bold", color="#B9C8D4"
)
for y, number, label, color in [
    (0.70, len(modalities), "MODALITIES", "white"),
    (0.48, len(courses), "COURSES", "#73D2C6"),
    (0.26, len(sections), "SECTIONS", "#F2C46D"),
    (0.07, len(cards), "BUILD-READY CARDS", "#F2A23A"),
]:
    overview.text(
        0.10, y, f"{number:,}", transform=overview.transAxes,
        fontsize=34, fontweight="bold", color=color
    )
    overview.text(
        0.10, y - 0.06, label, transform=overview.transAxes,
        fontsize=12, fontweight="bold", color="#B9C8D4"
    )

card_axis = fig.add_axes((0.33, 0.27, 0.25, 0.48))
card_axis.set_title("CARD TYPE", fontsize=16, fontweight="bold", pad=18)
group_values = [groups["Primary"], groups["Secondary"]]
card_axis.pie(
    group_values,
    colors=[BLUE, ORANGE],
    startangle=90,
    counterclock=False,
    wedgeprops={"width": 0.42, "edgecolor": BACKGROUND, "linewidth": 3},
    autopct="%1.0f%%",
    pctdistance=0.79,
    textprops={"color": "white", "fontweight": "bold", "fontsize": 14},
)
card_axis.text(
    0, 0.06, f"{len(cards):,}", ha="center", va="center",
    fontsize=26, fontweight="bold", color=DARK_BLUE
)
card_axis.text(0, -0.12, "CARDS", ha="center", va="center", fontsize=12, color=MUTED)
card_axis.legend(
    [f"Primary  {groups['Primary']:,}", f"Secondary  {groups['Secondary']:,}"],
    loc="lower center",
    bbox_to_anchor=(0.5, -0.18),
    frameon=False,
    ncol=2,
    fontsize=12,
)

topic_axis = fig.add_axes((0.62, 0.12, 0.34, 0.72))
topic_axis.set_title(
    "MAJOR TOPICS\ninner: modality  |  outer: course",
    fontsize=16,
    fontweight="bold",
    pad=16,
)

inner_values = [modality_counts[modality] for modality in modalities]
inner_colors = [
    MODALITY_COLORS[index % len(MODALITY_COLORS)]
    for index, _modality in enumerate(modalities)
]
inner_wedges, _ = topic_axis.pie(
    inner_values,
    radius=0.68,
    colors=inner_colors,
    startangle=90,
    counterclock=False,
    wedgeprops={"width": 0.32, "edgecolor": BACKGROUND, "linewidth": 3},
)

outer_values = []
outer_labels = []
outer_colors = []
for modality_index, modality in enumerate(modalities):
    modality_courses = sorted(
        (course, count)
        for (course_modality, course), count in course_counts.items()
        if course_modality == modality
    )
    for course_index, (course, count) in enumerate(modality_courses):
        outer_values.append(count)
        outer_labels.append(course)
        shade = 0.12 + 0.14 * (course_index % 4)
        outer_colors.append(lighter(inner_colors[modality_index], shade))

topic_axis.pie(
    outer_values,
    radius=1.0,
    labels=outer_labels,
    colors=outer_colors,
    startangle=90,
    counterclock=False,
    labeldistance=1.07,
    rotatelabels=False,
    textprops={"fontsize": 12, "color": TEXT},
    wedgeprops={"width": 0.30, "edgecolor": BACKGROUND, "linewidth": 2},
)
topic_axis.legend(
    inner_wedges,
    [f"{modality}  {modality_counts[modality]:,}" for modality in modalities],
    loc="lower center",
    bbox_to_anchor=(0.5, -0.12),
    frameon=False,
    ncol=min(3, len(modalities)),
    fontsize=12,
)

fig.savefig(
    OUTPUT_FILE,
    dpi=220,
    bbox_inches="tight",
    facecolor=fig.get_facecolor(),
)
print(f"Wrote {OUTPUT_FILE} with {len(cards):,} cards")
