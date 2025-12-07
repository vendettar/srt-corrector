from dataclasses import dataclass
from typing import Optional


@dataclass
class SRTEntry:
    """Single SRT subtitle entry."""

    index: int
    timestamp: str
    text: str
    original_text: Optional[str] = None

    def __post_init__(self):
        if self.original_text is None:
            self.original_text = self.text

    def __str__(self) -> str:
        return f"{self.index}\n{self.timestamp}\n{self.text}\n"
