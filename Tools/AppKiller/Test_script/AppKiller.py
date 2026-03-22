#"C:\Program Files\DekTec\StreamXpress\StreamXpress64.exe"
import ctypes
import time
import argparse
import os

# --- Get idle time ---
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def get_idle_duration():
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint),
                    ("dwTime", ctypes.c_uint)]

    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = ctypes.sizeof(LASTINPUTINFO)

    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))

    tick_64 = ctypes.windll.kernel32.GetTickCount64()

    # Convert to 32-bit (match dwTime)
    tick_32 = tick_64 & 0xFFFFFFFF
    last_input = lastInputInfo.dwTime

    # Handle wraparound
    if tick_32 < last_input:
        idle_ms = (tick_32 + (1 << 32)) - last_input
    else:
        idle_ms = tick_32 - last_input

    return idle_ms / 1000.0

# --- Kill process ---
def kill_process(process_name):
    print(f"[INFO] Killing {process_name}")
    os.system(f"taskkill /f /im {process_name}")


# --- Main ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=300,
                        help="Idle timeout in seconds")
    parser.add_argument("--process", type=str, required=True,
                        help="Process name (e.g., notepad.exe)")

    args = parser.parse_args()

    print(f"[START] Monitoring idle time. Timeout = {args.timeout}s")

    while True:
        idle_time = get_idle_duration()
        print(f"Idle: {int(idle_time)}s", end="\r")

        if idle_time > args.timeout:
            kill_process(args.process)
            break

        time.sleep(2)


if __name__ == "__main__":
    main()