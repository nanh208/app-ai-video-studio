"""
AI Service Provider for api.buihuuthang.com & OpenAI-compatible Gateways
Handles:
- Key verification & health check
- Intelligent Vietnamese news scriptwriting (GPT-4o, Claude 3.5, Gemini via gateway)
- Automated image generation for news illustrations (DALL-E 3 / Flux)
"""

import os
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, List

ROOT_DIR = Path(__file__).resolve().parent
ENV_FILE = ROOT_DIR / "OpenMontage" / ".env"

DEFAULT_BASE_URL = "https://api.buihuuthang.com/v1"


def get_configured_credentials() -> tuple[Optional[str], str]:
    """Reads OPENAI_API_KEY and OPENAI_BASE_URL from .env or os.environ."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "")

    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("OPENAI_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and not api_key:
                        api_key = val
                elif line.startswith("OPENAI_BASE_URL="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and not base_url:
                        base_url = val

    if not base_url:
        base_url = DEFAULT_BASE_URL

    return api_key if api_key else None, base_url


def save_credentials(api_key: str, base_url: str = DEFAULT_BASE_URL) -> None:
    """Saves API key and Base URL to OpenMontage/.env."""
    lines = []
    found_key = False
    found_base = False

    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("OPENAI_API_KEY="):
            new_lines.append(f"OPENAI_API_KEY={api_key.strip()}\n")
            found_key = True
        elif line.startswith("OPENAI_BASE_URL="):
            new_lines.append(f"OPENAI_BASE_URL={base_url.strip()}\n")
            found_base = True
        else:
            new_lines.append(line)

    if not found_key:
        new_lines.append(f"OPENAI_API_KEY={api_key.strip()}\n")
    if not found_base:
        new_lines.append(f"OPENAI_BASE_URL={base_url.strip()}\n")

    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Also update current process environment
    if api_key.strip():
        os.environ["OPENAI_API_KEY"] = api_key.strip()
    else:
        os.environ.pop("OPENAI_API_KEY", None)
    os.environ["OPENAI_BASE_URL"] = base_url.strip()


def check_api_connection(api_key: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
    """Tests connection to the api.buihuuthang.com gateway."""
    import time
    current_key, current_base = get_configured_credentials()
    key_to_test = api_key if api_key else current_key
    base_to_test = (base_url if base_url else current_base).rstrip("/")

    if not key_to_test:
        return {
            "status": "missing_key",
            "message": "Chưa có API key. Vui lòng nhập API key từ https://api.buihuuthang.com.",
            "base_url": base_to_test,
        }

    # Endpoint test: GET /models
    url = f"{base_to_test}/models"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {key_to_test.strip()}",
            "User-Agent": "AIVideoStudio/1.0",
        },
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            latency_ms = int((time.time() - t0) * 1000)
            data = json.loads(resp.read().decode("utf-8"))
            models = []
            if isinstance(data, dict) and "data" in data:
                models = [m.get("id") for m in data["data"] if isinstance(m, dict) and m.get("id")]
            
            # Mask key for safety
            masked = key_to_test[:7] + "..." + key_to_test[-4:] if len(key_to_test) > 12 else "***"

            # Filter popular models
            popular = [
                m for m in models if any(k in m.lower() for k in [
                    "gpt-4o", "claude-3-5", "gemini-2", "gemini-1.5", "deepseek", "dall-e", "flux"
                ])
            ]
            if not popular:
                popular = models[:12]

            return {
                "status": "connected",
                "message": "Kết nối thành công tới cổng API https://api.buihuuthang.com!",
                "base_url": base_to_test,
                "masked_key": masked,
                "latency_ms": latency_ms,
                "total_models": len(models),
                "popular_models": popular[:15],
                "all_models": models[:40],
            }
    except urllib.error.HTTPError as e:
        latency_ms = int((time.time() - t0) * 1000)
        err_msg = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_msg)
            msg = err_json.get("error", {}).get("message", err_msg)
        except Exception:
            msg = err_msg or f"HTTP Error {e.code}"
        return {
            "status": "error",
            "message": f"Lỗi xác thực API ({e.code}): {msg}",
            "base_url": base_to_test,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "status": "error",
            "message": f"Không thể kết nối tới {base_to_test}: {e}",
            "base_url": base_to_test,
            "latency_ms": latency_ms,
        }


def test_chat_completion(prompt: str = "Chào bạn! Hãy giới thiệu ngắn gọn 1 câu về sức mạnh của AI trong việc sản xuất video tự động.", model: Optional[str] = None) -> Dict[str, Any]:
    """Sends a live test prompt to api.buihuuthang.com to verify model response and latency."""
    import time
    api_key, base_url = get_configured_credentials()
    if not api_key:
        return {"status": "error", "message": "Chưa có API key để kiểm tra."}

    t0 = time.time()
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)

        # If model is not set or not valid, resolve available models
        target_model = model
        if not target_model or target_model in ["gpt-4o-mini", "gpt-4o"]:
            try:
                available = [m.id for m in client.models.list().data]
                if target_model not in available:
                    # Pick best available DeepSeek model
                    for preferred in ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-v4.1-flash", "deepseek-chat"]:
                        if preferred in available:
                            target_model = preferred
                            break
                    if not target_model and available:
                        target_model = available[0]
            except Exception:
                target_model = "deepseek-v4-flash"

        resp = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        latency_ms = int((time.time() - t0) * 1000)
        reply = resp.choices[0].message.content.strip()
        tokens = resp.usage.total_tokens if resp.usage else None

        return {
            "status": "success",
            "reply": reply,
            "model": target_model,
            "latency_ms": latency_ms,
            "tokens": tokens,
        }
    except Exception as e:
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "status": "error",
            "message": f"Lỗi gọi model {model}: {e}",
            "latency_ms": latency_ms,
        }


def llm_craft_vietnamese_script(
    news_title: str,
    news_summary: str,
    source: str,
    min_duration_seconds: int = 60
) -> Optional[Dict[str, Any]]:
    """
    Calls DeepSeek / GPT / Claude via api.buihuuthang.com to write a viral Vietnamese news script
    with dynamic kinetic punch typography, evidence citations, and yellow banners.
    Supports in-depth 60s+ editorial mode with concrete benchmarks and independent verifications.
    """
    api_key, base_url = get_configured_credentials()
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)

        # Get list of valid models from gateway
        available_models = []
        try:
            available_models = [m.id for m in client.models.list().data]
        except Exception:
            available_models = ["deepseek-v4-flash", "deepseek-v4-pro"]

        # Prioritize DeepSeek models available on buihuuthang.com
        candidate_models = []
        for pref in ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-v4.1-flash", "deepseek-chat", "buihuuthang/gpt-5.6-luna", "gpt-4o-mini"]:
            if pref in available_models:
                candidate_models.append(pref)
        if not candidate_models and available_models:
            candidate_models = available_models[:3]

        if min_duration_seconds >= 120:
            prompt = f"""Bạn là một đạo diễn tài liệu và nhà phân tích công nghệ AI xuất sắc (theo phong cách phóng sự điều tra kịch tính của ColdFusion, Vox, MagnatesMedia, Bloomberg Quicktake).
