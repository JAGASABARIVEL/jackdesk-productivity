import requests
from google_auth_oauthlib.flow import InstalledAppFlow

from constants import JckdeskApi

CLIENT_SECRETS_FILE = "client_secret.json"  # Download from Google Console
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email']


def login_and_get_app_token():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    id_token = credentials.id_token

    # Send to your Django backend to validate
    response = requests.post(JckdeskApi.LOGIN, json={"token": id_token})

    if response.status_code == 200:
        result = response.json()
        token = result.get("access")
        email = result.get("user").get("email")
        return email, token
    else:
        print(response.text)
        raise Exception("Login failed: " + response.text)
