#!/usr/bin/env python3
"""
SRT文本修正工具 - 模糊匹配版本
添加滑动窗口模糊匹配，处理首词拼写错误的情况
无需额外依赖，纯Python实现
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


def find_by_sliding_window(srt_normalized: str, search_region: str,
                          fuzzy_threshold: float = 0.80) -> Tuple[int, float]:
    """
    使用滑动窗口模糊匹配
    当精确匹配失败时使用此方法

    参数:
        srt_normalized: 标准化的SRT文本
        search_region: 搜索区域
        fuzzy_threshold: 模糊匹配阈值（默认0.80 = 80%相似度）

    返回:
        (position, score) - 最佳匹配位置和相似度分数
    """
    srt_len = len(srt_normalized)

    if srt_len == 0 or len(search_region) < srt_len:
        return -1, 0.0

    best_score = 0.0
    best_pos = -1

    # 滑动窗口：每隔一定步长检查一次（平衡速度和准确性）
    # 步长设为 max(1, srt_len // 10)，较短的文本步长小，较长的文本步长大
    step = max(1, srt_len // 10)

    # 窗口大小：使用更精确的窗口，接近SRT长度
    # 对于短文本（<50字符），使用1.2倍；长文本使用1.15倍
    if srt_len < 50:
        window_size = int(srt_len * 1.2)
    else:
        window_size = int(srt_len * 1.15)

    for i in range(0, len(search_region) - srt_len + 1, step):
        window = search_region[i:i + window_size]

        # 计算相似度
        score = SequenceMatcher(None, srt_normalized, window).ratio()

        if score > best_score:
            best_score = score
            best_pos = i

            # 如果找到非常高的匹配度，可以提前返回（优化）
            if score >= 0.95:
                return best_pos, best_score

    # 只返回达到阈值的结果
    if best_score >= fuzzy_threshold:
        return best_pos, best_score

    return -1, 0.0


def find_text_in_reference(srt_text: str, reference_text: str, start_hint: int = 0,
                          use_fuzzy: bool = True) -> Tuple[int, int, float, str]:
    """
    在参考文本中找到SRT文本的位置
    使用标准化文本进行匹配，但返回原始位置

    返回:
        (start, end, score, method) - 开始位置、结束位置、相似度分数、匹配方法
    """
    srt_normalized = normalize_for_matching(srt_text)
    ref_normalized = normalize_for_matching(reference_text)

    if not srt_normalized:
        return -1, -1, 0.0, "none"

    srt_words = srt_normalized.split()
    if len(srt_words) == 0:
        return -1, -1, 0.0, "none"

    # 确定搜索范围
    # 根据统计：84%的条目距离≤10字符，中位数=1，平均=24，最大=313
    # 使用更精确的搜索窗口：向前50，向后300（覆盖99%+的情况）
    # 对于短文本（<20字符），使用更小的窗口避免误匹配
    if len(srt_normalized) < 20:
        # 短文本使用紧凑窗口
        search_start = max(0, start_hint - 50)
        search_end = min(len(ref_normalized), start_hint + 200)
    else:
        # 长文本可以使用稍大的窗口
        search_start = max(0, start_hint - 100)
        search_end = min(len(ref_normalized), start_hint + 500)

    search_region = ref_normalized[search_start:search_end]

    # ============================================================
    # 层次1：精确锚点匹配（最快）
    # ============================================================
    num_anchor_words = min(5, max(2, len(srt_words) // 3))
    start_anchor = ' '.join(srt_words[:num_anchor_words])
    end_anchor = ' '.join(srt_words[-num_anchor_words:]) if len(srt_words) > num_anchor_words else start_anchor

    # 如果锚点较短（<=3个单词），找所有匹配并选择最佳
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
            # 多个匹配，选择相似度最高的
            best_score = 0
            best_pos = all_positions[0]

            # 对于非常短的文本（<10个字符），使用更长的比较窗口
            # 否则所有匹配的得分都会是1.0，无法区分
            compare_len = max(len(srt_normalized), 50) if len(srt_normalized) < 10 else len(srt_normalized)

            for pos in all_positions:
                test_start = search_start + pos
                test_end = min(test_start + compare_len, len(ref_normalized))
                test_text = ref_normalized[test_start:test_end]
                score = SequenceMatcher(None, srt_normalized, test_text).ratio()

                # 如果得分相同或非常接近（差异<0.01），优先选择更接近start_hint的位置
                # 因为SRT条目是按顺序出现的
                if score > best_score + 0.01:
                    best_score = score
                    best_pos = pos
                elif abs(score - best_score) <= 0.01:
                    # 得分接近，选择更接近start_hint的位置
                    current_distance = abs(test_start - start_hint)
                    best_distance = abs(search_start + best_pos - start_hint)
                    if current_distance < best_distance:
                        best_score = score
                        best_pos = pos

            start_pos = best_pos
    else:
        # 锚点较长，使用第一个匹配即可
        start_pos = search_region.find(start_anchor)

    method = "exact"

    # ============================================================
    # 层次2：缩短锚点再试（找到所有匹配，选择最佳）
    # ============================================================
    if start_pos == -1:
        start_anchor = ' '.join(srt_words[:2])

        # 找到所有匹配的短锚点位置
        all_positions = []
        pos = 0
        while True:
            pos = search_region.find(start_anchor, pos)
            if pos == -1:
                break
            all_positions.append(pos)
            pos += 1

        # 如果找到多个位置，选择相似度最高的
        if len(all_positions) > 0:
            if len(all_positions) == 1:
                start_pos = all_positions[0]
            else:
                # 多个匹配，计算每个位置的相似度
                best_score = 0
                best_pos = all_positions[0]

                # 对于非常短的文本（<10个字符），使用更长的比较窗口
                compare_len = max(len(srt_normalized), 50) if len(srt_normalized) < 10 else len(srt_normalized)

                for pos in all_positions:
                    test_start = search_start + pos
                    test_end = min(test_start + compare_len, len(ref_normalized))
                    test_text = ref_normalized[test_start:test_end]
                    score = SequenceMatcher(None, srt_normalized, test_text).ratio()

                    # 如果得分相同或非常接近，优先选择更接近start_hint的位置
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

    # ============================================================
    # 层次3：模糊匹配（处理拼写错误）⭐ 新增
    # ============================================================
    if start_pos == -1 and use_fuzzy:
        fuzzy_pos, fuzzy_score = find_by_sliding_window(
            srt_normalized,
            search_region,
            fuzzy_threshold=0.80
        )

        if fuzzy_pos != -1:
            # 找到模糊匹配
            method = "fuzzy"

            # 模糊匹配找到的是大致位置，现在需要精确定位
            abs_start = search_start + fuzzy_pos

            # 使用SequenceMatcher找到最佳对齐
            # 在找到的位置附近搜索精确匹配
            best_ratio = 0
            best_start = abs_start
            best_end = abs_start + len(srt_normalized)

            # 在fuzzy_pos附近±30个字符范围内微调（扩大搜索窗口以找到更精确的边界）
            search_window_start = max(abs_start - 30, search_start)
            search_window_end = min(abs_start + 60, search_start + len(search_region))

            for test_start in range(search_window_start, search_window_end):
                # 不仅调整起始位置，也尝试不同的结束位置（处理长度差异）
                # 搜索范围：SRT长度的0.9倍到1.1倍
                min_len = int(len(srt_normalized) * 0.9)
                max_len = int(len(srt_normalized) * 1.1)

                for test_len in range(min_len, min(max_len + 1, len(ref_normalized) - test_start + 1)):
                    test_end = test_start + test_len
                    if test_end > len(ref_normalized):
                        break

                    test_text = ref_normalized[test_start:test_end]
                    ratio = SequenceMatcher(None, srt_normalized, test_text).ratio()

                    # 优先选择从单词边界开始的位置
                    # 检查是否在单词边界（前面是空格或开头）
                    at_word_boundary = (test_start == 0 or
                                       ref_normalized[test_start - 1].isspace())

                    # 如果在单词边界，给予小幅加分（提高加分以确保选择正确边界）
                    if at_word_boundary:
                        ratio += 0.02

                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_start = test_start
                        best_end = test_end

            return best_start, best_end, best_ratio, method

    # ============================================================
    # 如果所有方法都失败
    # ============================================================
    if start_pos == -1:
        return -1, -1, 0.0, "none"

    # ============================================================
    # 找到了匹配（精确或缩短锚点）
    # ============================================================
    abs_start = search_start + start_pos

    # 查找结束锚点
    max_search_length = len(srt_normalized) * 3
    end_search_region = ref_normalized[abs_start:abs_start + max_search_length]

    end_pos = end_search_region.find(end_anchor)
    if end_pos == -1:
        # 结束锚点未找到，使用SequenceMatcher找到最佳对齐
        # 在可能的范围内搜索最佳匹配
        best_ratio = 0
        best_end = abs_start + len(srt_normalized)

        # 搜索范围：SRT长度的0.8倍到1.5倍
        min_len = int(len(srt_normalized) * 0.8)
        max_len = int(len(srt_normalized) * 1.5)

        for test_len in range(min_len, min(max_len, len(ref_normalized) - abs_start)):
            test_text = ref_normalized[abs_start:abs_start + test_len]
            ratio = SequenceMatcher(None, srt_normalized, test_text).ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_end = abs_start + test_len

        abs_end = best_end
    else:
        abs_end = abs_start + end_pos + len(end_anchor)

    # 计算匹配分数
    matched_text = ref_normalized[abs_start:abs_end]
    score = SequenceMatcher(None, srt_normalized, matched_text).ratio()

    return abs_start, abs_end, score, method


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
    while orig_start > 0 and reference_text[orig_start - 1].isalnum():
        orig_start -= 1

    # 如果orig_end指向空格，回退到最后一个非空格字符
    while orig_end > orig_start and reference_text[orig_end].isspace():
        orig_end -= 1

    # 向后扩展到单词边界（只有当前字符是字母数字时才扩展）
    if reference_text[orig_end].isalnum():
        while orig_end < len(reference_text) - 1 and reference_text[orig_end + 1].isalnum():
            orig_end += 1

    # 包含紧随的标点符号，但在句子终止符+引号处停止
    sentence_terminators = '.!?:;'
    closing_quotes = '"\u201d\u2019'  # 右引号
    other_punct = ',—–-\u201c\u2018\''  # 其他标点（逗号、破折号、左引号等）

    while orig_end < len(reference_text) - 1:
        next_char = reference_text[orig_end + 1]

        # 如果是句子终止符，包含它并检查后续是否有引号
        if next_char in sentence_terminators:
            orig_end += 1
            # 检查终止符后是否紧跟右引号
            if orig_end < len(reference_text) - 1:
                after_terminator = reference_text[orig_end + 1]
                if after_terminator in closing_quotes:
                    orig_end += 1  # 包含右引号
            break  # 找到终止符后停止

        # 如果是右引号（在终止符之前）
        elif next_char in closing_quotes:
            orig_end += 1
            # 检查引号后是否有终止符
            if orig_end < len(reference_text) - 1:
                after_quote = reference_text[orig_end + 1]
                if after_quote in sentence_terminators:
                    orig_end += 1  # 包含终止符
            break  # 找到右引号后停止

        # 如果是其他标点（逗号、破折号等），包含它并继续
        elif next_char in other_punct:
            orig_end += 1

        # 如果是空格，可能到了下一个词，停止
        elif next_char.isspace():
            break

        # 其他情况停止
        else:
            break

    # 向前包含开头的引号
    quote_chars = '"\'""''\u201c\u201d\u2018\u2019'
    while orig_start > 0:
        prev_char = reference_text[orig_start - 1]
        if prev_char in quote_chars:
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
    extracted = extracted.strip()

    # 移除段落分隔符（双换行符），因为会破坏SRT格式
    # 将连续的换行符替换为单个换行符
    extracted = re.sub(r'\n\n+', '\n', extracted)

    return extracted


def correct_srt_entries(srt_entries: List[SRTEntry],
                       reference_text: str,
                       confidence_threshold: float = 0.65,
                       use_fuzzy: bool = True) -> List[SRTEntry]:
    """修正所有SRT条目"""
    print(f"\n开始修正字幕...")
    print(f"匹配阈值: {confidence_threshold}")
    print(f"模糊匹配: {'启用' if use_fuzzy else '禁用'}")

    corrected_count = 0
    fuzzy_count = 0
    ref_position_hint = 0

    for i, entry in enumerate(srt_entries):
        if (i + 1) % 10 == 0:
            print(f"进度: {i+1}/{len(srt_entries)} ({100*(i+1)//len(srt_entries)}%)", end='\r')

        # 在参考文本中查找
        norm_start, norm_end, score, method = find_text_in_reference(
            entry.text,
            reference_text,
            ref_position_hint,
            use_fuzzy=use_fuzzy
        )

        if score >= confidence_threshold and norm_start != -1:
            # 提取修正后的文本
            corrected = extract_corrected_text(reference_text, norm_start, norm_end)

            if corrected and len(corrected.strip()) > 0:
                entry.text = corrected
                ref_position_hint = norm_end
                corrected_count += 1

                if method == "fuzzy":
                    fuzzy_count += 1

                # 显示模糊匹配的例子
                if method == "fuzzy" and entry.text != entry.original_text:
                    print(f"\n\n🔍 模糊匹配成功 - 字幕 #{entry.index}:")
                    print(f"  原文: {entry.original_text[:70]}")
                    print(f"  修正: {entry.text[:70]}")
                    print(f"  置信度: {score:.2%}")

    print(f"\n\n修正完成: {corrected_count}/{len(srt_entries)} 条字幕被修正")
    if use_fuzzy and fuzzy_count > 0:
        print(f"  其中 {fuzzy_count} 条通过模糊匹配修正")

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


def main(srt_path: str, txt_path: str, output_path: str = None,
         threshold: float = 0.65, use_fuzzy: bool = True):
    """主函数"""
    if output_path is None:
        output_path = srt_path.replace('.srt', '_corrected_fuzzy.srt')

    print("=" * 80)
    print("SRT 文本修正工具 - 模糊匹配版本".center(80))
    print("添加滑动窗口模糊匹配，处理首词拼写错误".center(80))
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
    corrected_entries = correct_srt_entries(srt_entries, reference_text, threshold, use_fuzzy)

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
        print("用法: python srt_corrector_fuzzy.py <srt文件> <txt文件> [输出文件] [阈值] [模糊匹配]")
        print("\n参数说明:")
        print("  srt文件     - 需要修正的SRT字幕文件")
        print("  txt文件     - 准确的参考文本文件")
        print("  输出文件    - 可选，默认为原文件名_corrected_fuzzy.srt")
        print("  阈值        - 可选，匹配置信度阈值(0.0-1.0)，默认0.65")
        print("  模糊匹配    - 可选，启用模糊匹配(true/false)，默认true")
        print("\n特性:")
        print("  ✓ 三层匹配机制：精确锚点 → 缩短锚点 → 模糊匹配")
        print("  ✓ 处理首词拼写错误（如 'Waz' → 'Woz'）")
        print("  ✓ 无需额外依赖，纯Python实现")
        print("  ✓ 预计修正率提升 3-8%")
        print("\n示例:")
        print("  python srt_corrector_fuzzy.py 'audio.srt' 'reference.txt'")
        print("  python srt_corrector_fuzzy.py 'audio.srt' 'reference.txt' 'output.srt' 0.7")
        print("  python srt_corrector_fuzzy.py 'audio.srt' 'reference.txt' 'output.srt' 0.65 false")
        sys.exit(1)

    srt_file = sys.argv[1]
    txt_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 0.65
    use_fuzzy_match = sys.argv[5].lower() != 'false' if len(sys.argv) > 5 else True

    main(srt_file, txt_file, output_file, threshold, use_fuzzy_match)
