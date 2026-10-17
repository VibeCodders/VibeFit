"""Equilibrio sul ghiaccio: il pinguino scivola su una lastra inclinata dal tuo peso."""
import math
import random

from gamekit import Game, blob, box, clamp, make_penguin, perspective

RADIUS = 4.5
PICKUP = 0.8


class IceBalance(Game):
    key = "ice"
    title = "Equilibrio sul ghiaccio"
    blurb = "Sposta il peso per far scivolare il pinguino a prendere i pesci"
    music = "calm"
    duration = 60.0

    def setup(self):
        d = self.diff
        self.gain = (8.0, 10.0, 13.0)[d]
        self.friction = 1.2
        self.lives = (5, 3, 3)[d]
        perspective(self.app, 55)
        self.app.setBackgroundColor(0.45, 0.7, 0.85, 1)
        self.app.camera.setPos(0, -8.5, 11)
        self.app.camera.lookAt(0, 0.6, 0)
        L = self.loader
        self.sea = box(self.root, L, (60, 60, 0.1), (0.15, 0.4, 0.65), (0, 0, -0.9))
        self.plat = self.root.attachNewNode("plat")
        blob(self.plat, L, (RADIUS, RADIUS, 0.3), (0.85, 0.95, 1.0), (0, 0, -0.3))
        self.peng = make_penguin(self.plat, L)
        self.peng.setScale(0.75)
        self.fish = self.plat.attachNewNode("fish")
        blob(self.fish, L, (0.45, 0.22, 0.2), (1.0, 0.55, 0.15), (0, 0, 0.3))
        box(self.fish, L, (0.05, 0.3, 0.3), (1.0, 0.45, 0.1), (-0.5, 0, 0.3))
        self.pos = [0.0, 0.0]
        self.vel = [0.0, 0.0]
        self.fallen = 0.0
        self.fish_pos = [0.0, 0.0]
        self._new_fish()
        self.catches = 0

    def _new_fish(self):
        while True:
            a = random.uniform(0, 2 * math.pi)
            r = random.uniform(1.5, RADIUS - 1.2)
            p = [math.cos(a) * r, math.sin(a) * r]
            if math.hypot(p[0] - self.pos[0], p[1] - self.pos[1]) > 2.0:
                break
        self.fish_pos = p
        self.fish.setPos(p[0], p[1], 0.05)

    def medals(self):
        return ((300, 600, 1000), (400, 800, 1300), (500, 1000, 1600))[self.diff]

    def update(self, dt, inp):
        # la lastra si inclina verso il lato dove sposti il peso
        lx, ly = clamp(inp.x / 110.0), clamp(inp.y / 70.0)
        self.plat.setHpr(0, -ly * 8, lx * 8)
        self.fish.setH(self.fish.getH() + 90 * dt)
        self.hud_msg["text"] = "Vite: " + "O" * self.lives if self.lives else ""

        if self.fallen > 0:
            self.fallen -= dt
            if self.fallen <= 0:
                self.pos, self.vel = [0.0, 0.0], [0.0, 0.0]
                self.peng.show()
            return

        for i, l in enumerate((lx, ly)):
            self.vel[i] += l * self.gain * dt
            self.vel[i] *= max(0.0, 1 - self.friction * dt)
            self.pos[i] += self.vel[i] * dt
        speed = math.hypot(*self.vel)
        self.peng.setPos(self.pos[0], self.pos[1], 0.0)
        if speed > 0.3:
            self.peng.setH(math.degrees(math.atan2(-self.vel[0], self.vel[1])))

        if math.hypot(*self.pos) > RADIUS:
            self.lives -= 1
            self.app.sound.play("splash")
            self.peng.hide()
            self.fallen = 1.0
            if self.lives <= 0:
                self.done = True
            return
        if math.hypot(self.pos[0] - self.fish_pos[0], self.pos[1] - self.fish_pos[1]) < PICKUP:
            self.catches += 1
            self.score += 100
            self.app.sound.play("coin")
            self._new_fish()
