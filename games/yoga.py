"""Yoga: prendi la posa e mantieni il baricentro dentro la zona verde per 10 secondi."""
import random

from fx import make_shadow, stones, sun
from gamekit import Game, blob, box, make_penguin, perspective, set_flippers

MM = 0.008  # 1 mm di baricentro = 0.008 unita' nel pannello
PANEL = (3.9, 0.0, 1.7)  # centro del pannello nella scena
PREP, HOLD = 4.0, 10.0

# nome, bersaglio (x, y) in mm, azione sul pinguino
POSES = [
    ("Albero sulla gamba sinistra", (-70, 0), "tree", -1),
    ("Albero sulla gamba destra", (70, 0), "tree", 1),
    ("Guerriero: affondo avanti", (0, 45), "warrior", 0),
    ("Sedia: siediti indietro", (0, -40), "chair", 0),
]


class Yoga(Game):
    key = "yoga"
    title = "Yoga"
    blurb = "Prendi la posa e tieni il baricentro nella zona verde"
    music = "calm"
    met = 2.5  # equivalente metabolico, per stimare le calorie
    duration = len(POSES) * (PREP + HOLD)
    cheer = False
    show_mini = False  # ha gia' il suo pannello

    def setup(self):
        self.said_hold = False
        self.app.voice.say("pose_0")
        self.radius = (35.0, 28.0, 22.0)[self.diff]
        perspective(self.app, 55)
        self.app.setBackgroundColor(0.85, 0.8, 0.95, 1)
        self.app.camera.setPos(1.5, -9.5, 2.2)
        self.app.camera.lookAt(1.5, 0, 1.6)
        L = self.loader
        box(self.root, L, (60, 40, 0.2), (0.75, 0.9, 0.78), (0, 0, -0.1))
        box(self.root, L, (3.2, 3.0, 0.05), (0.55, 0.42, 0.3), (0, 0.2, 0.03))  # stuoia
        stones(self.root, L, 9, 8, 1)
        for x in (-7.5, -6.7, -5.9, 8.8, 9.6):  # bambu'
            h = random.uniform(5, 8)
            box(self.root, L, (0.18, 0.18, h), (0.45, 0.7, 0.35), (x, 5, h / 2))
            for k in range(1, int(h)):
                box(self.root, L, (0.24, 0.24, 0.06), (0.3, 0.55, 0.25), (x, 5, k))
        self.sun = sun(self.root, L, (-9, 30, 10), 2.4, (1.0, 0.9, 0.8))
        self.shadow = make_shadow(self.root, L, 0.9)
        self.shadow.setPos(0, 0, 0.06)
        self.glow_t = 0.0
        self.banked = 0.0
        self.peng = make_penguin(self.root, L)
        self.peng.setH(180)
        self.peng.setScale(1.1)
        self.parts = self.peng.getPythonTag("parts")
        # pannello 2D: la board vista dall'alto (x -> destra, y -> su)
        self.panel = self.root.attachNewNode("panel")
        self.panel.setPos(*PANEL)
        box(self.panel, L, (433 * MM, 0.06, 238 * MM), (0.97, 0.97, 0.97), (0, 0.1, 0))
        box(self.panel, L, (433 * MM, 0.02, 0.02), (0.7, 0.7, 0.75), (0, 0.06, 0))
        box(self.panel, L, (0.02, 0.02, 238 * MM), (0.7, 0.7, 0.75), (0, 0.06, 0))
        self.zone = blob(self.panel, L, (self.radius * MM, 0.02, self.radius * MM), (0.3, 0.8, 0.4), (0, 0.03, 0))
        self.marker = blob(self.panel, L, (0.1, 0.03, 0.1), (0.9, 0.2, 0.25), (0, 0, 0))
        self.pose_i = -1
        self.hold_in = 0.0
        self.hold_total = 0.0
        self._set_pose(0)

    def medals(self):
        return ((400, 600, 800), (500, 700, 900), (600, 800, 950))[self.diff]

    def _set_pose(self, i):
        self.pose_i = i
        name, (tx, ty), kind, sign = POSES[i]
        self.target = (tx, ty)
        self.zone.setPos(tx * MM, 0.03, ty * MM)
        self.hold_in = self.hold_total = 0.0
        p = self.peng
        p.setScale(1.1)
        p.setP(0)
        set_flippers(p, 25)
        for s in (-1, 1):
            f = self.parts["feet"][s]
            f.setZ(0)
            f.setX(s * 0.2)
        if kind == "tree":
            raised = sign  # il piede sollevato e' dal lato locale opposto all'appoggio sullo schermo
            self.parts["feet"][raised].setZ(0.5)
            set_flippers(p, 160)  # braccia alzate sopra la testa
        elif kind == "warrior":
            p.setP(-12)
            set_flippers(p, 90)
            for s in (-1, 1):
                self.parts["feet"][s].setX(s * 0.5)
        elif kind == "chair":
            p.setScale(1.1, 1.1, 0.85)
            p.setP(8)
            set_flippers(p, 70)

    def update(self, dt, inp):
        self.marker.setPos(max(-216, min(216, inp.x)) * MM, 0, max(-119, min(119, inp.y)) * MM)
        elapsed = self.duration - self.time_left
        i = min(int(elapsed // (PREP + HOLD)), len(POSES) - 1)
        t = elapsed - i * (PREP + HOLD)
        if i != self.pose_i:
            earned = 250 * min(1.0, self.hold_in / HOLD)  # punti della posa appena finita
            self.banked += earned
            if earned > 150:
                self.fx.burst((0, 0, 2.0), ((1, 0.85, 0.3), (1, 1, 1), (0.6, 1, 0.7)), 22, 3.0, 1.0, 0.1, up=4.0)
            self.app.sound.play("ok")
            self._set_pose(i)
            self.app.voice.say(f"pose_{i}")
            self.said_hold = False
        if t >= PREP and not self.said_hold:
            self.said_hold = True
            self.app.voice.say("hold")
        name = POSES[i][0]
        inside = ((inp.x - self.target[0]) ** 2 + (inp.y - self.target[1]) ** 2) ** 0.5 < self.radius
        if inside:
            self.zone.setColor(0.3, 0.8, 0.4, 1)
            self.glow_t -= dt
            if self.glow_t <= 0 and t >= PREP:  # scintille di armonia attorno al pinguino
                self.glow_t = 0.12
                self.fx.emit((random.uniform(-0.9, 0.9), random.uniform(-0.3, 0.3), random.uniform(0.2, 1.8)),
                             (0, 0, 0.8), (0.5, 1, 0.6), 1.0, 0.09, 0)
        else:
            self.zone.setColor(0.85, 0.75, 0.3, 1)
        if t < PREP:
            self.hud_msg["text"] = f"{i + 1}/{len(POSES)}  {name}: preparati ({PREP - t:.0f})"
        else:
            self.hold_total += dt
            if inside:
                self.hold_in += dt
            frac = self.hold_in / max(self.hold_total, 1e-3)
            self.hud_msg["text"] = f"{i + 1}/{len(POSES)}  {name}: resisti! {HOLD - (t - PREP):.0f}s  ({frac * 100:.0f}%)"
            self.score = self.banked + 250 * min(1.0, self.hold_in / HOLD)
