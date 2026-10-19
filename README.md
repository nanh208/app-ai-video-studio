# 🎬 AI Video Studio (OpenMontage Edition)

> **Hệ thống tự động hóa sản xuất video ngắn 9:16 chuyên nghiệp (TikTok, YouTube Shorts, Reels) bằng Remotion, Edge-TTS, FastAPI và LLM.**

---

## 🌟 Điểm nổi bật & Tính năng chính

- 🤖 **Robot quét tin AI & tự dựng video (Zero-Input):**
  - Tự động quét tin tức công nghệ AI toàn cầu mới nhất (Google News, TechCrunch, The Verge, Reuters...).
  - Tự động đối chiếu lịch sử để loại bỏ hoàn toàn tin trùng lặp.
  - Tự động viết kịch bản phân tích chuyên sâu 5 hồi với đầy đủ dẫn chứng kiểm chứng độc lập.
  - Hỗ trợ tùy chọn độ dài: **60s (Tin vắn)**, **90s (Bản tin tiêu chuẩn)**, **120s (Phân tích chuyên sâu 2 phút)**, và **180s (Phóng sự 3 phút)**.
- 🔥 **Bộ máy Remake Douyin / TikTok cao cấp:**
  - **Cắt dựng đa nguồn B-roll:** Phối hợp nhịp nhàng giữa video thực tế, bài báo mạng và clip phản ứng của YouTuber mỗi 3–5 giây.
  - **5 Cú đấm số liệu cực đại (`Giant Stat Punches`):** Hiệu ứng số liệu nhảy bật lò xo (Spring pop) giữa khung hình thu hút người xem.
  - **Chữ giật Kinetic Typography 2 tầng:** Chữ trắng viền đen dày kết hợp tầng vàng rực rỡ.
  - **Giao diện đọc báo điện tử (`News Mockup Cards`):** Giả lập thanh URL Safari/Chrome với domain thực tế (`news.cn`, `ifeng.com`).
  - **Hiệu ứng xóa viền mờ `Letterbox Blur`:** Giúp video 16:9 hiển thị sang trọng, vừa vặn trên khung hình dọc 9:16.
- 🎙️ **Giọng đọc AI & Phụ đề Karaoke chuẩn Safe Zone:**
  - Giọng thuyết minh tiếng Việt tự nhiên (`vi-VN-NamMinhNeural` / `vi-VN-HoaiMyNeural`).
  - Phụ đề Karaoke nảy chữ vàng rực rỡ, canh chuẩn vị trí an toàn (`bottom: 200px`) không bao giờ bị che bởi icon giao diện mạng xã hội.
- 🎨 **Web Studio UI Trực quan:**
  - Giao diện web chạy trên FastAPI (`http://127.0.0.1:8000`) quản lý tác vụ ngầm.
  - Tích hợp Remotion Studio (`http://localhost:3000`) cho phép xem trước và can thiệp timeline theo thời gian thực.

---

## 🚀 Cài đặt & Khởi động nhanh

### 1. Yêu cầu hệ thống
- **Python:** 3.10 trở lên
- **Node.js:** 18 trở lên (đã cài đặt npm / npx)
- **FFmpeg:** Đã thêm vào biến môi trường hệ thống (PATH)

### 2. Cài đặt thư viện Python
```bash
# Tạo và kích hoạt môi trường ảo
python -m venv .venv
# Trên Windows:
.venv\Scripts\activate
# Trên macOS/Linux:
source .venv/bin/activate

# Cài đặt các gói phụ thuộc
pip install fastapi uvicorn edge-tts requests openai pydantic
```

### 3. Cài đặt Remotion Studio
```bash
cd OpenMontage/remotion-composer
npm install
```

### 4. Khởi chạy ứng dụng
```bash
# 1. Khởi động Web Studio UI (cổng 8000)
python -m uvicorn studio_ui:app --host 127.0.0.1 --port 8000

# 2. Khởi động Remotion Studio Preview (cổng 3000)
cd OpenMontage/remotion-composer
npx remotion studio
```
Truy cập trình duyệt tại: **`http://127.0.0.1:8000`** để bắt đầu sáng tạo video!

---

## 📁 Cấu trúc thư mục dự án

```text
├── studio_ui.py                   # Máy chủ FastAPI & API điều khiển Web UI
├── ai_news_crawler.py             # Robot quét tin AI tự động & sinh kịch bản
├── ai_service.py                  # Cổng kết nối LLM (DeepSeek, GPT-4o, Claude) & sinh ảnh AI
├── create_news_video.py           # Bộ dựng video tin tức Bento HUD Full HD
├── remake_douyin_video.py         # Bộ dựng video Remake Douyin đa nguồn
├── produce_2m_deepdive_video.py   # Pipeline sản xuất video tài liệu chuyên sâu 2 phút
├── templates/
│   └── index.html                 # Giao diện Web Studio UI tương tác
├── OpenMontage/
│   └── remotion-composer/         # Engine React/TypeScript Remotion
│       └── src/
│           ├── DouyinRemake.tsx   # Composition Remake Douyin (Letterbox blur, Stat punches)
│           ├── NewsShort.tsx      # Composition Bento HUD tin tức
│           └── Root.tsx           # Khai báo metadata & timeline
└── output/                        # Thư mục chứa các video MP4 đã xuất thành phẩm
```

---

## 🔑 Cấu hình API Key (Tùy chọn)
Để kích hoạt trí tuệ nhân tạo viết kịch bản thông minh bằng DeepSeek / GPT-4o:
1. Mở thẻ **"Cài Đặt & Check API Key"** trên giao diện Web UI (`http://127.0.0.1:8000`).
2. Dán API Key OpenAI-compatible (hoặc từ cổng `api.buihuuthang.com`).
3. Nhấn **Lưu & Test Key** để kích hoạt!
# app-ai-video-studio
