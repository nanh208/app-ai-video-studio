import subprocess
from pathlib import Path

ROOT = Path("d:/aivideo")
REF_DIR = ROOT / "reference_videos"
REF_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_VIDEO = ROOT / "sample_drive_learning.mp4"

# 12 diverse micro-segments from the learned reference video
scenes = [
    (0.0, 3.8, "douyin_pack_01.mp4"),
    (3.8, 7.5, "douyin_pack_02.mp4"),
    (8.0, None, "xinhua_headline.jpg"),
    (11.5, None, "xinhua_illustration.jpg"),
    (15.0, None, "phoenix_article_top.jpg"),
    (18.5, None, "phoenix_article_body.jpg"),
    (22.0, 26.5, "youtube_elliot_01.mp4"),
    (26.5, 31.5, "youtube_elliot_02.mp4"),
    (31.5, 36.8, "youtube_elliot_03.mp4"),
    (37.0, 42.0, "youtube_lego_unboxing.mp4"),
    (42.0, 47.8, "youtube_home_haul.mp4"),
]

for start, end, name in scenes:
    target = REF_DIR / name
    if name.endswith(".mp4"):
        cmd = ["ffmpeg", "-ss", str(start), "-to", str(end), "-i", str(SAMPLE_VIDEO), "-c", "copy", str(target), "-y"]
    else:
        cmd = ["ffmpeg", "-ss", str(start), "-i", str(SAMPLE_VIDEO), "-vframes", "1", "-q:v", "2", str(target), "-y"]
    subprocess.run(cmd, capture_output=True)
    if target.exists():
        print(f"Created {target.name} ({target.stat().st_size} bytes)")

print("Scene library ready!")
