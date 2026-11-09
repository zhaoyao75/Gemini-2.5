"""Music for 《美国中期选举一次看懂》 (adapted from ../douyin_vibe_all_nighter/src/bgm.py) — dark F-minor atmosphere, after the user's second reference recording. numpy only, no sound effects.

Reference (measured from the recording): ~113 BPM, thick sustained chords (F3 pedal, Eb4/F4/G4/Ab4/C5 = F minor),
very sparse rhythm (1–2 onsets/s), a deep kick every ~0.55 s over a sustained sub, a breakdown where sub and kick drop out
for ~2 s and then re-enter louder.
Here (video beat 66 BPM, so a quarter = 0.4545 s, 132 BPM):
  chords   Fm9 – Ebmaj9 – Fm9 – Abmaj7, one per video bar, warm detuned saws, slow filter
  melody   a slow 4-bar line on long notes (same every time):  F G Ab | G F Eb | F G C | C Ab G
  bass     sustained 808 on the chord root, ducked by the kick
  kick     every video beat in A–B, every half beat from C;  hats only offbeat, very soft
  DROP-2   breakdown: kick + sub drop out, chords filtered shut and rising, then DROP (80 mg crossing) = loud re-entry
  I–J      F major (the sun comes up), drums out, the melody once more, long final F
"""
import json, os, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "src" / "timeline.json").read_text())
SR, VBEAT = 44100, 60 / float(os.environ.get("VIDEO_BPM", TL["bpm"]))   # VIDEO_BPM=66 -> the music runs at 132 BPM
INTRO, TB = TL["intro_seconds"], TL["scenes_beats"]["D_title"][1]
def T(n): return n / TB * INTRO if n < TB else INTRO + (n - TB) * VBEAT
SC, TOTAL = TL["scenes_beats"], TL["total_beats"]
A0, C0, E0, I0 = (SC[k][0] for k in ("B_what", "C_power", "E_history", "L_end"))
DROP = SC["G_senate"][0] + 6                     # video beat 44: the 4th Senate flip pushes the reading past 51
STEP = 1 / 8                                     # one 16th of the double-time bar, in video beats
DUR = T(TOTAL) + TL["tail_seconds"]
N = int(DUR * SR); tt = np.arange(N) / SR; rng = np.random.default_rng(132)
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
    """Euclidean rhythm E(k,n): k hits spread as evenly as possible over n steps (Toussaint)"""
    pat = [((i * k) // n) != (((i - 1) * k) // n) if i else True for i in range(n)]
    return pat[-rot:] + pat[:-rot] if rot else pat

KICK = euclid(4, 16)
TRESILLO = [i % 2 == 0 and euclid(3, 8)[i // 2] for i in range(16)]
_c = euclid(5, 8); _c = _c[2:] + _c[:2]
CINQUILLO = [i % 2 == 0 and _c[i // 2] for i in range(16)]
DEMBOW = [i in (3, 6, 11, 14) for i in range(16)]
CQ_LEN = [4, 2, 4, 2, 4]                         # steps until the next cinquillo hit


KICK_STEP = 0.5                                              # half a video beat = one quarter at 132 BPM
def saw(f, n, phase=0.0):
    return 2 * np.mod(np.cumsum(np.broadcast_to(f, (n,)) / SR) + phase, 1.0) - 1
def warm_pad(notes, dur, cut=1800, att=0.35, rel=0.6):
    n = int(dur * SR); out = np.zeros((n, 2))
    for m in notes:
        for vi, d in enumerate((-0.09, -0.03, 0.03, 0.09)):
            s = saw(hz(m) * 2 ** (d / 12), n, rng.uniform()); pan = (vi - 1.5) / 1.5 * 0.7
            out[:, 0] += s * np.sqrt(0.5 * (1 - pan)); out[:, 1] += s * np.sqrt(0.5 * (1 + pan))
    out = filt(out, hi=cut, order=2) * env(n, att, rel)[:, None]
    return out / (len(notes) * 4) ** 0.5 / 2.2
def lead(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    f = hz(m) * (1 + 0.005 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.25) / 0.3, 0, 1)); ph = np.cumsum(f) / SR
    s = 0.6 * np.sin(2 * np.pi * ph) + 0.25 * (2 * np.mod(ph, 1) - 1) + 0.15 * (2 * np.mod(ph * 1.004, 1) - 1)
    s = filt(s, hi=2200, order=2) * env(n, 0.03, 0.3)
    return s / (np.abs(s).max() + 1e-9)
def kick():
    n = int(0.45 * SR); t = np.arange(n) / SR
    return np.tanh(2.0 * np.sin(2 * np.pi * np.cumsum(46 + 110 * np.exp(-t * 28)) / SR) * np.exp(-t * 8)) * env(n, 0.0008, 0.04)
def sub(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; ph = 2 * np.pi * hz(m) * t
    return np.tanh(1.6 * (np.sin(ph) + 0.2 * np.sin(2 * ph))) * env(n, 0.01, 0.12)
HH = filt(rng.standard_normal(int(0.3 * SR)), lo=7000); HH /= np.abs(HH).max()
def hat():
    n = int(0.05 * SR); return HH[:n] * np.exp(-np.arange(n) / SR * 80)
def crash():
    n = int(2.6 * SR); t = np.arange(n) / SR; c = filt(rng.standard_normal((n, 2)), lo=3500); return c / np.abs(c).max() * np.exp(-t * 1.5)[:, None]
def bell(m, dur=3.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 1.2), (2.76, 0.4, 2.5), (5.4, 0.2, 5))) * env(n, 0.001, 0.2)

PROG = ["Fm9", "Eb", "Fm9", "Ab"]
CH = {"Fm9": [53, 56, 60, 63, 67], "Eb": [51, 55, 58, 62, 65], "Ab": [56, 60, 63, 67]}
ROOTS = {"Fm9": 41, "Eb": 39, "Ab": 44}
# melody: (start offset in video beats within the 4-beat bar, MIDI note, length in video beats)
LINE = [[(0, 65, 2), (2, 67, 1), (3, 68, 1)],
        [(0, 67, 2), (2, 65, 1), (3, 63, 1)],
        [(0, 65, 2), (2, 67, 1), (3, 72, 1)],
        [(0, 72, 2), (2, 68, 1), (3, 67, 1)]]
def level(b, pts): xs, ys = zip(*pts); return float(np.interp(b, xs, ys))
BREAK0 = DROP - 2                                            # the breakdown starts two video beats before the crossing

# ---------- 0–1 s: chord swell + boom ----------
add("pad", warm_pad(CH["Fm9"], 1.4, cut=3500, att=0.02, rel=0.6), 0, gain=1.0)
add("bass", sub(29, 1.2), 0, gain=0.9); add("drums", kick(), 0, gain=0.9); add("drums", crash(), 0, gain=0.3)

# ---------- A .. I ----------
for bar in range(A0, I0, 4):
    bi = ((bar - A0) // 4) % 4; c = PROG[bi]; end = min(bar + 4, I0); drop = bar >= DROP
    in_break = lambda b: BREAK0 <= b < DROP
    # pad: whole bar; closed + rising in the breakdown
    for seg_start, seg_end in ((bar, min(end, BREAK0)) if bar < BREAK0 < end else (bar, end),) if not (bar < BREAK0 < end) else ((bar, BREAK0), (BREAK0, end)):
        if seg_end <= seg_start: continue
        cut = 650 if in_break(seg_start) else (2600 if drop else 1500)
        add("pad", warm_pad(CH[c], (seg_end - seg_start) * VBEAT + 0.4, cut=cut, att=0.25 if not drop else 0.05), T(seg_start), gain=level(seg_start, [(A0, 0.6), (C0, 0.75), (E0, 0.9), (DROP, 1.15)]))
    # melody on long notes
    for off, m, ln in LINE[bi]:
        b = bar + off
        if b >= I0: continue
        add("lead", lead(m, ln * VBEAT * 0.97), T(b), pan=-0.1, gain=level(b, [(A0, 0.7), (DROP, 0.85)]))
        if drop: add("lead", lead(m + 12, ln * VBEAT * 0.97), T(b), pan=0.2, gain=0.3)
    # sustained sub on the root (out during the breakdown)
    for k in range(int((end - bar))):
        b = bar + k
        if in_break(b) or b >= I0: continue
        add("bass", sub(ROOTS[c], VBEAT * 1.0), T(b), gain=0.85)
# kick (sparse in A–B, every quarter from C), hats offbeat from C
k = 0
while A0 + k * KICK_STEP < I0:
    b = A0 + k * KICK_STEP; k += 1
    if BREAK0 <= b < DROP: continue
    if b < C0 and b % 1: continue
    add("drums", kick(), T(b), gain=level(b, [(A0, 0.7), (C0, 0.85), (DROP, 1.0)]))
    if b >= C0 and (b % 1) == 0.5: add("drums", hat(), T(b), pan=0.3, gain=0.35)
# breakdown riser, re-entry hit
nb = int((T(DROP) - T(BREAK0)) * SR); u = np.arange(nb) / nb
nz = filt(rng.standard_normal((nb, 2)), lo=1500) * (u ** 2)[:, None]
add("fx", nz / np.abs(nz).max(), T(BREAK0), gain=0.3)
add("drums", crash(), T(DROP), gain=0.5); add("drums", kick(), T(DROP), gain=1.1); add("keys", bell(79), T(DROP), pan=0.2, gain=0.25)

# ---------- I–J: F major, drums out, the line once more ----------
for vb, root, notes, ln in ((I0, 41, [53, 57, 60, 64], 2), (I0 + 2, 36, [55, 60, 64, 67], 2), (I0 + 4, 41, [53, 57, 60, 64], TOTAL - I0 - 4)):
    add("pad", warm_pad(notes, ln * VBEAT + 1.2, cut=2400, att=0.3, rel=1.2), T(vb), gain=0.95)
    add("bass", sub(root, ln * VBEAT), T(vb), gain=0.7)
add("drums", crash(), T(I0), gain=0.25)
END = [(0, 65, 2), (2, 67, 1), (3, 69, 1), (4, 67, 2), (6, 65, 1), (7, 64, 1), (8, 65, 3)]   # F G A | G F E | F (long)
for off, m, ln in END:
    b = I0 + off
    if b < TOTAL: add("lead", lead(m, min(ln, TOTAL - b) * VBEAT * (1.0 if ln == 3 else 0.97) + (1.0 if ln == 3 else 0)), T(b), pan=-0.1, gain=0.75)

# ---------- mix ----------
irn = int(1.6 * SR); it = np.arange(irn) / SR
ir = filt(rng.standard_normal((irn, 2)), lo=300, hi=7000) * np.exp(-it / 0.35)[:, None]; ir /= np.sqrt((ir ** 2).sum(axis=0))
send = BUS["lead"] * 0.5 + BUS["keys"] * 0.4 + BUS["pad"] * 0.35 + BUS["fx"] * 0.3
nf = 1 << (N + irn - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(send[:, c], nf) * np.fft.rfft(ir[:, c], nf), nf)[:N] for c in range(2)], 1)
sc = np.ones(N)                                               # sidechain: pad / lead / sub duck on every kick
k = 0
while A0 + k * KICK_STEP < I0:
    b = A0 + k * KICK_STEP; k += 1
    if BREAK0 <= b < DROP or (b < C0 and b % 1): continue
    i = int(T(b) * SR); n = min(int(0.25 * SR), N - i); e = np.arange(n) / SR
    sc[i:i + n] = np.minimum(sc[i:i + n], 1 - 0.4 * np.exp(-e / 0.08))
for bus in ("pad", "lead"): BUS[bus] *= sc[:, None]
BUS["bass"] *= (0.5 + 0.5 * sc)[:, None]
BUS["bass"] = filt(BUS["bass"], lo=28, order=2)
mix = BUS["pad"] + BUS["lead"] * 1.2 + BUS["keys"] + BUS["drums"] + BUS["bass"] * 1.1 + BUS["fx"] + wet * 0.35
mix = filt(mix, lo=28, order=2); mix += 0.9 * filt(mix, lo=2500, order=2)
mix *= np.clip((DUR - tt) / 1.5, 0, 1)[:, None]
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-15.0 / 20) / max(rms, 1e-9)
ceil = 10 ** (-1 / 20)
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
outp = ROOT / "build" / os.environ.get("BGM_OUT", "bgm.wav"); outp.parent.mkdir(exist_ok=True)
with wave.open(str(outp), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {outp} ({DUR:.2f}s, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS, crossing at {T(DROP):.2f}s)")
