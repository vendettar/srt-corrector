#!/usr/bin/env python3
"""
SRT文本修正工具 - 严格位置匹配版本
基于用户建议：更严格地利用SRT和TXT的相对位置关系
"""

import re
from typing import List, Tuple, Optional
from difflib import SequenceMatcher


class SRTEntry:
    """SRT字幕条目"""
    def __init__(self, index: int, timestamp: str, text: str):
        self.index = index
        self.timestamp = timestamp
        self.text = text
        self.original_text = text

    def __str__(self):
        return f"{self.index}\n{self.timestamp}\n{self.text}\n"


def parse_srt(srt_path: str) -> List[SRTEntry]:
    """解析SRT文件"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = []
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3})\n((?:.*\n)*?)(?=\n\d+\n|\Z)'

    for match in re.finditer(pattern, content, re.MULTILINE):
        entries.append(SRTEntry(
            int(match.group(1)),
            match.group(2),
            match.group(3).strip()
        ))

    return entries


def normalize_for_matching(text: str) -> str:
    """标准化文本用于匹配（只保留字母数字和空格）"""
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()


def find_best_match_strict(srt_text: str, reference_text: str,
                           start_pos: int, max_search_window: int = 3000) -> Tuple[int, int, float]:
    """
    严格的位置匹配策略：
    1. 优先在start_pos附近的小窗口内搜索
    2. 如果找不到，才扩大搜索范围
    3. 总是返回最佳匹配（即使分数不高）
    """
    srt_normalized = normalize_for_matching(srt_text)
    ref_normalized = normalize_for_matching(reference_text)

    if not srt_normalized:
        return -1, -1, 0.0

    # 策略1: 在小窗口内精确搜索（假设顺序严格）
    window_size = 1000
    search_start = max(0, start_pos - 100)
    search_end = min(len(ref_normalized), start_pos + window_size)

    best_score = 0.0
    best_start = -1
    best_end = -1

    # 尝试精确查找
    srt_words = srt_normalized.split()
    if len(srt_words) >= 3:
        # 使用前3个词作为锚点
        anchor = ' '.join(srt_words[:3])
        anchor_pos = ref_normalized[search_start:search_end].find(anchor)

        if anchor_pos != -1:
            abs_pos = search_start + anchor_pos
            # 向后扩展
            end_pos = abs_pos + len(srt_normalized) * 2
            matched_text = ref_normalized[abs_pos:end_pos]

            # 使用模糊匹配找到最佳结束位置
            best_ratio = 0
            best_end_offset = len(srt_normalized)

            for offset in range(len(srt_normalized) - 10, len(srt_normalized) * 2):
                if abs_pos + offset > len(ref_normalized):
                    break
                candidate = ref_normalized[abs_pos:abs_pos + offset]
                ratio = SequenceMatcher(None, srt_normalized, candidate).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_end_offset = offset

            return abs_pos, abs_pos + best_end_offset, best_ratio

    # 策略2: 如果精确查找失败，扩大窗口
    search_end = min(len(ref_normalized), start_pos + max_search_window)

    # 滑动窗口搜索
    search_region = ref_normalized[search_start:search_end]

    # 使用首尾词作为锚点
    num_anchor_words = min(5, max(2, len(srt_words) // 3))
    start_anchor = ' '.join(srt_words[:num_anchor_words])

    start_pos_in_region = search_region.find(start_anchor)

    if start_pos_in_region != -1:
        abs_start = search_start + start_pos_in_region

        # 尝试不同的结束位置，找到最佳匹配
        best_score = 0
        best_end = abs_start + len(srt_normalized)

        for length in range(len(srt_normalized) - 20, len(srt_normalized) * 2, 5):
            if abs_start + length > len(ref_normalized):
                break

            candidate = ref_normalized[abs_start:abs_start + length]
            score = SequenceMatcher(None, srt_normalized, candidate).ratio()

            if score > best_score:
                best_score = score
                best_end = abs_start + length

        return abs_start, best_end, best_score

    return -1, -1, 0.0


def map_normalized_to_original(norm_start: int, norm_end: int,
                               reference_text: str) -> Tuple[int, int]:
    """将标准化文本位置映射回原始文本位置"""
    ref_normalized = normalize_for_matching(reference_text)

    norm_to_orig = []
    norm_idx = 0

    for orig_idx, char in enumerate(reference_text):
        if char.isalnum():
            if norm_idx < len(ref_normalized) and char.lower() == ref_normalized[norm_idx]:
                norm_to_orig.append(orig_idx)
                norm_idx += 1
        elif char.isspace():
            if norm_idx < len(ref_normalized) and ref_normalized[norm_idx] == ' ':
                norm_to_orig.append(orig_idx)
                norm_idx += 1

    if norm_start >= len(norm_to_orig) or norm_end > len(norm_to_orig):
        return -1, -1

    orig_start = norm_to_orig[norm_start]
    orig_end = norm_to_orig[norm_end - 1] if norm_end > 0 else norm_to_orig[0]

    while orig_start > 0 and reference_text[orig_start - 1].isalnum():
        orig_start -= 1

    while orig_end < len(reference_text) - 1 and reference_text[orig_end + 1].isalnum():
        orig_end += 1

    punctuation_chars = '.,;:!?\'"—–-\u201c\u201d\u2018\u2019'
    while orig_end < len(reference_text) - 1:
        next_char = reference_text[orig_end + 1]
        if next_char in punctuation_chars:
            orig_end += 1
        else:
            break

    quote_chars = '"\'""''\u201c\u201d\u2018\u2019'
    while orig_start > 0:
        prev_char = reference_text[orig_start - 1]
        if prev_char in quote_chars:
            orig_start -= 1
        else:
            break

    return orig_start, orig_end + 1


def extract_corrected_text(reference_text: str, norm_start: int, norm_end: int) -> str:
    """从参考文本中提取修正后的文本"""
    orig_start, orig_end = map_normalized_to_original(norm_start, norm_end, reference_text)

    if orig_start == -1:
        return ""

    extracted = reference_text[orig_start:orig_end]
    extracted = extracted.strip()

    return extracted


def correct_srt_entries_strict(srt_entries: List[SRTEntry],
                               reference_text: str,
                               min_confidence: float = 0.50) -> List[SRTEntry]:
    """
    严格的修正策略：
    1. 强制按顺序匹配
    2. 降低置信度阈值（因为我们依赖位置）
    3. 总是尝试修正（即使置信度不高也会修正，除非完全匹配失败）
    """
    print(f"\n开始修正字幕（严格位置匹配模式）...")
    print(f"最低置信度阈值: {min_confidence}")

    corrected_count = 0
    ref_position = 0

    for i, entry in enumerate(srt_entries):
        if (i + 1) % 10 == 0:
            print(f"进度: {i+1}/{len(srt_entries)} ({100*(i+1)//len(srt_entries)}%)", end='\r')

        # 使用严格的位置匹配
        norm_start, norm_end, score = find_best_match_strict(
            entry.text,
            reference_text,
            ref_position
        )

        # 显示详细信息（前10条）
        if i < 10:
            print(f"\n\n字幕 #{entry.index}:")
            print(f"  SRT文本: {entry.original_text[:60]}...")
            print(f"  搜索起点: {ref_position}")
            print(f"  找到位置: {norm_start} ~ {norm_end}")
            print(f"  置信度: {score:.2%}")

        if score >= min_confidence and norm_start != -1:
            corrected = extract_corrected_text(reference_text, norm_start, norm_end)

            if corrected and len(corrected.strip()) > 0:
                if i < 10:
                    print(f"  修正文本: {corrected[:60]}...")

                entry.text = corrected
                ref_position = norm_end
                corrected_count += 1
            else:
                if i < 10:
                    print(f"  ❌ 提取失败，保持原文")
        else:
            if i < 10:
                print(f"  ❌ 置信度太低或未找到，保持原文")

    print(f"\n\n修正完成: {corrected_count}/{len(srt_entries)} 条字幕被修正")
    return srt_entries


def write_srt(entries: List[SRTEntry], output_path: str):
    """写入SRT文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(str(entry))
            f.write('\n')


