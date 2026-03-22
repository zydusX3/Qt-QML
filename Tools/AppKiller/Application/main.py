import sys
import threading
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QVBoxLayout, QLabel, QComboBox,
    QCheckBox, QTimeEdit, QFrame
)
from PySide6.QtCore import Qt, QTime

from worker import monitor
from utils import (
    is_process_running,
    load_history,
    save_history
)

DEFAULT_PROCESS = "StreamXpress64.exe"


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RF Safety Controller v4.2")

        self.layout = QVBoxLayout()

        # -------- INPUT SECTION --------
        self.layout.addWidget(QLabel("Process Name (comma separated)"))

        self.process_input = QComboBox()
        self.process_input.setEditable(True)

        history = load_history()
        self.process_input.addItems(history)

        if not history:
            self.process_input.setEditText(DEFAULT_PROCESS)

        self.layout.addWidget(self.process_input)

        # --- Mode ---
        self.layout.addWidget(QLabel("Mode"))
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Idle", "Duration", "Fixed Time"])
        self.layout.addWidget(self.mode_selector)

        # --- Time Input ---
        self.time_label = QLabel("Idle Timeout (HH:MM:SS)")
        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat("HH:mm:ss")
        self.time_input.setTime(QTime(4, 0, 0))

        self.layout.addWidget(self.time_label)
        self.layout.addWidget(self.time_input)

        # --- Shutdown option ---
        self.shutdown_checkbox = QCheckBox("Shutdown PC after closing app")
        self.layout.addWidget(self.shutdown_checkbox)

        # -------- SEPARATOR --------
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(line)

        # -------- STATUS --------
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.timer_label)

        # -------- BUTTONS --------
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.reset_btn = QPushButton("Reset Timer")

        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.stop_btn)
        self.layout.addWidget(self.reset_btn)

        self.setLayout(self.layout)

        # --- Control ---
        self.control = {"stop": False, "reset": False, "shutdown": False}

        # --- Connections ---
        self.start_btn.clicked.connect(self.start_monitor)
        self.stop_btn.clicked.connect(self.stop_monitor)
        self.reset_btn.clicked.connect(self.reset_timer)
        self.mode_selector.currentTextChanged.connect(self.update_ui)

        self.update_ui()

    # -------- UI STATE --------
    def set_inputs_enabled(self, enabled):
        self.process_input.setEnabled(enabled)
        self.mode_selector.setEnabled(enabled)
        self.time_input.setEnabled(enabled)
        self.shutdown_checkbox.setEnabled(enabled)

    def update_ui(self):
        mode = self.mode_selector.currentText()

        self.reset_btn.setVisible(mode == "Duration")

        if mode == "Fixed Time":
            self.time_label.setText("Fixed Time (HH:MM)")
            self.time_input.setDisplayFormat("HH:mm")
        else:
            self.time_input.setDisplayFormat("HH:mm:ss")

            if mode == "Duration":
                self.time_label.setText("Duration (HH:MM:SS)")
            else:
                self.time_label.setText("Idle Timeout (HH:MM:SS)")

    # -------- HELPERS --------
    def get_duration_seconds(self):
        t = self.time_input.time()
        return t.hour() * 3600 + t.minute() * 60 + t.second()

    def get_target_time(self):
        selected = self.time_input.time()
        now = datetime.now()

        target = now.replace(
            hour=selected.hour(),
            minute=selected.minute(),
            second=0,
            microsecond=0
        )

        if target < now:
            target += timedelta(days=1)

        return target

    def format_time(self, seconds):
        seconds = max(0, int(seconds))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02}:{m:02}:{s:02}"

    def parse_processes(self):
        text = self.process_input.currentText()
        return [p.strip() for p in text.split(",") if p.strip()]

    # -------- TIMER UPDATE --------
    def update_timer(self, value):
        mode = self.mode_selector.currentText()

        if mode == "Fixed Time":
            remaining = value
        else:
            remaining = self.get_duration_seconds() - int(value)

        self.timer_label.setText(self.format_time(remaining))

    # -------- START --------
    def start_monitor(self):
        process_text = self.process_input.currentText()
        process_list = self.parse_processes()

        # --- Save history ---
        save_history(process_text)

        # --- Validate processes ---
        valid = []
        invalid = []

        for p in process_list:
            if is_process_running(p):
                valid.append(p)
            else:
                invalid.append(p)

        if invalid:
            print(f"[WARN] Not running: {invalid}")

        if not valid:
            print("[ERROR] No valid processes found")
            return

        mode = self.mode_selector.currentText().lower()

        self.control["stop"] = False
        self.control["reset"] = False
        self.control["shutdown"] = self.shutdown_checkbox.isChecked()

        timeout = None
        target_time = None

        if mode == "fixed time":
            mode = "fixed"
            target_time = self.get_target_time()
            timeout = 1
        else:
            timeout = self.get_duration_seconds()

        self.set_inputs_enabled(False)

        threading.Thread(
            target=monitor,
            args=(valid, timeout, mode, target_time,
                  self.update_timer, self.control),
            daemon=True
        ).start()

    # -------- STOP --------
    def stop_monitor(self):
        self.control["stop"] = True
        self.set_inputs_enabled(True)
        self.timer_label.setText("Stopped")

    # -------- RESET --------
    def reset_timer(self):
        self.control["reset"] = True


# --- Run ---
app = QApplication(sys.argv)
window = App()
window.show()
sys.exit(app.exec())