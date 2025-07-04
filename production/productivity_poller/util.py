
import os
import socket
import requests
import constants
from constants import CentralServerApi

def get_hostname():
    return os.environ.get('COMPUTERNAME') or socket.gethostname()

def get_credentials_from_server(custom_config_path=None):
    try:
        CentralServerApi.refresh_config(custom_config_path)
        r = requests.get(CentralServerApi.TOKEN.format(hostname=get_hostname()), timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print("Token fetch error:", e)
    return None

def update_central_server_ip(central_server_ip, config_path):
    configurations = {}
    with open(config_path, 'r') as config:
        for config_line in config.readlines():
            config_pair = config_line.strip().split('=')
            if len(config_pair) == 2:
                configurations[config_pair[0]] = config_pair[1]

    configurations["CENTRAL_SERVER_IP"] = central_server_ip

    with open(config_path, 'w') as config:
        for k, v in configurations.items():
            config.write(f"{k}={v}")
    return configurations
