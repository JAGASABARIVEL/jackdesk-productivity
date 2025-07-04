import requests
from constants import CentralServerApi  # e.g., CENTRAL_REGISTER = http://yourapi/register_device/

def register_device_with_server(email, token, hostname, custom_config_path=None):
    try:
        CentralServerApi.refresh_config(custom_config_path)
        response = requests.post(
            CentralServerApi.REGISTER,
            json={"email": email, "token": token, "hostname": hostname},
            timeout=10
        )
        if response.status_code == 200:
            return True
        print(f"Register failed: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print("Error sending device registration:", e)
        return False


def unregister_device_from_server(email, token, hostname, custom_config_path=None):
    try:
        print("CentralServerApi.UNREGISTER ", CentralServerApi.UNREGISTER)
        CentralServerApi.refresh_config(custom_config_path)
        response = requests.delete(
            CentralServerApi.UNREGISTER,
            json={"email": email, "token": token, "hostname": hostname},
            timeout=10
        )
        if response.status_code == 200:
            return True
        print(f"Register failed: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print("Error sending device registration:", e)
        return False
