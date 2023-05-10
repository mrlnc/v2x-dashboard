The Docker-Compose file runs two services:

- influxdb
- grafana

First set up a `DATA_DIR` for persistent data:

```
mkdir ~/data
export DATA_DIR=/home/merlin/data/
```

Then start the containers:

```
sudo -E docker-compose up -d
```
