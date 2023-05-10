This is an adapter that:

1. listens on the WiFi interface for incoming ITS-G5 traffic
2. pushes the data to InfluxDB

Create a venv and install dependencies:
```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

You can then run the script. Set `-l` to the location of the sniffer, which helps identify the data if you have multiple sniffers pushing to the same DB.

```
01-pyshark/monitor.py -l home -i wlp2s0-monitor
```

NOTE: the script requires that you previously configured the interface correctly. see `01-setup-interface/`.

The systemd-unit `monitor.service` helps running the script on startup.
