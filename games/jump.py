"""Salto: salta piu' in alto che puoi. L'altezza si calcola dal tempo in cui non pesi sulla board."""
from gamekit import Game, box, make_penguin, perspective

G = 9.81
VISUAL_SCALE = 3.0  # il salto sullo schermo e' esagerato per renderlo leggibile


class Jump(Game):
    key = "jump"
    title = "Salto"
    blurb = "Salta piu' in alto che puoi, poi ricomponiti e salta ancora"
    music = "action"
    duration = 45.0

    def setup(self):
        self.min_h = (4.0, 7.0, 10.0)[self.diff]  # cm minimi perche' il salto conti
        perspective(self.app, 50)
        self.app.setBackgroundColor(0.7, 0.88, 1.0, 1)
        self.app.camera.setPos(0, -9, 3.2)
        self.app.camera.lookAt(0, 0, 2.0)
        L = self.loader
        box(self.root, L, (40, 40, 0.2), (0.55, 0.8, 0.5), (0, 0, -0.1))
        self.peng = make_penguin(self.root, L)
        self.peng.setH(180)
        self.record = box(self.root, L, (3.0, 0.05, 0.04), (0.9, 0.2, 0.25), (0, 0, -1.0))
        self.base = None
        self.cal_t = self.cal_sum = self.cal_n = 0
        self.air = False
        self.air_t = 0.0
        self.best = 0.0
        self.jumps = 0
        self.anim_t = None
        self.anim_T = 0.0
        self.anim_H = 0.0

    def medals(self):
        return ((600, 1200, 1900), (800, 1600, 2400), (1000, 2000, 3000))[self.diff]

    def update(self, dt, inp):
        if self.base is None:  # calibrazione: in piedi, fermo
            self.time_left += dt
            self.cal_t += dt
            self.cal_sum += inp.total
            self.cal_n += 1
            self.hud_msg["text"] = "Resta in piedi, fermo..."
            if self.cal_t >= 1.5:
                self.base = max(self.cal_sum / self.cal_n, 1.0)
                self.hud_msg["text"] = "Salta!"
                self.app.sound.play("ok")
            return
        ratio = inp.total / self.base
        if not self.air:
            if ratio < 0.25:
                self.air, self.air_t = True, 0.0
        else:
            self.air_t += dt
            if ratio > 0.5:  # atterrato
                self.air = False
                t = self.air_t
                if 0.15 <= t <= 0.9:
                    h = G * t * t / 8 * 100  # cm
                    if h >= self.min_h:
                        self.jumps += 1
                        self.score += round(h * 10)
                        vis = h / 100 * VISUAL_SCALE
                        if h > self.best:
                            self.best = h
                            self.record.setZ(vis + 0.05)  # linea del record
                            self.app.sound.play("medal")
                        else:
                            self.app.sound.play("jump")
                        self.anim_t, self.anim_T, self.anim_H = 0.0, t, vis
                        self.hud_msg["text"] = f"{h:.0f} cm!   Record: {self.best:.0f} cm"
            elif self.air_t > 1.2:
                self.air = False
        if self.anim_t is not None:
            self.anim_t += dt
            u = self.anim_t / max(self.anim_T, 0.01)
            if u >= 1:
                self.anim_t = None
                self.peng.setZ(0)
            else:
                self.peng.setZ(4 * self.anim_H * u * (1 - u))
