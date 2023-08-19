import numpy as np
import cv2
import threading
import redis
import kafka
import signal
import encoding.JSON as je
from enum import IntEnum
import TrafficSignBack


class TurnWarning(IntEnum):
    NONE = 0
    LEFT = 1
    RIGHT = 2
    STRAIGHT = 4
    LEFT_STRAIGHT = LEFT | STRAIGHT
    RIGHT_STRAIGHT = RIGHT | STRAIGHT
    ALL = LEFT | STRAIGHT | RIGHT


VEHICLE_IGN = 'vehicle_ign'
VEHICLE_L = 'vehicle_l'
VEHICLE_R = 'vehicle_r'
VEHICLE_S = 'vehicle_s'


class Visualization:
    __turn_masks = {
        'default': {VEHICLE_L: TurnWarning.NONE,
                    VEHICLE_R: TurnWarning.LEFT_STRAIGHT,
                    VEHICLE_S: TurnWarning.LEFT},
        'priority': {VEHICLE_L: TurnWarning.NONE,
                     VEHICLE_R: TurnWarning.NONE,
                     VEHICLE_S: TurnWarning.LEFT},
        'priority_to_left': {VEHICLE_L: TurnWarning.NONE,
                             VEHICLE_R: TurnWarning.NONE,
                             VEHICLE_S: TurnWarning.LEFT},
        'priority_to_right': {VEHICLE_L: TurnWarning.NONE,
                              VEHICLE_R: TurnWarning.LEFT_STRAIGHT,
                              VEHICLE_S: TurnWarning.NONE},
        'yield': {VEHICLE_L: TurnWarning.ALL,
                  VEHICLE_R: TurnWarning.LEFT_STRAIGHT,
                  VEHICLE_S: TurnWarning.LEFT},
        'yield_left_straight': {VEHICLE_L: TurnWarning.ALL,
                                VEHICLE_R: TurnWarning.LEFT_STRAIGHT,
                                VEHICLE_S: TurnWarning.ALL},
        'yield_right_straight': {VEHICLE_L: TurnWarning.NONE,
                                 VEHICLE_R: TurnWarning.ALL,
                                 VEHICLE_S: TurnWarning.ALL}

    }

    def __init__(self):
        self.__preds_dict = {"frame_n": -1024, 'classes': []}
        self.lock = threading.Lock()
        self.event = threading.Event()
        self.thread_frm = threading.Thread(target=lambda: self.__thread_frames())
        self.thread_det = threading.Thread(target=lambda: self.__thread_detection())
        self.names = ['vehicle_ign', 'vehicle_l', 'vehicle_r', 'vehicle_s']
        self.colors = {
            'vehicle_ign': (128, 128, 128),
            'vehicle_l': (255, 0, 0),
            'vehicle_r': (0, 255, 0),
            'vehicle_s': (0, 0, 255)
        }
        signal.signal(signal.SIGINT, self.__sigint_handler)

        self.priority_mode = 'default'
        self.warning_player = TrafficSignBack.WarningPlayer()

    def __thread_detection(self):

        # Kafka
        topic = 'frame_detection'
        consumer = kafka.KafkaConsumer(topic, bootstrap_servers='localhost:9092', auto_offset_reset='earliest', consumer_timeout_ms=2000)
        consumer.poll(1000)

        while True:

            consumer.seek_to_end()
            # Read detection data from Kafka
            for message in consumer:

                with self.lock:
                    self.__preds_dict = je.decode_bin(message.value)

                if self.event.is_set():
                    break

            # Stop loop
            if self.event.is_set():
                cv2.destroyAllWindows()
                break

    def __thread_frames(self):
        # Redis
        red = redis.Redis()

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

                if message != "new_frame":
                    continue

                frame_temp = np.frombuffer(red.get("frame:latest"), dtype=np.uint8)

                h, w = msg_dict['res']
                if np.shape(frame_temp)[0] != h * w * 3:
                    continue
                frame = frame_temp.reshape((h, w, 3))

                with self.lock:
                    f_diff = (msg_dict["frame_n"] - self.__preds_dict['frame_n'])
                    dets = self.__preds_dict['classes']
                    turn_rules = Visualization.__turn_masks[self.priority_mode]
                    # print(f_diff)
                if 0 <= f_diff < 100:
                    for cls in dets:
                        color = self.colors.get(cls, (0, 0, 0))
                        restriction = turn_rules.get(cls)
                        self.warning_player.try_queue_warning(cls, raw_message.timestamp * 1000)
                        for d in dets[cls]:
                            rect = np.int32(d)
                            cv2.rectangle(frame, rect[0: 2], rect[2: 4], color, 3)
                            cv2.putText(frame, cls, (rect[0], rect[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

                            # warning sounds

                            if restriction is None:
                                continue

                            center = ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)

                            if restriction & TurnWarning.LEFT > 0:  # L_TURN
                                cv2.line(frame, center, (rect[0], center[1]), color, 3)
                            if restriction & TurnWarning.RIGHT > 0:  # R_TURN
                                cv2.line(frame, center, (rect[2], center[1]), color, 3)
                            if restriction & TurnWarning.STRAIGHT > 0:  # STRAIGHT
                                cv2.line(frame, center, (center[0], rect[1]), color, 3)

                        # self.__detection_logic(frame, classes)
                cv2.imshow('Frame', frame)
                cv2.waitKey(1)

                if self.event.is_set():
                    break

            # Stop loop
            if self.event.is_set():
                cv2.destroyAllWindows()
                break

    def __sigint_handler(self, signum, frame):
        self.stop()
        exit(0)

    def set_priority_mode(self, mode: str):
        assert mode in Visualization.__turn_masks
        with self.lock:
            self.priority_mode = mode

    def start(self):
        self.thread_frm.start()
        self.thread_det.start()
        self.warning_player.start()
        while True:
            print('Options:')
            print('  1: Set priority mode')
            print('  q: Quit')

            s = input('Selection: ')
            match s:
                case '1':
                    print("Select priority mode:")
                    print('  1: Default')
                    print('  2: Priority')
                    print('  3: Priority to left')
                    print('  4: Priority to right')
                    print('  5: Yield')
                    print('  6: Yield straight and left')
                    print('  7: Yield straight and right')
                    while True:
                        m = int(input("Selection: ")) - 1
                        if 0 > m >= len(Visualization.__turn_masks):
                            print("invalid option, try again!")
                            continue
                        mode = list(Visualization.__turn_masks)[m]
                        self.set_priority_mode(mode)
                        break
                    print("Mode set")

                case 'q':
                    print('Stopping ...')
                    break

        self.stop()

    def stop(self):
        self.event.set()
        self.warning_player.stop()
        self.thread_frm.join()
        self.thread_det.join()

if __name__ == "__main__":
    vis = Visualization()
    vis.start()
