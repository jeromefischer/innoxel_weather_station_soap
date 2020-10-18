# Innoxel Weather Station Configuration
ip = 'http://192.168.2.172'
port = '5001'
username = 'SOAP'
password = 'soap'

dict_room_temperature = {'UG - Waschküche': 16,
                         'UG - Vorplatz': 20,
                         'EG - WC': 34,
                         'EG - Küche': 36,
                         'EG - Wohnen': 48,
                         'OG - Vorplatz': 56,
                         'OG - Büro Jerome': 60,
                         'OG - Zimmer Nord': 62,
                         'OG - Elternzimmer': 64,
                         'OG - Büro Jasmin': 70,
                         'OG - Bad': 72,
                         'OG - Elternbad': 74
                         }

dict_heater_valves = {'UG - Waschküche': [4, 0],
                      'UG - Vorplatz': [4, 1],
                      'EG - WC': [4, 2],
                      'EG - Küche': [4, 3],
                      'EG - Wohnen': [4, 4],
                      'OG - Vorplatz': [5, 0],
                      'OG - Büro Jerome': [5, 1],
                      'OG - Zimmer Nord': [5, 2],
                      'OG - Elternzimmer': [5, 3],
                      'OG - Büro Jasmin': [5, 4],
                      'OG - Bad': [5, 5],
                      'OG - Elternbad': [5, 6]
                      }

# InfluxDB Configuration
db_ip = '192.168.2.152'
db_port = '8086'
db_name = 'innoxel'

# Heatpump
heatpump_db_name = 'heatpump'
heatpump_url = "http://192.168.2.223/Webserver/index.html"
# TEMPERATUREN: parsed_html.contents[1].contents[2].contents[5].contents[0].contents[00]
# 01: Vorlauf
# 02: Rücklauf
# 03: Rücklauf Soll
# 05: Aussentemperatur
# 06: Mitteltemperatur
# 07: Warmwasser-Ist
# 08: Warmwasser-Soll
# 09: Wärmequelle-Ein
temps = [1, 2, 3, 5, 6, 7, 8, 9]

# EINGÄNGE: parsed_html.contents[1].contents[2].contents[5].contents[0].contents[01]

# AUSGÄNGE: parsed_html.contents[1].contents[2].contents[5].contents[0].contents[02]

# ABLAUFZEITEN: parsed_html.contents[1].contents[2].contents[5].contents[0].contents[03]

# BETRIEBSSTUNDEN: parsed_html.contents[1].contents[2].contents[5].contents[0].contents[04]
# 1: Betriebsstunden VD1
# 2: Impulse Verdichter 1
# 3: Laufzeit Durchschnitt VD1
# 5: Betriebsstunden WP
# 6: Betriebsstunden Heizung
# 7: Betriebsstunden WW
eingaenge = [1, 2, 5, 6, 7]

# FEHLERSPEICHER: parsed_html.contents[1].contents[2].contents[5].contents[0].contents[05]
# 1:

# ABSCHALTUNGEN: parsed_html.contents[1].contents[2].contents[5].contents[0].contents[06]
# 1:

# ANLAGESTATUS: parsed_html.contents[1].contents[2].contents[5].contents[0].contents[07]
# 5: Betriebszustand
# 6: Leistung
anlagestatus = [5, 6]

# WÄRMEERZEUGER: parsed_html.contents[1].contents[2].contents[5].contents[0].contents[08]
# 1: Heizung
# 2: Warmwasser
# 3: Gesamt
waermeerzeugung = [1, 2, 3]

heatpump_data_points = [(0, 1), (0, 2), (0, 3), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9),
                        (4, 1), (4, 2), (4, 5,), (4, 6), (4, 7),
                        (7, 5), (7, 6),
                        (8, 1), (8, 2), (8, 3)]


