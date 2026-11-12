"""9 秒可循环东方旋律《清风》 — D 宫五声音阶，笛子 + 古筝 + 琵琶 + 堂鼓 + 木鱼 + 碰铃。
尾音与混响折回开头，首尾无缝衔接。纯 numpy 合成。"""
import numpy as np, wave

SR = 44100
DUR = 9.0
N = int(SR * DUR)
L = np.zeros(N + SR * 3); R = np.zeros(N + SR * 3)
rng = np.random.default_rng(7)

BEAT = 0.5625    # 16 拍正好 9 秒（≈107 BPM）
START = 0.0      # 循环起点即第一拍

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

def drum(f0=95, d=0.5):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2*np.pi*(f0*t + 25*(1-np.exp(-t*30))/30)) * np.exp(-t*9) + rng.standard_normal(len(t))*np.exp(-t*120)*.3

T = lambda bar, beat: START + (bar * 4 + beat) * BEAT

# ======== 循环起点 ========
put(bell(), T(0, 0), pan=-0.1, gain=0.03)

# ======== 起（第1小节，弱）：笛子低音区轻吟，句尾一顿 ========
for b, d, m, g, gn in [(0, 1.5, 69, 66, .40), (1.5, .5, 71, None, .36), (2, 1.0, 74, None, .38)]:
    put(dizi(m, d * BEAT * .95, vib=d >= 1, grace=g), T(0, b), pan=0.2, gain=gn)
for b, m, g in [(0, 50, .36), (1, 57, .20), (1.5, 62, .17), (2, 66, .20), (2.5, 57, .14)]:   # 稀疏伴奏，第4拍留白
    put(pluck(m, 2.4, bright=0.9, vib=0.004 if b == 0 else 0), T(0, b), pan=-0.4, gain=g)
put(woodblock(740), T(0, 3), pan=0.3, gain=0.06)                                     # 顿处一点木鱼
for b, m in [(3.5, 74), (3.75, 76)]:                                                 # 笛子弱起接句
    put(dizi(m, .25 * BEAT * .9, vib=False), T(0, b), pan=0.2, gain=0.36)
put(drum(120, .3), T(0, 3.5), gain=0.10); put(drum(120, .3), T(0, 3.75), gain=0.16)

# ======== 承（第2小节，中强）：笛子跳跃应答，断连相间，中间再一顿 ========
for b, d, m, g, st in [(0, .5, 78, None, .55), (.5, .25, 76, None, .9), (.75, .25, 78, None, .9),
                       (1, 1, 81, 78, .92), (2.5, .5, 78, None, .6), (3, .5, 76, None, .6), (3.5, .5, 74, None, .95)]:
    put(dizi(m, d * BEAT * st, vib=d >= 1, grace=g), T(1, b), pan=0.2, gain=0.50 if b != 1 else 0.60)
    put(pluck(m - 12, .8, bright=1.6, decay=2.6, bend=0.004), T(1, b), pan=0.5, gain=0.20)   # 琵琶点染
for i, m in enumerate([47, 54, 59, 54, None, 54, 59, 62]):                           # 第3拍正拍留白
    if m: put(pluck(m, 2.2, bright=1.0), T(1, i * .5), pan=-0.4, gain=0.40 if i == 0 else 0.22)
for b, f, g in [(0, 740, .10), (1, 988, .06), (2.5, 988, .05), (3, 740, .08), (3.5, 988, .06)]:
    put(woodblock(f), T(1, b), pan=0.3, gain=g)
for i, m in enumerate([66, 69, 71, 74, 76, 78, 81, 83]):                             # 渐强刮奏推向高潮
    put(pluck(m, 1.8, bright=1.25), T(1, 3.5) + i * 0.031, pan=-0.5 + i * 0.1, gain=0.12 + 0.02 * i)

