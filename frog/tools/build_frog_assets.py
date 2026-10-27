#!/usr/bin/env python3
"""腕上奶蛙 · 素材管线（只用 pet/ 四个循环动画）

源：https://github.com/Nailong-Studio/wallpaper  pet/ 目录（MIT）
处理：GIF 抽帧 → 按整段动画的联合 bbox 裁切 → 等比缩放 → 烘焙舞台底色 → 量化

用法：
  python3 build_frog_assets.py [clip ...]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

SRC = '/Users/jay/开发/band11/frog_src'
OUT = '/Users/jay/开发/band11/frog/app/src/assets'

# 舞台画布（与 index.ux 中 .frog 的宽高、圆角严格一致）
CW, CH = 204, 246
PAD = 17
SPOT = (253, 235, 178)      # #FDEBB2

CLIPS = {
    'idle':   ('pet/奶蛙-桌宠-待机.gif',    8, True),
    'laugh':  ('pet/奶蛙-桌宠-捧腹大笑.gif', 10, False),
    'listen': ('pet/奶蛙-桌宠-倾听.gif',    10, False),
    'lie':    ('pet/奶蛙-桌宠-躺平.gif',     6, True),
}

TITLE = {
    'idle': '待机',
    'laugh': '捧腹大笑',
    'listen': '倾听',
    'lie': '躺平',
}


def union_bbox(im):
    x0, y0, x1, y1 = 10 ** 6, 10 ** 6, 0, 0
    for i in range(im.n_frames):
        im.seek(i)
        a = np.array(im.convert('RGBA'))[..., 3]
        ys, xs = np.where(a > 10)
        if len(xs) == 0:
            continue
        x0 = min(x0, int(xs.min()))
        x1 = max(x1, int(xs.max()))
        y0 = min(y0, int(ys.min()))
        y1 = max(y1, int(ys.max()))
    return x0, y0, x1 + 1, y1 + 1


def fit(im, w, h):
    r = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)


STANDING = ('idle', 'laugh', 'listen')
_COMMON = {}


def common_box():
    """三个站立动画用同一个联合 bbox，切换时人物不跳。"""
    if 'box' in _COMMON:
        return _COMMON['box']
    x0, y0, x1, y1 = 10 ** 6, 10 ** 6, 0, 0
    for n in STANDING:
        im = Image.open(os.path.join(SRC, CLIPS[n][0]))
        b = union_bbox(im)
        x0, y0 = min(x0, b[0]), min(y0, b[1])
        x1, y1 = max(x1, b[2]), max(y1, b[3])
    _COMMON['box'] = (x0, y0, x1, y1)
    return _COMMON['box']


def build_clip(name):
    src, fps, loop = CLIPS[name]
    im = Image.open(os.path.join(SRC, src))
    box = common_box() if name in STANDING else union_bbox(im)
    d = f'{OUT}/frog/{name}'
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))

    canvas = Image.new('RGB', (CW, CH), SPOT)
    n = 0
    for i in range(im.n_frames):
        im.seek(i)
        frame = im.convert('RGBA').crop(box)
        frame = fit(frame, CW - PAD * 2, CH - PAD * 2)
        canvas = Image.new('RGB', (CW, CH), SPOT)
        canvas.paste(frame, ((CW - frame.width) // 2, (CH - frame.height) // 2), frame)
        canvas.quantize(colors=160, method=Image.FASTOCTREE).save(
            f'{d}/f_{n:03d}.png', optimize=True)
        n += 1
    print(f'  {name}: {n} 帧  bbox {box}')
    return {'name': name, 'title': TITLE[name], 'frames': n, 'fps': fps,
            'loop': loop, 'w': CW, 'h': CH}


def main():
    want = sys.argv[1:] or list(CLIPS)
    reg = [build_clip(n) for n in want]
    json.dump(reg, open(f'{OUT}/clips.json', 'w'), ensure_ascii=False, indent=1)
    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _, fs in os.walk(OUT) for f in fs)
    print(f'  素材合计 {total / 1024:.0f} KB')


if __name__ == '__main__':
    main()
