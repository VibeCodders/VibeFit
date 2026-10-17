"""Voce italiana: le frasi vengono sintetizzate una volta con la voce di Windows (SAPI) in assets/voice/.

Se la voce italiana non e' installata, il gioco funziona senza voce.
"""
import subprocess
import sys

from panda3d.core import Filename

from paths import DATA_DIR

OUT = DATA_DIR / "assets" / "voice"
VOICE_NAME = "Microsoft Elsa Desktop"

BASE = {
    "go": "Via!",
    "gold": "Medaglia d'oro! Complimenti!",
    "silver": "Medaglia d'argento! Ottimo lavoro!",
    "bronze": "Medaglia di bronzo! Bravo!",
    "nomedal": "Riprova, puoi fare di meglio!",
    "record": "Nuovo record! Fantastico!",
    "cheer1": "Continua così!",
    "cheer2": "Ottimo ritmo!",
    "cheer3": "Bravissimo, non mollare!",
    "session_start": "Iniziamo l'allenamento di oggi!",
    "session_done": "Allenamento completato! Ottimo lavoro!",
    "next": "Prossimo esercizio.",
    "hold": "Tieni la posizione!",
    "stepon": "Sali sulla board.",
    "cal_left": "Calibrazione dello yoga: appoggia tutto il peso sulla gamba sinistra, alzando l'altra.",
    "cal_right": "Ora appoggia tutto il peso sulla gamba destra.",
    "cal_done": "Calibrazione completata.",
}

PS_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $s.SelectVoice('%s') } catch { exit 2 }
Get-Content -Encoding UTF8 phrases.txt | ForEach-Object {
    $k, $t = $_ -split "`t", 2
    $s.SetOutputToWaveFile("$k.wav")
    $s.Speak($t)
    $s.SetOutputToNull()
}
""" % VOICE_NAME


class Voice:
    def __init__(self, loader, phrases):
        self.loader = loader
        self.enabled = True
        self.cache = {}
        self.current = None
        self.proc = None
        OUT.mkdir(parents=True, exist_ok=True)
        todo = {k: t for k, t in phrases.items() if not (OUT / f"{k}.wav").exists()}
        if todo and sys.platform == "win32":
            (OUT / "phrases.txt").write_text("\n".join(f"{k}\t{t}" for k, t in todo.items()), encoding="utf-8")
            (OUT / "gen.ps1").write_text(PS_SCRIPT, encoding="utf-8")
            self.proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "gen.ps1"],
                cwd=OUT, creationflags=0x08000000)  # senza finestra

    def _ready(self):
        return self.proc is None or self.proc.poll() is not None

    def say(self, key):
        """Pronuncia la frase; restituisce la durata in secondi (0 se non disponibile)."""
        if not self.enabled or not self._ready():
            return 0.0
        path = OUT / f"{key}.wav"
        if not path.exists():
            return 0.0
        snd = self.cache.get(key)
        if snd is None:
            snd = self.loader.loadSfx(Filename.fromOsSpecific(str(path)))
            self.cache[key] = snd
        if self.current is not None:
            self.current.stop()
        snd.play()
        self.current = snd
        return snd.length()

    def stop(self):
        if self.current is not None:
            self.current.stop()