# ======== 转（第3小节，强）：笛子大跳至最高音，古筝低八度齐奏，琵琶轮指，鼓点 ========
put(drum(85, .7), T(2, 0), gain=0.42); put(drum(110, .4), T(2, 2), gain=0.22); put(drum(110, .3), T(2, 3.5), gain=0.12)
dz = [(0, 1.5, 83, 81), (1.5, .5, 81, None), (2, .5, 78, None), (2.5, .5, 76, None), (3, .5, 74, None), (3.5, .5, 76, None)]
for j, (b, d, m, g) in enumerate(dz):
    put(dizi(m, d * BEAT * .96, vib=d >= 1, grace=g), T(2, b), pan=0.2, gain=[.70, .62, .56, .50, .44, .38][j])
for j, (b, d, m, g) in enumerate(dz):                                               # 古筝低八度齐奏旋律
    put(pluck(m - 12, 2.0, bright=1.2, vib=0.005 if d >= 1 else 0), T(2, b), pan=-0.15, gain=[.40, .32, .30, .27, .24, .20][j])
for i in range(8):                                                                   # 琵琶轮指托长音
    put(pluck(71, .5, bright=1.6, decay=3.5, bend=0.002), T(2, 0) + i * 0.098, pan=0.5, gain=0.20 - 0.012 * i)
for i, m in enumerate([47, 54, 59, 62, 45, 52, 57, 64]):
    put(pluck(m, 2.4, bright=1.1), T(2, i * .5), pan=-0.4, gain=[.62, .30, .32, .30, .46, .24, .24, .18][i])
put(pluck(35, 2.5, bright=0.9), T(2, 0), pan=-0.4, gain=0.45)
for b, f, g in [(0, 740, .12), (1, 988, .07), (2, 740, .09), (3, 988, .05)]:
    put(woodblock(f), T(2, b), pan=0.3, gain=g)

# ======== 合（第4小节，突弱）：全体一顿，笛子落回主音；古筝上行刮奏把乐句送回开头 ========
put(dizi(69, .5 * BEAT * .95, vib=False), T(3, 0), pan=0.2, gain=0.36)
put(dizi(74, 1.7 * BEAT, grace=71), T(3, .5), pan=0.2, gain=0.40)
for j, (m, g) in enumerate([(38, .40), (50, .32), (57, .24), (62, .24), (66, .22)]):  # 半拍后和弦琶音落下
    put(pluck(m, 3.0, bright=0.9, vib=0.004), T(3, .5) + j * 0.022, pan=-0.4, gain=g)
put(pluck(86, 2.0, bright=1.1, vib=0.006), T(3, 2.5), pan=-0.2, gain=0.22)           # 高音泛音般一点
put(bell(), T(3, 2.5), pan=0.1, gain=0.045)
put(woodblock(988), T(3, 3), pan=0.3, gain=0.05)
for i, m in enumerate([62, 64, 66, 69, 71, 74, 76, 78, 81]):                         # 刮奏弱起，直接落在循环第一拍
    put(pluck(m, 1.6, bright=1.2), T(3, 3.5) + i * 0.030, pan=-0.5 + i * 0.1, gain=0.10 + i * 0.009)

# ---- 混响（厅堂感）----
def reverb(x, seed):
    r = np.random.default_rng(seed); n = int(1.9 * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t * 3.4) * np.clip(t / 0.012, 0, 1)
    ir = np.convolve(ir, np.ones(5) / 5, 'same')
    m = len(x) + n; F = np.fft.rfft(x, m) * np.fft.rfft(ir, m)
    return np.fft.irfft(F, m)[:len(x)] * 0.02
L2 = L + reverb(L, 1) * 0.9 + reverb(R, 3) * 0.3
R2 = R + reverb(R, 2) * 0.9 + reverb(L, 4) * 0.3

# ---- 无缝循环：把 9 秒之后的余音折回开头 ----
out = np.stack([L2[:N], R2[:N]], 1).copy()
ext = len(L2) - N
out[:ext, 0] += L2[N:]; out[:ext, 1] += R2[N:]
out = np.tanh(out / np.abs(out).max() * 1.15) / np.tanh(1.15) * 0.92
with wave.open('qingfeng_9s.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype('<i2').tobytes())
print('ok', len(out) / SR, 's peak', np.abs(out).max(), 'rms', np.sqrt((out**2).mean()))
