"""9 秒东方旋律《清风》 — D 宫五声音阶，笛子 + 古筝 + 琵琶 + 木鱼 + 碰铃。纯 numpy 合成。"""
import numpy as np, wave

SR = 44100
DUR = 9.0
N = int(SR * DUR)
L = np.zeros(N + SR * 3); R = np.zeros(N + SR * 3)
rng = np.random.default_rng(7)

BEAT = 0.54      # ≈111 BPM：明快而不急
START = 0.30     # 开头留给古筝刮奏

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def put(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR); a = np.sqrt((1 - pan) / 2); b = np.sqrt((1 + pan) / 2)
    L[i:i + len(sig)] += sig * gain * a; R[i:i + len(sig)] += sig * gain * b

def pluck(m, dur=2.2, bright=1.0, decay=1.0, bend=0.012, vib=0.0):
    """拨弦（古筝/琵琶）：加法合成，高次泛音衰减更快，起音带轻微滑音。"""
    t = np.arange(int(dur * SR)) / SR
    f = hz(m) * (1 + bend * np.exp(-t * 28))
    if vib: f = f * (1 + vib * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - .12) * 5, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    out = np.zeros_like(t)
    for k in range(1, 15):
        if hz(m) * k > 9000: break
        amp = (1 / k ** (1.25 / bright)) * (0.35 + abs(np.sin(k * np.pi * 0.21)))  # 拨弦点梳状
        out += amp * np.exp(-t * decay * (1.4 + 0.75 * k)) * np.sin(k * ph * (1 + 0.00012 * k * k))
    att = np.clip(t / 0.003, 0, 1)
    click = rng.standard_normal(len(t)) * np.exp(-t * 900) * 0.25   # 指甲触弦
    return (out + click) * att

