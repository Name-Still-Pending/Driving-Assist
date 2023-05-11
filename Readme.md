# Project Name Pending

### Structure
* **root**
  * **custom_utils:** Utility python package
  * **docs:** Useful literature and examples
  * **object_recognition:** Object recognition component
  * **training_data:** Organized and annotated samples for YOLO object recognition training
  * **video_provider:** Video provider component
  * **visualization:** Visualization component
  * **yolov5**: YOLO v5 submodule (do not edit)

### Setup

1. Create a python virtual environment.
    ```
   python -m venv <path/to/new/venv>
    ```
2. Install python requirements:
    ```
    pip install -r requirements.txt
    ```
    If that doesn't work, try:
    ```
    pip3 install -r requirements.txt
    ```
3. Start docker images for kafka, redis...:
   ```
    docker-compose up
   ```
4. run python scripts:
   ```
   python object_detection/detection.py
   python video_provider/video_provider.py
   python visualization/visualization.py
   ```