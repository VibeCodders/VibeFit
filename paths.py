"""Percorsi dei dati: accanto al codice in sviluppo, in %LOCALAPPDATA%\\VibeFit quando e' un eseguibile."""
import os
import pathlib
import sys

FROZEN = getattr(sys, "frozen", False)
CODE_DIR = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).parent))
if FROZEN:
    DATA_DIR = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home())) / "VibeFit"
else:
    DATA_DIR = pathlib.Path(__file__).parent
DATA_DIR.mkdir(parents=True, exist_ok=True)
