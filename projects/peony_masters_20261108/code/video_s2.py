import sys, os
from PIL import Image, ImageDraw, ImageFont
d, out = sys.argv[1], sys.argv[2]
F = '/tmp/claude-0/-home-user-Gemini-2-5/c96cf704-d013-5c2a-be1f-2857f80af15a/scratchpad/fonts/LXGWWenKai-Regular.ttf'
f = lambda s: ImageFont.truetype(F, s)
W, H, FPS = 720, 1280, 30
BG, INK, SUB, ACC = (246, 241, 230), (40, 32, 28), (110, 98, 88), (168, 48, 70)
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
IW, IH, IY = 600, 800, 150
imgs = [Image.open(f'{d}/{it[0]}').convert('RGB') for it in items]

def card(i, zoom):
    zh, en, yrs, mov, note = items[i][1:]
    P = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(P)
    # corner mark: 牡丹 + seal (left), progress (right)
    dr.text((x0_ := (W - IW) // 2, 78), '牡丹', font=f(44), fill=INK, anchor='lm', stroke_width=1, stroke_fill=INK)
    P.paste(SEAL_S, (x0_ + 100, 56), SEALM_S)
    tot = len(items) - 1
    if i == 0: prog = '线稿'
    else: prog = f'{i:02d} / {tot:02d}'
    dr.text((x0_ + IW, 78), prog, font=f(36), fill=ACC if i else SUB, anchor='rm')
    src = imgs[i]; sw, sh = src.size; cw, chh = sw / zoom, sh / zoom
    crop = src.crop(((sw - cw) / 2, (sh - chh) / 2, (sw + cw) / 2, (sh + chh) / 2)).resize((IW, IH), Image.LANCZOS)
    x0 = (W - IW) // 2
    dr.rectangle((x0 + 8, IY + 10, x0 + IW + 8, IY + IH + 10), fill=(220, 210, 194))
    P.paste(crop, (x0, IY))
    y = IY + IH + 60
    dr.text((x0, y), f'{i:02d}', font=f(30), fill=ACC, anchor='lm')
    dr.text((x0 + 60, y), zh, font=f(62), fill=INK, anchor='lm', stroke_width=1, stroke_fill=INK)
    tw = dr.textlength(mov, font=f(26)) + 30
    dr.rounded_rectangle((x0 + IW - tw, y - 22, x0 + IW, y + 22), 22, fill=ACC)
    dr.text((x0 + IW - tw / 2, y), mov, font=f(26), fill=(255, 248, 240), anchor='mm')
    dr.text((x0 + 60, y + 62), en + ('  ' + yrs if yrs else ''), font=f(26), fill=SUB, anchor='lm')
    dr.text((x0 + 60, y + 112), note, font=f(32), fill=INK, anchor='lm')
    return P

thumbs = None
_sc = Image.open(f'{d}/seal_crop.png').convert('RGB').resize((70, 67), Image.LANCZOS)
SEALM = _sc.convert('L').point(lambda v: 255 if v < 200 else 0).filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(0.5))
SEAL = _sc
SEAL_S = _sc.resize((46, 44), Image.LANCZOS); SEALM_S = SEALM.resize((46, 44), Image.LANCZOS)
def title(t):
    global thumbs
    TW, TH, G = 200, 267, 10
    if thumbs is None: thumbs = [im.resize((TW, TH), Image.LANCZOS) for im in imgs]
    P = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(P)
    dr.text((W // 2 - 70, 66), '牡', font=f(76), fill=INK, anchor='mm', stroke_width=1, stroke_fill=INK)
    dr.text((W // 2 + 30, 66), '丹', font=f(76), fill=INK, anchor='mm', stroke_width=1, stroke_fill=INK)
    P.paste(SEAL, (W // 2 + 90, 30), SEALM)
    dr.text((W // 2, 126), '第二季 · 十一位西方艺术家 · 同一张线稿', font=f(26), fill=SUB, anchor='mm')
    x0, y0 = (W - 3 * TW - 2 * G) // 2, 150
    for k in range(12):
        a = (t - k * 0.08) / 0.15                      # each tile pops in, one after another
        if a <= 0: continue
        a = min(1, a); s_ = 0.6 + 0.4 * (1 - (1 - a) ** 3)
        c, r = k % 3, k // 3
        w, h = int(TW * s_), int(TH * s_)
        cx, cy = x0 + c * (TW + G) + TW // 2, y0 + r * (TH + G) + TH // 2
        tile = thumbs[k].resize((w, h))
        if a < 1: tile = Image.blend(Image.new('RGB', (w, h), BG), tile, a)
        P.paste(tile, (cx - w // 2, cy - h // 2))
    return P

poster = Image.open(f'{d}/poster_s2.jpg').convert('RGB')
def outro(t):
    P = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(P)
    pw = 640; ph = int(pw * 4 / 3); P.paste(poster.resize((pw, ph), Image.LANCZOS), ((W - pw) // 2, 140))
    dr.text((W // 2, 140 + ph + 90), '第二季 · 同一朵牡丹，十一种看见', font=f(44), fill=INK, anchor='mm')
    return P

frames = []
T_TITLE, T_ITEM, T_OUT, XF = 1.5, 1.0, 1.5, 0.2
total = T_TITLE + T_ITEM * len(items) + T_OUT
os.makedirs(f'{out}_frames', exist_ok=True)
def scene_at(t):
    if t < T_TITLE: return title(t)
    t2 = t - T_TITLE
    if t2 < T_ITEM * len(items): i = int(t2 // T_ITEM); return card(i, 1.0 + 0.05 * (t2 - i * T_ITEM) / T_ITEM)
    return outro(t2 - T_ITEM * len(items))
bounds = [T_TITLE + k * T_ITEM for k in range(len(items) + 1)]
for n in range(int(total * FPS)):
    t = n / FPS
    im = scene_at(t)
    for b in bounds:                      # crossfade around each cut
        if b - XF / 2 <= t < b + XF / 2 and t >= b:
            prev = scene_at(b - 1e-3); a = (t - b) / (XF / 2)
            im = Image.blend(prev, im, min(1, 0.5 + a / 2))
        elif b - XF / 2 <= t < b:
            nxt = scene_at(b + 1e-3); a = (t - (b - XF / 2)) / (XF / 2)
            im = Image.blend(im, nxt, a / 2)
    im.save(f'{out}_frames/f{n:04d}.png')
print('frames', n + 1, 'duration', total)
