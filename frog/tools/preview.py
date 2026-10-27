#!/usr/bin/env python3
"""按 index.ux / library.ux 的 CSS 数值 1:1 还原预览。"""
from PIL import Image, ImageDraw, ImageFont

S = 3
W, H = 212, 520
A = '/Users/jay/开发/band11/frog/app/src/assets/frog'
F_CJK = '/System/Library/Fonts/Hiragino Sans GB.ttc'
F_DIN = '/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf'

BG = (255, 249, 230)
INK = (58, 42, 10)
DIM = (150, 124, 74)
DIM2 = (168, 144, 96)
SPOT = (253, 235, 178)
CARD = (255, 253, 245)
BORD = (233, 206, 140)

f_clock = ImageFont.truetype(F_DIN, 34 * S)
f_date = ImageFont.truetype(F_CJK, 12 * S)
f_bub = ImageFont.truetype(F_CJK, 12 * S)
f_btn = ImageFont.truetype(F_CJK, 13 * S)
f_small = ImageFont.truetype(F_CJK, 9 * S)
f_title = ImageFont.truetype(F_CJK, 16 * S)
f_sub = ImageFont.truetype(F_CJK, 10 * S)
f_name = ImageFont.truetype(F_CJK, 11 * S)


def rounded(img, box, radius, fill):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=radius, fill=fill)


def paste_round(img, path, box, radius):
    im = Image.open(path).convert('RGB')
    w = int(box[2] - box[0])
    h = int(box[3] - box[1])
    im = im.resize((w, h), Image.LANCZOS)
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    img.paste(im, (int(box[0]), int(box[1])), mask)


def build_index(out, clip='idle', frame=0, line='看什么看，没见过靓蛙？',
                laughs=3, streak=12):
    img = Image.new('RGB', (W * S, H * S), BG)
    d = ImageDraw.Draw(img)

    def ct(x, y, t, f, fill):
        d.text((x * S, y * S), t, font=f, fill=fill, anchor='mm')

    blocks = [(40, 0), (14, 1), (246, 6), (36, 12), (34, 12), (12, 10)]
    total = sum(b[0] for b in blocks) + sum(b[1] for b in blocks)
    y = (H - total) / 2

    ct(W / 2, y + 20, '21:53', f_clock, INK); y += 40 + 1
    ct(W / 2, y + 7, '10月27日 周二', f_date, DIM); y += 14 + 6
    paste_round(img, f'{A}/{clip}/f_{frame:03d}.png', (4 * S, y * S, 208 * S, (y + 246) * S), 26 * S)
    y += 246 + 12

    rounded(img, (11 * S, y * S, 201 * S, (y + 36) * S), 17 * S, CARD)
    d.rounded_rectangle((11 * S, y * S, 201 * S, (y + 36) * S), radius=17 * S, outline=BORD, width=S)
    ct(W / 2, y + 18, line, f_bub, INK); y += 36 + 12

    rounded(img, (58 * S, y * S, 154 * S, (y + 34) * S), 17 * S, SPOT)
    d.rounded_rectangle((58 * S, y * S, 154 * S, (y + 34) * S), radius=17 * S, outline=BORD, width=S)
    ct(W / 2, y + 17, '动画库', f_btn, INK); y += 34 + 10

    ct(W / 2, y + 6, f'今日笑 {laughs} 次 · 连续陪伴 {streak} 天', f_small, DIM2)
    img.save(out)
    img.resize((W * 2, H * 2), Image.LANCZOS).save(out.replace('.png', '_2x.png'))


def build_library(out):
    img = Image.new('RGB', (W * S, H * S), BG)
    d = ImageDraw.Draw(img)

    def ct(x, y, t, f, fill):
        d.text((x * S, y * S), t, font=f, fill=fill, anchor='mm')

    total = 20 + 16 + 14 + 2 * 124 + 12 + 32
    y = (H - total) / 2
    ct(W / 2, y + 10, '动画库', f_title, INK); y += 20
    ct(W / 2, y + 5, '点一个，回首页播给你看', f_sub, DIM2); y += 16 + 14

    cards = [('idle', 0, '待机'), ('laugh', 6, '捧腹大笑'),
             ('listen', 6, '倾听'), ('lie', 2, '躺平')]
    for i, (clip, fr, name) in enumerate(cards):
        col = i % 2
        row = i // 2
        x = 18 + col * 98
        yy = y + row * 134
        rounded(img, (x * S, yy * S, (x + 88) * S, (yy + 124) * S), 16 * S, CARD)
        d.rounded_rectangle((x * S, yy * S, (x + 88) * S, (yy + 124) * S), radius=16 * S,
                            outline=BORD, width=S)
        paste_round(img, f'{A}/{clip}/f_{fr:03d}.png',
                    ((x + 4) * S, (yy + 4) * S, (x + 84) * S, (yy + 102) * S), 10 * S)
        ct(x + 44, yy + 113, name, f_name, INK)

    y += 2 * 124 + 12
    rounded(img, (58 * S, y * S, 154 * S, (y + 32) * S), 16 * S, SPOT)
    d.rounded_rectangle((58 * S, y * S, 154 * S, (y + 32) * S), radius=16 * S, outline=BORD, width=S)
    ct(W / 2, y + 16, '返回', f_btn, INK)
    img.save(out)
    img.resize((W * 2, H * 2), Image.LANCZOS).save(out.replace('.png', '_2x.png'))


if __name__ == '__main__':
    build_index('/Users/jay/开发/band11/frog/preview.png')
    build_library('/Users/jay/开发/band11/frog/preview_library.png')
    print('ok')
