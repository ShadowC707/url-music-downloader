import os
import uuid
import asyncio
import shutil
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from downloader import fetch_info, download_audio
from trimmer import trim_audio, embed_metadata

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks = {}
batch_tasks = {}
TEMP_DIR = "/tmp/music-dl"
if os.name == 'nt':
    TEMP_DIR = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'music-dl')

class InfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    format: str
    quality: str
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None

class TrimRequest(BaseModel):
    task_id: str
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None

class BatchRequest(BaseModel):
    urls: list[str]
    format_id: str
    quality: str = "Best"

@app.post("/api/info")
async def get_info(req: InfoRequest):
    try:
        return await fetch_info(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def progress_callback(task_id, percent, speed, eta):
    if task_id in tasks:
        tasks[task_id].update({
            "progress": percent,
            "speed": speed,
            "eta": eta
        })

async def run_trim_task(new_task_id, original_file_path, req: TrimRequest):
    out_dir = os.path.join(TEMP_DIR, new_task_id)
    os.makedirs(out_dir, exist_ok=True)
    try:
        tasks[new_task_id]["status"] = "processing"
        filename = os.path.basename(original_file_path)
        base, ext = os.path.splitext(filename)
        
        # If trim is requested, use trim_audio
        if req.start_sec is not None and req.end_sec is not None and req.end_sec > req.start_sec:
            tasks[new_task_id]["status"] = "trimming"
            trimmed_path = os.path.join(out_dir, f"{base}_trimmed{ext}")
            await trim_audio(original_file_path, trimmed_path, req.start_sec, req.end_sec)
            file_path = trimmed_path
        else:
            # Just copy for metadata tagging
            file_path = os.path.join(out_dir, filename)
            shutil.copy(original_file_path, file_path)

        if any([req.title, req.artist, req.album]):
            tasks[new_task_id]["status"] = "tagging"
            await embed_metadata(file_path, req.title, req.artist, req.album)

        tasks[new_task_id].update({
            "status": "done",
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "progress": 100
        })
    except Exception as e:
        logger.exception(f"Trim task {new_task_id} failed")
        tasks[new_task_id].update({
            "status": "error",
            "error": str(e)
        })

async def process_batch_item(url: str, task_id: str, format_name: str, quality_name: str, sem: asyncio.Semaphore):
    async with sem:
        out_dir = os.path.join(TEMP_DIR, task_id)
        try:
            logger.info(f"Starting batch item info fetch for {task_id}")
            info = await fetch_info(url)
            title = info.get("title") or "Unknown Title"
            artist = info.get("uploader") or "Unknown Artist"
            album = ""
            
            tasks[task_id]["title"] = title
            
            logger.info(f"Starting batch download task {task_id} to {out_dir}")
            tasks[task_id]["status"] = "downloading"
            
            file_path = await download_audio(
                url, format_name, quality_name, out_dir, task_id, progress_callback
            )
            
            tasks[task_id]["status"] = "tagging"
            await embed_metadata(file_path, title, artist, album)
            
            tasks[task_id].update({
                "status": "done",
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "progress": 100
            })
        except Exception as e:
            logger.exception(f"Batch task {task_id} failed")
            tasks[task_id].update({
                "status": "error",
                "error": str(e)
            })

async def run_batch_tasks(batch_id: str, req: BatchRequest, task_ids: list[str]):
    sem = asyncio.Semaphore(3)
    format_name = req.format_id
    quality_name = req.quality
    
    corsos = []
    for url, task_id in zip(req.urls, task_ids):
        corsos.append(process_batch_item(url, task_id, format_name, quality_name, sem))
        
    await asyncio.gather(*corsos)

async def run_download_task(task_id, req: DownloadRequest):
    out_dir = os.path.join(TEMP_DIR, task_id)
    try:
        logger.info(f"Starting download task {task_id} to {out_dir}")
        tasks[task_id]["status"] = "downloading"
        file_path = await download_audio(
            req.url, req.format, req.quality, out_dir, task_id, progress_callback
        )
        
        logger.info(f"Downloaded file: {file_path}, exists: {os.path.exists(file_path)}")
        filename = os.path.basename(file_path)
        
        if req.start_sec is not None and req.end_sec is not None:
            if req.end_sec <= req.start_sec:
                logger.warning(f"Invalid trim range for task {task_id}: {req.start_sec} to {req.end_sec}. Skipping trim.")
                req.start_sec = None
                req.end_sec = None

        if req.start_sec is not None and req.end_sec is not None:
            tasks[task_id]["status"] = "trimming"
            base, ext = os.path.splitext(file_path)
            trimmed_path = f"{base}_trimmed{ext}"
            await trim_audio(file_path, trimmed_path, req.start_sec, req.end_sec)
            if os.path.exists(file_path):
                os.remove(file_path)
            file_path = trimmed_path
            filename = os.path.basename(file_path)

        if any([req.title, req.artist, req.album]):
            tasks[task_id]["status"] = "tagging"
            await embed_metadata(file_path, req.title, req.artist, req.album)

        tasks[task_id].update({
            "status": "done",
            "file_path": file_path,
            "filename": filename,
            "progress": 100
        })
    except Exception as e:
        logger.exception(f"Task {task_id} failed")
        tasks[task_id].update({
            "status": "error",
            "error": str(e)
        })

@app.post("/api/download")
async def download(req: DownloadRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "speed": "0",
        "eta": "0",
        "file_path": None,
        "filename": None,
        "error": None
    }
    background_tasks.add_task(run_download_task, task_id, req)
    return {"task_id": task_id}

@app.get("/api/task/{task_id}")
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.get("/api/file/{task_id}")
async def get_file(task_id: str):
    if task_id not in tasks or tasks[task_id]["status"] != "done":
        raise HTTPException(status_code=404, detail="File not ready or task not found")
    
    file_path = tasks[task_id]["file_path"]
    filename = tasks[task_id]["filename"]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
        
    return FileResponse(
        file_path, 
        media_type="application/octet-stream", 
        filename=filename
    )

@app.get("/api/preview/{task_id}")
async def get_preview(task_id: str):
    if task_id not in tasks or tasks[task_id]["status"] != "done":
        raise HTTPException(status_code=404, detail="Task not found or not done")
    file_path = tasks[task_id]["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="audio/mpeg")

@app.post("/api/trim")
async def trim(req: TrimRequest, background_tasks: BackgroundTasks):
    if req.task_id not in tasks or tasks[req.task_id]["status"] != "done":
        raise HTTPException(status_code=400, detail="Original task not found or not done")
    
    original_file_path = tasks[req.task_id]["file_path"]
    if not os.path.exists(original_file_path):
        raise HTTPException(status_code=404, detail="Original file not found")

    new_task_id = str(uuid.uuid4())
    tasks[new_task_id] = {
        "status": "pending",
        "progress": 0,
        "speed": "0",
        "eta": "0",
        "file_path": None,
        "filename": None,
        "error": None
    }
    background_tasks.add_task(run_trim_task, new_task_id, original_file_path, req)
    return {"task_id": new_task_id}

@app.post("/api/batch")
async def create_batch(req: BatchRequest, background_tasks: BackgroundTasks):
    batch_id = str(uuid.uuid4())
    task_ids = []
    
    for url in req.urls:
        task_id = str(uuid.uuid4())
        task_ids.append(task_id)
        tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "speed": "0",
            "eta": "0",
            "file_path": None,
            "filename": None,
            "error": None,
            "title": None,
            "url": url
        }
        
    batch_tasks[batch_id] = {
        "batch_id": batch_id,
        "task_ids": task_ids
    }
    
    background_tasks.add_task(run_batch_tasks, batch_id, req, task_ids)
    return {"batch_id": batch_id, "task_ids": task_ids}

@app.get("/api/batch/{batch_id}")
async def get_batch(batch_id: str):
    if batch_id not in batch_tasks:
        raise HTTPException(status_code=404, detail="Batch not found")
        
    batch = batch_tasks[batch_id]
    task_list = []
    for tid in batch["task_ids"]:
        t = tasks.get(tid, {})
        task_list.append({
            "task_id": tid,
            "title": t.get("title"),
            "status": t.get("status"),
            "progress": t.get("progress"),
            "error": t.get("error")
        })
        
    return {
        "batch_id": batch_id,
        "tasks": task_list
    }

# Serve frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
