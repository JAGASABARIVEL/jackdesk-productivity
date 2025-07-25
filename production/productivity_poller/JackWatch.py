import requests
import time
import os
import sys
import subprocess
import threading
from datetime import datetime, timedelta

from constants import ActivewatchApi, JckdeskApi
from registration import unregister_device_from_server
from util import get_hostname, get_credentials_from_server

CACHE_FILE = "aw_status.flag"
SYNC_PERIOD = 60  # 10 minute - TODO
HOST_VALIDATION_PERIOD = 30
LOGIN_TIME_WAIT = 300 # 30 minutes - TODO
CACHED_CREDS = {"email": None, "token": None}

LAST_ID_FILES = {
    "window": "last_event_id_window.txt",
    "afk": "last_event_id_afk.txt"
}

AW_SERVICES = ["ActivityWatchServer", "aw-watcher-afk", "aw-watcher-window"]


# ─── Utility Functions ───────────────────────────────────────────────────────────

def is_login_already_open():
    return "Jackdesk Productivity" in subprocess.getoutput('tasklist')


login_processes = []  # global list to track PyQt subprocesses

def launch_login_window():
    if not is_login_already_open():
        pyqt_path = os.path.join(os.path.dirname(__file__), "client.py")
        proc = subprocess.Popen([sys.executable, pyqt_path])
        login_processes.append(proc)

def close_last_login_window():
    if login_processes:
        proc = login_processes.pop()
        if proc.poll() is None:  # still running
            proc.terminate()
            print(f"Terminated login window with PID: {proc.pid}")





def is_aw_stopped():
    return os.path.exists(CACHE_FILE)


def set_aw_stopped(flag: bool):
    if flag:
        with open(CACHE_FILE, "w") as f:
            f.write("stopped")
    else:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)


