
import os
import socket
import requests
import constants
from constants import CentralServerApi

def get_hostname():
    return os.environ.get('COMPUTERNAME') or socket.gethostname()

def get_credentials_from_server():
    try:
        r = requests.get(CentralServerApi.TOKEN.format(hostname=get_hostname()), timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print("Token fetch error:", e)
    return None

def update_central_server_ip(central_server_ip):
    configurations = {}
    config_file = os.path.join(os.path.dirname(__file__), constants.CONFIG_FILE)
    with open(config_file, 'r') as config:
        for config_line in config.readlines():
            config_pair = config_line.split('=')
            configurations.update({config_pair[0]: config_pair[1]})
    configurations[CentralServerApi.CENTRAL_SERVER_IP_KEY] = central_server_ip
    with open(config_file, 'w') as config:
        for configuration_key, configuration_value in configurations.items():
            config.writelines(configuration_key+'='+configuration_value)
    CentralServerApi.reload()
    return configurations