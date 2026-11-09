"""15 s vertical video (720x1280, 30 fps): 12 paintings x 1.0 s + closing poster 3 s (no separate line-art page; Van Gogh opens).
usage: video_lotus.py paintings_dir font.ttf music.wav out.mp4"""
import sys, subprocess
from PIL import Image, ImageDraw, ImageFont
pd, FONT, MUSIC, OUT = sys.argv[1:5]
f = lambda s: ImageFont.truetype(FONT, s)
W, H, FPS = 720, 1280, 30
BG, INK, SUB, ACC = (246, 241, 230), (40, 32, 28), (110, 98, 88), (176, 52, 74)
items = [  # file, 中文, English, years, one-line, movement  (shuffled: Van Gogh opens; abstract and figurative alternate)
 ('vangogh', '梵高', 'Vincent van Gogh', '1853–1890', '旋转的厚涂笔触', '后印象派'),
 ('matisse', '马蒂斯', 'Henri Matisse', '1869–1954', '大红底与蓝色藤蔓', '野兽派'),
 ('kandinsky', '康定斯基', 'Wassily Kandinsky', '1866–1944', '同心圆、棋盘与线', '抽象艺术'),
 ('monet', '莫奈', 'Claude Monet', '1840–1926', '睡莲池的光与水', '印象派'),
 ('magritte', '马格利特', 'René Magritte', '1898–1967', '“这不是一朵荷花”', '超现实主义'),
 ('mondrian', '蒙德里安', 'Piet Mondrian', '1872–1944', '红黄蓝色块与黑线', '风格派'),
 ('klimt', '克里姆特', 'Gustav Klimt', '1862–1918', '金箔、螺旋与马赛克', '维也纳分离派'),
 ('schiele', '席勒', 'Egon Schiele', '1890–1918', '神经质的线与淡彩', '表现主义'),
 ('pollock', '波洛克', 'Jackson Pollock', '1912–1956', '层叠泼洒的线条', '抽象表现主义'),
 ('picasso', '毕加索', 'Pablo Picasso', '1881–1973', '把画面打碎再拼起', '立体主义'),
 ('munch', '蒙克', 'Edvard Munch', '1863–1944', '《呐喊》式天空波浪', '表现主义'),
 ('lichtenstein', '利希滕斯坦', 'Roy Lichtenstein', '1923–1997', '漫画网点与粗黑线', '波普艺术'),
]
imgs = [Image.open(f'{pd}/lotus_{it[0]}.png').convert('RGB') for it in items]
IW, IH, IY = 600, 800, 150
ease = lambda a: 1 - (1 - min(max(a, 0), 1)) ** 3

def header(dr, right):
    x0 = (W - IW) // 2
    dr.text((x0, 78), '荷花', font=f(44), fill=INK, anchor='lm', stroke_width=1, stroke_fill=INK)
    dr.rounded_rectangle((x0 + 100, 58, x0 + 140, 98), 6, fill=ACC); dr.text((x0 + 120, 78), '荷', font=f(28), fill=(255, 248, 240), anchor='mm')   # red seal
    dr.text((x0 + IW, 78), right, font=f(36), fill=ACC, anchor='rm')

def card(i, t):                         # t in 0..1 inside the card
    zh, en, yrs, note = items[i][1], items[i][2], items[i][3], items[i][4]
    P = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(P); header(dr, f'{i + 1:02d} / 12')
    zoom = 1.0 + 0.07 * t; src = imgs[i]; sw, sh = src.size; cw, ch = sw / zoom, sh / zoom
    crop = src.crop(((sw - cw) / 2, (sh - ch) / 2, (sw + cw) / 2, (sh + ch) / 2)).resize((IW, IH), Image.LANCZOS)
    x0 = (W - IW) // 2
    dr.rectangle((x0 + 8, IY + 10, x0 + IW + 8, IY + IH + 10), fill=(220, 210, 194)); P.paste(crop, (x0, IY))
    a = ease(t / 0.3); dx = int((1 - a) * 60); y = IY + IH + 60
    tx = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); td = ImageDraw.Draw(tx)
    td.text((x0 + dx, 40), zh, font=f(62), fill=INK + (255,), anchor='lm', stroke_width=1, stroke_fill=INK + (255,))
    td.text((x0 + dx, 100), en + '  ' + yrs, font=f(26), fill=SUB + (255,), anchor='lm')
    td.text((x0 + dx, 150), note, font=f(32), fill=INK + (255,), anchor='lm')
    if a < 1: tx.putalpha(tx.getchannel('A').point(lambda v: int(v * a)))
    P.paste(tx, (0, y - 40), tx)
    return P

