import asyncio
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Fix Windows Python 3.14 asyncio ConnectionResetError bug on video streaming
if sys.platform == "win32":
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_call_conn_lost = _ProactorBasePipeTransport._call_connection_lost

        def _patched_call_conn_lost(self, exc):
            try:
                _orig_call_conn_lost(self, exc)
            except (ConnectionResetError, OSError):
                pass

        _ProactorBasePipeTransport._call_connection_lost = _patched_call_conn_lost
    except Exception:
        pass

from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output"
SAMPLE_FRAMES_DIR = ROOT_DIR / "sample_frames"
COMPOSER_DIR = ROOT_DIR / "OpenMontage" / "remotion-composer"
PYTHON_EXE = ROOT_DIR / "OpenMontage" / ".venv" / "Scripts" / "python.exe"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_FRAMES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Video Studio")

# Static files mounts
app.mount("/videos", StaticFiles(directory=str(OUTPUT_DIR)), name="videos")
app.mount("/sample_frames", StaticFiles(directory=str(SAMPLE_FRAMES_DIR)), name="sample_frames")

# In-memory job tracker
jobs = {}

from auto_video_engine import run_auto_pipeline

class AutoRequest(BaseModel):
    prompt: str

class RemakeRequest(BaseModel):
    video_path: str
    script_text: str
    source_credit: str = "Nguồn: Douyin"
    voice: str = "vi-VN-NamMinhNeural"
    rate: str = "+20%"
    custom_punches: Optional[str] = None
    custom_banners: Optional[str] = None

class NewsRequest(BaseModel):
    url_or_text: str
    theme: str = "flat-motion-graphics"
    voice: str = "vi-VN-NamMinhNeural"
    rate: str = "+20%"


def run_remake_job(job_id: str, req: RemakeRequest):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["log"] = "Đang tổng hợp giọng đọc tiếng Việt bằng Edge-TTS..."

        out_name = f"remake_{int(time.time())}.mp4"
        out_file = OUTPUT_DIR / out_name

        script_file = OUTPUT_DIR / f"{job_id}_script.txt"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(req.script_text)

        cmd = [
            str(PYTHON_EXE),
            str(ROOT_DIR / "remake_douyin_video.py"),
            "--video", req.video_path,
            "--text", str(script_file),
            "--source", req.source_credit,
            "--voice", req.voice,
            "--rate", req.rate,
            "--output", str(out_file),
        ]

        if req.custom_punches:
            p_file = OUTPUT_DIR / f"{job_id}_punches.json"
            with open(p_file, "w", encoding="utf-8") as f:
                f.write(req.custom_punches)
            cmd.extend(["--punches", str(p_file)])

        if req.custom_banners:
            b_file = OUTPUT_DIR / f"{job_id}_banners.json"
            with open(b_file, "w", encoding="utf-8") as f:
                f.write(req.custom_banners)
            cmd.extend(["--banners", str(b_file)])

        jobs[job_id]["log"] = "Đang trích xuất nhịp phụ đề và render video qua Remotion..."

        proc = subprocess.run(
            cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8"
        )
        if proc.returncode != 0:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = proc.stderr or proc.stdout
            return

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["video_url"] = f"/videos/{out_name}"
        jobs[job_id]["video_name"] = out_name
        jobs[job_id]["log"] = "Video đã được tạo thành công!"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


def run_news_job(job_id: str, req: NewsRequest):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["log"] = "Đang phân tích nội dung bài viết và tạo giọng đọc..."

        out_slug = f"news_{int(time.time())}"
        target_dir = OUTPUT_DIR / out_slug
        target_dir.mkdir(parents=True, exist_ok=True)
        out_file = target_dir / f"{out_slug}.mp4"

        cmd = [
            str(PYTHON_EXE),
            str(ROOT_DIR / "create_news_video.py"),
            "--input", req.url_or_text,
            "--theme", req.theme,
            "--voice", req.voice,
            "--rate", req.rate,
            "--output", str(out_file),
        ]

        jobs[job_id]["log"] = "Đang render video tin tức Bento HUD Remotion..."

        proc = subprocess.run(
            cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8"
        )
        if proc.returncode != 0:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = proc.stderr or proc.stdout
            return

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["video_url"] = f"/videos/{out_slug}/{out_slug}.mp4"
        jobs[job_id]["video_name"] = f"{out_slug}.mp4"
        jobs[job_id]["log"] = "Video tin tức đã được tạo thành công!"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@app.get("/api/samples")
