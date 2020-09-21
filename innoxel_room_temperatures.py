#! /usr/bin/python3

import datetime
import json
import time
from enum import Enum
from logging.handlers import RotatingFileHandler

import config
import requests
from requests.auth import HTTPDigestAuth
import xmltodict
from influxdb import InfluxDBClient
import logging

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logFile = 'info.log'
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=50*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

logger = logging.getLogger('Innoxel_Room_Temperatures')
logger.setLevel(logging.INFO)
logger.addHandler(my_handler)


class WeatherStation:
    class UnitToRead(Enum):
        WeatherStation = 1
        RoomTemperature = 2
        HeaterValve = 3

    unit_to_read = UnitToRead.WeatherStation

    def __init__(self, ip, port, username, password, db_ip, db_port, db_name, room_temperature_enable):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.db_ip = db_ip
        self.db_port = db_port
        self.db_name = db_name
        self.room_temperature_enable = room_temperature_enable

    def get_data_from_innoxel(self, index=36, channelIndex=-1):
        """
        Read the weather data from innoxel weather station.
        :return: <dict> of measured values.
        """

        if self.unit_to_read == WeatherStation.UnitToRead.RoomTemperature:
            module = 'masterInModule'
            room_temp_str = "                    <u:roomTemperature />\\r\\n \r\n"
        elif self.unit_to_read == WeatherStation.UnitToRead.WeatherStation:
            module = 'masterInModule'
            room_temp_str = ""
        elif self.unit_to_read == WeatherStation.UnitToRead.HeaterValve:
            module = 'masterOutModule'
            room_temp_str = ""
        else:
            raise NameError

        payload = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n" \
                  "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/" \
                  "\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\r\n" \
                  "    <s:Body>\r\n" \
                  "        <u:getState xmlns:u=\"urn:innoxel-ch:service:noxnetRemote:1\">\r\n" \
                  "            <u:bootId />\r\n" \
                  "            <u:stateId />\r\n" \
                  "            <u:moduleList>\r\n" \
                  "                <u:module class=\"" + module + "\" index=\"" + str(index) + "\">\r\n" \
                  + room_temp_str + \
                  "                    <u:channel index=\"" + str(channelIndex) + "\" />\r\n" \
                  "                </u:module>\r\n" \
                  "            </u:moduleList>\r\n" \
                  "        </u:getState>\r\n" \
                  "    </s:Body>\r\n</s:Envelope>"
        headers = {
            'Content-Type': 'text/xml',
            'SOAPACTION': 'urn:innoxel-ch:service:noxnetRemote:1#getState'
        }
        url = self.ip + ':' + self.port + '/control'

        response = requests.request(method="POST",
                                    url=url,
                                    headers=headers,
                                    data=payload,
                                    auth=HTTPDigestAuth(self.username, self.password))
        result = xmltodict.parse(response.content)
        return result

    def parse_data_from_innoxel(self, dict_innoxel):

        parsed_dict = dict()

        if self.unit_to_read == WeatherStation.UnitToRead.RoomTemperature:
            module = dict_innoxel['s:Envelope']['s:Body']['u:getStateResponse']['u:moduleList']['u:module']['u:roomTemperature']
            parsed_dict['room_temperature'] = module["@value"]
        elif self.unit_to_read == WeatherStation.UnitToRead.HeaterValve:
            module = dict_innoxel['s:Envelope']['s:Body']['u:getStateResponse']['u:moduleList']['u:module']['u:channel']
            if module['@outState'] == 'on':
                parsed_dict['heater_status'] = 1
            elif module['@outState'] == 'off':
                parsed_dict['heater_status'] = 0
            else:
                raise TypeError

        elif self.unit_to_read == WeatherStation.UnitToRead.WeatherStation:
            module = dict_innoxel['s:Envelope']['s:Body']['u:getStateResponse']['u:moduleList']['u:module']
            for k, v in module.items():
                if str(k).startswith('u:'):
                    parsed_dict[k[2:]] = module[k]['@value']

        return parsed_dict

    def write_to_influx(self, measurement_dict, location_string):
        """
        Writes the measurement dict to the influx database.
        :param measurement_dict:
        :return: <boolean> successfully written to influxdb
        """
        if self.unit_to_read in [WeatherStation.UnitToRead.RoomTemperature, WeatherStation.UnitToRead.HeaterValve] :
            json_body = [
                {
                    "measurement": location_string,
                    "location": "Neuendorf",
                    "tags": {
                        "host": "Innoxel",
                        "Region": "Neuendorf"
                    },
                    "time": datetime.datetime.utcnow().isoformat(),
                    "fields": {
                        'roomTemperature': float(measurement_dict['room_temperature']),
                        'heater_status': float(measurement_dict['heater_status'])
                    }
                }
            ]
        else:

            json_body = [
                {
                    "measurement": "innoxel_weather_station",
                    "location": "Neuendorf",
                    "tags": {
                        "host": "Innoxel",
                        "Region": "Neuendorf"
                    },
                    "time": datetime.datetime.utcnow().isoformat(),
                    "fields": {
                        'temperatureAir': float(measurement_dict['temperatureAir']),
                         'temperatureAirFelt': float(measurement_dict['temperatureAirFelt']),
                         'windSpeed': float(measurement_dict['windSpeed']),
                         'sunBrightnessEast': float(measurement_dict['sunBrightnessEast']),
                         'sunBrightnessSouth': float(measurement_dict['sunBrightnessSouth']),
                         'sunBrightnessWest': float(measurement_dict['sunBrightnessWest']),
                         'sunTwilight': float(measurement_dict['sunTwilight']),
                         'precipitation': measurement_dict['precipitation']
                    }
                }
            ]
        # print(json_body)
        client = InfluxDBClient(host=self.db_ip, port=self.db_port, database=self.db_name)
        # print(client.get_list_database())
        # client.drop_database(dbname=self.db_name)
        # client.create_database(dbname=self.db_name)
        success = client.write_points(points=json_body, time_precision='s', database=self.db_name, protocol=u'json')
        return success


