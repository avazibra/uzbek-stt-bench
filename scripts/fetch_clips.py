#!/usr/bin/env python3
"""Fetch the benchmark clips from the podcast's public RSS audio and cut them.

Mirrors oddiy-podcast/scripts/namuna.ts: same episodes, same start offsets,
`-c copy` so nothing is re-encoded. Needs ffmpeg and network.

  python3 scripts/fetch_clips.py          # all clips
  python3 scripts/fetch_clips.py ep40     # one clip
"""
import json, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = json.loads((ROOT / "clips.json").read_text())
FULL = ROOT / "clips" / "full"

def fetch(clip):
    FULL.mkdir(parents=True, exist_ok=True)
    full = FULL / f"{clip['id']}.mp3"
    out = ROOT / "clips" / f"{clip['id']}.mp3"
    if out.exists() and out.stat().st_size > 0:
        print(f"{clip['id']}: already present"); return
    if not full.exists():
        print(f"{clip['id']}: downloading {clip['audio_url']}")
        req = urllib.request.Request(clip["audio_url"], headers={"User-Agent": "uzbek-stt-bench/1.0"})
        with urllib.request.urlopen(req, timeout=600) as r, open(full, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(clip["start_sec"]),
                    "-t", str(META["clip_seconds"]), "-i", str(full), "-c", "copy", str(out)], check=True)
    print(f"{clip['id']}: {out} ({out.stat().st_size/1e6:.1f} MB)")

if __name__ == "__main__":
    want = set(sys.argv[1:])
    for c in META["clips"]:
        if not want or c["id"] in want:
            fetch(c)
