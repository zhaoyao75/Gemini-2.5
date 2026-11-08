"""Shot 1 demo (5s): particles converge -> flash + ring -> "道" ink reveal -> scripture fades in.

Usage: python3 render_demo.py   (writes demo_5s.mp4 next to this file)
"""
import os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1920, 1080, 30, 5.0
N = int(FPS * DUR)
CX, CY = W // 2, int(H * 0.42)
FRAMES = os.path.join(HERE, "frames")
os.makedirs(FRAMES, exist_ok=True)

IVORY = np.array([237, 230, 214], np.float32) / 255
GOLD = np.array([200, 168, 106], np.float32) / 255
GREY = np.array([120, 118, 112], np.float32) / 255
rng = np.random.default_rng(7)


def ease_in_out(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def blur(a, r):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


def text_mask(text, font, size, pos, spacing=0):
    """Render text to a float mask; returns list of per-char masks when spacing given."""
    f = ImageFont.truetype(font, size)
    img = Image.new("L", (W, H), 0)
    ImageDraw.Draw(img).text(pos, text, font=f, fill=255, anchor="mm")
    return np.asarray(img, np.float32) / 255


def char_masks(text, font, size, cy, spacing):
    f = ImageFont.truetype(font, size)
    step = size + spacing
    x0 = W / 2 - step * (len(text) - 1) / 2
    out = []
    for i, ch in enumerate(text):
        img = Image.new("L", (W, H), 0)
        ImageDraw.Draw(img).text((x0 + i * step, cy), ch, font=f, fill=255, anchor="mm")
        out.append(np.asarray(img, np.float32) / 255)
    return out


def fractal_noise(scales=(8, 24, 64), weights=(0.55, 0.3, 0.15)):
    acc = np.zeros((H, W), np.float32)
    for s, w in zip(scales, weights):
        small = rng.random((H // s + 2, W // s + 2)).astype(np.float32)
        big = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((W + s * 2, H + s * 2), Image.BICUBIC), np.float32)[:H, :W] / 255
        acc += w * big
    return acc


# ---------- precompute ----------
CAL = os.path.join(HERE, "fonts", "MaShanZheng-Regular.ttf")
SERIF = os.path.join(HERE, "fonts", "NotoSerifSC-Light.otf")
glyph = text_mask("道", CAL, 470, (CX, CY))
glyph_glow = blur(glyph, 28)
glyph_bleed = blur(glyph, 6)
verse = char_masks("道可道，非常道", SERIF, 54, int(H * 0.79), 26)
source = text_mask("《 道 德 经 》  第 一 章", SERIF, 24, (W / 2, int(H * 0.87)))

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
dist = np.hypot(xx - CX, yy - CY)
noise = blur(fractal_noise(), 3)
reveal_field = dist / 330 + (noise - 0.5) * 0.55  # ink spreads from center with ragged edge
vignette = np.clip(1.15 - (np.hypot((xx - W / 2) / W, (yy - H / 2) / H) * 1.5) ** 2, 0, 1)

# particles
P = 3200
r0 = rng.uniform(260, 1150, P)
th0 = rng.uniform(0, 2 * np.pi, P)
delay = rng.uniform(0, 0.45, P)
spin = rng.uniform(2.2, 3.6, P)
bright = rng.uniform(0.25, 1.0, P)
# ambient dust after the flash
D = 260
dx, dy = rng.uniform(0, W, D), rng.uniform(0, H, D)
dvx, dvy = rng.normal(0, 6, D), rng.uniform(-14, -4, D)
dph = rng.uniform(0, 2 * np.pi, D)

trail = np.zeros((H, W), np.float32)
T_CONVERGE = 2.0

for i in range(N):
    t = i / FPS
    rgb = np.zeros((H, W, 3), np.float32)

    # 1) particles spiralling into the center
    splat = np.zeros((H, W), np.float32)
    if t < T_CONVERGE + 0.1:
        p = np.clip((t - delay) / (T_CONVERGE - delay), 0, 1)
        e = p ** 2.2
        r = r0 * (1 - e)
        th = th0 + spin * e
        px, py = CX + r * np.cos(th), CY + r * np.sin(th) * 0.82
        a = bright * np.clip(t / 0.6, 0, 1) * (0.35 + 0.65 * e)
        ok = (px >= 0) & (px < W - 1) & (py >= 0) & (py < H - 1) & (p < 1)
        iy, ix = py[ok].astype(int), px[ok].astype(int)
        for oy, ox in ((0, 0), (1, 0), (0, 1), (1, 1)):
            np.add.at(splat, (iy + oy, ix + ox), a[ok])
    trail = trail * 0.78 + splat
    pt = blur(np.clip(trail, 0, 1.5) / 1.5, 1.0) * 2.6 + np.clip(trail, 0, 1) * 0.6
    rgb += pt[..., None] * GOLD

    # central point gathering light
    core_amt = ease_in_out((t - 0.8) / 1.2) if t < T_CONVERGE else max(0.0, 1 - (t - T_CONVERGE) / 0.9)
    rgb += (core_amt * np.exp(-(dist / 9) ** 2))[..., None] * IVORY * 1.4
    rgb += (core_amt * 0.35 * np.exp(-(dist / 60) ** 2))[..., None] * GOLD

    # 2) flash + expanding ring
    if t >= T_CONVERGE:
        dt = t - T_CONVERGE
        flash = np.exp(-dt * 6) * np.exp(-(dist / 260) ** 2) * 0.9
        rgb += flash[..., None] * GOLD
        R = 40 + 900 * (1 - np.exp(-dt * 1.6))
        ring = np.exp(-((dist - R) / 2.2) ** 2) * np.exp(-dt * 1.3) * 0.8
        rgb += ring[..., None] * GOLD

        # ambient dust
        dust = np.zeros((H, W), np.float32)
        ax = (dx + dvx * dt).astype(int) % W
        ay = (dy + dvy * dt).astype(int) % H
        tw = 0.25 + 0.25 * np.sin(dph + t * 3)
        np.add.at(dust, (ay, ax), tw * min(1, dt / 0.8))
        rgb += blur(dust, 1.0)[..., None] * 3 * GOLD

    # 3) "道" ink reveal
    if t >= T_CONVERGE + 0.1:
        k = (t - T_CONVERGE - 0.1) / 1.5
        thr = ease_in_out(k) * 1.55
        m = np.clip((thr - reveal_field) / 0.16, 0, 1)
        bleed_amt = np.clip(1 - k * 0.7, 0.15, 1)
        g = glyph * m
        rgb += (glyph_bleed * m * 0.35 * bleed_amt)[..., None] * GOLD  # wet ink halo
        rgb += (glyph_glow * ease_in_out(k) * 0.55)[..., None] * GOLD
        rgb = rgb * (1 - g[..., None]) + g[..., None] * IVORY

    # 4) verse, char by char
    T_V = 3.25
    for j, cm in enumerate(verse):
        a = ease_in_out((t - T_V - j * 0.12) / 0.5)
        if a > 0:
            rgb = rgb * (1 - cm[..., None] * a) + cm[..., None] * a * IVORY * 0.92
    a = ease_in_out((t - 4.15) / 0.6)
    if a > 0:
        rgb = rgb * (1 - source[..., None] * a) + source[..., None] * a * GREY

    # grade: vignette + grain
    rgb *= vignette[..., None]
    rgb += rng.normal(0, 0.012, (H, W, 1)).astype(np.float32)
    rgb = np.clip(rgb, 0, 1)

    img = Image.fromarray((rgb * 255).astype(np.uint8))
    z = 1 + 0.035 * ease_in_out(t / DUR)  # slow push-in
    if z > 1.0005:
        cw, ch = W / z, H / z
        img = img.crop(((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).resize((W, H), Image.BICUBIC)
    img.save(os.path.join(FRAMES, f"{i:04d}.png"))
    print(f"\rframe {i + 1}/{N}", end="", flush=True)
print()

# ---------- audio: drone + bell at the flash ----------
SR = 48000
ts = np.arange(int(SR * DUR)) / SR
drone = sum(a * np.sin(2 * np.pi * f * ts + ph) for f, a, ph in [(55, 0.5, 0), (82.5, 0.25, 1), (110.3, 0.18, 2), (164.8, 0.08, 0.5)])
drone *= np.clip(ts / 1.5, 0, 1) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * ts)) * 0.35
whoosh = np.convolve(rng.normal(0, 1, ts.size), np.ones(60) / 60, "same") * np.clip(ts / T_CONVERGE, 0, 1) ** 3 * (ts < T_CONVERGE) * 0.25
bt = np.clip(ts - T_CONVERGE, 0, None)
bell = sum(a * np.sin(2 * np.pi * f * bt) * np.exp(-bt * d) for f, a, d in [(392, 0.5, 1.2), (392 * 2.76, 0.25, 2.2), (392 * 5.4, 0.12, 3.5), (392 * 0.5, 0.3, 0.9)])
bell *= (ts >= T_CONVERGE) * np.clip(bt / 0.004, 0, 1)
mix = drone + whoosh + bell * 0.6
mix *= np.clip((DUR - ts) / 0.4, 0, 1)
mix = (mix / np.abs(mix).max() * 0.8 * 32767).astype(np.int16)
wav_path = os.path.join(HERE, "audio.wav")
with wave.open(wav_path, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(mix.tobytes())

out = os.path.join(HERE, "demo_5s.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "%04d.png"), "-i", wav_path,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "slow", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
print("wrote", out)
