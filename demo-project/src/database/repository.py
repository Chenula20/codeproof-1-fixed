class EventRepository:
    def __init__(self):
        self.events = []

    def add(self, event):
        self.events.append(dict(event))

    def all(self):
        return [dict(event) for event in self.events]
