import numpy as np
import cv2

import threading
import redis
import kafka
import signal
from datetime import datetime
import time
import torch
import encoding.JSON as je
from prometheus_client import start_http_server, Counter



class Detection:
    def __init__(self):
        self.counter_neuralnetwork = Counter('nn_detections', 'Number of NN detections')
        self.event = threading.Event()
        self.thread = threading.Thread(target=lambda: self.thread_do_work())

    def thread_do_work(self):
        # Redis
        red = redis.Redis()

        # Kafka
        con_topic = 'frame_notification'
        prod_topic = 'frame_detection'
        producer = kafka.KafkaProducer(bootstrap_servers='localhost:9092')

        # auto_offset_reset indicates where the consumer starts consuming the message in case of an interruption
        consumer = kafka.KafkaConsumer(con_topic, bootstrap_servers='localhost:9092', auto_offset_reset='earliest',
                                       group_id='grp_detection', consumer_timeout_ms=2000)
        consumer.poll()
        # PyTorch
        # model = torch.hub.load("ultralytics/yolov5", 'custom', path='results/train/exp2/weights/bes.pt', trust_repo=True)
        model = torch.hub.load("../yolov5", 'custom', source='local', path='weights/best.pt')
        consumer.topics()
        while True:

            # Read from Redis when message is received over Kafka
            consumer.seek_to_end()
            for raw_message in consumer:
                msgJSON = je.decode_bin(raw_message.value)
                message = msgJSON["id"]

                if message == "new_frame":
                    frame_time = datetime.fromtimestamp(raw_message.timestamp / 1000)
                    curr_time = datetime.now()
                    diff = (curr_time - frame_time).total_seconds()

                    # Exclude old frames
                    if diff < 2:
                        frame_temp = np.frombuffer(red.get("frame:latest"), dtype=np.uint8)

                        # Convert image
                        if np.shape(frame_temp)[0] == 540 * 960 * 3:
                            frame = frame_temp.reshape((540, 960, 3))

                            # Detection
                            results = model(frame)
                            names = results.names
                            preds = results.xyxy[0].numpy()
                            sorted_dets = [[] for _ in range(len(names))]
                            for i in preds:
                                sorted_dets[int(i[5])].append(i[0: 5].tolist())

                            detection_message = {
                                "frame_n": msgJSON["frame_n"],
                                "classes": {
                                    names[i]: n for i, n in enumerate(sorted_dets) if len(n) > 0
                                }
                            }

                            # Send detection data over Kafka
                            future = producer.send(prod_topic, je.encode_bin(detection_message),
                                                   timestamp_ms=round(time.time() * 1000))

                            # Wait until message is delivered to Kafka
                            try:
                                rm = future.get(timeout=10)
                            except kafka.KafkaError:
                                pass

                        self.counter_neuralnetwork.inc(1)

                if self.event.is_set():
                    break

            # Stop loop
            if self.event.is_set():
                break

    def sigint_handler(self, signum, frame):
        self.event.set()
        self.thread.join()
        exit(0)

    def run(self):
        signal.signal(signal.SIGINT, self.sigint_handler)
        start_http_server(8000)
        self.thread.start()
        input("Press CTRL+C or Enter to stop visualization...")
        self.event.set()
        self.thread.join()


if __name__ == "__main__":
    det = Detection()
    det.run()
