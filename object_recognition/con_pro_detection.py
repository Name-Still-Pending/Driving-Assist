import numpy as np
import cv2
import threading
import redis
import kafka
import signal
from datetime import datetime
import time
import torch
import json
import custom_utils as cu


def thread_do_work():
    # Redis
    red = redis.Redis()

    # Kafka
    con_topic = 'frame_notification'
    prod_topic = 'frame_detection'
    producer = kafka.KafkaProducer(bootstrap_servers='localhost:9092')

    # auto_offset_reset indicates where the consumer starts consuming the message in case of an interruption
    consumer = kafka.KafkaConsumer(con_topic, bootstrap_servers='localhost:9092', auto_offset_reset='earliest',
                                   group_id='grp_detection', consumer_timeout_ms=2000)
    consumer.poll(10000)
    # PyTorch
    model = torch.hub.load("ultralytics/yolov5", "yolov5n", trust_repo=True)
    consumer.topics()
    while True:

        # Read from Redis when message is received over Kafka
        consumer.seek_to_end()
        for raw_message in consumer:
            msgJSON = cu.json_decode(raw_message.value)
            message = msgJSON["id"]

            if message == "new_frame":
                frame_time = datetime.fromtimestamp(raw_message.timestamp / 1000)
                curr_time = datetime.now()
                diff = (curr_time - frame_time).total_seconds()

                # Exclude old frames
                if diff < 2:
                    frame_temp = np.frombuffer(red.get("frame:latest"), dtype=np.uint8)

                    # Convert image
                    if np.shape(frame_temp)[0] == 1229760:
                        frame = frame_temp.reshape((480, 854, 3))

                        # Detection
                        results = model(frame)
                        names = results.names
                        preds = results.xyxy[0].numpy()
                        preds_list = []
                        for pred in preds:
                            if names[int(pred[-1])] == "person":
                                preds_list.append(",".join(str(v) for v in pred[0:4]))

                        # Send detection data over Kafka
                        # TODO: Not the best way of sending and reading data with Kafka
                        #       Modify sending and receiving using value_serializer and value_deserializer and work with JSON on both sides
                        future = producer.send(prod_topic, str.encode("|".join(preds_list)),
                                               timestamp_ms=round(time.time() * 1000))

                        # Wait until message is delivered to Kafka
                        try:
                            rm = future.get(timeout=10)
                        except kafka.KafkaError:
                            pass

        if event.is_set():
            break

        # Stop loop
        if event.is_set():
            break


def sigint_handler(signum, frame):
    event.set()
    thread.join()
    exit(0)


signal.signal(signal.SIGINT, sigint_handler)

event = threading.Event()
thread = threading.Thread(target=lambda: thread_do_work())

if __name__ == "__main__":
    thread.start()
    input("Press CTRL+C or Enter to stop visualization...")
    event.set()
    thread.join()
