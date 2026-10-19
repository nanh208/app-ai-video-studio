import time
from ai_news_crawler import auto_crawl_and_produce_video

def on_prog(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

print("==================================================")
print("🚀 RUNNING 2-MINUTE AUTONOMOUS AI NEWS CRAWLER")
print("Target duration: >= 120s (2 minutes)")
print("==================================================")

res = auto_crawl_and_produce_video(on_progress=on_prog, min_duration_seconds=120)

print("\n" + "="*50)
print("🏆 VIDEO PRODUCED SUCCESSFULLY!")
print("Title:    ", res.get("news_title"))
print("Video URL:", res.get("video_url"))
print("Video File:", res.get("video_name"))
print("="*50)
