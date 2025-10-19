#!/bin/bash
# SRT字幕修正工具 - 使用示例脚本

echo "========================================"
echo "   SRT 字幕文本修正工具 - 使用示例"
echo "========================================"
echo ""

# 示例1: 基本用法（自动生成输出文件名）
echo "示例1: 基本用法"
echo "命令: python3 srt_corrector_final.py \"原始.srt\" \"参考.txt\""
echo "输出: 原始_corrected_final.srt"
echo ""

# 示例2: 指定输出文件名
echo "示例2: 指定输出文件名"
echo "命令: python3 srt_corrector_final.py \"原始.srt\" \"参考.txt\" \"我的输出.srt\""
echo "输出: 我的输出.srt"
echo ""

# 示例3: 调整匹配阈值（更严格）
echo "示例3: 使用更严格的匹配阈值"
echo "命令: python3 srt_corrector_final.py \"原始.srt\" \"参考.txt\" \"输出.srt\" 0.75"
echo "说明: 阈值0.75比默认的0.65更严格，只修正高度匹配的条目"
echo ""

# 示例4: 调整匹配阈值（更宽松）
echo "示例4: 使用更宽松的匹配阈值"
echo "命令: python3 srt_corrector_final.py \"原始.srt\" \"参考.txt\" \"输出.srt\" 0.55"
echo "说明: 阈值0.55比默认的0.65更宽松，会修正更多条目（但可能有误匹配）"
echo ""

# 实际运行示例（使用当前文件夹的文件）
echo "========================================"
echo "实际运行示例（当前文件夹）:"
echo "========================================"
echo ""
echo "python3 srt_corrector_final.py \"Steve Jobs - 02.mp3.srt\" \"Steve Jobs - 02.txt\""
echo ""
echo "按回车键执行上述命令，或按 Ctrl+C 取消..."
read

# 执行命令
python3 srt_corrector_final.py "Steve Jobs - 02.mp3.srt" "Steve Jobs - 02.txt"
