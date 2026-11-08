import sys
from PIL import Image, ImageDraw, ImageFont
d = sys.argv[1]
F = '/tmp/claude-0/-home-user-Gemini-2-5/c96cf704-d013-5c2a-be1f-2857f80af15a/scratchpad/fonts/LXGWWenKai-Regular.ttf'
f = lambda s: ImageFont.truetype(F, s)
W, H = 1080, 1440
BLK, WHT, YEL, RED = (17, 17, 17), (255, 255, 255), (255, 212, 0), (226, 0, 26)
art = Image.open(f'{d}/peony_kusama.png').convert('RGB').resize((W, H), Image.LANCZOS)
SH = 120
P = Image.new('RGB', (W, H)); P.paste(art, (0, SH))
P.paste(art.crop((0, 0, W, SH)), (0, 0))          # the dot pattern simply continues upwards
dr = ImageDraw.Draw(P)
# kicker in a black pill
k = '当牡丹遇见 · 草间弥生'
fk = f(40); kw = dr.textlength(k, font=fk)
dr.rounded_rectangle((W // 2 - kw / 2 - 30, 30, W // 2 + kw / 2 + 30, 92), 31, fill=BLK)
dr.text((W // 2, 61), k, font=fk, fill=WHT, anchor='mm')
# main title: yellow with a heavy black outline, like her pumpkins
T = '波点牡丹'
dr.text((W // 2 + 8, 198 + 9), T, font=f(176), fill=BLK, anchor='mm', stroke_width=14, stroke_fill=BLK)
dr.text((W // 2, 198), T, font=f(176), fill=YEL, anchor='mm', stroke_width=12, stroke_fill=BLK)
# black dots sprinkled on the yellow letters
import numpy as np
mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).text((W // 2, 198), T, font=f(176), fill=255, anchor='mm')
dots = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(dots)
for y in range(100, 300, 26):
    for x in range((y // 26) % 2 * 13, W, 26): dd.ellipse((x - 5, y - 5, x + 5, y + 5), fill=255)
m = np.minimum(np.asarray(mask), np.asarray(dots)); P.paste(Image.new('RGB', (W, H), BLK), (0, 0), Image.fromarray(m))
dr = ImageDraw.Draw(P)
# hook band
hook = '第二季 · 11位西方大师画牡丹'
fh = f(50); tw = dr.textlength(hook, font=fh)
dr.rounded_rectangle((W // 2 - tw / 2 - 34, 318, W // 2 + tw / 2 + 34, 388), 35, fill=BLK)
dr.text((W // 2, 353), hook, font=fh, fill=YEL, anchor='mm', stroke_width=1, stroke_fill=YEL)
# zhuwen seal (white ground behind so it reads on the red dots)
post = Image.open(f'{d}/poster_wenkai.png').convert('RGB')
seal = post.crop((1460, 80, 1680, 290)).resize((96, 92), Image.LANCZOS)
dr.rounded_rectangle((W - 136, 120, W - 30, 222), 10, fill=(250, 244, 232))
P.paste(seal, (W - 131, 125), seal.convert('L').point(lambda v: 255 if v < 200 else 0))
# artist tag
tag = 'Yayoi Kusama · 当代艺术'
ft = f(34); lw = dr.textlength(tag, font=ft) + 40
dr.rounded_rectangle((36, 1180, 36 + lw, 1236), 28, fill=BLK)
dr.text((36 + lw / 2, 1208), tag, font=ft, fill=WHT, anchor='mm')
P.save(f'{d}/douyin_cover_kusama.jpg', quality=93)
P.resize((540, 720)).save(f'{d}/cover_kusama_small.png')
