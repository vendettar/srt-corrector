# SRT 字幕文本修正工具

这个工具可以使用准确的参考文本（如EPUB书籍文本）来修正音频转文字生成的SRT字幕文件中的错误，同时完整保留时间戳和所有标点符号。

## 文件说明

- **srt_corrector_final.py** - 最终版本的修正脚本
- **Steve Jobs - 02.mp3.srt** - 原始SRT文件（包含转录错误）
- **Steve Jobs - 02.txt** - 准确的参考文本
- **Steve Jobs - 02.mp3_corrected_final.srt** - 修正后的SRT文件

## 使用方法

### 基本用法

```bash
python3 srt_corrector_final.py <SRT文件> <TXT参考文件>
```

**示例：**
```bash
python3 srt_corrector_final.py "Steve Jobs - 02.mp3.srt" "Steve Jobs - 02.txt"
```

### 高级用法

#### 1. 指定输出文件名

```bash
python3 srt_corrector_final.py <SRT文件> <TXT参考文件> <输出文件>
```

**示例：**
```bash
python3 srt_corrector_final.py "Steve Jobs - 02.mp3.srt" "Steve Jobs - 02.txt" "output.srt"
```

#### 2. 调整匹配阈值

```bash
python3 srt_corrector_final.py <SRT文件> <TXT参考文件> <输出文件> <阈值>
```

**示例：**
```bash
python3 srt_corrector_final.py "Steve Jobs - 02.mp3.srt" "Steve Jobs - 02.txt" "output.srt" 0.7
```

- 阈值范围: 0.0 - 1.0
- 默认值: 0.65
- 阈值越高，匹配越严格，但可能遗漏一些可修正的条目
- 阈值越低，修正的条目越多，但可能出现误匹配

## 功能特点

✅ **完整保留时间戳** - 不改变任何时间轴
✅ **保留所有标点符号** - 包括Unicode引号 `" "` 、em-dash `—`、冒号等
✅ **智能文本匹配** - 使用序列匹配算法找到最佳对应文本
✅ **自动边界检测** - 准确提取单词和句子边界
✅ **进度显示** - 实时显示修正进度
✅ **详细统计** - 显示修正率和示例对比

## 输出示例

```
================================================================================
                               SRT 文本修正工具 - 最终版本
                              完整保留TXT原文的所有标点符号和格式
================================================================================

[1/4] 读取SRT文件...
      路径: Steve Jobs - 02.mp3.srt
      ✓ 读取 572 条字幕

[2/4] 读取参考文本...
      路径: Steve Jobs - 02.txt
      ✓ 读取 52,281 字符

[3/4] 执行文本修正...
进度: 572/572 (100%)

[4/4] 保存修正结果...
      路径: Steve Jobs - 02.mp3_corrected_final.srt
      ✓ 保存成功

统计信息:
  总字幕数: 572
  已修正: 381
  未修正: 191
  修正率: 66.6%
```

## 修正效果示例

**原文:**
```
Shakespeare, Plato, I loved King Lear.
```

**修正后:**
```
Shakespeare, Plato. I loved King Lear."
```

- 修正了逗号为句号
- 添加了缺失的Unicode右引号

---

**原文:**
```
One course the jobs took would become part of Silicon Valley lore.
```

**修正后:**
```
One course that Jobs took would become part of Silicon Valley lore:
```

- "the jobs" → "that Jobs"（词汇错误修正）
- 添加了缺失的冒号

## 技术说明

- 使用 `difflib.SequenceMatcher` 进行文本序列匹配
- 支持Unicode字符（引号、破折号等）
- 采用锚点匹配算法提高匹配精度
- 建立标准化文本到原始文本的位置映射
- 智能边界扩展保留完整的标点符号

## 注意事项

1. **不会合并或拆分字幕条目** - 只修正文本内容
2. **时间轴保持不变** - 所有时间戳完全保留
3. **编码要求** - SRT和TXT文件必须是UTF-8编码
4. **Python版本** - 需要Python 3.6或更高版本

## 适用场景

- 修正语音转文字生成的SRT字幕
- 使用准确的书籍文本修正有声书字幕
- 批量处理多个章节的字幕文件（可编写循环脚本）

## 故障排除

**问题：修正率太低**
- 尝试降低阈值（如从0.65降到0.60）
- 检查TXT文件是否与SRT内容对应

**问题：出现误匹配**
- 尝试提高阈值（如从0.65升到0.70）

**问题：缺少标点符号**
- 确保TXT文件包含完整的标点符号
- 检查TXT文件编码是否为UTF-8
