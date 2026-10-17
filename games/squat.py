"""Squat: scendi e risali a ritmo regolare. Le ripetizioni si riconoscono dalla variazione del peso."""
from fx import make_shadow
from gamekit import Game, blob, box, clamp, make_penguin, perspective, set_flippers


class Squat(Game):
    key = "squat"
    title = "Squat"
    blurb = "Stai in piedi fermo, poi fai squat: scendi e risali con calma"
    music = "calm"
    met = 5.0  # equivalente metabolico, per stimare le calorie
    duration = 45.0

    def setup(self):
        self.th = (0.06, 0.08, 0.10)[self.diff]  # variazione relativa del peso richiesta
        perspective(self.app, 50)
        self.app.setBackgroundColor(0.78, 0.9, 0.82, 1)
        self.app.camera.setPos(0, -7.5, 2.6)
        self.app.camera.lookAt(0, 0, 1.2)
        L = self.loader
        box(self.root, L, (40, 40, 0.2), (0.75, 0.68, 0.55), (0, 0, -0.1))  # parquet
        box(self.root, L, (30, 0.3, 12), (0.88, 0.9, 0.95), (0, 9, 5.9))  # parete
        box(self.root, L, (4, 0.1, 2.6), (0.65, 0.85, 1.0), (-6.5, 8.8, 3.4))  # finestra
        box(self.root, L, (2.6, 2.4, 0.06), (0.8, 0.25, 0.3), (0, 0, 0.03))  # tappetino
        for x in (-3.2, 3.2):  # manubri
            box(self.root, L, (0.9, 0.12, 0.12), (0.25, 0.25, 0.3), (x, 0.5, 0.35))
            for s in (-1, 1):
                blob(self.root, L, (0.22, 0.22, 0.22), (0.2, 0.2, 0.25), (x + s * 0.5, 0.5, 0.35))
        blob(self.root, L, (0.7, 0.7, 0.9), (0.25, 0.6, 0.3), (-7, 5, 0.9))  # pianta
        box(self.root, L, (0.5, 0.5, 0.4), (0.6, 0.35, 0.2), (-7, 5, 0.2))
        self.shadow = make_shadow(self.root, L, 0.8)
        # indicatore del peso: la pallina sale se spingi, scende se ti abbassi; le tacche sono le soglie
        box(self.root, L, (0.28, 0.08, 3.4), (0.35, 0.35, 0.42), (2.9, 0.2, 1.7))
        for s in (-1, 1):
            box(self.root, L, (0.5, 0.1, 0.05), (0.3, 0.85, 0.4), (2.9, 0.15, 1.7 + s * self.th * 7))
        self.gauge = blob(self.root, L, (0.17, 0.17, 0.17), (0.95, 0.85, 0.2), (2.9, 0.1, 1.7))
        self.peng = make_penguin(self.root, L)
        self.peng.setH(180)
        self.base = None
        self.cal_t = 0.0
        self.cal_sum = 0.0
        self.cal_n = 0
        self.state = "up"
        self.state_t = 0.0
        self.depth = 0.0
        self.depth_target = 0.0
        self.reps = 0
        self.time_left += 1.5  # la calibrazione non conta

    def medals(self):
        return ((400, 800, 1200), (600, 1000, 1500), (800, 1300, 1800))[self.diff]

    def _set_depth(self, dt):
        self.depth += (self.depth_target - self.depth) * min(1.0, 8 * dt)
        s = 0.9
        self.peng.setScale(s * (1 + 0.1 * self.depth), s * (1 + 0.1 * self.depth), s * (1 - 0.4 * self.depth))
        set_flippers(self.peng, 25 + 60 * self.depth)  # braccia in avanti per bilanciarsi

    def update(self, dt, inp):
        if self.base is None:
            self.cal_t += dt
            self.cal_sum += inp.total
            self.cal_n += 1
            self.hud_msg["text"] = "Resta in piedi, fermo..."
            if self.cal_t >= 1.5 and self.cal_n:
                self.base = max(self.cal_sum / self.cal_n, 1.0)
                self.app.sound.play("ok")
            return
        ratio = inp.total / self.base
        self.gauge.setZ(1.7 + clamp((ratio - 1) * 7, -1.6, 1.6))
        self.state_t += dt
        if self.state == "up":
            self.hud_msg["text"] = f"Ripetizioni: {self.reps}  -  scendi!"
            if ratio < 1 - self.th:
                self.state, self.state_t, self.depth_target = "down", 0.0, 1.0
        elif self.state == "down":
            self.hud_msg["text"] = "Giu'... ora risali!"
            if ratio > 1 + self.th:
                self.state, self.state_t, self.depth_target = "push", 0.0, 0.4
        elif self.state == "push":
            self.hud_msg["text"] = "Risali in piedi"
            if abs(ratio - 1) < self.th * 0.6:
                self.reps += 1
                self.score += 100
                self.app.sound.play("rep")
                self.fx.burst((0, -0.5, 2.2), ((1, 0.85, 0.2), (1, 1, 1), (0.4, 0.8, 1)), 14, 2.5, 0.8, 0.1, up=3.5)
                self.state, self.state_t, self.depth_target = "up", 0.0, 0.0
        if self.state != "up" and self.state_t > 4.0:  # ripetizione abbandonata
            self.state, self.state_t, self.depth_target = "up", 0.0, 0.0
        self._set_depth(dt)
