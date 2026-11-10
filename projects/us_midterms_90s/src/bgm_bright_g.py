"""Music for 《美国中期选举一次看懂》 — bright, bouncy G major to go with the elephant-and-donkey cartoon. numpy only, no sound effects, no vocals.

Layout (video beat = 60/66 s, music runs at double time = 132 BPM; one music bar = 2 video beats, one chord per 4-beat video bar):
  chords   G – D – Em – C, one per video bar
  melody   a 4-bar hook in the mid register (D4–D5) played on a marimba, the same every time it comes round
  bass     bouncy root / octave on every video beat
  drums    verse: soft pulse (kick on every video beat, rim on the dembow steps, offbeat hats)
           chorus: the full Euclidean groove — kick E(4,16), dembow snare, cinquillo hats
  DROP     video beat 44 (the Senate scale tips): two beats of breakdown (drums out, riser) then the full groove re-enters with a crash
  outro    drums out, a slow version of the hook, a final G chord
"""
import json, os, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "src" / "timeline.json").read_text())
SC, TOTAL = TL["scenes_beats"], TL["total_beats"]
SR, VBEAT = 44100, 60 / float(os.environ.get("VIDEO_BPM", TL["bpm"]))
INTRO, TB = TL["intro_seconds"], SC["D_title"][1]
def T(n): return n / TB * INTRO if n < TB else INTRO + (n - TB) * VBEAT
A0 = SC["A_what"][0]                       # first bar of the groove (video beat 4)
DROP = SC["E_senate"][0] + 6               # video beat 44
BREAK0 = DROP - 2
OUT0 = SC["J_end"][0]                      # outro starts with the last scene
STEP = 1 / 8                               # one 16th note in video beats
DUR = T(TOTAL) + TL["tail_seconds"]
N = int(DUR * SR); tt = np.arange(N) / SR; rng = np.random.default_rng(66)
BUS = {k: np.zeros((N, 2)) for k in ("lead", "keys", "drums", "bass", "pad", "fx")}

def add(bus, sig, start, pan=0.0, gain=1.0):
    i = int(round(start * SR))
    if i >= N: return
    sig = np.asarray(sig, float)
    if sig.ndim == 1: sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1)
    if i < 0: sig, i = sig[-i:], 0
    sig = sig[: N - i] * gain; BUS[bus][i:i + len(sig)] += sig
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def filt(x, lo=None, hi=None, order=4):
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1 / SR); H = np.ones_like(f)
    if hi: H /= 1 + (f / hi) ** order
    if lo: H /= 1 + (lo / np.maximum(f, 1e-3)) ** order
    return np.fft.irfft(X * (H[:, None] if x.ndim == 2 else H), n=len(x), axis=0)
def env(n, a=0.002, r=0.08):
    e = np.ones(n); na = max(1, min(n, int(a * SR))); nr = max(1, min(n, int(r * SR)))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def euclid(k, n, rot=0):
    pat = [((i * k) // n) != (((i - 1) * k) // n) if i else True for i in range(n)]
    return pat[-rot:] + pat[:-rot] if rot else pat

KICK = euclid(4, 16)                       # steps 0 4 8 12
DEMBOW = [i in (3, 6, 11, 14) for i in range(16)]
_c = euclid(5, 8); _c = _c[2:] + _c[:2]
CINQ = [i % 2 == 0 and _c[i // 2] for i in range(16)]

# ---------- instruments ----------
def marimba(m, dur=0.6, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 5.5) + 0.45 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 18) + 0.15 * np.sin(2 * np.pi * f * 10 * t) * np.exp(-t * 40)
    s += 0.18 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 9)
    return s * env(n, 0.002, 0.05) * vel
def pluck(m, dur=0.35, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m); ph = 2 * np.pi * f * t
    s = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)) * np.exp(-t * 9)
    return filt(s, hi=2600, order=2) * env(n, 0.003, 0.05) * vel
