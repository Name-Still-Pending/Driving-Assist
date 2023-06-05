import cv2
import numpy as np
import playsound
import threading
from queue import Queue

# Create a queue for storing sound files to be played
sound_queue = Queue()

# Function to play sound files
def play_sound(sound_file):
    playsound.playsound(sound_file)

# Load the pre-trained YOLO model and labels
net = cv2.dnn.readNetFromDarknet('yolo.cfg', 'yolo.weights')
labels = ['stop', 'yield', 'right_of_way', '30', '40', '50', '60', '70', '80', '100', 'residential_area', 'residential_area_end', 'speed_limit_end', 'end_of_30', 'warning', 'one_way_road', 'bus_stop', 'crosswalk', 'roundebound', 'direction', 'no_entry', 'prohibition', 'ignore', 'info_sign']
    # List of class labels
detectedStatus = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]

# Set the paths to the WAV files for each class
audio_files = {
    0: 'Stop.wav',
    1: 'Yield.wav',
    2: 'RightOfWay.wav',
    3: '30.wav',
    4: '40.wav',
    5: '50.wav',
    6: '60.wav',
    7: '70.wav',
    8: '80.wav',
    9: '100.wav',
    10: 'ResidentialArea.wav',
    11: 'ResidentialAreaEnd.wav',
    12: 'SpeedLimitEnd.wav',
    13: 'EndOf30.wav',
    14: 'Warning.wav',
    15: 'OneWayRoad.wav',
    16: 'BusStop.wav',
    17: 'Crosswalk.wav',
    18: 'Roundebound.wav',
    19: 'Direction.wav',
    20: 'NoEntry.wav',
    21: 'Prohibition.wav',
}

# Load the image
image = cv2.imread('image.jpg')

# Perform object detection
blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
net.setInput(blob)
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
outputs = net.forward(output_layers)

# Process the detections
for output in outputs:
    for detection in output:
        scores = detection[5:]
        class_id = np.argmax(scores)
        confidence = scores[class_id]

        if confidence > 0.5 :
            if class_id < 22:
                # Play the corresponding sound based on the class index
                if detectedStatus[class_id] == False :
                    detectedStatus[class_id] = True
                    sound_file = audio_files[class_id]
                    sound_queue.put(sound_file)  # Add sound file to the queue

                    if sound_queue.qsize() == 1:  # If it's the only sound in the queue, start playing immediately
                        sound_thread = threading.Thread(target=play_sound, args=(sound_file,))
                        sound_thread.start()

                    if class_id == 0 or class_id == 1:
                        # send NoPriority
                        pass
                    elif class_id == 2:
                        # send Priority
                        pass

            # Print the class label and confidence
            label = labels[class_id]
            print(f"Detected: {label} (Confidence: {confidence})")
