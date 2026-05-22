import asyncio
from typing import Callable, Dict, List, Any


class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Any], Any]]] = {}

    def subscribe(self, event_name: str, callback: Callable[[Any], Any]):
        self._listeners.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Any], Any]):
        if event_name in self._listeners:
            try:
                self._listeners[event_name].remove(callback)
            except ValueError:
                pass

    async def emit(self, event_name: str, payload: Any = None):
        listeners = list(self._listeners.get(event_name, []))
        tasks = []
        for cb in listeners:
            # support both async and sync callbacks
            if asyncio.iscoroutinefunction(cb):
                tasks.append(asyncio.create_task(cb(payload)))
            else:
                # run sync callback in thread to avoid blocking
                tasks.append(asyncio.to_thread(cb, payload))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
from typing import Callable


class EventBus:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_name: str, callback: Callable):
        self.listeners.setdefault(event_name, []).append(callback)

    def emit(self, event_name: str, payload=None):
        for callback in self.listeners.get(event_name, []):
            callback(payload)
