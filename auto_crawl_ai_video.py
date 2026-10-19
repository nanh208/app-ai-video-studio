"""
Autonomous AI News Video Generator (CLI)
Usage:
  python auto_crawl_ai_video.py
Automatically scans global AI news, picks a fresh story (never duplicated),
writes a viral Vietnamese script, and renders a 1080x1920 video!
"""

import sys
from ai_news_crawler import auto_crawl_and_produce_video

def main():
    print("==================================================")
    print("🤖 AUTONOMOUS AI NEWS VIDEO ROBOT")
    print("Quét tin AI thế giới ➔ Lọc trùng ➔ Lên kịch bản ➔ Dựng video")
    print("==================================================")

    def print_progress(msg: str):
        print(f"⏳ {msg}")

    try:
        res = auto_crawl_and_produce_video(on_progress=print_progress)
        print("\n🎉 HOÀN THÀNH XUẤT SẮC!")
        print(f"Tin tức:   {res['news_title']}")
        print(f"Nguồn:     {res['source']}")
        print(f"Video MP4: {res['video_url']}")
        print(f"File gốc:  d:\\aivideo\\output\\{res['video_name']}")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
