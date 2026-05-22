class LongTermMemory:
    def __init__(self):
        self.notes = []

    def remember(self, note: str):
        self.notes.append(note)

    def recall(self):
        return self.notes
