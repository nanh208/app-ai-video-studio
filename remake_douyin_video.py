"""
Douyin/TikTok Video Remake Pipeline (Hinton Bot2B Style)
Converts raw footage (Douyin, TikTok, YouTube, News Screenshots, Photos)
into high-retention localized Vietnamese shorts:
- Mutes original audio & replaces with sharp Vietnamese voiceover (+20% rate)
- Generates signature 2-tier Big Punch Text (White + Yellow with thick black stroke)
- Giant Stat Center Punches (e.g. 22,9 TRIỆU, 110 TỶ, $2.5M)
- Inserts Yellow Highlight Banners on key terms
- Overlays word-level karaoke subtitles in safe zone
- Dynamic Multi-Source Attribution Pill (updates per clip: Tân Hoa Xã, YouTube, Douyin...)
- Multi-Source B-Roll mixing (videos, article screenshots, letterbox blurred 16:9)
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
import time
from pathlib import Path

import edge_tts

ROOT_DIR = Path(__file__).resolve().parent
OPENMONTAGE_DIR = ROOT_DIR / "OpenMontage"
COMPOSER_DIR = OPENMONTAGE_DIR / "remotion-composer"
OUTPUT_DIR = ROOT_DIR / "output"


def sanitize_script_for_tts(text: str) -> str:
    t = text
    t = re.sub(r"(?:Chương|Phần)\s*\d+\s*:\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"[—–]", ", ", t)
    t = re.sub(r"[\(\)]", " ", t)
    t = re.sub(r"(\d+[\.,]?\d*)\s*%", r"\1 phần trăm", t)
    t = re.sub(r"\$\s*(\d+[\.,]?\d*)", r"\1 đô la Mỹ", t)
    t = re.sub(r"(\d+)\s*USD", r"\1 đô la Mỹ", t)
    t = t.replace("&", " và ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def parse_vtt_subtitles(vtt_path: Path) -> list[dict]:
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


async def generate_voice(script_text: str, voice: str, rate: str, out_path: Path):
    cleaned_text = sanitize_script_for_tts(script_text)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    vtt_path = out_path.with_suffix(".vtt")
    txt_temp = out_path.with_suffix(".txt")
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
            "--write-media", str(out_path),
            "--write-subtitles", str(vtt_path),
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=120)
        if res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 5000:
            sentences = parse_vtt_subtitles(vtt_path)
            print(f"  [TTS] Synthesized via CLI ({out_path.stat().st_size/1024:.1f} KB, {len(sentences)} sentences)", flush=True)
    except Exception as e:
        print(f"  [TTS] CLI attempt failed ({e}), falling back to Python API...", flush=True)

    # 2. Fallback to Python API
    if not sentences:
        comm = edge_tts.Communicate(cleaned_text, voice, rate=rate)
        audio_data = bytearray()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                s_start = chunk["offset"] / 10_000_000.0
                s_dur = chunk["duration"] / 10_000_000.0
                sentences.append({
                    "text": chunk["text"],
                    "start": s_start,
                    "end": s_start + s_dur,
                    "duration": s_dur,
                })
        with open(out_path, "wb") as f:
            f.write(audio_data)

    words = []
    for sent in sentences:
        tokens = [w.strip() for w in sent["text"].split() if w.strip()]
        if not tokens:
            continue
        total_chars = sum(len(w) for w in tokens)
        cur_t = sent["start"]
        for idx, w in enumerate(tokens):
            w_dur = sent["duration"] * (max(1, len(w)) / max(1, total_chars))
            words.append({
                "word": w,
                "startMs": int(cur_t * 1000),
                "endMs": int((cur_t + w_dur) * 1000),
                "pageBreakAfter": (idx == len(tokens) - 1),
            })
            cur_t += w_dur

    return (sentences[-1]["end"] if sentences else 0.0), sentences, words


def auto_detect_visual_elements(sentences: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Scans script sentences for numbers and salient phrases to generate:
    1. 2-tier punch texts (White + Yellow) for hooks & pivots
    2. Giant Stat Center Punches (e.g. 22,9 TRIỆU, 110 TỶ, 70%)
    3. Yellow highlight banners for trending concepts
    """
    punches = []
    stat_punches = []
    banners = []

    # Regex for prominent numbers/percentages/metrics
    stat_regex = re.compile(
        r"(\d+[\.,]?\d*\s*(?:triệu|tỷ|nghìn|đô|usd|\$|%|lần|vali))",
        re.IGNORECASE
    )

    for idx, s in enumerate(sentences):
        text = s["text"]
        start = s["start"]
        end = s["end"]
        dur = end - start

        # Check for big stats
        stat_match = stat_regex.search(text)
        if stat_match and len(stat_punches) < 4:
            matched_stat = stat_match.group(1).strip()
            # Context label: remaining words in sentence or generic
            label_text = text.replace(matched_stat, "").strip()
            # Trim label to 2-4 key words
            label_words = [w for w in label_text.split() if len(w) > 1 and w.lower() not in ["là", "có", "được", "và", "nhưng", "tới"]]
            clean_label = " ".join(label_words[:4]) if label_words else ""

            stat_punches.append({
                "in_seconds": round(start + 0.1, 2),
                "out_seconds": round(min(end, start + 2.6), 2),
                "stat": matched_stat.upper(),
                "label": clean_label.upper() if clean_label else None,
            })
        elif idx == 0 and len(punches) == 0:
            # Sentence 1 Hook Punch
            words = text.split()
            mid = max(1, len(words) // 2)
            punches.append({
                "in_seconds": round(start + 0.1, 2),
                "out_seconds": round(min(end, start + 3.2), 2),
                "line1": " ".join(words[:mid]).upper(),
                "line2": " ".join(words[mid:mid+5]).upper(),
            })
        elif len(banners) < 3 and len(text) > 20:
            words = text.split()
            short_phrase = " ".join(words[:4])
            banners.append({
                "in_seconds": round(start + 0.15, 2),
                "out_seconds": round(min(end, start + 2.8), 2),
                "text": short_phrase.upper(),
            })

    return punches, stat_punches, banners


def infer_media_source_pill(file_name: str, fallback: str) -> str:
    """Infers an authentic attribution source pill from the media filename."""
    lower = file_name.lower()
    if "tan_hoa_xa" in lower or "xinhua" in lower or "news_cn" in lower:
        return "Nguồn: Tân Hoa Xã"
    if "phuong_hoang" in lower or "ifeng" in lower:
        return "Nguồn: Phượng Hoàng"
    if "youtube" in lower:
        parts = file_name.split("_")
        return f"Nguồn: YouTube"
    if "douyin" in lower:
        return "Nguồn: Douyin"
    if "tiktok" in lower:
        return "Nguồn: TikTok"
    if "dantri" in lower:
        return "Nguồn: Báo Dân Trí"
    if "vnexpress" in lower:
        return "Nguồn: VnExpress"
    if "reuters" in lower:
        return "Nguồn: Reuters"
    return fallback


def build_multi_source_timeline(
    media_paths: list[Path],
    sentences: list[dict],
    total_dur: float,
    public_vid_dir: Path,
    public_img_dir: Path,
    slug: str,
    default_source: str
) -> list[dict]:
    """
    Builds an alternating multi-source visual timeline:
    - Videos (B-roll, unboxing, talking head)
    - Images (article screenshots, mockups, entity photos)
    - Dynamic source pill per clip
    - Automatic letterbox blur for 16:9 media in vertical 9:16
    """
    processed_items = []
    for idx, p in enumerate(media_paths):
        ext = p.suffix.lower()
        is_img = ext in [".jpg", ".jpeg", ".png", ".webp"]
        target_name = f"{slug}_ref_{idx}_{p.name}"

        if is_img:
            shutil.copy2(p, public_img_dir / target_name)
            src_path = f"images/{target_name}"
            m_type = "image"
        else:
            shutil.copy2(p, public_vid_dir / target_name)
            src_path = f"videos/{target_name}"
            m_type = "video"

        # Check aspect ratio if possible using ffprobe
        is_horizontal = False
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "json", str(p)],
                capture_output=True, text=True
            )
            if probe.returncode == 0:
                p_data = json.loads(probe.stdout)
                streams = p_data.get("streams", [])
                if streams:
                    w = int(streams[0].get("width", 1080))
                    h = int(streams[0].get("height", 1920))
                    if w > h:
                        is_horizontal = True
        except Exception:
            pass

        # Source pill deduction
        clip_source = infer_media_source_pill(p.name, default_source)

        processed_items.append({
            "src": src_path,
            "mediaType": m_type,
            "is_horizontal": is_horizontal,
            "source": clip_source,
            "filename": p.name,
        })

    clips = []
    num_items = len(processed_items)
    if not num_items:
        return clips

    if sentences and len(sentences) > 1:
        for idx, s in enumerate(sentences):
            start = s["start"]
            end = s["end"]
            if idx == len(sentences) - 1:
                end = max(end, total_dur + 0.3)

            item = processed_items[idx % num_items]
            start_at = (idx * 2.8) % 15.0

            # Decide layout: horizontal videos/images get letterbox blur
            layout = "letterbox_blur" if item["is_horizontal"] else "fullscreen"
            news_domain = None
            if "article" in item["filename"].lower() or "news" in item["filename"].lower():
                if "tan_hoa_xa" in item["filename"].lower():
                    news_domain = "news.cn"
                    layout = "news_mockup"
                elif "phuong_hoang" in item["filename"].lower():
                    news_domain = "ifeng.com"
                    layout = "news_mockup"

            clips.append({
                "id": f"clip-{idx}",
                "src": item["src"],
                "mediaType": item["mediaType"],
                "in_seconds": round(start, 2),
                "out_seconds": round(end, 2),
                "startAt": round(start_at, 2),
                "layout": layout,
                "source": item["source"],
                "newsDomain": news_domain,
            })
    else:
        t = 0.0
        idx = 0
        while t < total_dur:
            out_t = min(t + 3.0, total_dur)
            item = processed_items[idx % num_items]
            layout = "letterbox_blur" if item["is_horizontal"] else "fullscreen"
            clips.append({
                "id": f"clip-{idx}",
                "src": item["src"],
                "mediaType": item["mediaType"],
                "in_seconds": round(t, 2),
                "out_seconds": round(out_t, 2),
                "startAt": round((idx * 2.5) % 15.0, 2),
                "layout": layout,
                "source": item["source"],
            })
            t = out_t
            idx += 1

    return clips


