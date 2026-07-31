import asyncio
import yt_dlp
import os
import re
import logging

logger = logging.getLogger(__name__)

async def fetch_info(url: str) -> dict:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'noplaylist': True,
    }
    def _extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, _extract)
    
    formats = []
    for f in info.get('formats', []):
        if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
            formats.append({
                'format_id': f.get('format_id'),
                'ext': f.get('ext'),
                'abr': f.get('abr'),
                'filesize_approx': f.get('filesize_approx') or f.get('filesize'),
            })
            
    return {
        'title': info.get('title'),
        'uploader': info.get('uploader'),
        'duration': info.get('duration'),
        'thumbnail': info.get('thumbnail'),
        'formats': formats
    }

async def download_audio(url, format_name, quality_name, out_dir, task_id, progress_cb) -> str:
    os.makedirs(out_dir, exist_ok=True)
    
    def hook(d):
        if d['status'] == 'downloading':
            p_str = d.get('_percent_str', '0%')
            p = re.sub(r'\x1b\[[0-9;]*m', '', p_str).replace('%', '').strip()
            try:
                percent = float(p)
            except ValueError:
                percent = 0
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            progress_cb(task_id, percent, speed, eta)

    format_map = {
        'MP3': 'mp3',
        'M4A': 'm4a',
        'WEBM': 'webm',
        'FLAC': 'flac',
        'OPUS': 'opus'
    }
    codec = format_map.get(format_name, 'mp3')
    quality_map = {'Best': '0', 'High': '5', 'Medium': '7', 'Low': '9'}
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
        'progress_hooks': [hook],
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': codec,
            'preferredquality': quality_map.get(quality_name, '0') if codec == 'mp3' else None,
        }],
    }
    
    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        # find the file that was actually created
        logger.info(f"Files in out_dir: {os.listdir(out_dir)}")
        files = os.listdir(out_dir)
        if not files:
            raise Exception("Download failed: no file found in output directory")
        return os.path.join(out_dir, files[0])

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _download)
