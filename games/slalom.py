"""Slalom sugli sci: inclinati a destra e a sinistra per passare tra le porte."""
import math
import random

from fx import Clouds, follow_shadow, make_shadow, mountains, sun
from gamekit import Game, blob, box, clamp, make_penguin, perspective, set_flippers

W = 6.0  # semi-larghezza della pista
GATE_EVERY = 18.0
FIRST_GATE = 25.0


class Slalom(Game):
    key = "slalom"
    title = "Slalom sugli sci"
    blurb = "Inclinati a destra e a sinistra e passa tra le porte"
    music = "action"
    met = 3.5  # equivalente metabolico, per stimare le calorie
    duration = 45.0

    def setup(self):
        d = self.diff
        self.speed = (8.0, 11.0, 14.0)[d]
        self.gate_w = (5.0, 4.0, 3.2)[d]
        perspective(self.app, 65)
        self.app.setBackgroundColor(0.72, 0.87, 0.97, 1)
        L = self.loader
        self.ground = box(self.root, L, (60, 700, 0.2), (0.96, 0.98, 1.0), (0, 300, -0.1))
        self.peng = make_penguin(self.root, L)
        self.peng.setScale(0.8)
        for s in (-1, 1):  # sci
            box(self.peng, L, (0.18, 1.6, 0.06), (0.75, 0.3, 0.1), (s * 0.22, 0.25, 0.02))
        self.shadow = make_shadow(self.root, L, 0.7)
        self.mountains = mountains(self.root, L, 7, (-200, 200), 330)
        self.clouds = Clouds(self.root, L, 6, (-120, 120), 250, (35, 70))
        self.sun = sun(self.root, L, (80, 380, 90), 14)
        self.snow_t = 0.0
        self.px = self.py = 0.0
        self.streak = self.passed = 0
        self.gates = []
        self.trees = []
        self.cx = 0.0
        self.next_gate = FIRST_GATE
        self.next_tree = 6.0
        self.msg_t = 0.0
        self._spawn(90)

    # --- generazione del percorso ---
    def _spawn(self, upto):
        L = self.loader
        while self.next_gate < upto:
            self.cx = clamp(self.cx + random.uniform(-3.5, 3.5), -(W - 2.2), W - 2.2)
            nodes = []
            for s, col in ((-1, (0.9, 0.15, 0.15)), (1, (0.15, 0.3, 0.9))):
                x = self.cx + s * self.gate_w / 2
                nodes.append(box(self.root, L, (0.25, 0.25, 2.2), col, (x, self.next_gate, 1.1)))
                nodes.append(box(self.root, L, (0.7, 0.05, 0.45), col, (x, self.next_gate, 2.0)))
            self.gates.append({"y": self.next_gate, "cx": self.cx, "nodes": nodes, "done": False})
            self.next_gate += GATE_EVERY
        while self.next_tree < upto:
            side = random.choice((-1, 1))
            x = side * random.uniform(W + 2.5, W + 9)
            t = self.root.attachNewNode("tree")
            box(t, L, (0.35, 0.35, 1.0), (0.4, 0.25, 0.1), (0, 0, 0.5))
            blob(t, L, (1.3, 1.3, 1.1), (0.1, 0.5, 0.25), (0, 0, 1.6))
            blob(t, L, (0.9, 0.9, 0.9), (0.15, 0.6, 0.3), (0, 0, 2.5))
            t.setPos(x, self.next_tree, 0)
            self.trees.append((self.next_tree, t))
            self.next_tree += random.uniform(3, 6)

    def medals(self):
        n = max(int((self.duration * self.speed - FIRST_GATE) / GATE_EVERY) + 1, 1)
        return (0.4 * n * 100, 0.65 * n * 100, 0.85 * n * 100)

    # --- ciclo di gioco ---
    def update(self, dt, inp):
        target = clamp(inp.x / 100.0) * W
        dx = target - self.px
        self.px += dx * min(1.0, 5 * dt)
        self.py += self.speed * dt
        self.peng.setPos(self.px, self.py, 0.05)
        self.peng.setH(clamp(-dx * 6, -35, 35))
        self.peng.setR(clamp(-dx * 4, -20, 20))  # si inclina nella curva
        set_flippers(self.peng, 40 + min(abs(dx) * 14, 50))
        follow_shadow(self.shadow, self.px, self.py)
        for m in self.mountains:
            m.setY(self.py + 330)
        self.sun.setY(self.py + 380)
        self.clouds.update(dt, self.py)
        self.snow_t -= dt
        while self.snow_t <= 0:  # neve che cade attorno al pinguino
            self.snow_t += 0.03
            self.fx.emit((self.px + random.uniform(-14, 14), self.py + random.uniform(2, 45), 9),
                         (random.uniform(-0.5, 0.5), 0, -random.uniform(2.5, 4.5)), (1, 1, 1), 3.0, 0.07, 0)
        if self.speed > 0:  # scia di neve dietro agli sci
            self.fx.emit((self.px + random.uniform(-0.3, 0.3), self.py - 0.4, 0.15),
                         (random.uniform(-0.6, 0.6), -1.0, random.uniform(0.4, 1.2)), (0.95, 0.97, 1), 0.5, 0.1, -3)
        cam = self.app.camera
        cam.setPos(self.px * 0.6, self.py - 9, 5.2)
        cam.lookAt(self.px * 0.7, self.py + 8, 0.5)
        self.ground.setY(self.py + 300)

        for g in self.gates:
            if not g["done"] and self.py >= g["y"]:
                g["done"] = True
                if abs(self.px - g["cx"]) < self.gate_w / 2 - 0.2:
                    self.streak += 1
                    self.passed += 1
                    self.score += 100 + min(self.streak, 10) * 10
                    self.app.sound.play("coin")
                    self.fx.burst((g["cx"], g["y"], 1.2), ((1, 0.9, 0.2), (1, 1, 1)), 14, 3.0, 0.7)
                    self.hud_msg["text"] = f"Serie x{self.streak}!" if self.streak >= 3 else "Bene!"
                else:
                    self.streak = 0
                    self.app.sound.play("bump")
                    self.hud_msg["text"] = "Mancata!"
                self.msg_t = 1.0
        self.msg_t -= dt
        if self.msg_t <= 0:
            self.hud_msg["text"] = ""

        for g in [g for g in self.gates if g["y"] < self.py - 12]:
            for n in g["nodes"]:
                n.removeNode()
            self.gates.remove(g)
        for y, t in [(y, t) for y, t in self.trees if y < self.py - 12]:
            t.removeNode()
            self.trees.remove((y, t))
        self._spawn(self.py + 90)
