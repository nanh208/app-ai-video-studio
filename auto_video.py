"""
CLI tool for 1-Click Prompt-To-Video Generation
Usage:
  python auto_video.py "Trào lưu mua sắm China Haul"
  python auto_video.py "Cảnh báo AI mất kiểm soát từ CEO Microsoft"
  python auto_video.py "https://vnexpress.net/..."
"""

import argparse
import sys
from auto_video_engine import run_auto_pipeline

def main():
    parser = argparse.ArgumentParser(description="1-Click Prompt-To-Video Auto Generator")
    parser.add_argument("prompt", type=str, help="Single sentence prompt, topic idea, or URL")
    args = parser.parse_args()

    print("==================================================")
    print("🚀 1-CLICK PROMPT-TO-VIDEO AUTO GENERATOR")
    print(f"Câu lệnh: \"{args.prompt}\"")
    print("==================================================")

    def print_progress(msg: str):
        print(f"⏳ {msg}")

    try:
        res = run_auto_pipeline(args.prompt, on_progress=print_progress)
        print("\n🎉 HOÀN THÀNH XUẤT SẮC!")
        print(f"Tiêu đề:  {res['title']}")
        print(f"File MP4: {res['video_url']}")
        print(f"File cục bộ: d:\\aivideo\\output\\{res['video_name']}")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
