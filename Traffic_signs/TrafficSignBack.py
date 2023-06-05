import cv2
import numpy as np
import playsound
import asyncio
from queue import Queue

# Create a queue for storing sound files to be played
sound_queue = Queue()

# Function to play sound files
async def play_sound():
    is_playing = False  # Flag to track if a sound is currently being played

    while True:
        if not is_playing and not sound_queue.empty():
            sound_file = sound_queue.get()  # Retrieve sound file from the queue
            is_playing = True

            def callback():
                nonlocal is_playing
                is_playing = False

            playsound.playsound(sound_file, False, callback=callback)
        await asyncio.sleep(0)  # Non-blocking delay

# Load the pre-trained YOLO model and labels
net = cv2.dnn.readNetFromDarknet('yolo.cfg', 'yolo.weights')
labels = ['stop', 'yield', 'right_of_way', '30', '40', '50', '60', '70', '80', '100', 'residential_area', 'residential_area_end', 'speed_limit_end', 'end_of_30', 'warning', 'one_way_road', 'bus_stop', 'crosswalk', 'roundebound', 'direction', 'no_entry', 'prohibition', 'ignore', 'info_sign']
# List of class labels

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

# Function to perform object detection on an image/frame
def perform_object_detection(image):
    # Perform object detection
    blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    outputs = net.forward(output_layers)

    # Process the detections
    detections = []
    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > 0.5:
                if class_id < 22:
                    # Add the detection to the list
                    detections.append((class_id, confidence))

    return detections

# Function to process frames
async def process_frames():
    detectedStatus = [False] * 22

    # Create a loop to continuously receive frames
    while True:
        currentStatus = [False] * 22

        # Receive a frame from the video loader (replace 'get_frame()' with the appropriate function from your video loader)
        frame = get_frame()  # TODO!!

        # Perform object detection on the frame
        detections = perform_object_detection(frame)

        # Process the detections and play sounds
        for detection in detections:
            class_id, confidence = detection

            currentStatus[class_id] = True

            if detectedStatus[class_id] == False:
                detectedStatus[class_id] = True
                sound_file = audio_files[class_id]
                sound_queue.put(sound_file)  # Add sound file to the queue

                if sound_queue.qsize() == 1:  # If it's the only sound in the queue, start playing immediately
                    asyncio.create_task(play_sound())  # Create a task for playing sound asynchronously

                if class_id == 0 or class_id == 1:
                    # send NoPriority TODO!!
                    pass
                elif class_id == 2:
                    # send Priority TODO!!
                    pass

            # Print the class label and confidence
            label = labels[class_id]
            print(f"Detected: {label} (Confidence: {confidence})")

        detectedStatus = currentStatus.copy()
        await asyncio.sleep(0)  # Non-blocking delay

# Main code
if __name__ == "__main__":
    # Start the event loop
    loop = asyncio.get_event_loop()

    # Create tasks for playing sounds and processing frames
    tasks = [
        asyncio.create_task(play_sound()),
        asyncio.create_task(process_frames())
    ]

    # Run the tasks concurrently in the event loop
    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except KeyboardInterrupt:
        pass
    finally:
        # Cancel tasks and close the event loop
        for task in tasks:
            task.cancel()
        loop.close()
