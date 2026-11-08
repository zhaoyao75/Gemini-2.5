"""15s gentle Chinese-style background track (original). Additive pluck + string pad + convolution reverb."""
import numpy as np, wave, sys

SR = 44100
DUR = 15.0
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(11)

NOTE = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}
def hz(n):
    name, octv = n[:-1], int(n[-1])
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octv + 1) - 69) / 12)

def place(sig, t, pan=0.0, gain=1.0):
    s = int(t * SR); e = min(N, s + len(sig))
    if s >= N: return
    seg = sig[:e - s] * gain
    L[s:e] += seg * np.sqrt(0.5 * (1 - pan)); R[s:e] += seg * np.sqrt(0.5 * (1 + pan))

def pluck(f, dur, bright=1.0, vib=0.0):
    """Clean plucked-string tone: decaying harmonics, higher ones fade faster."""
    n = int(SR * dur); t = np.arange(n) / SR
    # optional guzheng-style vibrato after the attack
    if vib:
        depth = vib * np.clip((t - 0.35) / 0.4, 0, 1)
        fm = 1 + depth * np.sin(2 * np.pi * 5.2 * t)
        phase = 2 * np.pi * f * np.cumsum(fm) / SR
    else:
        phase = 2 * np.pi * f * t
    y = np.zeros(n)
    for k in range(1, 11):
        if f * k > 9000: break
        a = (1 / k ** 1.3) * abs(np.sin(np.pi * k * 0.18)) * (bright ** (k - 1))
        tau = 1.6 / (1 + 0.7 * (k - 1))
        y += a * np.sin(k * phase * (1 + 0.0004 * (k - 1))) * np.exp(-t / tau)
    att = np.clip(t / 0.004, 0, 1)
    rel = np.clip((dur - t) / 0.08, 0, 1)
    return y * att * rel

def pad(freqs, dur):
    """Soft string pad: detuned voices, slow swell."""
    n = int(SR * dur); t = np.arange(n) / SR
    y = np.zeros(n)
    for f in freqs:
        for det in (-0.004, 0.0, 0.004):
            ph = 2 * np.pi * f * (1 + det) * t + rng.uniform(0, 6.28)
            y += np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    env = np.minimum(np.clip(t / 1.2, 0, 1), np.clip((dur - t) / 1.0, 0, 1))
    return y * env / (len(freqs) * 3)

def bass(f, dur):
    n = int(SR * dur); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    return y * np.exp(-t / 1.8) * np.clip(t / 0.01, 0, 1) * np.clip((dur - t) / 0.2, 0, 1)

BEAT = 60 / 64  # 64 bpm, 4 beats per bar, 4 bars = 15s
BAR = 4 * BEAT
chords = [  # (start bar offset in beats, notes for arpeggio, pad notes, bass)
    (0,  ['D3','A3','D4','F#4','A4','F#4','D4','A3'], ['D3','F#3','A3'], 'D2'),
    (4,  ['B2','F#3','B3','D4','F#4','D4','B3','F#3'], ['B2','D3','F#3'], 'B1'),
    (8,  ['G2','D3','G3','B3','D4','B3','G3','D3'],   ['G2','B2','D3'], 'G1'),
    (12, ['A2','E3','A3','C#4'],                       ['A2','C#3','E3'], 'A1'),
    (14, ['D3','A3','D4','F#4'],                       ['D3','F#3','A3'], 'D2'),
]
for beat0, arp, padn, b in chords:
    t0 = beat0 * BEAT
    span = (len(arp) / 2) * BEAT
    for i, n in enumerate(arp):  # eighth-note harp arpeggio
        place(pluck(hz(n), 2.2, bright=0.8), t0 + i * BEAT / 2, pan=-0.35 + 0.1 * (i % 3), gain=0.16)
    place(pad([hz(x) for x in padn], span + 1.0), t0, pan=0.0, gain=0.10)
    place(bass(hz(b), span), t0, gain=0.22)

melody = [  # (beat, note, beats)  D major pentatonic
    (0,'F#5',1),(1,'E5',.5),(1.5,'D5',.5),(2,'A4',2),
    (4,'B4',1),(5,'D5',1),(6,'F#5',1),(7,'E5',1),
    (8,'D5',1.5),(9.5,'B4',.5),(10,'A4',1),(11,'B4',1),
    (12,'A4',1),(13,'E5',1),(14,'D5',2),
]
for b0, n, dur in melody:
    d = max(dur * BEAT + 1.2, 1.6)
    place(pluck(hz(n), d, bright=0.9, vib=0.006 if dur >= 1 else 0.0), b0 * BEAT, pan=0.2, gain=0.30)

# final soft glissando-like ripple
for k, n in enumerate(['D4','E4','F#4','A4','B4','D5','E5','F#5']):
    place(pluck(hz(n), 1.4, bright=0.7), 14 * BEAT + 0.35 + k * 0.045, pan=0.3, gain=0.07)

# convolution reverb (synthetic hall IR)
def ir(seed):
    n = int(SR * 2.4); t = np.arange(n) / SR
    noise = np.random.default_rng(seed).standard_normal(n)
    k = 12; noise = np.convolve(noise, np.ones(k) / k, mode='same')  # darken
    h = noise * np.exp(-t / 0.55)
    h[: int(SR * 0.012)] = 0  # pre-delay
    return h / np.sqrt(np.sum(h ** 2))
def conv(x, h):
    m = len(x) + len(h) - 1; nfft = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(h, nfft), nfft)[:len(x)]
wetL, wetR = conv(L, ir(1)), conv(R, ir(2))
mixL = L + 0.28 * wetL; mixR = R + 0.28 * wetR

st = np.stack([mixL, mixR], 1)
fi, fo = int(SR * 0.6), int(SR * 1.8)
st[:fi] *= np.linspace(0, 1, fi)[:, None]
st[-fo:] *= (np.linspace(1, 0, fo) ** 2)[:, None]
st = np.tanh(st / np.max(np.abs(st)) * 1.1) / np.tanh(1.1) * 0.89  # gentle soft-clip/limit
pcm = (st * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok')
