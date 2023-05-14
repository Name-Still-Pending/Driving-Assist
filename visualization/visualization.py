import numpy as np
import cv2
import threading
import redis
import kafka
import signal
from datetime import datetime
import encoding.JSON as je


# Global detection list
# TODO: Using globals is not the best solution, modify this
preds_list = []
preds_time = datetime.now()
lock = threading.Lock()

def thread_detection():
    global preds_list, preds_time

    # Kafka
    topic = 'frame_detection'
    consumer = kafka.KafkaConsumer(bootstrap_servers='localhost:9092', auto_offset_reset='earliest', consumer_timeout_ms=2000)
    consumer.subscribe([topic])

    while True:
    
        # Read detection data from Kafka
        for message in consumer:

            # Decode string
            preds_str = message.value.decode("utf-8")

            with lock:
                preds_list = preds_str.split("|") if len(preds_str) > 0 else []
                preds_time = datetime.fromtimestamp(message.timestamp / 1000)

            if event.is_set():
                break   

        # Stop loop
        if event.is_set():
            cv2.destroyAllWindows()
            break    


def thread_frames():
    global preds_list, preds_time

    # Redis
    red = redis.Redis()

    # Video
    frame = 0

    # Kafka
    topic = 'frame_notification'
    consumer = kafka.KafkaConsumer(topic, bootstrap_servers='localhost:9092', auto_offset_reset='earliest', group_id='grp_visualization', consumer_timeout_ms=2000)
    consumer.poll()

    while True:
        # Read from Redis when message is received over Kafka
        consumer.seek_to_end()
        for raw_message in consumer:
            msg_dict = je.decode_bin(raw_message.value)
            message = msg_dict["id"]

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

                    # Plot detection
                    if (curr_time - preds_time).total_seconds() < 5:
                        with lock:
                            for pred_str in preds_list:
                                # column_start,row_start,column_end,row_end
                                pred = [int(float(v)) for v in pred_str.split(",")]
                                # Top
                                cv2.line(frame, (pred[0], pred[1]), (pred[2], pred[1]), (0, 0, 255), 5)
                                # Bottom
                                cv2.line(frame, (pred[0], pred[3]), (pred[2], pred[3]), (0, 0, 255), 5)
                                # Left
                                cv2.line(frame, (pred[0], pred[1]), (pred[0], pred[3]), (0, 0, 255), 5)
                                # Right
                                cv2.line(frame, (pred[2], pred[1]), (pred[2], pred[3]), (0, 0, 255), 5)

                    # Display image
                    cv2.imshow("frame", frame)
                    cv2.waitKey(1)

            if event.is_set():
                break

        # Stop loop
        if event.is_set():
            cv2.destroyAllWindows()
            break    


def sigint_handler(signum, frame):
    event.set()
    thread_frm.join()
    thread_det.join()
    exit(0)


signal.signal(signal.SIGINT, sigint_handler)

event = threading.Event()
thread_frm = threading.Thread(target=lambda: thread_frames())
thread_det = threading.Thread(target=lambda: thread_detection())

if __name__ == "__main__":
    thread_frm.start()
    thread_det.start()
    input("Press CTRL+C or Enter to stop visualization...")
    event.set()
    thread_frm.join()
    thread_det.join()