PW, PH, S = 720, 960, 2                      # poster 3:4, drawn at 2x then downsampled
def build_poster():
    P = Image.new('RGB', (PW * S, PH * S), (245, 240, 229)); dr = ImageDraw.Draw(P)
    g = lambda v: int(v * S)
    ff = lambda sz: ImageFont.truetype(FONT, g(sz))
    # faint line-art watermark in both top corners
    wm = Image.open(f'{pd}/../../lineart/base_plain.png').convert('L').resize((g(230), g(307)), Image.LANCZOS)
    wm = wm.point(lambda v: 255 - int((255 - v) * 0.32)); 
    for (x, y, flip) in [(-10, 8, False), (PW - 220, 8, True)]:
        w = wm.transpose(Image.FLIP_LEFT_RIGHT) if flip else wm
        P.paste(Image.merge('RGB', (w, w, w)), (g(x), g(y)), Image.eval(w, lambda v: 255 - v))
    cx = PW // 2
    dr.text((g(cx - 14), g(62)), '荷  花', font=ff(76), fill=INK, anchor='mm', stroke_width=g(1.2), stroke_fill=INK)
    sx, sy = cx + 112, 28                                              # seal: red square, white characters (白文)
    dr.rounded_rectangle((g(sx), g(sy), g(sx + 58), g(sy + 58)), g(5), fill=ACC)
    for k, ch in enumerate('出水芙蓉'):
        dr.text((g(sx + 15 + (1 - k // 2) * 28), g(sy + 15 + (k % 2) * 28)), ch, font=ff(25), fill=(255, 248, 240), anchor='mm')
    dr.text((g(cx), g(122)), '十二位西方现代绘画大师 · 同一张线稿', font=ff(23), fill=INK, anchor='mm')
    for (x0, x1) in [(70, 150), (PW - 150, PW - 70)]:
        dr.line((g(x0), g(122), g(x1), g(122)), fill=ACC, width=g(1.5))
    dr.text((g(cx), g(150)), 'LOTUS · TWELVE MASTERS OF MODERN ART', font=ff(11), fill=SUB, anchor='mm')
    CW, CH, GX, GY = 215, 170, 10, 10; X0 = (PW - 3 * CW - 2 * GX) // 2; Y0 = 178
    for k, it in enumerate(items):
        c, r = k % 3, k // 3; x, y = X0 + c * (CW + GX), Y0 + r * (CH + GY)
        dr.rounded_rectangle((g(x + 2), g(y + 3), g(x + CW + 2), g(y + CH + 3)), g(8), fill=(228, 220, 205))       # soft shadow
        dr.rounded_rectangle((g(x), g(y), g(x + CW), g(y + CH)), g(8), fill=(252, 249, 243))
        th = imgs[k].resize((g(104), g(139)), Image.LANCZOS); P.paste(th, (g(x + 8), g(y + 15)))
        tx = x + 120
        dr.text((g(tx), g(y + 22)), f'{k + 1:02d}', font=ff(11), fill=ACC, anchor='lm')
        dr.text((g(tx), g(y + 46)), it[1], font=ff(21 if len(it[1]) < 5 else 18), fill=INK, anchor='lm', stroke_width=g(0.5), stroke_fill=INK)
        dr.text((g(tx), g(y + 66)), it[2], font=ff(8.5), fill=SUB, anchor='lm')
        dr.text((g(tx), g(y + 79)), it[3], font=ff(8.5), fill=SUB, anchor='lm')
        mv = it[5]; tw = dr.textlength(mv, font=ff(10)) / S + 14
        dr.rounded_rectangle((g(tx), g(y + 92), g(tx + tw), g(y + 108)), g(8), fill=ACC)
        dr.text((g(tx + tw / 2), g(y + 100)), mv, font=ff(10), fill=(255, 248, 240), anchor='mm')
        note = it[4]; h = (len(note) + 1) // 2; n1, n2 = (note[:h], note[h:]) if len(note) > 5 else (note, '')
        dr.text((g(tx), g(y + 123)), n1, font=ff(10.5), fill=INK, anchor='lm')
        if n2: dr.text((g(tx), g(y + 139)), n2, font=ff(10.5), fill=INK, anchor='lm')
    return P.resize((PW, PH), Image.LANCZOS)
POSTER = build_poster()
try:
    emo = Image.new('RGBA', (136, 128), (0, 0, 0, 0)); ImageDraw.Draw(emo).text((0, 0), '\U0001F60D', font=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109), embedded_color=True)
    EMO = emo.resize((72, 68), Image.LANCZOS)
except Exception: EMO = None
def outro(t):                           # t in 0..1: poster fades/scales in, then the question pops in
    P = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(P)
    a = ease(t / 0.18); sc = 0.94 + 0.06 * a
    po = POSTER.resize((int(PW * sc), int(PH * sc)), Image.LANCZOS); po = Image.blend(Image.new('RGB', po.size, BG), po, a)
    P.paste(po, ((W - po.width) // 2, 110 + (PH - po.height) // 2))
    b = ease((t - 0.3) / 0.15)
    if b > 0:
        q = Image.new('RGBA', (W, 130), (0, 0, 0, 0)); qd = ImageDraw.Draw(q)
        txt = '谁是你的最爱'; tw = qd.textlength(txt, font=f(62))
        x0 = (W - tw - (84 if EMO else 0)) / 2
        qd.text((x0, 65), txt, font=f(62), fill=INK + (255,), anchor='lm', stroke_width=1, stroke_fill=INK + (255,))
        if EMO: q.paste(EMO, (int(x0 + tw + 12), 31), EMO)
        q.putalpha(q.getchannel('A').point(lambda v: int(v * b))); P.paste(q, (0, 1100 + int((1 - b) * 30)), q)
    return P
if len(sys.argv) > 5: POSTER.save(sys.argv[5])

p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-i', MUSIC, '-t', '15', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-b:a', '160k', '-shortest', OUT], stdin=subprocess.PIPE)
for fr in range(15 * FPS):
    t = fr / FPS
    D = 1.0
    if t < 12 * D: i = int(t / D); im = card(min(i, 11), (t - i * D) / D)
    else: im = outro((t - 12 * D) / (15 - 12 * D))
    p.stdin.write(im.tobytes())
p.stdin.close(); p.wait(); print('saved', OUT)
