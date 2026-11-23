#!/usr/bin/env python3
"""Render satu Shorts vertikal 720x1280 dari satu klip sumber.

Ditulis dari nol untuk pipeline Kaggle (mesin render gratis).
Alur:
  1. intro 2 dtk: frame pertama dibekukan + judul besar + "TONTON SAMPAI HABIS"
  2. segmen A: awal klip sampai 0,4 dtk sebelum boom
     (dipercepat 1,2x bila sumber >= 75 dtk)
  3. segmen B: jendela boom, zoom 1,6x + goyang
  4. segmen C: 1,6 dtk setelah boom, slow-motion 0,65x + zoom
  5. segmen D: sisa klip
  6. replay jendela boom bila total < 61 dtk (syarat durasi Shorts)
  7. finishing: pita judul di atas, caption setup sebelum boom,
     punchline kuning saat boom, SFX boom + pop,
     freeze akhir 1,2 dtk dengan teks WKWKWK.

Pakai: render.py <sumber.mp4> <keluar.mp4> <detik_boom> <JUDUL> <caption_setup> <punchline>
"""
import glob
import os
import subprocess
import sys
import tempfile

BASE = ("scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,"
        "setsar=1,eq=saturation=1.25:contrast=1.08,fps=30")
ZOOM = (BASE + ",crop=450:800:(in_w-450)/2+sin(t*9)*7:(in_h-800)/2+cos(t*7)*7,"
        "scale=720:1280,setsar=1")
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
       "-c:a", "aac", "-b:a", "128k"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2500:])
        sys.exit(1)


def duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], text=True)
    return float(out.strip())


def find_font():
    cands = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    cands += sorted(glob.glob("/usr/share/fonts/**/DejaVuSans-Bold.ttf",
                               recursive=True))
    cands += sorted(glob.glob("/usr/share/fonts/**/*Bold*.ttf", recursive=True))
    for c in cands:
        if os.path.isfile(c):
            return c
    sys.exit("ERROR: font Bold .ttf tidak ditemukan di /usr/share/fonts")


def esc(text):
    """Escape teks untuk drawtext (tanpa expansion)."""
    return (text.replace("\\", "\\\\").replace("'", "\\'")
                .replace(":", "\\:").replace("%", "\\%"))


def fit(text, cap):
    return max(26, min(cap, int(1020 / max(len(text), 1))))


