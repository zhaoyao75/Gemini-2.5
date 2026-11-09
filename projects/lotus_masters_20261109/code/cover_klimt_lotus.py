"""Single-painting Douyin cover (1080x1440): black ground, big white + yellow hook, pill with the style name, glowing painting.
usage: cover_klimt_lotus.py painting.png out.png [line1 line2 pill]"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
src, out = sys.argv[1:3]
l1, l2, pill = (sys.argv[3:6] + ['金色荷花', '这样画?', '克里姆特风'][len(sys.argv[3:6]):]) if len(sys.argv) > 3 else ('金色荷花', '这样画?', '克里姆特风')
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
f = lambda s: ImageFont.truetype(FONT, s)
W, H = 1080, 1440
P = Image.new('RGB', (W, H), (0, 0, 0))
# painting, feathered into the black ground with an elliptical mask, plus a warm halo behind it
ph = 880; pw = int(ph * 1086 / 1448)
art = Image.open(src).convert('RGB').resize((pw, ph), Image.LANCZOS)
ox, oy = (W - pw) // 2, H - ph
halo = Image.new('L', (W, H), 0); ImageDraw.Draw(halo).ellipse((ox - 120, oy - 20, ox + pw + 120, oy + ph + 60), fill=150)
halo = halo.filter(ImageFilter.GaussianBlur(90))
P.paste(Image.new('RGB', (W, H), (214, 150, 20)), (0, 0), halo)
mask = Image.new('L', (pw, ph), 0); ImageDraw.Draw(mask).rounded_rectangle((26, 26, pw - 26, ph - 26), 90, fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(26))
P.paste(art, (ox, oy), mask)
# two small glowing lights at the foot, like the reference
glow = Image.new('RGB', (W, H), (0, 0, 0)); gd = ImageDraw.Draw(glow)
for (x, y) in [(300, 1368), (780, 1368)]: gd.ellipse((x - 16, y - 8, x + 16, y + 8), fill=(255, 190, 60))
big = glow.filter(ImageFilter.GaussianBlur(26)); P = ImageChops.add(P, big); P = ImageChops.add(P, glow.filter(ImageFilter.GaussianBlur(5)))
dr = ImageDraw.Draw(P)
def heavy(xy, text, size, fill):                                   # faux-bold: the font is regular weight, so stroke it
    dr.text(xy, text, font=f(size), fill=fill, anchor='mm', stroke_width=max(3, size // 22), stroke_fill=fill)
heavy((W // 2, 128), l1, 176, (255, 255, 255))
heavy((W // 2, 308), l2, 196, (255, 236, 0))
fp = f(78); tw = dr.textlength(pill, font=fp) + 44
bx0, bx1 = W // 2 - tw / 2 - 70, W // 2 + tw / 2 + 70
dr.rounded_rectangle((bx0, 430, bx1, 530), 50, fill=(0, 0, 0), outline=(255, 255, 255), width=5)
dr.text((W // 2, 481), pill, font=fp, fill=(255, 255, 255), anchor='mm', stroke_width=2, stroke_fill=(255, 255, 255))
P.save(out)
