import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
d = sys.argv[1]
F = '/tmp/claude-0/-home-user-Gemini-2-5/c96cf704-d013-5c2a-be1f-2857f80af15a/scratchpad/fonts/LXGWWenKai-Regular.ttf'
f = lambda s: ImageFont.truetype(F, s)
W, H = 1080, 1440
GOLD, CREAM, ACC = (240, 206, 112), (255, 244, 220), (186, 38, 44)
art = Image.open(f'{d}/peony_klimt.png').convert('RGB').resize((W, H), Image.LANCZOS)
SH = 90
P = Image.new('RGB', (W, H)); P.paste(art, (0, SH))
P.paste(art.crop((0, 0, W, SH)).transpose(Image.FLIP_TOP_BOTTOM), (0, 0))   # extend the gold ground upwards
# top dark gradient for the title, light bottom vignette
a = np.zeros((H, W), np.float32)
yy = np.arange(H)[:, None]
a += (np.clip(1 - yy / 440, 0, 1) ** 1.4) * 215
a += (np.clip((yy - 1250) / 190, 0, 1) ** 1.6) * 120
P.paste(Image.new('RGB', (W, H), (22, 14, 8)), (0, 0), Image.fromarray(a.clip(0, 255).astype(np.uint8)))
dr = ImageDraw.Draw(P)
# small kicker
dr.text((W // 2, 62), '当牡丹遇见 · 克里姆特', font=f(40), fill=GOLD, anchor='mm')
# main title in gold with dark shadow
for off in [(4, 5)]:
    dr.text((W // 2 + off[0], 168 + off[1]), '金色牡丹', font=f(168), fill=(10, 6, 2), anchor='mm', stroke_width=4, stroke_fill=(10, 6, 2))
dr.text((W // 2, 168), '金色牡丹', font=f(168), fill=GOLD, anchor='mm', stroke_width=3, stroke_fill=(150, 104, 30))
# thin gold rules
dr.line((W // 2 - 380, 272, W // 2 + 380, 272), fill=GOLD, width=2)
# hook band
hook = '11位西方大师 画同一朵牡丹'
fh = f(54); tw = dr.textlength(hook, font=fh)
dr.rounded_rectangle((W // 2 - tw / 2 - 34, 290, W // 2 + tw / 2 + 34, 362), 16, fill=ACC)
dr.text((W // 2, 326), hook, font=fh, fill=CREAM, anchor='mm', stroke_width=1, stroke_fill=CREAM)
# seal (zhuwen, from the poster)
post = Image.open(f'{d}/poster_wenkai.png').convert('RGB')
seal = post.crop((1460, 80, 1680, 290)).resize((92, 88), Image.LANCZOS)
m = seal.convert('L').point(lambda v: 255 if v < 200 else 0)
P.paste(Image.new('RGB', seal.size, (210, 52, 52)), (W - 122, 30), m)
# artist tag above the mosaic table (kept clear of the app's bottom UI)
tag = 'Gustav Klimt · 维也纳分离派'
ft = f(34); lw = dr.textlength(tag, font=ft) + 40
dr.rounded_rectangle((36, 1220, 36 + lw, 1276), 28, fill=(20, 14, 8))
dr.text((36 + lw / 2, 1248), tag, font=ft, fill=GOLD, anchor='mm')
P.save(f'{d}/douyin_cover_klimt.jpg', quality=93)
P.resize((540, 720)).save(f'{d}/cover_klimt_small.png')
