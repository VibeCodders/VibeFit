"""Corsa sul posto: alterna il peso da un piede all'altro; piu' passi fai, piu' il pinguino corre."""
import collections
import math
import random

from gamekit import Game, blob, box, make_penguin, perspective

STEP_LEN = 1.1  # metri per passo (distanza di gioco)
CHECKPOINT = 50.0


class Run(Game):
    key = "run"
    title = "Corsa sul posto"
    blurb = "Alterna il peso da un piede all'altro, come se corressi sul posto"
    music = "action"
    duration = 45.0

    def setup(self):
        self.th = (12.0, 18.0, 24.0)[self.diff]  # spostamento laterale minimo (mm)
        perspective(self.app, 65)
        self.app.setBackgroundColor(0.72, 0.88, 0.98, 1)
        L = self.loader
        self.ground = box(self.root, L, (60, 900, 0.2), (0.55, 0.78, 0.45), (0, 400, -0.1))
        box(self.root, L, (3.0, 900, 0.03), (0.85, 0.75, 0.55), (0, 400, 0.01))  # sentiero
        self.peng = make_penguin(self.root, L)
        self.peng.setScale(0.8)
        self.py = 0.0
        self.speed = 0.0
        self.t = 0.0
        self.side = 0
        self.last_step = 0.0
        self.flash_t = -10.0
        self.steps = 0
        self.step_times = collections.deque()
        self.next_cp = CHECKPOINT
        self.trees = []
        self.next_tree = 4.0
        self._spawn(80)

    def _spawn(self, upto):
        L = self.loader
        while self.next_tree < upto:
            x = random.choice((-1, 1)) * random.uniform(4, 11)
            t = self.root.attachNewNode("tree")
            box(t, L, (0.35, 0.35, 1.0), (0.4, 0.25, 0.1), (0, 0, 0.5))
            blob(t, L, (1.3, 1.3, 1.1), (0.15, 0.55, 0.25), (0, 0, 1.6))
            blob(t, L, (0.9, 0.9, 0.9), (0.2, 0.65, 0.3), (0, 0, 2.5))
            t.setPos(x, self.next_tree, 0)
            self.trees.append((self.next_tree, t))
            self.next_tree += random.uniform(3, 6)

    def medals(self):
        return (500, 800, 1100)

    def update(self, dt, inp):
        self.t += dt
        new = 1 if inp.x > self.th else -1 if inp.x < -self.th else 0
        if new and new != self.side and self.t - self.last_step > 0.15:
            self.side = new
            self.last_step = self.t
            self.steps += 1
            self.score += 10
            self.step_times.append(self.t)
            self.app.sound.play("click")
        while self.step_times and self.t - self.step_times[0] > 2.0:
            self.step_times.popleft()
        cadence = len(self.step_times) / 2.0  # passi al secondo
        self.speed += (cadence * STEP_LEN - self.speed) * min(1.0, 3 * dt)
        self.py += self.speed * dt

        if self.py >= self.next_cp:
            self.next_cp += CHECKPOINT
            self.score += 50
            self.flash_t = self.t
            self.app.sound.play("ok")
        if self.t - self.flash_t < 1.2:
            self.hud_msg["text"] = "Traguardo! +50"
        elif self.t - self.last_step > 1.5:
            self.hud_msg["text"] = "Corri! Muovi i piedi!"
        else:
            self.hud_msg["text"] = f"{self.steps} passi   {self.py:.0f} m"

        bob = abs(math.sin(self.t * max(cadence, 0.5) * math.pi)) * 0.12 * min(1.0, cadence)
        self.peng.setPos(0, self.py, 0.05 + bob)
        self.peng.setR(self.side * 8)
        cam = self.app.camera
        cam.setPos(0, self.py - 8, 4.2)
        cam.lookAt(0, self.py + 8, 0.8)
        self.ground.setY(self.py + 400)
        for y, t in [(y, t) for y, t in self.trees if y < self.py - 12]:
            t.removeNode()
            self.trees.remove((y, t))
        self._spawn(self.py + 80)
