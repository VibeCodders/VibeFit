"""Utilita' comuni ai giochi: forme low-poly, mascotte pinguino, classe base Game."""
import random

from panda3d.core import PerspectiveLens, TextNode


def clamp(v, lo=-1.0, hi=1.0):
    return max(lo, min(hi, v))


def box(parent, loader, size, color, pos=(0, 0, 0)):
    """Parallelepipedo colorato con origine al centro."""
    w = parent.attachNewNode("box")
    m = loader.loadModel("models/box")
    m.reparentTo(w)
    m.setScale(*size)
    m.setPos(-size[0] / 2, -size[1] / 2, -size[2] / 2)
    m.setTextureOff(1)
    m.setColor(*color, 1)
    w.setPos(*pos)
    return w


def blob(parent, loader, scale, color, pos=(0, 0, 0), hpr=(0, 0, 0)):
    """Sfera low-poly (raggio 1) scalata, per corpi tondi."""
    m = loader.loadModel("models/misc/sphere")
    m.reparentTo(parent)
    m.setScale(*scale)
    m.setPos(*pos)
    m.setHpr(*hpr)
    m.setTextureOff(1)
    m.setColor(*color, 1)
    return m


def make_penguin(parent, loader):
    """Mascotte: pinguino tondo low-poly, rivolto verso +Y."""
    p = parent.attachNewNode("penguin")
    dark, white, orange = (0.1, 0.13, 0.22), (0.97, 0.97, 0.97), (1.0, 0.6, 0.1)
    blob(p, loader, (0.5, 0.42, 0.65), dark, (0, 0, 0.7))
    blob(p, loader, (0.38, 0.3, 0.52), white, (0, 0.17, 0.66))
    blob(p, loader, (0.36, 0.34, 0.34), dark, (0, 0.02, 1.3))
    feet, flippers, eyes = {}, {}, []
    for s in (-1, 1):
        eyes.append(blob(p, loader, (0.09, 0.07, 0.09), white, (s * 0.14, 0.28, 1.38)))
        eyes.append(blob(p, loader, (0.04, 0.04, 0.04), dark, (s * 0.14, 0.34, 1.38)))
        pivot = p.attachNewNode("flipper")  # l'ala ruota attorno alla spalla
        pivot.setPos(s * 0.48, 0, 0.98)
        blob(pivot, loader, (0.1, 0.25, 0.4), dark, (0, 0, -0.3))
        flippers[s] = pivot
        feet[s] = box(p, loader, (0.22, 0.4, 0.08), orange, (s * 0.2, 0.18, 0.04))
    blob(p, loader, (0.1, 0.2, 0.07), orange, (0, 0.34, 1.25))
    p.setPythonTag("parts", {"feet": feet, "flippers": flippers, "eyes": eyes})
    set_flippers(p, 25)
    return p


def set_flippers(penguin, angle, side=None):
    """Angolo delle ali dal corpo: 0 = lungo il corpo, 90 = orizzontali, 155 = alzate."""
    fl = penguin.getPythonTag("parts")["flippers"]
    for s in (-1, 1):
        if side is None or s == side:
            fl[s].setR(-s * angle)


def perspective(app, fov=60):
    lens = PerspectiveLens()
    lens.setFov(fov)
    lens.setAspectRatio(app.getAspectRatio())
    lens.setNearFar(0.5, 400)
    app.cam.node().setLens(lens)


class Game:
    """Base dei giochi. Le sottoclassi definiscono setup() e update(dt, inp).

    inp ha: x, y (mm del baricentro, x destra / y avanti), total (kg), present (bool).
    Il punteggio sta in self.score; self.done = True termina la partita.
    """
    key = ""
    title = ""
    blurb = ""
    music = "action"
    duration = 45.0
    cheer = True  # ogni tanto la voce incoraggia
    met = 3.5  # equivalente metabolico (stima calorie)

    def __init__(self, app, diff):
        self.cheer_t = random.uniform(10, 16)
        self.app = app
        self.loader = app.loader
        self.diff = diff  # 0 facile, 1 normale, 2 difficile
        self.root = app.render.attachNewNode(self.key)
        self.score = 0
        self.time_left = self.duration
        self.done = False
        self.hud_score = app.label("", (-1.25, 0, 0.88), 0.08, TextNode.ALeft)
        self.hud_time = app.label("", (1.25, 0, 0.88), 0.08, TextNode.ARight)
        self.hud_msg = app.label("", (0, 0, 0.72), 0.07)
        if self.hud_fg:  # scritte chiare per gli sfondi scuri
            for lab in (self.hud_score, self.hud_time, self.hud_msg):
                lab["text_fg"] = self.hud_fg
        from fx import Particles  # import qui: fx importa gamekit
        self.fx = Particles(app.loader, self.root)
        self.mini = app.mini_board() if self.show_mini and hasattr(app, "mini_board") else None
        self.setup()

    hud_fg = None  # colore delle scritte a schermo (None = scuro di default)
    show_mini = True  # piccola board con il pallino del baricentro, in basso a sinistra

    def setup(self):
        pass

    def update(self, dt, inp):
        pass

    def medals(self):
        """Soglie (bronzo, argento, oro) di punteggio."""
        return (100, 200, 300)

    def tick(self, dt, inp):
        self.time_left -= dt
        self.update(dt, inp)
        self.fx.update(dt)
        if self.mini:
            self.mini(inp.x, inp.y)
        if self.cheer:
            self.cheer_t -= dt
            if self.cheer_t <= 0 and self.time_left > 5:
                self.app.voice.say(random.choice(("cheer1", "cheer2", "cheer3")))
                self.cheer_t = random.uniform(14, 22)
        self.hud_score["text"] = f"Punti: {int(self.score)}"
        self.hud_time["text"] = f"{max(self.time_left, 0):.0f} s"
        if self.time_left <= 0:
            self.done = True

    def cleanup(self):
        self.root.removeNode()
