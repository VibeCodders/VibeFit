"""Accoppia la Wii Balance Board a Windows (PIN binario = indirizzo BT del PC).

Uso: tieni premuto il tasto rosso SYNC (vano batterie) e lancia lo script.
Mantieni SYNC premuto finche' lo script non ha finito.
"""
import ctypes
from ctypes import wintypes

bt = ctypes.WinDLL("bthprops.cpl")

BOARD_NAMES = ("RVL-WBC-01",)
HID_SERVICE = (0x00001124, 0x0000, 0x1000, (0x80, 0x00, 0x00, 0x80, 0x5F, 0x9B, 0x34, 0xFB))


class GUID(ctypes.Structure):
    _fields_ = [("D1", wintypes.DWORD), ("D2", wintypes.WORD), ("D3", wintypes.WORD), ("D4", ctypes.c_ubyte * 8)]


class SYSTEMTIME(ctypes.Structure):
    _fields_ = [(n, wintypes.WORD) for n in
                ("y", "mo", "dow", "d", "h", "mi", "s", "ms")]


class FindRadioParams(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD)]


class RadioInfo(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("address", ctypes.c_ulonglong),
                ("szName", ctypes.c_wchar * 248), ("ulClassofDevice", wintypes.ULONG),
                ("lmpSubversion", wintypes.USHORT), ("manufacturer", wintypes.USHORT)]


class SearchParams(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("fReturnAuthenticated", wintypes.BOOL),
                ("fReturnRemembered", wintypes.BOOL), ("fReturnUnknown", wintypes.BOOL),
                ("fReturnConnected", wintypes.BOOL), ("fIssueInquiry", wintypes.BOOL),
                ("cTimeoutMultiplier", ctypes.c_ubyte), ("hRadio", wintypes.HANDLE)]


class DeviceInfo(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("Address", ctypes.c_ulonglong),
                ("ulClassofDevice", wintypes.ULONG), ("fConnected", wintypes.BOOL),
                ("fRemembered", wintypes.BOOL), ("fAuthenticated", wintypes.BOOL),
                ("lastSeen", SYSTEMTIME), ("lastUsed", SYSTEMTIME),
                ("szName", ctypes.c_wchar * 248)]


def fmt(addr):
    return ":".join(f"{b:02X}" for b in addr.to_bytes(6, "big"))


def find_radio():
    params = FindRadioParams(ctypes.sizeof(FindRadioParams))
    h = wintypes.HANDLE()
    bt.BluetoothFindFirstRadio.restype = wintypes.HANDLE
    find = bt.BluetoothFindFirstRadio(ctypes.byref(params), ctypes.byref(h))
    if not find:
        raise SystemExit("Nessun adattatore Bluetooth trovato.")
    bt.BluetoothFindRadioClose(find)
    info = RadioInfo(ctypes.sizeof(RadioInfo))
    bt.BluetoothGetRadioInfo(h, ctypes.byref(info))
    return h, info


def scan(radio):
    sp = SearchParams(ctypes.sizeof(SearchParams), True, True, True, True, True, 8, radio)
    di = DeviceInfo(dwSize=ctypes.sizeof(DeviceInfo))
    bt.BluetoothFindFirstDevice.restype = wintypes.HANDLE
    h = bt.BluetoothFindFirstDevice(ctypes.byref(sp), ctypes.byref(di))
    found = []
    if not h:
        return found
    while True:
        copy = DeviceInfo()
        ctypes.memmove(ctypes.byref(copy), ctypes.byref(di), ctypes.sizeof(DeviceInfo))
        found.append(copy)
        if not bt.BluetoothFindNextDevice(h, ctypes.byref(di)):
            break
    bt.BluetoothFindDeviceClose(h)
    return found


def main():
    radio, rinfo = find_radio()
    print(f"Adattatore: {rinfo.szName} ({fmt(rinfo.address)})")
    board = None
    for attempt in range(1, 6):
        print(f"Ricerca {attempt}/5 (tieni premuto SYNC)...")
        for d in scan(radio):
            print(f"  - {d.szName!r} {fmt(d.Address)}")
            if any(n in d.szName for n in BOARD_NAMES):
                board = d
        if board:
            break
    if not board:
        raise SystemExit("Balance Board non trovata. Rimuovi eventuali vecchi accoppiamenti e riprova.")

    print(f"Trovata: {board.szName} {fmt(board.Address)}")
    # Accoppiamento via SYNC: PIN = indirizzo del PC, 6 byte in ordine little-endian
    pin = (ctypes.c_ubyte * 6)(*rinfo.address.to_bytes(6, "little"))
    bt.BluetoothAuthenticateDevice.argtypes = [wintypes.HWND, wintypes.HANDLE,
                                               ctypes.POINTER(DeviceInfo), ctypes.c_void_p, wintypes.ULONG]
    res = bt.BluetoothAuthenticateDevice(None, radio, ctypes.byref(board), ctypes.byref(pin), 6)
    if res != 0:
        raise SystemExit(f"Accoppiamento fallito (codice {res}).")
    print("Accoppiata. Abilito il servizio HID...")
    guid = GUID(HID_SERVICE[0], HID_SERVICE[1], HID_SERVICE[2], (ctypes.c_ubyte * 8)(*HID_SERVICE[3]))
    res = bt.BluetoothSetServiceState(radio, ctypes.byref(board), ctypes.byref(guid), 1)
    print("Servizio HID abilitato." if res == 0 else f"SetServiceState codice {res} (puo' essere gia' attivo).")
    print("Fatto. Ora la board dovrebbe comparire come dispositivo HID.")


if __name__ == "__main__":
    main()