Hãy chuyển hóa thông tin bài viết dưới đây thành một kịch bản video dọc 9:16 DẪN DẮT CỰC KỲ LÔI CUỐN, GIÀU KỊCH TÍNH, ĐẦY ĐỦ BẰNG CHỨNG XÁC THỰC VÀ ĐẢO LỘN TƯ DUY NGƯỜI XEM.

Tiêu đề gốc: {news_title}
Nội dung chi tiết: {news_summary}
Nguồn tin: {source}

NGHỆ THUẬT DẪN DẮT NỘI DUNG (STORYTELLING ARCS):
1. ĐỘ DÀI BẮT BUỘC: 380 đến 450 từ tiếng Việt (đọc trong khoảng 125-145 giây, gồm 12-16 câu văn sắc sảo).
2. NGUYÊN TẮC VÀNG VỀ LỐI DẪN DẮT:
   - TUYỆT ĐỐI KHÔNG dùng các từ cứng nhắc như "Chương 1", "Chương 2", "Về benchmark", "Về kiến trúc", "Về chi phí".
   - MỞ ĐẦU (HOOK SỐC 0-10s): Đặt ngay một nghịch lý gây chấn động hoặc câu hỏi kịch tính (ví dụ: Làm thế nào một nhóm kỹ sư vô danh với 6 triệu đô la vừa giáng đòn chí mạng vào đế chế hàng trăm tỷ đô của Thung lũng Silicon?).
   - LẬT TẨY NGHỊCH LÝ: Phơi bày sự ảo tưởng của các tập đoàn lớn vốn tin rằng "chỉ có hàng trăm ngàn chip đắt đỏ mới tạo ra siêu trí tuệ".
   - BẰNG CHỨNG ĐỐI ĐẦU ĐANH THÉP: Dẫn chứng điểm số toán AIME 2024 (79.8% so kè 79.2% của OpenAI o1), bài thi MATH-500 chạm mốc 97.3% và Codeforces.
   - BÍ MẬT THUẬT TOÁN & KHOẢNH KHẮC "AHA": Phân tích kiến trúc MoE 671 tỷ tham số cùng cơ chế MLA tiết kiệm 93% bộ nhớ; mô tả khoảnh khắc kỳ diệu khi DeepSeek-R1-Zero tự học tư duy và thốt lên "hãy để tôi nghĩ lại" mà không cần con người gán nhãn!
   - CÚ TÁT VÀO TÚI TIỀN (KINH TẾ): So sánh rợn ngườI giữa 15 đô la và 0.55 đô la trên mỗi triệu token (rẻ hơn 27 lần), làm bốc hơi hàng trăm tỷ USD vốn hóa Phố Wall.
   - CUỘC NỔI LOẠN MÃ NGUỒN MỞ: Giấy phép MIT mở hoàn toàn, Đại học Stanford và cộng đồng toàn cầu xác nhận bất kỳ ai cũng có thể chạy mô hình trên laptop cá nhân.
   - KẾT LUẬN & THỨC TỈNH: Một câu chốt đắt giá về việc kỷ nguyên độc quyền AI đã sụp đổ và câu hỏi mở kích thích người xem tranh luận.
