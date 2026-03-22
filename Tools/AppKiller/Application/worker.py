import time
from datetime import datetime
from utils import get_idle_duration, kill_process, shutdown_pc


def monitor(process_list, timeout, mode,
            target_time=None,
            callback=None,
            control=None):

    print(f"[START] Mode={mode}, processes={process_list}")

    start_time = time.time()

    while True:
        if control and control.get("stop"):
            print("[STOP] Monitoring stopped")
            break

        if mode == "duration" and control and control.get("reset"):
            start_time = time.time()
            control["reset"] = False

        if mode == "idle":
            elapsed = get_idle_duration()

        elif mode == "duration":
            elapsed = time.time() - start_time

        elif mode == "fixed":
            now = datetime.now()
            remaining = (target_time - now).total_seconds()

            if callback:
                callback(remaining)

            if remaining <= 0:
                print("\n[TRIGGER] Fixed time reached")

                for p in process_list:
                    kill_process(p)

                if control and control.get("shutdown"):
                    shutdown_pc()
                break

            time.sleep(1)
            continue

        else:
            elapsed = 0

        if callback:
            callback(elapsed)

        if elapsed > timeout:
            print("\n[TRIGGER] Condition met")

            for p in process_list:
                kill_process(p)

            if control and control.get("shutdown"):
                shutdown_pc()
            break

        time.sleep(1)