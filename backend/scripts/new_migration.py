#!/usr/bin/env python3
"""Generate a new Alembic migration and commit it.

This repo hand-authors migration bodies (see documentation/database-schema.md
and 0001_initial_schema.py's enum-handling comments) rather than using
--autogenerate, and uses sequential revision ids ("0001", "0002", ...)
instead of Alembic's default random hash -- this fills in --rev-id with
the next one so every generated file matches that convention without
having to compute it by hand.

Usage: pnpm migrate:gen -m "add foo column"
"""

import argparse
import re
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
VERSIONS_DIR = BACKEND_DIR / "alembic" / "versions"


def next_revision_id() -> str:
    existing = [
        int(match.group(1))
        for path in VERSIONS_DIR.glob("*.py")
        if (match := re.match(r"(\d+)_", path.name))
    ]
    return f"{max(existing, default=0) + 1:04d}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-m", "--message", required=True, help="Migration description")
    args = parser.parse_args()

    rev_id = next_revision_id()
    before = set(VERSIONS_DIR.glob("*.py"))

    subprocess.run(
        ["alembic", "revision", "--rev-id", rev_id, "-m", args.message],
        cwd=BACKEND_DIR,
        check=True,
    )

    [new_file] = set(VERSIONS_DIR.glob("*.py")) - before
    relative_path = new_file.relative_to(REPO_ROOT)

    # The mako template's repr() emits single-quoted strings; normalize to
    # this repo's double-quoted style so generated files don't stand out
    # from hand-written ones.
    subprocess.run(["ruff", "format", str(new_file)], cwd=BACKEND_DIR, check=True)

    subprocess.run(["git", "add", str(relative_path)], cwd=REPO_ROOT, check=True)
    subprocess.run(["git", "commit", "-m", args.message], cwd=REPO_ROOT, check=True)

    print(f"Created and committed {relative_path} -- fill in upgrade()/downgrade() next.")


if __name__ == "__main__":
    main()
