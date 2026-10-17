"""VibeFit: menu, profili, pesata e storico."""
import collections
import datetime
import math
import time
import types

from direct.gui.DirectGui import DirectButton, DirectEntry, DirectFrame, DirectLabel
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (AmbientLight, DirectionalLight, LineSegs, OrthographicLens, TextNode,
                          WindowProperties, loadPrcFileData)

from audio import Sound
from balance_board import BOARD_LENGTH_MM, BOARD_WIDTH_MM, BalanceBoard
from db import Store
from games import GAMES
from gamekit import clamp

loadPrcFileData("", "window-title VibeFit\nwin-size 1100 700")

SCALE = 0.01
BG = (0.55, 0.78, 0.9, 1)
BTN = (0.2, 0.55, 0.45, 1)
INK = (0.1, 0.15, 0.2, 1)


class VibeFit(ShowBase):
    def __init__(self):
        super().__init__()
        self.setBackgroundColor(*BG)
        self.disableMouse()
        self.store = Store()
        self.profile = None
        self.board = BalanceBoard()
        self.board_error = None
        self.offsets = [0.0] * 4
        self.tared = False
        self.root = None
        self.task = None
        self.game = None
        self.difficulty = 1  # 0 facile, 1 normale, 2 difficile
        self.use_keyboard = False
        self.keys = set()
        self.kb = [0.0, 0.0]
        self.inp = types.SimpleNamespace(x=0.0, y=0.0, total=0.0, present=False)
        self.sound = Sound(self.loader)
        self._build_scene()
        self.accept("escape", self.userExit)
        self.accept("f11", self.toggle_fullscreen)
        self.accept("aspectRatioChanged", self._on_aspect)
        for k in ("arrow_left", "arrow_right", "arrow_up", "arrow_down"):
            self.accept(k, self.keys.add, [k])
            self.accept(k + "-up", self.keys.discard, [k])
        self.sound.music("menu")
        self.show_profiles()

    # ---------- finestra e camera ----------
    def toggle_fullscreen(self):
        props = WindowProperties()
        if self.win.isFullscreen():
            props.setFullscreen(False)
            props.setSize(1100, 700)
        else:
            props.setFullscreen(True)
            props.setSize(self.pipe.getDisplayWidth(), self.pipe.getDisplayHeight())
        self.win.requestProperties(props)

    def _on_aspect(self):
        lens = self.cam.node().getLens()
        if isinstance(lens, OrthographicLens):
            lens.setFilmSize(8.0, 8.0 / self.getAspectRatio())
        else:
            lens.setAspectRatio(self.getAspectRatio())

    def _topdown(self):
        """Camera ortografica dall'alto, usata da pesata e test di equilibrio."""
        self.camera.setPos(0, 0, 20)
        self.camera.setHpr(0, -90, 0)
        self.ortho.setFilmSize(8.0, 8.0 / self.getAspectRatio())
        self.cam.node().setLens(self.ortho)
        self.setBackgroundColor(*BG)

    # ---------- scena 3D (visibile solo durante la pesata) ----------
    def _build_scene(self):
        self.scene = self.render.attachNewNode("scene")
        self.scene.hide()
        # vista dall'alto, ortografica: la board appare piatta e frontale
        self.camera.setPos(0, 0, 20)
        self.camera.setHpr(0, -90, 0)
        self.ortho = OrthographicLens()
        self.ortho.setNearFar(1, 100)
        self._topdown()
        light = DirectionalLight("sun")
        light.setColor((0.9, 0.9, 0.85, 1))
        ln = self.render.attachNewNode(light)
        ln.setHpr(-30, -50, 0)
        self.render.setLight(ln)
        amb = AmbientLight("amb")
        amb.setColor((0.45, 0.45, 0.5, 1))
        self.render.setLight(self.render.attachNewNode(amb))
        w, l = BOARD_WIDTH_MM * SCALE, BOARD_LENGTH_MM * SCALE
        for dims, z, color in (((w, l, 0.4), -0.2, (0.95, 0.95, 0.95, 1)),):
            wrapper = self.scene.attachNewNode("box")
            box = self.loader.loadModel("models/box")
            box.reparentTo(wrapper)
            box.setScale(*dims)
            box.setPos(-dims[0] / 2, -dims[1] / 2, 0)
            box.setTextureOff(1)
            box.setColor(*color)
            wrapper.setPos(0, 0, z)
        guide = LineSegs()  # croce al centro della board
        guide.setColor(0.6, 0.6, 0.65, 1)
        guide.moveTo(-w / 2, 0, 0.21)
        guide.drawTo(w / 2, 0, 0.21)
        guide.moveTo(0, -l / 2, 0.21)
        guide.drawTo(0, l / 2, 0.21)
        self.scene.attachNewNode(guide.create())
        self.marker = self.loader.loadModel("models/misc/sphere")
        self.marker.reparentTo(self.scene)
        self.marker.setScale(0.25)
        self.marker.setColor(0.9, 0.2, 0.25, 1)
        self.marker.setZ(0.2)
        self.target = self.loader.loadModel("models/misc/sphere")
        self.target.reparentTo(self.scene)
        self.target.setScale(0.35)
        self.target.setColor(0.2, 0.8, 0.3, 0.6)
        self.target.setTransparency(True)
        self.target.setZ(0.0)  # sotto il marker, cosi' la pallina rossa resta visibile

    # ---------- utilita' GUI ----------
    def _screen(self, title=None):
        if self.task:
            self.taskMgr.remove(self.task)
            self.task = None
        if self.game:
            self.game.cleanup()
            self.game = None
        if self.root:
            self.root.destroy()
        self.scene.hide()
        self.target.hide()
        self._topdown()
        self.root = DirectFrame(frameColor=(0, 0, 0, 0))
        if title:
            self.label(title, (0, 0, 0.8), 0.12)
        return self.root

    def label(self, text, pos, scale=0.07, align=TextNode.ACenter):
        return DirectLabel(parent=self.root, text=text, pos=pos, scale=scale, text_fg=INK,
                           text_align=align, frameColor=(0, 0, 0, 0))

    def button(self, text, pos, cmd, scale=0.08, width=7):
        return DirectButton(parent=self.root, text=text, pos=pos, scale=scale, command=cmd,
                            frameColor=BTN, text_fg=(1, 1, 1, 1), frameSize=(-width, width, -0.8, 1.0),
                            relief=1, pressEffect=1, clickSound=self.sound.sfx["click"])

    def entry(self, pos, initial=""):
        return DirectEntry(parent=self.root, pos=pos, scale=0.07, initialText=initial, width=14,
                           numLines=1, focus=0, frameColor=(1, 1, 1, 1), text_fg=INK)

    # ---------- profili ----------
    def show_profiles(self):
        self._screen("Chi sei?")
        profiles = self.store.list_profiles()
        y = 0.55
        for p in profiles[:7]:
            self.button(p["name"], (0, 0, y), lambda pid=p["id"]: self.select_profile(pid))
            y -= 0.17
        if not profiles:
            self.label("Nessun profilo: creane uno!", (0, 0, 0.4))
        self.button("+ Nuovo profilo", (0, 0, -0.75), self.show_new_profile, width=8)

    def select_profile(self, pid):
        self.profile = self.store.get_profile(pid)
        self.show_menu()

    def show_new_profile(self, error=""):
        self._screen("Nuovo profilo")
        self.label("Nome", (-0.5, 0, 0.5), align=TextNode.ARight)
        self.label("Altezza (cm)", (-0.5, 0, 0.3), align=TextNode.ARight)
        self.label("Anno di nascita", (-0.5, 0, 0.1), align=TextNode.ARight)
        name = self.entry((-0.4, 0, 0.5))
        height = self.entry((-0.4, 0, 0.3), "170")
        year = self.entry((-0.4, 0, 0.1), "1990")
        self.label(error, (0, 0, -0.15), 0.06)

        def save():
            n = name.get().strip()
            try:
                h = float(height.get().replace(",", "."))
                y = int(year.get())
            except ValueError:
                return self.show_new_profile("Altezza e anno devono essere numeri.")
            if not n:
                return self.show_new_profile("Inserisci un nome.")
            if not 80 <= h <= 250 or not 1900 <= y <= datetime.date.today().year:
                return self.show_new_profile("Altezza o anno non validi.")
            try:
                pid = self.store.add_profile(n, h, y)
            except Exception:  # nome duplicato
                return self.show_new_profile("Esiste gia' un profilo con questo nome.")
            self.select_profile(pid)

        self.button("Salva", (-0.45, 0, -0.5), save, width=5)
        self.button("Annulla", (0.45, 0, -0.5), self.show_profiles, width=5)

    # ---------- menu ----------
    def show_menu(self):
        self._screen(f"Ciao, {self.profile['name']}!")
        self.button("Pesati", (0, 0, 0.5), self.show_weigh, width=8)
        self.button("Test di equilibrio", (0, 0, 0.3), self.show_balance, width=8)
        self.button("Storico peso", (0, 0, 0.1), self.show_history, width=8)
        self.button("Storico equilibrio", (0, 0, -0.1), self.show_balance_history, width=8)
        self.button("Cambia profilo", (0, 0, -0.3), self.show_profiles, width=8)
        self.button("Esci", (0, 0, -0.5), self.userExit, width=8)
        self.status = self.label("", (0, 0, -0.75), 0.055)

    def ensure_board(self):
        if self.board.connected:
            return True
        try:
            self.board.open()
            return True
        except Exception as e:  # noqa: BLE001
            self.board_error = str(e)
            return False

    # ---------- pesata ----------
    def show_weigh(self):
        if not self.ensure_board():
            self.show_menu()
            self.status["text"] = ("Board non raggiunta. Accendila (tasto power) e riprova.\n"
                                   f"({self.board_error})")
            return
        self._screen("Pesata")
        self.scene.show()
        self.msg = self.label("", (0, 0, 0.65), 0.08)
        self.big = self.label("", (0, 0, -0.7), 0.18)
        self.button("Indietro", (1.15, 0, -0.85), self.show_menu, scale=0.06, width=4)
        self.phase = "empty"
        self.empty_since = None
        self.samples = collections.deque()
        self.task = self.taskMgr.add(self._weigh_task, "weigh")

    def _cog(self, kg, total):
        if total <= 2.0:
            return 0.0, 0.0
        tr, br, tl, bl = kg
        x = ((tr + br) - (tl + bl)) / total * (BOARD_WIDTH_MM / 2)
        y = ((tl + tr) - (bl + br)) / total * (BOARD_LENGTH_MM / 2)
        return x, y

    def _weigh_task(self, task):
        now = time.time()
        raw = self.board.kg
        total = sum(raw)
        if self.phase == "empty":
            self.msg["text"] = "Non salire ancora: sto azzerando la board..."
            self.big["text"] = ""
            if abs(total) > 4.0:
                self.msg["text"] = "Scendi dalla board"
                self.empty_since = None
            elif self.empty_since is None:
                self.empty_since = now
            elif now - self.empty_since > 1.5:
                self.offsets = list(raw)
                self.tared = True
                self.phase = "step"
        else:
            kg = [r - o for r, o in zip(raw, self.offsets)]
            total = sum(kg)
            self._move_marker(kg, total)
            if self.phase == "step":
                self.msg["text"] = "Sali sulla board e resta fermo"
                self.big["text"] = f"{max(total, 0):.1f} kg"
                if total > 10:
                    self.phase = "hold"
                    self.samples.clear()
            elif self.phase == "hold":
                if total < 10:
                    self.phase = "step"
                    return task.cont
                self.samples.append((now, total))
                while self.samples and now - self.samples[0][0] > 2.5:
                    self.samples.popleft()
                vals = [v for _, v in self.samples]
                span = now - self.samples[0][0]
                self.big["text"] = f"{total:.1f} kg"
                self.msg["text"] = "Resta fermo..."
                if span > 2.2 and max(vals) - min(vals) < 0.5:
                    self._finish_weigh(sum(vals) / len(vals))
                    return task.done
        return task.cont

    def _move_marker(self, kg, total):
        x, y = self._cog(kg, total)
        self.marker.setPos(x * SCALE, y * SCALE, 0.2)
        return x, y

    # ---------- test di equilibrio ----------
    STILL_SECS = 20.0
    FOLLOW_SECS = 20.0

    def show_balance(self):
        if not self.ensure_board():
            self.show_menu()
            self.status["text"] = ("Board non raggiunta. Accendila (tasto power) e riprova.\n"
                                   f"({self.board_error})")
            return
        self._screen("Test di equilibrio")
        self.scene.show()
        self.msg = self.label("", (0, 0, 0.65), 0.08)
        self.big = self.label("", (0, 0, -0.7), 0.18)
        self.button("Indietro", (1.15, 0, -0.85), self.show_menu, scale=0.06, width=4)
        self.phase = "step" if self.tared else "empty"
        self.empty_since = None
        self.t0 = None
        self.pos_still = []
        self.err_follow = []
        self.task = self.taskMgr.add(self._balance_task, "balance")

    def _balance_task(self, task):
        now = time.time()
        raw = self.board.kg
        if self.phase == "empty":
            self.msg["text"] = "Non salire ancora: sto azzerando la board..."
            if abs(sum(raw)) > 4.0:
                self.msg["text"] = "Scendi dalla board"
                self.empty_since = None
            elif self.empty_since is None:
                self.empty_since = now
            elif now - self.empty_since > 1.5:
                self.offsets = list(raw)
                self.tared = True
                self.phase = "step"
            return task.cont

        kg = [r - o for r, o in zip(raw, self.offsets)]
        total = sum(kg)
        x, y = self._cog(kg, total)
        self.marker.setPos(x * SCALE, y * SCALE, 0.2)

        if total < 10 and self.phase != "step":  # sceso dalla board: ricomincia
            self.phase = "step"
            self.target.hide()
        if self.phase == "step":
            self.msg["text"] = "Sali sulla board a piedi uniti"
            self.big["text"] = ""
            if total > 10:
                self.phase, self.t0 = "settle", now
        elif self.phase == "settle":
            self.msg["text"] = "Bene, resta fermo..."
            if now - self.t0 > 1.5:
                self.phase, self.t0 = "count", now
        elif self.phase == "count":
            left = 3 - int(now - self.t0)
            self.msg["text"] = "Parte il test: stai fermo, guarda avanti"
            self.big["text"] = str(left)
            if now - self.t0 >= 3:
                self.phase, self.t0 = "still", now
                self.pos_still = []
        elif self.phase == "still":
            self.pos_still.append((x, y))
            left = self.STILL_SECS - (now - self.t0)
            self.msg["text"] = "Stai fermo il piu' possibile"
            self.big["text"] = f"{max(left, 0):.0f}"
            if left <= 0:
                self.phase, self.t0 = "intro", now
        elif self.phase == "intro":
            self.msg["text"] = "Ora segui il bersaglio verde col baricentro (pallina rossa)"
            self.big["text"] = ""
            if now - self.t0 > 4:
                self.phase, self.t0 = "follow", now
                self.err_follow = []
                self.target.show()
        elif self.phase == "follow":
            t = now - self.t0
            tx = 80 * math.sin(2 * math.pi * t / 26)
            ty = 45 * math.sin(2 * math.pi * t / 17 + 1.0)
            self.target.setPos(tx * SCALE, ty * SCALE, 0.0)
            self.err_follow.append(math.hypot(x - tx, y - ty))
            left = self.FOLLOW_SECS - t
            self.msg["text"] = "Segui il bersaglio verde"
            self.big["text"] = f"{max(left, 0):.0f}"
            if left <= 0:
                self._finish_balance()
                return task.done
        return task.cont

    @staticmethod
    def _clamp(v, lo=0.0, hi=100.0):
        return max(lo, min(hi, v))

    def _finish_balance(self):
        n = len(self.pos_still)
        mx = sum(p[0] for p in self.pos_still) / n
        my = sum(p[1] for p in self.pos_still) / n
        rms = math.sqrt(sum((p[0] - mx) ** 2 + (p[1] - my) ** 2 for p in self.pos_still) / n)
        score_still = self._clamp(100 - (rms - 5) * 2.5)
        err = sum(self.err_follow) / len(self.err_follow)
        score_follow = self._clamp(100 - (err - 15) * 100 / 45)
        score = (score_still + score_follow) / 2
        age = 20 + (100 - score) * 0.6
        self.store.add_balance_test(self.profile["id"], score_still, score_follow, age)
        real_age = datetime.date.today().year - self.profile["birth_year"]
        self._screen("Risultato equilibrio")
        self.label(f"Eta' d'equilibrio: {age:.0f} anni", (0, 0, 0.5), 0.13)
        self.label(f"(la tua eta': {real_age})", (0, 0, 0.33), 0.06)
        self.label(f"Fermo: {score_still:.0f}/100   (oscillazione {rms:.1f} mm)", (0, 0, 0.1), 0.075)
        self.label(f"Bersaglio: {score_follow:.0f}/100   (errore medio {err:.1f} mm)", (0, 0, -0.05), 0.075)
        self.button("Storico", (-0.45, 0, -0.4), self.show_balance_history, width=5)
        self.button("Menu", (0.45, 0, -0.4), self.show_menu, width=5)

    def _finish_weigh(self, kg):
        self.store.add_weight(self.profile["id"], kg)
        h = self.profile["height_cm"] / 100
        bmi = kg / (h * h)
        if bmi < 18.5:
            cat = "sottopeso"
        elif bmi < 25:
            cat = "normopeso"
        elif bmi < 30:
            cat = "sovrappeso"
        else:
            cat = "obesita'"
        self._screen("Risultato")
        self.label(f"{kg:.1f} kg", (0, 0, 0.45), 0.2)
        self.label(f"BMI {bmi:.1f} ({cat})", (0, 0, 0.15), 0.09)
        self.button("Storico", (-0.45, 0, -0.4), self.show_history, width=5)
        self.button("Menu", (0.45, 0, -0.4), self.show_menu, width=5)

    # ---------- storico ----------
    def show_history(self):
        rows = [{"ts": r["ts"], "v": r["kg"]} for r in self.store.weights(self.profile["id"])]
        self._graph("Storico peso", rows, "kg", "Ancora nessuna pesata.", "pesate")

    def show_balance_history(self):
        rows = [{"ts": r["ts"], "v": r["balance_age"]}
                for r in self.store.balance_tests(self.profile["id"])]
        self._graph("Storico equilibrio", rows, "anni", "Ancora nessun test.", "test", 0)

    def _graph(self, title, rows, unit, empty_msg, noun, decimals=1):
        self._screen(title)
        self.button("Indietro", (1.15, 0, -0.85), self.show_menu, scale=0.06, width=4)
        if not rows:
            self.label(empty_msg, (0, 0, 0.2))
            return
        lo = min(r["v"] for r in rows) - 1
        hi = max(r["v"] for r in rows) + 1
        t0, t1 = rows[0]["ts"], rows[-1]["ts"]
        X0, X1, Y0, Y1 = -1.1, 1.1, -0.5, 0.55

        def pt(r):
            fx = 0.5 if t1 == t0 else (r["ts"] - t0) / (t1 - t0)
            return X0 + fx * (X1 - X0), Y0 + (r["v"] - lo) / (hi - lo) * (Y1 - Y0)

        axes = LineSegs()
        axes.setColor(*INK)
        axes.moveTo(X0, 0, Y1)
        axes.drawTo(X0, 0, Y0)
        axes.drawTo(X1, 0, Y0)
        self.root.attachNewNode(axes.create())
        line = LineSegs()
        line.setThickness(3)
        line.setColor(0.8, 0.2, 0.25, 1)
        for i, r in enumerate(rows):
            x, y = pt(r)
            (line.moveTo if i == 0 else line.drawTo)(x, 0, y)
        self.root.attachNewNode(line.create())
        self.label(f"{hi:.0f} {unit}", (X0 - 0.03, 0, Y1), 0.05, TextNode.ARight)
        self.label(f"{lo:.0f} {unit}", (X0 - 0.03, 0, Y0), 0.05, TextNode.ARight)
        last = rows[-1]
        when = datetime.datetime.fromtimestamp(last["ts"]).strftime("%d/%m/%Y %H:%M")
        self.label(f"Ultimo: {last['v']:.{decimals}f} {unit} ({when}) - {len(rows)} {noun}",
                   (0, 0, -0.65), 0.06)

    def destroy(self):
        self.board.close()
        super().destroy()


if __name__ == "__main__":
    VibeFit().run()
