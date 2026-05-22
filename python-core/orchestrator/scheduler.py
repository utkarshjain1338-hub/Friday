import asyncio


class Scheduler:
    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def schedule_task(self, coro):
        return self.loop.create_task(coro)
