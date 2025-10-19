#!/bin/bash
################################################################################
# SRT批量处理示例脚本
#
# 这个脚本演示如何批量处理多个SRT文件
# 你可以根据自己的需求修改这个脚本
################################################################################

echo "========================================"
echo "   SRT批量处理工具"
echo "========================================"
echo ""

# 方式1: 处理指定范围的章节
echo "方式1: 处理第1-5章（假设文件名格式为 Chapter_01.srt）"
echo "----------------------------------------"
echo ""

# 取消下面的注释来实际运行
# for i in {01..05}; do
#     echo "正在处理第 $i 章..."
#     python3 srt_corrector_final.py \
#         "Chapter_${i}.srt" \
#         "Chapter_${i}.txt" \
#         "Chapter_${i}_corrected.srt"
#     echo ""
# done

echo "（示例命令已注释，取消注释可运行）"
echo ""

# 方式2: 处理当前目录下所有.srt文件
echo "方式2: 自动处理当前目录所有SRT文件"
echo "----------------------------------------"
echo ""

# 取消下面的注释来实际运行
# for srt_file in *.srt; do
#     # 跳过已修正的文件
#     if [[ $srt_file == *"_corrected"* ]]; then
#         continue
#     fi
#
#     # 构造对应的TXT文件名（假设SRT和TXT文件名相同，只是扩展名不同）
#     txt_file="${srt_file%.srt}.txt"
#
#     # 检查TXT文件是否存在
#     if [ -f "$txt_file" ]; then
#         echo "处理: $srt_file"
#         python3 srt_corrector_final.py "$srt_file" "$txt_file"
#         echo ""
#     else
#         echo "⚠️  跳过 $srt_file (找不到对应的 $txt_file)"
#     fi
# done

echo "（示例命令已注释，取消注释可运行）"
echo ""

# 方式3: 处理指定文件列表
echo "方式3: 处理指定的文件列表"
echo "----------------------------------------"
echo ""

# 定义文件对列表
# declare -a files=(
#     "Steve Jobs - 01.mp3.srt:Steve Jobs - 01.txt"
#     "Steve Jobs - 02.mp3.srt:Steve Jobs - 02.txt"
#     "Steve Jobs - 03.mp3.srt:Steve Jobs - 03.txt"
# )
#
# for pair in "${files[@]}"; do
#     IFS=':' read -r srt_file txt_file <<< "$pair"
#     echo "处理: $srt_file"
#     python3 srt_corrector_final.py "$srt_file" "$txt_file"
#     echo ""
# done

echo "（示例命令已注释，取消注释可运行）"
echo ""

# 方式4: 使用不同阈值处理
echo "方式4: 根据质量使用不同阈值"
echo "----------------------------------------"
echo ""

# 取消下面的注释来实际运行
# # 高质量文件用高阈值
# python3 srt_corrector_final.py "high_quality.srt" "high_quality.txt" "output1.srt" 0.75
#
# # 普通质量用默认阈值
# python3 srt_corrector_final.py "normal_quality.srt" "normal_quality.txt" "output2.srt"
#
# # 低质量文件用低阈值
# python3 srt_corrector_final.py "low_quality.srt" "low_quality.txt" "output3.srt" 0.55

echo "（示例命令已注释，取消注释可运行）"
echo ""

# 方式5: 批量处理并统计结果
echo "方式5: 批量处理并生成统计报告"
echo "----------------------------------------"
echo ""

# 取消下面的注释来实际运行
# total=0
# success=0
# failed=0
#
# for srt_file in *.srt; do
#     if [[ $srt_file == *"_corrected"* ]]; then
#         continue
#     fi
#
#     txt_file="${srt_file%.srt}.txt"
#
#     if [ -f "$txt_file" ]; then
#         total=$((total + 1))
#         echo "[$total] 处理: $srt_file"
#
#         if python3 srt_corrector_final.py "$srt_file" "$txt_file" > /dev/null 2>&1; then
#             success=$((success + 1))
#             echo "    ✓ 成功"
#         else
#             failed=$((failed + 1))
#             echo "    ✗ 失败"
#         fi
#     fi
# done
#
# echo ""
# echo "========================================"
# echo "处理完成！"
# echo "总计: $total 个文件"
# echo "成功: $success 个"
# echo "失败: $failed 个"
# echo "========================================"

echo "（示例命令已注释，取消注释可运行）"
echo ""

echo "========================================"
echo "使用说明："
echo "========================================"
echo "1. 编辑此脚本，取消注释你需要的处理方式"
echo "2. 根据你的文件名格式修改脚本"
echo "3. 运行: ./batch_process_example.sh"
echo ""
echo "提示: 你也可以直接运行单个命令，例如："
echo "python3 srt_corrector_final.py \"你的文件.srt\" \"你的文本.txt\""
echo ""
