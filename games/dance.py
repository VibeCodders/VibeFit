"""Danza del pinguino: a tempo di musica sposta il peso sulla pedana illuminata."""
import math
import random

from fx import make_shadow
from gamekit import Game, blob, box, make_penguin, perspective, set_flippers

BPM = 120.0  # come la musica 'dance'
BEAT = 60.0 / BPM
LEAD_IN = 2.0  # secondi prima del primo segnale

# direzione -> (dx, dy sulla scena, colore)
PADS = {
    "left": ((-4.2, 0.0), (0.3, 0.5, 0.95)),
    "right": ((4.2, 0.0), (0.95, 0.3, 0.3)),
    "front": ((0.0, 2.7), (0.35, 0.85, 0.45)),
    "back": ((0.0, -2.7), (0.98, 0.8, 0.2)),
}
NAMES = {"left": "SINISTRA", "right": "DESTRA", "front": "AVANTI", "back": "INDIETRO"}


class Dance(Game):
    key = "dance"
    title = "Danza del pinguino"
    blurb = "A tempo di musica sposta il peso sulla pedana che si illumina"
    music = "dance"
    met = 5.0
    duration = 46.0

    def setup(self):
        d = self.diff
        self.every = (4, 2, 2)[d] * BEAT  # tempo fra due segnali
        self.thx = (45.0, 60.0, 85.0)[d]  # mm a destra/sinistra
        self.thy = (30.0, 40.0, 55.0)[d]  # mm avanti/indietro
        self.window = (0.45, 0.3, 0.2)[d]  # tolleranza prima del segnale (s)
        perspective(self.app, 55)
        self.app.setBackgroundColor(0.12, 0.08, 0.22, 1)
        self.app.camera.setPos(0, -9.5, 14)
        self.app.camera.lookAt(0, 0.2, 0)
        L = self.loader
        box(self.root, L, (16, 10, 0.3), (0.2, 0.15, 0.3), (0, 0, -0.2))  # palco
        self.tiles = []
        for ix in range(-3, 4):
            for iy in range(-2, 3):
                t = box(self.root, L, (1.0, 1.0, 0.04), (0.28, 0.22, 0.4), (ix * 1.1, iy * 1.05, 0.02))
                self.tiles.append(t)
        self.pads = {}
        for k, ((x, y), col) in PADS.items():
            pad = blob(self.root, L, (1.5, 1.3, 0.1), tuple(c * 0.45 for c in col), (x, y, 0.08))
            ring = blob(self.root, L, (1.5, 1.3, 0.05), col, (x, y, 0.2))
            ring.setTransparency(True)
            ring.setColor(*col, 0.0)
            ring.setLightOff()
            self.pads[k] = {"node": pad, "ring": ring, "col": col, "pos": (x, y)}
        for i in range(5):  # luci da discoteca sul fondo
            b = blob(self.root, L, (0.5, 0.5, 0.5), (1, 1, 1), (-6 + i * 3, 6.5, 2.2))
            b.setLightOff()
            self.tiles.append(b)
        self.lights = self.tiles[-5:]
        self.shadow = make_shadow(self.root, L, 0.7)
        self.peng = make_penguin(self.root, L)
        self.peng.setScale(0.75)
        self.peng.setH(180)
        self.t = 0.0
        self.cues = []  # {T, dir, best, done}
        n = int((self.duration - LEAD_IN - 1.5) / self.every)
        last = None
        for i in range(n):
            choices = [k for k in PADS if k != last]
            last = random.choice(choices)
            self.cues.append({"T": LEAD_IN + i * self.every, "dir": last, "best": 0.0, "done": False})
        self.n_cues = len(self.cues)
        self.combo = 0
        self.hits = 0
        self.pos = [0.0, 0.0]
        self.msg_t = 0.0
        self.hud_msg["text"] = "Preparati..."

    def medals(self):
        n = max(self.n_cues, 1)
        return (0.4 * n * 100, 0.65 * n * 100, 0.85 * n * 100)

    def _proj(self, d, inp):
        return {"left": -inp.x / self.thx, "right": inp.x / self.thx,
                "front": inp.y / self.thy, "back": -inp.y / self.thy}[d]

    def update(self, dt, inp):
        self.t += dt
        beat_phase = (self.t % BEAT) / BEAT
        for i, b in enumerate(self.lights):  # le luci pulsano a tempo
            col = list(PADS.values())[i % 4][1]
            k = 0.5 + 0.5 * (1 - beat_phase)
            b.setColor(col[0] * k, col[1] * k, col[2] * k, 1)
        pulse = 1.0 - beat_phase
        for k, p in self.pads.items():
            p["ring"].setColor(*p["col"], 0.0)
        # animazione del pinguino: si sposta leggermente nella direzione del baricentro e balla
        tx, ty = inp.x * 0.012, inp.y * 0.012
        self.pos[0] += (tx - self.pos[0]) * min(1.0, 8 * dt)
        self.pos[1] += (ty - self.pos[1]) * min(1.0, 8 * dt)
        hop = abs(math.sin(self.t * math.pi / BEAT)) * 0.25
        self.peng.setPos(self.pos[0], self.pos[1], hop)
        set_flippers(self.peng, 90 + 60 * math.sin(self.t * math.pi / BEAT), side=1)
        set_flippers(self.peng, 90 - 60 * math.sin(self.t * math.pi / BEAT), side=-1)
        self.peng.setH(180 + 12 * math.sin(self.t * math.pi / BEAT))
        self.shadow.setPos(self.pos[0], self.pos[1], 0.05)

        for c in self.cues:
            if c["done"]:
                continue
            T, w = c["T"], self.window
            appr = T - self.t  # secondi al segnale
            pad = self.pads[c["dir"]]
            if -0.15 <= appr <= self.every:
                # anello che si stringe sulla pedana fino al momento giusto
                grow = 1.0 + 1.6 * max(min(appr / self.every, 1.0), 0.0)
                pad["ring"].setScale(1.5 * grow, 1.3 * grow, 0.05)
                pad["ring"].setColor(*pad["col"], 0.6 if appr > 0 else 0.9)
                pad["node"].setColor(*pad["col"], 1)
            if self.t >= T - w:
                c["best"] = max(c["best"], self._proj(c["dir"], inp))
            if self.t >= T + 0.15:
                c["done"] = True
                pad["node"].setColor(*tuple(x * 0.45 for x in pad["col"]), 1)
                if c["best"] >= 1.0:
                    self.hits += 1
                    self.combo += 1
                    self.score += 100 + min(self.combo, 10) * 5
                    self.app.sound.play("coin")
                    px, py = pad["pos"]
                    self.fx.burst((px, py, 0.4), (pad["col"], (1, 1, 1)), 14, 3.0, 0.7)
                    self.hud_msg["text"] = f"Perfetto! x{self.combo}" if self.combo >= 3 else "Bene!"
                else:
                    self.combo = 0
                    self.app.sound.play("bump")
                    self.hud_msg["text"] = "Mancato"
                self.msg_t = 0.8
        self.msg_t -= dt
        if self.msg_t <= 0:
            nxt = next((c for c in self.cues if not c["done"]), None)
            if nxt and nxt["T"] - self.t < self.every:
                self.hud_msg["text"] = f"Vai a {NAMES[nxt['dir']]}!"
            elif self.t < LEAD_IN:
                self.hud_msg["text"] = "Preparati..."
            else:
                self.hud_msg["text"] = ""
