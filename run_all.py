#!/usr/bin/env python3
"""Run every top-level build script for the UBC IAA pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_SCRIPTS = [
    "build_anki_deck.py",
    "generate_project_status.py",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all Python build scripts in the UBC IAA pipeline."
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="keep running later scripts after one script fails",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable to use for each script (default: current Python)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures = []

    for index, script_name in enumerate(DEFAULT_SCRIPTS, start=1):
        script_path = REPO_ROOT / script_name
        if not script_path.exists():
            failures.append((script_name, "missing"))
            print(
                f"[{index}/{len(DEFAULT_SCRIPTS)}] Missing {script_name}",
                file=sys.stderr,
                flush=True,
            )
            if not args.continue_on_error:
                break
            continue

        print(f"\n[{index}/{len(DEFAULT_SCRIPTS)}] Running {script_name}", flush=True)
        result = subprocess.run([args.python, str(script_path)], cwd=REPO_ROOT)
        if result.returncode != 0:
            failures.append((script_name, result.returncode))
            print(
                f"{script_name} failed with exit code {result.returncode}",
                file=sys.stderr,
                flush=True,
            )
            if not args.continue_on_error:
                break

    if failures:
        print("\nFailed script(s):", file=sys.stderr, flush=True)
        for script_name, reason in failures:
            print(f"- {script_name}: {reason}", file=sys.stderr, flush=True)
        return 1

    print("\nAll Python build scripts completed successfully.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
