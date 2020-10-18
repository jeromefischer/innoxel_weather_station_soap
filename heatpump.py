#! /usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import time
import config
from idna import unicode
from influxdb import InfluxDBClient
from bs4 import BeautifulSoup
import selenium
from selenium.webdriver.common.keys import Keys


def generate_json(data):

    json_body = [
        {
            "measurement": "heatpump",
            "location": "Neuendorf",
            "tags": {
                "host": "heatpump",
                "Region": "Neuendorf"
            },
            "time": datetime.datetime.utcnow().isoformat(),
            "fields": data
        }
    ]
    print(json_body)
    return json_body


class Heatpump():

    def __init__(self, url, heatpump_data_points, db_ip, db_port, db_name):

        self.url = url
        self.heatpump_data_points = heatpump_data_points
        self.db_ip = db_ip
        self.db_port = db_port
        self.db_name = db_name

    def get_measurements_from_heatpump(self):
        
        chrome_options = selenium.webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        driver = selenium.webdriver.Chrome(options=chrome_options,
                                           executable_path='/usr/lib/chromium-browser/chromedriver')
        driver.get(self.url)
        search_box = driver.find_element_by_id(("password_prompt_input"))
        search_box.send_keys('99999')
        search_box.send_keys(Keys.RETURN)
        nav = driver.find_element_by_xpath("/html/body/nav/ul/li/a")
        nav.click()
        time.sleep(0.5)
        r = driver.page_source
        driver.quit()
        return r

    def parse_measurement(self, measurement_data):

        parsed_html = BeautifulSoup(measurement_data, features="lxml")
        data = {}
        for k, i in self.heatpump_data_points:
            measure = parsed_html.contents[1].contents[2].contents[5].contents[0].contents[k].contents[0].contents[0].contents[i].contents[0].contents[0]
            try:
                status = unicode(parsed_html.contents[1].contents[2].contents[5].contents[0].contents[k].contents[0].contents[0].contents[i].contents[1].contents[0])
            except:
                status = 'n.a.'

            # remove unit from data point
            if status.endswith('kWh'):
                status = status[:-3]
            elif status.endswith('°C') or status.endswith('kW'):
                status = status[:-2]
            elif status.endswith('h'):
                status = status[:-1]
            print("{}: {}".format(measure, status))
            data[measure] = status

        # check if current status is "Heizen".
        # If so, create new data point "Leistung Heizen" and write value.
        # If it is "Warmwasser", create new data point "Leistung Warmwasser" and write value
        data['Leistung Heizen'] = float(0)
        data['Leistung WW']  = float(0)
        if data['Betriebszustand'] == 'Heizen':
            data['Leistung Heizen'] = data['Leistung Ist']
        elif data['Betriebszustand'] == 'WW':
            data['Leistung WW'] = data['Leistung Ist']
        # remove unused data points from dict
        del data['Leistung Ist']
        del data['Betriebszustand']

        # since we now have only integers in the data dict as values, we can convert all values to float
        # (required to have for influxDB
        for m, n in data.items():
            data[m] = float(data[m])

        return data

    def write_to_influx(self, json_body):
        # InfluxDB Configuration
        client = InfluxDBClient(host=self.db_ip, port=self.db_port, database=self.db_name)
        # print(client.get_list_database())
        #client.drop_database(dbname=self.db_name)
        #client.create_database(dbname=self.db_name)
        success = client.write_points(points=json_body, time_precision='s', database=self.db_name, protocol=u'json')

        print('successfully written to db: {}'.format(success))
        return success


hp = Heatpump(url=config.heatpump_url,
              heatpump_data_points=config.heatpump_data_points,
              db_ip=config.db_ip,
              db_port=config.db_port,
              db_name=config.heatpump_db_name)

meas = hp.get_measurements_from_heatpump()
parsed = hp.parse_measurement(measurement_data=meas)
json_data = generate_json(data=parsed)
success = hp.write_to_influx(json_body=json_data)
