import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
d = sys.argv[1]
F = '/tmp/claude-0/-home-user-Gemini-2-5/c96cf704-d013-5c2a-be1f-2857f80af15a/scratchpad/fonts/LXGWWenKai-Regular.ttf'
f = lambda s: ImageFont.truetype(F, s)
W, H = 1080, 1440
WHITE, NAVY, PINK, SUN = (255, 255, 255), (16, 40, 96), (232, 48, 122), (255, 216, 42)
art = Image.open(f'{d}/peony_hockney.png').convert('RGB').resize((W, H), Image.LANCZOS)
SH = 110
P = Image.new('RGB', (W, H)); P.paste(art, (0, SH))
# extend the flat sky upwards (Hockney's sky is a flat blue anyway)
P.paste(Image.new('RGB', (W, SH), art.getpixel((W // 2, 4))), (0, 0))
dr = ImageDraw.Draw(P)
# a flat yellow sun behind the title, pop-flat like Hockney
dr.ellipse((W - 250, 40, W - 60, 230), fill=SUN)
# kicker
dr.text((W // 2, 66), '当牡丹遇见 · 霍克尼', font=f(40), fill=NAVY, anchor='mm')
# main title: white with a navy drop shadow (flat, poster-like)
T = '牡丹去了加州'
dr.text((W // 2 + 6, 186 + 7), T, font=f(146), fill=NAVY, anchor='mm', stroke_width=3, stroke_fill=NAVY)
dr.text((W // 2, 186), T, font=f(146), fill=WHITE, anchor='mm', stroke_width=3, stroke_fill=WHITE)
# hook band (pink, matching the peonies)
hook = '第二季 · 11位西方大师画牡丹'
fh = f(52); tw = dr.textlength(hook, font=fh)
dr.rounded_rectangle((W // 2 - tw / 2 - 34, 290, W // 2 + tw / 2 + 34, 362), 36, fill=PINK)
dr.text((W // 2, 326), hook, font=fh, fill=WHITE, anchor='mm', stroke_width=1, stroke_fill=WHITE)
# zhuwen seal from the poster
post = Image.open(f'{d}/poster_wenkai.png').convert('RGB')
seal = post.crop((1460, 80, 1680, 290)).resize((88, 84), Image.LANCZOS)
m = seal.convert('L').point(lambda v: 255 if v < 200 else 0)
P.paste(Image.new('RGB', seal.size, (200, 40, 50)), (40, 34), m)
# artist tag above the bottom UI zone
tag = 'David Hockney · 波普 / 当代'
ft = f(34); lw = dr.textlength(tag, font=ft) + 40
dr.rounded_rectangle((36, 1180, 36 + lw, 1236), 28, fill=NAVY)
dr.text((36 + lw / 2, 1208), tag, font=ft, fill=WHITE, anchor='mm')
P.save(f'{d}/douyin_cover_hockney.jpg', quality=93)
P.resize((540, 720)).save(f'{d}/cover_hockney_small.png')
# side-by-side with season 1 cover
a = Image.open(f'{d}/douyin_cover_klimt.jpg').resize((540, 720)); b = P.resize((540, 720))
s = Image.new('RGB', (1100, 720), (240, 236, 228)); s.paste(a, (0, 0)); s.paste(b, (560, 0)); s.save(f'{d}/covers_pair.jpg', quality=90)
