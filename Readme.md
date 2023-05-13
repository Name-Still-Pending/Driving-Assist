# Project Name Pending

### Structure
* **root**
  * **custom_utils:** Utility python package
  * **docs:** Useful literature and examples
  * **Grafana:** Files related to Grafana metrics overview tool
  * **Kafka:** Kafka files (do not edit)
  * **object_recognition:** Object recognition component
  * **Prometheus:** Prometheus files (do not edit)
  * **training_data:** Organized and annotated samples for YOLO object recognition training
  * **video_provider:** Video provider component
  * **visualization:** Visualization component
  * **yolov5**: YOLO v5 submodule (do not edit)

## Setup
### 1. Linux

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
3. Build Kafka docker image:
    ```
    sudo docker-compose build
    ```
4. Start docker containers (Kafka, Zookeeper, Redis, Prometheus, Grafana):
    ```
    sudo docker-compose up
    ```
5. Run python scripts:
    ```
    python object_detection/detection.py
    python video_provider/video_provider.py
    python visualization/visualization.py
    ```