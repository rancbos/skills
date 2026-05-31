#!/usr/bin/env bash
# bili-to-local.sh — B站视频 → 音频下载 + 本地 faster-whisper 逐字稿
# 用法: bash bili-to-local.sh <B站URL或BV号> [输出目录] [whisper模型]
# 依赖: yt-dlp, ffmpeg, faster-whisper (pip)

set -euo pipefail

# ── 参数 ──
INPUT="${1:?用法: $0 <B站URL或BV号> [输出目录] [whisper模型]}"
OUTDIR="${2:-/root/obsidian/B站教程}"
MODEL="${3:-small}"  # tiny/base/small/medium/medium.en
DEVICE="cpu"
COMPUTE_TYPE="int8"  # CPU 最优: int8; GPU 可用: float16

# ── 工具检查 ──
for cmd in yt-dlp ffmpeg; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "❌ 缺少 $cmd，请先安装"; exit 1; }
done
python3 -c "import faster_whisper" 2>/dev/null || {
  echo "⚠️  faster-whisper 未安装，正在安装..."
  pip install faster-whisper -i https://mirrors.aliyun.com/pypi/simple/ -q
}

# ── 临时目录 ──
TMPDIR=$(mktemp -d /tmp/bili-whisper-XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT

# ── Step 1: 获取视频信息 ──
echo "📡 获取视频信息..."
INFO=$(yt-dlp --no-download --print '{"title":"%(title)s","duration":%(duration)s,"uploader":"%(uploader)s","id":"%(id)s","upload_date":"%(upload_date)s"}' "$INPUT" 2>/dev/null | head -1)
TITLE=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
DURATION=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['duration'])")
UPLOADER=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['uploader'])")
UPLOAD_DATE=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['upload_date'])")
VIDEO_ID=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 格式化日期 YYYY-MM-DD
FORMATTED_DATE="${UPLOAD_DATE:0:4}-${UPLOAD_DATE:4:2}-${UPLOAD_DATE:6:2}"
# 格式化时长
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))
DURATION_FMT="${DURATION_MIN}m${DURATION_SEC}s"

echo "  标题: $TITLE"
echo "  UP主: $UPLOADER"
echo "  时长: $DURATION_FMT"
echo "  日期: $FORMATTED_DATE"

# 预估转写时间（CPU small 模型约 0.3x 实时速度）
EST_MIN=$((DURATION / 60 * 3 / 10))
echo "  预估转写时间: ~${EST_MIN} 分钟 (CPU/${MODEL}模型)"

# ── Step 2: 下载音频 ──
echo ""
echo "⬇️  下载音频..."
AUDIO_FILE="$TMPDIR/audio.m4a"
yt-dlp -x --audio-format m4a --audio-quality 0 \
  -o "$AUDIO_FILE" \
  --no-playlist \
  --quiet --progress \
  "$INPUT" 2>&1 | tail -3

if [ ! -f "$AUDIO_FILE" ]; then
  echo "❌ 音频下载失败"
  exit 1
fi
echo "✅ 音频下载完成: $(du -h "$AUDIO_FILE" | cut -f1)"

# ── Step 3: 转写 ──
echo ""
echo "🎙️  开始转写 (模型: $MODEL, 设备: $DEVICE)..."
TRANSCRIPT_FILE="$TMPDIR/transcript.txt"

python3 << 'PYEOF'
import sys
from faster_whisper import WhisperModel

model_name = "MODELPLACEHOLDER"
device = "cpu"
compute_type = "int8"

print(f"  加载模型: {model_name}...", flush=True)
model = WhisperModel(model_name, device=device, compute_type=compute_type)

print(f"  转写中...", flush=True)
segments, info = model.transcribe(
    "AUDIOPLACEHOLDER",
    beam_size=5,
    language="zh",
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500),
)

