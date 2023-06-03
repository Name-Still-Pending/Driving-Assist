import numpy as np
import cv2
import threading
import redis
import signal
import time
import kafka


class FrameModifier:
    NOISE_NONE = 0
    NOISE_GAUSSIAN = 1
    NOISE_SALT_AND_PEPPER = 2

    @staticmethod
    def scale_frame(frame: np.ndarray, res: [int, int]):
        modified_frame = cv2.resize(frame, res, interpolation=cv2.INTER_LINEAR)
        return modified_frame

    @staticmethod
    def add_noise(frame: np.ndarray, mode: int, factor: float):
        h, w, _ = frame.shape
        match mode:
            case FrameModifier.NOISE_GAUSSIAN:
                noise = np.random.normal(0, factor * 255, (h, w, 3)).astype(np.uint8)
                noisy_frame = cv2.add(frame.astype(np.int16), noise.astype(np.int16)).clip(0, 255).astype(np.uint8)

            case FrameModifier.NOISE_SALT_AND_PEPPER:
                salt = np.random.choice([0, 1], (h, w, 3), p=[0.9, 0.1])
                pepper = np.random.choice([0, 1], (h, w, 3), p=[0.9, 0.1])
                noise = salt * 255 + pepper * 0
                noisy_frame = cv2.add(frame.astype(np.int16), noise.astype(np.int16)).clip(0, 255).astype(np.uint8)

            case _:
                return frame
        return noisy_frame

    @staticmethod
    def rotate_frame(frame: np.ndarray):
        rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        return rotated_frame
