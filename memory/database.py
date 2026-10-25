import json
import sqlite3
from pathlib import Path

from config import DATABASE_PATH
from engine.events import SecurityEvent
from engine.risk import RiskAssessment


class SecurityDatabase:

    def __init__(self, database_path: Path = DATABASE_PATH):
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False
        )

        self.create_tables()

    def create_tables(self):

        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                pid INTEGER,
                process_name TEXT,
                executable TEXT,
                data TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                timestamp TEXT NOT NULL,
                pid INTEGER,
                process_name TEXT,
                executable TEXT,
                score INTEGER NOT NULL,
                level TEXT NOT NULL,
                reasons TEXT,
                FOREIGN KEY(event_id)
                    REFERENCES events(id)
            )
            """
        )

        self.connection.commit()

    def save_event(
        self,
        event: SecurityEvent
    ) -> int:

        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO events (
                timestamp,
                event_type,
                pid,
                process_name,
                executable,
                data
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.timestamp.isoformat(),
                event.event_type,
                event.pid,
                event.process_name,
                event.executable,
                json.dumps(event.data),
            )
        )

        self.connection.commit()

        return cursor.lastrowid

    def save_assessment(
        self,
        event_id: int,
        event: SecurityEvent,
        assessment: RiskAssessment
    ):

        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO assessments (
                event_id,
                timestamp,
                pid,
                process_name,
                executable,
                score,
                level,
                reasons
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event.timestamp.isoformat(),
                event.pid,
                event.process_name,
                event.executable,
                assessment.score,
                assessment.level,
                json.dumps(assessment.reasons),
            )
        )

        self.connection.commit()

    def close(self):

        self.connection.close()