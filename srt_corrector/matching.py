import re
from difflib import SequenceMatcher
from typing import Tuple


def normalize_for_matching(text: str) -> str:
    """Normalize text for matching (letters, digits, and spaces only)."""
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def find_by_sliding_window(
    srt_normalized: str, search_region: str, fuzzy_threshold: float = 0.80
) -> Tuple[int, float]:
    """
    Sliding-window fuzzy match when exact matching fails.

    Returns (position, score).
    """
    srt_len = len(srt_normalized)

    if srt_len == 0 or len(search_region) < srt_len:
        return -1, 0.0

    best_score = 0.0
    best_pos = -1
    step = max(1, srt_len // 10)

    if srt_len < 50:
        window_size = int(srt_len * 1.2)
    else:
        window_size = int(srt_len * 1.15)

    for i in range(0, len(search_region) - srt_len + 1, step):
        window = search_region[i : i + window_size]
        score = SequenceMatcher(None, srt_normalized, window).ratio()

        if score > best_score:
            best_score = score
            best_pos = i

            if score >= 0.95:
                return best_pos, best_score

    if best_score >= fuzzy_threshold:
        return best_pos, best_score

    return -1, 0.0


def find_text_in_reference(
    srt_text: str, reference_text: str, start_hint: int = 0, use_fuzzy: bool = True
) -> Tuple[int, int, float, str]:
    """
    Find SRT text inside reference text using layered matching.

    Returns (start, end, score, method).
    """
    srt_normalized = normalize_for_matching(srt_text)
    ref_normalized = normalize_for_matching(reference_text)

    if not srt_normalized:
        return -1, -1, 0.0, "none"

    srt_words = srt_normalized.split()
    if len(srt_words) == 0:
        return -1, -1, 0.0, "none"

    if len(srt_normalized) < 20:
        search_start = max(0, start_hint - 50)
        search_end = min(len(ref_normalized), start_hint + 200)
    else:
        search_start = max(0, start_hint - 100)
        search_end = min(len(ref_normalized), start_hint + 500)

    search_region = ref_normalized[search_start:search_end]

    num_anchor_words = min(5, max(2, len(srt_words) // 3))
    start_anchor = " ".join(srt_words[:num_anchor_words])
    end_anchor = (
        " ".join(srt_words[-num_anchor_words:])
        if len(srt_words) > num_anchor_words
        else start_anchor
    )

    if num_anchor_words <= 3:
        all_positions = []
        pos = 0
        while True:
            pos = search_region.find(start_anchor, pos)
            if pos == -1:
                break
            all_positions.append(pos)
            pos += 1

        if len(all_positions) == 0:
            start_pos = -1
        elif len(all_positions) == 1:
            start_pos = all_positions[0]
        else:
            best_score = 0
            best_pos = all_positions[0]
            compare_len = (
                max(len(srt_normalized), 50)
                if len(srt_normalized) < 10
                else len(srt_normalized)
            )

            for pos in all_positions:
                test_start = search_start + pos
                test_end = min(test_start + compare_len, len(ref_normalized))
                test_text = ref_normalized[test_start:test_end]
                score = SequenceMatcher(None, srt_normalized, test_text).ratio()

                if score > best_score + 0.01:
                    best_score = score
                    best_pos = pos
                elif abs(score - best_score) <= 0.01:
                    current_distance = abs(test_start - start_hint)
                    best_distance = abs(search_start + best_pos - start_hint)
                    if current_distance < best_distance:
                        best_score = score
                        best_pos = pos

            start_pos = best_pos
    else:
        start_pos = search_region.find(start_anchor)

    method = "exact"

    if start_pos == -1:
        start_anchor = " ".join(srt_words[:2])
        all_positions = []
        pos = 0
        while True:
            pos = search_region.find(start_anchor, pos)
            if pos == -1:
                break
            all_positions.append(pos)
            pos += 1

        if len(all_positions) > 0:
            if len(all_positions) == 1:
                start_pos = all_positions[0]
            else:
                best_score = 0
                best_pos = all_positions[0]
                compare_len = (
                    max(len(srt_normalized), 50)
                    if len(srt_normalized) < 10
                    else len(srt_normalized)
                )

                for pos in all_positions:
                    test_start = search_start + pos
                    test_end = min(test_start + compare_len, len(ref_normalized))
                    test_text = ref_normalized[test_start:test_end]
                    score = SequenceMatcher(None, srt_normalized, test_text).ratio()

                    if score > best_score + 0.01:
                        best_score = score
                        best_pos = pos
                    elif abs(score - best_score) <= 0.01:
                        current_distance = abs(test_start - start_hint)
                        best_distance = abs(search_start + best_pos - start_hint)
                        if current_distance < best_distance:
                            best_score = score
                            best_pos = pos

                start_pos = best_pos

            method = "short"

    if start_pos == -1 and use_fuzzy:
        fuzzy_pos, fuzzy_score = find_by_sliding_window(
            srt_normalized, search_region, fuzzy_threshold=0.80
        )

        if fuzzy_pos != -1:
            method = "fuzzy"
            abs_start = search_start + fuzzy_pos
            best_ratio = 0
            best_start = abs_start
            best_end = abs_start + len(srt_normalized)

            search_window_start = max(abs_start - 30, search_start)
            search_window_end = min(abs_start + 60, search_start + len(search_region))

            for test_start in range(search_window_start, search_window_end):
                min_len = int(len(srt_normalized) * 0.9)
                max_len = int(len(srt_normalized) * 1.1)

                for test_len in range(
                    min_len, min(max_len + 1, len(ref_normalized) - test_start + 1)
                ):
                    test_end = test_start + test_len
                    if test_end > len(ref_normalized):
                        break

                    test_text = ref_normalized[test_start:test_end]
                    ratio = SequenceMatcher(None, srt_normalized, test_text).ratio()
                    at_word_boundary = test_start == 0 or ref_normalized[
                        test_start - 1
                    ].isspace()

                    if at_word_boundary:
                        ratio += 0.02

                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_start = test_start
                        best_end = test_end

            return best_start, best_end, best_ratio, method

    if start_pos == -1:
        return -1, -1, 0.0, "none"

    abs_start = search_start + start_pos
    max_search_length = len(srt_normalized) * 3
    end_search_region = ref_normalized[abs_start : abs_start + max_search_length]

    end_pos = end_search_region.find(end_anchor)
    if end_pos == -1:
        best_ratio = 0
        best_end = abs_start + len(srt_normalized)
        min_len = int(len(srt_normalized) * 0.8)
        max_len = int(len(srt_normalized) * 1.5)

        for test_len in range(
            min_len, min(max_len, len(ref_normalized) - abs_start)
        ):
            test_text = ref_normalized[abs_start : abs_start + test_len]
            ratio = SequenceMatcher(None, srt_normalized, test_text).ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_end = abs_start + test_len

        abs_end = best_end
    else:
        abs_end = abs_start + end_pos + len(end_anchor)

    matched_text = ref_normalized[abs_start:abs_end]
    score = SequenceMatcher(None, srt_normalized, matched_text).ratio()

    return abs_start, abs_end, score, method


def map_normalized_to_original(
    norm_start: int, norm_end: int, reference_text: str
) -> Tuple[int, int]:
    """
    Map normalized text positions back to original text positions.
    Preserves punctuation and quotes in the returned range.
    """
    ref_normalized = normalize_for_matching(reference_text)
    norm_to_orig = []
    norm_idx = 0

    for orig_idx, char in enumerate(reference_text):
        if char.isalnum():
            if norm_idx < len(ref_normalized) and char.lower() == ref_normalized[norm_idx]:
                norm_to_orig.append(orig_idx)
                norm_idx += 1
        elif char.isspace():
            if norm_idx < len(ref_normalized) and ref_normalized[norm_idx] == " ":
                norm_to_orig.append(orig_idx)
                norm_idx += 1

    if norm_start >= len(norm_to_orig) or norm_end > len(norm_to_orig):
        return -1, -1

    orig_start = norm_to_orig[norm_start]
    orig_end = norm_to_orig[norm_end - 1] if norm_end > 0 else norm_to_orig[0]

    while orig_start > 0 and reference_text[orig_start - 1].isalnum():
        orig_start -= 1

    while orig_end > orig_start and reference_text[orig_end].isspace():
        orig_end -= 1

    if reference_text[orig_end].isalnum():
        while orig_end < len(reference_text) - 1 and reference_text[
            orig_end + 1
        ].isalnum():
            orig_end += 1

    sentence_terminators = ".!?:;"
    closing_quotes = '"\u201d\u2019'
    other_punct = ",—–-\u201c\u2018'"

    while orig_end < len(reference_text) - 1:
        next_char = reference_text[orig_end + 1]

        if next_char in sentence_terminators:
            orig_end += 1
            if orig_end < len(reference_text) - 1:
                after_terminator = reference_text[orig_end + 1]
                if after_terminator in closing_quotes:
                    orig_end += 1
            break
        elif next_char in closing_quotes:
            orig_end += 1
            if orig_end < len(reference_text) - 1:
                after_quote = reference_text[orig_end + 1]
                if after_quote in sentence_terminators:
                    orig_end += 1
            break
        elif next_char in other_punct:
            orig_end += 1
        elif next_char.isspace():
            break
        else:
            break

    quote_chars = '"\'\u201c\u201d\u2018\u2019'
    while orig_start > 0:
        prev_char = reference_text[orig_start - 1]
        if prev_char in quote_chars:
            orig_start -= 1
        else:
            break

    return orig_start, orig_end + 1


def extract_corrected_text(reference_text: str, norm_start: int, norm_end: int) -> str:
    """Extract corrected text from the reference string, preserving punctuation."""
    orig_start, orig_end = map_normalized_to_original(
        norm_start, norm_end, reference_text
    )

    if orig_start == -1:
        return ""

    extracted = reference_text[orig_start:orig_end].strip()
    extracted = re.sub(r"\n\n+", "\n", extracted)

    return extracted
