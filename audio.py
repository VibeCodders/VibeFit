"""Musica ed effetti sonori sintetizzati dal codice (nessun file esterno, nessun copyright).

I WAV vengono generati una volta in assets/audio/ e poi caricati da Panda3D.
"""
import pathlib
import wave

import numpy as np
from panda3d.core import Filename

SR = 22050
from paths import DATA_DIR

OUT = DATA_DIR / "assets" / "audio"

NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def freq(name):
    """'A4' -> Hz."""
    base, octave = name[:-1], int(name[-1])
    midi = 12 * (octave + 1) + NOTE[base]
    return 440.0 * 2 ** ((midi - 69) / 12)


def _env(n, attack=0.005, release=0.08):
    e = np.ones(n)
    a, r = max(int(attack * SR), 1), max(int(release * SR), 1)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, min(r, n))
    return e


def tone(f, dur, shape="square", vol=0.3, f_end=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    fs = np.linspace(f, f_end if f_end else f, n)
    phase = 2 * np.pi * np.cumsum(fs) / SR
    if shape == "square":
        w = np.sign(np.sin(phase)) * 0.7
    elif shape == "triangle":
        w = 2 / np.pi * np.arcsin(np.sin(phase))
    elif shape == "noise":
        w = np.random.uniform(-1, 1, n)
    else:
        w = np.sin(phase)
    return w * _env(n) * vol


def silence(dur):
    return np.zeros(int(dur * SR))


def seq(notes, shape="square", vol=0.3):
    """notes: lista di (nota o None, durata in secondi)."""
    return np.concatenate([tone(freq(n), d, shape, vol) if n else silence(d) for n, d in notes])


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = np.zeros(n)
    for t in tracks:
        out[:len(t)] += t
    return out


def save(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    data = np.clip(data, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------- effetti sonori ----------
def make_sfx():
    save("click", tone(880, 0.06, "square", 0.25))
    save("ok", seq([("E5", 0.07), ("A5", 0.12)], "square", 0.25))
    save("coin", seq([("B5", 0.06), ("E6", 0.2)], "square", 0.22))
    save("fail", tone(330, 0.35, "triangle", 0.4, f_end=110))
    save("bump", tone(140, 0.18, "noise", 0.4) * 0.6 + tone(120, 0.18, "triangle", 0.4, f_end=60))
    save("whoosh", tone(0, 0.35, "noise", 0.18) * np.linspace(0, 1, int(0.35 * SR)) ** 0.5)
    save("beep", tone(660, 0.12, "square", 0.3))
    save("go", tone(1320, 0.4, "square", 0.3))
    save("splash", tone(0, 0.45, "noise", 0.3) * np.exp(-np.linspace(0, 6, int(0.45 * SR))))
    save("jump", tone(300, 0.2, "square", 0.25, f_end=700))
    save("medal", seq([("C5", 0.12), ("E5", 0.12), ("G5", 0.12), ("C6", 0.35)], "square", 0.28))
    save("rep", seq([("G5", 0.05), ("C6", 0.12)], "triangle", 0.4))


# ---------- musiche ----------
def _drums(beats, bpm):
    """Cassa su ogni movimento e charleston sugli ottavi: base ritmica per la danza."""
    beat = 60.0 / bpm
    kick = tone(110, 0.14, "sine", 0.55, f_end=45)
    hat = tone(0, 0.04, "noise", 0.12)
    out = np.zeros(int(beats * beat * SR) + SR // 2)
    for i in range(int(beats * 2)):
        start = int(i * beat / 2 * SR)
        if i % 2 == 0:
            out[start:start + len(kick)] += kick
        else:
            out[start:start + len(hat)] += hat
    return out


def _loop(melody, bass, bpm, bars, mel_shape="square", bass_shape="triangle", drums=False):
    beat = 60.0 / bpm
    m = seq([(n, d * beat) for n, d in melody], mel_shape, 0.16)
    b = seq([(n, d * beat) for n, d in bass], bass_shape, 0.28)
    tracks = [m, b]
    if drums:
        total_beats = sum(d for _, d in bass)
        tracks.append(_drums(total_beats, bpm)[:len(b)])
    return mix(*tracks)


def make_music():
    # Menu: allegro, DO maggiore
    mel = [("C5", .5), ("E5", .5), ("G5", .5), ("E5", .5), ("A5", .5), ("G5", .5), ("E5", .5), ("C5", .5),
           ("D5", .5), ("F5", .5), ("A5", .5), ("F5", .5), ("G5", 1), ("E5", .5), ("D5", .5)] * 2
    bass = [("C3", 2), ("G3", 2), ("A3", 2), ("F3", 2)] * 2
    save("music_menu", _loop(mel, bass, 120, 8))
    # Azione: piu' veloce, LA minore
    mel = [("A4", .25), ("C5", .25), ("E5", .25), ("A5", .25), ("G5", .25), ("E5", .25), ("C5", .25), ("E5", .25),
           ("F5", .25), ("A5", .25), ("C6", .25), ("A5", .25), ("G5", .25), ("E5", .25), ("D5", .25), ("E5", .25)] * 2
    bass = [("A2", .5), ("A3", .5), ("A2", .5), ("A3", .5), ("F2", .5), ("F3", .5), ("G2", .5), ("G3", .5)] * 2
    save("music_action", _loop(mel, bass, 150, 4, "square", "square"))
    # Calma: lenta, morbida
    mel = [("E5", 2), ("G5", 1), ("A5", 1), ("G5", 2), ("D5", 2), ("C5", 2), ("E5", 1), ("D5", 1), ("C5", 4)]
    bass = [("C3", 4), ("G2", 4), ("A2", 4), ("F2", 4)]
    save("music_calm", _loop(mel, bass, 72, 4, "sine", "sine"))
    # Danza: 120 bpm (un movimento ogni 0,5 s), DO maggiore con batteria. La danza si sincronizza su questo.
    bars = (("E5", "G5", "C6"), ("F5", "A5", "C6"), ("G5", "B5", "D6"), ("A5", "C6", "E6"))
    mel = []
    for a, b, c in bars:
        mel += [(a, .5), (b, .5), (c, .5), (b, .5), (a, .5), (b, .5), (c, 1.0)]
    bass = []
    for r, f in (("C3", "G3"), ("F3", "C3"), ("G3", "D3"), ("A3", "E3")):
        bass += [(r, 1), (f, 1), (r, 1), (f, 1)]
    save("music_dance", _loop(mel, bass, 120, 16, "square", "triangle", drums=True))
    # Mare: lento e sognante, per la pesca delle perle
    mel = [("A4", 2), ("C5", 1), ("E5", 1), ("D5", 2), ("C5", 2), ("E5", 2), ("D5", 1), ("C5", 1), ("A4", 4)]
    bass = [("A2", 4), ("F2", 4), ("C3", 4), ("G2", 4)]
    save("music_sea", _loop(mel, bass, 90, 16, "sine", "sine"))
    # Tensione: staccato in minore, per la fune
    mel = []
    for n1, n2, n3 in (("E4", "G4", "A4"), ("D4", "F4", "G4"), ("C4", "E4", "F4")):
        mel += [(n1, .5), (None, .5), (n1, .5), (n2, .5), (n3, .5), (None, .5), (n2, .5), (n1, .5)]
    mel += [("B3", .5), (None, .5), ("B3", .5), ("D4", .5), ("E4", 1.0), (None, 1.0)]
    bass = []
    for r in ("E2", "D2", "C2", "B1"):
        bass += [(r, 1), (r, 1), (r[0] + str(int(r[1]) + 1), 1), (r, 1)]
    save("music_tension", _loop(mel, bass, 110, 16, "square", "triangle"))


MUSIC_TRACKS = ("menu", "action", "calm", "dance", "sea", "tension")


def generate_all(force=False):
    if force or not all((OUT / f"music_{n}.wav").exists() for n in MUSIC_TRACKS):
        make_sfx()
        make_music()


class Sound:
    """Gestione riproduzione: effetti, musica in loop, volume."""

    def __init__(self, loader):
        generate_all()
        self.loader = loader
        fn = lambda p: Filename.fromOsSpecific(str(p))  # noqa: E731
        self.sfx = {p.stem: loader.loadSfx(fn(p)) for p in OUT.glob("*.wav") if not p.stem.startswith("music")}
        self.tracks = {p.stem[6:]: loader.loadMusic(fn(p)) for p in OUT.glob("music_*.wav")}
        self.current = None
        self.muted = False

    def play(self, name):
        if not self.muted and name in self.sfx:
            self.sfx[name].play()

    def music(self, name):
        if name == self.current:
            return
        if self.current:
            self.tracks[self.current].stop()
        self.current = name
        if name and not self.muted:
            m = self.tracks[name]
            m.setLoop(True)
            m.setVolume(0.5)
            m.play()

    def toggle_mute(self):
        self.muted = not self.muted
        cur, self.current = self.current, None
        if self.muted and cur:
            self.tracks[cur].stop()
        else:
            self.music(cur)


if __name__ == "__main__":
    generate_all(force=True)
    print("generati:", sorted(p.name for p in OUT.glob("*.wav")))
