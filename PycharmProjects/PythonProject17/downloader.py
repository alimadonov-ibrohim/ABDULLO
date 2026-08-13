import os
import re
import shutil
import tempfile
import uuid

import yt_dlp

MAX_FILE_SIZE = 50 * 1024 * 1024
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), "downloads")

SUPPORTED_RE = re.compile(
    r"(youtube\.com|youtu\.be|instagram\.com|tiktok\.com|pinterest\.\w+|facebook\.com|fb\.watch)",
    re.IGNORECASE,
)
HAS_FFMPEG = shutil.which("ffmpeg") is not None


def ydl_opts():
    return {
        "format": "best[ext=mp4]/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4().hex[:8]}_%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "socket_timeout": 20,
    }


def download_video(url: str) -> str:
    opts = ydl_opts()
    if not HAS_FFMPEG:
        opts["format"] = "best[filesize<50M][ext=mp4]/best[filesize<50M]/best[ext=mp4]/best"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


def cleanup(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass