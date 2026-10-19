"""
Auto Video Engine - 1-Click Multi-Source Video Generation (Learned Formula)
Incorporates the proven visual principles from the reference video:
1. Multi-source B-roll mixing (real videos, web article screenshots, mobile readers, reaction clips)
2. Letterbox blur for horizontal 16:9 media in vertical 9:16
3. Dynamic per-clip source attribution pills (Tân Hoa Xã, Phượng Hoàng, YouTube, Douyin, Báo chí...)
4. 2-Tier Kinetic Punch Texts (White + Yellow with heavy black outline)
5. Giant Stat Center Punches (e.g. 22,9 TRIỆU, 110 TỶ, $2.5M, 70%)
6. Word-level karaoke captions in safe zone
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import urllib.request
import urllib.parse

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output"
REF_DIR = ROOT_DIR / "reference_videos"
PYTHON_EXE = ROOT_DIR / "OpenMontage" / ".venv" / "Scripts" / "python.exe"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REF_DIR.mkdir(parents=True, exist_ok=True)

# Curated intelligent multi-source footage knowledgebase
TOPIC_KNOWLEDGE = {
    "china_haul": {
        "keywords": ["china haul", "mua sắm", "vali", "trung quốc", "order", "hàng giá rẻ", "săn hàng", "đồ chơi", "thời trang"],
        "media": [
            "reference_videos/douyin_china_haul_luggage_01.mp4",
            "reference_videos/article_tan_hoa_xa_news_cn.jpg",
            "reference_videos/article_phuong_hoang_ifeng.jpg",
            "reference_videos/youtube_elliot_page_interview.mp4",
            "reference_videos/youtube_homeysbee_unboxing.mp4",
        ],
        "default_source": "Nguồn: Douyin - #ChinaHaul",
        "title": "Cơn sốt China Haul càn quét mạng xã hội",
        "script": """Mang một chiếc vali rỗng sang, nhưng xách về tới ba chiếc vali đầy ắp đồ!
Trào lưu China Haul đang bùng nổ dữ dội và càn quét mạng xã hội toàn cầu.
Hàng nghìn du khách phương Tây đổ xô sang các khu chợ và trung tâm thương mại lớn.
Từ thời trang thiết kế, đồ chơi nghệ thuật cho tới các loại dược liệu nội địa.
Tất cả đều có mức giá rẻ hơn tới 70% so với mua tại quê nhà của họ.
Các video gắn hashtag China Haul hiện đã vượt mốc hơn 110 triệu lượt xem trên TikTok.
Người thì khen ngợi vì tiết kiệm cả nghìn đô, người lại lo ngại về xu hướng tiêu dùng quá đà.
Còn bạn nghĩ sao về cơn sốt mua sắm này? Hãy để lại bình luận nhé!""",
        "punches": [
            {"in_seconds": 0.5, "out_seconds": 4.2, "line1": "VALI RỖNG SANG", "line2": "3 VALI ĐẦY VỀ"},
            {"in_seconds": 15.0, "out_seconds": 19.5, "line1": "GIÁ RẺ HƠN 70%", "line2": "TIẾT KIỆM HÀNG NGHÌN ĐÔ"},
        ],
        "stat_punches": [
            {"in_seconds": 21.0, "out_seconds": 25.5, "stat": "110 TRIỆU", "label": "LƯỢT XEM TIKTOK"}
        ],
        "banners": [
            {"in_seconds": 5.0, "out_seconds": 8.5, "text": "CƠN SỐT MUA SẮM QUỐC TẾ"},
            {"in_seconds": 27.0, "out_seconds": 31.0, "text": "TIÊU DÙNG BÙNG NỔ"}
        ]
    },
    "ai_ceo": {
        "keywords": ["ai", "microsoft", "ceo", "satya nadella", "cảnh báo", "mất kiểm soát", "trí tuệ nhân tạo", "phanh khẩn cấp", "safety", "deepseek", "openai"],
        "media": [
            "sample_douyin_video02_full.mp4",
            "output/deepseek_cinematic_breakthrough.mp4",
        ],
        "default_source": "Nguồn: Diễn đàn AI Quốc tế",
        "title": "Cảnh báo khẩn cấp về sự bùng nổ của AI",
        "script": """Liệu trí tuệ nhân tạo có đang vượt khỏi tầm kiểm soát của con người?
