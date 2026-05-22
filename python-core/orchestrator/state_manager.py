from collections import deque


class StateManager:
    def __init__(self, max_history=20):
        self.history = deque(maxlen=max_history)

    def add_message(self, text: str):
        self.history.append(text)

    def get_history(self):
        return list(self.history)
