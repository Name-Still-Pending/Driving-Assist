import concurrent.futures.thread
import threading

import cv2
import numpy as np
import playsound
import asyncio
from queue import Queue
import time
import os
import random


labels = ['stop', 'yield', 'right_of_way', '30', '40', '50', '60', '70', '80', '100', 'residential_area',
          'residential_area_end', 'speed_limit_end', 'end_of_30', 'warning', 'one_way_road', 'bus_stop', 'crosswalk',
          'roundebound', 'direction', 'no_entry', 'prohibition', 'ignore', 'info_sign']

audio_files = [
     'Stop.wav',
     'Yield.wav',
     'RightOfWay.wav',
     '30.wav',
     '40.wav',
     '50.wav',
     '60.wav',
     '70.wav',
     '80.wav',
     '100.wav',
     'ResidentialArea.wav',
     'ResidentialAreaEnd.wav',
     'SpeedLimitEnd.wav',
     'EndOf30.wav',
     'Warning.wav',
     'OneWayRoad.wav',
     'BusStop.wav',
     'Crosswalk.wav',
     'Roundabout.wav',
     'Direction.wav',
     'NoEntry.wav',
     'Prohibition.wav',
]


class WarningPlayer:
    audio = {
        labels[i]: audio_files[i] for i in range(min(len(labels), len(audio_files)))
    }

    def __init__(self, audio_path: str | None = 'warning_sounds', replay_threshold_ms: int | None = 3000):
        self.audio_path = audio_path
        self.replay_threshold = replay_threshold_ms
        t = int(time.time() * 1000 - replay_threshold_ms)
        self.last_detected_timestamp = {cls: t for cls in WarningPlayer.audio}
        self.warn_queue = Queue()
        self.queue_lock = threading.Lock()
        self.sound_thread = threading.Thread(target=self.play_sound)
        self.end_event = threading.Event()
        self.end_event.clear()
        self.pause_event = threading.Event()

    def play_sound(self):
        while not self.end_event.is_set():
            with self.queue_lock:
                empty = self.warn_queue.empty()
            if empty:
                self.pause_event.clear()
                self.pause_event.wait()

            if self.end_event.is_set():
                break

            with self.queue_lock:
                file = self.warn_queue.get()

            playsound.playsound(os.path.join(self.audio_path, file), True)

    def try_queue_warning(self, warning: str, time_ms):
        with self.queue_lock:
            warn = WarningPlayer.audio.get(warning)

        if warn is None:
            return

        diff = time_ms - self.last_detected_timestamp[warning]
        self.last_detected_timestamp[warning] = time_ms
        if diff < self.replay_threshold:
            return

        with self.queue_lock:
            self.warn_queue.put(warn)
            self.pause_event.set()

    def start(self):
        self.sound_thread.start()

    def stop(self):
        self.end_event.set()
        self.pause_event.set()
        self.sound_thread.join()


def test(fps):
    player = WarningPlayer()
    player.start()
    f_time = 1 / fps
    for _ in range(100):
        t_start = time.perf_counter()

        samples = random.sample(labels, random.randint(0, 5))
        t = time.time() * 1000
        for s in samples:
            player.try_queue_warning(s, t)

        diff = f_time - (time.perf_counter() - t_start)
        if diff > 0:
            time.sleep(diff)

    time.sleep(10)
    player.stop()

# Main code
if __name__ == "__main__":
    test(30)
