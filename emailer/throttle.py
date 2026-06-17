from __future__ import annotations

import random
import time
from collections import deque


class RateLimiter:
    def __init__(self, max_per_hour: int, min_delay: int = 20, max_delay: int = 60):
        self.max_per_hour = max(1, max_per_hour)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.sent_timestamps: deque[float] = deque()

    def wait_if_needed(self) -> None:
        now = time.time()
        one_hour_ago = now - 3600
        while self.sent_timestamps and self.sent_timestamps[0] < one_hour_ago:
            self.sent_timestamps.popleft()

        if len(self.sent_timestamps) >= self.max_per_hour:
            wait_time = 3600 - (now - self.sent_timestamps[0])
            if wait_time > 0:
                time.sleep(wait_time)

        self.sent_timestamps.append(time.time())

    def random_delay_seconds(self) -> int:
        return random.randint(self.min_delay, self.max_delay)
