import sys
import json
import math
import html
import sqlite3
import threading
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QRadialGradient
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


# ----------------------------------------------------------------------------
# Visual identity (UI only: nothing below touches monitoring or detection logic)
# ----------------------------------------------------------------------------
BG, SURFACE, SURFACE2 = "#0A101B", "#111A29", "#172336"
BORDER, TEXT, MUTED = "#223149", "#E4EAF3", "#8190A6"
ACCENT, GREEN, RED, AMBER, BLUE = "#2DD4BF", "#34D399", "#F87171", "#FBBF24", "#60A5FA"
LEVEL_COLOURS = {"HIGH": RED, "MEDIUM": AMBER, "LOW": BLUE}
EVENT_COLOURS = {"process": BLUE, "network": AMBER, "file": ACCENT}

STYLE = f"""
* {{ font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif; }}
QMainWindow, QWidget#root {{ background:{BG}; }}
QWidget {{ color:{TEXT}; background:transparent; }}
QDialog, QMessageBox {{ background:{SURFACE}; }}
QLabel#muted {{ color:{MUTED}; }}
QLabel#caption {{ color:{MUTED}; font-size:11px; font-weight:600; letter-spacing:1.5px; }}
QLabel#chip {{ color:{ACCENT}; background:rgba(45,212,191,0.10); border:1px solid rgba(45,212,191,0.35);
               border-radius:13px; padding:6px 14px; font-size:11px; font-weight:700; letter-spacing:1.2px; }}
QFrame#panel {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:14px; }}

QPushButton {{ background:{SURFACE2}; border:1px solid {BORDER}; border-radius:9px; padding:10px 20px;
               font-weight:600; letter-spacing:0.6px; }}
QPushButton:hover {{ background:#1E2D45; border-color:#31466A; }}
QPushButton:pressed {{ background:#142033; }}
QPushButton:disabled {{ color:#4A586D; background:#0E1623; border-color:#17233A; }}
QPushButton#start {{ background:{ACCENT}; color:#04201C; border:1px solid {ACCENT}; }}
QPushButton#start:hover {{ background:#5BE3D2; }}
QPushButton#start:disabled {{ background:#0E1623; color:#4A586D; border-color:#17233A; }}
QPushButton#stop {{ background:rgba(248,113,113,0.10); color:{RED}; border:1px solid rgba(248,113,113,0.45); }}
QPushButton#stop:hover {{ background:rgba(248,113,113,0.20); }}
QPushButton#stop:disabled {{ background:#0E1623; color:#4A586D; border-color:#17233A; }}
QPushButton#run {{ background:rgba(45,212,191,0.12); color:{ACCENT}; border:1px solid rgba(45,212,191,0.40); padding:8px 22px; }}
QPushButton#run:hover {{ background:rgba(45,212,191,0.22); }}

QLineEdit {{ background:#070C14; color:#BFF3EA; border:1px solid {BORDER}; border-radius:9px; padding:9px 12px;
             font-family:"Cascadia Mono","Consolas",monospace; selection-background-color:{ACCENT}; selection-color:#04201C; }}
QLineEdit:focus {{ border:1px solid {ACCENT}; }}
QTextEdit {{ background:#070C14; border:1px solid {BORDER}; border-radius:9px; padding:8px 10px;
             font-family:"Cascadia Mono","Consolas",monospace; }}

QTabWidget::pane {{ border:none; border-top:1px solid {BORDER}; }}
QTabBar::tab {{ color:{MUTED}; padding:11px 20px; margin-right:6px; font-weight:600; border-bottom:2px solid transparent; }}
QTabBar::tab:hover {{ color:{TEXT}; }}
QTabBar::tab:selected {{ color:{ACCENT}; border-bottom:2px solid {ACCENT}; }}

QTableWidget {{ background:{SURFACE}; alternate-background-color:#0F1826; border:1px solid {BORDER};
                border-radius:12px; gridline-color:transparent; outline:0; selection-background-color:rgba(45,212,191,0.14);
                selection-color:{TEXT}; }}
QTableWidget::item {{ padding:4px 10px; border:none; }}
QHeaderView::section {{ background:{BG}; color:{MUTED}; padding:9px 10px; border:none; border-bottom:1px solid {BORDER};
                        font-size:11px; font-weight:700; letter-spacing:1.2px; }}
QScrollBar:vertical {{ background:transparent; width:10px; margin:2px; }}
QScrollBar::handle:vertical {{ background:#2A3B58; border-radius:4px; min-height:30px; }}
QScrollBar::handle:vertical:hover {{ background:#3A5078; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height:0; width:0; }}
QScrollBar:horizontal {{ height:0; }}
QMessageBox QPushButton {{ min-width:80px; }}
"""


