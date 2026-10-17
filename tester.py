"""Tester Balance Board: peso e baricentro in tempo reale (Panda3D).

Tasti: SPAZIO = azzera (a vuoto), ESC = esci.
"""
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, TextNode, loadPrcFileData

from balance_board import BOARD_LENGTH_MM, BOARD_WIDTH_MM, BalanceBoard

loadPrcFileData("", "window-title VibeFit - Tester Balance Board\nwin-size 1000 700")

SCALE = 0.01  # 1 unita' Panda = 100 mm


class Tester(ShowBase):
    def __init__(self):
        super().__init__()
        self.setBackgroundColor(0.55, 0.78, 0.9)
        self.disableMouse()
        self.camera.setPos(0, -8, 7)
        self.camera.lookAt(0, 0, 0)

        light = DirectionalLight("sun")
        light.setColor((0.9, 0.9, 0.85, 1))
        ln = self.render.attachNewNode(light)
        ln.setHpr(-30, -50, 0)
        self.render.setLight(ln)
        amb = AmbientLight("amb")
        amb.setColor((0.45, 0.45, 0.5, 1))
        self.render.setLight(self.render.attachNewNode(amb))

        w, l = BOARD_WIDTH_MM * SCALE, BOARD_LENGTH_MM * SCALE
        self.board_np = self._box(w, l, 0.4, (0.95, 0.95, 0.95, 1))
        self.board_np.setPos(0, 0, -0.2)
        for sx in (-1, 1):  # sensori agli angoli
            for sy in (-1, 1):
                foot = self._box(0.5, 0.5, 0.1, (0.3, 0.3, 0.35, 1))
                foot.setPos(sx * (w / 2 - 0.4), sy * (l / 2 - 0.4), 0.02)
        self.marker = self.loader.loadModel("models/misc/sphere")
        self.marker.reparentTo(self.render)
        self.marker.setScale(0.25)
        self.marker.setColor(0.9, 0.2, 0.25, 1)

        self.txt = OnscreenText(text="", pos=(-1.55, 0.9), scale=0.07, align=TextNode.ALeft,
                                fg=(0, 0, 0, 1), mayChange=True)
        OnscreenText(text="SPAZIO = azzera   ESC = esci", pos=(-1.55, -0.95), scale=0.05,
                     align=TextNode.ALeft, fg=(0.2, 0.2, 0.2, 1))

        self.board = BalanceBoard()
        self.offsets = [0.0] * 4
        try:
            self.board.open()
            self.status = ""
        except Exception as e:  # noqa: BLE001
            self.status = f"Board non disponibile: {e}"
        self.accept("space", self.tare)
        self.accept("escape", self.userExit)
        self.taskMgr.add(self.update, "update")

    def _box(self, w, l, h, color):
        np = self.loader.loadModel("models/box")
        np.reparentTo(self.render)
        np.setScale(w, l, h)
        np.setPos(-w / 2, -l / 2, 0)
        np.setColor(*color)
        wrapper = self.render.attachNewNode("box")
        np.reparentTo(wrapper)
        return wrapper

    def tare(self):
        if self.board.connected:
            self.offsets = list(self.board.kg)

    def update(self, task):
        if not self.board.connected:
            self.txt.setText(self.status or "Connessione...")
            return task.cont
        kg = [k - o for k, o in zip(self.board.kg, self.offsets)]
        total = sum(kg)
        x = y = 0.0
        if total > 2.0:
            tr, br, tl, bl = kg
            x = ((tr + br) - (tl + bl)) / total * (BOARD_WIDTH_MM / 2)
            y = ((tl + tr) - (bl + br)) / total * (BOARD_LENGTH_MM / 2)
        self.marker.setPos(x * SCALE, y * SCALE, 0.2)
        self.txt.setText(
            f"Peso: {total:5.1f} kg\n"
            f"Baricentro: x={x:6.1f} mm  y={y:6.1f} mm\n"
            f"TL {kg[2]:5.1f}   TR {kg[0]:5.1f}\n"
            f"BL {kg[3]:5.1f}   BR {kg[1]:5.1f}")
        return task.cont

    def destroy(self):
        self.board.close()
        super().destroy()


if __name__ == "__main__":
    Tester().run()
