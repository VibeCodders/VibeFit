"""Hula hoop: fai ruotare il bacino in cerchio, a ritmo, senza fermarti."""
import math

from fx import Clouds, follow_shadow, make_shadow, palm, sun
from gamekit import Game, blob, box, make_penguin, perspective, set_flippers

TWO_PI = 2 * math.pi


def wrap(a):
    return (a + math.pi) % TWO_PI - math.pi


class Hula(Game):
    key = "hula"
    title = "Hula hoop"
    blurb = "Fai ruotare il bacino in cerchio, a ritmo, senza fermarti"
    music = "menu"
    met = 4.0  # equivalente metabolico, per stimare le calorie
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
        box(self.root, L, (60, 40, 0.2), (0.96, 0.85, 0.55), (0, 0, -0.1))
        box(self.root, L, (80, 30, 0.1), (0.25, 0.65, 0.85), (0, 28, 0.0))  # mare
        box(self.root, L, (80, 3, 0.12), (1, 1, 1), (0, 12.5, 0.02))  # schiuma
        self.sun = sun(self.root, L, (-6, 40, 12), 4.5)
        self.clouds = Clouds(self.root, L, 4, (-30, 30), 35, (8, 14), (1.0, 1.8))
        for x, s in ((-5.5, 1.1), (5.0, 1.3), (-8.5, 0.9), (8.2, 1.0)):
            palm(self.root, L, (x, 6.0, 0), s)
        self.shadow = make_shadow(self.root, L, 0.75)
        self.beat_orb = blob(self.root, L, (0.35, 0.35, 0.35), (1.0, 0.85, 0.2), (2.4, 0, 2.6))
        self.beat_orb.setLightOff()
        self.t = 0.0
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
        self.fx.burst((self.hoop.getX(), self.hoop.getY() - 0.8, 1.6), ((1, 0.85, 0.2), (0.95, 0.25, 0.3), (1, 1, 1)),
                      10, 2.2, 0.6, 0.1, up=2.5)

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
        set_flippers(self.peng, 80 + 25 * math.sin(self.hoop_a))
        follow_shadow(self.shadow, inp.x * 0.002, inp.y * 0.002)
        self.clouds.update(dt)
        self.t += dt

        self.beat += dt
        if self.beat >= self.period:
            self.beat -= self.period
            self.app.sound.play("click")
        pulse = max(0.0, 1.0 - (self.beat / self.period) * 5)  # il pallone pulsa a tempo
        self.beat_orb.setScale(0.35 * (1 + 0.8 * pulse))
        if self.idle > 2.5:
            self.combo = 0
            self.hud_msg["text"] = "Muovi i fianchi in cerchio!"
        else:
            self.hud_msg["text"] = f"Giri: {self.rotations}" + (f"   Serie x{self.combo}" if self.combo >= 3 else "")
