"""Squat: scendi e risali a ritmo regolare. Le ripetizioni si riconoscono dalla variazione del peso."""
from gamekit import Game, box, clamp, make_penguin, perspective


class Squat(Game):
    key = "squat"
    title = "Squat"
    blurb = "Stai in piedi fermo, poi fai squat: scendi e risali con calma"
    music = "calm"
    duration = 45.0

    def setup(self):
        self.th = (0.06, 0.08, 0.10)[self.diff]  # variazione relativa del peso richiesta
        perspective(self.app, 50)
        self.app.setBackgroundColor(0.78, 0.9, 0.82, 1)
        self.app.camera.setPos(0, -7.5, 2.6)
        self.app.camera.lookAt(0, 0, 1.2)
        box(self.root, self.loader, (40, 40, 0.2), (0.62, 0.8, 0.62), (0, 0, -0.1))
        self.peng = make_penguin(self.root, self.loader)
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
                self.state, self.state_t, self.depth_target = "up", 0.0, 0.0
        if self.state != "up" and self.state_t > 4.0:  # ripetizione abbandonata
            self.state, self.state_t, self.depth_target = "up", 0.0, 0.0
        self._set_depth(dt)
