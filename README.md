# srt-corrector

一个用于修正 SRT 字幕的命令行工具，支持精确和模糊匹配流程。

## 安装

```bash
pip install -e .
```

## 使用

```bash
srtc raw.srt original.txt > corrected.srt
```

`srtc` 会读取原始字幕文件与参考文本，自动匹配并生成修正后的字幕输出。
