"""Effetti visivi: particelle, ombre, decorazioni (sole, nuvole, montagne, palme)."""
import math
import random

from panda3d.core import Vec3

from gamekit import blob, box


class Particles:
    """Piccole sfere che volano e si rimpiccioliscono: scintille, polvere, neve, coriandoli."""

    def __init__(self, loader, parent):
        self.parent = parent
        self.proto = loader.loadModel("models/misc/sphere")
        self.items = []

    def emit(self, pos, vel, color, life=0.8, size=0.12, gravity=-9.0):
        n = self.proto.copyTo(self.parent)
        n.setTextureOff(1)
        n.setLightOff()
        n.setColor(*color, 1)
        n.setPos(*pos)
        n.setScale(size)
        self.items.append([n, Vec3(*vel), life, life, gravity, size])

    def burst(self, pos, color, n=12, speed=3.0, life=0.7, size=0.12, up=3.0, gravity=-9.0):
        colors = color if isinstance(color[0], (tuple, list)) else (color,)
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi)
            s = random.uniform(0.35, 1.0) * speed
            vel = (math.cos(a) * s, math.sin(a) * s * 0.4, random.uniform(0.4, 1.0) * up)
            self.emit(pos, vel, random.choice(colors), life * random.uniform(0.7, 1.2), size, gravity)

    def update(self, dt):
        for it in self.items[:]:
            n, vel, t, t0, g, size = it
            vel.setZ(vel.getZ() + g * dt)
            n.setPos(n.getPos() + vel * dt)
            it[2] = t - dt
            if it[2] <= 0:
                n.removeNode()
                self.items.remove(it)
            else:
                n.setScale(size * (it[2] / t0) ** 0.5)

    def clear(self):
        for it in self.items:
            it[0].removeNode()
        self.items = []


def make_shadow(parent, loader, radius=0.6):
    """Ombra tonda sotto un personaggio (si sposta con follow())."""
    n = blob(parent, loader, (radius, radius, 0.02), (0, 0, 0), (0, 0, 0.03))
    n.setTransparency(True)
    n.setColor(0, 0, 0, 0.28)
    n.setLightOff()
    n.setPythonTag("radius", radius)
    return n


def follow_shadow(shadow, x, y, height=0.0):
    """Posiziona l'ombra a terra sotto (x, y); si rimpicciolisce quando il personaggio e' in aria."""
    shadow.setPos(x, y, 0.03)
    k = max(0.3, 1.0 - height * 0.25)
    r = shadow.getPythonTag("radius")
    shadow.setScale(r * k, r * k, 0.02)


# ---------- decorazioni ----------
def sun(parent, loader, pos, size=5.0, color=(1.0, 0.95, 0.55)):
    n = blob(parent, loader, (size, size * 0.4, size), color, pos)
    n.setLightOff()
    return n


def cloud(parent, loader, pos, scale=1.0):
    n = parent.attachNewNode("cloud")
    for dx, dz, s in ((0, 0, 1.6), (1.6, -0.2, 1.2), (-1.5, -0.3, 1.1), (0.4, 0.5, 1.2)):
        c = blob(n, loader, (s * 1.3, s * 0.8, s * 0.7), (1, 1, 1), (dx, 0, dz))
        c.setLightOff()
    n.setScale(scale)
    n.setPos(*pos)
    return n


class Clouds:
    """Nuvole che scorrono lentamente e ricompaiono dall'altra parte."""

    def __init__(self, parent, loader, n, x_range, y, z_range, scale=(1.5, 3.0)):
        self.x_range = x_range
        self.nodes = []  # (nodo, distanza in y da un riferimento che avanza)
        for _ in range(n):
            dy = y + random.uniform(-20, 20)
            pos = (random.uniform(*x_range), dy, random.uniform(*z_range))
            self.nodes.append((cloud(parent, loader, pos, random.uniform(*scale)), dy))

    def update(self, dt, follow_y=None):
        for c, dy in self.nodes:
            c.setX(c.getX() + 0.8 * dt)
            if c.getX() > self.x_range[1]:
                c.setX(self.x_range[0])
            if follow_y is not None:
                c.setY(follow_y + dy)


def mountains(parent, loader, n, x_range, y, height=(18, 34)):
    nodes = []
    for i in range(n):
        h = random.uniform(*height)
        w = h * random.uniform(1.2, 1.8)
        x = x_range[0] + (x_range[1] - x_range[0]) * (i + random.uniform(0.1, 0.9)) / n
        m = parent.attachNewNode("mountain")
        blob(m, loader, (w, w * 0.6, h), (0.55, 0.62, 0.78), (0, 0, 0))
        blob(m, loader, (w * 0.45, w * 0.3, h * 0.42), (0.97, 0.98, 1.0), (0, 0, h * 0.62))
        m.setPos(x, y, -h * 0.25)
        nodes.append(m)
    return nodes


def palm(parent, loader, pos, scale=1.0):
    n = parent.attachNewNode("palm")
    for i in range(5):
        box(n, loader, (0.35, 0.35, 0.8), (0.55, 0.38, 0.2), (0.05 * i, 0, 0.4 + 0.78 * i))
    for k in range(6):
        a = k * 60
        leaf = blob(n, loader, (1.5, 0.3, 0.12), (0.2, 0.62, 0.3), (0, 0, 4.0), (a, 0, 18))
        leaf.setPos(math.cos(math.radians(a)) * 1.2, math.sin(math.radians(a)) * 1.2, 4.0)
    n.setScale(scale)
    n.setPos(*pos)
    return n


def stones(parent, loader, n, spread, y):
    for _ in range(n):
        s = random.uniform(0.25, 0.6)
        g = random.uniform(0.55, 0.75)
        blob(parent, loader, (s, s * 0.9, s * 0.6), (g, g, g + 0.05),
             (random.choice((-1, 1)) * random.uniform(2.5, spread), y + random.uniform(-2, 8), s * 0.3))


def bleachers(parent, loader, side, y0, y1):
    """Tribuna con tifosi colorati (gradini di parallelepipedi)."""
    colors = ((0.9, 0.3, 0.3), (0.3, 0.5, 0.9), (0.95, 0.8, 0.2), (0.4, 0.8, 0.45), (0.9, 0.6, 0.8))
    for row in range(3):
        x = side * (13 + row * 1.6)
        box(parent, loader, (1.6, y1 - y0, 1.0 + row * 1.0), (0.6, 0.6, 0.65), (x, (y0 + y1) / 2, (1.0 + row) / 2))
        for k in range(int((y1 - y0) / 2)):
            blob(parent, loader, (0.5, 0.5, 0.6), random.choice(colors),
                 (x - side * 0.2, y0 + k * 2 + random.uniform(0, 1), 1.0 + row + 0.6))
