"""Douyin cover 1080x1440 (3:4), 12-up grid (4 columns x 3 rows), title and hook kept in the upper part
(the bottom of a Douyin cover is covered by the title/buttons).
usage: cover_lotus.py paintings_dir font.ttf out.png"""
import sys
from PIL import Image, ImageDraw, ImageFont
pd, FONT, OUT = sys.argv[1:4]
f = lambda s: ImageFont.truetype(FONT, s)
W, H = 1080, 1440
BG, INK, SUB, ACC = (246, 241, 230), (36, 28, 24), (110, 98, 88), (186, 38, 44)
order = [('vangogh', '梵高'), ('matisse', '马蒂斯'), ('kandinsky', '康定斯基'), ('monet', '莫奈'), ('magritte', '马格利特'), ('mondrian', '蒙德里安'),
         ('klimt', '克里姆特'), ('schiele', '席勒'), ('pollock', '波洛克'), ('picasso', '毕加索'), ('munch', '蒙克'), ('lichtenstein', '利希滕斯坦')]
P = Image.new('RGB', (W, H), BG)
wm = Image.open(f'{pd}/../../lineart/base_plain.png').convert('L').resize((420, 560), Image.LANCZOS)
for (x, y, flip) in [(-30, -10, False), (W - 390, -10, True)]:
    w = wm.transpose(Image.FLIP_LEFT_RIGHT) if flip else wm
    a = w.point(lambda v: int((255 - v) * 0.30)); P.paste(Image.new('RGB', w.size, (60, 50, 46)), (x, y), a)
dr = ImageDraw.Draw(P)
dr.text((W // 2 - 40, 125), '同一朵荷花', font=f(150), fill=INK, anchor='mm', stroke_width=3, stroke_fill=INK)
sx, sy = W - 150, 52                                              # seal: 出水芙蓉, white characters on red
dr.rounded_rectangle((sx, sy, sx + 92, sy + 92), 8, fill=ACC)
for k, ch in enumerate('出水芙蓉'):
    dr.text((sx + 24 + (1 - k // 2) * 44, sy + 24 + (k % 2) * 44), ch, font=f(38), fill=(255, 248, 240), anchor='mm')
hook = '12位西方大师 怎么画？'
fh = f(66); tw = dr.textlength(hook, font=fh)
dr.rounded_rectangle((W // 2 - tw / 2 - 40, 230, W // 2 + tw / 2 + 40, 326), 18, fill=ACC)
dr.text((W // 2, 278), hook, font=fh, fill=(255, 246, 236), anchor='mm', stroke_width=1, stroke_fill=(255, 246, 236))
dr.text((W // 2, 372), '梵高 · 莫奈 · 毕加索 · 克里姆特 · 马蒂斯 · 蒙克 …', font=f(36), fill=SUB, anchor='mm')
gap, mx, top = 12, 60, 410
tw_ = (W - 2 * mx - 3 * gap) // 4; th_ = int(tw_ * 4 / 3)
for k, (fn, name) in enumerate(order):
    c, r = k % 4, k // 4; x, y = mx + c * (tw_ + gap), top + r * (th_ + gap)
    dr.rectangle((x + 5, y + 6, x + tw_ + 5, y + th_ + 6), fill=(222, 212, 196))
    P.paste(Image.open(f'{pd}/lotus_{fn}.png').convert('RGB').resize((tw_, th_), Image.LANCZOS), (x, y))
    ft = f(28 if len(name) < 5 else 25); lw = dr.textlength(name, font=ft) + 22
    dr.rounded_rectangle((x + 8, y + th_ - 48, x + 8 + lw, y + th_ - 10), 10, fill=(255, 250, 242))
    dr.text((x + 8 + lw / 2, y + th_ - 29), name, font=ft, fill=INK, anchor='mm')
P.save(OUT)
