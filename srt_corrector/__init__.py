"""Core package for correcting SRT subtitle files against reference text."""

from .models import SRTEntry
from .parsing import parse_srt, write_srt
from .matching import (
    normalize_for_matching,
    find_by_sliding_window,
    find_text_in_reference,
    map_normalized_to_original,
    extract_corrected_text,
)
from .corrector import (
    correct_srt_entries,
    show_statistics,
    show_comparison_examples,
)

__all__ = [
    "SRTEntry",
    "parse_srt",
    "write_srt",
    "normalize_for_matching",
    "find_by_sliding_window",
    "find_text_in_reference",
    "map_normalized_to_original",
    "extract_corrected_text",
    "correct_srt_entries",
    "show_statistics",
    "show_comparison_examples",
]