3. CHÍNH TẢ & THUẬT NGỮ: Giữ nguyên chuẩn quốc tế: AI, OpenAI, DeepSeek, Anthropic, Claude, ChatGPT, Gemini, CEO, GPU, API, AIME, USD, MoE, MLA, MIT. Tuyệt đối KHÔNG phiên âm sai.

Yêu cầu xuất định dạng JSON DUY NHẤT:
{{
  "headline": "TIÊU ĐỀ HOA 3-5 TỪ",
  "sub_headline": "DÒNG PHỤ HOA 3-5 TỪ",
  "stat": "CON SỐ HOẶC TỪ KHÓA SỐ LIỆU 1",
  "stat_desc": "CHÚ THÍCH SỐ LIỆU 1 (DƯỚI 6 TỪ)",
  "stat_2": "CON SỐ HOẶC TỪ KHÓA SỐ LIỆU 2",
  "stat_desc_2": "CHÚ THÍCH SỐ LIỆU 2 (DƯỚI 6 TỪ)",
  "compare_old": "HẠN CHẾ / CHI PHÍ TRƯỚC ĐÂY",
  "compare_new": "ĐỘT PHÁ / CHI PHÍ HIỆN TẠI",
  "evidence_quote": "TRÍCH DẪN DẪN CHỨNG KIỂM CHỨNG ĐỘC LẬP",
  "evidence_source": "NGUỒN DẪN CHỨNG (ví dụ: Đại học Stanford / Financial Times)",
  "script_text": "Toàn văn 380-450 từ tiếng Việt viết liền mạch theo lối kể chuyện điện ảnh kịch tính, cuốn hút từng câu chữ, không chứa tiêu đề mục chương."
}}
"""
        elif min_duration_seconds >= 60:
            prompt = f"""Bạn là một biên tập viên tin tức công nghệ và trí tuệ nhân tạo (AI) cao cấp, chuyên nghiệp (theo chuẩn báo chí quốc tế Reuters, TechCrunch, The Verge, Bloomberg).
Hãy phân tích thông tin dưới đây và biên tập thành kịch bản video dọc 9:16 CHUYÊN SÂU với ĐẦY ĐỦ DẪN CHỨNG XÁC THỰC, SỐ LIỆU ĐO LƯỜNG VÀ ĐỒNG NHẤT VỀ CHỦ ĐỀ.

Tiêu đề gốc: {news_title}
Nội dung chi tiết: {news_summary}
Nguồn tin: {source}

