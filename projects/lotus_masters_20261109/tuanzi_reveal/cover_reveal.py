from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
F='fonts/ZCOOLKuaiLe-Regular.ttf'; f=lambda s:ImageFont.truetype(F,s)
W,H=1080,1440; INK=(59,32,64)
base=Image.open('p2/mondrian.jpg').convert('RGBA')
over=base.copy(); over.alpha_composite(Image.open('halo.png')); over.alpha_composite(Image.open('lines.png'))
# diagonal reveal: lineart version on the lower-right side of a line from (0,700) to (1080,330)
yy,xx=np.mgrid[0:H,0:W]; edge=700-(xx/W)*370
m=np.clip((yy-edge)/3,0,1)
mask=Image.fromarray((m*255).astype(np.uint8))
P=Image.composite(over,base,mask).convert('RGB')
d=ImageDraw.Draw(P)
d.line([(0,700),(W,330)],fill=(255,224,74),width=12); d.line([(0,700),(W,330)],fill=(255,255,255),width=4)
for (t,x,y,col) in [('看不懂?',90,610,(255,255,255)),('是荷花!',690,880,(255,224,74))]:
    pass
def heavy(xy,text,size,fill,anchor='mm'):
    d.text(xy,text,font=f(size),fill=fill,anchor=anchor,stroke_width=max(10,size//8),stroke_fill=INK)
heavy((W//2,130),'看不懂的画?',150,(255,255,255))
heavy((W//2,300),'其实都是荷花',138,(255,224,74))
# series tag
tw=d.textlength('团子猫日常 · 特别篇',font=f(38))+60
d.rounded_rectangle((W//2-tw/2,400,W//2+tw/2,468),34,fill=(255,213,102),outline=INK,width=6)
d.text((W//2,434),'团子猫日常 · 特别篇',font=f(38),fill=INK,anchor='mm')
# before / after tags
for (t,x,y) in [('原画',60,520),('叠上线稿',700,830)]:
    w=d.textlength(t,font=f(40))+40; d.rounded_rectangle((x,y,x+w,y+64),20,fill=(255,243,220),outline=INK,width=5); d.text((x+w/2,y+32),t,font=f(40),fill=INK,anchor='mm')
# cat, shocked, big, bottom-left, overlapping the artwork
cat=Image.open('sprites/dot_w.png').convert('RGBA'); cat=cat.crop(cat.getbbox()); k=0.98; cat=cat.resize((int(cat.width*k),int(cat.height*k)),Image.LANCZOS)
sh=Image.new('RGBA',cat.size,(0,0,0,0)); P=P.convert('RGBA'); P.alpha_composite(cat,(-20,H-cat.height+20)); P=P.convert('RGB')
d=ImageDraw.Draw(P)
heavy((800,1290),'……是荷花?',76,(255,255,255))
P.save('/tmp/claude-0/cat2/cover_reveal.png')
print(cat.size)
