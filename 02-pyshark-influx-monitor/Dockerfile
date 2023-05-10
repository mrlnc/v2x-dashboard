FROM python:3.7-alpine

ARG INTERFACE
ARG LOCATION

LABEL maintainer="Merlin Chlosta" \
      description="PyShark to InfluxDB bridge"

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /app
WORKDIR /app

CMD ["python3", "-u", "monitor.py", "--interface", $INTERFACE, "--location", $LOCATION]