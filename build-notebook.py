#!/usr/bin/env python3
"""Bangun notebook Kaggle (.ipynb) untuk render Shorts.

Menanam script render.py (ditulis sendiri, ~/workspace/kliper/render.py)
ke dalam sel %%writefile, plus sel setup/config/run/verifikasi.
Jalankan: python3 build-notebook.py
Hasil: ~/workspace/kliper/kaggle-render-notebook.ipynb
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "render.py")) as f:
    render_src = f.read()

MD_INTRO = """# 🎬 Render Shorts di Kaggle (GPU T4 — gratis)
Notebook ini merender 1 Shorts vertikal 720x1280 dari satu klip sumber.
Isi konfigurasi di sel CONFIG, lalu Run All.

**Sebelum run, pastikan di panel kanan notebook:**
- Accelerator = **GPU T4** (untuk whisper/transkrip; render ffmpeg jalan di CPU)
- Internet = **ON** (untuk unduh video via yt-dlp)
- Akun Kaggle sudah **verifikasi nomor HP** (syarat GPU + internet)

**Kuota gratis:** 30 jam GPU/minggu, sesi maks ~12 jam. File hasil ada di `/kaggle/working` → tab Output.
"""

CODE_ENV = """!nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "GPU tidak terdeteksi (cek Accelerator = GPU)"
!ffmpeg -version 2>/dev/null | head -1
!ffprobe -version 2>/dev/null | head -1
!python3 --version
!free -m | head -2
!df -h /kaggle/working | tail -1
"""

CODE_INSTALL = """# Install sekali per sesi (Kaggle reset tiap sesi baru)
%pip install -q yt-dlp faster-whisper pillow pysubs2
!fc-list 2>/dev/null | grep -i dejavu | head -3 || echo "cek font manual"
print("install selesai")
"""

MD_CONFIG = """## ⚙️ CONFIG — isi di sini
- `SOURCE_URL`: link video sumber (YouTube/dll). Kosongkan bila upload file manual ke **Add data → Upload** (file masuk `/kaggle/input`).
- `BOOM`: detik momen lucu/puncak (zoom + slow-mo mulai 0,4 dtk sebelumnya).
- `TITLE`, `SETUP`, `PUNCH`: teks judul, caption sebelum boom, punchline saat boom.
- Hindari tanda petik ganda (`"`) di dalam teks.
"""

CODE_CONFIG = """SOURCE_URL = ""   # contoh: "https://www.youtube.com/watch?v=..."
BOOM = 5.0
TITLE = "JUDUL SHORTS DI SINI"
SETUP = "caption setup sebelum boom"
PUNCH = "punchline saat boom"
OUT_NAME = "shorts-01.mp4"

import glob, os, subprocess

# 1) cari file upload di /kaggle/input
uploads = sorted(glob.glob("/kaggle/input/**/*.*", recursive=True))
videos = [p for p in uploads if p.lower().endswith((".mp4", ".mov", ".mkv", ".webm", ".m4v"))]
SRC = videos[0] if videos else None

# 2) kalau tidak ada upload, unduh dari URL (butuh Internet ON)
if SRC is None:
    assert SOURCE_URL, "Isi SOURCE_URL atau upload file video ke /kaggle/input"
    SRC = "/kaggle/working/src.mp4"
    subprocess.run(["yt-dlp", "-f", "bv*[height<=1080]+ba/b[height<=1080]",
                    "-o", SRC, SOURCE_URL], check=True)

print("sumber:", SRC)
print("durasi:", subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "csv=p=0", SRC], text=True).strip(), "detik")
"""

CODE_RUN = """import subprocess
subprocess.run(["python3", "render.py", SRC, f"/kaggle/working/{OUT_NAME}",
                str(BOOM), TITLE, SETUP, PUNCH], check=True)
"""

CODE_VERIFY = """import subprocess
out = f"/kaggle/working/{OUT_NAME}"
info = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
    "-show_entries", "stream=width,height", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1", out], text=True)
print(info)
!ls -lh /kaggle/working/
"""

MD_DONE = """## ✅ Selesai
- File hasil: `/kaggle/working/shorts-01.mp4` — unduh dari tab **Output** (kanan) atau sel di atas.
- Mau render klip berikutnya: ubah CONFIG lalu Run All lagi (satu notebook = satu Shorts; duplikat notebook untuk batch).
- Kuota: 30 jam GPU/minggu — render 1 Shorts ±1–3 menit, jadi kuota sangat longgar.
- Langkah berikut: auto-subtitle (faster-whisper sudah terinstall) + kartu meme dari frame.
"""


def md(text):
    return {"cell_type": "markdown", "metadata": {},
            "source": text.splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": text.splitlines(keepends=True)}


cells = [
    md(MD_INTRO),
    code(CODE_ENV),
    code(CODE_INSTALL),
    md(MD_CONFIG),
    code(CODE_CONFIG),
    code("%%writefile render.py\n" + render_src),
    code(CODE_RUN),
    code(CODE_VERIFY),
    md(MD_DONE),
]

nb = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python",
                       "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"},
    },
    "cells": cells,
}

out = os.path.join(HERE, "kaggle-render-notebook.ipynb")
with open(out, "w") as f:
    json.dump(nb, f, indent=1)
print("OK", out, len(cells), "cells")
