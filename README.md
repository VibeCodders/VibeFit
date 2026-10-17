# VibeFit

Un gioco di fitness per PC ispirato a Wii Fit, da giocare con la **Wii Balance Board** collegata via Bluetooth.
Protagonista: un pinguino low-poly. Scritto in Python con Panda3D.

## Cosa c'e'

- **11 giochi** con 3 difficolta', medaglie e record per profilo: Slalom sugli sci, Equilibrio sul ghiaccio,
  Calcio di testa, Hula hoop, Squat, Salto, Corsa sul posto, Yoga, Funambolo, Pesca perle, Danza del pinguino.
- **Allenamento di oggi**: 4 giochi diversi ogni giorno, con giorni consecutivi e obiettivo settimanale.
- **Pesata** (con BMI), **test di equilibrio** (eta' d'equilibrio) e **statistiche** (minuti, calorie, grafici).
- Musiche, effetti sonori e **voce italiana** sintetizzati sul posto (nessun file audio da scaricare).
- Si gioca anche **senza board**, con la tastiera: frecce, W/S = piu'/meno peso, SPAZIO = volo (per il salto).

## Avvio da sorgente

```powershell
pip install -r requirements.txt
python app.py
```

## Collegare la Balance Board (Windows)

La board non usa un PIN digitabile: Windows 11 non riesce ad accoppiarla dalle Impostazioni.
Si accoppia con lo script incluso:

1. Rimuovi la board da Impostazioni > Bluetooth, se compare gia'.
2. `python pair_board.py`
3. Subito dopo premi e **tieni premuto** il tasto rosso SYNC (nel vano batterie) finche' lo script non finisce.

Poi accendi la board con il tasto power: l'app si collega da sola. Se la board si spegne durante una partita,
questa va in pausa e riparte quando torna disponibile.

## Eseguibile (.exe)

```powershell
pip install pyinstaller
.\build_exe.ps1
```

Crea `dist\VibeFit\VibeFit.exe`, che non richiede Python. I dati (profili, impostazioni, audio generato)
stanno in `%LOCALAPPDATA%\VibeFit`.

## Test

```powershell
pip install pytest
python -m pytest -q
```

I test coprono la matematica della board, il database e la logica di ogni gioco (rilevamento di giri, squat,
salti, passi, pose...), incluso un controllo che **stare fermi non dia mai medaglie** a nessuna difficolta'.

## Struttura

| File | Contenuto |
| --- | --- |
| `app.py` | Applicazione, menu, partite, allenamento giornaliero |
| `screens.py` | Impostazioni, statistiche, medaglie, aiuto |
| `balance_board.py` | Lettura della board via HID, calibrazione, baricentro |
| `gamekit.py`, `fx.py` | Classe base dei giochi, forme 3D, pinguino, particelle, ombre, scenari |
| `games/` | I giochi (uno per file) |
| `audio.py`, `voice.py` | Musica ed effetti sintetizzati, voce italiana (SAPI) |
| `db.py`, `paths.py` | Database SQLite, percorsi dei dati |
| `pair_board.py` | Accoppiamento Bluetooth della board |

## Sicurezza

Usa la board su un pavimento piano e antiscivolo, con spazio libero attorno, e fermati se senti dolore o
capogiro. Se hai problemi di salute o di equilibrio chiedi prima il parere del medico. Peso massimo della
board: 150 kg.