def main():
    parser = argparse.ArgumentParser(description="Douyin/TikTok Style Video Remake (Learned Formula)")
    parser.add_argument("--video", type=str, default="", help="Input video file path or comma-separated list")
    parser.add_argument("--media", type=str, default="", help="Comma-separated list or directory of mixed media (videos and images)")
    parser.add_argument("--text", type=str, required=True, help="Vietnamese script or path to .txt file")
    parser.add_argument("--source", type=str, default="Nguồn: Douyin", help="Default source credit pill")
    parser.add_argument("--voice", type=str, default="vi-VN-NamMinhNeural", help="Edge-TTS voice")
    parser.add_argument("--rate", type=str, default="+20%", help="Voice speed rate")
    parser.add_argument("--punches", type=str, default=None, help="JSON file or string for punch texts")
    parser.add_argument("--stat-punches", type=str, default=None, help="JSON file or string for stat punches")
    parser.add_argument("--banners", type=str, default=None, help="JSON file or string for yellow banners")
    parser.add_argument("--output", type=str, help="Output MP4 path")

    args = parser.parse_args()

    # Collect media paths (videos and images)
    media_paths: list[Path] = []

    raw_inputs = []
    if args.media:
        raw_inputs.extend([p.strip() for p in args.media.split(",") if p.strip()])
    if args.video:
        raw_inputs.extend([p.strip() for p in args.video.split(",") if p.strip()])

    for p_str in raw_inputs:
        p = Path(p_str).resolve()
        if p.is_dir():
            for ext in ("*.mp4", "*.mov", "*.webm", "*.jpg", "*.jpeg", "*.png", "*.webp"):
                media_paths.extend(sorted(p.glob(ext)))
        elif p.is_file():
            media_paths.append(p)

    if not media_paths:
        ref_dir = ROOT_DIR / "reference_videos"
        if ref_dir.is_dir():
            media_paths = sorted(ref_dir.glob("*.mp4"))

    if not media_paths:
        # Fallback to local sample videos
        for s in ("sample_douyin_video01.mp4", "sample_drive_learning.mp4", "sample_douyin_video02_full.mp4", "sample_v03.mp4"):
            sp = ROOT_DIR / s
            if sp.exists() and sp not in media_paths:
                media_paths.append(sp)

    if not media_paths:
        raise FileNotFoundError("Không tìm thấy tư liệu media (video/ảnh) nào để dựng video!")

    script_text = ""
    if os.path.isfile(args.text):
        with open(args.text, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
    else:
        script_text = args.text.strip()

    slug = f"douyin_remake_{int(time.time())}"
    job_dir = OUTPUT_DIR / slug
    job_dir.mkdir(parents=True, exist_ok=True)

    output_mp4 = Path(args.output) if args.output else job_dir / f"{slug}.mp4"
    voice_file = job_dir / "voice.mp3"

    print("==================================================")
    print("🎬 ADVANCED DOUYIN / SHORT NEWS VIDEO ENGINE")
    print(f"Media count:  {len(media_paths)} assets (videos & images)")
    for i, mp in enumerate(media_paths[:6]):
        print(f"  - [{i+1}] {mp.name}")
    if len(media_paths) > 6:
        print(f"  ... và thêm {len(media_paths) - 6} tư liệu khác")
    print(f"Default Src:  {args.source}")
    print(f"Script:       {script_text[:80]}...")
    print(f"Output:       {output_mp4}")
    print("==================================================")

    # 1. Prepare public directories
    public_vid_dir = COMPOSER_DIR / "public" / "videos"
    public_img_dir = COMPOSER_DIR / "public" / "images"
    public_aud_dir = COMPOSER_DIR / "public" / "audio"
    public_vid_dir.mkdir(parents=True, exist_ok=True)
    public_img_dir.mkdir(parents=True, exist_ok=True)
    public_aud_dir.mkdir(parents=True, exist_ok=True)

    # 2. Synthesize audio & get word timestamps
    print("\n[Step 1/3] Synthesizing Vietnamese voiceover and word timing...")
    dur, sentences, words = asyncio.run(
        generate_voice(script_text, args.voice, args.rate, voice_file)
    )
    shutil.copy2(voice_file, public_aud_dir / f"{slug}.mp3")
    print(f"  Voice duration: {dur:.2f}s, {len(words)} words.")

    # 3. Build multi-source timeline
    print("\n[Step 2/3] Assembling multi-source timeline & kinetic typography...")
    video_clips = build_multi_source_timeline(
        media_paths, sentences, dur, public_vid_dir, public_img_dir, slug, args.source
    )
    print(f"  Built Multi-Source Montage with {len(video_clips)} dynamic cuts!")

    # 4. Auto detect visual punches, stat punches & highlight banners
    auto_p, auto_stats, auto_b = auto_detect_visual_elements(sentences)

    punches = auto_p
    if args.punches:
        if os.path.isfile(args.punches):
            with open(args.punches, "r", encoding="utf-8") as f:
                punches = json.load(f)
        else:
            punches = json.loads(args.punches)

    stat_punches = auto_stats
    if args.stat_punches:
        if os.path.isfile(args.stat_punches):
            with open(args.stat_punches, "r", encoding="utf-8") as f:
                stat_punches = json.load(f)
        else:
            stat_punches = json.loads(args.stat_punches)

    banners = auto_b
    if args.banners:
        if os.path.isfile(args.banners):
            with open(args.banners, "r", encoding="utf-8") as f:
                banners = json.load(f)
        else:
            banners = json.loads(args.banners)

    print(f"  Visual elements: {len(punches)} punch popups, {len(stat_punches)} giant stat punches, {len(banners)} banners.")

    props_payload = {
        "videoSrc": "",
        "videoClips": video_clips,
        "muteOriginalVideo": True,
        "voiceSrc": f"audio/{slug}.mp3",
        "voiceVolume": 1.0,
        "sourceText": args.source,
        "punchTexts": punches,
        "statPunches": stat_punches,
        "yellowBanners": banners,
        "captions": words,
    }

    props_file = job_dir / "props.json"
    with open(props_file, "w", encoding="utf-8") as f:
        json.dump(props_payload, f, ensure_ascii=False, indent=2)

    # 5. Render MP4
    print("\n[Step 3/3] Rendering 1080x1920 MP4 via Remotion...")
    npx_cmd = shutil.which("npx.cmd") or shutil.which("npx") or "npx"
    cmd = [
        npx_cmd,
        "remotion",
        "render",
        "src/index.tsx",
        "DouyinRemake",
        str(output_mp4),
        "--props",
        str(props_file),
        "--codec",
        "h264",
    ]
    subprocess.run(cmd, cwd=COMPOSER_DIR, check=True)

    print("\n🎉 HOÀN THÀNH XUẤT SẮC!")
    print(f"File video: {output_mp4} ({output_mp4.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
