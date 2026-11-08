import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
d = sys.argv[1]
F = '/tmp/claude-0/-home-user-Gemini-2-5/c96cf704-d013-5c2a-be1f-2857f80af15a/scratchpad/fonts/LXGWWenKai-Regular.ttf'
f = lambda s: ImageFont.truetype(F, s)
W, H = 1080, 1440
BG, INK, SUB, ACC = (246, 241, 230), (36, 28, 24), (110, 98, 88), (186, 38, 44)
P = Image.new('RGB', (W, H), BG)
# faint ink peony from the poster's header
post = Image.open(f'{d}/poster_wenkai.png').convert('RGB')
ink = post.crop((0, 0, 720, 440)).resize((560, 342))
g = np.asarray(ink.convert('L')).astype(np.float32); a = ((246 - g).clip(0, 80) * 3.2).clip(0, 255).astype(np.uint8)
P.paste(Image.new('RGB', ink.size, (60, 50, 46)), (-20, 0), Image.fromarray(a).point(lambda v: int(v * 0.5)))
P.paste(Image.new('RGB', ink.size, (60, 50, 46)), (W - 600, 30), Image.fromarray(a).transpose(Image.FLIP_LEFT_RIGHT).point(lambda v: int(v * 0.4)))
dr = ImageDraw.Draw(P)
# main title
dr.text((W // 2, 120), '同一朵牡丹', font=f(150), fill=INK, anchor='mm', stroke_width=3, stroke_fill=INK)
# seal (from poster)
seal = post.crop((1460, 80, 1680, 290)).resize((96, 92), Image.LANCZOS)
m = seal.convert('L').point(lambda v: 255 if v < 200 else 0)
P.paste(seal, (W - 128, 40), m)
# red hook band
hook = '11位西方大师 怎么画？'
fh = f(66); tw = dr.textlength(hook, font=fh)
dr.rounded_rectangle((W // 2 - tw / 2 - 40, 220, W // 2 + tw / 2 + 40, 316), 18, fill=ACC)
dr.text((W // 2, 268), hook, font=fh, fill=(255, 246, 236), anchor='mm', stroke_width=1, stroke_fill=(255, 246, 236))
names = '梵高 · 莫奈 · 毕加索 · 达利 · 克里姆特 · 马蒂斯 …'
dr.text((W // 2, 362), names, font=f(36), fill=SUB, anchor='mm')
# 4 x 3 grid
files = ['peony_lineart_vangogh', 'peony_monet', 'peony_picasso', 'peony_klimt', 'peony_matisse', 'peony_dali',
         'peony_munch', 'peony_kandinsky', 'peony_cezanne', 'peony_mondrian', 'peony_pollock', 'base']
lab = ['梵高', '莫奈', '毕加索', '克里姆特', '马蒂斯', '达利', '蒙克', '康定斯基', '塞尚', '蒙德里安', '波洛克', '线稿']
gap, mx, top = 12, 36, 410
tw_ = (W - 2 * mx - 3 * gap) // 4; th_ = int(tw_ * 4 / 3)
for k, fn in enumerate(files):
    c, r = k % 4, k // 4
    x, y = mx + c * (tw_ + gap), top + r * (th_ + gap)
    im = Image.open(f'{d}/{fn}.png').convert('RGB').resize((tw_, th_), Image.LANCZOS)
    P.paste(im, (x, y))
    # name tag
    ft = f(30); lw = dr.textlength(lab[k], font=ft) + 22
    dr.rounded_rectangle((x + 8, y + th_ - 50, x + 8 + lw, y + th_ - 10), 10, fill=(255, 250, 242))
    dr.text((x + 8 + lw / 2, y + th_ - 30), lab[k], font=ft, fill=INK, anchor='mm')
P.save(f'{d}/douyin_cover.jpg', quality=93); P.save(f'{d}/douyin_cover.png')
