"""Hula hoop: fai ruotare il bacino in cerchio, a ritmo, senza fermarti."""
import math

from gamekit import Game, blob, box, make_penguin, perspective

TWO_PI = 2 * math.pi


def wrap(a):
    return (a + math.pi) % TWO_PI - math.pi


class Hula(Game):
    key = "hula"
    title = "Hula hoop"
    blurb = "Fai ruotare il bacino in cerchio, a ritmo, senza fermarti"
    music = "menu"
    duration = 40.0

    def setup(self):
        d = self.diff
        self.period = (1.6, 1.2, 0.9)[d]  # secondi per giro consigliati
        self.rmin = (10.0, 14.0, 18.0)[d]  # raggio minimo del baricentro (mm)
        perspective(self.app, 50)
        self.app.setBackgroundColor(1.0, 0.86, 0.62, 1)
        self.app.camera.setPos(0, -7.5, 2.6)
        self.app.camera.lookAt(0, 0, 1.2)
        L = self.loader
        box(self.root, L, (40, 40, 0.2), (0.96, 0.85, 0.55), (0, 0, -0.1))
        self.peng = make_penguin(self.root, L)
        self.peng.setH(180)  # rivolto verso la camera
        self.hoop = self.root.attachNewNode("hoop")
        self.hoop.setZ(0.75)
        n = 16
        for i in range(n):
            a = TWO_PI * i / n
            col = (0.95, 0.25, 0.3) if i % 2 else (1.0, 0.85, 0.2)
            blob(self.hoop, L, (0.14, 0.14, 0.14), col, (math.cos(a) * 0.95, math.sin(a) * 0.95, 0))
        self.last_a = None
        self.acc = 0.0
        self.omega = 0.0
        self.hoop_a = 0.0
        self.combo = 0
        self.since_rot = 0.0
        self.idle = 0.0
        self.beat = 0.0
        self.rotations = 0

    def medals(self):
        n = self.duration / self.period
        return (0.25 * n * 100, 0.45 * n * 100, 0.65 * n * 100)

    def _rotation(self):
        self.combo = self.combo + 1 if self.since_rot <= self.period * 1.8 else 1
        self.score += 50 + 10 * min(self.combo, 10)
        self.rotations += 1
        self.since_rot = 0.0
        self.app.sound.play("rep")

    def update(self, dt, inp):
        r = math.hypot(inp.x, inp.y)
        self.since_rot += dt
        if r >= self.rmin:
            a = math.atan2(inp.y, inp.x)
            if self.last_a is not None:
                da = wrap(a - self.last_a)
                self.acc += da
                self.omega += (da / max(dt, 1e-3) - self.omega) * min(1.0, 6 * dt)
            self.last_a = a
            self.idle = 0.0
        else:
            self.last_a = None
            self.idle += dt
            self.omega *= max(0.0, 1 - 3 * dt)
        while abs(self.acc) >= TWO_PI:
            self.acc -= math.copysign(TWO_PI, self.acc)
            self._rotation()

        self.hoop_a += self.omega * dt
        self.hoop.setH(math.degrees(self.hoop_a))
        self.hoop.setPos(inp.x * 0.004, inp.y * 0.004, 0.75)
        self.peng.setPos(inp.x * 0.002, inp.y * 0.002, 0)

        self.beat += dt
        if self.beat >= self.period:
            self.beat -= self.period
            self.app.sound.play("click")
        if self.idle > 2.5:
            self.combo = 0
            self.hud_msg["text"] = "Muovi i fianchi in cerchio!"
        else:
            self.hud_msg["text"] = f"Giri: {self.rotations}" + (f"   Serie x{self.combo}" if self.combo >= 3 else "")
