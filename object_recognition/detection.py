import numpy as np

import threading
import redis
import kafka
import signal
from datetime import datetime
import time
import torch
import encoding.JSON as je
from prometheus_client import start_http_server, Counter, Gauge


class Detection:
    def __init__(self):
        self.counter_frames = Counter('nn_frames', 'Number of frames processed by YOLO.')
        self.counter_vehicles = Counter("nn_vehicles", 'Number of detected vehicles.')
        self.gauge_detection_time = Gauge('nn_detection_time', 'Time taken to detect objects in frame.')
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
        model = torch.hub.load("../yolov5", 'custom', source='local', path='weights/best.pt')
        consumer.topics()

        while True:

            # Read from Redis when message is received over Kafka
            consumer.seek_to_end()
            for raw_message in consumer:
                msg_dict = je.decode_bin(raw_message.value)

                if msg_dict['id'] != "new_frame":
                    continue

                frame_time = datetime.fromtimestamp(raw_message.timestamp / 1000)
                curr_time = datetime.now()
                diff = (curr_time - frame_time).total_seconds()

                if diff >= 2:
                    continue
                # Exclude old frames
                frame_temp = np.frombuffer(red.get("frame:latest"), dtype=np.uint8)

                h, w = msg_dict['res']
                if np.shape(frame_temp)[0] != h * w * 3:
                    continue
                # Convert image
                frame = frame_temp.reshape((h, w, 3))

                # Detection
                det_s = time.perf_counter()
                results = model(frame)
                self.gauge_detection_time.set(time.perf_counter() - det_s)

                names = results.names
                preds = results.xyxy[0].numpy()
                sorted_dets = [[] for _ in range(len(names))]
                for i in preds:
                    sorted_dets[int(i[5])].append(i[0: 5].tolist())
                classes = {names[i]: n for i, n in enumerate(sorted_dets) if len(n) > 0}
                detection_message = {
                    "frame_n": msg_dict["frame_n"],
                    "classes": classes
                }

                # Send detection data over Kafka
                future = producer.send(prod_topic, je.encode_bin(detection_message),
                                       timestamp_ms=round(time.time() * 1000))

                # Wait until message is delivered to Kafka
                try:
                    _ = future.get(timeout=10)
                except kafka.KafkaError:
                    pass

                self.counter_frames.inc(1)

                vc = len(classes.get('vehicle_ign', []))
                vc += len(classes.get('vehicle_s', []))
                vc += len(classes.get('vehicle_r', []))
                vc += len(classes.get('vehicle_l', []))

                self.counter_vehicles.inc(vc)

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
