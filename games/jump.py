"""Salto: salta piu' in alto che puoi. L'altezza si calcola dal tempo in cui non pesi sulla board."""
from fx import Clouds, follow_shadow, make_shadow, sun
from gamekit import Game, blob, box, make_penguin, perspective, set_flippers

G = 9.81
VISUAL_SCALE = 3.0  # il salto sullo schermo e' esagerato per renderlo leggibile


class Jump(Game):
    key = "jump"
    title = "Salto"
    blurb = "Salta piu' in alto che puoi, poi ricomponiti e salta ancora"
    music = "action"
    met = 6.0  # equivalente metabolico, per stimare le calorie
    duration = 45.0

    def setup(self):
        self.min_h = (4.0, 7.0, 10.0)[self.diff]  # cm minimi perche' il salto conti
        perspective(self.app, 50)
        self.app.setBackgroundColor(0.7, 0.88, 1.0, 1)
        self.app.camera.setPos(0, -9, 3.2)
        self.app.camera.lookAt(0, 0, 2.0)
        L = self.loader
        box(self.root, L, (60, 40, 0.2), (0.55, 0.8, 0.5), (0, 0, -0.1))
        for x, s in ((-9, 4.0), (-3, 3.0), (7, 4.5), (13, 3.2)):  # colline
            blob(self.root, L, (s * 1.8, s * 1.2, s * 0.8), (0.4, 0.72, 0.4), (x, 14, -s * 0.2))
        self.clouds = Clouds(self.root, L, 5, (-25, 25), 20, (7, 12), (1.0, 1.8))
        self.sun = sun(self.root, L, (8, 30, 14), 3.5)
        self.shadow = make_shadow(self.root, L, 0.8)
        self.peng = make_penguin(self.root, L)
        self.peng.setH(180)
        # righello: una tacca ogni 10 cm di salto (altezza esagerata sullo schermo)
        box(self.root, L, (0.05, 0.05, 2.5), (0.3, 0.3, 0.35), (-3.0, 0, 1.25))
        for k in range(1, 9):
            long_tick = k % 5 == 0
            box(self.root, L, (0.5 if long_tick else 0.3, 0.05, 0.04), (0.3, 0.3, 0.35),
                (-3.0, 0, k * 0.1 * VISUAL_SCALE))
        self.record = box(self.root, L, (3.0, 0.05, 0.04), (0.9, 0.2, 0.25), (0, 0, -1.0))
        self.base = None
        self.cal_t = 0.0
        self.cal = []
        self.stable_t = 0.0
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
            self.cal.append(inp.total)
            self.hud_msg["text"] = "Resta in piedi, fermo..."
            if self.cal_t >= 1.5:
                self.base = max(sum(self.cal) / len(self.cal), 1.0)
                self.hud_msg["text"] = "Salta!"
                self.app.sound.play("ok")
            return
        ratio = inp.total / self.base
        self.clouds.update(dt)
        if not self.air:
            if 0.85 < ratio < 1.15:  # la base segue le derive lente quando sei fermo a terra
                self.stable_t += dt
                if self.stable_t > 1.0:
                    self.base += (inp.total - self.base) * min(1.0, 0.5 * dt)
            else:
                self.stable_t = 0.0
            if ratio < 0.25:
                self.air, self.air_t = True, 0.0
        else:
            self.air_t += dt
            if self.anim_t is None:  # sollevamento immediato al distacco, poi il ritorno riproduce il salto vero
                self.peng.setZ(min(self.air_t, 0.3) * 2.0)
            if ratio > 0.5:  # atterrato
                self.air = False
                t = self.air_t
                if self.anim_t is None:
                    self.peng.setZ(0)
                    self.fx.burst((0, 0.3, 0.1), ((0.85, 0.8, 0.65),), 10, 2.2, 0.5, 0.12, up=0.8, gravity=-2)
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
                self.fx.burst((0, 0.3, 0.1), ((0.85, 0.8, 0.65),), 10, 2.2, 0.5, 0.12, up=0.8, gravity=-2)
            else:
                self.peng.setZ(4 * self.anim_H * u * (1 - u))
        z = self.peng.getZ()
        set_flippers(self.peng, 150 if z > 0.05 else 25)  # braccia in alto in volo
        follow_shadow(self.shadow, 0, 0, z)
