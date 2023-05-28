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
        return ret, frame


class VideoModifier:
    @staticmethod
    def add_noise(video, noise_type='salt_and_pepper', strength=0.1):
        noisy_video = []
        for frame in video:
            noisy_frame = frame.copy()
            h, w, _ = frame.shape

            if noise_type == 'gaussian':
                noise = np.random.normal(0, strength * 255, (h, w, 3)).astype(np.uint8)
                noisy_frame = cv2.add(noisy_frame.astype(np.int16), noise.astype(np.int16)).clip(0, 255).astype(
                    np.uint8)
            elif noise_type == 'salt_and_pepper':
                salt = np.random.choice([0, 1], (h, w, 3), p=[0.9, 0.1])
                pepper = np.random.choice([0, 1], (h, w, 3), p=[0.9, 0.1])
                noise = salt * 255 + pepper * 0
                noisy_frame = cv2.add(noisy_frame.astype(np.int16), noise.astype(np.int16)).clip(0, 255).astype(
                    np.uint8)

            noisy_video.append(noisy_frame)

        return noisy_video

    @staticmethod
    def change_spatial_resolution(video, target_resolution):
        modified_video = []
        for frame in video:
            modified_frame = cv2.resize(frame, target_resolution, interpolation=cv2.INTER_LINEAR)
            modified_video.append(modified_frame)

        return modified_video

    @staticmethod
    def modify_sampling_frequency(video, target_fps):
        current_fps = 30  # Assuming the current frame rate is 30 FPS
        target_delay = int(1000 / target_fps)  # Calculate the target delay between frames

        modified_video = []
        for frame in video:
            cv2.waitKey(target_delay)  # Delay between frames to achieve the desired FPS
            modified_video.append(frame)

        return modified_video

    @staticmethod
    def rotate_video(video):
        rotated_video = []
        for frame in video:
            rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            rotated_video.append(rotated_frame)

        return rotated_video


class FrameProducer:
    def __init__(self, video_processor, frame_modifier):
        self.video_processor = video_processor
        self.frame_modifier = frame_modifier
        self.red = redis.Redis()
        self.topic = 'frame_notification'
        self.producer = kafka.KafkaProducer(bootstrap_servers='localhost:9092')
        self.modifications = {
            ord('1'): {'name': 'Add Noise', 'function': self.frame_modifier.add_noise,
                       'args': {'noise_type': 'args', 'strength': 0.1}},
            ord('2'): {'name': 'Change Resolution', 'function': self.frame_modifier.change_spatial_resolution,
                       'args': {}},
            ord('3'): {'name': 'Modify Sampling Frequency', 'function': self.frame_modifier.modify_sampling_frequency,
                       'args': {}},
            ord('4'): {'name': 'Rotate Video', 'function': self.frame_modifier.rotate_video, 'args': {}}
        }
        self.modified_video = []
        self.current_modification = None
        self.display_thread = None
        self.display_frame = None
        self.quit_display = False

    def process_frames(self):
        while True:
            ret, frame = self.video_processor.read_frame()

            message = {
                "id": "new_frame",
                "frame_n": int(self.video_processor.vc.get(cv2.CAP_PROP_POS_FRAMES)),
                "fps": self.video_processor.fps,
                "width": self.video_processor.width,
                "height": self.video_processor.height
            }

            # Write new dimensions and FPS to Kafka message
            if self.current_modification:
                if 'target_resolution' in self.current_modification['args']:
                    message['width'], message['height'] = self.current_modification['args']['target_resolution']
                if 'target_fps' in self.current_modification['args']:
                    message['fps'] = self.current_modification['args']['target_fps']

            key = cv2.waitKey(1) & 0xFF

            if key == ord('0'):
                self.modified_video = []
                self.current_modification = None
                self.display_frame = frame
            elif key in self.modifications:
                self.current_modification = self.modifications[key]
                if self.current_modification['name'] == 'Change Resolution':
                    new_width = int(input("Enter new width: "))
                    new_height = int(input("Enter new height: "))
                    self.current_modification['args']['target_resolution'] = (new_width, new_height)
                elif self.current_modification['name'] == 'Modify Sampling Frequency':
                    target_fps = int(input("Enter target FPS: "))
                    self.current_modification['args']['target_fps'] = target_fps
                self.display_frame = None
            elif key == ord('4') and self.current_modification and self.current_modification['name'] == 'Rotate Video':
                self.modified_video = self.frame_modifier.rotate_video(self.modified_video)
                message['width'] = self.modified_video.shape
                message['height'] = self.video_processor.width

                if len(self.modified_video) > 0:
                    self.display_frame = self.modified_video[0]

            if self.current_modification:
                self.modified_video = self.current_modification['function']([frame],
                                                                            **self.current_modification['args'])
                if len(self.modified_video) > 0:
                    self.display_frame = self.modified_video[0]

            if key == ord('q'):
                break

            # send frame over redis
            self.red.set("frame:latest", np.array(self.display_frame).tobytes())

            # send frame info over kafka
            future = self.producer.send(self.topic, json.dumps(message).encode('utf-8'),
                                        timestamp_ms=round(time.time() * 1000))

            try:
                rm = future.get(timeout=10)
            except kafka.KafkaError:
                pass

            t_start = time.perf_counter()
            t_stop = time.perf_counter()
            t_elapsed = t_stop - t_start
            t_frame = 1 / self.video_processor.fps
            t_sleep = t_frame - t_elapsed
            if t_sleep > 0:
                time.sleep(t_sleep)

        self.video_processor.vc.release()
        cv2.destroyAllWindows()


def sigint_handler(signum, frame):
    # f_producer.stop_display_thread()
    exit(0)


def display_menu():
    print("Menu:")
    print("0: Play Original Video")
    print("1: Add Noise")
    print("2: Change Spatial Resolution")
    print("3: Modify Sampling Frequency")
    print("4: Rotate Video")
    print("q: Quit")


def get_noise_type():
    while True:
        noise_type = input("Select noise type (1 for Gaussian, 2 for Salt and Pepper): ")
        if noise_type == '1':
            return 'gaussian'
        elif noise_type == '2':
            return 'salt_and_pepper'
        else:
            print("Invalid input. Please try again.")


v_provider = VideoProvider("data/sample_0.avi")
f_modifier = VideoModifier()
f_producer = FrameProducer(v_provider, f_modifier)


def main():

    signal.signal(signal.SIGINT, sigint_handler)

    thread = threading.Thread(target=f_producer.process_frames)
    thread.start()
    # f_producer.start_display_thread()

    while True:
        display_menu()
        option = input("Select an option: ")

        if option == '0':
            f_producer.current_modification = None
        elif option == '1':
            f_producer.current_modification = f_producer.modifications[ord('1')]
            f_producer.current_modification['args']['noise_type'] = get_noise_type()
        elif option == '2':
            new_width = int(input("Enter new width: "))
            new_height = int(input("Enter new height: "))
            f_producer.current_modification = f_producer.modifications[ord('2')]
            f_producer.current_modification['args']['target_resolution'] = (new_width, new_height)
        elif option == '3':
            target_fps = int(input("Enter target FPS: "))
            f_producer.current_modification = f_producer.modifications[ord('3')]
            f_producer.current_modification['args']['target_fps'] = target_fps
        elif option == '4':
            f_producer.current_modification = f_producer.modifications[ord('4')]
        elif option == 'q':
            break

    # f_producer.stop_display_thread()
    thread.join()


if __name__ == "__main__":
    main()
