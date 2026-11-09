"""15 s vertical video (720x1280, 30 fps): 12 paintings x 1.1 s + closing grid 1.8 s (no separate line-art page; Van Gogh opens).
usage: video_lotus.py paintings_dir font.ttf music.wav out.mp4"""
import sys, subprocess
from PIL import Image, ImageDraw, ImageFont
pd, FONT, MUSIC, OUT = sys.argv[1:5]
f = lambda s: ImageFont.truetype(FONT, s)
W, H, FPS = 720, 1280, 30
BG, INK, SUB, ACC = (246, 241, 230), (40, 32, 28), (110, 98, 88), (176, 52, 74)
items = [  # file, 中文, English, years, one-line  (Van Gogh opens; the rest by birth year)
 ('vangogh', '梵高', 'Vincent van Gogh', '1853–1890', '旋转的厚涂笔触'),
 ('monet', '莫奈', 'Claude Monet', '1840–1926', '睡莲池的光与水'),
 ('klimt', '克里姆特', 'Gustav Klimt', '1862–1918', '金箔、螺旋与马赛克'),
 ('munch', '蒙克', 'Edvard Munch', '1863–1944', '《呐喊》式的天空波浪'),
 ('matisse', '马蒂斯', 'Henri Matisse', '1869–1954', '大红底与蓝色藤蔓'),
 ('picasso', '毕加索', 'Pablo Picasso', '1881–1973', '把画面打碎再拼起'),
 ('schiele', '席勒', 'Egon Schiele', '1890–1918', '神经质的线与淡彩'),
 ('magritte', '马格利特', 'René Magritte', '1898–1967', '“这不是一朵荷花”'),
 ('dali', '达利', 'Salvador Dalí', '1904–1989', '融化的釉与梦中沙漠'),
 ('lichtenstein', '利希滕斯坦', 'Roy Lichtenstein', '1923–1997', '漫画网点与粗黑线'),
 ('warhol', '沃霍尔', 'Andy Warhol', '1928–1987', '四联荧光丝网印刷'),
 ('kusama_pumpkin', '草间弥生', 'Yayoi Kusama', '1929–', '南瓜黄与无尽波点'),
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

def outro(t):
    P = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(P)
    dr.text((W // 2, 80), '荷花 · 十二位大师 · 同一张线稿', font=f(40), fill=INK, anchor='mm', stroke_width=1, stroke_fill=INK)
    TW, TH, G = 200, 267, 10; x0, y0 = (W - 3 * TW - 2 * G) // 2, 150
    for k in range(12):
        c, r = k % 3, k // 3; tile = imgs[k].resize((TW, TH), Image.LANCZOS)
        a = ease((t - k * 0.03) / 0.2)
        tile = Image.blend(Image.new('RGB', (TW, TH), BG), tile, a); P.paste(tile, (x0 + c * (TW + G), y0 + r * (TH + G)))
    return P

p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-i', MUSIC, '-t', '15', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-b:a', '160k', '-shortest', OUT], stdin=subprocess.PIPE)
for fr in range(15 * FPS):
    t = fr / FPS
    D = 1.1
    if t < 12 * D: i = int(t / D); im = card(min(i, 11), (t - i * D) / D)
    else: im = outro((t - 12 * D) / (15 - 12 * D))
    p.stdin.write(im.tobytes())
p.stdin.close(); p.wait(); print('saved', OUT)
