"""Build bilingual GitHub release notes from CHANGELOG.md and CHANGELOG.de.md.

Usage:
    python dev/release_notes.py 0.8.1            # print the notes for one version
    python dev/release_notes.py 0.8.1 --apply    # also update the GitHub release (needs gh)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "berwil84afk/ha-level-watch"


def section(path: Path, version: str) -> str:
    """The body of one version's section, with its headings one level lower."""
    text = path.read_text(encoding="utf-8")
    match = re.search(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|^\[[^\]]+\]: |\Z)",
        text,
        flags=re.S | re.M,
    )
    if not match:
        raise SystemExit(f"{version} not found in {path.name}")
    return match.group(1).strip().replace("\n### ", "\n#### ").replace("### ", "#### ", 1)


def notes(version: str) -> str:
    en = section(ROOT / "CHANGELOG.md", version)
    de = section(ROOT / "CHANGELOG.de.md", version)
    base = f"https://github.com/{REPO}/blob/main"
    return (
        f"### English\n\n{en}\n\n"
        f"### Deutsch\n\n{de}\n\n"
        f"---\n[Changelog]({base}/CHANGELOG.md) · [Änderungsprotokoll]({base}/CHANGELOG.de.md)\n"
    )


def main() -> None:
    version = sys.argv[1].lstrip("v")
    body = notes(version)
    print(body)
    if "--apply" in sys.argv:
        subprocess.run(
            ["gh", "release", "edit", f"v{version}", "--repo", REPO, "--notes-file", "-"],
            input=body.encode("utf-8"),
            check=True,
        )


if __name__ == "__main__":
    main()
