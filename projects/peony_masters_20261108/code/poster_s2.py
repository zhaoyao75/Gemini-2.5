import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
d = sys.argv[1]
F = '/tmp/claude-0/-home-user-Gemini-2-5/c96cf704-d013-5c2a-be1f-2857f80af15a/scratchpad/fonts/LXGWWenKai-Regular.ttf'
f = lambda s: ImageFont.truetype(F, s)
W, H = 2400, 3200
BG, INK, SUB, ACC = (246, 241, 230), (40, 32, 28), (110, 98, 88), (168, 48, 70)
P = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(P)
items = [
  ('base.png',                 '线稿底图',   'Line Art',          '—',          '共同的出发点', '所有作品使用同一张线稿'),
  ('peony_gauguin.png',        '高更',       'Paul Gauguin',      '1848–1903', '后印象派',     '平涂色带与深色勾边'),
  ('peony_seurat.png',         '修拉',       'Georges Seurat',    '1859–1891', '点彩派',       '纯色小点在眼中混色'),
  ('peony_chagall.png',        '夏加尔',     'Marc Chagall',      '1887–1985', '超现实主义',   '蓝夜、月亮与倒飘的房子'),
  ('peony_schiele.png',        '席勒',       'Egon Schiele',      '1890–1918', '表现主义',     '神经质的线与白色光边'),
  ('peony_magritte.png',       '马格利特',   'René Magritte',     '1898–1967', '超现实主义',   '“这不是一朵牡丹”'),
  ('peony_rothko.png',         '罗斯科',     'Mark Rothko',       '1903–1970', '色域绘画',     '牡丹化入发光的色块'),
  ('peony_frida.png',          '弗里达',     'Frida Kahlo',       '1907–1954', '墨西哥民间',   '热带大叶与墨西哥粉'),
  ('peony_lichtenstein.png',   '利希滕斯坦', 'Roy Lichtenstein',  '1923–1997', '波普艺术',     '漫画网点与对话气泡'),
  ('peony_warhol.png',         '沃霍尔',     'Andy Warhol',       '1928–1987', '波普艺术',     '四联丝网印刷荧光色'),
  ('peony_kusama.png',         '草间弥生',   'Yayoi Kusama',      '1929–',     '当代艺术',     '无处不在的波点'),
  ('peony_hockney.png',        '霍克尼',     'David Hockney',     '1937–',     '当代 / 波普',  '加州阳光与泳池波纹'),
]
# ---- faint ink-wash peony behind the title (from the line art)
import numpy as np
from PIL import ImageChops
base = Image.open(f'{d}/base.png').convert('L'); cls = np.asarray(Image.open(f'{d}/cls.png'))
box = (380, 140, 900, 640)                                    # top bloom, its bud and leaves
lineA = np.asarray(base.crop(box)).astype(np.float32) / 255
cl = cls[box[1]:box[3], box[0]:box[2], 0]; puff = cls[box[1]:box[3], box[0]:box[2], 2].astype(np.float32) / 255
petal = np.isin(cl, [6, 7, 8]); leaf = np.isin(cl, [4, 5, 9])
wash = np.zeros_like(lineA)
wash[petal] = 0.18 + 0.32 * (1 - puff[petal])                # petals: pale ink, deeper in the folds
wash[leaf] = 0.55 + 0.25 * (1 - puff[leaf])                   # leaves: darker ink
washI = Image.fromarray((wash * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
ink = np.maximum(np.asarray(washI).astype(np.float32) / 255, (1 - lineA) * 0.9)
inkI = Image.fromarray((ink * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
inkI = inkI.resize((int(inkI.width * 1.05), int(inkI.height * 1.05)), Image.LANCZOS)
# fade towards the inner edge so it melts into the paper
fx = np.linspace(1, 0.3, inkI.width)[None, :] ** 1.1; fy = np.linspace(0.6, 1, inkI.height)[:, None] * np.linspace(1, 0.35, inkI.height)[:, None]
alpha = (np.asarray(inkI).astype(np.float32) * fx * fy * 0.36).clip(0, 255).astype(np.uint8)
inkcol = Image.new('RGB', inkI.size, (52, 44, 40))
P.paste(inkcol, (30, -30), Image.fromarray(alpha))
# mirrored, smaller sprig on the right
inkR = Image.fromarray(alpha).transpose(Image.FLIP_LEFT_RIGHT).resize((int(inkI.width * 0.7), int(inkI.height * 0.7)), Image.LANCZOS)
P.paste(Image.new('RGB', inkR.size, (52, 44, 40)), (W - inkR.width + 30, 20), Image.fromarray((np.asarray(inkR) * 0.75).astype(np.uint8)))
dr = ImageDraw.Draw(P)
# title block
cxT = W // 2
ft = f(210); tw = dr.textlength('牡丹', font=ft) + 60          # letter-spaced main title
x = cxT - tw / 2
for ch in '牡丹':
    dr.text((x, 175), ch, font=ft, fill=INK, anchor='lm', stroke_width=3, stroke_fill=INK); x += dr.textlength(ch, font=ft) + 60
# antique zhuwen seal 国色天香: red characters inside a thick red frame, worn and uneven
sx, sy, ss = int(cxT + tw / 2 + 40), 92, 156
seal = Image.new('L', (ss, ss), 0); sd = ImageDraw.Draw(seal)
sd.rounded_rectangle((0, 0, ss - 1, ss - 1), 10, fill=255); sd.rounded_rectangle((15, 15, ss - 16, ss - 16), 5, fill=0)   # thick frame
sd.line((ss // 2, 22, ss // 2, ss - 22), fill=255, width=5)                                                               # centre divider
for ch, (qx, qy) in zip('国色天香', [(1, 0), (1, 1), (0, 0), (0, 1)]):
    sd.text((ss * (0.285 + 0.43 * qx), ss * (0.29 + 0.42 * qy)), ch, font=f(56), fill=255, anchor='mm', stroke_width=2, stroke_fill=255)
rng = np.random.default_rng(7); m = np.asarray(seal).astype(np.float32)
m *= (rng.random(m.shape) > 0.06)                              # speckled wear in the ink
yy_, xx_ = np.mgrid[0:ss, 0:ss]
edge = np.minimum(np.minimum(xx_, ss - 1 - xx_), np.minimum(yy_, ss - 1 - yy_))
chips = (edge < 7) & (rng.random(m.shape) < 0.35)              # chipped, broken outer edge
m[chips] = 0
for _ in range(5):                                             # a few larger nicks
    cx_, cy_ = rng.integers(0, ss, 2); r_ = rng.integers(3, 8)
    if min(cx_, cy_, ss - cx_, ss - cy_) < 18: m[(xx_ - cx_) ** 2 + (yy_ - cy_) ** 2 < r_ * r_] = 0
sealA = Image.fromarray(m.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)).rotate(-3, resample=Image.BICUBIC, expand=True)
P.paste(Image.new('RGB', sealA.size, (186, 38, 44)), (sx, sy), sealA.point(lambda v: int(v * 0.92)))
# subtitle with ornaments
sub = '第二季 · 十一位西方艺术家 · 同一张线稿'
fsub = f(54); sw_ = dr.textlength(sub, font=fsub)
dr.text((cxT, 335), sub, font=fsub, fill=INK, anchor='mm')
for sgn in (-1, 1):
    x1 = cxT + sgn * (sw_ / 2 + 40); x2 = x1 + sgn * 170
    dr.line((x1, 335, x2, 335), fill=ACC, width=3)
    dr.ellipse((x1 - 7, 328, x1 + 7, 342), fill=ACC)
# English line, letter-spaced
eng = 'PEONY · SEASON TWO · ELEVEN MODERN ARTISTS'
fe_ = f(30); ew = sum(dr.textlength(c, font=fe_) + 8 for c in eng) - 8
x = cxT - ew / 2
for c in eng: dr.text((x, 405), c, font=fe_, fill=SUB, anchor='lm'); x += dr.textlength(c, font=fe_) + 8
# grid 3 x 4
mx, top, gap = 70, 460, 34
cw = (W - 2 * mx - 2 * gap) // 3
ch = (H - top - 140 - 3 * gap) // 4
ih = ch - 20; iw = int(ih * 3 / 4)
for n, (fn, zh, en, yrs, mov, note) in enumerate(items):
    c, r = n % 3, n // 3
    x0, y0 = mx + c * (cw + gap), top + r * (ch + gap)
    dr.rounded_rectangle((x0, y0, x0 + cw, y0 + ch), 18, fill=(255, 252, 245), outline=(222, 212, 196), width=2)
    im = Image.open(f'{d}/{fn}').convert('RGB').resize((iw, ih), Image.LANCZOS)
    ix, iy = x0 + 10, y0 + 10
    sh = Image.new('RGBA', (iw + 30, ih + 30), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((15, 15, iw + 15, ih + 15), fill=(0, 0, 0, 70))
    P.paste(sh.filter(ImageFilter.GaussianBlur(8)), (ix - 9, iy - 7), sh.filter(ImageFilter.GaussianBlur(8)))
    P.paste(im, (ix, iy))
    tx = ix + iw + 34
    dr.text((tx, y0 + 40), f'{n:02d}' if n else '00', font=f(34), fill=ACC)
    avail = x0 + cw - tx - 22; fs = 66
    while dr.textlength(zh, font=f(fs)) > avail: fs -= 2
    dr.text((tx, y0 + 95 + (66 - fs) // 2), zh, font=f(fs), fill=INK, stroke_width=1, stroke_fill=INK)
    fe = 26
    while dr.textlength(en, font=f(fe)) > avail: fe -= 1
    dr.text((tx, y0 + 185), en, font=f(fe), fill=SUB)
    dr.text((tx, y0 + 230), yrs, font=f(30), fill=SUB)
    dr.rounded_rectangle((tx, y0 + 300, tx + dr.textlength(mov, font=f(30)) + 30, y0 + 350), 24, fill=ACC)
    dr.text((tx + 15, y0 + 325), mov, font=f(30), fill=(255, 248, 240), anchor='lm')
    # wrap note
    s, line, yy = note, '', y0 + 395
    for chh in s:
        if dr.textlength(line + chh, font=f(30)) > cw - (tx - x0) - 24: dr.text((tx, yy), line, font=f(30), fill=INK); yy += 44; line = ''
        line += chh
    dr.text((tx, yy), line, font=f(30), fill=INK)
dr.text((W // 2, H - 70), '按画家出生年份排序', font=f(32), fill=SUB, anchor='mm')
P.save(f'{d}/poster_s2.png'); P.save(f'{d}/poster_s2.jpg', quality=92)
P.resize((900, 1200)).save(f'{d}/poster_s2_small.png')