def dizi(m, dur, vib=True, grace=None):
    """竹笛：带笛膜的明亮泛音 + 气声 + 延迟颤音。"""
    n = int((dur + 0.08) * SR); t = np.arange(n) / SR
    f = hz(m) * (1 - 0.018 * np.exp(-t * 60))
    if grace is not None:                      # 倚音
        g = int(0.055 * SR); f[:g] = hz(grace)
    if vib:
        f = f * (1 + 0.0055 * np.sin(2 * np.pi * 5.6 * t) * np.clip((t - .22) * 3.5, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    amps = [1, .62, .40, .30, .14, .12, .05, .05]
    out = sum(a * np.sin((k + 1) * ph) for k, a in enumerate(amps) if hz(m) * (k + 1) < 10000)
    noise = rng.standard_normal(n); noise = np.convolve(noise, np.ones(6) / 6, 'same')
    noise = noise - np.convolve(noise, np.ones(60) / 60, 'same')
    env = np.clip(t / 0.035, 0, 1) * np.clip((dur + 0.08 - t) / 0.08, 0, 1)
    env *= 0.82 + 0.18 * np.exp(-t * 6)
    return (out * 0.33 + noise * (0.10 + 0.25 * np.exp(-t * 40))) * env

def woodblock(f=880):
    t = np.arange(int(0.12 * SR)) / SR
    return (np.sin(2*np.pi*f*t) + .5*np.sin(2*np.pi*f*2.41*t)) * np.exp(-t * 55)

def bell(f=2637):
    t = np.arange(int(2.5 * SR)) / SR
    return sum(a*np.sin(2*np.pi*f*r*t)*np.exp(-t*d) for r, a, d in
               [(1, 1, 2.2), (2.76, .5, 3.5), (5.4, .25, 6), (1.003, .6, 2.0)])

T = lambda bar, beat: START + (bar * 4 + beat) * BEAT

# ---- 开场：古筝上行刮奏 ----
for i, m in enumerate([62, 64, 66, 69, 71, 74, 76, 78, 81]):
    put(pluck(m, 1.6, bright=1.2), 0.02 + i * 0.030, pan=-0.5 + i * 0.1, gain=0.16 + i * 0.012)

# ---- 主旋律（笛子）：(起拍, 时值, 音高, 倚音) ----
melody = [
 (0,0,1,69,66),(0,1,.5,71,None),(0,1.5,.5,74,None),(0,2,1,76,None),(0,3,.5,74,None),(0,3.5,.5,71,None),
 (1,0,.5,69,None),(1,.5,.5,71,None),(1,1,.5,74,None),(1,1.5,.5,76,None),(1,2,1.5,78,76),(1,3.5,.5,76,None),
 (2,0,1,81,78),(2,1,.5,78,None),(2,1.5,.5,76,None),(2,2,.5,74,None),(2,2.5,.5,76,None),(2,3,.5,71,None),(2,3.5,.5,69,None),
]
for bar, b, d, m, g in melody:
    put(dizi(m, d * BEAT * 0.96, vib=d >= 1, grace=g), T(bar, b), pan=0.12, gain=0.50)
    if d >= 1 or b == int(b):                      # 琵琶在骨干音上低八度点染
        put(pluck(m - 12, 1.0, bright=1.5, decay=2.4, bend=0.004), T(bar, b), pan=0.45, gain=0.20)
# 琵琶轮指：第二小节长音
for i in range(7):
    put(pluck(66, .5, bright=1.6, decay=3.5, bend=0.002), T(1, 2) + i * 0.105, pan=0.45, gain=0.085 + 0.012 * i)

# ---- 古筝伴奏：八分音符分解和弦 ----
arps = [[50,57,62,57,66,57,62,57],[47,54,59,54,62,54,59,54],[45,52,57,52,59,52,57,52]]
for bar, arp in enumerate(arps):
    for i, m in enumerate(arp):
        put(pluck(m, 2.4, bright=0.95 if i else 0.8, vib=0.004 if i == 0 else 0),
            T(bar, i * .5), pan=-0.35, gain=0.44 if i == 0 else (0.25 if i % 2 == 0 else 0.19))

# ---- 木鱼：轻点节拍 ----
for bar in range(3):
    for b, f, g in [(0, 740, .10), (1, 988, .055), (2, 740, .08), (2.5, 988, .04), (3, 988, .055)]:
        put(woodblock(f), T(bar, b), pan=0.3, gain=g)

# ---- 收束：主音长吟 + 古筝回旋刮奏 + 碰铃 ----
put(dizi(74, 2.5 * BEAT, grace=71), T(3, 0), pan=0.12, gain=0.50)
for m, g in [(38, .50), (50, .40), (57, .28), (62, .28), (66, .24)]:
    put(pluck(m, 3.2, bright=0.9, vib=0.004), T(3, 0) + (m - 38) * 0.0012, pan=-0.35, gain=g)
put(pluck(62, 1.5, bright=1.5, decay=2.0), T(3, 0), pan=0.45, gain=0.22)
put(bell(), T(0, 0), pan=-0.1, gain=0.035)
run = [81, 78, 76, 74, 71, 69, 66, 69, 71, 74, 76, 78, 81, 83, 86]
t0 = T(3, 1.5)
for i, m in enumerate(run):
    put(pluck(m, 2.2, bright=1.2), t0 + i * 0.036 + 0.0006 * i * i, pan=-0.6 + i * 0.08, gain=0.13 + 0.008 * i)
tend = T(3, 3)
put(pluck(86, 2.5, bright=1.1, vib=0.006), tend, pan=-0.2, gain=0.34)
put(pluck(74, 2.5, bright=1.0), tend, pan=-0.35, gain=0.26)
put(bell(), tend, pan=0.1, gain=0.06)

# ---- 混响（厅堂感）----
def reverb(x, seed):
    r = np.random.default_rng(seed); n = int(1.9 * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t * 3.4) * np.clip(t / 0.012, 0, 1)
    ir = np.convolve(ir, np.ones(5) / 5, 'same')
    m = len(x) + n; F = np.fft.rfft(x, m) * np.fft.rfft(ir, m)
    return np.fft.irfft(F, m)[:len(x)] * 0.02
L2 = L + reverb(L, 1) * 0.9 + reverb(R, 3) * 0.3
R2 = R + reverb(R, 2) * 0.9 + reverb(L, 4) * 0.3

out = np.stack([L2[:N], R2[:N]], 1)
fade = int(0.9 * SR); out[-fade:] *= (np.cos(np.linspace(0, np.pi / 2, fade)) ** 2)[:, None]
out[:200] *= np.linspace(0, 1, 200)[:, None]
out = np.tanh(out / np.abs(out).max() * 1.15) / np.tanh(1.15) * 0.92
with wave.open('qingfeng_9s.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype('<i2').tobytes())
print('ok', len(out) / SR, 's peak', np.abs(out).max(), 'rms', np.sqrt((out**2).mean()))
