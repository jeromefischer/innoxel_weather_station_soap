#! /usr/bin/python3

import datetime
import config
import requests
from requests.auth import HTTPDigestAuth
import xmltodict
from influxdb import InfluxDBClient


class WeatherStation:

    def __init__(self, ip, port, username, password, db_ip, db_port, db_name):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.db_ip = db_ip
        self.db_port = db_port
        self.db_name = db_name

    def get_weather_from_innoxel(self):
        """
        Read the weather data from innoxel weather station.
        :return: <dict> of measured values.
        """

        payload = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n" \
                  "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\r\n" \
                  "    <s:Body>\r\n" \
                  "        <u:getState xmlns:u=\"urn:innoxel-ch:service:noxnetRemote:1\">\r\n" \
                  "            <u:bootId />\r\n" \
                  "            <u:stateId />\r\n" \
                  "            <u:moduleList>\r\n" \
                  "                <u:module class=\"masterWeatherModule\" index=\"-1\">\r\n" \
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

    @staticmethod
    def parse_weather_station_measurement(dict_innoxel):

        module = dict_innoxel['s:Envelope']['s:Body']['u:getStateResponse']['u:moduleList']['u:module']
        parsed_dict = dict()
        for k, v in module.items():
            if str(k).startswith('u:'):
                parsed_dict[k[2:]] = module[k]['@value']
        return parsed_dict

    def write_to_influx(self, measurement_dict):
        """
        Writes the measurement dict to the influx database.
        :param measurement_dict:
        :return: <boolean> successfully written to influxdb
        """

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
        print(json_body)
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
                    db_name=config.db_name)

ws_measurement = ws.get_weather_from_innoxel()
ws_parsed_dict = ws.parse_weather_station_measurement(ws_measurement)
ws.write_to_influx(ws_parsed_dict)


