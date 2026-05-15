class ShortTermMemory:
    def __init__(self):
        self.messages = []

    def add(self, message: str):
        self.messages.append(message)

    def get_recent(self, count=5):
        return self.messages[-count:]
