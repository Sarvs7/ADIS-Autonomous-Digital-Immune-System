from queue import Queue

from engine.events import SecurityEvent


class EventBus:

    def __init__(self):
        self.queue = Queue()

    def publish(self, event: SecurityEvent):
        self.queue.put(event)

    def get(self, timeout=None):
        return self.queue.get(timeout=timeout)

    def empty(self):
        return self.queue.empty()