Mới đây, các chuyên gia hàng đầu đã đưa ra lời cảnh báo cực kỳ đanh thép.
Họ nhấn mạnh rằng các tập đoàn công nghệ bắt buộc phải trang bị phanh khẩn cấp cho AI ngay từ bây giờ!
Nếu để các mô hình tự hành phát triển không kiểm soát, rủi ro an ninh mạng và kinh tế toàn cầu sẽ không thể cứu vãn.
Nhiều quốc gia lớn đã bắt đầu yêu cầu các công ty công nghệ phải báo cáo sự cố an toàn định kỳ.
Liệu chúng ta có thể kiểm soát được siêu trí tuệ nhân tạo trong tương lai?
Hãy để lại ý kiến của bạn ngay phía dưới!""",
        "punches": [
            {"in_seconds": 0.5, "out_seconds": 4.0, "line1": "AI MẤT KIỂM SOÁT?", "line2": "LỜI CẢNH BÁO KHẨN CẤP"},
            {"in_seconds": 6.5, "out_seconds": 11.0, "line1": "PHANH KHẨN CẤP", "line2": "CHO SIÊU TRÍ TUỆ NHÂN TẠO"},
        ],
        "stat_punches": [
            {"in_seconds": 16.0, "out_seconds": 20.5, "stat": "BÁO ĐỘNG ĐỎ", "label": "AN TOÀN CÔNG NGHỆ TOÀN CẦU"}
        ],
        "banners": [
            {"in_seconds": 4.2, "out_seconds": 6.8, "text": "CẢNH BÁO NGUY CƠ AI"},
            {"in_seconds": 12.0, "out_seconds": 15.5, "text": "SIẾT CHẶT QUY ĐỊNH PHÁP LÝ"}
        ]
    },
    "tesla_tech": {
        "keywords": ["tesla", "xe điện", "cybertruck", "cyberquad", "elon musk", "xe địa hình", "công nghệ mới", "tự lái", "robot"],
        "media": [
            "sample_v03.mp4",
        ],
        "default_source": "Nguồn: YouTube - TechReview",
        "title": "Chiếc xe địa hình chạy điện độc lạ nhất thế giới",
        "script": """Đây chính là cỗ máy địa hình chạy điện mang phong cách viễn tưởng của tương lai!
