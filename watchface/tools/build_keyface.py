#!/usr/bin/env python3
"""生成「深蓝密钥」表盘（小米手环 11 / q66）的 wfDef.json + images/。

设计：212x520 画布
  y   0-300  角色插画（裁切 + 底部渐隐）
  y 302-306  发光分隔线
  y 330-394  时间 HH:MM（4 个单字符数字控件，冒号烘焙进底图）
  y 398-486  玻璃面板：DEEPSEEK · QUOTA + 余额 + 进度条 + 同步时间
  y 500-520  底部品牌小字

时间控件用 dataSrc（从官方熄屏表盘 362150004 逆向得到的编码）：
  0A11 = 小时十位（3 张图 0-2）
  0911 = 小时个位（10 张图）
  1211 = 分钟十位（6 张图 0-5）
  1111 = 分钟个位（10 张图）
每个控件 showCount=1，位置完全由我们控制；冒号是静态图形，不依赖固件。

余额是**静态快照**（表盘不能联网），刷新要重新打包：
  python3 refresh_quota.py                      # 调 API 拉余额 → 重打包
  python3 build_keyface.py --balance 23.45 --updated "10-27 11:52" --pack
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H = 212, 520

# ---- 配色 -------------------------------------------------------------
BG_TOP = (6, 16, 39)
BG_MID = (10, 27, 58)
BG_BOT = (4, 9, 20)
INK = (232, 246, 255)
ACCENT = (79, 216, 255)
ACCENT_DIM = (31, 78, 122)
PANEL = (11, 27, 51)
TRACK = (17, 41, 74)
MUTED = (122, 168, 198)

FONT_DIN = "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf"
FONT_UI = "/System/Library/Fonts/Supplemental/Futura.ttc"
FONT_CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"

# ---- 布局 -------------------------------------------------------------
ART_H = 300
TIME_Y = 330
DIGIT_W, DIGIT_H = 32, 64
DIGIT_X = [28, 65, 115, 152]
COLON_X = 102
PANEL_BOX = (12, 398, 200, 486)
BAR_BOX = (26, 456, 186, 462)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(size, stops):
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                px[0, y] = lerp(c0, c1, (t - p0) / max(1e-6, p1 - p0))
                break
        else:
            px[0, y] = stops[-1][1]
    return img.resize(size, Image.BILINEAR)


def glow(mask: Image.Image, color, radius, strength=1.0) -> Image.Image:
    blurred = mask.filter(ImageFilter.GaussianBlur(radius))
    layer = Image.new("RGBA", mask.size, color + (0,))
    layer.putalpha(blurred.point(lambda v: min(255, int(v * strength))))
    return layer


def draw_spaced(draw, xy, text, font, fill, spacing=0.0, center=True):
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * max(0, len(text) - 1)
    x = xy[0] - total / 2 if center else xy[0]
    for ch, w in zip(text, widths):
        draw.text((x, xy[1]), ch, font=font, fill=fill, anchor="la")
        x += w + spacing


def build_character(art_path: Path) -> Image.Image:
    art = Image.open(art_path).convert("RGBA")
    scale = ART_H / art.height
    art = art.resize((max(W, round(art.width * scale)), ART_H), Image.LANCZOS)
    left = max(0, (art.width - W) // 2)
    art = art.crop((left, 0, left + W, ART_H))

    fade_h = 110
    ramp = Image.new("L", (W, fade_h), 255)
    rp = ramp.load()
    for y in range(fade_h):
        t = y / (fade_h - 1)
        v = int(255 * (1 - t) ** 1.6)
        for x in range(W):
            rp[x, y] = v
    base_alpha = art.getchannel("A")
    tail = base_alpha.crop((0, ART_H - fade_h, W, ART_H))
    base_alpha.paste(ImageChops.multiply(tail, ramp), (0, ART_H - fade_h))
    art.putalpha(base_alpha)
    return art


def draw_quota_panel(bg: Image.Image, quota: dict):
    box = PANEL_BOX
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle(box, radius=16, fill=PANEL + (150,),
                                            outline=ACCENT_DIM + (200,), width=1)
    inner = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(inner).rounded_rectangle(
        (box[0] + 1, box[1] + 1, box[2] - 1, box[3] - 1), radius=15, fill=ACCENT + (10,))
    bg.alpha_composite(panel)
    bg.alpha_composite(inner)

    d = ImageDraw.Draw(bg)
    f_title = ImageFont.truetype(FONT_UI, 8)
    draw_spaced(d, (W / 2, box[1] + 9), "DEEPSEEK  ·  QUOTA", f_title, ACCENT + (230,), spacing=1.7)

    total = quota.get("total")
    if total is None:
        f_num = ImageFont.truetype(FONT_DIN, 30)
        draw_spaced(d, (W / 2, box[1] + 20), "--.--", f_num, MUTED + (150,), spacing=1.0)
    else:
        f_cur = ImageFont.truetype(FONT_CJK, 16)
        f_num = ImageFont.truetype(FONT_DIN, 32)
        num = f"{total:,.2f}"
        wn = d.textlength(num, font=f_num)
        wc = d.textlength("¥", font=f_cur)
        gap = 4
        x0 = W / 2 - (wn + wc + gap) / 2
        d.text((x0, box[1] + 25), "¥", font=f_cur, fill=MUTED + (235,))
        d.text((x0 + wc + gap, box[1] + 17), num, font=f_num, fill=INK + (250,))

    # 进度条
    cap = quota.get("cap") or 50.0
    ratio = 0.0 if total is None else max(0.0, min(1.0, total / cap))
    x0, y0, x1, y1 = BAR_BOX
    d.rounded_rectangle(BAR_BOX, radius=(y1 - y0) // 2, fill=TRACK + (255,))
    if ratio > 0:
        fill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        xr = x0 + max(5, round((x1 - x0) * ratio))
        ImageDraw.Draw(fill).rounded_rectangle((x0, y0, xr, y1), radius=(y1 - y0) // 2,
                                               fill=ACCENT + (235,))
        bg.alpha_composite(fill.filter(ImageFilter.GaussianBlur(3)))
        bg.alpha_composite(fill)
        dot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cy = (y0 + y1) / 2
        ImageDraw.Draw(dot).ellipse((xr - 3, cy - 3, xr + 3, cy + 3), fill=(214, 246, 255, 255))
        bg.alpha_composite(dot.filter(ImageFilter.GaussianBlur(1.2)))
        bg.alpha_composite(dot)

    f_foot = ImageFont.truetype(FONT_CJK, 7)
    note = quota.get("updated") or "未同步 · 待刷新"
    draw_spaced(d, (W / 2, box[1] + 72), note, f_foot, MUTED + (170,), spacing=0.6)


def build_background(art_path: Path, quota: dict) -> Image.Image:
    bg = vgrad((W, H), [(0.0, BG_TOP), (0.55, BG_MID), (1.0, BG_BOT)]).convert("RGBA")
    bg.alpha_composite(build_character(art_path), (0, 0))

    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse((10, 150, W - 10, H - 40), fill=ACCENT + (18,))
    bg.alpha_composite(halo.filter(ImageFilter.GaussianBlur(48)))

    d = ImageDraw.Draw(bg)

    line = Image.new("RGBA", (W, 1), (0, 0, 0, 0))
    lp = line.load()
    for x in range(W):
        t = abs(x - W / 2) / (W / 2)
        lp[x, 0] = ACCENT + (int(190 * max(0.0, 1 - t) ** 1.4),)
    bg.alpha_composite(line.filter(ImageFilter.GaussianBlur(2)).resize((W, 5)), (0, 301))
    bg.alpha_composite(line.resize((W, 1)), (0, 303))

    rnd = random.Random(11)
    for _ in range(34):
        x = rnd.randint(4, W - 5)
        y = rnd.randint(306, H - 6)
        if 320 < y < 396 and 20 < x < 196:
            continue
        if 398 < y < 486:
            continue
        r = rnd.choice([0.6, 0.8, 1.0, 1.4])
        d.ellipse((x, y, x + r, y + r), fill=ACCENT + (rnd.randint(30, 110),))

    draw_quota_panel(bg, quota)

    f_foot = ImageFont.truetype(FONT_UI, 7)
    draw_spaced(d, (W / 2, H - 20), "BAND 11   ·   DEEPSEEK", f_foot, MUTED + (150,), spacing=1.6)
    return bg


def build_colon(bg: Image.Image):
    d = ImageDraw.Draw(bg)
    for cy in (TIME_Y + 18, TIME_Y + 40):
        d.ellipse((COLON_X, cy, COLON_X + 8, cy + 8), fill=ACCENT + (255,))
    return bg


def build_digits() -> dict[str, list[Image.Image]]:
    font = ImageFont.truetype(FONT_DIN, 54)

    def one(ch: str) -> Image.Image:
        img = Image.new("RGBA", (DIGIT_W, DIGIT_H), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((DIGIT_W / 2, DIGIT_H / 2 - 2), ch, font=font,
                                 fill=(236, 250, 255, 255), anchor="mm")
        g = glow(img.getchannel("A"), (60, 190, 255), 4.0, 1.05)
        out = Image.new("RGBA", img.size, (0, 0, 0, 0))
        out.alpha_composite(g)
        out.alpha_composite(img)
        return out

    return {
        "h_tens": [one(c) for c in "012"],
        "h_units": [one(c) for c in "0123456789"],
        "m_tens": [one(c) for c in "012345"],
        "m_units": [one(c) for c in "0123456789"],
    }


def compose_preview(bg: Image.Image, digits, hh: str, mm: str) -> Image.Image:
    out = bg.copy()
    for x, img in [
        (DIGIT_X[0], digits["h_tens"][int(hh[0])]),
        (DIGIT_X[1], digits["h_units"][int(hh[1])]),
        (DIGIT_X[2], digits["m_tens"][int(mm[0])]),
        (DIGIT_X[3], digits["m_units"][int(mm[1])]),
    ]:
        out.alpha_composite(img, (x, TIME_Y))
    return out


def write_project(out: Path, art: Path, quota: dict, face_id: str, name: str):
    out.mkdir(parents=True, exist_ok=True)
    img_dir = out / "images"
    if img_dir.exists():
        shutil.rmtree(img_dir)
    img_dir.mkdir()

    bg = build_colon(build_background(art, quota))
    bg.save(img_dir / "image_0001.png")

    digits = build_digits()
    for li, imgs in enumerate(digits.values()):
        for i, im in enumerate(imgs):
            im.save(img_dir / f"imagelist_{li:04d}_{i:04d}.png")

    sample = compose_preview(bg, digits, "21", "53").convert("RGBA")
    sample.resize((134, 328), Image.LANCZOS).save(img_dir / "preview.png")
    sample.convert("RGB").resize((W * 2, H * 2), Image.NEAREST).save(out / "preview_2x.png")

    def digit_el(idx, x, src, cnt, li):
        return {
            "x": x, "y": TIME_Y,
            "prop7Index": idx, "prop7Length": 20,
            "prop7Raw": "000000110000E8030100000300000000000000",
            "dataSrc": src,
            "type": "widge_dignum",
            "showZero": False, "align": 1, "showCount": 1, "spacing": 0,
            "imageList": [f"imagelist_{li:04d}_{i:04d}" for i in range(cnt)],
        }

    wf = {
        "name": name,
        "id": face_id,
        "previewImg": "preview",
        "faceStyleCount": 1,
        "faces": [{
            "name": "样式1",
            "imageDir": "images",
            "elements": [
                {"x": 0, "y": 0, "type": "element", "image": "image_0001"},
                digit_el(0, DIGIT_X[0], "0A11", 3, 0),
                digit_el(1, DIGIT_X[1], "0911", 10, 1),
                digit_el(2, DIGIT_X[2], "1211", 6, 2),
                digit_el(3, DIGIT_X[3], "1111", 10, 3),
            ],
            "imageDefs": [1],
            "imageListDefs": [0, 1, 2, 3],
            "extraProp7": [],
        }],
    }
    (out / "wfDef.json").write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def pack(work: Path, bin_out: Path, tool_java: Path):
    cmd = ["java", str(tool_java), "pack", str(work), str(bin_out), "o66"]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"  -> {bin_out} ({bin_out.stat().st_size:,} bytes)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--balance", type=float, default=None, help="余额快照，如 23.45；不填显示 --.--")
    ap.add_argument("--cap", type=float, default=50.0, help="进度条满格对应的金额")
    ap.add_argument("--updated", default="", help='同步时间文本，如 "10-27 11:52"')
    ap.add_argument("--id", default="362155011")
    ap.add_argument("--name", default="深蓝密钥")
    ap.add_argument("--pack", action="store_true")
    ap.add_argument("--tool", default="/Users/jay/开发/band11/_research/Mi8WfBinTool.java")
    a = ap.parse_args()

    quota = {"total": a.balance, "cap": a.cap, "updated": a.updated or None}
    work = write_project(Path(a.out), Path(a.art), quota, a.id, a.name)
    print(f"project -> {work}")
    if a.pack:
        pack(work, work.parent / f"{a.name}_{a.id}.bin", Path(a.tool))


if __name__ == "__main__":
    sys.exit(main())
