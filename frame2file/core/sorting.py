from __future__ import annotations

import re
from pathlib import Path


def natural_key(path: Path) -> list[int | str]:
    """Sort paths in human order, e.g. frame2 before frame10."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]

