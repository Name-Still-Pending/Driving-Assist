# Get diagnostic data from Kafka using JMX Exporter and Kafka Exporter
Check Kafka/Dockerfile
- Instructions copy latest JMX Exporter and its configutation to Kafka image
- If you encounter problem like (docker-compose logs -f):
  - Error opening zip file or JAR manifest missing: /usr/app/jnx_prometheus.jar
- Try removing Kafka image from docker (docker image rm wurstmeister/kafka -f)
- Rebuild image using docker-compose build and then running docker-compose up -d

Lets take a look into
- Kafka/Dockerfile and Kafka/jmx_prometheus_config.yml

# To run JMX Exporter
We have to add EXTRA_ARGS to docker-compose.yaml
8181 is the port of JMX exporter

Lest check docker-compose.yaml file.

The docker-compose.yaml file specifies running Redis, Prometheus, Grafana, Zookeeper and Kafka
- At the part where Prometheus gets loaded, configuration file prometheus.yml is added.
- At the part where Kafka gets loaded KAFKA_CREATE_TOPICS is added, to automaticly add needed topics.

File Prometheus/prometheus.yml specifies how Kafka metrics will be exposed

# Running system
After running docker-compose up -d we should have a working system

Check http://localhost:8000 - python script metrics

Take a look to address http://localhost:9090 (Prometheus)
In menu select Status/Targets - Kafka and our pythron script must be UP

Continue to Grafana
Open address http://localhost:3000 (Default login is admin/admin)
You should add new connection
- Open menu Top/Left and select Connections
- Search for Prometheus
- Create new Prometheus connection Top/Right
- Enter http://prometheus:9090 into URL field
- Click Save and Test on the bottom

Next thing you need to do is add a Dashboard to display data
- Open menu Top/Left and select Dashboards
- From New menu Top/Left select Import
- Select Grafana/kafka_board.json
- Set Prometheus datasource and click Import

## IMPORTANT
Changes in code:
- con_visualization.py - at line 20 added group_id='grp_visualization'
- con_pro_detection.py - added Prometheus metrics

Prometheus needs access to host
- open port 8000 in firewall (port where python metrics are exposed)

## Additional
Adding Docker metrics to Prometheus/Grafana
- https://docs.docker.com/config/daemon/prometheus/

## USEFUL COMMANDS

# Modify retention time
sudo docker exec kafka /opt/kafka/bin/kafka-configs.sh --alter --add-config retention.ms=2000 --bootstrap-server=kafka:9092 --topic frame_noticifation

# Kill all running docker containers
sudo docker kill $(sudo docker ps -q)

# Remove all images
sudo docker rmi $(sudo docker images -a -q)

# Prune - Remove unused data
sudo docker system prune