class LogoMark(QWidget):
    """Cell-with-nucleus mark: the immune-system idea in one glyph."""

    def __init__(self, size=48):
        super().__init__()
        self.setFixedSize(size, size)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self.width()
        c = QPointF(s / 2, s / 2)
        r = s / 2 - 3
        p.setBrush(QBrush(QColor(45, 212, 191, 28)))
        p.setPen(QPen(QColor(ACCENT), 2.2))
        p.drawEllipse(c, r, r)
        p.setPen(QPen(QColor(45, 212, 191, 90), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(c, r * 0.62, r * 0.62)
        g = QRadialGradient(c.x() - 3, c.y() - 3, s / 3)
        g.setColorAt(0, QColor("#8AF5E6"))
        g.setColorAt(1, QColor("#0F9C8C"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(c, s * 0.15, s * 0.15)
        p.setBrush(QColor(ACCENT))
        for a in (25, 145, 265):
            p.drawEllipse(QPointF(c.x() + r * math.cos(math.radians(a)), c.y() + r * math.sin(math.radians(a))), 2.8, 2.8)


class StatusPill(QWidget):
    """RUNNING / STOPPED indicator with a soft pulse while monitoring is active."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(138, 38)
        self.running = False
        self.phase = 0.0
        self.pulse = QTimer(self)
        self.pulse.timeout.connect(self._tick)

    def setRunning(self, running):
        if running == self.running:
            return
        self.running = running
        if running:
            self.pulse.start(40)
        else:
            self.pulse.stop()
            self.phase = 0.0
        self.update()

    def _tick(self):
        self.phase = (self.phase + 0.04) % 1.0
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor(GREEN if self.running else RED)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        bg = QColor(col)
        bg.setAlpha(26)
        edge = QColor(col)
        edge.setAlpha(110)
        p.setPen(QPen(edge, 1))
        p.setBrush(bg)
        p.drawRoundedRect(rect, 19, 19)
        cx, cy = 21, self.height() / 2
        if self.running:
            halo = QColor(col)
            halo.setAlpha(int(110 * (1 - self.phase)))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(halo)
            rr = 5 + 8 * self.phase
            p.drawEllipse(QPointF(cx, cy), rr, rr)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(col)
        p.drawEllipse(QPointF(cx, cy), 5, 5)
        f = QFont("Segoe UI", 9, QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.4)
        p.setFont(f)
        p.setPen(col)
        p.drawText(QRectF(36, 0, self.width() - 40, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   "RUNNING" if self.running else "STOPPED")


class MetricCard(QFrame):
    """Headline number with an accent edge; exposes setText like a QLabel."""

    def __init__(self, caption, initial, sub, accent=ACCENT):
        super().__init__()
        self.setObjectName("metricCard")
        self.accent = QColor(accent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 18, 16)
        lay.setSpacing(2)
        cap = QLabel(caption)
        cap.setObjectName("caption")
        self.value = QLabel(initial)
        self.value.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.sub = QLabel(sub)
        self.sub.setObjectName("muted")
        self.sub.setStyleSheet("font-size:12px;")
        lay.addWidget(cap)
        lay.addWidget(self.value)
        lay.addWidget(self.sub)
        self.setTone(accent)

    def setText(self, text):
        self.value.setText(text)

    def setTone(self, colour):
        self.accent = QColor(colour)
        self.value.setStyleSheet(f"color:{colour};")
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        p.setPen(QPen(QColor(BORDER), 1))
        p.setBrush(QColor(SURFACE))
        p.drawRoundedRect(rect, 14, 14)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.accent)
        p.drawRoundedRect(QRectF(0, 18, 4, self.height() - 36), 2, 2)
        super().paintEvent(_)


class DataTable(QTableWidget):
    """Table that explains itself when empty."""

    def __init__(self, columns, placeholder):
        super().__init__(0, len(columns))
        self.placeholder = placeholder

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.rowCount() == 0:
            p = QPainter(self.viewport())
            p.setPen(QColor(MUTED))
            p.setFont(QFont("Segoe UI", 11))
            p.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self.placeholder)


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
        self.resize(1120, 780)
        self.setMinimumSize(880, 640)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet(STYLE)
        root = QWidget()
        root.setObjectName("root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(16)

        # --- header -------------------------------------------------------
        header = QHBoxLayout()
        header.setSpacing(14)
        header.addWidget(LogoMark(48))
        brand = QVBoxLayout()
        brand.setSpacing(0)
        title = QLabel("ADIS")
        tf = QFont("Segoe UI", 24, QFont.Weight.Bold)
        tf.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        title.setFont(tf)
        subtitle = QLabel("AUTONOMOUS DIGITAL IMMUNE SYSTEM")
        subtitle.setObjectName("caption")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header.addLayout(brand)
        header.addStretch()
        self.status = StatusPill()
        header.addWidget(self.status)
        layout.addLayout(header)

        # --- metrics ------------------------------------------------------
        grid = QGridLayout()
        grid.setSpacing(14)
        self.metrics = {}
        for i, (key, caption, initial, sub, accent) in enumerate([
            ("runtime", "MONITOR STATUS", "STOPPED", "Sensors and collector", RED),
            ("events", "EVENTS STORED", "—", "Rows in the events table", ACCENT),
            ("assessments", "ASSESSMENTS", "—", "Risk evaluations saved", BLUE),
            ("alerts", "NON-NORMAL RISKS", "—", "Level above NORMAL", GREEN),
        ]):
            card = MetricCard(caption, initial, sub, accent)
            self.metrics[key] = card
            grid.addWidget(card, 0, i)
            grid.setColumnStretch(i, 1)
        layout.addLayout(grid)

        # --- controls -----------------------------------------------------
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.start_btn = QPushButton("▶  START ADIS")
        self.start_btn.setObjectName("start")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_runtime)
        self.stop_btn = QPushButton("■  STOP ADIS")
        self.stop_btn.setObjectName("stop")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.stop_runtime)
        self.stop_btn.setEnabled(False)
        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.stop_btn)
        buttons.addStretch()
        safe = QLabel("RESPONSE MODE: DRY RUN" if DRY_RUN else "REAL CONTAINMENT DISABLED")
        safe.setObjectName("chip")
        buttons.addWidget(safe)
        layout.addLayout(buttons)

        # --- tables -------------------------------------------------------
        self.tabs = QTabWidget()
        self.events_table = self.make_table(["Time (UTC)", "Event", "PID", "Process"], "No events recorded yet. Press START ADIS.", 3)
        self.alerts_table = self.make_table(["Time (UTC)", "Level", "Score", "PID", "Process", "Reasons"], "No elevated risk assessments. All clear.", 5)
        self.tabs.addTab(self.alerts_table, "Risk assessments")
        self.tabs.addTab(self.events_table, "Recent events")
        layout.addWidget(self.tabs, 1)

        # --- terminal -----------------------------------------------------
        terminal = QFrame()
        terminal.setObjectName("panel")
        term_layout = QVBoxLayout(terminal)
        term_layout.setContentsMargins(18, 14, 18, 16)
        term_layout.setSpacing(10)
        term_head = QHBoxLayout()
        term_title = QLabel("ADIS COMMAND TERMINAL")
        term_title.setObjectName("caption")
        term_title.setStyleSheet(f"color:{ACCENT};")
        term_head.addWidget(term_title)
        term_head.addStretch()
        hint = QLabel("help · status · events · alerts · start · stop · clear")
        hint.setObjectName("muted")
        hint.setStyleSheet("font-size:12px;")
        term_head.addWidget(hint)
        term_layout.addLayout(term_head)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 10))
        self.console.setMaximumHeight(140)
        term_layout.addWidget(self.console)
        row = QHBoxLayout()
        row.setSpacing(10)
        prompt = QLabel("adis›")
        prompt.setStyleSheet(f'color:{ACCENT};font-family:"Cascadia Mono","Consolas",monospace;font-weight:700;')
        row.addWidget(prompt)
        self.command = QLineEdit()
        self.command.setPlaceholderText("Type a command and press Enter")
        self.command.returnPressed.connect(self.run_command)
        row.addWidget(self.command, 1)
        run = QPushButton("RUN")
        run.setObjectName("run")
        run.setCursor(Qt.CursorShape.PointingHandCursor)
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

    def make_table(self, headers, placeholder="", stretch_col=None):
        table = DataTable(headers, placeholder)
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(36)
        head = table.horizontalHeader()
        head.setHighlightSections(False)
        head.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for c in range(len(headers)):
            head.setSectionResizeMode(
                c, QHeaderView.ResizeMode.Stretch if c == stretch_col else QHeaderView.ResizeMode.ResizeToContents
            )
        return table

    def say(self, message):
        text = html.escape(str(message))
        colour = "#BFF3EA"
        if str(message).startswith("adis>"):
            colour = ACCENT
        elif str(message).startswith(("START ERROR", "STOP WARNING", "Unknown command", "Usage")):
            colour = RED
        elif str(message).startswith(("ADIS started", "ADIS stopped")):
            colour = GREEN
        self.console.append(
            f'<span style="color:{MUTED}">[{datetime.now():%H:%M:%S}]</span> <span style="color:{colour}">{text}</span>'
        )

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
        running = self.runtime.running
        self.metrics["runtime"].setText("RUNNING" if running else "STOPPED")
        self.metrics["runtime"].setTone(GREEN if running else RED)
        self.metrics["events"].setText(f"{event_count:,}")
        self.metrics["assessments"].setText(f"{assessment_count:,}")
        self.metrics["alerts"].setText(f"{alert_count:,}")
        self.metrics["alerts"].setTone(AMBER if alert_count else GREEN)
        self.status.setRunning(running)
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.fill(self.events_table, events, False)
        self.fill(self.alerts_table, alerts, True)

    def fill(self, table, rows, is_alert):
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
                item = QTableWidgetItem("—" if value is None else str(value))
                if c == 0:
                    item.setForeground(QBrush(QColor(MUTED)))
                if is_alert and c in (1, 2):
                    colour = LEVEL_COLOURS.get(str(values[1]).upper())
                    if colour:
                        item.setForeground(QBrush(QColor(colour)))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                if not is_alert and c == 1:
                    for key, colour in EVENT_COLOURS.items():
                        if key in str(value).lower():
                            item.setForeground(QBrush(QColor(colour)))
                            break
                table.setItem(r, c, item)
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