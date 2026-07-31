import asyncio
import os
import subprocess

def _run_ffmpeg(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"ffmpeg failed: {result.stderr}")
    return result

async def trim_audio(input_path, output_path, start_sec, end_sec) -> str:
    # ffmpeg -i input -ss start -to end -c copy output
    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-ss', str(start_sec),
        '-to', str(end_sec),
        '-c', 'copy',
        output_path
    ]
    await asyncio.to_thread(_run_ffmpeg, cmd)
    return output_path

async def embed_metadata(file_path, title, artist, album) -> str:
    if not any([title, artist, album]):
        return file_path
        
    base, ext = os.path.splitext(file_path)
    tmp_path = f"{base}_meta{ext}"
    
    cmd = ['ffmpeg', '-y', '-i', file_path]
    if title: cmd.extend(['-metadata', f'title={title}'])
    if artist: cmd.extend(['-metadata', f'artist={artist}'])
    if album: cmd.extend(['-metadata', f'album={album}'])
    cmd.extend(['-c', 'copy', tmp_path])
    
    await asyncio.to_thread(_run_ffmpeg, cmd)
        
    os.replace(tmp_path, file_path)
    return file_path
