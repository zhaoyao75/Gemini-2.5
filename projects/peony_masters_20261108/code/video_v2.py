"""Season-1 peony video, re-cut to the user's script (hook first, rule, fast cuts, Pollock, payoff, CTA)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
d, out = sys.argv[1], sys.argv[2]
F = '/tmp/claude-0/-home-user-Gemini-2-5/c96cf704-d013-5c2a-be1f-2857f80af15a/scratchpad/fonts/LXGWWenKai-Regular.ttf'
f = lambda s: ImageFont.truetype(F, s)
W, H, FPS = 720, 1280, 30
WHITE, GOLD, INK, ACC = (255, 255, 255), (255, 214, 102), (20, 16, 14), (232, 52, 80)
IMG = lambda n: Image.open(f'{d}/{n}.png').convert('RGB')
AW, AH, AY = 720, 960, 170                      # artwork frame inside the 9:16 canvas

# ---------------- timeline (seconds) ----------------
QUICK = [('peony_cezanne', '塞尚', '斜笔触'), ('peony_monet', '莫奈', '碎笔光色'), ('peony_klimt', '克里姆特', '金箔螺旋'),
         ('peony_munch', '蒙克', '起伏色带'), ('peony_kandinsky', '康定斯基', '几何线条'), ('peony_matisse', '马蒂斯', '纯色平涂'),
         ('peony_mondrian', '蒙德里安', '色块黑线'), ('peony_picasso', '毕加索', '多面碎块'), ('peony_dali', '达利', '软质变形')]
T_HOOK, T_RULE, T_Q, T_POL, T_PAY, T_CTA = 2.4, 3.4, 1.0, 3.2, 3.0, 3.0
t0 = 0; SEG = []
SEG.append(('hook', t0, t0 + T_HOOK)); t0 += T_HOOK
SEG.append(('rule', t0, t0 + T_RULE)); t0 += T_RULE
for i in range(len(QUICK)): SEG.append((f'q{i}', t0, t0 + T_Q)); t0 += T_Q
SEG.append(('pollock', t0, t0 + T_POL)); t0 += T_POL
SEG.append(('payoff', t0, t0 + T_PAY)); t0 += T_PAY
SEG.append(('cta', t0, t0 + T_CTA)); t0 += T_CTA
TOTAL = t0
# voice-over lines (also burnt in as subtitles) -> (start, end, text)
VO = [(0.15, T_HOOK - 0.1, '当牡丹撞上梵高的画风'),
      (T_HOOK + 0.1, T_HOOK + T_RULE - 0.1, '其实这十一款牡丹，用的是同一张线稿')]
pol0 = [s for s in SEG if s[0] == 'pollock'][0][1]; pay0 = pol0 + T_POL; cta0 = pay0 + T_PAY
VO += [(pol0 + 0.1, pay0 - 0.1, '最后这版泼墨感的，是波洛克的风格'),
       (pay0 + 0.1, cta0 - 0.1, '同一朵牡丹，十一种看见'),
       (cta0 + 0.1, TOTAL - 0.2, '你最喜欢哪一种风格，打在评论区告诉我')]

# ---------------- helpers ----------------
cache = {}
def art(name, zoom=1.0):
    if name not in cache:
        im = IMG(name)
        bg = im.resize((W, int(W * im.height / im.width))).resize((W, H)).filter(ImageFilter.GaussianBlur(28))
        cache[name] = (im, ImageEnhance.Brightness(bg).enhance(0.45))
    im, bg = cache[name]
    sw, sh = im.size; cw, ch = sw / zoom, sh / zoom
    a = im.crop(((sw - cw) / 2, (sh - ch) / 2, (sw + cw) / 2, (sh + ch) / 2)).resize((AW, AH), Image.LANCZOS)
    P = bg.copy(); P.paste(a, (0, AY)); return P
def outline_text(dr, xy, s, size, fill, stroke=(0, 0, 0), sw=4, anchor='mm'):
    dr.text(xy, s, font=f(size), fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=stroke)
def fit(dr, s, size, maxw):
    while dr.textlength(s, font=f(size)) > maxw: size -= 2
    return size
def tag(dr, cy, name, kw, a=1.0):           # "梵高 · 厚涂铬黄" title band at the top
    s = f'{name} · {kw}'; sz = fit(dr, s, 64, W - 80)
    outline_text(dr, (W // 2, cy), s, sz, GOLD, sw=5)
def subtitle(P, t):
    for s, e, txt in VO:
        if s <= t < e:
            dr = ImageDraw.Draw(P); sz = fit(dr, txt, 46, W - 60)
            yy = AY + AH + 62 if not any(k[0] in ('payoff', 'cta') and k[1] <= t < k[2] for k in SEG) else 1236
            outline_text(dr, (W // 2, yy), txt, sz, WHITE, sw=5)
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3

# ---------------- scenes ----------------
thumbs = None
ALL11 = ['peony_cezanne', 'peony_monet', 'peony_lineart_vangogh', 'peony_klimt', 'peony_munch', 'peony_kandinsky',
         'peony_matisse', 'peony_mondrian', 'peony_picasso', 'peony_dali', 'peony_pollock', 'base']
NAMES = '塞尚  莫奈  梵高  克里姆特  蒙克  康定斯基\n马蒂斯  蒙德里安  毕加索  达利  波洛克'
def grid(p):                               # 11 works + the line art, popping in
    global thumbs
    TW, TH, G = 162, 216, 8
    if thumbs is None: thumbs = [IMG(n).resize((TW, TH), Image.LANCZOS) for n in ALL11]
    P = Image.new('RGB', (W, H), (24, 18, 16)); x0, y0 = (W - 3 * TW - 2 * G) // 2, 140
    for k, th in enumerate(thumbs):
        a = ease((p - k * 0.04) / 0.25)
        if a <= 0: continue
        w, h = int(TW * (0.7 + 0.3 * a)), int(TH * (0.7 + 0.3 * a)); c, r = k % 3, k // 3
        cx, cy = x0 + c * (TW + G) + TW // 2, y0 + r * (TH + G) + TH // 2
        P.paste(Image.blend(Image.new('RGB', (w, h), (24, 18, 16)), th.resize((w, h)), a), (cx - w // 2, cy - h // 2))
    return P

def frame(t):
    seg = next(s for s in SEG if s[1] <= t < s[2]) if t < TOTAL else SEG[-1]
    kind, s0, s1 = seg; p = (t - s0) / (s1 - s0)
    if kind == 'hook':                     # full-screen Van Gogh, slow punch-in
        P = art('peony_lineart_vangogh', 1.0 + 0.08 * p); dr = ImageDraw.Draw(P)
        tag(dr, 92, '梵高', '厚涂铬黄')
    elif kind == 'rule':                   # back to the clean line art, the rule appears
        P = Image.new('RGB', (W, H), (246, 241, 230)); a = IMG('base').resize((AW, AH), Image.LANCZOS); P.paste(a, (0, AY))
        dr = ImageDraw.Draw(P); al = ease((t - s0) / 0.4)
        box = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        bd.rounded_rectangle((50, AY + AH // 2 - 120, W - 50, AY + AH // 2 + 120), 26, fill=(255, 250, 240, int(235 * al)))
        P = Image.alpha_composite(P.convert('RGBA'), box).convert('RGB'); dr = ImageDraw.Draw(P)
        if al > 0.05:
            col = tuple(int(255 + (c - 255) * al) for c in INK)
            dr.text((W // 2, AY + AH // 2 - 45), '同一张牡丹线稿', font=f(58), fill=col, anchor='mm', stroke_width=1, stroke_fill=col)
            dr.text((W // 2, AY + AH // 2 + 45), '十一位大师风格', font=f(58), fill=tuple(int(255 + (c - 255) * al) for c in ACC), anchor='mm', stroke_width=1, stroke_fill=tuple(int(255 + (c - 255) * al) for c in ACC))
    elif kind.startswith('q'):             # 1-second fast cuts
        i = int(kind[1:]); n, name, kw = QUICK[i]
        P = art(n, 1.0 + 0.05 * p); dr = ImageDraw.Draw(P); tag(dr, 92, name, kw)
        dr.text((W - 40, AY + 34), f'{i + 1:02d}/11', font=f(30), fill=WHITE, anchor='rm', stroke_width=3, stroke_fill=(0, 0, 0))
    elif kind == 'pollock':                # Pollock, held longer, slow pull-back
        P = art('peony_pollock', 1.12 - 0.12 * p); dr = ImageDraw.Draw(P); tag(dr, 92, '波洛克', '层叠滴洒')
        dr.text((W - 40, AY + 34), '11/11', font=f(30), fill=WHITE, anchor='rm', stroke_width=3, stroke_fill=(0, 0, 0))
    elif kind == 'payoff':                 # all eleven + the line art, names roll in
        P = grid(p); dr = ImageDraw.Draw(P)
        outline_text(dr, (W // 2, 92), '同一朵牡丹，十一种看见', 54, GOLD, sw=4)
        a = ease((p - 0.35) / 0.4)
        if a > 0:
            box = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
            P = Image.alpha_composite(P.convert('RGBA'), box).convert('RGB'); dr = ImageDraw.Draw(P)
            for k, line in enumerate(NAMES.split('\n')):
                col = tuple(int(c * a) for c in WHITE)
                dr.text((W // 2, 1122 + k * 44), line, font=f(32), fill=col, anchor='mm')
    else:                                  # CTA freeze + hashtags
        P = grid(1.0); dr = ImageDraw.Draw(P)
        outline_text(dr, (W // 2, 92), '同一朵牡丹，十一种看见', 54, GOLD, sw=4)
        box = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        a = ease((t - s0) / 0.35)
        P = Image.alpha_composite(P.convert('RGBA'), box).convert('RGB'); dr = ImageDraw.Draw(P)
        s = '你最喜欢哪一种？评论区告诉我'
        dr.rounded_rectangle((W // 2 - 300, 1098, W // 2 + 300, 1162), 32, fill=ACC)
        dr.text((W // 2, 1130), s, font=f(fit(dr, s, 40, 560)), fill=WHITE, anchor='mm')
        dr.text((W // 2, 1210), '#国花十画  #AI绘画  #牡丹', font=f(34), fill=GOLD, anchor='mm')
        return P                            # CTA line is shown in the button, not repeated as a subtitle
    subtitle(P, t); return P

os.makedirs(f'{out}_frames', exist_ok=True)
N = int(round(TOTAL * FPS)); cuts = [s[1] for s in SEG[1:]]
for n in range(N):
    t = n / FPS; im = frame(t)
    for c in cuts:                          # short dissolve only into / out of the slower scenes; hard cuts in the fast run
        kinds = (next(s for s in SEG if s[2] == c)[0], next(s for s in SEG if s[1] == c)[0])
        if all(k.startswith('q') for k in kinds) or ('q' in kinds[1][:1]): continue
        if c <= t < c + 0.18: im = Image.blend(frame(c - 1e-3), im, (t - c) / 0.18)
    im.save(f'{out}_frames/f{n:04d}.png')
# SRT for CapCut / 剪映 text-to-speech
def ts(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f'{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}'
with open(f'{out}.srt', 'w', encoding='utf-8') as fp:
    for i, (s, e, txt) in enumerate(VO, 1): fp.write(f'{i}\n{ts(s)} --> {ts(e)}\n{txt}\n\n')
print('frames', N, 'duration', TOTAL)