def start_activitywatch_services():
    for service in AW_SERVICES:
        subprocess.run(["sc", "start", service], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    set_aw_stopped(False)
    print(f"[{datetime.now()}] ActivityWatch services started.")


def stop_activitywatch_services():
    for service in AW_SERVICES:
        subprocess.run(["sc", "stop", service], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    set_aw_stopped(True)
    print(f"[{datetime.now()}] ActivityWatch services stopped.")


# ─── Event ID Storage ────────────────────────────────────────────────────────────

def get_last_synced_event_id(bucket_type):
    file_path = LAST_ID_FILES.get(bucket_type)
    try:
        with open(file_path, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return -1


def set_last_synced_event_id(bucket_type, last_event_id):
    file_path = LAST_ID_FILES.get(bucket_type)
    with open(file_path, "w") as f:
        f.write(str(last_event_id))


# ─── ActivityWatch Fetching ──────────────────────────────────────────────────────

def get_bucket_ids():
    try:
        response = requests.get(ActivewatchApi.LIST_BUCKETS)
        response.raise_for_status()
        all_buckets = response.json()
        window_bucket = next((b["id"] for k, b in all_buckets.items() if k.startswith("aw-watcher-window_")), None)
        afk_bucket = next((b["id"] for k, b in all_buckets.items() if k.startswith("aw-watcher-afk_")), None)
        return window_bucket, afk_bucket
    except Exception as e:
        print("Error fetching bucket IDs:", e)
        return None, None


def fetch_events(bucket_id, start, end):
    try:
        url = ActivewatchApi.GET_EVENTS.format(bucket_id=bucket_id, start=start, end=end)
        return requests.get(url).json()
    except Exception as e:
        print(f"Failed to fetch events from {bucket_id}:", e)
        return []


def filter_events_by_last_id(events, last_id, include_last_sent_event=False):
    if include_last_sent_event:
        return [event for event in events if event.get("id", -1) >= last_id]  # ✅ include last ID
    return [event for event in events if event.get("id", -1) > last_id]

# ─── Core Logic ──────────────────────────────────────────────────────────────────

start_monitor_level = -1
start_sync_level = -1
def sync_loop():
    global start_sync_level, start_monitor_level
    print("Starting sync loop...")
    while True:
        start_sync_level += 1
        try:
            creds = get_credentials_from_server()
            if not creds or not creds.get("token") or not creds.get("email"):
                print(f"[{datetime.now()}] No valid credentials; skipping sync.")
                close_last_login_window()
                launch_login_window()
                try:
                    time.sleep(LOGIN_TIME_WAIT)
                except KeyboardInterrupt as e:
                    close_last_login_window()
                    raise e
                continue
            email = creds["email"]
            token = creds["token"]
            CACHED_CREDS["email"] = email
            CACHED_CREDS["token"] = token
            # Unregistering after caching the credentials and 1st time the script starts or after user logs in to the system
            if start_sync_level == 0:
                unregister_device_from_server(email, token, get_hostname())
            else:
                # Skip(continue in line 136) unregistration, if the user is already logged into other system and we would get fresh login
                print("Skipping unregistration")
            window_bucket, afk_bucket = get_bucket_ids()
            if not window_bucket or not afk_bucket:
                print("Missing bucket IDs.")
                time.sleep(60)
                continue
            now = datetime.utcnow()
            start = (now - timedelta(hours=12)).isoformat() + "Z"
            end = now.isoformat() + "Z"
            all_window_events = fetch_events(window_bucket, start, end)
            all_afk_events = fetch_events(afk_bucket, start, end)
            last_window_id = get_last_synced_event_id("window")
            last_afk_id = get_last_synced_event_id("afk")
            window_events = sorted(
                filter_events_by_last_id(all_window_events, last_window_id, True),
                key=lambda e: e["id"]
            )
            afk_events = sorted(
                filter_events_by_last_id(all_afk_events, last_afk_id),
                key=lambda e: e["id"]
            )
            payload = {
                "email": email,
                "system": get_hostname(),
                "window_events": window_events,
                "afk_events": afk_events
            }
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            response = requests.post(JckdeskApi.SYNC, json=payload, headers=headers)
            if response.status_code == 401:
                close_last_login_window()
                launch_login_window()
                try:
                    time.sleep(LOGIN_TIME_WAIT)
                except KeyboardInterrupt as e:
                    close_last_login_window()
                    raise e
                continue
            elif response.status_code != 200:
                print(f"[{datetime.now()}] Error syncing: {response.status_code} - {response.text}")
            else:
                print(f"[{datetime.now()}] Synced {len(window_events)} window, {len(afk_events)} afk events.")
                if window_events:
                    max_win_id = max(e["id"] for e in window_events)
                    set_last_synced_event_id("window", max_win_id)
                if afk_events:
                    max_afk_id = max(e["id"] for e in afk_events)
                    set_last_synced_event_id("afk", max_afk_id)
        except Exception as e:
            print(f"Sync exception: {e}")
            close_last_login_window()
        if start_monitor_level == -1:
            threading.Thread(target=monitor_aw_state, daemon=True).start()
            start_monitor_level += 1
        time.sleep(SYNC_PERIOD)


def sync__flush():
    print("Flushing sync...")
    email = CACHED_CREDS["email"]
    token = CACHED_CREDS["token"]
    CACHED_CREDS["email"] = None
    CACHED_CREDS["token"] = None
    window_bucket, afk_bucket = get_bucket_ids()
    if not window_bucket or not afk_bucket:
        print("Missing bucket IDs.")
        return
    now = datetime.utcnow()
    start = (now - timedelta(hours=12)).isoformat() + "Z"
    end = now.isoformat() + "Z"
    all_window_events = fetch_events(window_bucket, start, end)
    all_afk_events = fetch_events(afk_bucket, start, end)
    last_window_id = get_last_synced_event_id("window")
    last_afk_id = get_last_synced_event_id("afk")
    window_events = sorted(
        filter_events_by_last_id(all_window_events, last_window_id, True),
        key=lambda e: e["id"]
    )
    afk_events = sorted(
        filter_events_by_last_id(all_afk_events, last_afk_id),
        key=lambda e: e["id"]
    )
    payload = {
        "email": email,
        "system": get_hostname(),
        "window_events": window_events,
        "afk_events": afk_events
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Even if the sync fails we would reset the last syn id since the new user would not
    # get accounted as this function gets called only when the user changes the system
    if window_events:
        max_win_id = max(e["id"] for e in window_events)
        set_last_synced_event_id("window", max_win_id)
    if afk_events:
        max_afk_id = max(e["id"] for e in afk_events)
        set_last_synced_event_id("afk", max_afk_id)
    response = requests.post(JckdeskApi.SYNC, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"[{datetime.now()}] Error syncing: {response.status_code} - {response.text}")
    else:
        print(f"[{datetime.now()}] Synced {len(window_events)} window, {len(afk_events)} afk events.")


def monitor_aw_state():
    print("Starting AW monitoring thread...")
    while True:
        try:
            creds = get_credentials_from_server()
            active = bool(creds and creds.get("token") and creds.get("email"))
            if active and is_aw_stopped():
                print(f"[{datetime.now()}] Detected valid creds. Restarting AW...")
                # start_activitywatch_services()
            elif not active and not is_aw_stopped():
                if CACHED_CREDS["token"]:
                    print(f"[{datetime.now()}] Flushing unsynced events...")
                    sync__flush()
                print(f"[{datetime.now()}] No valid creds. Stopping AW...")
                # stop_activitywatch_services()
                close_last_login_window()
                launch_login_window()
                try:
                    time.sleep(LOGIN_TIME_WAIT)
                except KeyboardInterrupt as e:
                    close_last_login_window()
                    raise e
        except Exception as e:
            print(f"[Monitor] Exception: {e}")
        time.sleep(HOST_VALIDATION_PERIOD)


if __name__ == "__main__":
    sync_loop()
