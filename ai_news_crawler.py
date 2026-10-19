"""
AI News Crawler & Autonomous Video Producer
Scans global AI news feeds in real time, selects an unprocessed breaking news item,
deduplicates it against a persistent history, writes an engaging Vietnamese short video script,
and automatically renders the complete 1080x1920 video.
"""

import asyncio
import hashlib
import json
import html
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
import urllib.request
import xml.etree.ElementTree as ET

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output"
PROCESSED_FILE = ROOT_DIR / "processed_ai_news.json"
PYTHON_EXE = ROOT_DIR / "OpenMontage" / ".venv" / "Scripts" / "python.exe"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Curated feeds for breaking AI news
AI_FEEDS = [
    {
        "name": "Google News AI",
        "url": "https://news.google.com/rss/search?q=OpenAI+OR+Anthropic+OR+Gemini+OR+\"Artificial+Intelligence\"+OR+DeepSeek+when:2d&hl=en-US&gl=US&ceid=US:en"
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/"
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
    }
]

# Keywords to discard spam, crypto scams, hacks, legal drama
DISCARD_KEYWORDS = [
    "crypto", "bitcoin", "solana", "memecoin", "ethereum", "wallet",
    "hack", "scam", "phishing", "stolen", "heist", "jailbreak", "exploit",
    "arrested", "lawsuit", "court", "sued", "fraud", "scandal", "nsfw"
]

# Keywords that signal high-value technological breakthroughs
HIGH_VALUE_KEYWORDS = [
    "model", "launch", "releases", "release", "unveils", "announces", "debut",
    "open source", "reasoning", "benchmark", "breakthrough", "agent",
    "feature", "update", "gemini", "claude", "gpt", "deepseek", "nvidia",
    "openai", "anthropic", "meta ai", "apple intelligence", "chip", "robot"
]

# Fallback pool of top breaking AI topics if offline or network timeout
FALLBACK_AI_NEWS = [
    {
        "id": "deepseek_r1_revolution",
        "title": "DeepSeek R1 Open Source Reasoning Model Disrupts AI Market",
        "source": "TechCrunch",
        "link": "https://techcrunch.com",
        "summary": "Mô hình mã nguồn mở DeepSeek R1 ra mắt với khả năng suy luận tương đương OpenAI o1 nhưng chi phí vận hành rẻ hơn tới 90%."
    },
    {
        "id": "openai_operator_autonomous",
        "title": "OpenAI Launches Autonomous Computer-Using Agent Operator",
        "source": "Bloomberg",
        "link": "https://bloomberg.com",
        "summary": "OpenAI chính thức phát hành Operator - trợ lý AI có khả năng tự động điều khiển máy tính, duyệt web và viết mã thay con người."
    },
    {
        "id": "anthropic_claude_37_sonnet",
        "title": "Anthropic Unveils Hybrid Reasoning Claude 3.7 Sonnet",
        "source": "The Verge",
        "link": "https://theverge.com",
        "summary": "Anthropic ra mắt mô hình AI lai Claude 3.7 Sonnet cho phép người dùng tự điều chỉnh thời gian suy nghĩ từ vài giây đến nhiều phút."
    },
    {
        "id": "nvidia_blackwell_ultra_ai",
        "title": "NVIDIA Blackwell Ultra Chips Enter Mass Production",
        "source": "Reuters",
        "link": "https://reuters.com",
        "summary": "NVIDIA thông báo thế hệ siêu chip Blackwell Ultra đã bắt đầu bàn giao cho các tập đoàn công nghệ lớn, nâng tốc độ huấn luyện AI lên gấp 4 lần."
    },
    {
        "id": "google_gemini_2_flash_thinking",
        "title": "Google Releases Gemini 2.0 Flash Thinking Globally",
        "source": "Google Blog",
        "link": "https://blog.google",
        "summary": "Google phổ cập dòng mô hình suy luận siêu tốc Gemini 2.0 Flash Thinking đến hàng tỷ người dùng với tốc độ phản hồi tính bằng mili-giây."
    }
]


def load_processed_history() -> Dict[str, Any]:
    if not PROCESSED_FILE.exists():
        return {"processed_ids": [], "items": []}
    try:
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"processed_ids": [], "items": []}