def main():
    src, out, boom, title, setup, punch = (
        sys.argv[1], sys.argv[2], float(sys.argv[3]),
        sys.argv[4], sys.argv[5], sys.argv[6])
    font = find_font()
    dur = duration(src)
    if not (1.0 <= boom <= dur - 1.0):
        sys.exit(f"ERROR: boom harus 1..{dur - 1:.1f} detik (durasi sumber {dur:.1f})")

    b0 = max(0.0, boom - 0.4)
    b1 = min(dur, boom + 0.6)
    b2 = min(dur, boom + 2.2)
    ramp = 1.2 if dur >= 75 else 1.0
    a_dur = b0 / ramp
    win = (b1 - b0) + (b2 - b1) / 0.65
    tail = max(0.0, dur - b2)
    total_main = 2.0 + a_dur + win + tail
    replay = total_main < 61.0
    total = total_main + ((b2 - b0) / 0.6 if replay else 0.0)
    boom_out = 2.0 + a_dur
    win_end = boom_out + win

    tmp = tempfile.mkdtemp(prefix="shorts-")
    boom_wav = os.path.join(tmp, "boom.wav")
    pop_wav = os.path.join(tmp, "pop.wav")
    run(["ffmpeg", "-v", "error", "-f", "lavfi",
         "-i", "sine=frequency=150:duration=0.7",
         "-af", "afade=t=out:st=0.1:d=0.6,volume=2.2", boom_wav, "-y"])
    run(["ffmpeg", "-v", "error", "-f", "lavfi",
         "-i", "sine=frequency=900:duration=0.12",
         "-af", "afade=t=out:st=0.02:d=0.1,volume=1.6", pop_wav, "-y"])

    def seg(args, name):
        run(["ffmpeg", "-v", "error"] + args + ENC +
            [os.path.join(tmp, name), "-y"])

    parts = []

    def add(args):
        name = f"{len(parts)}.mp4"
        seg(args, name)
        parts.append(name)

    # 0: intro 2 dtk, frame pertama + judul
    add(["-ss", "0.5", "-i", src, "-f", "lavfi",
         "-i", "anullsrc=r=44100:cl=stereo", "-t", "2",
         "-vf", BASE +
         f",drawtext=fontfile={font}:text='{esc(title)}':fontsize={fit(title, 56)}"
         f":fontcolor=yellow:borderw=5:bordercolor=black:expansion=none"
         f":x=(w-text_w)/2:y=560,"
         f"drawtext=fontfile={font}:text='TONTON SAMPAI HABIS':fontsize=36"
         f":fontcolor=white:borderw=3:bordercolor=black:expansion=none"
         f":x=(w-text_w)/2:y=660",
         "-shortest"])
    # 1: segmen A
    if b0 > 0.05:
        add(["-i", src, "-ss", "0", "-t", str(b0),
             "-vf", BASE + f",setpts=PTS/{ramp}", "-af", f"atempo={ramp}"])
    # 2: segmen B (boom, zoom + goyang)
    add(["-i", src, "-ss", str(b0), "-t", str(b1 - b0), "-vf", ZOOM])
    # 3: segmen C (slow-mo + zoom)
    add(["-i", src, "-ss", str(b1), "-t", str(b2 - b1),
         "-vf", BASE + ",crop=450:800:(in_w-450)/2:(in_h-800)/2,scale=720:1280,"
         "setsar=1,setpts=PTS/0.65", "-af", "atempo=0.65"])
    # 4: segmen D (sisa)
    if tail > 0.05:
        add(["-i", src, "-ss", str(b2), "-vf", BASE])
    # 5: replay jendela boom bila total < 61 dtk
    if replay:
        add(["-i", src, "-ss", str(b0), "-t", str(b2 - b0),
             "-vf", ZOOM + f",setpts=PTS/0.6,"
             f"drawtext=fontfile={font}:text='REPLAY':fontsize=40"
             f":fontcolor=yellow:borderw=4:bordercolor=black:expansion=none"
             f":x=24:y=130", "-af", "atempo=0.6"])

    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.join(tmp, p)}'\n")
    joined = os.path.join(tmp, "joined.mp4")
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c", "copy", joined, "-y"])

    fc = (
        f"[0:v]tpad=stop_mode=clone:stop_duration=1.2,"
        f"drawbox=x=0:y=0:w=720:h=104:color=black@0.72:t=fill,"
        f"drawtext=fontfile={font}:text='{esc(title)}':fontsize={fit(title, 42)}"
        f":fontcolor=white:borderw=3:bordercolor=black:expansion=none"
        f":x=(w-text_w)/2:y=30,"
        f"drawtext=fontfile={font}:text='{esc(setup)}':fontsize={fit(setup, 38)}"
        f":fontcolor=white:borderw=3:bordercolor=black:expansion=none"
        f":x=(w-text_w)/2:y=1150:enable='lt(t,{boom_out:.2f})',"
        f"drawtext=fontfile={font}:text='{esc(punch)}':fontsize={fit(punch, 46)}"
        f":fontcolor=yellow:borderw=4:bordercolor=black:expansion=none"
        f":x=(w-text_w)/2:y=1140:enable='between(t,{boom_out:.2f},{win_end + 1.2:.2f})',"
        f"drawtext=fontfile={font}:text='WKWKWK':fontsize=54"
        f":fontcolor=yellow:borderw=4:bordercolor=black:expansion=none"
        f":x=(w-text_w)/2:y=1060:enable='gte(t,{total:.2f})'[vout];"
        f"[0:a]apad,atrim=0:{total + 1.2:.2f}[a0];"
        f"[1:a]adelay={int(boom_out * 1000)}:all=1[ab];"
        f"[2:a]adelay={int(total * 1000)}:all=1[ap];"
        f"[a0][ab][ap]amix=inputs=3:duration=first:dropout_transition=0[aout]"
    )
    run(["ffmpeg", "-v", "error", "-i", joined, "-i", boom_wav, "-i", pop_wav,
         "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out, "-y"])
    print("OK", out, "dur", round(duration(out), 1), "replay", replay)


if __name__ == "__main__":
    main()
