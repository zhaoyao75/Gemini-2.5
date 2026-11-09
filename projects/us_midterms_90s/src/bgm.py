"""Synthesize BGM + SFX with numpy, aligned to timeline.json beats (adapted from the friendship-paradox project).
A minor (Am-F-C-G). Title: pad only. Pulse kick from the first content scene; chords each bar; arpeggio from the senate scene.
Writes build/bgm.wav."""
import json, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "src" / "timeline.json").read_text())
SC = TL["scenes_beats"]
SR = 44100
BEAT = 60 / TL["bpm"]
INTRO, TB = TL["intro_seconds"], SC["D_title"][1]
def T(n): return n / TB * INTRO if n < TB else INTRO + (n - TB) * BEAT
DUR = T(TL["total_beats"]) + TL["tail_seconds"]
N = int(DUR * SR); t = np.arange(N) / SR
rng = np.random.default_rng(42)
mix = np.zeros((N, 2))
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    mix[i:i + len(sig), 0] += sig * np.sqrt(0.5 * (1 - pan)); mix[i:i + len(sig), 1] += sig * np.sqrt(0.5 * (1 + pan))
def env(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
TOTAL = TL["total_beats"]; n_bars = int(np.ceil(TOTAL / 4))
for bar in range(n_bars):
    start = T(bar * 4); n = int((T(bar * 4 + 4) - start + 0.8) * SR); tt = np.arange(n) / SR; sig = np.zeros(n)
    for m in CHORDS[bar % 4] + [CHORDS[bar % 4][0] - 12]:
        for det in (-0.12, 0.12):
            f = hz(m) * 2 ** (det / 12)
            for h, amp in ((1, 1.0), (2, 0.35), (3, 0.15)): sig += amp * np.sin(2 * np.pi * f * h * tt + rng.uniform(0, 6.28))
    add(sig * env(n, 0.05 if bar == 0 else 0.9, 0.9) * 0.018, start)
def piano(midi, dur=2.6, vel=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR; f = hz(midi)
    s = sum(a * np.sin(2 * np.pi * f * h * tt) * np.exp(-tt * (2.2 + h * 1.4)) for h, a in ((1, 1), (2, .45), (3, .22), (4, .1)))
    return s * np.minimum(1, tt / 0.004) * vel
NOTES = [69, 74, 76, 72, 69, 76, 74, 72, 76, 69, 72]
for (name, (s, e)), m in zip(SC.items(), NOTES): add(piano(m, 3.5, 0.16), T(s), pan=0.1)
add(piano(76, 3.5, 0.16), T(SC["L_end"][0]), pan=0.1)
B0, G0, K0, L0 = SC["B_what"][0], SC["G_senate"][0], SC["K_next"][0], SC["L_end"][0]
for beat in range(B0, TOTAL, 4):
    vel = 0.07 if beat < L0 else 0.05
    for k, m in enumerate(CHORDS[(beat // 4) % 4]): add(piano(m + 12, 3.0, vel), T(beat) + k * 0.012, pan=-0.2 + 0.2 * k)
for k in range(int((L0 - G0) * 2)):
    beat = G0 + k / 2; ch = CHORDS[(int(beat) // 4) % 4]
    add(piano(ch[k % 3] + 24, 1.2, 0.04), T(beat), pan=0.3 * np.sin(k))
def kick():
    n = int(0.35 * SR); tt = np.arange(n) / SR; f = 50 + 70 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)
for beat in range(B0, L0):
    if beat < SC["C_power"][0] and beat % 2: continue          # half-time for the first scene, every beat after
    add(kick(), T(beat), gain=0.16 if beat < SC["C_power"][0] else (0.26 if beat >= G0 else 0.22))
def whoosh():
    n = int(1.1 * SR); tt = np.arange(n) / SR; noise = rng.standard_normal(n); out = np.zeros(n)
    for i, w in enumerate(np.linspace(40, 4, 8)):
        seg = slice(int(i * n / 8), int((i + 1) * n / 8)); out[seg] = np.convolve(noise, np.ones(int(w)) / w, mode="same")[seg]
    return out * np.sin(np.pi * tt / tt[-1]) ** 2
def tick():
    n = int(0.12 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 60)
def pop():
    n = int(0.15 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * (900 + 500 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 35)
def ding(): return piano(88, 2.5, 1.0) + 0.5 * piano(95, 2.5, 1.0)
def swell_sfx():
    n = int(2.2 * SR); tt = np.arange(n) / SR
    return np.convolve(rng.standard_normal(n), np.ones(60) / 60, mode="same") * (tt / tt[-1]) ** 2 * np.exp(-np.maximum(0, tt - 1.9) * 30)
def thud():
    n = int(0.6 * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * (46 + 60 * np.exp(-tt * 18)) * tt) + 0.25 * rng.standard_normal(n) * np.exp(-tt * 60)) * np.exp(-tt * 7)
SFX = {"thud": (thud, 0.55), "whoosh": (whoosh, 0.35), "tick": (tick, 0.10), "pop": (pop, 0.12), "ding": (ding, 0.06), "swell": (swell_sfx, 0.5)}
for i, ev in enumerate(TL["sfx_beats"]):
    fn, g = SFX[ev["type"]]; add(fn(), T(ev["beat"]), pan=0.15 * ((i % 3) - 1), gain=g)
fade = np.clip(t / 0.06, 0, 1) * np.clip((DUR - t) / 1.2, 0, 1); mix *= fade[:, None]
mix *= 10 ** (-16 / 20) / max(np.sqrt(np.mean(mix ** 2)), 1e-9)
ceil = 10 ** (-1 / 20)
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
out = ROOT / "build" / "bgm.wav"; out.parent.mkdir(exist_ok=True)
with wave.open(str(out), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {out} ({DUR:.2f}s)")
