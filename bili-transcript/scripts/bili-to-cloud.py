#!/usr/bin/env python3
"""
bili-to-cloud.py — B站视频 → 音频下载 → 飞书妙记云端转写 → 存入 Obsidian
走飞书妙记 API，速度快、质量好

用法: python3 bili-to-cloud.py <B站URL或BV号> [输出目录]
依赖: lark-cli (已配置飞书认证)
"""
import sys
import os
import re
import json
import time
import subprocess
import tempfile
from datetime import datetime

# ── 配置 ──
DEFAULT_OUTDIR = "/root/obsidian/B站教程"
LARK_CLI = "/root/.hermes/node/bin/lark-cli"

# ── 解析 BV 号 ──
def parse_bvid(input_str):
    match = re.search(r'(BV[\w]{10})', input_str)
    if match:
        return match.group(1)
    raise ValueError(f"无法解析 BV 号: {input_str}")

# ── B站 API ──
def get_video_info(bvid):
    import urllib.request
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    if data["code"] != 0:
        raise RuntimeError(f"B站 API 错误: {data}")
    d = data["data"]
    return {
        "title": d["title"],
        "duration": d["duration"],
        "aid": d["aid"],
        "cid": d["cid"],
        "owner": d["owner"]["name"],
        "upload_date": d["pubdate"],
        "bvid": bvid,
    }

def get_audio_url(aid, cid):
    import urllib.request
    url = f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&fnval=16&qn=64"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    if data["code"] != 0:
        raise RuntimeError(f"获取音频 URL 失败: {data}")
    audio = data["data"]["dash"]["audio"][0]
    return audio.get("baseUrl") or audio.get("base_url")

