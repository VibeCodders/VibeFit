"""Calcio di testa: colpisci i palloni di testa e schiva le scarpe."""
import math
import random

from gamekit import Game, blob, box, clamp, make_penguin, perspective

W = 5.0


class Heading(Game):
    key = "heading"
    title = "Calcio di testa"
    blurb = "Muoviti a destra e a sinistra: colpisci i palloni e schiva le scarpe!"
    music = "action"
    duration = 45.0

    def setup(self):
        d = self.diff
        self.speed = (12.0, 16.0, 20.0)[d]
        self.interval = (1.5, 1.2, 0.95)[d]
        self.lives = (5, 3, 3)[d]
        perspective(self.app, 65)
        self.app.setBackgroundColor(0.6, 0.82, 0.97, 1)
        L = self.loader
        box(self.root, L, (80, 400, 0.2), (0.3, 0.65, 0.3), (0, 150, -0.1))
        self.stripes = [box(self.root, L, (80, 0.5, 0.02), (0.9, 0.95, 0.9), (0, i * 8.0, 0.01))
                        for i in range(9)]
        self.peng = make_penguin(self.root, L)
        self.peng.setScale(0.9)
        self.px = 0.0
        self.objs = []
        self.timer = 1.0
        self.streak = 0
        self.flash = 0.0

    def _ball(self):
        n = self.root.attachNewNode("ball")
        blob(n, self.loader, (0.5, 0.5, 0.5), (0.97, 0.97, 0.97))
        for dx, dy, dz in ((0.3, -0.38, 0.2), (-0.3, -0.38, 0.2), (0.0, -0.46, -0.22), (0.0, -0.1, 0.46)):
            blob(n, self.loader, (0.16, 0.16, 0.16), (0.1, 0.1, 0.12), (dx, dy, dz))
        return n

    def _shoe(self):
        n = self.root.attachNewNode("shoe")
        box(n, self.loader, (0.55, 1.2, 0.35), (0.75, 0.15, 0.15), (0, 0, 0.3))
        box(n, self.loader, (0.6, 1.25, 0.12), (0.95, 0.95, 0.95), (0, 0, 0.08))
        return n

    def medals(self):
        n = self.duration / self.interval * 0.7
        return (0.4 * n * 100, 0.65 * n * 100, 0.85 * n * 100)

    def update(self, dt, inp):
        self.px += (clamp(inp.x / 100.0) * W - self.px) * min(1.0, 8 * dt)
        self.peng.setPos(self.px, 0, 0)
        cam = self.app.camera
        cam.setPos(self.px * 0.5, -8, 4.5)
        cam.lookAt(self.px * 0.5, 12, 1.5)

        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.interval * random.uniform(0.8, 1.2)
            kind = "ball" if random.random() < 0.7 else "shoe"
            node = self._ball() if kind == "ball" else self._shoe()
            o = {"kind": kind, "node": node, "x": random.uniform(-W, W), "y": 70.0,
                 "z": 1.55 if kind == "ball" else 0.0, "state": "come", "life": 0.0, "judged": False}
            self.objs.append(o)

        for s in self.stripes:
            s.setY(s.getY() - self.speed * dt)
            if s.getY() < -6:
                s.setY(s.getY() + 72)

        for o in self.objs[:]:
            n = o["node"]
            if o["state"] == "come":
                o["y"] -= self.speed * dt
                if o["kind"] == "ball":
                    n.setP(n.getP() - self.speed * dt * 50)
                n.setPos(o["x"], o["y"], o["z"])
                if not o["judged"] and o["y"] <= 0.5:
                    o["judged"] = True
                    hit = abs(o["x"] - self.px) < 1.0
                    if o["kind"] == "ball" and hit:
                        self.streak += 1
                        self.score += 100 + min(self.streak, 10) * 5
                        self.app.sound.play("coin")
                        o["state"] = "fly"
                    elif o["kind"] == "ball":
                        self.streak = 0
                    elif hit:
                        self.lives -= 1
                        self.streak = 0
                        self.app.sound.play("bump")
                        o["state"] = "fly"
                        if self.lives <= 0:
                            self.done = True
                if o["y"] < -12:
                    n.removeNode()
                    self.objs.remove(o)
            else:  # colpito: vola via
                o["life"] += dt
                o["y"] += 14 * dt
                o["z"] += (6 - 14 * o["life"]) * dt
                n.setPos(o["x"], o["y"], max(o["z"], 0.0))
                if o["life"] > 0.8:
                    n.removeNode()
                    self.objs.remove(o)

        self.hud_msg["text"] = f"Vite: {self.lives}" + (f"   Serie x{self.streak}" if self.streak >= 3 else "")