def list_samples():
    ref_dir = ROOT_DIR / "reference_videos"
    ref_dir.mkdir(parents=True, exist_ok=True)
    res = [
        {
            "name": "🔥 GHÉP NHIỀU VIDEO THAM CHIẾU (Kho B-Roll - Tự đổi cảnh mỗi 3s)",
            "path": ref_dir.as_posix(),
            "size_mb": 0,
            "is_pool": True
        }
    ]
    sample_files = glob.glob(str(ROOT_DIR / "sample_*.mp4")) + list(glob.glob(str(ref_dir / "*.mp4")))
    seen = set()
    for sf in sample_files:
        p = Path(sf)
        if p.name not in seen:
            seen.add(p.name)
            res.append({
                "name": p.name,
                "path": p.as_posix(),
                "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
                "is_pool": False
            })
    return res


@app.get("/api/reference-videos")
def list_reference_videos():
    ref_dir = ROOT_DIR / "reference_videos"
    ref_dir.mkdir(parents=True, exist_ok=True)
    all_files = list(ref_dir.glob("*.mp4")) + list(ref_dir.glob("*.mov")) + list(ROOT_DIR.glob("sample_*.mp4"))
    seen = set()
    res = []
    for f in all_files:
        if f.name not in seen:
            seen.add(f.name)
            res.append({
                "name": f.name,
                "path": f.as_posix(),
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
            })
    return res


@app.post("/api/upload-reference")
async def upload_reference_video(file: UploadFile = File(...)):
    ref_dir = ROOT_DIR / "reference_videos"
    ref_dir.mkdir(parents=True, exist_ok=True)
    clean_name = re.sub(r"[^\w\.-]", "_", file.filename)
    target_path = ref_dir / f"{int(time.time())}_{clean_name}"
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"name": target_path.name, "path": target_path.as_posix()}


@app.get("/api/videos")
def list_rendered_videos():
    vids = []
    for f in OUTPUT_DIR.rglob("*.mp4"):
        rel_path = f.relative_to(OUTPUT_DIR).as_posix()
        vids.append({
            "name": f.name,
            "url": f"/videos/{rel_path}",
            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(f.stat().st_mtime)),
            "mtime": f.stat().st_mtime
        })
    vids.sort(key=lambda x: x["mtime"], reverse=True)
    return vids


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    target_path = ROOT_DIR / f"upload_{int(time.time())}_{file.filename}"
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"name": target_path.name, "path": target_path.as_posix()}


@app.post("/api/remake")
def start_remake(req: RemakeRequest, bg_tasks: BackgroundTasks):
    job_id = f"job_remake_{int(time.time() * 1000)}"
    jobs[job_id] = {
        "id": job_id,
        "type": "remake",
        "status": "queued",
        "log": "Đang xếp hàng thực thi...",
        "created_at": time.time()
    }
    bg_tasks.add_task(run_remake_job, job_id, req)
    return {"job_id": job_id}


@app.post("/api/news")
def start_news(req: NewsRequest, bg_tasks: BackgroundTasks):
    job_id = f"job_news_{int(time.time() * 1000)}"
    jobs[job_id] = {
        "id": job_id,
        "type": "news",
        "status": "queued",
        "log": "Đang xếp hàng thực thi...",
        "created_at": time.time()
    }
    bg_tasks.add_task(run_news_job, job_id, req)
    return {"job_id": job_id}


def run_auto_job(job_id: str, prompt: str):
    try:
        jobs[job_id]["status"] = "processing"
        
        def update_log(msg: str):
            jobs[job_id]["log"] = msg

        res = run_auto_pipeline(prompt, on_progress=update_log)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["video_url"] = res["video_url"]
        jobs[job_id]["video_name"] = res["video_name"]
        jobs[job_id]["title"] = res["title"]
        jobs[job_id]["log"] = "Video đã được tạo thành công 100%!"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@app.post("/api/auto")
def start_auto(req: AutoRequest, bg_tasks: BackgroundTasks):
    job_id = f"job_auto_{int(time.time() * 1000)}"
    jobs[job_id] = {
        "id": job_id,
        "type": "auto",
        "status": "queued",
        "log": "Đang phân tích câu lệnh của bạn...",
        "created_at": time.time()
    }
    bg_tasks.add_task(run_auto_job, job_id, req.prompt)
    return {"job_id": job_id}


from ai_news_crawler import auto_crawl_and_produce_video, load_processed_history

class AutoCrawlRequest(BaseModel):
    min_duration: int = 120
    topic: Optional[str] = None