def bell(m, dur=1.6, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 2.2), (2.76, 0.35, 4), (5.4, 0.15, 8))) * env(n, 0.001, 0.2) * vel
def bass(m, dur=0.4, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; ph = 2 * np.pi * hz(m) * t
    return np.tanh(1.5 * (np.sin(ph) + 0.25 * np.sin(2 * ph))) * np.exp(-t * 4.5) * env(n, 0.004, 0.08) * vel
def warm_pad(notes, dur, cut=2200, att=0.3, rel=0.5):
    n = int(dur * SR); out = np.zeros((n, 2))
    for m in notes:
        for vi, d in enumerate((-0.08, -0.03, 0.03, 0.08)):
            f = hz(m) * 2 ** (d / 12); s = 2 * np.mod(np.cumsum(np.full(n, f) / SR) + rng.uniform(), 1.0) - 1; pan = (vi - 1.5) / 1.5 * 0.7
            out[:, 0] += s * np.sqrt(0.5 * (1 - pan)); out[:, 1] += s * np.sqrt(0.5 * (1 + pan))
    return filt(out, hi=cut, order=2) * env(n, att, rel)[:, None] / (len(notes) * 4) ** 0.5 / 2.6
def kick():
    n = int(0.4 * SR); t = np.arange(n) / SR
    return np.tanh(2.0 * np.sin(2 * np.pi * np.cumsum(48 + 100 * np.exp(-t * 30)) / SR) * np.exp(-t * 9)) * env(n, 0.0008, 0.04)
def rim():
    n = int(0.09 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1700 * t) * 0.6 + filt(rng.standard_normal(n), lo=2500) * 0.5) * np.exp(-t * 55)
def snare():
    n = int(0.22 * SR); t = np.arange(n) / SR
    return (filt(rng.standard_normal(n), lo=1500, hi=7000) * np.exp(-t * 22) * 0.8 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 28) * 0.5)
HH = filt(rng.standard_normal(int(0.3 * SR)), lo=7000); HH /= np.abs(HH).max()
def hat(open_=False):
    n = int((0.16 if open_ else 0.045) * SR); return HH[:n] * np.exp(-np.arange(n) / SR * (22 if open_ else 90))
def crash():
    n = int(2.4 * SR); t = np.arange(n) / SR; c = filt(rng.standard_normal((n, 2)), lo=3500); return c / np.abs(c).max() * np.exp(-t * 1.6)[:, None]

CH = {"G": [55, 59, 62, 67], "D": [57, 62, 66, 69], "Em": [55, 59, 64, 67], "C": [55, 60, 64, 67]}
ROOT_NOTE = {"G": 43, "D": 38, "Em": 40, "C": 36}
PROG = ["G", "D", "Em", "C"]
# the hook: (offset in video beats within the 4-beat bar, MIDI, length in video beats), all in D4–D5
HOOK = [
    [(0, 74, .5), (.5, 71, .5), (1, 67, .5), (1.5, 71, .5), (2, 74, 1), (3, 71, .5), (3.5, 74, .5)],
    [(0, 69, .5), (.5, 66, .5), (1, 62, .5), (1.5, 66, .5), (2, 69, 1), (3, 66, .5), (3.5, 69, .5)],
    [(0, 67, .5), (.5, 71, .5), (1, 74, .5), (1.5, 71, .5), (2, 71, 1), (3, 67, 1)],
    [(0, 64, .5), (.5, 67, .5), (1, 72, .5), (1.5, 71, .5), (2, 69, .5), (2.5, 67, .5), (3, 74, 1)],
]
OUTRO = [(0, 74, 1), (1, 71, 1), (2, 67, 2)]

# ---------- 0–1 s: title hit, the hook starts on the very first note ----------
add("pad", warm_pad(CH["G"], 1.6, cut=3500, att=0.02, rel=0.6), 0, gain=1.0)
add("drums", kick(), 0, gain=0.9); add("drums", crash(), 0, gain=0.3); add("bass", bass(43, 0.8), 0, gain=0.9)
add("lead", marimba(74, 0.7), 0.0, pan=-0.1, gain=0.9); add("lead", marimba(71, 0.6), T(0) + 0.45, pan=-0.1, gain=0.85)