def save_processed_history(history: Dict[str, Any]):
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def score_news_candidate(item: Dict[str, str]) -> int:
    text = (item["title"] + " " + item.get("summary", "")).lower()
    for kw in DISCARD_KEYWORDS:
        if kw in text:
            return -999  # Discard immediately
    score = 0
    for kw in HIGH_VALUE_KEYWORDS:
        if kw in text:
            score += 2
    if 30 <= len(item["title"]) <= 120:
        score += 1
    return score


def fetch_full_article_summary(url: str, fallback_summary: str = "") -> str:
    """Fetches real article paragraphs to give LLM rich context."""
    if not url or not url.startswith("http"):
        return fallback_summary
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            html_raw = resp.read().decode("utf-8", errors="ignore")

        html_clean = re.sub(r"<(script|style|noscript|header|footer|nav)[^>]*>.*?</\1>", "", html_raw, flags=re.IGNORECASE | re.DOTALL)
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html_clean, re.IGNORECASE | re.DOTALL)
        clean_paras = []
        for p in paragraphs:
            text = html.unescape(re.sub(r"<[^>]+>", "", p)).strip()
            text = re.sub(r"\s+", " ", text)
            if len(text) > 50 and not any(skip in text.lower() for skip in ["register now", "save up to", "doors open", "cookie", "all rights reserved"]):
                clean_paras.append(text)
        if clean_paras:
            return " ".join(clean_paras[:3])[:800]
    except Exception:
        pass
    return fallback_summary


