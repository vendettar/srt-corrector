from __future__ import annotations

import sys

from .corrector import (
    correct_srt_entries,
    show_comparison_examples,
    show_statistics,
)
from .parsing import parse_srt, write_srt


def main(
    srt_path: str,
    txt_path: str,
    output_path: str | None = None,
    threshold: float = 0.65,
    use_fuzzy: bool = True,
):
    """High-level workflow: read, correct, write."""
    if output_path is None:
        output_path = srt_path.replace(".srt", "_corrected_fuzzy.srt")

    print("=" * 80)
    print("SRT 文本修正工具 - 模糊匹配版本".center(80))
    print("添加滑动窗口模糊匹配，处理首词拼写错误".center(80))
    print("=" * 80)

    print(f"\n[1/4] 读取SRT文件...")
    print(f"      路径: {srt_path}")
    srt_entries = parse_srt(srt_path)
    print(f"      ✓ 读取 {len(srt_entries)} 条字幕")

    print(f"\n[2/4] 读取参考文本...")
    print(f"      路径: {txt_path}")
    with open(txt_path, "r", encoding="utf-8") as f:
        reference_text = f.read()
    print(f"      ✓ 读取 {len(reference_text):,} 字符")

    print(f"\n[3/4] 执行文本修正...")
    corrected_entries = correct_srt_entries(
        srt_entries, reference_text, threshold, use_fuzzy
    )

    print(f"\n[4/4] 保存修正结果...")
    print(f"      路径: {output_path}")
    write_srt(corrected_entries, output_path)
    print("      ✓ 保存成功")

    show_statistics(corrected_entries)
    show_comparison_examples(corrected_entries, num_examples=8)

    print("\n" + "=" * 80)
    print("✓ 全部完成！".center(80))
    print("=" * 80)


def run_cli(argv: list[str] | None = None):
    """Entry point for command-line usage."""
    args = sys.argv[1:] if argv is None else argv

    if len(args) < 2:
        print("用法: python -m srt_corrector <srt文件> <txt文件> [输出文件] [阈值] [模糊匹配]")
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
        print("  python -m srt_corrector 'audio.srt' 'reference.txt'")
        print("  python -m srt_corrector 'audio.srt' 'reference.txt' 'output.srt' 0.7")
        print("  python -m srt_corrector 'audio.srt' 'reference.txt' 'output.srt' 0.65 false")
        sys.exit(1)

    srt_file = args[0]
    txt_file = args[1]
    output_file = args[2] if len(args) > 2 else None
    threshold = float(args[3]) if len(args) > 3 else 0.65
    use_fuzzy_match = args[4].lower() != "false" if len(args) > 4 else True

    main(srt_file, txt_file, output_file, threshold, use_fuzzy_match)


if __name__ == "__main__":
    run_cli()
