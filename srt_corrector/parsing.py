import re
from typing import List

from .models import SRTEntry


def parse_srt(srt_path: str) -> List[SRTEntry]:
    """Parse an SRT file into a list of entries."""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    entries: List[SRTEntry] = []
    pattern = (
        r"(\d+)\n"
        r"(\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3})\n"
        r"((?:.*\n)*?)(?=\n\d+\n|\Z)"
    )

    for match in re.finditer(pattern, content, re.MULTILINE):
        entries.append(
            SRTEntry(
                int(match.group(1)),
                match.group(2),
                match.group(3).strip(),
            )
        )

    return entries


def write_srt(entries: List[SRTEntry], output_path: str):
    """Write SRT entries back to disk."""
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(str(entry))
            f.write("\n")