Lấy cảm hứng trực tiếp từ thiết kế góc cạnh hầm hố của Tesla Cybertruck.
Toàn bộ khung xe được chế tạo từ hợp kim thép siêu cứng, trang bị động cơ điện phản hồi tức thì.
Không tiếng ồn, không khí thải, nhưng khả năng leo dốc và vượt địa hình hiểm trở lại cực kỳ ấn tượng.
Mẫu xe này đã tạo nên một cơn sốt đặt hàng ngay từ những ngày đầu ra mắt.
Bạn có sẵn sàng sở hữu một chiếc xe như thế này để dạo phố không?
Hãy bình luận cho mọi người cùng biết nhé!""",
        "punches": [
            {"in_seconds": 0.5, "out_seconds": 4.2, "line1": "SIÊU XE ĐỊA HÌNH", "line2": "PHONG CÁCH TƯƠNG LAI"},
            {"in_seconds": 7.0, "out_seconds": 11.5, "line1": "HỢP KIM THÉP", "line2": "ĐỘNG CƠ ĐIỆN SIÊU NHANH"},
        ],
        "stat_punches": [
            {"in_seconds": 16.0, "out_seconds": 20.5, "stat": "CHÁY HÀNG", "label": "NGAY NGÀY ĐẦU RA MẮT"}
        ],
        "banners": [
            {"in_seconds": 4.5, "out_seconds": 7.2, "text": "CÔNG NGHỆ ĐỘT PHÁ"},
            {"in_seconds": 12.0, "out_seconds": 15.8, "text": "HIỆU SUẤT KHÔNG TƯỞNG"}
        ]
    }
}


def fetch_url_article(url: str, slug: str) -> Dict[str, Any]:
    """Fetches web article text and high-res images."""
    import urllib.parse
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    domain = urllib.parse.urlparse(url).netloc.replace("www.", "")

    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = title_m.group(1).strip() if title_m else "Tin Tức Mới"
    title = re.sub(r"\s+", " ", title).split(" - ")[0].split(" | ")[0]

    # Clean text
    clean_html = re.sub(r"<(script|style|noscript|header|footer|nav)[^>]*>.*?</\1>", "", html, flags=re.I | re.S)
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", clean_html, re.I | re.S)
    clean_paras = []
    for p in paragraphs:
        t = re.sub(r"<[^>]+>", "", p).strip()
        t = re.sub(r"\s+", " ", t)
        if len(t) > 35:
            clean_paras.append(t)

    # Scrape images
    img_urls = re.findall(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    body_imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', clean_html, re.I)
    for src in body_imgs:
        if any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            if not any(bad in src.lower() for bad in ["avatar", "icon", "logo", "tracker", "badge"]):
                img_urls.append(src)

    saved_images = []
    temp_dir = OUTPUT_DIR / slug
    temp_dir.mkdir(parents=True, exist_ok=True)

    idx = 0
    parsed = urllib.parse.urlparse(url)
    for raw_u in img_urls[:4]:
        u = raw_u.strip()
        if u.startswith("//"):
            u = "https:" + u
        elif u.startswith("/"):
            u = f"{parsed.scheme}://{parsed.netloc}{u}"
        if not u.startswith("http"):
            continue

        out_img = temp_dir / f"article_{domain.replace('.', '_')}_{idx}.jpg"
        try:
            ireq = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(ireq, timeout=8) as iresp:
                idata = iresp.read()
            if len(idata) > 15000:
                out_img.write_bytes(idata)
                saved_images.append(str(out_img))
                idx += 1
        except Exception:
            continue

    return {
        "title": title,
        "domain": domain,
        "body": " ".join(clean_paras[:7]),
        "images": saved_images,
    }


def synthesize_script_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Intelligently analyzes the user's single prompt or URL and synthesizes
    the full multi-source production package.
    """
    clean_prompt = prompt.lower().strip()
    slug = f"auto_{int(time.time())}"

    # 1. Match against known high-quality video templates
    best_match = None
    max_score = 0
    for key, data in TOPIC_KNOWLEDGE.items():
        score = sum(1 for kw in data["keywords"] if kw in clean_prompt)
        if score > max_score:
            max_score = score
            best_match = data

    if best_match and max_score > 0:
        media_paths = []
        for m in best_match["media"]:
            mp = ROOT_DIR / m
            if mp.exists():
                media_paths.append(str(mp))

        if not media_paths:
            # Fallback to local files
            sample = ROOT_DIR / "sample_douyin_video01.mp4"
            if sample.exists():
                media_paths.append(str(sample))

        return {
            "mode": "douyin_remake",
            "media_paths": media_paths,
            "script_text": best_match["script"],
            "source_credit": best_match["default_source"],
            "punches": best_match["punches"],
            "stat_punches": best_match.get("stat_punches", []),
            "banners": best_match["banners"],
            "title": best_match["title"],
        }

    # 2. If it's a URL
    if clean_prompt.startswith("http://") or clean_prompt.startswith("https://"):
        try:
            art = fetch_url_article(prompt, slug)
            script = f"""Thông tin chấn động mới nhất từ {art['domain']} đang thu hút sự chú ý đặc biệt!
Tiêu điểm: {art['title'][:70]}.
{art['body'][:350]}
Hiện tại, bài viết này đang nhận được hàng ngàn lượt tương tác và bình luận sôi nổi từ cộng đồng mạng.
Bạn nghĩ gì về sự việc này? Hãy để lại ý kiến của mình ngay phía dưới nhé!"""

            media_paths = list(art["images"])
            # Add general tech/news B-roll video if available
            for v_name in ("sample_douyin_video02_full.mp4", "sample_douyin_video01.mp4", "sample_v03.mp4"):
                vp = ROOT_DIR / v_name
                if vp.exists():
                    media_paths.append(str(vp))
                    break

            return {
                "mode": "douyin_remake",
                "media_paths": media_paths,
                "script_text": script,
                "source_credit": f"Nguồn: {art['domain']}",
                "punches": [
                    {"in_seconds": 0.5, "out_seconds": 4.2, "line1": "TIN NÓNG 24H", "line2": art['domain'].upper()}
                ],
                "stat_punches": [],
                "banners": [
                    {"in_seconds": 4.5, "out_seconds": 7.5, "text": "TIÊU ĐIỂM DƯ LUẬN"}
                ],
                "title": art["title"],
            }
        except Exception as e:
            print(f"Error fetching URL: {e}")

    # 3. Dynamic subject prompt
    subject = prompt.replace("Tạo video về", "").replace("làm video về", "").replace("tạo video", "").strip()
    subject_upper = subject.upper()

    script = f"""Bạn đã biết thông tin chấn động về {subject} đang gây sốt mạng xã hội chưa?
Chủ đề này đang nhận được hàng triệu lượt quan tâm và bàn tán trên khắp các diễn đàn.
Hàng loạt chuyên gia và cộng đồng mạng đã liên tục đưa ra những phân tích đa chiều.
Từ những tiềm năng vượt trội cho tới những tranh luận không hồi kết đang diễn ra.
Rất nhiều người đã bày tỏ sự bất ngờ trước tốc độ lan tỏa nhanh chóng mặt của sự việc này.
Còn góc nhìn của bạn thì sao? Bạn đánh giá thế nào về {subject}?
Hãy để lại bình luận và quan điểm của bạn ngay dưới video này nhé!"""

    media_paths = []
    # Collect available reference media
    ref_files = list(REF_DIR.glob("*.*"))
    if ref_files:
        for rf in ref_files[:5]:
            media_paths.append(str(rf))
    else:
        for s in ("sample_douyin_video01.mp4", "sample_drive_learning.mp4", "sample_douyin_video02_full.mp4"):
            sp = ROOT_DIR / s
            if sp.exists():
                media_paths.append(str(sp))

    return {
        "mode": "douyin_remake",
        "media_paths": media_paths,
        "script_text": script,
        "source_credit": "Nguồn: Tin Tổng Hợp",
        "punches": [
            {"in_seconds": 0.5, "out_seconds": 4.5, "line1": "THÔNG TIN MỚI NHẤT", "line2": subject_upper[:24]}
        ],
        "stat_punches": [
            {"in_seconds": 5.0, "out_seconds": 8.5, "stat": "HÀNG TRIỆU", "label": "LƯỢT XEM VÀ BÀN TÁN"}
        ],
        "banners": [
            {"in_seconds": 9.0, "out_seconds": 12.5, "text": "TIÊU ĐIỂM XU HƯỚNG"}
        ],
        "title": f"Tiêu điểm: {subject}",
    }


