"""Pesca perle: il pinguino nuota dove sposti il peso. Prendi le perle e schiva i ricci di mare."""
import math
import random

from fx import Clouds
from gamekit import Game, blob, box, clamp, make_penguin, perspective, set_flippers

XR, YR = 6.2, 3.6  # semi-dimensioni del fondale
PICK = 0.85
HIT = 0.8


class Pearls(Game):
    key = "pearls"
    title = "Pesca perle"
    blurb = "Nuota spostando il peso: prendi le perle e schiva i ricci di mare"
    music = "sea"
    met = 4.0
    duration = 45.0

    def setup(self):
        d = self.diff
        self.life = (7.0, 5.5, 4.2)[d]  # secondi di vita di una perla
        self.n_urchins = (2, 3, 4)[d]
        self.urchin_speed = (1.4, 2.0, 2.8)[d]
        self.lives = (5, 4, 3)[d]
        perspective(self.app, 55)
        self.app.setBackgroundColor(0.05, 0.27, 0.5, 1)
        self.app.camera.setPos(0, -9.5, 14)
        self.app.camera.lookAt(0, 0.3, 0)
        L = self.loader
        box(self.root, L, (40, 26, 0.2), (0.42, 0.7, 0.78), (0, 0, -0.5))  # fondale
        for i in range(14):  # alghe
            x = random.choice((-1, 1)) * random.uniform(XR + 0.5, XR + 4)
            y = random.uniform(-YR - 2, YR + 3)
            h = random.uniform(1.2, 2.6)
            box(self.root, L, (0.18, 0.18, h), (0.15, 0.6, 0.35), (x, y, h / 2 - 0.4))
        for i in range(10):  # conchiglie e sassi
            blob(self.root, L, (0.3, 0.3, 0.18), (0.95, 0.75, 0.7), (random.uniform(-12, 12), random.uniform(-8, 9), -0.4))
        self.peng = make_penguin(self.root, L)
        self.peng.setScale(0.7)
        self.px = self.py = 0.0
        self.vx = self.vy = 0.0
        self.pearls = []
        self.spawn_t = 0.6
        self.urchins = []
        for _ in range(self.n_urchins):
            self._add_urchin()
        self.invuln = 0.0
        self.t = 0.0
        self.bubble_t = 0.0
        self.collected = 0

    def _add_urchin(self):
        L = self.loader
        n = self.root.attachNewNode("urchin")
        blob(n, L, (0.45, 0.45, 0.4), (0.3, 0.1, 0.4), (0, 0, 0))
        for k in range(10):
            a = k * 36
            s = blob(n, L, (0.06, 0.06, 0.4), (0.15, 0.05, 0.2), (0, 0, 0), (a, 0, random.uniform(20, 80)))
            s.setPos(math.cos(math.radians(a)) * 0.4, math.sin(math.radians(a)) * 0.4, 0.15)
        while True:
            x, y = random.uniform(-XR, XR), random.uniform(-YR, YR)
            if math.hypot(x - self.px, y - self.py) > 3.5:
                break
        ang = random.uniform(0, 2 * math.pi)
        self.urchins.append({"node": n, "x": x, "y": y, "vx": math.cos(ang) * self.urchin_speed,
                             "vy": math.sin(ang) * self.urchin_speed})

    def _add_pearl(self):
        L = self.loader
        n = self.root.attachNewNode("pearl")
        blob(n, L, (0.28, 0.28, 0.28), (0.98, 0.9, 0.95), (0, 0, 0.1))
        ring = blob(n, L, (0.6, 0.6, 0.04), (1, 1, 0.7), (0, 0, 0.02))
        ring.setTransparency(True)
        ring.setColor(1, 1, 0.7, 0.45)
        x, y = random.uniform(-XR + 0.5, XR - 0.5), random.uniform(-YR + 0.4, YR - 0.4)
        n.setPos(x, y, -0.3)
        self.pearls.append({"node": n, "x": x, "y": y, "age": 0.0, "ring": ring})

    def medals(self):
        return ((600, 1100, 1600), (700, 1300, 1900), (800, 1500, 2200))[self.diff]

    def update(self, dt, inp):
        self.t += dt
        tx = clamp(inp.x / 100.0) * XR
        ty = clamp(inp.y / 60.0) * YR
        ox, oy = self.px, self.py
        self.px += (tx - self.px) * min(1.0, 6 * dt)
        self.py += (ty - self.py) * min(1.0, 6 * dt)
        vx, vy = (self.px - ox) / max(dt, 1e-3), (self.py - oy) / max(dt, 1e-3)
        speed = math.hypot(vx, vy)
        self.peng.setPos(self.px, self.py, 0.3 + 0.08 * math.sin(self.t * 3))
        if speed > 0.5:
            self.peng.setH(math.degrees(math.atan2(-vx, vy)))
        set_flippers(self.peng, 50 + 40 * math.sin(self.t * 9))  # nuota
        self.invuln = max(0.0, self.invuln - dt)
        self.peng.setAlphaScale(1.0)
        if self.invuln > 0:  # lampeggia dopo un colpo
            self.peng.setTransparency(True)
            self.peng.setAlphaScale(0.35 if int(self.t * 12) % 2 else 1.0)

        self.bubble_t -= dt
        if self.bubble_t <= 0:
            self.bubble_t = 0.08
            self.fx.emit((random.uniform(-XR - 2, XR + 2), random.uniform(-YR - 2, YR + 2), -0.3),
                         (0, 0, random.uniform(0.8, 1.6)), (0.8, 0.95, 1), 3.0, random.uniform(0.05, 0.13), 0)

        self.spawn_t -= dt
        if self.spawn_t <= 0 and len(self.pearls) < 3:
            self.spawn_t = 1.3
            self._add_pearl()
        for p in self.pearls[:]:
            p["age"] += dt
            left = 1 - p["age"] / self.life
            p["ring"].setScale(0.6 * max(left, 0.1), 0.6 * max(left, 0.1), 0.04)
            p["node"].setH(p["node"].getH() + 60 * dt)
            if math.hypot(p["x"] - self.px, p["y"] - self.py) < PICK:
                self.collected += 1
                self.score += 100
                self.app.sound.play("coin")
                self.fx.burst((p["x"], p["y"], 0.3), ((1, 0.95, 0.8), (1, 1, 1), (0.6, 0.9, 1)), 14, 3.0, 0.8)
                p["node"].removeNode()
                self.pearls.remove(p)
            elif p["age"] >= self.life:
                p["node"].removeNode()
                self.pearls.remove(p)

        # i ricci rimbalzano sui bordi; col tempo ne arriva uno in piu'
        if self.t > 20 and len(self.urchins) == self.n_urchins:
            self._add_urchin()
        for u in self.urchins:
            u["x"] += u["vx"] * dt
            u["y"] += u["vy"] * dt
            if abs(u["x"]) > XR:
                u["vx"] *= -1
                u["x"] = clamp(u["x"], -XR, XR)
            if abs(u["y"]) > YR:
                u["vy"] *= -1
                u["y"] = clamp(u["y"], -YR, YR)
            u["node"].setPos(u["x"], u["y"], 0.0)
            u["node"].setH(u["node"].getH() + 40 * dt)
            if self.invuln <= 0 and math.hypot(u["x"] - self.px, u["y"] - self.py) < HIT:
                self.lives -= 1
                self.invuln = 1.6
                self.app.sound.play("bump")
                self.fx.burst((self.px, self.py, 0.4), ((0.9, 0.2, 0.3), (0.3, 0.1, 0.4)), 12, 3.0, 0.6)
                if self.lives <= 0:
                    self.done = True
        self.hud_msg["text"] = f"Vite: {self.lives}"