ws = WeatherStation(ip=config.ip,
                    port=config.port,
                    username=config.username,
                    password=config.password,
                    db_ip=config.db_ip,
                    db_port=config.db_port,
                    db_name=config.db_name,
                    room_temperature_enable=True)

# client = InfluxDBClient(host=ws.db_ip, port=ws.db_port, database=ws.db_name)
# for loc, val in config.dict_room_temperature.items():
#     client.drop_measurement(measurement=loc)
#     print("Deleted measurement: ", loc)
# time.sleep(1000005)
logger.info('...Gathering Data')

for [location_string, location_index] in config.dict_room_temperature.items():
    ws.unit_to_read = WeatherStation.UnitToRead.RoomTemperature
    ws_measurement = ws.get_data_from_innoxel(index=location_index, channelIndex=-1)
    ws_parsed_dict = ws.parse_data_from_innoxel(ws_measurement)
    # print(location_string, ": ".join(ws_parsed_dict.values()), "°C")
    # ws.write_to_influx(ws_parsed_dict, location_string)

    # print(ws_measurement)

    ws.unit_to_read = WeatherStation.UnitToRead.HeaterValve
    ws_heater_valve_state = ws.get_data_from_innoxel(index=config.dict_heater_valves[location_string][0],
                                                     channelIndex=config.dict_heater_valves[location_string][1])
    ws_parsed_dict.update(ws.parse_data_from_innoxel(ws_heater_valve_state))
    # print(location_string, " \t\t--> Temperatur: ",
    #       str(ws_parsed_dict.get('room_temperature')), "°C - Heater Status: ", ws_parsed_dict.get('heater_status'))
    ws.write_to_influx(ws_parsed_dict, location_string)
    log_msg = location_string, " --> Temperatur: ", str(ws_parsed_dict.get('room_temperature')), "°C - Heater Status: ", ws_parsed_dict.get('heater_status')
    logger.info(log_msg)

    # print(ws_heater_valve_state)
    # with open('outFile.json', 'w') as o:
    #     json.dump(ws_measurement, o, indent=4, sort_keys=True)

    time.sleep(0.25)



