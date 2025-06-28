
import os
import socket

def get_hostname():
    return os.environ.get('COMPUTERNAME') or socket.gethostname()