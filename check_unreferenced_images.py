#!/usr/bin/env python3
"""Report atlas images that have no matching workbook file-name entry."""

from pathlib import Path
import re

from build_anki_deck import (
    IMAGE_EXTS,
    image_dir_for_workbook,
    is_archived,
    SOURCE_ROOT,
    value,
    workbook_rows,
)


def content_workbooks_recursive():
    """Find workbooks below drive folders, including nested copied drives."""
    return sorted(
        path
        for path in SOURCE_ROOT.rglob("*_content.xlsx")
        if not path.name.startswith("~$")
        and not is_archived(path)
        and any(
            parent.name.casefold().endswith(" drive")
            for parent in path.parents
        )
    )


def key(text):
    stem = Path(text.strip()).stem
    return re.sub(r"_p$", "", stem, flags=re.IGNORECASE).casefold()


def referenced_keys(workbook):
    return {
        key(value(row, headers, "file_name", "file name"))
        for _sheet, _row_number, headers, row in workbook_rows(workbook)
        if value(row, headers, "file_name", "file name")
    }


def image_matches_reference(path, references):
    image_key = key(path.name)
    if image_key in references:
        return True

    # Variant images such as structure_1.jpg correspond to the structure row.
    variant_key = re.sub(r"_[^_]+$", "", image_key)
    return variant_key in references


def main():
    total_images = 0
    unmatched = []

    for workbook in content_workbooks_recursive():
        image_root = image_dir_for_workbook(workbook)
        references = referenced_keys(workbook)
        images = [
            path
            for path in sorted(image_root.rglob("*"))
            if path.is_file()
            and not is_archived(path)
            and path.suffix.casefold() in IMAGE_EXTS
        ]
        total_images += len(images)
        unmatched.extend(
            (workbook, path)
            for path in images
            if not image_matches_reference(path, references)
        )

    print(f"Images checked: {total_images}")
    print(f"Images without workbook info: {len(unmatched)}")
    for workbook, path in unmatched:
        print(f"{workbook}: {path}")


if __name__ == "__main__":
    main()
