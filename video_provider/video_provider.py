import numpy as np
import cv2
import threading
import redis
import signal
import time
import kafka
import json
import encoding.JSON as je


class VideoProvider:
    NOISE_NONE = 0
    NOISE_GAUSSIAN = 1
    NOISE_SALT_AND_PEPPER = 2

    def __init__(self, video_input):
        self.lock = threading.Lock()
        self.video_input = video_input
        self.vc = cv2.VideoCapture(video_input)
        self.default_fps = self.vc.get(cv2.CAP_PROP_FPS)
        self.fps = self.default_fps
        self.default_frame_duration = 1 / self.default_fps
        self.frame_duration = self.default_frame_duration
        self.noise_mode = VideoProvider.NOISE_NONE
        self.noise_factor = .2
        self.scaling = False
        self.scaling_resolution = (-1, -1)
        self.rotation = False

        self.producer_thread = threading.Thread(target=self.produce_frames)
        self.stop_event = threading.Event()

    def read_frame(self) -> [int, np.ndarray]:
        ret, frame = self.vc.read()
        if not ret:
            self.vc.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.vc.read()
        return self.vc.get(cv2.CAP_PROP_POS_FRAMES), frame

    def scale_frame(self, frame: np.ndarray):
        modified_frame = cv2.resize(frame, self.scaling_resolution, interpolation=cv2.INTER_LINEAR)
        return modified_frame

    def add_noise(self, frame: np.ndarray):
        h, w, _ = frame.shape
        match self.noise_mode:
            case VideoProvider.NOISE_GAUSSIAN:
                noise = np.random.normal(0, self.noise_factor * 255, (h, w, 3)).astype(np.uint8)
                noisy_frame = cv2.add(frame.astype(np.int16), noise.astype(np.int16)).clip(0, 255).astype(np.uint8)

            case VideoProvider.NOISE_SALT_AND_PEPPER:
                salt = np.random.choice([0, 1], (h, w, 3), p=[0.9, 0.1])
                pepper = np.random.choice([0, 1], (h, w, 3), p=[0.9, 0.1])
                noise = salt * 255 + pepper * 0
                noisy_frame = cv2.add(frame.astype(np.int16), noise.astype(np.int16)).clip(0, 255).astype(np.uint8)

            case _:
                return frame
        return noisy_frame

    def rotate_frame(self, frame: np.ndarray):
        rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        return rotated_frame

    def produce_frames(self):
        red = redis.Redis()
        topic = 'frame_notification'
        producer = kafka.KafkaProducer(bootstrap_servers='localhost:9092')
        last_frame_start = time.perf_counter()
        vid_time = self.vc.get(cv2.CAP_PROP_POS_MSEC)

        while True:
            f_start = time.perf_counter()
            vid_time += f_start - last_frame_start
            last_frame_start = f_start

            self.vc.set(cv2.CAP_PROP_POS_MSEC, vid_time * 1000)
            ret, frame = self.vc.read()
            if not ret:
                self.vc.set(cv2.CAP_PROP_POS_FRAMES, 0)
                vid_time = self.vc.get(cv2.CAP_PROP_POS_MSEC)
                continue

            with self.lock:
                # image scaling
                if self.scaling:
                    frame = self.scale_frame(frame)

                # noise
                if self.noise_mode != VideoProvider.NOISE_NONE:
                    frame = self.add_noise(frame)

                # rotation
                if self.rotation:
                    frame = self.rotate_frame(frame)

            message = {
                "id": "new_frame",
                "frame_n": int(self.vc.get(cv2.CAP_PROP_POS_FRAMES)),
                "fps": self.fps,
                "res": frame.shape[0: 2]
            }

            # send frame via Redis
            red.set("frame:latest", frame.tobytes())

            # send frame info over kafka
            future = producer.send(topic, je.encode_bin(message), timestamp_ms=int(time.time() * 1000))
            try:
                rm = future.get(timeout=10)
            except kafka.KafkaError:
                pass

            f_time = time.perf_counter() - f_start
            with self.lock:
                t_sleep = self.frame_duration - f_time
            if t_sleep > 0:
                time.sleep(t_sleep)

            if self.stop_event.is_set():
                break

    def set_noise(self, mode: int, factor: float):
        assert 0 <= mode <= 2

        with self.lock:
            self.noise_mode = mode
            self.noise_factor = factor

    def set_fps(self, fps: float):
        with self.lock:
            if abs(fps - self.default_fps) < 0.0001:
                self.fps = self.default_fps
                self.frame_duration = self.default_frame_duration
                return

            self.fps = fps
            self.frame_duration = 1 / fps

    def set_resolution(self, res: [int, int], default: bool | None = False):
        with self.lock:
            self.scaling_resolution = res
            self.scaling = not default

    def set_rotation(self, do: bool):
        with self.lock:
            self.rotation = do

    def start_frame_production(self):
        signal.signal(signal.SIGINT, self.sigint_handler)
        self.producer_thread.start()

    def stop_frame_production(self):
        self.stop_event.set()
        self.producer_thread.join()

    def sigint_handler(self, signum, frame):
        self.stop_frame_production()
        exit(0)


def display_menu():
    print("Menu:")
    print("  1: Set Noise")
    print("  2: Set resolution")
    print("  3: Set sampling framerate")
    print("  4: Toggle rotation")
    print("  5: Clear modifiers")
    print("  q: Quit")


def noise_setting():
    print("Select noise setting:")
    print("  0: None")
    print("  1: Gaussian")
    print("  2: Salt and pepper")

    o = VideoProvider.NOISE_NONE
    f = .0
    while True:
        s = input("Selection: ")
        match s:
            case '0':
                o = VideoProvider.NOISE_NONE
                break
            case '1' | '2':
                o = VideoProvider.NOISE_GAUSSIAN if s == '1' else VideoProvider.NOISE_SALT_AND_PEPPER
                f = float(input('Noise factor: '))
                break
            case _:
                print('Invalid selection, try again!')
    return [o, f]


def main():

    v_provider = VideoProvider("data/sample_0.avi")
    v_provider.start_frame_production()

    while True:
        display_menu()
        option = input("Select an option: ")

        match option:
            case '1':
                opts = noise_setting()
                v_provider.set_noise(*opts)

            case '2':
                h = int(input("Height: "))
                w = int(input("Width:  "))
                v_provider.set_resolution([h, w])

            case '3':
                fps = float(input("New sampling framerate: "))
                v_provider.set_fps(fps)

            case '4':
                v_provider.set_rotation(not v_provider.rotation)
                print('Rotation toggled')

            case '5':
                v_provider.set_rotation(False)
                v_provider.set_noise(VideoProvider.NOISE_NONE, 0)
                v_provider.set_fps(v_provider.default_fps)
                v_provider.set_resolution([-1, -1], True)

                print('Modifiers cleared')

            case 'q':
                print('Stopping ...')
                v_provider.stop_frame_production()
                break


if __name__ == "__main__":
    main()
