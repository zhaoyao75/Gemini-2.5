"""9 秒可循环东方旋律《清风》 — D 宫五声音阶，笛子 + 古筝 + 琵琶 + 堂鼓 + 木鱼 + 碰铃。
开门见山的钩子乐句，第 2 小节冲顶，全程不掉力度；尾音与混响折回开头，首尾无缝。纯 numpy 合成。"""
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

def gliss(t_land, notes, g0=0.11, g1=0.26, step=0.030):
    """古筝上行刮奏，最后一个音落在 t_land 之前一步，把力量送到下一拍。"""
    n = len(notes)
    for i, m in enumerate(notes):
        put(pluck(m, 1.6, bright=1.25), t_land - (n - i) * step, pan=-0.5 + i / n, gain=g0 + (g1 - g0) * i / n)

def roll(bar, beats, g0, g1):                       # 堂鼓滚奏渐强
    for k, b in enumerate(beats):
        put(drum(125, .25), T(bar, b), gain=g0 + (g1 - g0) * k / max(len(beats) - 1, 1))

# 笛子主旋律：(拍, 时值, 音高, 倚音, 断连, 力度)
MEL = {
 # 钩子：5 65 3 5–（切分长音）｜顿｜1235 冲上去
 0: [(0,.5,81,78,.62,.56),(.5,.25,83,None,.9,.50),(.75,.25,81,None,.9,.50),(1,.5,78,None,.7,.50),(1.5,1.0,81,None,.96,.60),
     (3,.25,74,None,.9,.46),(3.25,.25,76,None,.9,.49),(3.5,.25,78,None,.9,.53),(3.75,.25,81,None,.9,.57)],
 # 顶点：高音 1̇ 长音，6 5，十六分花舌 61̇65，3 5
 1: [(0,1.0,86,83,.96,.56),(1,.5,83,None,.8,.52),(1.5,.5,81,None,.8,.50),
     (2,.25,83,None,.9,.50),(2.25,.25,86,None,.9,.52),(2.5,.25,83,None,.9,.50),(2.75,.25,81,None,.9,.48),
     (3,.5,78,None,.7,.50),(3.5,.5,81,None,.92,.54)],
 # 呼应：6– 5｜3 2 3 5（跳音）
 2: [(0,1.5,83,81,.97,.60),(1.5,.5,81,None,.85,.52),(2,.5,78,None,.6,.50),(2.5,.5,76,None,.6,.50),
     (3,.5,78,None,.6,.52),(3.5,.5,81,None,.92,.55)],
 # 收束：6 5 3 2 ｜1（全体重音）｜顿｜123 送回开头
 3: [(0,.5,83,None,.72,.56),(.5,.5,81,None,.72,.54),(1,.5,78,None,.72,.52),(1.5,.5,76,None,.9,.52),(2,1.0,74,71,.95,.60),
     (3.25,.25,74,None,.9,.46),(3.5,.25,76,None,.9,.50),(3.75,.25,78,None,.9,.54)],
}
for bar, notes in MEL.items():
    for b, d, m, g, st, gn in notes:
        put(dizi(m, d * BEAT * st, vib=d >= 1, grace=g), T(bar, b), pan=0.2, gain=gn)
        put(pluck(m - 12, .8, bright=1.6, decay=2.6, bend=0.004), T(bar, b), pan=0.5, gain=0.23)     # 琵琶低八度齐奏
        if d >= 1:                                                                                  # 长音：琵琶轮指 + 古筝同度点亮
            for i in range(int(d * BEAT / 0.095)):
                put(pluck(m - 12, .45, bright=1.6, decay=3.6, bend=0.002), T(bar, b) + (i + 1) * 0.095, pan=0.5, gain=0.15)
            put(pluck(m, 2.0, bright=1.1, vib=0.006), T(bar, b), pan=-0.15, gain=0.26)

# 古筝：八分音符分解和弦（D – Bm – Esus→A – D），1、3 拍重音；None 为留白
ARP = {0: [50,57,62,66,50,None,45,None], 1: [47,54,59,62,47,54,59,66],
       2: [52,59,64,69,45,52,57,64],     3: [50,57,62,66,None,None,None,None]}
for bar, arp in ARP.items():
    for i, m in enumerate(arp):
        if m: put(pluck(m, 2.3, bright=1.05, vib=0.004 if i % 4 == 0 else 0), T(bar, i * .5), pan=-0.4,
                  gain=0.50 if i % 4 == 0 else 0.25)
for bar, m in enumerate([38, 35, 40, 38]):
    put(pluck(m, 2.6, bright=0.9), T(bar, 0), pan=-0.3, gain=0.42)                                   # 低音根音

# 打击：堂鼓定重音，木鱼走反拍
for bar, hits in {0: [(0,.40),(1.5,.24),(2,.14)], 1: [(0,.46),(2,.26),(3.5,.16)],
                  2: [(0,.44),(1.5,.20),(2,.26),(3.5,.16)], 3: [(0,.40),(1,.18),(2,.48)]}.items():
    for b, g in hits: put(drum(88, .6), T(bar, b), gain=g)
for bar, beats in {0: [.5,1,2], 1: [.5,1,1.5,2.5,3], 2: [.5,1,2.5,3], 3: [.5,1.5]}.items():
    for b in beats: put(woodblock(988 if b % 1 else 740), T(bar, b), pan=0.3, gain=0.06 if b % 1 else 0.075)
roll(0, [3, 3.25, 3.5, 3.75], .08, .22)             # 顿后滚奏冲向顶点
roll(3, [3.25, 3.5, 3.75], .10, .22)                # 送回循环开头

# 刮奏：把每个乐句推进下一小节
gliss(T(1, 0), [66, 69, 71, 74, 76, 78, 81, 83, 86], .12, .30)       # 2 秒处冲顶
gliss(T(2, 0), [64, 66, 69, 71, 74, 76, 78, 81], .10, .24)
gliss(T(4, 0), [62, 64, 66, 69, 71, 74, 76, 78, 81], .12, .28)       # 落在循环第一拍

# 第 4 小节第 3 拍：全体重音和弦 + 碰铃
for k, (m, g) in enumerate([(38, .46), (50, .40), (57, .30), (62, .32), (66, .28), (74, .30), (86, .22)]):
    put(pluck(m, 2.6, bright=1.0, vib=0.004), T(3, 2) + k * 0.012, pan=-0.4 + k * 0.08, gain=g)
put(bell(), T(3, 2), pan=0.1, gain=0.05)
put(bell(), T(1, 0), pan=-0.1, gain=0.05)

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