def run_auto_pipeline(prompt: str, on_progress=None) -> Dict[str, Any]:
    """Runs the complete multi-source video production pipeline from 1 prompt."""
    if on_progress:
        on_progress("Phân tích ý tưởng và tổng hợp tư liệu đa nguồn (video, bài báo, ảnh)...")

    plan = synthesize_script_from_prompt(prompt)
    timestamp = int(time.time())

    out_name = f"auto_douyin_{timestamp}.mp4"
    out_file = OUTPUT_DIR / out_name

    script_file = OUTPUT_DIR / f"auto_{timestamp}_script.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(plan["script_text"])

    media_arg = ",".join(plan["media_paths"])

    if on_progress:
        on_progress("Đang tổng hợp giọng đọc tiếng Việt và khớp nhịp chữ giật 2 tầng & số liệu cực đại...")

    cmd = [
        str(PYTHON_EXE),
        str(ROOT_DIR / "remake_douyin_video.py"),
        "--media", media_arg,
        "--text", str(script_file),
        "--source", plan["source_credit"],
        "--voice", "vi-VN-NamMinhNeural",
        "--rate", "+20%",
        "--output", str(out_file),
    ]

    if plan.get("punches"):
        p_file = OUTPUT_DIR / f"auto_{timestamp}_punches.json"
        with open(p_file, "w", encoding="utf-8") as f:
            json.dump(plan["punches"], f, ensure_ascii=False, indent=2)
        cmd.extend(["--punches", str(p_file)])

    if plan.get("stat_punches"):
        sp_file = OUTPUT_DIR / f"auto_{timestamp}_stat_punches.json"
        with open(sp_file, "w", encoding="utf-8") as f:
            json.dump(plan["stat_punches"], f, ensure_ascii=False, indent=2)
        cmd.extend(["--stat-punches", str(sp_file)])

    if plan.get("banners"):
        b_file = OUTPUT_DIR / f"auto_{timestamp}_banners.json"
        with open(b_file, "w", encoding="utf-8") as f:
            json.dump(plan["banners"], f, ensure_ascii=False, indent=2)
        cmd.extend(["--banners", str(b_file)])

    if on_progress:
        on_progress("Đang render Remotion Full HD 1080x1920 (30fps) đa tầng tư liệu...")

    proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)

    return {
        "status": "success",
        "video_url": f"/videos/{out_name}",
        "video_name": out_name,
        "title": plan["title"],
        "script": plan["script_text"],
    }
