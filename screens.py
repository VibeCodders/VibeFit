"""Schermate di contorno: impostazioni, statistiche, medaglie, aiuto. Mixin di VibeFit."""

from direct.gui.DirectGui import DirectFrame
from panda3d.core import TextNode

from games import GAMES

GOALS = (15, 30, 60, 90, 120)  # obiettivi settimanali in minuti
DAYS_IT = ("Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom")

HELP_BASICS = (
    "Accendi la board con il tasto power e premi 'Pesati' o un gioco: l'app si collega da sola.",
    "Quando la board e' vuota viene azzerata da sola: scendi per un secondo e mezzo.",
    "Sali a piedi uniti al centro e muoviti con calma: il gioco legge dove spingi il peso.",
    "Il pallino rosso nei menu di prova e' il tuo baricentro.",
    "Se scendi durante una partita questa va in pausa e riparte quando risali.",
    "Senza board puoi giocare con la tastiera: frecce, W/S = piu'/meno peso, SPAZIO = volo.",
    "Ogni gioco ha 3 difficolta' e da' medaglie di bronzo, argento e oro.",
    "'Allenamento di oggi' propone 4 giochi diversi ogni giorno: fai crescere i giorni di fila!",
)


class ExtraScreens:
    # ---------- impostazioni ----------
    def show_settings(self):
        self._screen("Impostazioni", mascot=None)
        diff = self.DIFF_NAMES[self.difficulty]
        rows = (
            ("Input", "Tastiera" if self.use_keyboard else "Board", self._toggle_input),
            ("Suono", "Spento" if self.sound.muted else "Acceso", self._toggle_sound),
            ("Voce", "Accesa" if self.voice.enabled else "Spenta", self._toggle_voice),
            ("Menu con la board", "Si'" if self.nav_board else "No", self._toggle_nav),
            ("Schermo intero (F11)", "Si'" if self.win.isFullscreen() else "No", self._toggle_fs),
            ("Difficolta'", diff, self._cycle_difficulty),
            ("Obiettivo settimanale", f"{self.weekly_goal} min", self._cycle_goal),
        )
        for i, (name, value, cmd) in enumerate(rows):
            y = 0.58 - i * 0.14
            self.label(name, (-0.1, 0, y - 0.01), 0.065, TextNode.ARight)
            self.button(value, (0.55, 0, y), cmd, scale=0.06, width=5)
        self.label("Menu con la board: inclinati avanti/indietro per scegliere, a destra (tenendo) per confermare.",
                   (0, 0, -0.5), 0.045)
        self.button("Indietro", (1.15, 0, -0.85), self.show_menu, scale=0.06, width=4)

    def _toggle_nav(self):
        self.nav_board = not self.nav_board
        self.store.set_setting("nav_board", int(self.nav_board))
        self.show_settings()

    def _toggle_fs(self):
        self.toggle_fullscreen()
        self.taskMgr.doMethodLater(0.4, lambda t: self.show_settings(), "refresh-settings")

    def _cycle_difficulty(self):
        self._set_difficulty((self.difficulty + 1) % 3, then=self.show_settings)

    def _cycle_goal(self):
        i = GOALS.index(self.weekly_goal) if self.weekly_goal in GOALS else 1
        self.weekly_goal = GOALS[(i + 1) % len(GOALS)]
        self.store.set_setting("goal_min", self.weekly_goal)
        self.show_settings()

    # ---------- statistiche ----------
    def bar(self, x0, x1, y0, y1, color):
        return DirectFrame(parent=self.root, frameColor=color, frameSize=(x0, x1, y0, y1))

    def show_stats(self):
        self._screen("Statistiche")
        pid = self.profile["id"]
        t = self.store.totals(pid)
        streak = self.store.streak(pid)
        boxes = (("Minuti", f"{t['minutes']:.0f}"), ("Calorie", f"{t['kcal']:.0f} kcal"),
                 ("Partite", f"{t['games']}"), ("Giorni di fila", f"{streak}"))
        for i, (name, value) in enumerate(boxes):
            x = -1.05 + i * 0.7
            self.label(value, (x, 0, 0.62), 0.09)
            self.label(name, (x, 0, 0.53), 0.045)

        days = self.store.minutes_by_day(pid, 7)
        week = sum(m for _, m in days)
        goal = self.weekly_goal
        self.label(f"Obiettivo settimanale: {week:.0f} / {goal} minuti"
                   + ("  -  raggiunto!" if week >= goal else ""), (0, 0, 0.38), 0.06)
        self.bar(-1.0, 1.0, 0.27, 0.33, (0.75, 0.82, 0.88, 1))
        done = min(week / goal, 1.0)
        if done > 0:
            self.bar(-1.0, -1.0 + 2.0 * done, 0.27, 0.33, (0.2, 0.7, 0.4, 1) if week >= goal else (0.95, 0.6, 0.15, 1))

        self.label("Minuti negli ultimi 7 giorni", (0, 0, 0.14), 0.05)
        peak = max(max(m for _, m in days), 5.0)
        base, height = -0.35, 0.42
        for i, (d, m) in enumerate(days):
            x = -0.95 + i * 0.3
            self.bar(x - 0.09, x + 0.09, base, base + 0.005, (0.4, 0.4, 0.45, 1))
            if m > 0:
                self.bar(x - 0.09, x + 0.09, base, base + height * m / peak, (0.2, 0.55, 0.45, 1))
                self.label(f"{m:.0f}", (x, 0, base + height * m / peak + 0.02), 0.04)
            self.label(DAYS_IT[d.weekday()], (x, 0, base - 0.07), 0.045)

        self.button("Storico peso", (-0.9, 0, -0.62), self.show_history, scale=0.05, width=6)
        self.button("Storico equilibrio", (0.0, 0, -0.62), self.show_balance_history, scale=0.05, width=6)
        self.button("Medaglie", (0.9, 0, -0.62), self.show_medals, scale=0.05, width=6)
        self.button("Indietro", (1.15, 0, -0.85), self.show_menu, scale=0.06, width=4)

    def show_medals(self):
        self._screen("Medaglie")
        best = self.store.best_medals(self.profile["id"])
        for d, name in enumerate(self.DIFF_NAMES):
            self.label(name, (0.2 + d * 0.5, 0, 0.66), 0.055)
        step = min(0.085, 1.2 / max(len(GAMES), 1))
        for i, cls in enumerate(GAMES):
            y = 0.55 - i * step
            self.label(cls.title, (-0.15, 0, y), 0.055, TextNode.ARight)
            for d in range(3):
                m = best.get((cls.key, d), 0)
                lab = self.label(self.MEDAL_NAMES[m] or "-", (0.2 + d * 0.5, 0, y), 0.055)
                lab["text_fg"] = self.MEDAL_COLORS[m]
        total = sum(1 for v in best.values() if v == 3)
        self.label(f"Ori ottenuti: {total} su {len(GAMES) * 3}", (0, 0, -0.8), 0.055)
        self.button("Indietro", (1.15, 0, -0.85), self.show_stats, scale=0.06, width=4)

    # ---------- aiuto ----------
    def show_help(self, page=0):
        self._screen("Come si gioca")
        if page == 0:
            for i, line in enumerate(HELP_BASICS):
                self.label(line, (0, 0, 0.58 - i * 0.14), 0.05)
            self.button("I giochi >", (0, 0, -0.65), lambda: self.show_help(1), scale=0.06, width=5)
        else:
            step = min(0.115, 1.35 / max(len(GAMES), 1))
            for i, cls in enumerate(GAMES):
                self.label(f"{cls.title}: {cls.blurb}", (0, 0, 0.62 - i * step), 0.046)
            self.button("< Le basi", (0, 0, -0.75), lambda: self.show_help(0), scale=0.06, width=5)
        self.button("Indietro", (1.15, 0, -0.85), self.show_menu, scale=0.06, width=4)
