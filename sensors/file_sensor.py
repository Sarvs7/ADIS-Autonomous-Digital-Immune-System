import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from engine.events import SecurityEvent, now_utc


class FileEventHandler(FileSystemEventHandler):

    def __init__(
        self,
        callback: Callable[[SecurityEvent], None]
    ):
        self.callback = callback

    def emit_event(
        self,
        event_type: str,
        path: str
    ):

        event = SecurityEvent(
            event_type=event_type,
            timestamp=now_utc(),
            data={
                "path": path
            }
        )

        self.callback(event)

    def on_created(self, event):

        if event.is_directory:
            return

        self.emit_event(
            "file_created",
            event.src_path
        )

    def on_modified(self, event):

        if event.is_directory:
            return

        self.emit_event(
            "file_modified",
            event.src_path
        )

    def on_deleted(self, event):

        if event.is_directory:
            return

        self.emit_event(
            "file_deleted",
            event.src_path
        )

    def on_moved(self, event):

        if event.is_directory:
            return

        self.emit_event(
            "file_modified",
            event.dest_path
        )


class FileSensor:

    def __init__(
        self,
        watch_path: str | Path,
        callback: Callable[[SecurityEvent], None]
    ):

        self.watch_path = Path(watch_path)
        self.callback = callback

        self.observer = Observer()

        self.handler = FileEventHandler(
            callback
        )

    def start(self):

        self.watch_path.mkdir(
            parents=True,
            exist_ok=True
        )

        self.observer.schedule(
            self.handler,
            str(self.watch_path),
            recursive=True
        )

        self.observer.start()

    def stop(self):

        self.observer.stop()
        self.observer.join()