def run_auto_crawl_job(job_id: str, min_duration: int = 120, topic: Optional[str] = None):
    try:
        jobs[job_id]["status"] = "processing"
        
        def update_log(msg: str):
            jobs[job_id]["log"] = msg

        if topic and topic.strip():
            # Dedicated topical creation
            clean_top = topic.strip()
            update_log(f"Đang soạn kịch bản chuyên sâu ({min_duration}s+) về: {clean_top}...")
            news_item = {
                "id": f"custom_{int(time.time())}",
                "title": clean_top,
                "summary": f"Báo cáo phân tích chuyên sâu, số liệu benchmark và dẫn chứng kiểm chứng thực tế về {clean_top}.",
                "source": "Báo cáo quốc tế & Phân tích thị trường",
                "link": ""
            }
            from ai_news_crawler import translate_and_craft_vietnamese_script
            crafted = translate_and_craft_vietnamese_script(news_item, min_duration_seconds=min_duration)
            
            timestamp = int(time.time())
            out_name = f"auto_topic_{timestamp}.mp4"
            out_file = OUTPUT_DIR / out_name
            meta_file = OUTPUT_DIR / f"auto_topic_{timestamp}_meta.json"
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(crafted, f, ensure_ascii=False, indent=2)

            update_log("Đang tổng hợp giọng đọc tiếng Việt Edge-TTS và thu thập ảnh tham chiếu...")
            cmd = [
                str(PYTHON_EXE),
                str(ROOT_DIR / "create_news_video.py"),
                "--text", crafted["script_text"],
                "--tag", "TIN AI NÓNG",
                "--title", crafted.get("headline", clean_top),
                "--source", crafted.get("source_pill", "Nguồn: Tin Công Nghệ"),
                "--meta", str(meta_file),
                "--voice", "vi-VN-NamMinhNeural",
                "--rate", "+8%" if min_duration >= 120 else "+12%",
                "--output", str(out_file),
            ]
            update_log(f"Đang render Remotion Full HD 1080x1920 (chuẩn {min_duration}s+)...")
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if res.returncode != 0:
                raise RuntimeError(f"Render failed: {res.stderr[:300]}")

            jobs[job_id]["status"] = "completed"
            jobs[job_id]["video_url"] = f"/videos/{out_name}"
            jobs[job_id]["video_name"] = out_name
            jobs[job_id]["title"] = crafted.get("headline", clean_top)
            jobs[job_id]["log"] = f"Đã dựng thành công video {min_duration}s+ về: {crafted.get('headline', clean_top)}"
        else:
            res = auto_crawl_and_produce_video(on_progress=update_log, min_duration_seconds=min_duration)
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["video_url"] = res["video_url"]
            jobs[job_id]["video_name"] = res["video_name"]
            jobs[job_id]["title"] = res["news_title"]
            jobs[job_id]["log"] = f"Đã quét và dựng video thành công: {res['news_title']}"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@app.post("/api/auto-crawl-news")
def start_auto_crawl_news(bg_tasks: BackgroundTasks, req: Optional[AutoCrawlRequest] = None):
    job_id = f"job_crawl_{int(time.time() * 1000)}"
    duration = req.min_duration if req else 60
    topic = req.topic if req else None
    jobs[job_id] = {
        "id": job_id,
        "type": "crawl",
        "status": "queued",
        "log": "Đang quét tin tức AI mới nhất trên thế giới..." if not topic else f"Đang phân tích chủ đề: {topic}...",
        "created_at": time.time()
    }
    bg_tasks.add_task(run_auto_crawl_job, job_id, duration, topic)
    return {"job_id": job_id}


@app.get("/api/crawled-history")
def get_crawled_history():
    return load_processed_history()


@app.get("/api/job/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


from ai_service import check_api_connection, save_credentials, get_configured_credentials

class ApiKeyRequest(BaseModel):
    api_key: str
    base_url: Optional[str] = "https://api.buihuuthang.com/v1"


@app.get("/api/buihuuthang/status")
def get_buihuuthang_status():
    return check_api_connection()


@app.post("/api/buihuuthang/save")
def save_buihuuthang_key(req: ApiKeyRequest):
    test_res = check_api_connection(api_key=req.api_key, base_url=req.base_url)
    save_credentials(req.api_key, req.base_url or "https://api.buihuuthang.com/v1")
    return {
        "status": "success" if test_res.get("status") == "connected" else "saved_with_warning",
        "message": "Đã lưu và kết nối thành công tới cổng API https://api.buihuuthang.com!" if test_res.get("status") == "connected" else f"Đã lưu key. Trạng thái: {test_res.get('message')}",
        "details": test_res
    }


class TestPromptRequest(BaseModel):
    prompt: Optional[str] = "Hãy viết 1 câu giới thiệu ngắn 15 từ về sức mạnh của AI trong việc sản xuất video tự động."
    model: Optional[str] = "deepseek-v4-flash"


@app.post("/api/buihuuthang/test-prompt")
def test_buihuuthang_prompt(req: TestPromptRequest):
    from ai_service import test_chat_completion
    return test_chat_completion(prompt=req.prompt, model=req.model)


@app.get("/", response_class=HTMLResponse)
def index_page():
    html_file = ROOT_DIR / "templates" / "index.html"
    with open(html_file, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
