"""video-watcher: bir videoyu Claude'un "izleyebileceği" pakete çevirir.

Çıktı klasörü:
  video.mp4          indirilen video
  frames/            sahne değişimlerinde + sabit aralıkla alınmış kareler (zaman damgalı)
  contact_sheet.jpg  tüm karelerin tek bakışta görüldüğü ızgara
  transcript.txt     zaman damgalı konuşma metni (YouTube altyazısı ya da Whisper)
  watch.md           kare + metni zaman çizelgesinde birleştiren rapor (Claude bunu okur)
  meta.json          başlık, kanal, süre, açıklama
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


# ---------- 1. İndirme ----------
def download(url: str, out: Path, sub_langs: str) -> dict:
    import yt_dlp

    opts = {
        "outtmpl": str(out / "video.%(ext)s"),
        "format": "bv*[height<=1080]+ba/b",
        "merge_output_format": "mp4",
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": sub_langs.split(","),
        "subtitlesformat": "vtt",
        "quiet": True,
        "noprogress": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    meta = {k: info.get(k) for k in ("id", "title", "uploader", "duration", "description", "upload_date", "webpage_url")}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return meta


def local_video(path: Path, out: Path) -> dict:
    shutil.copy(path, out / "video.mp4")
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).strip())
    meta = {"title": path.stem, "duration": dur}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return meta


# ---------- 2. Kareler ----------
def extract_frames(video: Path, out: Path, every: float, scene: float) -> list[tuple[float, Path]]:
    fdir = out / "frames"
    fdir.mkdir(exist_ok=True)
    # sabit aralık + sahne değişimi; showinfo ile zaman damgalarını yakala
    vf = f"select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,{every})+gt(scene\\,{scene})',showinfo,scale=540:-2"
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(video), "-vf", vf, "-vsync", "vfr", "-q:v", "3", str(fdir / "f_%04d.jpg")],
        capture_output=True, text=True,
    )
    times = [float(m) for m in re.findall(r"pts_time:([\d.]+)", proc.stderr)]
    files = sorted(fdir.glob("f_*.jpg"))
    frames = []
    for t, f in zip(times, files):
        new = fdir / f"t{t:07.2f}s.jpg"
        f.rename(new)
        frames.append((t, new))
    return frames


def contact_sheet(frames: list[tuple[float, Path]], out: Path, cols: int = 5, per_page: int = 20) -> list[Path]:
    """Okunabilirlik için sayfa başına 20 kare: contact_sheet_01.jpg, _02.jpg ..."""
    from PIL import Image, ImageDraw

    pages = []
    for n, start in enumerate(range(0, len(frames), per_page), 1):
        thumbs = [(t, Image.open(p)) for t, p in frames[start:start + per_page]]
        w = 240
        h = int(thumbs[0][1].height * w / thumbs[0][1].width)
        rows = math.ceil(len(thumbs) / cols)
        sheet = Image.new("RGB", (cols * w, rows * (h + 22)), "white")
        d = ImageDraw.Draw(sheet)
        for i, (t, im) in enumerate(thumbs):
            x, y = (i % cols) * w, (i // cols) * (h + 22)
            sheet.paste(im.resize((w, h)), (x, y + 22))
            d.text((x + 4, y + 4), f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}", fill="black")
        p = out / f"contact_sheet_{n:02d}.jpg"
        sheet.save(p, quality=85)
        pages.append(p)
    return pages


def auto_every(duration: float) -> float:
    """Süreye göre kare aralığı: ≤3 dk → 3 sn, ≤20 dk → 10 sn, daha uzun → 15 sn."""
    return 3.0 if duration <= 180 else 10.0 if duration <= 1200 else 15.0


# ---------- 3. Konuşma metni ----------
def parse_vtt(vtt: Path) -> list[tuple[float, str]]:
    segs, seen = [], set()
    for block in vtt.read_text(encoding="utf-8").split("\n\n"):
        m = re.search(r"(\d+):(\d+):([\d.]+) -->", block)
        if not m:
            continue
        t = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
        text = re.sub(r"<[^>]+>", "", "\n".join(block.splitlines()[1:])).strip()
        for line in text.splitlines():
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                segs.append((t, line))
    return segs


def whisper(video: Path, model: str) -> list[tuple[float, str]]:
    from faster_whisper import WhisperModel

    m = WhisperModel(model, device="auto", compute_type="int8")
    segments, _ = m.transcribe(str(video), vad_filter=True)
    return [(s.start, s.text.strip()) for s in segments]


def transcript(out: Path, video: Path, model: str, force_whisper: bool) -> list[tuple[float, str]]:
    vtts = sorted(out.glob("video*.vtt"))
    segs = [] if force_whisper or not vtts else parse_vtt(vtts[0])
    if not segs:
        try:
            segs = whisper(video, model)
        except ImportError:
            print("! faster-whisper kurulu değil, konuşma metni atlandı (pip install faster-whisper)", file=sys.stderr)
    (out / "transcript.txt").write_text("\n".join(f"[{t:06.1f}s] {x}" for t, x in segs), encoding="utf-8")
    return segs


# ---------- 4. Rapor ----------
def report(out: Path, meta: dict, frames, segs) -> Path:
    lines = [f"# {meta.get('title')}", "", f"- Kanal: {meta.get('uploader', '-')}", f"- Süre: {meta.get('duration')} sn",
             f"- Kaynak: {meta.get('webpage_url', '-')}", "", "## Açıklama", "", (meta.get("description") or "-"), "",
             "## Zaman çizelgesi (kare + konuşma)", ""]
    bounds = [t for t, _ in frames] + [float("inf")]
    for i, (t, p) in enumerate(frames):
        said = " ".join(x for st, x in segs if t <= st < bounds[i + 1])
        lines += [f"### {int(t // 60):02d}:{t % 60:05.2f}", f"![{p.name}](frames/{p.name})", "", f"> {said}" if said else "> (konuşma yok)", ""]
    lines += ["## Tam metin", "", "```", (out / "transcript.txt").read_text(encoding="utf-8"), "```"]
    p = out / "watch.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def main() -> None:
    ap = argparse.ArgumentParser(description="Videoyu kare + metin paketine çevirir (Claude'un izlemesi için).")
    ap.add_argument("source", help="YouTube/Shorts/Instagram/TikTok URL'si ya da yerel video dosyası")
    ap.add_argument("-o", "--out", default="watched", help="çıktı klasörü (varsayılan: watched/<id>)")
    ap.add_argument("--every", type=float, default=None, help="en az kaç saniyede bir kare (varsayılan: süreye göre 3/10/15)")
    ap.add_argument("--scene", type=float, default=0.30, help="sahne değişimi eşiği 0-1 (varsayılan 0.30)")
    ap.add_argument("--langs", default="tr,en,en-orig", help="tercih edilen altyazı dilleri")
    ap.add_argument("--whisper-model", default="small", help="faster-whisper modeli (tiny/base/small/medium/large-v3)")
    ap.add_argument("--force-whisper", action="store_true", help="altyazı olsa da Whisper ile yazıya dök")
    a = ap.parse_args()

    src = Path(a.source)
    slug = src.stem if src.exists() else re.sub(r"\W+", "_", a.source.rstrip("/").split("/")[-1].split("=")[-1])
    out = Path(a.out) / slug
    out.mkdir(parents=True, exist_ok=True)

    meta = local_video(src, out) if src.exists() else download(a.source, out, a.langs)
    video = next(out.glob("video.mp4"), None) or next(out.glob("video.*"))
    every = a.every or auto_every(float(meta.get("duration") or 0))
    frames = extract_frames(video, out, every, a.scene)
    contact_sheet(frames, out)
    segs = transcript(out, video, a.whisper_model, a.force_whisper)
    p = report(out, meta, frames, segs)
    print(f"✓ {len(frames)} kare, {len(segs)} konuşma satırı → {p}")


if __name__ == "__main__":
    main()
