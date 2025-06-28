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
    REGISTER = "http://localhost:8000/productivity/register"
    TOKEN = "http://localhost:8000/productivity/token?hostname={hostname}"