# ---------- the groove, bar by bar ----------
bar = A0
while bar < OUT0:
    bi = ((bar - A0) // 4) % 4; chord = PROG[bi]; end = min(bar + 4, OUT0)
    chorus = bar >= DROP
    # pad under the whole bar (shut during the breakdown)
    pad_end = end                                  # the pad never stops: the breakdown is only drums + melody dropping out
    add("pad", warm_pad(CH[chord], (pad_end - bar) * VBEAT + 0.35, cut=1500 if bar < DROP else 2800, att=0.2), T(bar), gain=0.8 if not chorus else 1.0)
    # the hook (rests in the last two beats before the drop)
    for off, m, ln in HOOK[bi]:
        b = bar + off
        if BREAK0 <= b < DROP or b >= OUT0: continue
        add("lead", marimba(m, ln * VBEAT * 0.95 + 0.25), T(b), pan=-0.1, gain=0.85)
        if chorus: add("lead", bell(m + 12, 0.9, 0.55), T(b), pan=0.25, gain=0.3)
    # bass: root on every video beat, octave on the offbeat in the chorus
    for k in range(int(end - bar)):
        b = bar + k
        add("bass", bass(ROOT_NOTE[chord], 0.45), T(b), gain=0.5 if BREAK0 <= b < DROP else 0.8)
        if chorus: add("bass", bass(ROOT_NOTE[chord] + 12, 0.25, 0.7), T(b + 0.5), gain=0.6)
    # chord stabs on the offbeats of the chorus
    if chorus:
        for k in range(int(end - bar)):
            for j, m in enumerate(CH[chord][1:]):
                add("keys", pluck(m + 12, 0.28, 0.5), T(bar + k + 0.75) + j * 0.008, pan=-0.25 + 0.25 * j, gain=0.45)
    bar += 4

# ---------- drums: 16 steps per music bar = 2 video beats ----------
k = 0
while A0 + k * STEP < OUT0:
    b = A0 + k * STEP; step = k % 16; k += 1
    if BREAK0 <= b < DROP: continue
    chorus = b >= DROP
    if chorus:
        if KICK[step]: add("drums", kick(), T(b), gain=0.95)
        if DEMBOW[step]: add("drums", snare(), T(b), pan=0.1, gain=0.34)
        if CINQ[step]: add("drums", hat(), T(b), pan=0.3, gain=0.3)
        elif step % 2 == 1: add("drums", hat(), T(b), pan=-0.3, gain=0.1)
    else:
        if step in (0, 8): add("drums", kick(), T(b), gain=0.75)
        if DEMBOW[step] and b >= A0 + 8: add("drums", rim(), T(b), pan=0.2, gain=0.22)
        if step % 4 == 2: add("drums", hat(), T(b), pan=0.3, gain=0.16)
# breakdown riser and the re-entry
nb = int((T(DROP) - T(BREAK0)) * SR); u = np.arange(nb) / nb
nz = filt(rng.standard_normal((nb, 2)), lo=1800) * (u ** 2)[:, None]
add("fx", nz / np.abs(nz).max(), T(BREAK0), gain=0.3)
add("drums", crash(), T(DROP), gain=0.5); add("drums", kick(), T(DROP), gain=1.1); add("keys", bell(79, 2.0, 1.0), T(DROP), pan=0.2, gain=0.25)

# ---------- outro: the hook slowly, one last chord ----------
for off, m, ln in OUTRO:
    add("lead", marimba(m, ln * VBEAT + 0.8), T(OUT0 + off), pan=-0.1, gain=0.85)
for vb, notes, ln in ((OUT0, CH["G"], 4), (OUT0 + 4, [55, 59, 62, 67, 71], TOTAL - OUT0 - 4)):
    add("pad", warm_pad(notes, ln * VBEAT + 1.2, cut=2600, att=0.3, rel=1.2), T(vb), gain=1.0)
add("bass", bass(43, 3.0), T(OUT0), gain=0.8)
add("lead", marimba(74, 2.5), T(OUT0 + 4), pan=0.0, gain=0.8); add("keys", bell(86, 3.0, 1.0), T(OUT0 + 4), pan=0.2, gain=0.2)

# ---------- mix ----------
irn = int(1.2 * SR); it = np.arange(irn) / SR
ir = filt(rng.standard_normal((irn, 2)), lo=300, hi=7000) * np.exp(-it / 0.28)[:, None]; ir /= np.sqrt((ir ** 2).sum(axis=0))
send = BUS["lead"] * 0.5 + BUS["keys"] * 0.4 + BUS["pad"] * 0.3 + BUS["fx"] * 0.3
nf = 1 << (N + irn - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(send[:, c], nf) * np.fft.rfft(ir[:, c], nf), nf)[:N] for c in range(2)], 1)
mix = BUS["pad"] + BUS["lead"] * 1.1 + BUS["keys"] + BUS["drums"] + BUS["bass"] * 1.1 + BUS["fx"] + wet * 0.3
mix = filt(mix, lo=30, order=2); mix += 0.9 * filt(mix, lo=2500, order=2)   # a little air on top so the marimba and hats are not muffled
mix *= np.clip((DUR - tt) / 1.5, 0, 1)[:, None]
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-15.0 / 20) / max(rms, 1e-9)
ceil = 10 ** (-1 / 20)
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
outp = ROOT / "build" / os.environ.get("BGM_OUT", "bgm.wav"); outp.parent.mkdir(exist_ok=True)
with wave.open(str(outp), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {outp} ({DUR:.2f}s, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS, drop at {T(DROP):.2f}s)")
