#!/usr/bin/env python3

"""PyShark <-> InfluxDB bridge for ITS traffic

This script listens for 802.11p ITS-G5 traffic and pushes packets to InfluxDB
"""

from typing import NamedTuple, Tuple
import argparse
import datetime

import pyshark
from influxdb import InfluxDBClient

INFLUXDB_ADDRESS    = '172.18.0.3' # IP of InfluxDB container
INFLUXDB_USER       = 'root'
INFLUXDB_PASSWORD   = 'root'
INFLUXDB_DATABASE   = 'its'

class SpeedMeasurement(NamedTuple):
    station_id: int
    timestamp:  int
    speed:      float
    latitude:   float
    longitude:  float

class MeasurementLocation(NamedTuple):
    """Which station was this recorded on?"""
    name: str

class Measurement(NamedTuple):
    measurementType = "speed"
    measurementLocation: MeasurementLocation
    measurementValue: SpeedMeasurement

def get_speed(its_layer) -> float:
    speed_ms = int(its_layer.speedValue)
    # speed format: 1412 = 14.12 m/s
    speed_kmh = speed_ms * 60.0 * 60.0 / 1000.0 / 100.0
    return speed_kmh

def get_lat_lon(its_layer) -> Tuple[float, float]:
    lat = float(its_layer.latitude) / 10000000.0
    lon = float(its_layer.longitude) / 10000000.0
    return lat, lon

def format_speed(speed: float) -> str:
    return format(speed, ".2f").rjust(5)

def _init_influxdb_database(influxdb_client: InfluxDBClient, database: str, purge_db: bool = False):
    if purge_db:
        influxdb_client.drop_database(database)
    
    databases = influxdb_client.get_list_database()
    if len(list(filter(lambda x: x['name'] == database, databases))) == 0:
        print('Creating database ' + database)
        influxdb_client.create_database(database)

    influxdb_client.switch_database(database)

def _send_data_to_influxdb(influxdb_client: InfluxDBClient, data: Measurement) -> bool:
    json_body = [
        {
            'measurement': data.measurementType,
            'tags': {
                'location': data.measurementLocation,
                'station_id': data.measurementValue.station_id
            },
            'fields': {
                'lat': data.measurementValue.latitude,
                'lon': data.measurementValue.longitude,
                "speed": data.measurementValue.speed,
                "station_id": data.measurementValue.station_id
            },
            "time": data.measurementValue.timestamp
        }
    ]
    return influxdb_client.write_points(json_body, time_precision="n")

def packet_to_influx(influxdb_client: InfluxDBClient, packet) -> bool:
    timestamp = int(float(packet.frame_info.time_epoch) * 1000000000)

    try:
        its_layer = packet["ITS"]
    except:
        return False

    if its_layer.speedValue == 16383:
        # reserved value "unavailable"
        return False

    speed = get_speed(its_layer)
    lat, lon = get_lat_lon(its_layer)
    station_id = int(its_layer.stationid)

    speedMeas = SpeedMeasurement(station_id=station_id,  timestamp=timestamp, speed=speed, latitude=lat, longitude=lon)
    measurement = Measurement(measurementLocation=args.location, measurementValue=speedMeas)
    return _send_data_to_influxdb(influxdb_client, measurement)

def main(args):
    influxdb_client = InfluxDBClient(args.db_ip, 8086, args.db_user, args.db_password, None)
    _init_influxdb_database(influxdb_client, args.db_table, args.purge_db)

    if args.file is not None:
        print(f"Reading PCAP: {args.file}")
        success = 0
        error = 0
        try:
            pcap = pyshark.FileCapture(args.file)
            for packet in pcap:
                ret = packet_to_influx(influxdb_client, packet)
                if ret:
                    success += 1
                else:
                    error += 1
        except:
            pass
        
        print(f"Reading PCAP finished. Packets read: {success}, errors: {error}")

    if args.interface is not None:
        print(f"Monitoring interface: {args.interface}")
        capture = pyshark.LiveCapture(interface=args.interface)

        try:
            for packet in capture.sniff_continuously():
                ret = packet_to_influx(influxdb_client, packet)
                print(f"Packet arrived: {datetime.datetime.now()}")
        except PermissionError as e:
            print(f"Insufficient permissions to sniff on interface {args.interface}. Try with sudo.")
            print(f"Error: ")
            print(f"{e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = 'ITS-G5 to InfluxDB',
        description = 'Read ITS-G5 V2X traffic and push to InfluxDB')

    parser.add_argument("-f", "--file", default=None, help="Input PCAP")
    parser.add_argument("-i", "--interface", default=None, help="Monitor Interface")
    parser.add_argument("-l", "--location", type=str, required=True, help="Name of this Station")
    parser.add_argument("-x", "--purge-db", action="store_true", help="Purge InfluxDB")
    parser.add_argument("-u", "--db-user", type=str, default=INFLUXDB_USER, help="InfluxDB Username")
    parser.add_argument("-p", "--db-password", type=str, default=INFLUXDB_PASSWORD, help="InfluxDB Password")
    parser.add_argument("-t", "--db-table", type=str, default=INFLUXDB_DATABASE, help="InfluxDB Table")
    parser.add_argument("-ip", "--db-ip", type=str, default=INFLUXDB_ADDRESS, help="InfluxDB IP")
    
    args = parser.parse_args()

    if args.file is None and args.interface is None:
        print(f"No input specified, you need to provide either PCAP input file or an interface to monitor.")
        parser.print_usage()
        exit(1)

    if args.file is not None and args.interface is not None:
        print(f"Specifiy either input file or interface, not both at the same time.")
        parser.print_usage()
        exit(1)

    main(args)