with open("OUTPUTPLACEHOLDER", "w", encoding="utf-8") as f:
    total_chars = 0
    for seg in segments:
        start_min = int(seg.start // 60)
        start_sec = int(seg.start % 60)
        line = f"[{start_min:02d}:{start_sec:02d}] {seg.text.strip()}"
        f.write(line + "\n")
        total_chars += len(seg.text.strip())
        if total_chars % 200 < 50:  # 每约200字打印一次进度
            print(f"  已转写 {total_chars} 字 [{start_min:02d}:{start_sec:02d}]...", flush=True)

print(f"  转写完成，共 {total_chars} 字", flush=True)
PYEOF

# 替换占位符并执行
sed -i "s|MODELPLACEHOLDER|${MODEL}|g" /tmp/bili-py-$$.py 2>/dev/null || true

# 直接生成 Python 脚本
cat > "$TMPDIR/transcribe.py" << PYEOF
import sys
from faster_whisper import WhisperModel

model = WhisperModel("${MODEL}", device="${DEVICE}", compute_type="${COMPUTE_TYPE}")
print(f"  模型加载完成", flush=True)

segments, info = model.transcribe(
    "${AUDIO_FILE}",
    beam_size=5,
    language="zh",
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500),
)

with open("${TRANSCRIPT_FILE}", "w", encoding="utf-8") as f:
    total_chars = 0
    for seg in segments:
        start_min = int(seg.start // 60)
        start_sec = int(seg.start % 60)
        line = f"[{start_min:02d}:{start_sec:02d}] {seg.text.strip()}"
        f.write(line + "\n")
        total_chars += len(seg.text.strip())
        if total_chars > 0 and total_chars % 300 < 50:
            print(f"  进度: {total_chars} 字 [{start_min:02d}:{start_sec:02d}]...", flush=True)

print(f"  转写完成，共 {total_chars} 字", flush=True)
PYEOF

python3 "$TMPDIR/transcribe.py"

if [ ! -f "$TRANSCRIPT_FILE" ] || [ ! -s "$TRANSCRIPT_FILE" ]; then
  echo "❌ 转写失败"
  exit 1
fi

CHAR_COUNT=$(wc -m < "$TRANSCRIPT_FILE")
echo "✅ 转写完成: ${CHAR_COUNT} 字"

# ── Step 4: 生成 Markdown 存入 Obsidian ──
echo ""
echo "📝 生成 Markdown..."
mkdir -p "$OUTDIR"

# 文件名清理（去掉特殊字符）
SAFE_TITLE=$(echo "$TITLE" | sed 's/[\/\\:*?"<>|]/_/g' | head -c 100)
MD_FILE="${OUTDIR}/${FORMATTED_DATE}_${SAFE_TITLE}.md"

# 估算 token（中文约 0.7 字/token）
EST_TOKENS=$((CHAR_COUNT * 7 / 10))

cat > "$MD_FILE" << MDEOF
---
title: "${TITLE}"
date: ${FORMATTED_DATE}
tags: [B站, 逐字稿]
source: "https://bilibili.com/video/${VIDEO_ID}"
uploader: "${UPLOADER}"
duration: "${DURATION_FMT}"
transcript_chars: ${CHAR_COUNT}
transcript_model: "${MODEL}"
---

# ${TITLE}

> UP主: ${UPLOADER} | 时长: ${DURATION_FMT} | 日期: ${FORMATTED_DATE}
> 来源: [B站原视频](https://bilibili.com/video/${VIDEO_ID})

## 逐字稿

$(cat "$TRANSCRIPT_FILE")

---
*由 faster-whisper (${MODEL}) 自动生成，${CHAR_COUNT} 字 ≈ ${EST_TOKENS} tokens*
MDEOF

echo "✅ 已保存: $MD_FILE"
echo ""
echo "═══════════════════════════════════════"
echo "  标题: $TITLE"
echo "  字数: ${CHAR_COUNT}"
echo "  Tokens: ~${EST_TOKENS}"
echo "  文件: $MD_FILE"
echo "═══════════════════════════════════════"
