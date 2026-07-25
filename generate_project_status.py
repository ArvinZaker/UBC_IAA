#!/usr/bin/env python3
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

from build_anki_deck import (
    card_group,
    content_workbooks,
    course_name,
    image_key,
    image_dir_for_workbook,
    index_images,
    index_lowercase_primary_images,
    index_variant_images,
    modality_name,
    row_is_empty,
    split_people,
    value,
    workbook_rows,
)


OUTPUT_FILE = Path("project_status.png")
BLUE = "#3A6EA5"
TEAL = "#2A9D8F"
GOLD = "#E9C46A"
LIGHT_GREY = "#E8ECEF"
DARK = "#243447"


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
        file_name = value(row, headers, "file name", "filename", "image", "image link")
        question = value(row, headers, "question")
        answer = value(row, headers, "answer")
        key = image_key(file_name) if file_name else ""
        image = images.get(key) or variant_images.get(key) or lowercase_images.get(key)
        if file_name and question and answer and image:
            cards.append(
                {
                    "group": card_group(value(row, headers, "tax", "tag")),
                    "author": value(row, headers, "authors"),
                    "reviewer": value(row, headers, "reviewer"),
                    "faculty": value(row, headers, "final approval"),
                }
            )

groups = Counter(card["group"] for card in cards)
authors = Counter(
    author
    for card in cards
    for author in split_people(card["author"])
)
reviewers = Counter(
    reviewer
    for card in cards
    for reviewer in split_people(card["reviewer"])
)
reviewed = sum(bool(card["reviewer"]) for card in cards)
faculty_reviewed = sum(bool(card["faculty"]) for card in cards)

plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": DARK})
fig = plt.figure(figsize=(12, 14), facecolor="#F7F4EE")
fig.text(0.5, 0.955, "UBC IAA", fontsize=38, fontweight="bold", color="#17324D", ha="center")
fig.text(0.5, 0.915, "ATLAS DECK", fontsize=17, fontweight="bold", color=TEAL, ha="center")

fig.patches.append(plt.Rectangle((0.07, 0.59), 0.39, 0.27, transform=fig.transFigure, color="#17324D", zorder=-1))
fig.text(0.10, 0.82, "DECK OVERVIEW", fontsize=11, fontweight="bold", color="#B9C8D4")
for x, y, value_text, label, color in [
    (0.10, 0.75, f"{len(courses)}", "COURSES", "white"),
    (0.29, 0.75, f"{len(sections)}", "SECTIONS", "#73D2C6"),
    (0.10, 0.64, f"{len(cards):,}", "BUILD-READY CARDS", "#F2A23A"),
]:
    fig.text(x, y, value_text, fontsize=32, fontweight="bold", color=color)
    fig.text(x, y - 0.035, label, fontsize=9.5, fontweight="bold", color="#B9C8D4")

fig.patches.append(plt.Rectangle((0.52, 0.59), 0.41, 0.27, transform=fig.transFigure, color="white", zorder=-1))
fig.text(0.55, 0.82, "CARD TYPE", fontsize=11, fontweight="bold", color="#66727F")
card_axis = fig.add_axes((0.54, 0.62, 0.22, 0.18))
_wedges, _texts, percentages = card_axis.pie(
    [groups["Primary"], groups["Secondary"]],
    colors=[BLUE, "#D98E32"],
    startangle=90,
    counterclock=False,
    wedgeprops={"width": 0.58, "edgecolor": "white", "linewidth": 3},
    autopct="%1.0f%%",
    pctdistance=0.72,
)
for percentage in percentages:
    percentage.set_color("white")
    percentage.set_fontsize(11)
    percentage.set_fontweight("bold")
for y, count, label, color in [
    (0.73, groups["Primary"], "PRIMARY", BLUE),
    (0.66, groups["Secondary"], "SECONDARY", "#D98E32"),
]:
    fig.text(0.79, y, f"{count:,}", fontsize=21, fontweight="bold", color=color)
    fig.text(0.79, y - 0.027, label, fontsize=9.5, fontweight="bold", color="#66727F")

bar_axes = [fig.add_axes((0.10, 0.37, 0.36, 0.15)), fig.add_axes((0.57, 0.37, 0.36, 0.15))]
for axis, counts, title, color in [
    (bar_axes[0], authors, "CARDS BY CONTRIBUTOR", BLUE),
    (bar_axes[1], reviewers, "CARDS BY STUDENT REVIEWER", TEAL),
]:
    names = [name for name, _count in counts.most_common()][::-1]
    values = [count for _name, count in counts.most_common()][::-1]
    axis.barh(names, values, color=color, height=0.48)
    axis.set_title(title, fontsize=12, fontweight="bold", loc="left", pad=15)
    axis.set_xscale("log")
    axis.set_xlim(1, max(values) * 1.15)
    axis.spines[:].set_visible(False)
    axis.set_facecolor("#F7F4EE")
    axis.tick_params(axis="x", bottom=False, labelbottom=False)
    axis.set_xticks([])
    axis.set_xticks([], minor=True)
    axis.tick_params(axis="y", length=0, labelsize=9.5)

review_axes = [fig.add_axes((0.14, 0.08, 0.28, 0.22)), fig.add_axes((0.58, 0.08, 0.28, 0.22))]
for axis, count, title, color in [
    (review_axes[0], reviewed, "STUDENT REVIEW", TEAL),
    (review_axes[1], faculty_reviewed, "FACULTY REVIEW", GOLD),
]:
    axis.pie(
        [count, len(cards) - count],
        colors=[color, LIGHT_GREY],
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.58, "edgecolor": "#F7F4EE", "linewidth": 3},
    )
    axis.text(0, 0, f"{count / len(cards):.0%}", ha="center", va="center", fontsize=22, fontweight="bold")
    axis.set_title(title, fontsize=13, fontweight="bold", pad=13)
fig.savefig(OUTPUT_FILE, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Wrote {OUTPUT_FILE} with {len(cards):,} cards")
