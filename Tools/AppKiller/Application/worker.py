from PySide6.QtCore import QThread, Signal
import time
from datetime import datetime
from utils import get_idle_duration, kill_process, shutdown_pc


class MonitorWorker(QThread):
    update_signal = Signal(float)
    finished_signal = Signal()

    def __init__(self, process_list, timeout, mode,
                 target_time=None, control=None):
        super().__init__()

        self.process_list = process_list
        self.timeout = timeout
        self.mode = mode
        self.target_time = target_time
        self.control = control or {}

    def run(self):
        print(f"[START] Mode={self.mode}, processes={self.process_list}")

        start_time = time.time()

        while True:
            if self.control.get("stop"):
                print("[STOP] Monitoring stopped")
                break

            # --- Reset ---
            if self.mode == "duration" and self.control.get("reset"):
                start_time = time.time()
                self.control["reset"] = False

            # --- Mode logic ---
            if self.mode == "idle":
                elapsed = get_idle_duration()

            elif self.mode == "duration":
                elapsed = time.time() - start_time

            elif self.mode == "fixed":
                now = datetime.now()
                remaining = (self.target_time - now).total_seconds()

                self.update_signal.emit(remaining)

                if remaining <= 0:
                    print("[TRIGGER] Fixed time reached")

                    for p in self.process_list:
                        kill_process(p)

                    if self.control.get("shutdown"):
                        shutdown_pc()

                    break

                time.sleep(1)
                continue

            else:
                elapsed = 0

            # --- Update UI safely ---
            self.update_signal.emit(elapsed)

            # --- Trigger ---
            if elapsed > self.timeout:
                print("[TRIGGER] Condition met")

                for p in self.process_list:
                    kill_process(p)

                if self.control.get("shutdown"):
                    shutdown_pc()

                break

            time.sleep(1)

        self.finished_signal.emit()