def crawl_live_ai_news() -> List[Dict[str, str]]:
    """Crawls real-time AI news from RSS feeds and filters high-value stories."""
    news_candidates = []

    for feed in AI_FEEDS:
        try:
            req = urllib.request.Request(
                feed["url"],
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            for it in items[:15]:
                raw_title = it.find("title").text if it.find("title") is not None else ""
                link = it.find("link").text if it.find("link") is not None else ""
                guid = it.find("guid").text if it.find("guid") is not None else ""
                pubDate = it.find("pubDate").text if it.find("pubDate") is not None else ""
                desc = it.find("description").text if it.find("description") is not None else ""

                if not raw_title or len(raw_title) < 15:
                    continue

                # Use guid if it's a direct permalink redirect
                if guid and guid.startswith("http") and ("?p=" in guid or len(guid) > len(link)):
                    link = guid

                # Clean up title: remove trailing " - Source"
                clean_title = raw_title
                source = feed["name"]
                if " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    clean_title = parts[0].strip()
                    source = parts[1].strip()

                news_id = hashlib.md5(clean_title.encode("utf-8")).hexdigest()[:12]
                candidate = {
                    "id": news_id,
                    "title": clean_title,
                    "link": link,
                    "source": source,
                    "pubDate": pubDate,
                    "summary": html.unescape(re.sub(r"<[^>]+>", " ", desc)).strip()[:300]
                }

                score = score_news_candidate(candidate)
                if score >= 0:
                    candidate["_score"] = score
                    news_candidates.append(candidate)
        except Exception as e:
            print(f"Warning: Failed to crawl {feed['name']}: {e}")

    # Prioritize stories by technological impact score
    news_candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return news_candidates


def get_next_unprocessed_news() -> Dict[str, str]:
    """Finds the freshest breaking AI news that has NEVER been processed."""
    history = load_processed_history()
    processed_set = set(history.get("processed_ids", []))

    # 1. Crawl live news
    live_news = crawl_live_ai_news()

    # Find highest ranked unpicked live item
    for item in live_news:
        if item["id"] not in processed_set:
            full_summary = fetch_full_article_summary(item.get("link", ""), item.get("summary", ""))
            if full_summary:
                item["summary"] = full_summary
            return item

    # 2. Check fallback curated pool
    for item in FALLBACK_AI_NEWS:
        if item["id"] not in processed_set:
            return item

    # 3. If everything in the history was processed, pick the newest live item to keep rolling
    if live_news:
        new_item = live_news[0].copy()
        new_item["id"] = f"{new_item['id']}_{int(time.time())}"
        full_summary = fetch_full_article_summary(new_item.get("link", ""), new_item.get("summary", ""))
        if full_summary:
            new_item["summary"] = full_summary
        return new_item

    # Default fallback
    fallback = FALLBACK_AI_NEWS[0].copy()
    fallback["id"] = f"{fallback['id']}_{int(time.time())}"
    return fallback


def translate_and_craft_vietnamese_script(
    news: Dict[str, str],
    min_duration_seconds: int = 60
) -> Dict[str, Any]:
    """
    Translates English AI news and crafts a high-retention in-depth vertical short video script (60s+)
    with signature Bento HUD, concrete benchmark evidence, and kinetic typography.
    """
    title = news.get("title", "Tin tức AI")
    source = news.get("source", "Báo Quốc Tế")
    summary = news.get("summary", "")

    # 0. Try LLM generation via api.buihuuthang.com if API key configured
    try:
        from ai_service import llm_craft_vietnamese_script
        llm_res = llm_craft_vietnamese_script(title, summary, source, min_duration_seconds=min_duration_seconds)
        if llm_res and "script_text" in llm_res and "headline" in llm_res:
            llm_res["link"] = news.get("link", "")
            return llm_res
    except Exception as e:
        print(f"LLM script crafting skipped: {e}")

    # Clean subject
    clean_title = re.sub(r"[^\w\s\d\-\.]", "", title).strip()
    title_lower = title.lower()

    if min_duration_seconds >= 120:
        if any(k in title_lower for k in ["deepseek", "reasoning", "r1"]):
            headline = "DEEPSEEK R1 GÂY ĐỊA CHẤN"
            sub_headline = "PHÂN TÍCH CHUYÊN SÂU TOÀN DIỆN"
            stat = "79.8% AIME"
            stat_desc = "ĐIỂM TOÁN VƯỢT TRỘI"
            stat_2 = "6 TRIỆU USD"
            stat_desc_2 = "TIẾT KIỆM 95% CHI PHÍ"
            comp_old = "OpenAI o1: 15 USD / 1M token"
            comp_new = "DeepSeek R1: 0.55 USD / 1M"
            evidence_q = "Đại học Stanford và các viện nghiên cứu quốc tế đã độc lập kiểm chứng mã nguồn, xác nhận hiệu năng thực tế đạt chuẩn ngang ngửa o1."
            evidence_src = "Đại học Stanford & Báo cáo độc lập"
            script = """Làm thế nào một nhóm kỹ sư vô danh với vỏn vẹn 6 triệu đô la vừa giáng đòn chí mạng vào đế chế hàng trăm tỷ đô của Thung lũng Silicon? 
Trong nhiều năm, niềm tin tối thượng của giới công nghệ là chỉ có hàng trăm ngàn GPU đắt đỏ và hàng tỷ đô la đốt vào siêu máy tính mới có thể sinh ra siêu trí tuệ. 
Nhưng rồi DeepSeek xuất hiện, lặng lẽ phát hành mô hình R1 mã nguồn mở và lật tung hoàn toàn niềm tin ấy. 
Trên bài thi toán Olympic AIME 2024, R1 đạt 79.8 phần trăm điểm, chính thức vượt qua con số 79.2 phần trăm của OpenAI o1. 
Ở bài thi chuyên sâu MATH-500, nó chạm mốc 97.3 phần trăm, còn đấu trường lập trình Codeforces cũng bị khuất phục hoàn toàn. 
Vậy bí mật nằm ở đâu? Kiến trúc hỗn hợp chuyên gia MoE với 671 tỷ tham số nhưng chỉ kích hoạt 37 tỷ mỗi token, kết hợp cơ chế MLA tiết kiệm tới 93 phần trăm bộ nhớ. 
Nhưng khoảnh khắc rợn người nhất là DeepSeek-R1-Zero: không cần con người gán nhãn, mô hình tự học cách tư duy và tự thốt lên hãy để tôi nghĩ lại khi phát hiện lập luận sai. 
Đó là lúc cỗ máy thực sự bắt đầu tự vấn chính mình! 
Và cú tát vào túi tiền mới là thứ khiến Phố Wall choáng váng: OpenAI thu 15 đô la mỗi triệu token, còn DeepSeek chỉ thu 0.55 đô la, rẻ hơn tới 27 lần. 
Chỉ sau một đêm, hàng trăm tỷ đô la vốn hóa của các tập đoàn bán dẫn và công nghệ lớn bốc hơi. 
Nhưng điều chấn động hơn là giấy phép MIT: mở hoàn toàn, không điều kiện giới hạn. 
Đại học Stanford và cộng đồng toàn cầu đã kiểm chứng độc lập và xác nhận: bất kỳ ai cũng có thể tải R1 về chạy mượt mà ngay trên chiếc máy tính cá nhân của mình. 
Kỷ nguyên độc quyền AI vừa chính thức sụp đổ ngay trước mắt chúng ta. 
Nếu một nhóm nhỏ với 6 triệu đô la làm được điều này, thì các đế chế công nghệ đang giấu sau cánh cửa đóng kín điều gì? Hãy để lại bình luận của bạn bên dưới!"""

        elif any(k in title_lower for k in ["nvidia", "chip", "blackwell", "gpu"]):
            headline = "SIÊU CHIP AI MẠNH NHẤT"
            sub_headline = "NVIDIA XÁC LẬP KỶ LỤC MỚI"
            stat = "208 TỶ BÓNG"
            stat_desc = "KIẾN TRÚC BLACKWELL"
            stat_2 = "GẤP 4 LẦN"
            stat_desc_2 = "TỐC ĐỘ HUẤN LUYỆN"
            comp_old = "Thế hệ Hopper H100"
            comp_new = "Kiến trúc Blackwell B200"
            evidence_q = "Báo cáo thử nghiệm thực tế từ các trung tâm dữ liệu đám mây xác nhận hiệu năng suy luận tăng vọt gấp 30 lần."
            evidence_src = "Báo cáo thử nghiệm đám mây"
            script = """Cuộc đua phần cứng điện toán trí tuệ nhân tạo toàn cầu vừa chính thức bước sang một nấc thang mới khi dòng siêu chip kiến trúc Blackwell chính thức đi vào giai đoạn sản xuất hàng loạt. 
Được thiết kế với hai trăm lẻ tám tỷ bóng bán dẫn ghép nối đồng bộ trên một đế bán dẫn duy nhất, thế hệ xử lý này sở hữu băng thông bộ nhớ kỷ lục lên tới mười terabyte mỗi giây. 
Theo công bố chi tiết từ các chuyên gia phần cứng hàng đầu, dòng chip mới giúp tăng tốc độ huấn luyện các mô hình ngôn ngữ lớn lên gấp 4 lần so với thế hệ trước. 
Đặc biệt trong các tác vụ suy luận thời gian thực, mức cải thiện hiệu năng đo đạc thực tế thậm chí đạt tới ba mươi lần, trong khi điện năng tiêu thụ giảm xuống đáng kể. 
Toàn bộ năng lực cung ứng của các nhà máy đúc chip bán dẫn hàng đầu thế giới đã được các tập đoàn công nghệ lớn đặt hàng kín chỗ cho tới hết năm nay. 
Các nhà phân tích phố Wall nhận định rằng sức mạnh phần cứng này sẽ là động cơ kích hoạt làn sóng mô hình tự hành và robot hình người thế hệ kế tiếp. 
Theo nguồn tin từ các tổ chức phân tích độc lập, việc sở hữu hạ tầng siêu chip quy mô lớn sẽ là yếu tố then chốt quyết định vị thế thống trị công nghệ toàn cầu trong thập kỷ tới. 
Tuy nhiên, sự bùng nổ của các mô hình thuật toán tối ưu như DeepSeek cũng đang đặt ra câu hỏi lớn về tính bền vững của các khoản đầu tư hàng trăm tỷ đô la vào phần cứng. 
Bạn đánh giá thế nào về năng lực tính toán phi thường và tương lai của thế hệ siêu chip bán dẫn này? Hãy chia sẻ quan điểm của bạn nhé!"""

        else:
            short_title = clean_title[:28].upper()
            headline = "BƯỚC TIẾN CÔNG NGHỆ MỚI"
            sub_headline = short_title
            stat = "ĐỘT PHÁ"
            stat_desc = "CÔNG NGHỆ TIÊN TIẾN"
            stat_2 = "TOÀN CẦU"
            stat_desc_2 = "GÂY ẤN TƯỢNG MẠNH"
            comp_old = "Giới hạn công nghệ cũ"
            comp_new = "Cải tiến vượt bậc hiện tại"
            evidence_q = "Cộng đồng nghiên cứu quốc tế đã tiến hành thử nghiệm và ghi nhận mức độ ổn định ấn tượng trên các kịch bản thực tế."
            evidence_src = "Báo cáo thử nghiệm quốc tế"
            script = f"""Thế giới công nghệ vừa ghi nhận một bước ngoặt mang tính chiến lược trong tiến trình phát triển của trí tuệ nhân tạo toàn cầu. 
Sự kiện công bố giải pháp công nghệ: {clean_title[:65]} đang thu hút sự quan tâm đặc biệt từ các nhà khoa học, giới nghiên cứu và các quỹ đầu tư mạo hiểm hàng đầu. 
Trong nhiều năm qua, rào cản lớn nhất của các hệ thống điện toán là chi phí vận hành đắt đỏ và độ trễ cao khi xử lý dữ liệu quy mô lớn. 
Tuy nhiên, bước tiến mới này đã giải quyết triệt để bài toán hóc búa trên bằng cách tối ưu hóa thuật toán từ tận gốc rễ. 
Theo các báo cáo thử nghiệm sơ bộ từ cộng đồng độc lập, thời gian phản hồi của hệ thống đã được rút ngắn đáng kể, trong khi độ chính xác và tính ổn định đạt chuẩn vượt bậc. 
Các chuyên gia công nghệ nhận định rằng sự kết hợp giữa kiến trúc phần mềm thế hệ mới và cơ chế phân phối tài nguyên thông minh chính là chìa khóa tạo nên sức mạnh này. 
Nhiều viện nghiên cứu và trường đại học lớn đã nhanh chóng tiến hành các thử nghiệm đối đầu trực tiếp và xác nhận hiệu năng thực tế hoàn toàn vượt trội so với các giải pháp truyền thống trước đây. 
Không chỉ dừng lại ở hiệu suất tính toán, cải tiến này còn mở ra tiềm năng ứng dụng to lớn trong tự động hóa sản xuất, y tế thông minh và giáo dục cá nhân hóa. 
Các tập đoàn công nghệ lớn trên thế giới đang gấp rút điều chỉnh lộ trình phát triển sản phẩm để thích ứng với làn sóng đổi mới sáng tạo thần tốc này. 
Rõ ràng, khoảng cách giữa các đột phá trong phòng thí nghiệm và việc triển khai thực tế vào đời sống hàng ngày đang ngày càng được thu hẹp lại. 
Đây là minh chứng không thể chối cãi cho thấy cuộc cách mạng trí tuệ nhân tạo đang bước vào giai đoạn tăng tốc mạnh mẽ nhất trong lịch sử. 
Kỷ nguyên mà các rào cản công nghệ bị xóa bỏ và sức mạnh tính toán được phổ cập tới mọi người dùng đang diễn ra ngay trước mắt chúng ta. 
Còn bạn, bạn đánh giá thế nào về tiềm năng ứng dụng và tầm ảnh hưởng sâu rộng của bước tiến công nghệ này trong tương lai? 
Hãy để lại bình luận và quan điểm của bạn ngay bên dưới để cộng đồng cùng thảo luận nhé!"""

    else:
        # Standard 60s - 75s scripts
        if any(k in title_lower for k in ["deepseek", "reasoning", "r1"]):
            headline = "DEEPSEEK R1 GÂY ĐỊA CHẤN"
            sub_headline = "LÀM THAY ĐỔI CUỘC ĐUA AI"
            stat = "79.8% AIME"
            stat_desc = "ĐIỂM TOÁN VƯỢT TRỘI"
            stat_2 = "6 TRIỆU USD"
            stat_desc_2 = "TIẾT KIỆM 95% CHI PHÍ"
            comp_old = "Hàng trăm triệu USD"
            comp_new = "Chỉ 6 triệu USD"
            evidence_q = "Đại học Stanford và cộng đồng mã nguồn mở đã độc lập kiểm chứng và xác nhận hiệu năng thực tế của mô hình."
            evidence_src = "Đại học Stanford"
            script = """Một cú sốc công nghệ vừa giáng xuống Thung lũng Silicon khi mô hình DeepSeek R1 chính thức ra mắt, khiến toàn bộ giới chuyên gia phải định hình lại tương lai của trí tuệ nhân tạo. 
Thay vì đổ hàng trăm triệu đô la vào các trung tâm dữ liệu khổng lồ, đội ngũ kỹ sư đã tối ưu hóa kiến trúc hỗn hợp chuyên gia MoE kết hợp kỹ thuật học tăng cường quy mô lớn. 
Theo báo cáo kỹ thuật chính thức được công bố, DeepSeek R1 đạt điểm số 79.8 phần trăm trên bài kiểm tra toán học chuyên sâu AIME 2024, sánh ngang với mô hình o1 của OpenAI. 
Điều gây chấn động nhất nằm ở ngân sách huấn luyện: hệ thống chỉ tiêu tốn xấp xỉ 6 triệu đô la Mỹ tiền GPU, thấp hơn tới 95 phần trăm so với các phòng thí nghiệm phương Tây. 
Các nhà nghiên cứu độc lập từ Đại học Stanford và cộng đồng mã nguồn mở đã trực tiếp xác minh mã nguồn và xác nhận khả năng vận hành thực tế. 
Sự kiện này ngay lập tức khiến cổ phiếu các tập đoàn công nghệ lớn bị rung lắc mạnh, đồng thời buộc OpenAI và Google phải nhanh chóng điều chỉnh chính sách giá API. 
Đây là minh chứng rõ ràng cho thấy kỷ nguyên tối ưu hóa thuật toán thông minh đang dần vượt lên chiến lược dựa vào sức mạnh tính toán cơ bắp. 
Bạn nghĩ sao về bước chuyển dịch mang tính lịch sử này của ngành công nghệ trí tuệ nhân tạo? Hãy để lại bình luận bên dưới nhé!"""

        elif any(k in title_lower for k in ["nvidia", "chip", "blackwell", "gpu"]):
            headline = "SIÊU CHIP AI MẠNH NHẤT"
            sub_headline = "NVIDIA XÁC LẬP KỶ LỤC MỚI"
            stat = "208 TỶ BÓNG"
            stat_desc = "KIẾN TRÚC BLACKWELL"
            stat_2 = "GẤP 4 LẦN"
            stat_desc_2 = "TỐC ĐỘ HUẤN LUYỆN"
            comp_old = "Thế hệ Hopper H100"
            comp_new = "Kiến trúc Blackwell B200"
            evidence_q = "Báo cáo tài chính và kiểm thử từ các nhà cung cấp đám mây xác nhận hiệu năng xử lý suy luận tăng vọt gấp 30 lần."
            evidence_src = "Báo cáo thử nghiệm đám mây"
            script = """Cuộc đua phần cứng trí tuệ nhân tạo toàn cầu vừa bước sang một nấc thang mới khi dòng siêu chip kiến trúc Blackwell chính thức đi vào sản xuất hàng loạt. 
Được thiết kế với hai trăm lẻ tám tỷ bóng bán dẫn ghép nối trên một đế chip duy nhất, thế hệ xử lý này sở hữu băng thông bộ nhớ lên tới mười terabyte mỗi giây. 
Theo công bố từ các kỹ sư phần cứng hàng đầu, dòng chip mới giúp tăng tốc độ huấn luyện mô hình ngôn ngữ lớn lên gấp 4 lần so với thế hệ trước. 
Đặc biệt trong các tác vụ suy luận thời gian thực, mức cải thiện hiệu năng đo đạc thực tế thậm chí đạt tới ba mươi lần, trong khi điện năng tiêu thụ giảm đáng kể. 
Toàn bộ năng lực sản xuất của các nhà máy đúc chip hàng đầu thế giới đã được các ông lớn công nghệ đặt trước kín chỗ cho tới hết năm nay. 
Các chuyên gia nhận định rằng sức mạnh phần cứng này sẽ là động cơ kích hoạt làn sóng mô hình tự hành và robot hình người thế hệ kế tiếp. 
Theo nguồn tin từ các tổ chức phân tích thị trường, đây sẽ là yếu tố quyết định vị thế thống trị công nghệ trong thập kỷ tới. 
Bạn đánh giá thế nào về năng lực tính toán phi thường của thế hệ siêu chip này? Hãy chia sẻ quan điểm của bạn nhé!"""

        else:
            short_title = clean_title[:28].upper()
            headline = "BƯỚC TIẾN CÔNG NGHỆ MỚI"
            sub_headline = short_title
            stat = "ĐỘT PHÁ"
            stat_desc = "CÔNG NGHỆ TIÊN TIẾN"
            stat_2 = "TOÀN CẦU"
            stat_desc_2 = "GÂY ẤN TƯỢNG MẠNH"
            comp_old = "Giới hạn công nghệ cũ"
            comp_new = "Cải tiến vượt bậc hiện tại"
            evidence_q = "Cộng đồng nghiên cứu quốc tế đã tiến hành thử nghiệm và ghi nhận mức độ ổn định ấn tượng trên các kịch bản thực tế."
            evidence_src = "Báo cáo thử nghiệm quốc tế"
            script = f"""Thế giới công nghệ vừa ghi nhận một bước ngoặt đáng chú ý trong tiến trình phát triển của trí tuệ nhân tạo toàn cầu. 
Sự kiện công bố giải pháp: {clean_title[:65]} đang thu hút sự quan tâm đặc biệt từ giới nghiên cứu và các quỹ đầu tư mạo hiểm. 
Nhờ việc cải tiến sâu về mặt thuật toán và phương pháp tối ưu hóa dữ liệu, giải pháp mới mang lại hiệu quả vượt trội trong vận hành. 
Các thử nghiệm sơ bộ từ cộng đồng độc lập cho thấy thời gian xử lý tác vụ được rút ngắn đáng kể trong khi độ chính xác được nâng cao rõ rệt. 
Nhiều chuyên gia công nghệ đánh giá đây sẽ là tiền đề quan trọng để đẩy nhanh tốc độ ứng dụng AI vào các hoạt động thực tiễn. 
Theo các nguồn phân tích uy tín, cuộc chạy đua đổi mới sáng tạo giữa các phòng thí nghiệm hàng đầu đang diễn ra quyết liệt hơn bao giờ hết. 
Đây là minh chứng rõ nét cho thấy làn sóng cách mạng công nghệ số đang tiếp tục định hình lại phương thức làm việc của tương lai. 
Còn bạn, bạn đánh giá thế nào về tiềm năng ứng dụng của bước tiến công nghệ này? Hãy để lại bình luận để cùng trao đổi nhé!"""

    return {
        "title": title,
        "headline": headline,
        "sub_headline": sub_headline,
        "stat": stat,
        "stat_desc": stat_desc,
        "stat_2": stat_2,
        "stat_desc_2": stat_desc_2,
        "compare_old": comp_old,
        "compare_new": comp_new,
        "evidence_quote": evidence_q,
        "evidence_source": evidence_src,
        "source_pill": f"Nguồn: {source}",
        "script_text": script,
        "link": news.get("link", ""),
    }


def auto_crawl_and_produce_video(
    on_progress: Optional[Callable[[str], None]] = None,
    render_mode: str = "news_short",
    min_duration_seconds: int = 120,
) -> Dict[str, Any]:
    """
    1-Click Autonomous Engine:
    1. Scans global AI news (RSS).
    2. Picks 1 unpicked story and records it to DB to prevent duplicate coverage.
    3. Crafts Vietnamese script & kinetic typography (via LLM api.buihuuthang.com or rule-based).
    4. Automatically renders 1080x1920 video (NewsShort Bento HUD by default, or Douyin Remake).
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if on_progress:
        on_progress("Đang quét các nguồn tin AI quốc tế mới nhất (Google News, TechCrunch, HackerNews)...")

    # Step 1 & 2: Pick unpicked news
    news_item = get_next_unprocessed_news()
    news_id = news_item["id"]

    if on_progress:
        on_progress(f"Đã chọn tin mới: \"{news_item['title'][:55]}...\" - Đang soạn kịch bản chuyên sâu...")

    # Step 3: Craft script & typography with evidence and >= 120s duration
    crafted = translate_and_craft_vietnamese_script(news_item, min_duration_seconds=min_duration_seconds)

    timestamp = int(time.time())
    out_name = f"auto_ai_news_{timestamp}.mp4"
    out_file = OUTPUT_DIR / out_name

    script_file = OUTPUT_DIR / f"auto_ai_{timestamp}_script.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(crafted["script_text"])

    if render_mode == "news_short":
        if on_progress:
            on_progress("Đang tổng hợp giọng đọc tiếng Việt Edge-TTS (chuẩn 60s+) và tạo khung HUD Bento tin tức...")

        meta_file = OUTPUT_DIR / f"auto_ai_{timestamp}_meta.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(crafted, f, ensure_ascii=False, indent=2)

        rate_val = "+8%" if min_duration_seconds >= 120 else "+12%"
        cmd = [
            str(PYTHON_EXE),
            str(ROOT_DIR / "create_news_video.py"),
            "--text", crafted["script_text"],
            "--tag", "TIN AI NÓNG",
            "--title", crafted.get("headline", crafted.get("title", "TIN TỨC CÔNG NGHỆ AI")),
            "--source", crafted.get("source_pill", "Nguồn: Tin Công Nghệ"),
            "--meta", str(meta_file),
            "--voice", "vi-VN-NamMinhNeural",
            "--rate", rate_val,
            "--output", str(out_file),
        ]
    else:
        sample_videos = list(ROOT_DIR.glob("sample_douyin_video*.mp4")) + list(ROOT_DIR.glob("sample_*.mp4"))
        valid_videos = [v for v in sample_videos if v.stat().st_size > 10 * 1024 * 1024]
        chosen_video = valid_videos[0] if valid_videos else (ROOT_DIR / "sample_douyin_video01.mp4")

        punches_file = OUTPUT_DIR / f"auto_ai_{timestamp}_punches.json"
        with open(punches_file, "w", encoding="utf-8") as f:
            json.dump(crafted.get("punches", []), f, ensure_ascii=False, indent=2)

        banners_file = OUTPUT_DIR / f"auto_ai_{timestamp}_banners.json"
        with open(banners_file, "w", encoding="utf-8") as f:
            json.dump(crafted.get("banners", []), f, ensure_ascii=False, indent=2)

        if on_progress:
            on_progress("Đang tổng hợp giọng đọc tiếng Việt Edge-TTS và tạo chữ giật 2 tầng...")

        cmd = [
            str(PYTHON_EXE),
            str(ROOT_DIR / "remake_douyin_video.py"),
            "--video", str(chosen_video),
            "--text", str(script_file),
            "--source", crafted["source_pill"],
            "--voice", "vi-VN-NamMinhNeural",
            "--rate", "+20%",
            "--punches", str(punches_file),
            "--banners", str(banners_file),
            "--output", str(out_file),
        ]

    if on_progress:
        on_progress("Đang render Remotion Full HD 1080x1920 (30fps)...")

    proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)

    # Step 6: Mark as processed in database
    history = load_processed_history()
    if news_id not in history.get("processed_ids", []):
        history.setdefault("processed_ids", []).append(news_id)
        history.setdefault("items", []).append({
            "id": news_id,
            "title": news_item["title"],
            "source": news_item.get("source", ""),
            "link": news_item.get("link", ""),
            "video_url": f"/videos/{out_name}",
            "video_name": out_name,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        save_processed_history(history)

    return {
        "status": "success",
        "news_id": news_id,
        "news_title": news_item["title"],
        "source": news_item.get("source", ""),
        "link": news_item.get("link", ""),
        "video_url": f"/videos/{out_name}",
        "video_name": out_name,
        "script": crafted["script_text"]
    }
