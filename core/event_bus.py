from typing import Callable


class EventBus:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_name: str, callback: Callable):
        self.listeners.setdefault(event_name, []).append(callback)

    def emit(self, event_name: str, payload=None):
        for callback in self.listeners.get(event_name, []):
            callback(payload)
