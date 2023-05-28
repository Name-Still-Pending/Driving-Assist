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
            cv2.imshow('Video Player', frame)  # Display the frame
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

    def display_frames(self):
        while not self.quit_display:
            if self.display_frame is not None:
                cv2.imshow('Modified Video - ' + self.current_modification['name'], self.display_frame)
            if cv2.waitKey(1) == ord('q'):
                break

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

            self.red.set("frame:latest", np.array(frame).tobytes())

            # Write new dimensions and FPS to Kafka message
            if self.current_modification:
                if 'target_resolution' in self.current_modification['args']:
                    message['width'], message['height'] = self.current_modification['args']['target_resolution']
                if 'target_fps' in self.current_modification['args']:
                    message['fps'] = self.current_modification['args']['target_fps']

            future = self.producer.send(self.topic, json.dumps(message).encode('utf-8'),
                                        timestamp_ms=round(time.time() * 1000))

            try:
                rm = future.get(timeout=10)
            except kafka.KafkaError:
                pass

            if frame.size > 0:
                cv2.imshow('Video Player', frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('0'):
                cv2.imshow('Modified Video - Original', frame)
                self.modified_video = []
                self.current_modification = None
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
                if len(self.modified_video) > 0:
                    self.display_frame = self.modified_video[0]

            if self.current_modification:
                self.modified_video = self.current_modification['function']([frame],
                                                                            **self.current_modification['args'])
                if len(self.modified_video) > 0:
                    self.display_frame = self.modified_video[0]

            if key == ord('q'):
                break

            t_start = time.perf_counter()
            t_stop = time.perf_counter()
            t_elapsed = t_stop - t_start
            t_frame = 1 / self.video_processor.fps
            t_sleep = t_frame - t_elapsed
            if t_sleep > 0:
                time.sleep(t_sleep)

        self.video_processor.vc.release()
        cv2.destroyAllWindows()

    def start_display_thread(self):
        self.display_thread = threading.Thread(target=self.display_frames)
        self.display_thread.start()

    def stop_display_thread(self):
        self.quit_display = True
        if self.display_thread:
            self.display_thread.join()


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