def download_audio(audio_url, output_path):
    import urllib.request
    req = urllib.request.Request(audio_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com"
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(output_path, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
    return os.path.getsize(output_path)

# ── 飞书 CLI 操作 ──
def lark_upload(file_path):
    """上传文件到飞书云空间，返回 file_token"""
    print(f"  上传到飞书云空间...", flush=True)
    result = subprocess.run(
        [LARK_CLI, "drive", "+upload", "--file", file_path],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"上传失败: {result.stderr}")
    
    # 解析返回的 JSON
    try:
        data = json.loads(result.stdout)
        file_token = data.get("file_token") or data.get("token")
        if not file_token:
            # 尝试从输出中提取
            for line in result.stdout.strip().split("\n"):
                if "file_token" in line or "token" in line:
                    match = re.search(r'(boxcn[A-Za-z0-9]+)', line)
                    if match:
                        file_token = match.group(1)
                        break
        if not file_token:
            raise RuntimeError(f"无法从返回结果中提取 file_token: {result.stdout}")
        return file_token
    except json.JSONDecodeError:
        # 尝试从纯文本中提取
        match = re.search(r'(boxcn[A-Za-z0-9]+)', result.stdout)
        if match:
            return match.group(1)
        raise RuntimeError(f"无法解析上传结果: {result.stdout}")

def lark_generate_minute(file_token):
    """将 file_token 转为妙记，返回 minute_url"""
    print(f"  生成妙记...", flush=True)
    result = subprocess.run(
        [LARK_CLI, "minutes", "+upload", "--file-token", file_token],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"生成妙记失败: {result.stderr}")
    
    try:
        data = json.loads(result.stdout)
        minute_url = data.get("minute_url", "")
        if not minute_url:
            raise RuntimeError(f"返回结果中没有 minute_url: {result.stdout}")
        return minute_url
    except json.JSONDecodeError:
        # 从文本中提取 URL
        match = re.search(r'https?://[^\s]+/minutes/([^\s]+)', result.stdout)
        if match:
            return match.group(0)
        raise RuntimeError(f"无法解析妙记结果: {result.stdout}")

def lark_get_transcript(minute_token):
    """获取妙记逐字稿"""
    print(f"  获取逐字稿...", flush=True)
    result = subprocess.run(
        [LARK_CLI, "vc", "+notes", "--minute-tokens", minute_token],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"获取逐字稿失败: {result.stderr}")
    
    # 解析返回结果
    try:
        data = json.loads(result.stdout)
        # vc +notes 返回的结构可能包含逐字稿
        transcript = data.get("transcript", "") or data.get("text", "") or data.get("content", "")
        if not transcript:
            # 可能返回的是文件路径
            file_path = data.get("file", "") or data.get("path", "")
            if file_path and os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    transcript = f.read()
        if not transcript:
            # 尝试从原始输出中提取
            transcript = result.stdout
        return transcript
    except json.JSONDecodeError:
        # 可能是纯文本或文件路径
        if os.path.exists(result.stdout.strip()):
            with open(result.stdout.strip(), "r", encoding="utf-8") as f:
                return f.read()
        return result.stdout

def save_to_obsidian(info, transcript, outdir):
    """保存到 Obsidian"""
    os.makedirs(outdir, exist_ok=True)
    
    date_str = datetime.fromtimestamp(info["upload_date"]).strftime("%Y-%m-%d")
    safe_title = re.sub(r'[\/\\:*?"<>|]', '_', info["title"])[:100]
    duration_min = info["duration"] // 60
    duration_sec = info["duration"] % 60
    duration_fmt = f"{duration_min}m{duration_sec}s"
    char_count = len(transcript)
    est_tokens = char_count * 7 // 10
    
    md_file = os.path.join(outdir, f"{date_str}_{safe_title}.md")
    
    md_content = f"""---
title: "{info['title']}"
date: {date_str}
tags: [B站, 逐字稿, 飞书妙记]
source: "https://bilibili.com/video/{info['bvid']}"
uploader: "{info['owner']}"
duration: "{duration_fmt}"
transcript_chars: {char_count}
transcript_source: "飞书妙记"
---

# {info['title']}

> UP主: {info['owner']} | 时长: {duration_fmt} | 日期: {date_str}
> 来源: [B站原视频](https://bilibili.com/video/{info['bvid']}) | 转写: 飞书妙记

## 逐字稿

{transcript}

---
*由飞书妙记云端转写生成，{char_count}字 ≈ {est_tokens} tokens*
"""
    
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return md_file, char_count, est_tokens

# ── 主流程 ──
def main():
    if len(sys.argv) < 2:
        print("用法: python3 bili-to-cloud.py <B站URL或BV号> [输出目录]")
        sys.exit(1)
    
    input_str = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTDIR
    
    bvid = parse_bvid(input_str)
    
    # Step 1: 获取视频信息
    print("📡 获取视频信息...", flush=True)
    info = get_video_info(bvid)
    duration_min = info["duration"] // 60
    duration_sec = info["duration"] % 60
    
    print(f"  标题: {info['title']}", flush=True)
    print(f"  UP主: {info['owner']}", flush=True)
    print(f"  时长: {duration_min}m{duration_sec}s", flush=True)
    
    # Step 2: 获取音频 URL
    print("\n🔗 获取音频流...", flush=True)
    audio_url = get_audio_url(info["aid"], info["cid"])
    
    # Step 3: 下载音频
    print("\n⬇️  下载音频...", flush=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        m4s_path = os.path.join(tmpdir, "audio.m4s")
        m4a_path = os.path.join(tmpdir, "audio.m4a")
        
        size = download_audio(audio_url, m4s_path)
        print(f"  下载完成: {size / 1024 / 1024:.1f}MB", flush=True)
        
        # 转为 m4a（飞书支持的格式）
        print("  转换格式...", flush=True)
        subprocess.run(
            ["ffmpeg", "-y", "-i", m4s_path, "-vn", "-acodec", "copy", m4a_path],
            capture_output=True, check=True
        )
        print(f"  m4a: {os.path.getsize(m4a_path) / 1024 / 1024:.1f}MB", flush=True)
        
        # Step 4: 上传到飞书云空间
        print("\n☁️  飞书妙记转写...", flush=True)
        file_token = lark_upload(m4a_path)
        print(f"  file_token: {file_token}", flush=True)
        
        # Step 5: 生成妙记
        minute_url = lark_generate_minute(file_token)
        print(f"  minute_url: {minute_url}", flush=True)
        
        # 提取 minute_token
        minute_token = minute_url.rstrip("/").split("/")[-1]
        print(f"  minute_token: {minute_token}", flush=True)
        
        # Step 6: 等待转写完成
        print("\n⏳ 等待云端转写...", flush=True)
        max_wait = 600  # 最多等 10 分钟
        start = time.time()
        while time.time() - start < max_wait:
            try:
                result = subprocess.run(
                    [LARK_CLI, "minutes", "minutes", "get", minute_token],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    status = data.get("status", "")
                    if status in ("COMPLETED", "DONE", "FINISHED"):
                        print(f"  转写完成!", flush=True)
                        break
                    else:
                        elapsed = int(time.time() - start)
                        print(f"  状态: {status} ({elapsed}秒)...", flush=True)
            except:
                pass
            time.sleep(10)
        else:
            print("  ⚠️ 等待超时，尝试获取已有结果...", flush=True)
        
        # Step 7: 获取逐字稿
        print("\n📝 获取逐字稿...", flush=True)
        transcript = lark_get_transcript(minute_token)
    
    # Step 8: 存入 Obsidian
    print("\n💾 存入 Obsidian...", flush=True)
    md_file, char_count, est_tokens = save_to_obsidian(info, transcript, outdir)
    
    print(f"\n{'='*50}", flush=True)
    print(f"  标题: {info['title']}", flush=True)
    print(f"  字数: {char_count}", flush=True)
    print(f"  Tokens: ~{est_tokens}", flush=True)
    print(f"  文件: {md_file}", flush=True)
    print(f"  妙记: {minute_url}", flush=True)
    print(f"{'='*50}", flush=True)

if __name__ == "__main__":
    main()
