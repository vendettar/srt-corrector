from typing import List

from .matching import extract_corrected_text, find_text_in_reference
from .models import SRTEntry


def correct_srt_entries(
    srt_entries: List[SRTEntry],
    reference_text: str,
    confidence_threshold: float = 0.65,
    use_fuzzy: bool = True,
) -> List[SRTEntry]:
    """Correct all SRT entries using the reference text."""
    print("\n开始修正字幕...")
    print(f"匹配阈值: {confidence_threshold}")
    print(f"模糊匹配: {'启用' if use_fuzzy else '禁用'}")

    corrected_count = 0
    fuzzy_count = 0
    ref_position_hint = 0

    for i, entry in enumerate(srt_entries):
        if (i + 1) % 10 == 0:
            print(
                f"进度: {i+1}/{len(srt_entries)} "
                f"({100*(i+1)//len(srt_entries)}%)",
                end="\r",
            )

        norm_start, norm_end, score, method = find_text_in_reference(
            entry.text, reference_text, ref_position_hint, use_fuzzy=use_fuzzy
        )

        if score >= confidence_threshold and norm_start != -1:
            corrected = extract_corrected_text(reference_text, norm_start, norm_end)

            if corrected and len(corrected.strip()) > 0:
                entry.text = corrected
                ref_position_hint = norm_end
                corrected_count += 1

                if method == "fuzzy":
                    fuzzy_count += 1

                if method == "fuzzy" and entry.text != entry.original_text:
                    print(f"\n\n🔍 模糊匹配成功 - 字幕 #{entry.index}:")
                    print(f"  原文: {entry.original_text[:70]}")
                    print(f"  修正: {entry.text[:70]}")
                    print(f"  置信度: {score:.2%}")

    print(f"\n\n修正完成: {corrected_count}/{len(srt_entries)} 条字幕被修正")
    if use_fuzzy and fuzzy_count > 0:
        print(f"  其中 {fuzzy_count} 条通过模糊匹配修正")

    return srt_entries


def show_statistics(entries: List[SRTEntry]):
    """Display simple correction statistics."""
    changed_count = sum(1 for e in entries if e.text != e.original_text)
    print("\n统计信息:")
    print(f"  总字幕数: {len(entries)}")
    print(f"  已修正: {changed_count}")
    print(f"  未修正: {len(entries) - changed_count}")
    print(f"  修正率: {100*changed_count/len(entries):.1f}%")


def show_comparison_examples(entries: List[SRTEntry], num_examples: int = 5):
    """Print examples of corrected entries."""
    print(f"\n修正示例（前{num_examples}个有变化的条目）:")
    print("=" * 80)

    count = 0
    for entry in entries:
        if entry.text != entry.original_text and count < num_examples:
            count += 1
            print(f"\n[字幕 #{entry.index}]")
            print(f"原文: {entry.original_text}")
            print(f"修正: {entry.text}")
            print("-" * 80)
