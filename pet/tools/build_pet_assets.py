#!/usr/bin/env python3
"""把 dsh-pet-indesktop 的 webm 素材转成手环快应用可用的 PNG 帧序列。

管线：抽帧 → 黑底抠像（alpha + 颜色反解）→ 固定框裁切 → 64 色量化 → 写入 app/src/assets/pet。
用法：
    python3 build_pet_assets.py            # 全部
    python3 build_pet_assets.py idle happy # 指定 clip
"""
import argparse
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path("/Users/jay/开发/band11")
SRC = ROOT / "pet_src/assets/characters/shenshen/videos"
OUT = ROOT / "pet/app/src/assets/pet"
FFMPEG = "/opt/homebrew/bin/ffmpeg"

# body_box（640×360 坐标系）：角色 + 手部动作的安全区
BODY = (206, 55, 434, 335)   # 实测所有片段角色包围盒的并集（再加 4px 余量）
W = 170                      # 输出画布宽，高按各 clip 裁剪框比例算
LO, HI = 22, 62          # 抠像阈值

SPECS = [
    # name,    source,                          fps, dur, loop, box(可选), start(可选)
    ("idle",   "idle/待机呼吸休闲.webm",          8, 3.0, True),
    ("happy",  "click/点击回应-开心跃动.webm",     12, 1.2, False),
    ("shy",    "click/点击回应-害羞惊讶.webm",     12, 1.2, False),
    ("pat",    "click/点击回应-挠痒咯咯笑.webm",   12, 1.2, False),
    ("eat",    "random/大口吃零食.webm",          10, 1.8, False),
    ("sleep",  "random/原地小憩沉眠.webm",         8, 2.5, True),
    ("token",  "random/吃Token.webm",            10, 1.8, False, (150, 45, 494, 335)),
    ("code",   "random/工作状态-忙碌点按.webm",    10, 1.8, False),
    ("yawn",   "random/哈欠连天.webm",            10, 2.0, False),
    # —— 扩展包 ——
    ("brush",  "random/晨间刷牙.webm",            10, 2.0, False),
    ("stretch","random/超大伸懒腰.webm",          10, 2.0, False),
    ("wake",   "random/打瞌睡被惊醒.webm",        10, 1.8, False),
    ("shock",  "random/被吓一跳.webm",            10, 1.8, False),
    ("dance1", "random/优雅女仆舞.webm",          10, 2.4, False),
    ("dance2", "random/轻快摇摆舞.webm",          10, 2.4, False),
    ("cat",    "random/撸猫.webm",                10, 2.0, False),
    ("rubik",  "random/原地专心玩魔方.webm",      10, 2.0, False),
    ("whale",  "random/蓝鲸现世.webm",            10, 2.4, False, (150, 40, 494, 340)),
]


def key_black(im: Image.Image) -> Image.Image:
    """黑底反解抠像：alpha 由最大通道给出，颜色除以 alpha 还原。"""
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    maxc = a.max(axis=2)
    alpha = np.clip((maxc - LO) / (HI - LO), 0, 1)
    safe = np.maximum(alpha, 1e-3)[..., None]
    rgb = np.clip(a / safe, 0, 255)
    return Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")


def extract(src: Path, fps: int, tmp: Path):
    tmp.mkdir(parents=True, exist_ok=True)
    cmd = [FFMPEG, "-v", "error", "-i", str(src), "-vf", f"fps={fps}", "-y", str(tmp / "f_%03d.png")]
    subprocess.run(cmd, check=True)
    return sorted(tmp.glob("f_*.png"))


def pick_loop_start(frames, n):
    """在帧序列里挑一个接缝最顺的 n 帧窗口。"""
    small = [np.asarray(Image.open(p).convert("L").resize((80, 45)), np.float32) for p in frames]
    best = (None, 1e9)
    for s in range(0, len(small) - n - 1):
        seam = float(np.abs(small[s] - small[s + n]).mean())
        motion = float(np.mean([np.abs(small[i] - small[i + 1]).mean() for i in range(s, s + n - 1)]))
        cost = seam + 0.2 * motion
        if cost < best[1]:
            best = (s, cost)
    return best[0] if best[0] is not None else 0


def build(name, rel, fps, dur, loop, box=None, start=None):
    src = SRC / rel
    if not src.exists():
        print(f"  !! 缺少素材 {rel}")
        return None
    n = max(2, round(fps * dur))
    with tempfile.TemporaryDirectory() as td:
        frames = extract(src, fps, Path(td))
        s = start if start is not None else (pick_loop_start(frames, n) if loop else round(fps * 0.5))
        s = min(s, max(0, len(frames) - n))
        sel = frames[s:s + n]

        x0, y0, x1, y1 = box or BODY
        outdir = OUT / name
        if outdir.exists():
            shutil.rmtree(outdir)
        outdir.mkdir(parents=True)

        total = 0
        h = round((y1 - y0) * W / (x1 - x0))
        for i, p in enumerate(sel):
            im = Image.open(p)
            im = im.crop((x0, y0, x1, y1)).resize((W, h), Image.LANCZOS)
            k = key_black(im)
            q = k.quantize(colors=64, method=Image.FASTOCTREE)
            buf = io.BytesIO()
            q.save(buf, "PNG", optimize=True)
            data = buf.getvalue()
            total += len(data)
            (outdir / f"f_{i:03d}.png").write_bytes(data)
        print(f"  {name:6s} {len(sel):3d} 帧  {total/1024:6.1f} KB  ({total/len(sel)/1024:.1f} KB/帧)  start={s}")
        return {"name": name, "frames": len(sel), "fps": fps, "loop": loop, "w": W, "h": h}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="*")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    metas = []
    for spec in SPECS:
        if args.clips and spec[0] not in args.clips:
            continue
        m = build(*spec)
        if m:
            metas.append(m)
    index = OUT / "clips.json"
    old = json.loads(index.read_text()) if index.exists() else []
    merged = {m["name"]: m for m in old}
    merged.update({m["name"]: m for m in metas})
    index.write_text(json.dumps(list(merged.values()), ensure_ascii=False, indent=2))
    print("total", sum(m["frames"] for m in metas), "frames")


if __name__ == "__main__":
    sys.exit(main())
