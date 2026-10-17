"""Lettura della Wii Balance Board via HID (hidapi). Nessuna dipendenza grafica."""
import threading
import time

import hid

VID, PID = 0x057E, 0x0306
BOARD_WIDTH_MM, BOARD_LENGTH_MM = 433.0, 238.0
REPORT_LEN = 22
SENSORS = ("TR", "BR", "TL", "BL")


class BalanceBoard:
    def __init__(self):
        self.dev = None
        self.calib = None  # 3 livelli (0, 17, 34 kg) x 4 sensori
        self.kg = [0.0] * 4
        self.total = 0.0
        self.cog = (0.0, 0.0)  # mm dal centro, x destra, y avanti
        self.connected = False
        self.error = None
        self.last_data = 0.0
        self._running = False
        self._thread = None
        self._cal_buf = {}

    @property
    def healthy(self):
        """True se la board e' aperta e sta mandando dati (con i report continui arrivano ~100 al secondo)."""
        return self.connected and time.time() - self.last_data < 1.5

    def reopen(self):
        """Chiude e riapre la connessione (dopo uno spegnimento della board). True se riuscita."""
        try:
            self.close()
            self.calib = None
            self._cal_buf = {}
            self.error = None
            self.open()
            return True
        except Exception as e:  # noqa: BLE001
            self.error = str(e)
            return False

    # --- basso livello ---
    def _send(self, *data):
        buf = bytes(data) + bytes(REPORT_LEN - len(data))
        self.dev.write(buf)

    def _write_mem(self, addr, value):
        self._send(0x16, 0x04, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF, 1, value)
        time.sleep(0.05)

    def _read_mem(self, addr, size):
        self._send(0x17, 0x04, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF, size >> 8, size & 0xFF)

    # --- ciclo di vita ---
    def open(self, timeout=5.0):
        self.dev = hid.device()
        self.dev.open(VID, PID)
        self.dev.set_nonblocking(True)
        self._write_mem(0xA400F0, 0x55)  # disattiva cifratura estensione
        self._write_mem(0xA400FB, 0x00)
        self._read_mem(0xA40024, 24)  # calibrazione
        self._send(0x12, 0x04, 0x32)  # report 0x32 (bottoni + 8 byte estensione), continuo
        self._send(0x11, 0x10)  # LED1 acceso
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        t0 = time.time()
        while self.calib is None and time.time() - t0 < timeout:
            time.sleep(0.05)
        if self.calib is None:
            self.close()
            raise RuntimeError("Calibrazione non ricevuta: la board risponde?")
        self.last_data = time.time()
        self.connected = True

    def close(self):
        self._running = False
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=1)
        self._thread = None
        if self.dev:
            try:
                self.dev.close()
            except OSError:
                pass
            self.dev = None
        self.connected = False

    # --- parsing ---
    def _loop(self):
        while self._running:
            try:
                data = self.dev.read(REPORT_LEN)
            except (OSError, ValueError) as e:  # board spenta o scollegata
                self.error = str(e)
                self.connected = False
                return
            if not data:
                time.sleep(0.002)
                continue
            rid = data[0]
            if rid == 0x21:
                self._on_read_reply(data)
            elif rid == 0x32:
                self._on_data(data[3:11])

    def _on_read_reply(self, d):
        size = (d[3] >> 4) + 1
        err = d[3] & 0x0F
        addr = (d[4] << 8) | d[5]
        if err:
            return
        self._cal_buf[addr] = bytes(d[6:6 + size])
        raw = self._cal_buf.get(0x0024, b"") + self._cal_buf.get(0x0034, b"")
        if len(raw) >= 24 and self.calib is None:
            vals = [(raw[i] << 8) | raw[i + 1] for i in range(0, 24, 2)]
            self.calib = [vals[0:4], vals[4:8], vals[8:12]]

    def _to_kg(self, raw, i):
        c0, c17, c34 = self.calib[0][i], self.calib[1][i], self.calib[2][i]
        if raw < c17:
            return 17.0 * (raw - c0) / max(c17 - c0, 1)
        return 17.0 + 17.0 * (raw - c17) / max(c34 - c17, 1)

    def _on_data(self, ext):
        if self.calib is None:
            return
        self.last_data = time.time()
        raws = [(ext[i] << 8) | ext[i + 1] for i in range(0, 8, 2)]
        kg = [self._to_kg(r, i) for i, r in enumerate(raws)]
        total = sum(kg)
        self.kg = kg
        self.total = total
        if total > 2.0:
            tr, br, tl, bl = kg
            x = ((tr + br) - (tl + bl)) / total * (BOARD_WIDTH_MM / 2)
            y = ((tl + tr) - (bl + br)) / total * (BOARD_LENGTH_MM / 2)
            self.cog = (x, y)


if __name__ == "__main__":
    b = BalanceBoard()
    b.open()
    try:
        while True:
            print(f"\r{b.total:6.1f} kg  CoG x={b.cog[0]:6.1f} y={b.cog[1]:6.1f}  "
                  f"TR={b.kg[0]:5.1f} BR={b.kg[1]:5.1f} TL={b.kg[2]:5.1f} BL={b.kg[3]:5.1f}", end="")
            time.sleep(0.1)
    except KeyboardInterrupt:
        b.close()
