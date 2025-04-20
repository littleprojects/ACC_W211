
"""
Class creates a timer how will set a Flag after a given time
"""

import time

class Timer:

    def __init__(self, sec_interval, event, stop_event):

        self.sec_interval = sec_interval

        self.event = event
        self.stop_event = stop_event

        self.last_ts = time.time()

    def tick(self):

        now = time.time()

        # only with valid interval
        if self.sec_interval > 0:
            # interval check
            if now - self.last_ts >= self.sec_interval:
                # time up - set Flag
                self.event.set()

                # reset time
                self.last_ts = now

                # print('.')

    def run(self):

        while True:
            self.tick()

            if self.stop_event.is_set():
                break

            time.sleep(0.0001)