import ctypes
import os
import subprocess
import json

HISTORY_FILE = "history.json"

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("dwTime", ctypes.c_uint)]


def get_idle_duration():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = ctypes.sizeof(LASTINPUTINFO)

    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))

    tick_64 = ctypes.windll.kernel32.GetTickCount64()
    tick_32 = tick_64 & 0xFFFFFFFF
    last_input = lastInputInfo.dwTime

    if tick_32 < last_input:
        idle_ms = (tick_32 + (1 << 32)) - last_input
    else:
        idle_ms = tick_32 - last_input

    return idle_ms / 1000.0


def kill_process(process_name):
    print(f"[INFO] Attempting graceful kill: {process_name}")
    os.system(f"taskkill /im {process_name}")

    print(f"[INFO] Force killing: {process_name}")
    os.system(f"taskkill /f /im {process_name}")

def is_process_running(process_name):
    try:
        output = subprocess.check_output(
            f'tasklist /FI "IMAGENAME eq {process_name}"',
            shell=True
        ).decode()
        return process_name.lower() in output.lower()
    except:
        return False

def shutdown_pc():
    print("[INFO] Shutting down system in 30 seconds...")
    os.system("shutdown /s /t 30")
    
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(process_str):
    history = load_history()

    if process_str in history:
        history.remove(process_str)

    history.insert(0, process_str)

    history = history[:5]  # keep last 5

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)