YÊU CẦU NỘI DUNG VÀ ĐỘ DÀI:
1. ĐỘ DÀI BẮT BUỘC: Từ 220 đến 260 từ tiếng Việt (BẮT BUỘC để khi đọc đạt thời lượng từ 70 đến 85 giây, khoảng 8-10 câu văn hoàn chỉnh).
2. DẪN CHỨNG RÕ RÀNG VÀ CHÍNH XÁC:
   - Dẫn chứng 1 (Bối cảnh & Đột phá kỹ thuật): Nêu rõ công nghệ/kiến trúc cốt lõi (ví dụ: MoE, Reinforcement Learning CoT, phần cứng GPU, quy trình đào tạo).
   - Dẫn chứng 2 (Số liệu & Benchmark cụ thể): Nêu con số định lượng (điểm số AIME, MATH, HumanEval, tỷ lệ phần trăm cải thiện, chi phí tính toán bằng USD).
   - Dẫn chứng 3 (Kiểm chứng độc lập & Uy tín): Trích dẫn nhận định từ bên thứ ba uy tín (Đại học Stanford, MIT, các nhà khoa học, Financial Times, cộng đồng mã nguồn mở).
   - Dẫn chứng 4 (So sánh đối đầu trực diện): So sánh rõ ràng với các mô hình hoặc hệ thống khác (OpenAI, Google, NVIDIA, Anthropic).
   - Dẫn chứng 5 (Tác động thị trường & Tương lai): Ảnh hưởng tới chuỗi cung ứng, cổ phiếu công nghệ hoặc bài toán cạnh tranh toàn cầu.
3. TÍNH ĐỒNG NHẤT: Toàn bộ kịch bản phải xoay quanh đúng một chủ đề duy nhất một cách xuyên suốt, không lạc đề hay nhảy sang nội dung không liên quan.
4. CHÍNH TẢ & THUẬT NGỮ: Giữ nguyên chuẩn xác: AI, OpenAI, DeepSeek, Anthropic, Claude, ChatGPT, Gemini, CEO, GPU, API, AIME, USD. Tuyệt đối KHÔNG viết phiên âm sai.

Yêu cầu xuất định dạng JSON DUY NHẤT (không kèm giải thích ngoài json):
{{
  "headline": "TIÊU ĐỀ HOA 3-5 TỪ",
  "sub_headline": "DÒNG PHỤ HOA 3-5 TỪ",
  "stat": "CON SỐ HOẶC TỪ KHÓA SỐ LIỆU 1",
  "stat_desc": "CHÚ THÍCH SỐ LIỆU 1 (DƯỚI 6 TỪ)",
  "stat_2": "CON SỐ HOẶC TỪ KHÓA SỐ LIỆU 2",
  "stat_desc_2": "CHÚ THÍCH SỐ LIỆU 2 (DƯỚI 6 TỪ)",
  "compare_old": "HẠN CHẾ / CHI PHÍ TRƯỚC ĐÂY",
  "compare_new": "ĐỘT PHÁ / CHI PHÍ HIỆN TẠI",
  "evidence_quote": "TRÍCH DẪN DẪN CHỨNG KIỂM CHỨNG ĐỘC LẬP",
  "evidence_source": "NGUỒN DẪN CHỨNG (ví dụ: Stanford AI Lab / Báo cáo kỹ thuật)",
  "script_text": "Toàn văn 220-260 từ tiếng Việt mạch lạc, sắc sảo, giàu dẫn chứng và số liệu."
}}
"""
        else:
            prompt = f"""Bạn là một biên tập viên tin tức công nghệ và trí tuệ nhân tạo chuyên nghiệp, uy tín (theo chuẩn báo chí quốc tế TechCrunch, The Verge, Reuters).
Hãy phân tích thông tin bài báo quốc tế dưới đây và biên tập thành kịch bản video tin tức dọc 9:16 sắc bén, mạch lạc, thông tin rõ ràng, chuẩn xác (độ dài 50-65 từ, gồm đúng 4 câu có cấu trúc logic):

Tiêu đề gốc: {news_title}
Nội dung chi tiết: {news_summary}
Nguồn tin: {source}

