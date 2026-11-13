"""9 秒可循环东方旋律《清风》 — D 宫五声音阶。
双笛 + 古筝（流水分解和弦）+ 琵琶轮指 + 笙 + 大阮低音 + 堂鼓 + 碰铃。
一个动机模进一次再收束；尾音与混响折回开头，首尾无缝。纯 numpy 合成。"""
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

def dizi(m, dur, vib=True, grace=None, det=0.0):
    """竹笛：带笛膜的明亮泛音 + 气声 + 延迟颤音。"""
    n = int((dur + 0.08) * SR); t = np.arange(n) / SR
    f = hz(m) * 2 ** (det / 1200) * (1 - 0.018 * np.exp(-t * 60))
    if grace is not None:                      # 倚音
        g = int(0.055 * SR); f[:g] = hz(grace)
    if vib:
        f = f * (1 + 0.0055 * np.sin(2 * np.pi * 5.6 * t) * np.clip((t - .22) * 3.5, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    amps = [1, .70, .50, .40, .26, .20, .12, .10, .06]   # 笛膜的亮色
    out = sum(a * np.sin((k + 1) * ph) for k, a in enumerate(amps) if hz(m) * (k + 1) < 10000)
    noise = rng.standard_normal(n); noise = np.convolve(noise, np.ones(6) / 6, 'same')
    noise = noise - np.convolve(noise, np.ones(60) / 60, 'same')
    env = np.clip(t / 0.035, 0, 1) * np.clip((dur + 0.08 - t) / 0.08, 0, 1)
    env *= 0.82 + 0.18 * np.exp(-t * 6)
    return (out * 0.33 + noise * (0.05 + 0.18 * np.exp(-t * 40))) * env

def woodblock(f=880):
    t = np.arange(int(0.12 * SR)) / SR
    return (np.sin(2*np.pi*f*t) + .5*np.sin(2*np.pi*f*2.41*t)) * np.exp(-t * 55)

def bell(f=2637):
    t = np.arange(int(2.5 * SR)) / SR
    return sum(a*np.sin(2*np.pi*f*r*t)*np.exp(-t*d) for r, a, d in
               [(1, 1, 2.2), (2.76, .5, 3.5), (5.4, .25, 6), (1.003, .6, 2.0)])

def drum(f0=95, d=0.5):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2*np.pi*(f0*t + 25*(1-np.exp(-t*30))/30)) * np.exp(-t*9) + rng.standard_normal(len(t))*np.exp(-t*120)*.3

def sheng(m, dur):
    """笙：持续的簧片和声，垫厚中频。"""
    n = int((dur + 0.2) * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(hz(m) * (1 + 0.002 * np.sin(2 * np.pi * 4.5 * t + m))) / SR
    out = sum(a * np.sin((k + 1) * ph) for k, a in enumerate([1, .5, .6, .25, .3, .12, .15, .06]))
    env = np.clip(t / 0.07, 0, 1) * np.clip((dur + 0.2 - t) / 0.2, 0, 1) * (1 + 0.05 * np.sin(2 * np.pi * 5 * t))
    return out * env * 0.3

def bass(m, dur=1.4):
    """大阮式低音：基频饱满、衰减慢，托住低频。"""
    t = np.arange(int(dur * SR)) / SR; f = hz(m)
    out = np.sin(2*np.pi*f*t) + .45*np.sin(2*np.pi*2*f*t)*np.exp(-t*2) + .2*np.sin(2*np.pi*3*f*t)*np.exp(-t*5)
    return out * np.exp(-t * 2.2) * np.clip(t / 0.006, 0, 1) * np.clip((dur - t) / 0.05, 0, 1)

T = lambda bar, beat: START + (bar * 4 + beat) * BEAT

def gliss(t_land, notes, g0=0.10, g1=0.24, step=0.030):
    n = len(notes)
    for i, m in enumerate(notes):
        put(pluck(m, 1.6, bright=1.2), t_land - (n - i) * step, pan=-0.5 + i / n, gain=g0 + (g1 - g0) * i / n)

# ---- 主旋律：一个动机，模进一次，再下行收束（连奏，全是四分/八分音符）----
# (拍, 时值, 音高, 倚音)
MEL = {
 0: [(0,.5,78,None),(.5,.5,81,None),(1,1,83,81),(2,1,81,None),(3,.5,78,None),(3.5,.5,76,None)],     # 3 5 6– 5– 3 2
 1: [(0,.5,78,None),(.5,.5,81,None),(1,1.5,86,83),(2.5,.5,83,None),(3,1,81,None)],                 # 3 5 1̇–– 6 5–
 2: [(0,1,83,None),(1,.5,81,None),(1.5,.5,78,None),(2,1,76,None),(3,.5,78,None),(3.5,.5,81,None)],  # 6– 5 3 2– 3 5
 3: [(0,1,78,None),(1,1,76,None),(2,1.75,74,71)],                                                   # 3– 2– 1––
}
for bar, notes in MEL.items():
    for b, d, m, g in notes:
        L_ = d * BEAT * 0.98; acc = 1.12 if b in (0, 2) or d > 1 else 1.0
        for det, pan in [(-4, 0.02), (4, 0.38)]:                               # 双笛齐奏
            put(dizi(m, L_, vib=d >= 1, grace=g, det=det), T(bar, b), pan=pan, gain=0.30 * acc)
        put(pluck(m, 2.0, bright=1.3, vib=0.005 if d >= 1 else 0), T(bar, b), pan=-0.15, gain=0.22)   # 古筝同度齐奏，音头清亮
        if d >= 1:                                                             # 长音：琵琶轮指托住
            for i in range(int(L_ / 0.1)):
                put(pluck(m - 12, .45, bright=1.6, decay=3.2, bend=0.002), T(bar, b) + i * 0.1, pan=0.5, gain=0.15)

# ---- 笙：和声长音（D – Bm – Esus/A – D），比上一稿轻 ----
for bar, b, d, chord in [(0, 0, 4, [50, 57, 62, 66, 69]), (1, 0, 4, [47, 54, 59, 62, 66]),
                         (2, 0, 2, [52, 59, 64, 69]), (2, 2, 2, [45, 57, 59, 64]), (3, 0, 4, [50, 57, 62, 66, 69])]:
    for m in chord:
        put(sheng(m, d * BEAT), T(bar, b), pan=0.15 * ((m % 3) - 1), gain=0.085 if m > 52 else 0.12)

# ---- 低音：只在 1、3 拍落根音，稳住重心 ----
for bar, (m1, m2) in enumerate([(38, 38), (35, 35), (40, 33), (38, 38)]):
    put(bass(m1, 1.6), T(bar, 0), gain=0.48); put(bass(m2, 1.6), T(bar, 2), gain=0.40)

# ---- 古筝：十六分音符"流水"分解和弦，连绵流动 ----
WAVE = {'D': [50,57,62,66,69,66,62,57], 'Bm': [47,54,59,62,66,62,59,54],
        'E': [52,59,64,69,71,69,64,59], 'A': [45,52,57,59,64,59,57,52]}
for bar, (c1, c2) in enumerate([('D', 'D'), ('Bm', 'Bm'), ('E', 'A'), ('D', None)]):
    for h, c in enumerate([c1, c2]):
        if c is None: continue
        for i, m in enumerate(WAVE[c]):
            put(pluck(m, 2.0, bright=1.35), T(bar, h * 2 + i * .25), pan=-0.45 + 0.06 * i,
                gain=0.30 if i == 0 else (0.17 if i % 2 == 0 else 0.13))

# ---- 打击：只留每小节第一拍的堂鼓和第三拍的轻点，不用木鱼 ----
for bar in range(4):
    put(drum(78, .8), T(bar, 0), gain=0.40)
    put(drum(78, .6), T(bar, 2), gain=0.14 if bar < 3 else 0.42)

# ---- 点睛：两处刮奏 —— 冲向顶点、送回开头 ----
gliss(T(1, 1), [69, 71, 74, 76, 78, 81, 83, 86], .10, .26)
gliss(T(4, 0), [62, 64, 66, 69, 71, 74, 76], .10, .24)
put(bell(), T(0, 0), pan=0.1, gain=0.035)
put(bell(), T(1, 1), pan=-0.1, gain=0.05)
for k, (m, g) in enumerate([(50, .40), (57, .30), (62, .32), (66, .28), (74, .30), (86, .20)]):   # 收束处全体和弦
    put(pluck(m, 2.6, bright=1.2, vib=0.004), T(3, 2) + k * 0.012, pan=-0.4 + k * 0.1, gain=g)
put(bell(), T(3, 2), pan=0.1, gain=0.045)

# ---- 混响（厅堂感）----
def reverb(x, seed):
    r = np.random.default_rng(seed); n = int(1.9 * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t * 3.4) * np.clip(t / 0.012, 0, 1)
    ir = np.convolve(ir, np.ones(5) / 5, 'same')
    m = len(x) + n; F = np.fft.rfft(x, m) * np.fft.rfft(ir, m)
    return np.fft.irfft(F, m)[:len(x)] * 0.027
L2 = L + reverb(L, 1) * 0.9 + reverb(R, 3) * 0.3
R2 = R + reverb(R, 2) * 0.9 + reverb(L, 4) * 0.3

# ---- 总线均衡：提亮高频、收一点中低频的浑浊 ----
def eq(x):
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g_db = 6.0 / (1 + (2600 / np.maximum(f, 1)) ** 2) - 1.0 * np.exp(-(np.log2(np.maximum(f, 1) / 320)) ** 2 / 0.5)
    return np.fft.irfft(np.fft.rfft(x) * 10 ** (g_db / 20), len(x))
L2, R2 = eq(L2), eq(R2)

# ---- 无缝循环：把 9 秒之后的余音折回开头 ----
out = np.stack([L2[:N], R2[:N]], 1).copy()
ext = len(L2) - N
out[:ext, 0] += L2[N:]; out[:ext, 1] += R2[N:]
out = np.tanh(out / np.abs(out).max() * 1.15) / np.tanh(1.15) * 0.92
with wave.open('qingfeng_9s.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype('<i2').tobytes())
print('ok', len(out) / SR, 's peak', np.abs(out).max(), 'rms', np.sqrt((out**2).mean()))
