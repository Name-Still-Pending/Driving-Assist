import numpy as np
import psutil
import threading
import redis
import kafka
import signal
from datetime import datetime
import time
import torch
import encoding.JSON as je
from prometheus_client import start_http_server, Counter, Gauge


process = psutil.Process()


class Detection:
    def __init__(self):
        # metrics gathering
        self.counter_frames = Counter('nn_frames', 'Number of frames processed by YOLO.')
        self.counter_vehicles_left = Counter("nn_vehicles_left", "Number of vehicles positioned left.")
        self.counter_vehicles_right = Counter("nn_vehicles_right", "Number of vehicles positioned right.")
        self.counter_vehicles_straight = Counter("nn_vehicles_straight", "Number of vehicles positioned straight.")
        self.counter_vehicles_ignored = Counter("nn_vehicles_ignored", "Number of ignored vehicles.")
        self.gauge_detection_time = Gauge('nn_detection_time', 'Time taken to detect objects in frame.')
        self.gauge_total_frame_time = Gauge('nn_total_frame_time', 'Total time taken to process a frame.')
        self.gauge_memory_usage = Gauge('nn_memory_usage', 'Amount of memory used by object detection.')
        self.gauge_cpu_usage = Gauge('nn_cpu_usage', 'CPU usage of object detection.')
        self.event = threading.Event()
        self.thread = threading.Thread(target=lambda: self.thread_do_work())

        self.vehicles_model = torch.hub.load("../yolov5", 'custom', source='local', path='weights/best.pt')
        self.signs_model = torch.hub.load("../yolov5", 'custom', source='local', path='weights/signs/weights.pt')

    @staticmethod
    def yolo_detect(model, frame, output, lock) -> None:
        # print(f'detection start')
        results = model(frame)
        # print('detection end')
        names = results.names
        preds = results.xyxy[0].numpy()
        sorted_dets = [list() for _ in range(len(names))]
        for i in preds:
            sorted_dets[int(i[5])].append(i[0: 5].tolist())
        classes = {names[i]: n for i, n in enumerate(sorted_dets) if len(n) > 0}
        with lock:
            output.update(classes)

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
        consumer.topics()
        lock = threading.Lock()
        models = [self.vehicles_model, self.signs_model]

        while True:

            # Read from Redis when message is received over Kafka
            consumer.seek_to_end()
            for raw_message in consumer:
                f_start = time.perf_counter()
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

                classes = {}

                # Detection
                det_s = time.perf_counter()
                threads = [threading.Thread(target=self.yolo_detect, args=[model, frame, classes, lock]) for model in models]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()

                self.gauge_detection_time.set(time.perf_counter() - det_s)

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

                self.counter_vehicles_ignored.inc(len(classes.get('vehicle_ign', [])))
                self.counter_vehicles_straight.inc(len(classes.get('vehicle_s', [])))
                self.counter_vehicles_right.inc(len(classes.get('vehicle_r', [])))
                self.counter_vehicles_left.inc(len(classes.get('vehicle_l', [])))

                if self.event.is_set():
                    break

                self.gauge_total_frame_time.set(time.perf_counter() - f_start)
                self.gauge_memory_usage.set(process.memory_info().rss)
                self.gauge_cpu_usage.set(process.cpu_percent(interval=None) / psutil.cpu_count())

                consumer.seek_to_end()
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