YÊU CẦU NỘI DUNG:
1. Câu 1 (Sự kiện chính): Nêu rõ ai ra mắt / công bố / đạt bước tiến gì nổi bật (khách quan, ấn tượng nhưng không giật gân rẻ tiền).
2. Câu 2 (Bản chất công nghệ): Giải thích ngắn gọn cách hoạt động hoặc điểm đột phá cốt lõi.
3. Câu 3 (Số liệu & Hiệu năng): Nêu số liệu, benchmark, hoặc cải tiến cụ thể (ví dụ: tốc độ, chi phí, quy mô).
4. Câu 4 (Nhận định & Tương lai): Một câu đúc kết ngắn gọn và câu hỏi mở kích thích thảo luận.
5. CHÍNH TẢ: Giữ nguyên tên chuẩn: AI, OpenAI, DeepSeek, Anthropic, Claude, Gemini, CEO, GPU, API. Tuyệt đối KHÔNG viết phiên âm sai như "ây ai", "xi i ô".

Yêu cầu xuất định dạng JSON DUY NHẤT (không kèm giải thích ngoài json):
{{
  "headline": "TIÊU ĐỀ HOA 3-5 TỪ",
  "sub_headline": "DÒNG PHỤ HOA 3-5 TỪ",
  "stat": "CON SỐ HOẶC TỪ KHÓA SỐ LIỆU ĐỘT PHÁ",
  "stat_desc": "CHÚ THÍCH NGẮN CHO SỐ LIỆU (DƯỚI 8 TỪ)",
  "compare_old": "HẠN CHẾ TRƯỚC ĐÂY",
  "compare_new": "ĐỘT PHÁ MỚI HIỆN TẠI",
  "script_text": "Toàn văn 4 câu tiếng Việt mạch lạc, chuyên nghiệp, thông tin rõ ràng."
}}
"""
        for model in candidate_models:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a professional tech editor. Output pure valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                )
                raw_content = response.choices[0].message.content.strip()
                clean_json = re.sub(r"^```json\s*", "", raw_content)
                clean_json = re.sub(r"^```\s*", "", clean_json)
                clean_json = re.sub(r"\s*```$", "", clean_json)
                data = json.loads(clean_json)
                data["source_pill"] = f"Nguồn: {source}"
                
                # Validate script word count against requested duration
                word_count = len(data.get("script_text", "").split())
                if min_duration_seconds >= 180 and word_count < 450:
                    print(f"[LLM] Model {model} produced only {word_count} words (< 450 for 180s target), retrying...")
                    continue
                if min_duration_seconds >= 120 and word_count < 320:
                    print(f"[LLM] Model {model} produced only {word_count} words (< 320 for 120s target), retrying...")
                    continue
                if min_duration_seconds >= 90 and word_count < 240:
                    print(f"[LLM] Model {model} produced only {word_count} words (< 240 for 90s target), retrying...")
                    continue

                print(f"[LLM] Successfully crafted clean editorial script ({word_count} words) using model {model}!")
                return data
            except Exception as e:
                print(f"[LLM] Model {model} failed: {e}")
                continue

    except Exception as e:
        print(f"Warning: LLM scriptwriting failed via gateway: {e}")

    return None


def generate_ai_news_illustration(news_title: str, headline: str, output_path: Path) -> Optional[Path]:
    """
    Generates a high-quality 1024x1024 tech editorial visual using req/gpt-image-2
    via api.buihuuthang.com. Saves base64 PNG directly to output_path.
    """
    import base64
    api_key, base_url = get_configured_credentials()
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=25.0)

        image_prompt = (
            f"Editorial tech visual for {headline}. "
            f"Topic: {news_title}. "
            f"Futuristic technology, cyber AI interfaces, dark tech room, glowing neon data screens, "
            f"cinematic studio lighting, 8k vertical poster composition, professional journalism photo, high resolution"
        )
        print(f"[AI Visual] Generating visual illustration via api.buihuuthang.com ({headline})...")
        res = client.images.generate(
            model="req/gpt-image-2",
            prompt=image_prompt,
            size="1024x1024",
            n=1
        )
        if res.data and res.data[0].b64_json:
            img_bytes = base64.b64decode(res.data[0].b64_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(img_bytes)
            print(f"[AI Visual] Successfully saved illustration to {output_path} ({len(img_bytes)/1024:.1f} KB)")
            return output_path
    except Exception as e:
        print(f"[AI Visual] Image generation skipped or failed: {e}")

    return None