def show_statistics(entries: List[SRTEntry]):
    """显示统计信息"""
    changed_count = sum(1 for e in entries if e.text != e.original_text)
    print(f"\n统计信息:")
    print(f"  总字幕数: {len(entries)}")
    print(f"  已修正: {changed_count}")
    print(f"  未修正: {len(entries) - changed_count}")
    print(f"  修正率: {100*changed_count/len(entries):.1f}%")


def show_comparison_examples(entries: List[SRTEntry], num_examples: int = 5):
    """显示修正前后的对比示例"""
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


def main(srt_path: str, txt_path: str, output_path: str = None, threshold: float = 0.50):
    """主函数"""
    if output_path is None:
        output_path = srt_path.replace('.srt', '_corrected_strict.srt')

    print("=" * 80)
    print("SRT 文本修正工具 - 严格位置匹配版本".center(80))
    print("基于相对位置关系的强制顺序匹配".center(80))
    print("=" * 80)

    # 1. 读取SRT
    print(f"\n[1/4] 读取SRT文件...")
    print(f"      路径: {srt_path}")
    srt_entries = parse_srt(srt_path)
    print(f"      ✓ 读取 {len(srt_entries)} 条字幕")

    # 2. 读取参考文本
    print(f"\n[2/4] 读取参考文本...")
    print(f"      路径: {txt_path}")
    with open(txt_path, 'r', encoding='utf-8') as f:
        reference_text = f.read()
    print(f"      ✓ 读取 {len(reference_text):,} 字符")

    # 3. 执行修正
    print(f"\n[3/4] 执行文本修正...")
    corrected_entries = correct_srt_entries_strict(srt_entries, reference_text, threshold)

    # 4. 保存结果
    print(f"\n[4/4] 保存修正结果...")
    print(f"      路径: {output_path}")
    write_srt(corrected_entries, output_path)
    print(f"      ✓ 保存成功")

    # 显示统计和示例
    show_statistics(corrected_entries)
    show_comparison_examples(corrected_entries, num_examples=8)

    print("\n" + "=" * 80)
    print("✓ 全部完成！".center(80))
    print("=" * 80)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python srt_corrector_strict.py <srt文件> <txt文件> [输出文件] [最低阈值]")
        print("\n参数说明:")
        print("  srt文件   - 需要修正的SRT字幕文件")
        print("  txt文件   - 准确的参考文本文件")
        print("  输出文件  - 可选，默认为原文件名_corrected_strict.srt")
        print("  最低阈值  - 可选，最低置信度阈值(0.0-1.0)，默认0.50（比标准版更宽松）")
        print("\n与标准版的区别:")
        print("  - 更严格地依赖相对位置关系")
        print("  - 降低了置信度要求（默认0.50 vs 0.65）")
        print("  - 强制按顺序匹配")
        print("  - 即使置信度不高也会尝试修正")
        print("\n示例:")
        print("  python srt_corrector_strict.py 'audio.srt' 'reference.txt'")
        sys.exit(1)

    srt_file = sys.argv[1]
    txt_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 0.50

    main(srt_file, txt_file, output_file, threshold)
