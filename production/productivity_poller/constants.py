import os

CONFIG_FILE = 'app.config'

def load_config():
    configurations = {}
    config_file = os.path.join(os.path.dirname(__file__), CONFIG_FILE)
    with open(config_file, 'r') as config:
        for config_line in config.readlines():
            print("config_line ", config_line, config_line.split('='))
            config_pair = config_line.split('=')
            configurations.update({config_pair[0]: config_pair[1]})
    return configurations

configurations = load_config()


class JckdeskApi:
    LOGIN = "https://api.jackdesk.com/users/login/google"
    SYNC = "https://api.jackdesk.com/productivity/sync"
    #LOGIN = "http://localhost:8000/users/login/google"
    #SYNC = "http://localhost:8000/productivity/sync"

############# Activewatch APIs ##############
class ActivewatchApi:
    LIST_BUCKETS = "http://localhost:5600/api/0/buckets"
    GET_EVENTS = "http://localhost:5600/api/0/buckets/{bucket_id}/events?start={start}&end={end}"

class CentralServerApi:
    CENTRAL_SERVER_IP_KEY = "CENTRAL_SERVER_IP"
    CENTRAL_SERVER_IP = configurations[CENTRAL_SERVER_IP_KEY]
    REGISTER = f"http://{CENTRAL_SERVER_IP}:8000/productivity/register"
    UNREGISTER = f"http://{CENTRAL_SERVER_IP}:8000/productivity/unregister"
    TOKEN = f"http://{CENTRAL_SERVER_IP}:8000/productivity/token?"+"hostname={hostname}"

    @classmethod
    def reload(cls):
        global configurations
        configurations = load_config()
        CENTRAL_SERVER_IP = configurations[CentralServerApi.CENTRAL_SERVER_IP_KEY]
        CentralServerApi.REGISTER = f"http://{CENTRAL_SERVER_IP}:8000/productivity/register"
        CentralServerApi.UNREGISTER = f"http://{CENTRAL_SERVER_IP}:8000/productivity/unregister"
        CentralServerApi.TOKEN = f"http://{CENTRAL_SERVER_IP}:8000/productivity/token?"+"hostname={hostname}"
