import json

import numpy as np
import cv2
import threading
import redis
import signal
import time
import kafka
import custom_utils as cu

def thread_produce():
    # Redis
    red = redis.Redis()

    # Video
    vidInput = "data/video_854x480.mp4"
    vc = cv2.VideoCapture(vidInput)
    fps = 30

    # Kafka
    topic = 'frame_notification'
    producer = kafka.KafkaProducer(bootstrap_servers='localhost:9092')

    while True:
        t_start = time.perf_counter()
        ret, frame = vc.read()

        # Jump back to the beginning of input
        if not ret:
            vc.set(cv2.CAP_PROP_POS_FRAMES, 0)

        message = {
            "id": "new_frame",
            "frame_n": int(vc.get(cv2.CAP_PROP_POS_FRAMES))
        }

        # Add frame to redis
        red.set("frame:latest", np.array(frame).tobytes())

        # Send notification about new frame over Kafka
        future = producer.send(topic, cu.json_encode(message), timestamp_ms=round(time.time()*1000))

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