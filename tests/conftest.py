"""Fixture comuni: un'app finta senza finestra per far girare la logica dei giochi nei test."""
import pathlib
import sys
import types

import pytest
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Camera, NodePath

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


class FakeApp:
    """Offre a Game quello che si aspetta da VibeFit (scena, loader, label, suoni)."""

    def __init__(self, base):
        self.loader = base.loader
        self.render = base.render
        self.camera = NodePath("camera")
        self.cam = NodePath(Camera("cam"))
        self.sound = types.SimpleNamespace(play=lambda *_: None)
        self.voice = types.SimpleNamespace(say=lambda *_: 0.0)

    def getAspectRatio(self):
        return 1.5

    def setBackgroundColor(self, *_):
        pass

    def label(self, *_args, **_kw):
        return {"text": ""}


@pytest.fixture(scope="session")
def base():
    b = ShowBase(windowType="none")
    yield b
    b.destroy()


@pytest.fixture
def app(base):
    return FakeApp(base)


def make_input(**kw):
    return types.SimpleNamespace(**{"x": 0.0, "y": 0.0, "total": 70.0, "present": True, **kw})


def run(game, seconds, feed, dt=1 / 60):
    """Fa girare il gioco per `seconds`; feed(t) -> dict di campi dell'input."""
    t = 0.0
    inp = make_input()
    while t < seconds and not game.done:
        for k, v in feed(t).items():
            setattr(inp, k, v)
        game.tick(dt, inp)
        t += dt
    return game


class CalibratableApp(FakeApp):
    """App finta che ricorda la calibrazione dello yoga."""

    def __init__(self, base, shift=None):
        super().__init__(base)
        self.shift = shift

    def get_yoga_shift(self):
        return self.shift

    def set_yoga_shift(self, v):
        self.shift = v


@pytest.fixture
def cal_app(base):
    return CalibratableApp(base)
