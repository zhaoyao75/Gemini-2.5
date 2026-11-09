"""Synthesize the BGM + SFX for the hot-hand video with numpy, aligned to timeline.json beats.

BPM and section beats come from timeline.json. A minor (Am-F-C-G). Title: pad swell, no drums.
Cards/network: half-time kick. Mechanism: piano chords each bar + kick every beat; arpeggio in the last part. Writes build/bgm.wav.
"""
import json, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "src" / "timeline.json").read_text())
SR = 44100
BEAT = 60 / TL["bpm"]
INTRO, TB = TL["intro_seconds"], TL["scenes_beats"]["D_title"][1]
def T(n):  # beat -> seconds; the title card is INTRO long, the beat grid starts right after it
    return n / TB * INTRO if n < TB else INTRO + (n - TB) * BEAT
DUR = T(TL["total_beats"]) + TL["tail_seconds"]
N = int(DUR * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(42)
mix = np.zeros((N, 2))

def hz(midi): return 440.0 * 2 ** ((midi - 69) / 12)
def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    mix[i:i + len(sig), 0] += sig * np.sqrt(0.5 * (1 - pan))
    mix[i:i + len(sig), 1] += sig * np.sqrt(0.5 * (1 + pan))
def env(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e

CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
BAR = 4 * BEAT
n_bars = int(np.ceil(TL["total_beats"] / 4))

# pad: detuned soft saw-ish stack, slow attack, one chord per bar
for bar in range(n_bars):
    start = T(bar * 4)
    n = int((T(bar * 4 + 4) - start + 0.8) * SR); tt = np.arange(n) / SR
    sig = np.zeros(n)
    for m in CHORDS[bar % 4] + [CHORDS[bar % 4][0] - 12]:
        for det in (-0.12, 0.12):
            f = hz(m) * 2 ** (det / 12)
            for h, amp in ((1, 1.0), (2, 0.35), (3, 0.15)):
                sig += amp * np.sin(2 * np.pi * f * h * tt + rng.uniform(0, 6.28))
    sig *= env(n, 0.05 if bar == 0 else 0.9, 0.9) * 0.018
    # title swell (beats 15-22) and final fade
    add(sig, start, gain=1.0)
SC = TL["scenes_beats"]
D0, A0, C0, E0, F10, F20, J0, K0, L0 = 0, SC["A_hook"][0], SC["C_1985"][0], SC["E_twist"][0], SC["F1_rules"][0], SC["F2_table"][0], SC["J_caveat"][0], SC["K_landing"][0], SC["L_end"][0]
TOTAL = TL["total_beats"]

def piano(midi, dur=2.6, vel=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR; f = hz(midi)
    s = sum(a * np.sin(2 * np.pi * f * h * tt) * np.exp(-tt * (2.2 + h * 1.4)) for h, a in ((1, 1), (2, .45), (3, .22), (4, .1)))
    return s * np.minimum(1, tt / 0.004) * vel

# single piano notes on scene changes
for beat, m in ((D0, 69), (A0, 74), (C0, 72), (F10, 76), (K0, 69), (L0, 76)):
    add(piano(m, 3.5, 0.16), T(beat), pan=0.1)
# mechanism (coin table -> benchmark): a piano chord every bar, arpeggio from the table on; softer after the caveat
for beat in range(F10, TOTAL, 4):
    ch = CHORDS[(beat // 4) % 4]
    vel = 0.07 if beat < J0 else 0.05
    for k, m in enumerate(ch):
        add(piano(m + 12, 3.0, vel), T(beat) + k * 0.012, pan=-0.2 + 0.2 * k)
for k in range(int((J0 - F20) * 2)):
    beat = F20 + k / 2
    ch = CHORDS[(int(beat) // 4) % 4]
    add(piano(ch[k % 3] + 24, 1.2, 0.04), T(beat), pan=0.3 * np.sin(k))

def kick():
    n = int(0.35 * SR); tt = np.arange(n) / SR
    f = 50 + 70 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)
for beat in range(A0, J0):
    half = beat < E0 and (beat - A0) % 2 == 0      # intro: half-time pulse
    full = beat >= F10                              # coin table onwards: every beat; none during the twist (E) or after J
    if half or full:
        add(kick(), T(beat), gain=0.24 if full else 0.16)

# SFX
def whoosh():
    n = int(1.1 * SR); tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # crude band sweep: moving average of decreasing width
    out = np.zeros(n)
    for i, w in enumerate(np.linspace(40, 4, 8)):
        seg = slice(int(i * n / 8), int((i + 1) * n / 8))
        out[seg] = np.convolve(noise, np.ones(int(w)) / w, mode="same")[seg]
    return out * np.sin(np.pi * tt / tt[-1]) ** 2
def tick():
    n = int(0.12 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 60)
def pop():
    n = int(0.15 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (900 + 500 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 35)
def ding():
    return piano(88, 2.5, 1.0) + 0.5 * piano(95, 2.5, 1.0)
def swell_sfx():
    n = int(2.2 * SR); tt = np.arange(n) / SR
    return np.convolve(rng.standard_normal(n), np.ones(60) / 60, mode="same") * (tt / tt[-1]) ** 2 * np.exp(-np.maximum(0, tt - 1.9) * 30)
def thud():
    n = int(0.6 * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * (46 + 60 * np.exp(-tt * 18)) * tt) + 0.25 * rng.standard_normal(n) * np.exp(-tt * 60)) * np.exp(-tt * 7)
SFX = {"thud": (thud, 0.55), "whoosh": (whoosh, 0.35), "tick": (tick, 0.10), "pop": (pop, 0.12), "ding": (ding, 0.06), "swell": (swell_sfx, 0.5)}
for i, ev in enumerate(TL["sfx_beats"]):
    fn, g = SFX[ev["type"]]
    add(fn(), T(ev["beat"]), pan=0.15 * ((i % 3) - 1), gain=g)

# master: fade in/out, normalise to -1 dBFS peak, gentle RMS target
fade = np.clip(t / 0.06, 0, 1) * np.clip((DUR - t) / 1.2, 0, 1)
mix *= fade[:, None]
rms = np.sqrt(np.mean(mix ** 2))
mix *= 10 ** (-16 / 20) / max(rms, 1e-9)          # push level up ...
ceil = 10 ** (-1 / 20)                              # ... then soft-limit peaks to -1 dBFS
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
out = ROOT / "build" / "bgm.wav"
out.parent.mkdir(exist_ok=True)
with wave.open(str(out), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {out} ({DUR:.2f}s, peak {20*np.log10(np.max(np.abs(mix))):.1f} dBFS, rms {20*np.log10(np.sqrt(np.mean(mix**2))):.1f} dBFS)")
