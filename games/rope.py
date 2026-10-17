"""Funambolo: cammina sulla fune. Sposta il peso verso il lato dove il pinguino pende per riequilibrarlo."""
import math
import random

from fx import Clouds, make_shadow, sun
from gamekit import Game, box, clamp, make_penguin, perspective, set_flippers

WALK = 2.2  # metri al secondo quando sei stabile


class Rope(Game):
    key = "rope"
    title = "Funambolo"
    blurb = "Cammina sulla fune: sposta il peso verso il lato dove il pinguino pende per riequilibrarlo"
    music = "tension"
    met = 2.5
    duration = 45.0

    def setup(self):
        d = self.diff
        self.drift = (1.2, 1.6, 2.0)[d]  # quanto in fretta cade da solo
        self.wind_amp = (0.4, 0.55, 0.8)[d]
        self.gain = 3.4  # efficacia dello spostamento del peso
        self.lives = (5, 3, 3)[d]
        perspective(self.app, 60)
        self.app.setBackgroundColor(0.55, 0.76, 0.96, 1)
        L = self.loader
        self.rope = box(self.root, L, (0.1, 400, 0.1), (0.25, 0.2, 0.15), (0, 190, -0.05))
        for side in (-1, 1):  # pareti del canyon
            for k, (w, h) in enumerate(((10, 30), (14, 45), (9, 38))):
                box(self.root, L, (w, 400, h), (0.62 - 0.07 * k, 0.45 - 0.05 * k, 0.32), (side * (16 + w / 2 + k * 6), 190, h / 2 - 40))
        self.posts = []
        for y in range(10, 400, 10):  # picchetti ogni 10 m per dare il senso del progresso
            box(self.root, L, (0.1, 0.1, 0.5), (0.95, 0.85, 0.2), (0.35, y, 0.15))
        self.sun = sun(self.root, L, (-30, 300, 60), 12)
        self.clouds = Clouds(self.root, L, 7, (-80, 80), 200, (-10, 30), (2.0, 4.0))
        self.shadow = make_shadow(self.root, L, 0.4)
        self.shadow.hide()  # sotto la fune c'e' il vuoto
        self.peng = make_penguin(self.root, L)
        self.peng.setScale(0.7)
        self.pole = box(self.root, L, (6.0, 0.12, 0.12), (0.85, 0.7, 0.3), (0, 0, 1.0))
        self.a = 0.0  # inclinazione: -1 cade a sinistra, +1 a destra
        self.v = 0.0
        self.dist = 0.0
        self.t = 0.0
        self.fall = 0.0
        self.gust_t = random.uniform(2.0, 4.0)
        self.phase = random.uniform(0, 6.28)
        self.misses = 0

    def medals(self):
        return ((500, 750, 900), (550, 780, 920), (600, 820, 940))[self.diff]

    def update(self, dt, inp):
        self.t += dt
        self.clouds.update(dt)
        cam = self.app.camera
        cam.setPos(0, self.dist - 7.5, 4.6)
        cam.lookAt(0, self.dist + 8, 1.0)
        self.sun.setY(self.dist + 300)

        if self.fall > 0:  # sta cadendo: poi torna sulla fune
            self.fall -= dt
            self.peng.setZ(self.peng.getZ() - 9 * dt)
            self.peng.setR(self.peng.getR() + 200 * dt * (1 if self.a > 0 else -1))
            if self.fall <= 0:
                self.a = self.v = 0.0
                self.peng.setR(0)
                self.peng.setZ(0.08)
            return

        u = clamp(inp.x / 90.0)
        wind = self.wind_amp * (math.sin(0.8 * self.t + self.phase) + 0.6 * math.sin(2.1 * self.t + 1.0))
        self.gust_t -= dt
        if self.gust_t <= 0:  # raffica improvvisa
            self.gust_t = random.uniform(3.0, 5.0)
            self.v += random.choice((-1, 1)) * self.wind_amp * 1.6
        acc = self.drift * self.a + wind - self.gain * u  # spostare il peso dal lato della pendenza la riduce
        self.v += acc * dt
        self.v *= max(0.0, 1 - 2.0 * dt)
        self.a += self.v * dt

        if abs(self.a) >= 1.0:
            self.misses += 1
            self.lives -= 1
            self.app.sound.play("splash")
            self.fx.burst((0, self.dist, 0.5), ((1, 1, 1),), 12, 3.0, 0.8, 0.12, up=-1.0)
            self.fall = 1.0
            if self.lives <= 0:
                self.done = True
            return

        walk = WALK * (1.0 if abs(self.a) < 0.6 else 0.5)
        self.dist += walk * dt
        self.score = max(0, int(self.dist * 10) - 80 * self.misses)  # ogni caduta costa 80 punti
        bob = abs(math.sin(self.t * 5)) * 0.05
        self.peng.setPos(0, self.dist, 0.08 + bob)
        self.peng.setR(self.a * 35)
        self.peng.setH(0)
        set_flippers(self.peng, 70 + 50 * abs(self.a))
        self.pole.setPos(0, self.dist, 0.95)
        self.pole.setR(self.a * -22 + math.sin(self.t * 3) * 3)

        if abs(self.a) > 0.5:
            side = "destra" if self.a > 0 else "sinistra"
            self.hud_msg["text"] = f"Sposta il peso a {side}!  Vite: {self.lives}"
        else:
            self.hud_msg["text"] = f"{self.dist:.0f} m   Vite: {self.lives}"
