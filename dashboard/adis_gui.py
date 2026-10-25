import sys
import sqlite3
import threading
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
    QTextEdit, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QMessageBox
)
from config import DATABASE_PATH, FILE_MONITOR_ENABLED, PROCESS_MONITOR_INTERVAL, NETWORK_MONITOR_INTERVAL, DRY_RUN
from engine.collector import EventCollector
from engine.event_bus import EventBus
from engine.pipeline import DetectionPipeline
from sensors.file_sensor import FileSensor
from sensors.network_sensor import NetworkSensor
from sensors.process_sensor import ProcessSensor


class Runtime:
    def __init__(self):
        self.running = False
        self.threads = []
        self.collector = self.process_sensor = self.network_sensor = self.file_sensor = None

    def start(self):
        if self.running:
            return "ADIS is already running."
        bus = EventBus()
        pipeline = DetectionPipeline()
        self.collector = EventCollector(bus, pipeline)
        self.process_sensor = ProcessSensor(bus.publish, PROCESS_MONITOR_INTERVAL)
        self.network_sensor = NetworkSensor(bus.publish, NETWORK_MONITOR_INTERVAL)
        self.file_sensor = None
        if FILE_MONITOR_ENABLED:
            self.file_sensor = FileSensor(ROOT / "data" / "watch", bus.publish)
        self.threads = [
            threading.Thread(target=self.collector.run, name="collector", daemon=True),
            threading.Thread(target=self.process_sensor.run, name="process-sensor", daemon=True),
            threading.Thread(target=self.network_sensor.run, name="network-sensor", daemon=True),
        ]
        try:
            for thread in self.threads:
                thread.start()
            if self.file_sensor:
                self.file_sensor.start()
            self.running = True
            return "ADIS started. Monitoring processes, files and network connections."
        except Exception:
            self.stop()
            raise

    def stop(self):
        if not any((self.running, self.collector, self.process_sensor, self.network_sensor, self.file_sensor)):
            return "ADIS is already stopped."
        if self.process_sensor:
            self.process_sensor.stop()
        if self.network_sensor:
            self.network_sensor.stop()
        if self.file_sensor:
            try:
                self.file_sensor.stop()
            except Exception:
                pass
        for t in self.threads:
            if t.name in ("process-sensor", "network-sensor"):
                t.join(timeout=max(PROCESS_MONITOR_INTERVAL, NETWORK_MONITOR_INTERVAL) + 4)
        if self.collector:
            self.collector.running = False
        for t in self.threads:
            if t.name == "collector":
                t.join(timeout=4)
        if self.collector:
            try:
                self.collector.database.close()
            except Exception:
                pass
        self.running = False
        self.collector = self.process_sensor = self.network_sensor = self.file_sensor = None
        self.threads = []
        return "ADIS stopped. Background monitoring is off."


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.runtime = Runtime()
        self.setWindowTitle("ADIS | Autonomous Digital Immune System")
        self.resize(1080, 740)
        self.setMinimumSize(850, 600)
        self.setStyleSheet("""
            QMainWindow,QWidget{background:#101820;color:#e7edf2}
            QFrame#card{background:#192630;border:1px solid #2c3c48;border-radius:10px}
            QLabel#muted{color:#9aabb8}
            QLabel#metric{font-size:22px;font-weight:700}
            QPushButton{background:#263744;border:1px solid #3a4c58;border-radius:7px;padding:10px 15px;font-weight:600}
            QPushButton:hover{background:#334956}
            QPushButton#start{background:#16835f;border-color:#23a77c}
            QPushButton#stop{background:#6d3038;border-color:#8f424b}
            QLineEdit,QTextEdit{background:#080e13;color:#b8f5d9;border:1px solid #344550;border-radius:6px;padding:8px}
            QTabWidget::pane{border:1px solid #2c3c48}
            QTabBar::tab{background:#192630;padding:9px 16px}
            QTabBar::tab:selected{background:#263944;color:#75e4b6}
            QTableWidget{background:#111a21;alternate-background-color:#17232c;gridline-color:#2b3b46}
            QHeaderView::section{background:#22323d;padding:7px;border:none}
        """)
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        brand = QVBoxLayout()
        title = QLabel("ADIS")
        title.setFont(QFont("Segoe UI", 23, QFont.Weight.Bold))
        subtitle = QLabel("AUTONOMOUS DIGITAL IMMUNE SYSTEM")
        subtitle.setObjectName("muted")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header.addLayout(brand)
        header.addStretch()
        self.status = QLabel("● STOPPED")
        self.status.setStyleSheet("color:#ff9b9b;font-weight:700;padding:9px;background:#2b2025;border-radius:7px")
        header.addWidget(self.status)
        layout.addLayout(header)

        grid = QGridLayout()
        self.metrics = {}
        for i, (key, caption, initial) in enumerate([
            ("runtime", "MONITOR STATUS", "STOPPED"),
            ("events", "EVENTS STORED", "—"),
            ("assessments", "ASSESSMENTS", "—"),
            ("alerts", "NON-NORMAL RISKS", "—"),
        ]):
            card = QFrame()
            card.setObjectName("card")
            box = QVBoxLayout(card)
            label = QLabel(caption)
            label.setObjectName("muted")
            value = QLabel(initial)
            value.setObjectName("metric")
            self.metrics[key] = value
            box.addWidget(label)
            box.addWidget(value)
            grid.addWidget(card, 0, i)
        layout.addLayout(grid)

        buttons = QHBoxLayout()
        self.start_btn = QPushButton("▶  START ADIS")
        self.start_btn.setObjectName("start")
        self.start_btn.clicked.connect(self.start_runtime)
        self.stop_btn = QPushButton("■  STOP ADIS")
        self.stop_btn.setObjectName("stop")
        self.stop_btn.clicked.connect(self.stop_runtime)
        self.stop_btn.setEnabled(False)
        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addStretch()
        safe = QLabel("RESPONSE MODE: DRY RUN" if DRY_RUN else "REAL CONTAINMENT DISABLED")
        safe.setStyleSheet("color:#75e4b6;font-weight:700")
        buttons.addWidget(safe)
        layout.addLayout(buttons)

        self.tabs = QTabWidget()
        self.events_table = self.make_table(["Time (UTC)", "Event", "PID", "Process"])
        self.alerts_table = self.make_table(["Time (UTC)", "Level", "Score", "PID", "Process", "Reasons"])
        self.tabs.addTab(self.alerts_table, "Risk assessments")
        self.tabs.addTab(self.events_table, "Recent events")
        layout.addWidget(self.tabs, 1)

        terminal = QFrame()
        terminal.setObjectName("card")
        term_layout = QVBoxLayout(terminal)
        term_head = QHBoxLayout()
        term_title = QLabel("ADIS COMMAND TERMINAL")
        term_title.setStyleSheet("color:#75e4b6;font-weight:700")
        term_head.addWidget(term_title)
        term_head.addStretch()
        hint = QLabel("help · status · events · alerts · start · stop · clear")
        hint.setObjectName("muted")
        term_head.addWidget(hint)
        term_layout.addLayout(term_head)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 10))
        self.console.setMaximumHeight(140)
        term_layout.addWidget(self.console)
        row = QHBoxLayout()
        row.addWidget(QLabel("adis>"))
        self.command = QLineEdit()
        self.command.setPlaceholderText("Type a command and press Enter")
        self.command.returnPressed.connect(self.run_command)
        row.addWidget(self.command, 1)
        run = QPushButton("RUN")
        run.clicked.connect(self.run_command)
        row.addWidget(run)
        term_layout.addLayout(row)
        layout.addWidget(terminal)
        self.setCentralWidget(root)

        self.say("ADIS desktop ready. Press START ADIS to begin background monitoring.")
        self.say("Commands: help, status, events [count], alerts [count], start, stop, clear.")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1500)
        self.refresh()

    def make_table(self, headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

    def say(self, message):
        self.console.append(f"[{datetime.now():%H:%M:%S}] {message}")

    def start_runtime(self):
        try:
            self.say(self.runtime.start())
        except Exception as exc:
            self.say(f"START ERROR: {exc}")
            QMessageBox.critical(self, "ADIS startup failed", str(exc))
        self.refresh()

    def stop_runtime(self):
        try:
            self.say(self.runtime.stop())
        except Exception as exc:
            self.say(f"STOP WARNING: {exc}")
        self.refresh()

    def db_data(self):
        path = Path(DATABASE_PATH)
        if not path.exists():
            return 0, 0, 0, [], []
        db = None
        try:
            db = sqlite3.connect(str(path), timeout=2)
            counts = (
                db.execute("SELECT COUNT(*) FROM events").fetchone()[0],
                db.execute("SELECT COUNT(*) FROM assessments").fetchone()[0],
                db.execute("SELECT COUNT(*) FROM assessments WHERE level != 'NORMAL'").fetchone()[0],
            )
            events = db.execute(
                "SELECT timestamp,event_type,pid,process_name FROM events ORDER BY id DESC LIMIT 50"
            ).fetchall()
            alerts = db.execute(
                "SELECT timestamp,level,score,pid,process_name,reasons FROM assessments WHERE level != 'NORMAL' ORDER BY id DESC LIMIT 50"
            ).fetchall()
            return *counts, events, alerts
        except sqlite3.Error as exc:
            return 0, 0, 0, [], []
        finally:
            if db:
                db.close()

    def refresh(self):
        event_count, assessment_count, alert_count, events, alerts = self.db_data()
        self.metrics["runtime"].setText("RUNNING" if self.runtime.running else "STOPPED")
        self.metrics["events"].setText(f"{event_count:,}")
        self.metrics["assessments"].setText(f"{assessment_count:,}")
        self.metrics["alerts"].setText(f"{alert_count:,}")
        self.status.setText("● RUNNING" if self.runtime.running else "● STOPPED")
        self.status.setStyleSheet(
            "color:#75e4b6;font-weight:700;padding:9px;background:#193b32;border-radius:7px"
            if self.runtime.running else
            "color:#ff9b9b;font-weight:700;padding:9px;background:#2b2025;border-radius:7px"
        )
        self.start_btn.setEnabled(not self.runtime.running)
        self.stop_btn.setEnabled(self.runtime.running)
        self.fill(self.events_table, events, False)
        self.fill(self.alerts_table, alerts, True)

    def fill(self, table, rows, is_alert):
        import json
        table.setUpdatesEnabled(False)
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            values = list(row)
            if is_alert and values[5]:
                try:
                    values[5] = "; ".join(json.loads(values[5]))
                except Exception:
                    pass
            for c, value in enumerate(values):
                if c == 0 and value:
                    value = str(value).replace("T", " ")[:19]
                table.setItem(r, c, QTableWidgetItem("—" if value is None else str(value)))
        table.setUpdatesEnabled(True)

    def run_command(self):
        raw = self.command.text().strip()
        self.command.clear()
        if not raw:
            return
        self.say(f"adis> {raw}")
        args = raw.lower().split()
        cmd = args[0]
        if cmd in ("help", "?"):
            self.say("Commands: help, status, events [1-50], alerts [1-50], start, stop, clear.")
        elif cmd == "status":
            e, a, al, _, _ = self.db_data()
            self.say(f"Monitor={'RUNNING' if self.runtime.running else 'STOPPED'} | events={e} | assessments={a} | non-normal={al} | dry_run={DRY_RUN}")
            self.say("The 18-feature supervised model is trained but not connected to the live pipeline.")
        elif cmd == "start":
            self.start_runtime()
        elif cmd == "stop":
            self.stop_runtime()
        elif cmd == "clear":
            self.console.clear()
        elif cmd in ("events", "alerts"):
            e, a, al, events, alerts = self.db_data()
            try:
                limit = max(1, min(50, int(args[1]))) if len(args) > 1 else 10
            except ValueError:
                self.say("Usage: events [1-50] or alerts [1-50]")
                return
            rows = events if cmd == "events" else alerts
            self.say(f"Showing {min(limit, len(rows))} recent {cmd}; database total={e if cmd == 'events' else al}.")
            for row in rows[:limit]:
                if cmd == "events":
                    self.say(f"{str(row[0])[:19]} | {row[1]} | PID={row[2]} | {row[3] or 'unknown'}")
                else:
                    self.say(f"{str(row[0])[:19]} | {row[1]} score={row[2]} | PID={row[3]} | {row[4] or 'unknown'}")
            self.tabs.setCurrentWidget(self.events_table if cmd == "events" else self.alerts_table)
        else:
            self.say(f"Unknown command '{cmd}'. Type help.")

    def closeEvent(self, event):
        if self.runtime.running:
            choice = QMessageBox.question(
                self, "Stop ADIS?", "Stop background monitoring and close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if choice != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.stop_runtime()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ADIS")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
