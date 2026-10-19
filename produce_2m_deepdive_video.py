"""
2-Minute Deep-Dive Video Producer (China Haul Documentary Edition)
Applies 100% of the breakthroughs learned from the reference video:
- Exact Duration: ~130 seconds (> 2 minutes)
- In-depth economic, cultural, and supply chain analysis across 5 acts
- 24 dynamic multi-source B-roll shots (Douyin, Xinhua, Phoenix Media, YouTube)
- Dynamic per-clip source attribution pills
- 5 Giant Stat Center Punches (110 TRIỆU, 22,9 TRIỆU, RẺ HƠN 70%, TIẾT KIỆM $1.000, 144 GIỜ)
- 3 Kinetic Typography Punches (VALI RỖNG SANG, BÍ MẬT KINH TẾ, BÀI HỌC VĨ MÔ)
- 7 Yellow Category Banners for clear thematic pacing
- News mockups with browser chrome (news.cn, ifeng.com)
- Letterbox Gaussian blur for 16:9 YouTuber footage in 9:16 vertical canvas
- Word-level karaoke captions with active gold pop (#FFE600) in safe zone (bottom 200px)
- Tech groove background music with voice ducking
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
OPENMONTAGE_DIR = ROOT_DIR / "OpenMontage"
COMPOSER_DIR = OPENMONTAGE_DIR / "remotion-composer"
OUTPUT_DIR = ROOT_DIR / "output"
REF_DIR = ROOT_DIR / "reference_videos"

SCRIPT_TEXT = """Mang một chiếc vali rỗng khi đi, nhưng xách về tới ba chiếc vali chật ních đồ!
Trào lưu mang tên China Haul không đơn thuần là một hiện tượng mạng xã hội nhất thời, mà đang thực sự tái định hình bản đồ du lịch mua sắm của thế hệ trẻ toàn cầu.
Từ các cơ quan báo chí chính thống như Tân Hoa Xã, Nhân Dân Nhật Báo cho tới các chuyên trang phân tích kinh tế của Phượng Hoàng Media, làn sóng này liên tục chiếm sóng trang nhất.
Chỉ tính riêng trên nền tảng TikTok, các video gắn hashtag China Haul đã vượt ngưỡng 110 triệu lượt xem, thu hút hơn 22,9 triệu lượt tương tác chỉ trong một thời gian ngắn.
Hàng loạt video đập hộp đồ chơi nghệ thuật, phụ kiện thời trang và thiết bị công nghệ thông minh đang gây sốt trên YouTube và Instagram.
Vậy điều gì đã biến các khu chợ và trung tâm thương mại lớn tại Thượng Hải, Thâm Quyến và Quảng Châu thành điểm nóng săn hàng của du khách quốc tế?
Bí mật nằm ở sức mạnh vượt trội của mô hình chuỗi cung ứng tận xưởng.
Khi mua sắm trực tiếp tại các công xưởng nội địa, người tiêu dùng có thể tiếp cận mức giá xuất xưởng, rẻ hơn từ 60 đến 70 phần trăm so với mua tại các cửa hàng ở New York hay London.
Từ thời trang may mặc, đồ chơi độc bản cho tới đồ gia dụng cao cấp, mức chênh lệch giá lớn đến mức đủ để bù đắp hoàn toàn chi phí vé máy bay khứ hồi và ăn ở.
Nhiều du khách như YouTuber Elliot Page đã không giấu nổi sự kinh ngạc khi tiết kiệm được cả nghìn đô la ngay trong chuyến đi ngắn ngày của mình.
Đặc biệt, đòn bẩy chiến lược từ chính sách miễn thị thực quá cảnh 144 giờ đã tạo ra cú hích khổng lồ, biến các chuyến bay trung chuyển thành những tour săn hàng quy mô lớn.
Tuy nhiên, sự bùng nổ này cũng làm dấy lên những cuộc tranh luận đa chiều gay gắt trong cộng đồng quốc tế.
Một bộ phận lo ngại về chủ nghĩa tiêu dùng quá mức và lượng rác thải bao bì gia tăng, trong khi số khác lại coi đây là bài học thực tế sống động cho ngành bán lẻ truyền thống toàn cầu.
Khi khoảng cách giữa nơi sản xuất và người tiêu dùng dần bị xóa bỏ, người tiêu dùng thông thái sẽ chủ động tìm đến tận nguồn hàng giá gốc.
Rõ ràng, China Haul không chỉ là câu chuyện mua sắm cá nhân, mà là minh chứng cho sức hút thương mại to lớn của một nền sản xuất hàng đầu thế giới.
Còn bạn, bạn nghĩ sao về xu hướng du lịch kết hợp săn hàng giá xưởng này? Hãy để lại bình luận để cùng nhau phân tích nhé!"""


def sanitize_for_tts(t: str) -> str:
    t = t.replace('$', ' đô la ')
    t = t.replace('%', ' phần trăm ')
    t = t.replace('—', ', ')
    t = t.replace('–', ', ')
    return t


def parse_vtt(vtt_path: Path) -> list[dict]:
    if not vtt_path.exists():
        return []
    content = vtt_path.read_text(encoding="utf-8")
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


def main():
    slug = f"china_haul_deepdive_2m_{int(time.time())}"
    job_dir = OUTPUT_DIR / slug
    job_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = OUTPUT_DIR / f"{slug}.mp4"

    print("==================================================")
    print("🎬 2-MINUTE IN-DEPTH DOCUMENTARY VIDEO PRODUCER")
    print(f"Target duration: ~130s (> 2 minutes)")
    print(f"Script words:    {len(SCRIPT_TEXT.split())} words")
    print(f"Output MP4:      {out_mp4}")
    print("==================================================")

    # 1. Voiceover Synthesis (Reuse if already synthesized or generate fresh)
    voice_file = job_dir / "voice.mp3"
    vtt_file = job_dir / "voice.vtt"
    txt_file = job_dir / "voice.txt"
    txt_file.write_text(sanitize_for_tts(SCRIPT_TEXT), encoding="utf-8")

    pre_mp3 = ROOT_DIR / "voice_sanitized.mp3"
    pre_vtt = ROOT_DIR / "voice_sanitized.vtt"

    if pre_mp3.exists() and pre_vtt.exists() and pre_mp3.stat().st_size > 100000:
        print("\n[Step 1/4] Using pre-synthesized high-fidelity Vietnamese voiceover...")
        shutil.copy2(pre_mp3, voice_file)
        shutil.copy2(pre_vtt, vtt_file)
    else:
        print("\n[Step 1/4] Synthesizing 2-minute Vietnamese voiceover with Edge-TTS...")
        edge_cli = OPENMONTAGE_DIR / ".venv" / "Scripts" / "edge-tts.exe"
        if not edge_cli.exists():
            edge_cli = Path(shutil.which("edge-tts") or "edge-tts")

        cmd = [
            str(edge_cli),
            "--voice", "vi-VN-NamMinhNeural",
            "--rate", "+0%",
            "--file", str(txt_file),
            "--write-media", str(voice_file),
            "--write-subtitles", str(vtt_file),
        ]
        subprocess.run(cmd, check=True)

    sentences = parse_vtt(vtt_file)
    total_dur = sentences[-1]["end"] if sentences else 130.0
    print(f"  Voice duration: {total_dur:.2f} seconds ({len(sentences)} analytical sentences)!")

    # 2. Build word-level karaoke captions in safe zone
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

    # 3. Copy audio and media to Remotion public dir
    public_aud_dir = COMPOSER_DIR / "public" / "audio"
    public_vid_dir = COMPOSER_DIR / "public" / "videos"
    public_img_dir = COMPOSER_DIR / "public" / "images"
    public_aud_dir.mkdir(parents=True, exist_ok=True)
    public_vid_dir.mkdir(parents=True, exist_ok=True)
    public_img_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(voice_file, public_aud_dir / f"{slug}.mp3")

    bgm_rel = ""
    candidate_bgm = COMPOSER_DIR / "public" / "audio" / "bgm_tech.wav"
    if candidate_bgm.exists():
        bgm_rel = "audio/bgm_tech.wav"

    # 4. Assemble Multi-Source Assets & 24 Dynamic Cuts
    print("\n[Step 2/4] Assembling 24-shot Multi-Source B-Roll timeline...")

    # Define the 24 shots matching narrative flow
    shot_definitions = [
        {"file": "douyin_pack_01.mp4", "source": "Nguồn: Douyin - #ChinaHaul", "type": "video", "layout": "fullscreen", "in": 0.0, "out": 5.5, "startAt": 0.0},
        {"file": "douyin_pack_02.mp4", "source": "Nguồn: Douyin - #ChinaHaul", "type": "video", "layout": "fullscreen", "in": 5.5, "out": 14.5, "startAt": 2.0},
        {"file": "xinhua_headline.jpg", "source": "Nguồn: Tân Hoa Xã", "type": "image", "layout": "news_mockup", "domain": "news.cn", "in": 14.5, "out": 19.5, "startAt": 0.0},
        {"file": "phoenix_article_top.jpg", "source": "Nguồn: Phượng Hoàng Media", "type": "image", "layout": "news_mockup", "domain": "ifeng.com", "in": 19.5, "out": 24.2, "startAt": 0.0},
        {"file": "douyin_pack_01.mp4", "source": "Nguồn: Douyin - #ChinaHaul", "type": "video", "layout": "fullscreen", "in": 24.2, "out": 29.5, "startAt": 6.0},
        {"file": "douyin_pack_02.mp4", "source": "Nguồn: Douyin - #ChinaHaul", "type": "video", "layout": "fullscreen", "in": 29.5, "out": 34.5, "startAt": 7.0},
        {"file": "youtube_lego_unboxing.mp4", "source": "Nguồn: YouTube - homeysbee", "type": "video", "layout": "letterbox_blur", "in": 34.5, "out": 38.5, "startAt": 1.5},
        {"file": "youtube_home_haul.mp4", "source": "Nguồn: YouTube - homeysbee", "type": "video", "layout": "letterbox_blur", "in": 38.5, "out": 42.1, "startAt": 3.0},
        {"file": "douyin_pack_01.mp4", "source": "Nguồn: Douyin - #ChinaHaul", "type": "video", "layout": "fullscreen", "in": 42.1, "out": 49.8, "startAt": 11.0},
        {"file": "phoenix_article_body.jpg", "source": "Nguồn: Phượng Hoàng Media", "type": "image", "layout": "news_mockup", "domain": "ifeng.com", "in": 49.8, "out": 54.2, "startAt": 0.0},
        {"file": "xinhua_illustration.jpg", "source": "Nguồn: Tân Hoa Xã", "type": "image", "layout": "news_mockup", "domain": "news.cn", "in": 54.2, "out": 59.5, "startAt": 0.0},
        {"file": "youtube_elliot_01.mp4", "source": "Nguồn: YouTube - Elliot Page", "type": "video", "layout": "letterbox_blur", "in": 59.5, "out": 64.5, "startAt": 2.0},
        {"file": "youtube_home_haul.mp4", "source": "Nguồn: YouTube - homeysbee", "type": "video", "layout": "letterbox_blur", "in": 64.5, "out": 69.5, "startAt": 8.0},
        {"file": "douyin_pack_02.mp4", "source": "Nguồn: Douyin - #ChinaHaul", "type": "video", "layout": "fullscreen", "in": 69.5, "out": 73.8, "startAt": 14.0},
        {"file": "youtube_elliot_02.mp4", "source": "Nguồn: YouTube - Elliot Page", "type": "video", "layout": "letterbox_blur", "in": 73.8, "out": 81.1, "startAt": 1.0},
        {"file": "xinhua_headline.jpg", "source": "Nguồn: Tân Hoa Xã", "type": "image", "layout": "news_mockup", "domain": "news.cn", "in": 81.1, "out": 86.0, "startAt": 0.0},
        {"file": "youtube_elliot_03.mp4", "source": "Nguồn: YouTube - Elliot Page", "type": "video", "layout": "letterbox_blur", "in": 86.0, "out": 90.9, "startAt": 2.5},
        {"file": "phoenix_article_top.jpg", "source": "Nguồn: Phượng Hoàng Media", "type": "image", "layout": "news_mockup", "domain": "ifeng.com", "in": 90.9, "out": 96.7, "startAt": 0.0},
        {"file": "douyin_pack_01.mp4", "source": "Nguồn: Douyin - #ChinaHaul", "type": "video", "layout": "fullscreen", "in": 96.7, "out": 101.5, "startAt": 18.0},
        {"file": "youtube_lego_unboxing.mp4", "source": "Nguồn: YouTube - homeysbee", "type": "video", "layout": "letterbox_blur", "in": 101.5, "out": 106.4, "startAt": 6.0},
        {"file": "phoenix_article_body.jpg", "source": "Nguồn: Phượng Hoàng Media", "type": "image", "layout": "news_mockup", "domain": "ifeng.com", "in": 106.4, "out": 113.7, "startAt": 0.0},
        {"file": "xinhua_illustration.jpg", "source": "Nguồn: Tân Hoa Xã", "type": "image", "layout": "news_mockup", "domain": "news.cn", "in": 113.7, "out": 118.0, "startAt": 0.0},
        {"file": "youtube_elliot_01.mp4", "source": "Nguồn: YouTube - Elliot Page", "type": "video", "layout": "letterbox_blur", "in": 118.0, "out": 122.1, "startAt": 7.0},
        {"file": "douyin_pack_02.mp4", "source": "Nguồn: Douyin - #ChinaHaul", "type": "video", "layout": "fullscreen", "in": 122.1, "out": round(total_dur + 0.5, 2), "startAt": 22.0},
    ]

    copied_files = {}
    video_clips = []
    for idx, item in enumerate(shot_definitions):
        src_path = REF_DIR / item["file"]
        if not src_path.exists():
            continue
        dest_filename = f"{slug}_{item['file']}"
        if item["file"] not in copied_files:
            if item["type"] == "image":
                shutil.copy2(src_path, public_img_dir / dest_filename)
                rel_src = f"images/{dest_filename}"
            else:
                shutil.copy2(src_path, public_vid_dir / dest_filename)
                rel_src = f"videos/{dest_filename}"
            copied_files[item["file"]] = rel_src
        else:
            rel_src = copied_files[item["file"]]

        video_clips.append({
            "id": f"clip-{idx:02d}",
            "src": rel_src,
            "mediaType": item["type"],
            "in_seconds": item["in"],
            "out_seconds": item["out"],
            "startAt": item["startAt"],
            "layout": item["layout"],
            "source": item["source"],
            "newsDomain": item.get("domain"),
        })

    print(f"  Constructed {len(video_clips)} dynamic shots across {total_dur:.1f} seconds!")

    # 5. Giant Stat Punches, Kinetic Typography & Yellow Banners
    print("\n[Step 3/4] Formulating Giant Stat Punches and Kinetic Typography...")

    punch_texts = [
        {
            "in_seconds": 0.5,
            "out_seconds": 5.0,
            "line1": "VALI RỖNG SANG",
            "line2": "3 VALI ĐẦY VỀ",
            "color1": "#FFFFFF",
            "color2": "#FFE600",
        },
        {
            "in_seconds": 49.8,
            "out_seconds": 54.0,
            "line1": "BÍ MẬT KINH TẾ",
            "line2": "CHUỖI CUNG ỨNG TẬN XƯỞNG",
            "color1": "#FFFFFF",
            "color2": "#FFE600",
        },
        {
            "in_seconds": 107.0,
            "out_seconds": 113.5,
            "line1": "BÀI HỌC VĨ MÔ",
            "line2": "XÓA BỎ TRUNG GIAN",
            "color1": "#FFFFFF",
            "color2": "#FFE600",
        }
    ]

    stat_punches = [
        {
            "in_seconds": 25.5,
            "out_seconds": 29.5,
            "stat": "110 TRIỆU",
            "label": "LƯỢT XEM TIKTOK",
            "statColor": "#FFFFFF",
            "labelColor": "#FFE600",
        },
        {
            "in_seconds": 29.8,
            "out_seconds": 34.2,
            "stat": "22,9 TRIỆU",
            "label": "LƯỢT TƯƠNG TÁC QUỐC TẾ",
            "statColor": "#FFFFFF",
            "labelColor": "#FFE600",
        },
        {
            "in_seconds": 58.5,
            "out_seconds": 64.0,
            "stat": "RẺ HƠN 70%",
            "label": "SO VỚI MUA TẠI NEW YORK - LONDON",
            "statColor": "#FFFFFF",
            "labelColor": "#FFE600",
        },
        {
            "in_seconds": 75.5,
            "out_seconds": 80.5,
            "stat": "$1.000 USD",
            "label": "TIẾT KIỆM MỖI CHUYẾN SĂN HÀNG",
            "statColor": "#FFFFFF",
            "labelColor": "#FFE600",
        },
        {
            "in_seconds": 83.5,
            "out_seconds": 89.0,
            "stat": "144 GIỜ",
            "label": "MIỄN THỊ THỰC QUÁ CẢNH",
            "statColor": "#FFFFFF",
            "labelColor": "#FFE600",
        }
    ]

    yellow_banners = [
        {
            "in_seconds": 6.0,
            "out_seconds": 11.0,
            "text": "TÁI ĐỊNH HÌNH DU LỊCH MUA SẮM",
        },
        {
            "in_seconds": 15.0,
            "out_seconds": 20.0,
            "text": "BÁO CHÍ ĐỒNG LOẠT LÊN TIẾNG",
        },
        {
            "in_seconds": 35.5,
            "out_seconds": 41.5,
            "text": "CƠN SỐT ĐẬP HỘP QUỐC TẾ",
        },
        {
            "in_seconds": 65.5,
            "out_seconds": 71.0,
            "text": "BÙ ĐẮP TOÀN BỘ TIỀN VÉ",
        },
        {
            "in_seconds": 91.5,
            "out_seconds": 96.0,
            "text": "TRANH LUẬN GAY GẮT",
        },
        {
            "in_seconds": 98.0,
            "out_seconds": 104.0,
            "text": "CHỦ NGHĨA TIÊU DÙNG QUÁ ĐÀ?",
        },
        {
            "in_seconds": 114.5,
            "out_seconds": 120.5,
            "text": "SỨC HÚT CHUỖI CUNG ỨNG TỶ DÂN",
        }
    ]

    props_payload = {
        "videoSrc": "",
        "videoClips": video_clips,
        "muteOriginalVideo": True,
        "voiceSrc": f"audio/{slug}.mp3",
        "voiceVolume": 1.0,
        "bgmSrc": bgm_rel,
        "bgmVolume": 0.10,
        "sourceText": "Nguồn: Douyin - #ChinaHaul",
        "punchTexts": punch_texts,
        "statPunches": stat_punches,
        "yellowBanners": yellow_banners,
        "captions": words,
    }

    props_file = job_dir / "props.json"
    with open(props_file, "w", encoding="utf-8") as f:
        json.dump(props_payload, f, ensure_ascii=False, indent=2)

    # 6. Render with Remotion
    print("\n[Step 4/4] Rendering 2-minute Full HD 1080x1920 MP4 via Remotion...")
    print(f"Total expected frames: {int(total_dur * 30)} @ 30fps")
    npx_cmd = shutil.which("npx.cmd") or shutil.which("npx") or "npx"
    cmd = [
        npx_cmd,
        "remotion",
        "render",
        "src/index.tsx",
        "DouyinRemake",
        str(out_mp4),
        "--props",
        str(props_file),
        "--concurrency",
        "6",
        "--codec",
        "h264",
    ]
    subprocess.run(cmd, cwd=COMPOSER_DIR, check=True)

    size_mb = out_mp4.stat().st_size / (1024 * 1024)
    print("\n" + "="*50)
    print("🏆 2-MINUTE IN-DEPTH BREAKTHROUGH VIDEO RENDERED!")
    print(f"Path:     {out_mp4}")
    print(f"Size:     {size_mb:.2f} MB")
    print(f"Duration: {total_dur:.2f}s (~{total_dur/60:.2f} minutes)")
    print("="*50)


if __name__ == "__main__":
    main()
