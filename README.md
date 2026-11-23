# Kliper 🎬

Pipeline render YouTube Shorts vertikal 720x1280 otomatis (Python + ffmpeg),
dengan Kaggle Notebooks (GPU T4 gratis) sebagai mesin render tambahan.

## ✨ Fitur

- Render satu Shorts vertikal 720x1280 dari satu klip sumber
- Intro 2 detik: frame pertama dibekukan + judul besar
- Segmen boom: zoom 1,6x + goyang, lalu slow-motion 0,65x setelah boom
- Replay jendela boom bila total durasi < 61 detik (syarat durasi Shorts)
- Judul, caption, punchline, SFX, dan freeze akhir otomatis
- Notebook Kaggle siap pakai: upload, isi konfigurasi, Run All

## 🚀 Cara pakai

### Lokal (uji cepat)

```bash
python3 render.py <sumber.mp4> <keluar.mp4> <detik_boom> <JUDUL> <caption_setup> <punchline>
```

Butuh `ffmpeg` + `ffprobe` terinstal.

### Di Kaggle (mesin render)

1. Daftar Kaggle dan **verifikasi nomor HP** (syarat GPU + internet).
2. Upload `kaggle-render-notebook.ipynb`.
3. Atur Accelerator = **GPU T4**, Internet = **ON**.
4. Isi sel CONFIG (link klip sumber, detik boom, judul, caption, punchline),
   lalu Run All. Hasil ada di `/kaggle/working` → tab Output.

Kuota gratis Kaggle: 30 jam GPU/minggu, sesi maks ~12 jam.

### Bangun ulang notebook

`build-notebook.py` menanam `render.py` ke dalam notebook (sel `%%writefile`):

```bash
python3 build-notebook.py
```

## 🛠️ Teknologi

- Python 3 + ffmpeg (libx264, aac)
- Kaggle Notebooks (GPU T4 gratis, tanpa kartu)
- Notebook Jupyter (`.ipynb`)

## ⚠️ Catatan

- Notebook sudah **teruji lokal** (sumber sintetis 15 detik → output 23,4 detik
  720x1280, replay berfungsi), tapi **belum teruji end-to-end dengan klip
  asli di Kaggle** — masih menunggu akun Kaggle + uji 1 Shorts nyata.
- Render jalan di CPU; GPU dipakai untuk transkrip bila diperlukan.

## 👤 Author

Alvin Bintang Pratama — [@Jasonranti24](https://github.com/Jasonranti24)
