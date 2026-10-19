"""
AI News Video Generator (Hinton Media Style)
Transforms article text or URLs into seamless, high-retention 9:16 vertical news videos.
Uses:
- edge-tts (Vietnamese Neural TTS with fast, crisp cadence)
- Remotion NewsShort (1080x1920, Bento HUD, Ken Burns, kinetic stats, karaoke caption)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import edge_tts

ROOT_DIR = Path(__file__).resolve().parent
OPENMONTAGE_DIR = ROOT_DIR / "OpenMontage"
COMPOSER_DIR = OPENMONTAGE_DIR / "remotion-composer"
OUTPUT_DIR = ROOT_DIR / "output"


def sanitize_script_for_tts(text: str) -> str:
    """Sanitizes text for Edge-TTS while preserving natural Vietnamese pronunciation."""
    t = text
    # Strip literal outline labels if present (Chương 1:, Phần 2:, etc.)
    t = re.sub(r"(?:Chương|Phần)\s*\d+\s*:\s*", "", t, flags=re.IGNORECASE)
    # Replace em dashes and en dashes
    t = re.sub(r"[—–]", ", ", t)
    # Replace parentheses
    t = re.sub(r"[\(\)]", " ", t)
    # Replace percent symbol
    t = re.sub(r"(\d+[\.,]?\d*)\s*%", r"\1 phần trăm", t)
    # Replace USD / $
    t = re.sub(r"\$\s*(\d+[\.,]?\d*)", r"\1 đô la Mỹ", t)
    t = re.sub(r"(\d+)\s*USD", r"\1 đô la Mỹ", t)
    # Replace &
    t = t.replace("&", " và ")
    # Replace multiple spaces
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_vietnamese_numbers(text: str) -> str:
    """Preserves standard technical spelling (AI, CEO, GPT, OpenAI, API) for clean on-screen display."""
    return text.strip()


def parse_vtt_subtitles(vtt_path: Path) -> list[dict]:
    """Parses WebVTT subtitle file into structured sentence timing records."""
    if not vtt_path.exists():
        return []
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}[\.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[\.,]\d{3})\n(.*?)(?=\n\n|\n\d+|\Z)",
        re.DOTALL
    )
    def to_sec(ts: str) -> float:
        ts = ts.replace(",", ".")
        h, m, s = ts.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    sentences = []
    for m in pattern.finditer(content):
        start = to_sec(m.group(1))
        end = to_sec(m.group(2))
        text = m.group(3).strip().replace("\n", " ")
        if text:
            sentences.append({
                "text": text,
                "start": start,
                "end": end,
                "duration": max(0.2, end - start)
            })
    return sentences


async def generate_voice_and_timing(
    script_text: str,
    voice: str,
    rate: str,
    output_mp3: Path,
) -> tuple[float, list[dict], list[dict]]:
    """
    Synthesizes audio with edge-tts and captures sentence boundaries to derive
    word-level timestamps for Remotion karaoke captions and shot cut snapping.
    Uses edge-tts CLI for rock-solid stability on long 60s+ texts with Python API fallback.
    """
    cleaned_text = sanitize_script_for_tts(script_text)
    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    vtt_path = output_mp3.with_suffix(".vtt")
    txt_temp = output_mp3.with_suffix(".txt")
    txt_temp.write_text(cleaned_text, encoding="utf-8")

    sentences: list[dict] = []

    # 1. Try robust CLI tool first
    edge_cli = OPENMONTAGE_DIR / ".venv" / "Scripts" / "edge-tts.exe"
    if not edge_cli.exists():
        edge_cli = Path(shutil.which("edge-tts") or "edge-tts")

    try:
        cmd = [
            str(edge_cli),
            "--voice", voice,
            "--rate", rate,
            "--file", str(txt_temp),
            "--write-media", str(output_mp3),
            "--write-subtitles", str(vtt_path),
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=120)
        if res.returncode == 0 and output_mp3.exists() and output_mp3.stat().st_size > 5000:
            sentences = parse_vtt_subtitles(vtt_path)
            print(f"  [TTS] Synthesized via edge-tts CLI ({output_mp3.stat().st_size/1024:.1f} KB, {len(sentences)} sentences)")
    except Exception as e:
        print(f"  [TTS] CLI attempt failed ({e}), falling back to Python API...")

    # 2. Fallback to Python API if CLI produced no sentences
    if not sentences:
        comm = edge_tts.Communicate(cleaned_text, voice, rate=rate)
        audio_data = bytearray()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                start_s = chunk["offset"] / 10_000_000.0
                dur_s = chunk["duration"] / 10_000_000.0
                sentences.append({
                    "text": chunk["text"],
                    "start": start_s,
                    "end": start_s + dur_s,
                    "duration": dur_s,
                })
        with open(output_mp3, "wb") as f:
            f.write(audio_data)

    total_duration = sentences[-1]["end"] if sentences else 0.0

    # Build word-level captions with proportional duration based on word length
    words: list[dict] = []
    for s_idx, sent in enumerate(sentences):
        sent_words = [w.strip() for w in sent["text"].split() if w.strip()]
        if not sent_words:
            continue
        total_chars = sum(len(w) for w in sent_words)
        cur_t = sent["start"]
        s_dur = sent["duration"]

        for w_idx, w in enumerate(sent_words):
            # weight by char length with minimum duration floor
            weight = max(1, len(w)) / max(1, total_chars)
            w_dur = s_dur * weight
            w_start_ms = int(cur_t * 1000)
            w_end_ms = int((cur_t + w_dur) * 1000)
            cur_t += w_dur

            is_last = (w_idx == len(sent_words) - 1)
            words.append({
                "word": w,
                "startMs": w_start_ms,
                "endMs": w_end_ms,
                "pageBreakAfter": is_last,
            })

    return total_duration, sentences, words


def plan_news_shots(
    sentences: list[dict],
    total_duration: float,
    custom_shots: list[dict] | None = None,
    meta: dict | None = None,
    image_assets: list[str] | None = None,
) -> list[dict]:
    """
    Plans clean, high-retention visual cuts aligned with sentence start times.
    Uses structured editorial metadata (headline, stat, comparison) and rich
    visual media assets (photos, tech illustrations) to ensure each scene is
    vivid, dynamic, and engaging.
    """
    if custom_shots:
        return custom_shots

    meta = meta or {}
    image_assets = image_assets or []
    primary_img = image_assets[0] if image_assets else None
    secondary_img = image_assets[1] if len(image_assets) > 1 else primary_img

    shots: list[dict] = []
    n_sent = len(sentences)

    for i, s in enumerate(sentences):
        start = s["start"]
        end = s["end"]
        if i == n_sent - 1:
            end = max(end, total_duration + 0.3)

        # Check if any image asset matches keywords in this specific sentence
        current_img = None
        s_lower = s["text"].lower()
        if image_assets:
            if any(k in s_lower for k in ["stanford", "đại học", "viện nghiên cứu"]):
                current_img = next((img for img in image_assets if "stanford" in img.lower()), None)
            elif any(k in s_lower for k in ["openai", "chatgpt", "o1"]):
                current_img = next((img for img in image_assets if "openai" in img.lower()), None)
            elif any(k in s_lower for k in ["siêu máy tính", "gpu", "huấn luyện", "ngân sách", "triệu đô", "kiến trúc"]):
                current_img = next((img for img in image_assets if "supercomputer" in img.lower()), None)
            elif any(k in s_lower for k in ["thị trường", "nvidia", "ngành công nghệ"]):
                current_img = next((img for img in image_assets if "nvidia" in img.lower()), None)
            elif any(k in s_lower for k in ["deepseek"]):
                current_img = next((img for img in image_assets if "deepseek" in img.lower() or "wiki" in img.lower()), None)

            if not current_img:
                img_idx = i % len(image_assets)
                current_img = image_assets[img_idx]

        if i == 0:
            h_title = meta.get("headline", "")
            if not h_title or len(h_title) > 35:
                h_title = " ".join(s["text"].split()[:5]).upper()
            h_sub = meta.get("sub_headline", "CẬP NHẬT CÔNG NGHỆ MỚI")
            shot = {
                "id": f"shot-{i}",
                "type": "hero_title",
                "in_seconds": start,
                "out_seconds": end,
                "title": h_title,
                "subtitle": h_sub,
            }
            if current_img:
                shot["src"] = current_img
            shots.append(shot)

        elif i == 1:
            stat_num = meta.get("stat", "ĐỘT PHÁ")
            stat_sub = meta.get("stat_desc", s["text"][:50])
            if current_img:
                shots.append({
                    "id": f"shot-{i}",
                    "type": "kenburns",
                    "in_seconds": start,
                    "out_seconds": end,
                    "src": current_img,
                    "stat": stat_num,
                    "title": stat_sub.upper(),
                    "subtitle": s["text"],
                    "scaleFrom": 1.04,
                    "scaleTo": 1.18,
                })
            else:
                shots.append({
                    "id": f"shot-{i}",
                    "type": "stat_card",
                    "in_seconds": start,
                    "out_seconds": end,
                    "stat": stat_num,
                    "subtitle": stat_sub,
                    "accentColor": "#FFE600",
                })

        elif i == 2:
            shot = {
                "id": f"shot-{i}",
                "type": "callout",
                "in_seconds": start,
                "out_seconds": end,
                "text": s["text"],
                "title": "KIẾN TRÚC & CÔNG NGHỆ",
                "callout_type": "info",
                "accentColor": "#38BDF8",
            }
            if current_img:
                shot["src"] = current_img
            shots.append(shot)

        elif i == 3:
            # Second evidence shot: benchmark metrics with animated live bars
            shot = {
                "id": f"shot-{i}",
                "type": "benchmark_card",
                "in_seconds": start,
                "out_seconds": end,
                "title": "BẢNG ĐIỂM ĐỐI ĐẦU TRỰC DIỆN",
                "subtitle": "THỬ NGHIỆM CHUẨN TOÁN HỌC & TƯ DUY LOGIC",
                "benchmarkData": {
                    "items": [
                        {
                            "category": "TOÁN OLYMPIC AIME 2024",
                            "modelA": {"name": "DeepSeek R1", "score": "79.8%", "value": 79.8, "color": "#10B981", "isWinner": True},
                            "modelB": {"name": "OpenAI o1", "score": "79.2%", "value": 79.2, "color": "#FB7185"}
                        },
                        {
                            "category": "TOÁN CHUYÊN SÂU MATH-500",
                            "modelA": {"name": "DeepSeek R1", "score": "97.3%", "value": 97.3, "color": "#10B981", "isWinner": True},
                            "modelB": {"name": "OpenAI o1", "score": "96.4%", "value": 96.4, "color": "#FB7185"}
                        },
                        {
                            "category": "LẬP TRÌNH THI ĐẤU CODEFORCES",
                            "modelA": {"name": "DeepSeek R1", "score": "96.3%", "value": 96.3, "color": "#38BDF8", "isWinner": True},
                            "modelB": {"name": "OpenAI o1", "score": "96.6%", "value": 96.6, "color": "#A78BFA"}
                        }
                    ],
                    "sourceNote": "Kiểm chứng độc lập: Stanford AI Lab & Technical Report"
                }
            }
            if current_img:
                shot["src"] = current_img
            shots.append(shot)

        elif i == 4:
            # Architecture callout
            shot = {
                "id": f"shot-{i}",
                "type": "callout",
                "in_seconds": start,
                "out_seconds": end,
                "text": s["text"],
                "title": "KIẾN TRÚC MoE & BỘ NHỚ MLA",
                "callout_type": "info",
                "accentColor": "#38BDF8",
            }
            if current_img:
                shot["src"] = current_img
            shots.append(shot)

        elif i == 5:
            # Midpoint dramatic Hero Title: The Aha moment / Pure RL
            shot = {
                "id": f"shot-{i}",
                "type": "hero_title",
                "in_seconds": start,
                "out_seconds": end,
                "title": "KHOẢNH KHẮC AHA!",
                "subtitle": "KHI CỖ MÁY TỰ HỌC CÁCH SUY NGHĨ",
            }
            if current_img:
                shot["src"] = current_img
            shots.append(shot)

        elif i == 6 and i < n_sent - 1:
            # Economic Shock Card with side-by-side cost and pricing breakdown
            shot = {
                "id": f"shot-{i}",
                "type": "economic_card",
                "in_seconds": start,
                "out_seconds": end,
                "title": "BÀI TOÁN KINH TẾ ĐẢO LỘN",
                "subtitle": "SỰ KHÁC BIỆT GÂY CHẤN ĐỘNG THUNG LŨNG SILICON",
                "economicData": {
                    "metrics": [
                        {
                            "title": "CHI PHÍ HUẤN LUYỆN (TRAINING BUDGET)",
                            "legacyLabel": "OpenAI & Big Tech",
                            "legacyValue": "$100M+ (~2.500 TỶ)",
                            "newLabel": "DeepSeek R1",
                            "newValue": "$6M (~150 TỶ)",
                            "badgeText": "TIẾT KIỆM 95%",
                            "badgeColor": "#F59E0B"
                        },
                        {
                            "title": "GIÁ THÀNH API (1 TRIỆU TOKEN)",
                            "legacyLabel": "OpenAI o1 Reasoning",
                            "legacyValue": "$15.00",
                            "newLabel": "DeepSeek R1",
                            "newValue": "$0.55",
                            "badgeText": "RẺ HƠN 27 LẦN",
                            "badgeColor": "#10B981"
                        },
                        {
                            "title": "QUY MÔ CỤM GPU HUẤN LUYỆN",
                            "legacyLabel": "Cụm Siêu Máy Tính H100",
                            "legacyValue": "16.000+ Chip",
                            "newLabel": "Cụm Thuê H800 Tối Ưu",
                            "newValue": "2.048 Chip",
                            "badgeText": "ĐỘT PHÁ THUẬT TOÁN",
                            "badgeColor": "#38BDF8"
                        }
                    ],
                    "footnote": "Số liệu công bố chính thức · Financial Times & Technical Report"
                }
            }
            if current_img:
                shot["src"] = current_img
            shots.append(shot)

        elif i == n_sent - 1:
            # Outro / Call to Action / Open Discussion
            shot = {
                "id": f"shot-{i}",
                "type": "text_card",
                "in_seconds": start,
                "out_seconds": end,
                "text": s["text"],
                "subtitle": "GÓC NHÌN & BÌNH LUẬN",
            }
            if current_img:
                shot["src"] = current_img
            shots.append(shot)

        else:
            # Dynamic varied cards for deep-dive long-form videos (Shots 7, 8, 9, 10, 11, 12+)
            pattern_idx = (i - 7) % 6
            if pattern_idx == 0:
                # Verification / Expert quote callout
                shot = {
                    "id": f"shot-{i}",
                    "type": "callout",
                    "in_seconds": start,
                    "out_seconds": end,
                    "text": s["text"],
                    "title": "ĐÁNH GIÁ: ĐẠI HỌC STANFORD",
                    "callout_type": "success",
                    "accentColor": "#34D399",
                }
            elif pattern_idx == 1:
                # Open-source / Industry impact Ken Burns
                shot = {
                    "id": f"shot-{i}",
                    "type": "kenburns",
                    "in_seconds": start,
                    "out_seconds": end,
                    "src": current_img or (image_assets[0] if image_assets else None),
                    "stat": "MÃ NGUỒN MỞ",
                    "title": "GIẤY PHÉP THƯƠNG MẠI MIT",
                    "subtitle": s["text"],
                    "scaleFrom": 1.15,
                    "scaleTo": 1.02,
                }
            elif pattern_idx == 2:
                # Distillation Big Stat Card
                shot = {
                    "id": f"shot-{i}",
                    "type": "stat_card",
                    "in_seconds": start,
                    "out_seconds": end,
                    "stat": "1.5B - 70B",
                    "subtitle": "Chưng Cất Mô Hình Chạy Mượt Trên Laptop",
                    "accentColor": "#38BDF8",
                }
            elif pattern_idx == 3:
                # Financial / Market reaction photo
                shot = {
                    "id": f"shot-{i}",
                    "type": "kenburns",
                    "in_seconds": start,
                    "out_seconds": end,
                    "src": current_img or (image_assets[0] if image_assets else None),
                    "stat": "ĐỊA CHẤN",
                    "title": "RUNG LẮC CỔ PHIẾU BÁN DẪN",
                    "subtitle": s["text"],
                    "scaleFrom": 1.04,
                    "scaleTo": 1.18,
                }
            elif pattern_idx == 4:
                # Algorithm shift callout
                shot = {
                    "id": f"shot-{i}",
                    "type": "callout",
                    "in_seconds": start,
                    "out_seconds": end,
                    "text": s["text"],
                    "title": "THUẬT TOÁN ĐÁNH BẠI PHẦN CỨNG",
                    "callout_type": "tip",
                    "accentColor": "#818CF8",
                }
            else:
                # Strategic shift Ken Burns
                shot = {
                    "id": f"shot-{i}",
                    "type": "kenburns",
                    "in_seconds": start,
                    "out_seconds": end,
                    "src": current_img or (image_assets[0] if image_assets else None),
                    "stat": "BƯỚC NGOẶT",
                    "title": "KỶ NGUYÊN MỚI CỦA TRÍ TUỆ",
                    "subtitle": s["text"],
                    "scaleFrom": 1.03,
                    "scaleTo": 1.17,
                }

            if current_img and "src" not in shot:
                shot["src"] = current_img
            shots.append(shot)

    return shots


def render_news_short(
    props_data: dict,
    output_path: Path,
    npx_cmd: str,
) -> None:
    """Invokes Remotion CLI to render the NewsShort composition into an MP4 video."""
    props_tmp = output_path.parent / f"{output_path.stem}_props.json"
    with open(props_tmp, "w", encoding="utf-8") as f:
        json.dump(props_data, f, ensure_ascii=False, indent=2)

    print(f"\n[NewsShort] Rendering composition 'NewsShort' to {output_path}...")
    cmd = [
        npx_cmd,
        "remotion",
        "render",
        "src/index.tsx",
        "NewsShort",
        str(output_path),
        "--props",
        str(props_tmp),
        "--codec",
        "h264",
    ]

    subprocess.run(cmd, cwd=COMPOSER_DIR, check=True)

    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\n[SUCCESS] Video rendered successfully: {output_path} ({size_mb:.2f} MB)")
    else:
        raise RuntimeError("Render finished but output file was not found.")


def extract_text_from_url(url: str) -> tuple[str, str, str]:
    """Fetches a web article and extracts title, main paragraphs and domain."""
    import urllib.request
    from urllib.parse import urlparse

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_m.group(1).strip() if title_m else ""
    title = re.sub(r"\s+", " ", title).split(" - ")[0].split(" | ")[0]

    # Clean HTML
    html = re.sub(r"<(script|style|noscript|header|footer|nav)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, re.IGNORECASE | re.DOTALL)
    clean_paras = []
    for p in paragraphs:
        text = re.sub(r"<[^>]+>", "", p).strip()
        text = re.sub(r"\s+", " ", text)
        if len(text) > 40:
            clean_paras.append(text)

    body = " ".join(clean_paras[:8])
    domain = urlparse(url).netloc.replace("www.", "")
    return title, body, domain


def extract_article_all_images(url: str, slug: str, public_img_dir: Path, max_images: int = 4) -> list[str]:
    """Downloads up to max_images high-resolution reference images from a news article URL."""
    if not url or not url.startswith("http"):
        return []
    try:
        import urllib.request
        from urllib.parse import urlparse
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        found_urls: list[str] = []

        # 1. og:image & twitter:image
        og = re.findall(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if not og:
            og = re.findall(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
        found_urls.extend(og)

        tw = re.findall(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        found_urls.extend(tw)

        # 2. Extract article body img src
        body_imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
        for src in body_imgs:
            if any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                if not any(bad in src.lower() for bad in ["avatar", "icon", "logo", "tracker", "pixel", "badge", "1x1"]):
                    found_urls.append(src)

        # Download distinct valid images
        downloaded = []
        parsed = urlparse(url)
        idx = 0
        for raw_u in found_urls:
            u = raw_u.strip()
            if u.startswith("//"):
                u = "https:" + u
            elif u.startswith("/"):
                u = f"{parsed.scheme}://{parsed.netloc}{u}"
            if not u.startswith("http"):
                continue

            out_file = public_img_dir / f"{slug}_art_{idx}.jpg"
            if out_file.exists():
                downloaded.append(f"images/{out_file.name}")
                idx += 1
                if len(downloaded) >= max_images:
                    break
                continue

            try:
                img_req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(img_req, timeout=8) as img_resp:
                    img_data = img_resp.read()
                if len(img_data) > 12000:
                    out_file.write_bytes(img_data)
                    downloaded.append(f"images/{out_file.name}")
                    print(f"  [Media] Downloaded article reference image: {out_file.name} ({len(img_data)/1024:.1f} KB)")
                    idx += 1
                    if len(downloaded) >= max_images:
                        break
            except Exception:
                continue

        return downloaded
    except Exception as e:
        print(f"  [Media] Could not extract images from {url}: {e}")
        return []


def fetch_entity_photo(entity_query: str, slug: str, prefix: str, public_img_dir: Path) -> str | None:
    """Fetches and optimizes an authentic photo for a named entity from Wikipedia/Wikimedia."""
    import urllib.request
    import urllib.parse
    import json
    headers = {"User-Agent": "AIVideoEditorial/1.0 (contact@internal)"}
    out_file = public_img_dir / f"{slug}_{prefix}.jpg"
    if out_file.exists():
        return f"images/{out_file.name}"

    try:
        search_url = (
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search"
            f"&gsrsearch={urllib.parse.quote(entity_query)}&gsrlimit=4&prop=pageimages"
            f"&piprop=original|thumbnail&pithumbsize=1280"
        )
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                img_src = pdata.get("original", {}).get("source") or pdata.get("thumbnail", {}).get("source")
                if img_src and not img_src.lower().endswith(".svg"):
                    ireq = urllib.request.Request(img_src, headers=headers)
                    with urllib.request.urlopen(ireq, timeout=8) as iresp:
                        idata = iresp.read()
                    if len(idata) > 12000:
                        out_file.write_bytes(idata)
                        try:
                            from PIL import Image
                            im = Image.open(out_file)
                            im.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                            im.convert("RGB").save(out_file, "JPEG", quality=86, optimize=True)
                        except Exception:
                            pass
                        print(f"  [Media] Acquired entity photo ({prefix}): {out_file.name} ({out_file.stat().st_size/1024:.1f} KB)")
                        return f"images/{out_file.name}"
    except Exception as e:
        print(f"  [Media] Entity fetch skipped for '{entity_query}': {e}")
    return None


def fetch_topic_reference_images(topic: str, slug: str, public_img_dir: Path, max_images: int = 3) -> list[str]:
    """Fetches high-quality authentic reference photos for the topic from Wikipedia/Wikimedia API."""
    import urllib.request
    import urllib.parse
    import json
    headers = {"User-Agent": "AIVideoEditorial/1.0 (contact@internal)"}
    downloaded = []

    # Clean keywords for search
    clean_q = re.sub(r"[^\w\s]", "", topic).strip()
    words = clean_q.split()
    target_q = " ".join(words[:4]) if len(words) >= 4 else clean_q

    try:
        search_url = (
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search"
            f"&gsrsearch={urllib.parse.quote(target_q)}&gsrlimit=4&prop=pageimages"
            f"&piprop=original|thumbnail&pithumbsize=1280"
        )
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=7) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            idx = 0
            for pid, pdata in pages.items():
                img_src = None
                if "original" in pdata and pdata["original"].get("source"):
                    img_src = pdata["original"]["source"]
                elif "thumbnail" in pdata and pdata["thumbnail"].get("source"):
                    img_src = pdata["thumbnail"]["source"]

                if img_src and not img_src.endswith(".svg"):
                    out_file = public_img_dir / f"{slug}_wiki_{idx}.jpg"
                    try:
                        ireq = urllib.request.Request(img_src, headers=headers)
                        with urllib.request.urlopen(ireq, timeout=8) as iresp:
                            idata = iresp.read()
                        if len(idata) > 15000:
                            out_file.write_bytes(idata)
                            try:
                                from PIL import Image
                                im = Image.open(out_file)
                                im.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                                im.convert("RGB").save(out_file, "JPEG", quality=86, optimize=True)
                            except Exception:
                                pass
                            downloaded.append(f"images/{out_file.name}")
                            print(f"  [Media] Downloaded topic reference photo: {out_file.name} ({out_file.stat().st_size/1024:.1f} KB)")
                            idx += 1
                            if len(downloaded) >= max_images:
                                break
                    except Exception:
                        continue
    except Exception as e:
        print(f"  [Media] Topic reference image search skipped: {e}")

    return downloaded


def acquire_news_images(slug: str, url: str | None, headline: str, summary: str) -> list[str]:
    """
    Acquires authentic, high-resolution thematic reference visual assets:
    1. Direct hero & body photos from the news article (if URL provided).
    2. Specific named entity reference photos (DeepSeek, OpenAI, Stanford, Supercomputer, Nvidia).
    3. Topic search via Wikipedia API with automatic PIL optimization.
    4. Curated high-resolution fallback.
    Returns list of distinct relative paths for Remotion (e.g. ['images/news_123_ref_0.jpg', ...]).
    """
    public_img_dir = COMPOSER_DIR / "public" / "images"
    public_img_dir.mkdir(parents=True, exist_ok=True)

    assets: list[str] = []
    combined_text = (headline + " " + summary).lower()

    # 1. Scrape all article images if URL available
    if url:
        art_imgs = extract_article_all_images(url, slug, public_img_dir, max_images=3)
        assets.extend(art_imgs)

    # 2. Entity-based thematic photos
    entity_rules = [
        (["deepseek"], "DeepSeek (AI)", "deepseek"),
        (["stanford"], "Stanford University building", "stanford"),
        (["openai", "chatgpt"], "OpenAI", "openai"),
        (["gpu", "siêu máy tính", "supercomputer", "ngân sách", "chi phí", "cluster"], "Supercomputer", "supercomputer"),
        (["nvidia", "thị trường"], "Nvidia", "nvidia"),
        (["anthropic", "claude"], "Anthropic", "anthropic"),
        (["google", "gemini"], "Googleplex", "google"),
    ]

    for keywords, search_q, prefix in entity_rules:
        if any(kw in combined_text for kw in keywords):
            p = fetch_entity_photo(search_q, slug, prefix, public_img_dir)
            if p and p not in assets:
                assets.append(p)
            if len(assets) >= 4:
                break

    # 3. Fallback topic search if fewer than 3 images
    if len(assets) < 3:
        search_term = headline
        for key in ["DeepSeek", "OpenAI", "Anthropic", "Claude", "NVIDIA", "ChatGPT", "Supercomputer"]:
            if key.lower() in combined_text:
                search_term = f"{key} technology"
                break
        wiki_imgs = fetch_topic_reference_images(search_term, slug, public_img_dir, max_images=3 - len(assets))
        for wi in wiki_imgs:
            if wi not in assets:
                assets.append(wi)

    # 4. Fallback to existing high-res tech visual
    if not assets:
        sample_img = ROOT_DIR / "output" / "test_agent_ai.png"
        if sample_img.exists():
            target_fb = public_img_dir / f"{slug}_fallback.png"
            shutil.copy2(sample_img, target_fb)
            assets.append(f"images/{slug}_fallback.png")

    # If only 1 image found, duplicate for scene variety
    if len(assets) == 1:
        assets.append(assets[0])

    return assets


def main():
    parser = argparse.ArgumentParser(description="Generate seamless AI News Shorts (Hinton Style)")
    parser.add_argument("--url", type=str, help="URL of the news article to summarize")
    parser.add_argument("--text", type=str, help="Raw script text or path to .txt file")
    parser.add_argument("--title", type=str, default="", help="Main 2-line headline (defaults to article title or preset)")
    parser.add_argument("--tag", type=str, default="🔥 TIN AI NÓNG", help="Category tag pill")
    parser.add_argument("--source", type=str, default="", help="Source attribution (e.g. Nguồn: The Verge)")
    parser.add_argument("--voice", type=str, default="vi-VN-NamMinhNeural", help="Edge-TTS voice (NamMinh or HoaiMy)")
    parser.add_argument("--rate", type=str, default="+20%", help="Cadence rate (+15%%, +20%%)")
    parser.add_argument("--meta", type=str, default="", help="Path to JSON metadata containing structured editorial info")
    parser.add_argument("--output", type=str, help="Output MP4 file path")
    parser.add_argument("--props-only", action="store_true", help="Only generate audio and props JSON without rendering")

    args = parser.parse_args()

    # Load editorial metadata if provided
    meta_data = {}
    if args.meta and os.path.isfile(args.meta):
        try:
            with open(args.meta, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load meta JSON {args.meta}: {e}")

    # Determine script content
    script_text = ""
    headline_title = args.title
    source_label = args.source

    if not headline_title and meta_data.get("headline"):
        headline_title = meta_data["headline"]
    elif not headline_title and meta_data.get("headline_title"):
        headline_title = meta_data["headline_title"]

    if not source_label and meta_data.get("source_pill"):
        source_label = meta_data["source_pill"]
    elif not source_label and meta_data.get("source"):
        source_label = f"Nguồn: {meta_data['source']}"

    if args.url:
        print(f"[Fetching] Reading article from {args.url}...")
        art_title, art_body, domain = extract_text_from_url(args.url)
        if not headline_title:
            headline_title = art_title[:45].upper()
        if not source_label:
            source_label = f"Nguồn: {domain}"
        # Use extracted body (or if empty, fallback)
        script_text = art_body if art_body else art_title
    elif args.text:
        if os.path.isfile(args.text):
            with open(args.text, "r", encoding="utf-8") as f:
                script_text = f.read().strip()
        else:
            script_text = args.text.strip()
    else:
        # Default test script matching 260 syllables
        script_text = (
            "OpenAI vừa chính thức phát hành bản cập nhật mới mang tính đột phá. "
            "Mô hình này giúp tăng tốc độ xử lý dữ liệu lên gấp ba lần so với phiên bản trước. "
            "Điểm đáng chú ý nhất là khả năng suy luận logic đạt độ chính xác trên tám mươi phần trăm. "
            "Người dùng hiện đã có thể trải nghiệm hoàn toàn miễn phí trên toàn thế giới. "
            "Bạn đánh giá thế nào về bước tiến này của trí tuệ nhân tạo, hãy bình luận bên dưới nhé."
        )

    if not headline_title:
        headline_title = "BƯỚC TIẾN MỚI CỦA TRÍ TUỆ NHÂN TẠO"
    if not source_label:
        source_label = "Nguồn: Tin Công Nghệ"

    slug = f"news_{int(time.time())}"
    job_dir = OUTPUT_DIR / slug
    job_dir.mkdir(parents=True, exist_ok=True)

    output_mp4 = Path(args.output) if args.output else job_dir / f"{slug}.mp4"
    voice_file = job_dir / "voice.mp3"

    print(f"==================================================")
    print(f"🎬 HINTON-STYLE AI NEWS SHORT PIPELINE")
    print(f"Tag:     {args.tag}")
    print(f"Title:   {headline_title}")
    print(f"Source:  {source_label}")
    print(f"Voice:   {args.voice} ({args.rate})")
    print(f"Script:  {script_text[:80]}...")
    print(f"Output:  {output_mp4}")
    print(f"==================================================")

    # 1. Synthesize audio & extract word timestamps
    print("\n[Step 1/3] Generating voiceover and word-level timestamps...")
    total_dur, sentences, words = asyncio.run(
        generate_voice_and_timing(
            normalize_vietnamese_numbers(script_text),
            args.voice,
            args.rate,
            voice_file,
        )
    )
    print(f"  Voice duration: {total_dur:.2f}s across {len(sentences)} sentences and {len(words)} words.")

    # 2. Acquire visual media & plan cuts aligned with speech
    print("\n[Step 2/3] Acquiring visual media assets and planning cinematic visual cuts...")
    article_link = args.url or meta_data.get("link")
    image_assets = acquire_news_images(slug, article_link, headline_title, script_text)
    print(f"  Acquired {len(image_assets)} visual media assets: {image_assets}")
    shots = plan_news_shots(sentences, total_dur, meta=meta_data, image_assets=image_assets)
    print(f"  Generated {len(shots)} rhythmic shots.")

    # Copy voice file to remotion-composer/public/audio for reliable Remotion rendering
    public_audio_dir = COMPOSER_DIR / "public" / "audio"
    public_audio_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(voice_file, public_audio_dir / f"{slug}.mp3")

    # Build Remotion Props
    props_payload = {
        "headlineTag": args.tag,
        "headlineTitle": headline_title,
        "sourceText": source_label,
        "shots": shots,
        "captions": words,
        "audio": {
            "narration": {
                "src": f"audio/{slug}.mp3",
                "volume": 1.0,
            },
            "music": {
                "src": "audio/bgm_tech.wav",
                "volume": 0.08,
                "fadeInSeconds": 1.5,
                "fadeOutSeconds": 2.5,
                "loop": True,
            }
        },
        "theme": {
            "primaryColor": "#0F172A",
            "accentColor": "#FFE600",
        },
    }

    props_path = job_dir / "props.json"
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props_payload, f, ensure_ascii=False, indent=2)
    print(f"  Saved props to {props_path}")

    if args.props_only:
        print("[Done] Props generated. Skipping render.")
        return

    # 3. Render MP4
    print("\n[Step 3/3] Assembling and rendering 1080x1920 30fps MP4 via Remotion...")
    npx_cmd = shutil.which("npx.cmd") or shutil.which("npx") or "npx"
    render_news_short(props_payload, output_mp4, npx_cmd)

    print(f"\n🎉 HOÀN THÀNH!")
    print(f"File video:  {output_mp4}")
    print(f"File voice:  {voice_file}")
    print(f"File props:  {props_path}")


if __name__ == "__main__":
    main()
