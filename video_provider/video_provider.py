import numpy as np
import cv2
import threading
import redis
import signal
import time
import kafka
import json


class VideoProvider:
    def __init__(self, video_input):
        self.video_input = video_input
        self.vc = cv2.VideoCapture(video_input)
        self.fps = self.vc.get(cv2.CAP_PROP_FPS)
        self.width = int(self.vc.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vc.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def read_frame(self):
        ret, frame = self.vc.read()
        if not ret:
            vc.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # Prepare message
        message = {
            "id": "new_frame",
            "frame_n": int(vc.get(cv2.CAP_PROP_POS_FRAMES))
        }

        # Add frame to redis
        red.set("frame:latest", np.array(frame).tobytes())

        # Send notification about new frame over Kafka
        future = producer.send(topic, je.encode_bin(message), timestamp_ms=round(time.time() * 1000))

        # Wait until message is delivered to Kafka
        try:
            rm = future.get(timeout=10)
        except kafka.KafkaError:
            pass

        # Preserve FPS
        t_stop = time.perf_counter()
        t_elapsed = t_stop - t_start
        t_frame = 1000 / fps / 1000
        t_sleep = t_frame - t_elapsed
        if t_sleep > 0:
            time.sleep(t_sleep)

        # Stop loop
        if event.is_set():
            vc.release()
            break    


def sigint_handler(signum, frame):
    event.set()
    thread.join()
    exit(0)


signal.signal(signal.SIGINT, sigint_handler)

event = threading.Event()
thread = threading.Thread(target=lambda: thread_produce())

if __name__ == "__main__":
    thread.start()
    input("Press CTRL+C or Enter to stop producing...")
    event.set()
    thread.join()
