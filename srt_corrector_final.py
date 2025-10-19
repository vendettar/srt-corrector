#!/usr/bin/env python3
"""
SRT文本修正工具 - 最终版本
完整保留TXT原文的所有标点符号和格式
"""

import re
from typing import List, Tuple
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


def find_text_in_reference(srt_text: str, reference_text: str, start_hint: int = 0) -> Tuple[int, int, float]:
    """
    在参考文本中找到SRT文本的位置
    使用标准化文本进行匹配，但返回原始位置
    """
    srt_normalized = normalize_for_matching(srt_text)
    ref_normalized = normalize_for_matching(reference_text)

    if not srt_normalized:
        return -1, -1, 0.0

    srt_words = srt_normalized.split()
    if len(srt_words) == 0:
        return -1, -1, 0.0

    # 使用首尾词作为锚点
    num_anchor_words = min(5, max(2, len(srt_words) // 3))
    start_anchor = ' '.join(srt_words[:num_anchor_words])
    end_anchor = ' '.join(srt_words[-num_anchor_words:]) if len(srt_words) > num_anchor_words else start_anchor

    # 在参考文本中搜索
    search_start = max(0, start_hint - 1000)
    search_end = min(len(ref_normalized), start_hint + 6000)
    search_region = ref_normalized[search_start:search_end]

    # 查找起始锚点
    start_pos = search_region.find(start_anchor)
    if start_pos == -1:
        # 尝试更短的锚点
        start_anchor = ' '.join(srt_words[:2])
        start_pos = search_region.find(start_anchor)

    if start_pos == -1:
        return -1, -1, 0.0

    # 计算绝对位置
    abs_start = search_start + start_pos

    # 查找结束锚点
    max_search_length = len(srt_normalized) * 3
    end_search_region = ref_normalized[abs_start:abs_start + max_search_length]

    end_pos = end_search_region.find(end_anchor)
    if end_pos == -1:
        abs_end = abs_start + len(srt_normalized)
    else:
        abs_end = abs_start + end_pos + len(end_anchor)

    # 计算匹配分数
    matched_text = ref_normalized[abs_start:abs_end]
    score = SequenceMatcher(None, srt_normalized, matched_text).ratio()

    return abs_start, abs_end, score


def map_normalized_to_original(norm_start: int, norm_end: int,
                               reference_text: str) -> Tuple[int, int]:
    """
    将标准化文本位置映射回原始文本位置
    完整保留原文的所有字符（包括标点符号、引号、破折号等）
    """
    ref_normalized = normalize_for_matching(reference_text)

    # 建立映射：标准化位置 -> 原始位置
    norm_to_orig = []
    norm_idx = 0

    for orig_idx, char in enumerate(reference_text):
        if char.isalnum():
            # 字母数字字符
            if norm_idx < len(ref_normalized) and char.lower() == ref_normalized[norm_idx]:
                norm_to_orig.append(orig_idx)
                norm_idx += 1
        elif char.isspace():
            # 空格字符
            if norm_idx < len(ref_normalized) and ref_normalized[norm_idx] == ' ':
                norm_to_orig.append(orig_idx)
                norm_idx += 1

    # 获取边界
    if norm_start >= len(norm_to_orig) or norm_end > len(norm_to_orig):
        return -1, -1

    orig_start = norm_to_orig[norm_start]
    orig_end = norm_to_orig[norm_end - 1] if norm_end > 0 else norm_to_orig[0]

    # 向前扩展到单词边界（但不包括前面的标点）
    # 只向前扩展字母数字字符
    while orig_start > 0 and reference_text[orig_start - 1].isalnum():
        orig_start -= 1

    # 向后扩展到单词边界并包含紧随的标点符号
    # 首先扩展字母数字
    while orig_end < len(reference_text) - 1 and reference_text[orig_end + 1].isalnum():
        orig_end += 1

    # 然后包含紧随的标点符号（引号、句号、逗号、冒号、破折号等）
    # 这些是原文本的一部分，应该被保留
    punctuation_chars = '.,;:!?\'"—–-\u201c\u201d\u2018\u2019'
    while orig_end < len(reference_text) - 1:
        next_char = reference_text[orig_end + 1]
        # 包含常见的标点符号（包括Unicode引号和破折号）
        if next_char in punctuation_chars:
            orig_end += 1
        else:
            break

    # 向前包含开头的引号（如果存在）
    # 包含所有类型的引号：ASCII引号和Unicode引号
    quote_chars = '"\'""''\u201c\u201d\u2018\u2019'
    while orig_start > 0:
        prev_char = reference_text[orig_start - 1]
        if prev_char in quote_chars:  # ASCII + Unicode引号
            orig_start -= 1
        else:
            break

    return orig_start, orig_end + 1


def extract_corrected_text(reference_text: str, norm_start: int, norm_end: int) -> str:
    """从参考文本中提取修正后的文本，完整保留所有标点"""
    orig_start, orig_end = map_normalized_to_original(norm_start, norm_end, reference_text)

    if orig_start == -1:
        return ""

    extracted = reference_text[orig_start:orig_end]

    # 只修剪前后的空白字符，保留所有标点符号
    extracted = extracted.strip()

    return extracted


def correct_srt_entries(srt_entries: List[SRTEntry],
                       reference_text: str,
                       confidence_threshold: float = 0.65) -> List[SRTEntry]:
    """修正所有SRT条目"""
    print(f"\n开始修正字幕...")
    print(f"匹配阈值: {confidence_threshold}")

    corrected_count = 0
    ref_position_hint = 0

    for i, entry in enumerate(srt_entries):
        if (i + 1) % 10 == 0:
            print(f"进度: {i+1}/{len(srt_entries)} ({100*(i+1)//len(srt_entries)}%)", end='\r')

        # 在参考文本中查找
        norm_start, norm_end, score = find_text_in_reference(
            entry.text,
            reference_text,
            ref_position_hint
        )

        if score >= confidence_threshold and norm_start != -1:
            # 提取修正后的文本
            corrected = extract_corrected_text(reference_text, norm_start, norm_end)

            if corrected and len(corrected.strip()) > 0:
                entry.text = corrected
                ref_position_hint = norm_end
                corrected_count += 1

                # 显示前10个修正的例子
                if i < 10 and entry.text != entry.original_text:
                    print(f"\n\n字幕 #{entry.index}:")
                    print(f"  原文: {entry.original_text[:70]}...")
                    print(f"  修正: {entry.text[:70]}...")
                    print(f"  置信度: {score:.2%}")

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


def main(srt_path: str, txt_path: str, output_path: str = None, threshold: float = 0.65):
    """主函数"""
    if output_path is None:
        output_path = srt_path.replace('.srt', '_corrected_final.srt')

    print("=" * 80)
    print("SRT 文本修正工具 - 最终版本".center(80))
    print("完整保留TXT原文的所有标点符号和格式".center(80))
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
    corrected_entries = correct_srt_entries(srt_entries, reference_text, threshold)

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
        print("用法: python srt_corrector_final.py <srt文件> <txt文件> [输出文件] [阈值]")
        print("\n参数说明:")
        print("  srt文件   - 需要修正的SRT字幕文件")
        print("  txt文件   - 准确的参考文本文件")
        print("  输出文件  - 可选，默认为原文件名_corrected_final.srt")
        print("  阈值      - 可选，匹配置信度阈值(0.0-1.0)，默认0.65")
        print("\n示例:")
        print("  python srt_corrector_final.py 'audio.srt' 'reference.txt'")
        print("  python srt_corrector_final.py 'audio.srt' 'reference.txt' 'output.srt' 0.7")
        sys.exit(1)

    srt_file = sys.argv[1]
    txt_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 0.65

    main(srt_file, txt_file, output_file, threshold)
