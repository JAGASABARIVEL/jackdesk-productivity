
import requests

from constants import ActivewatchApi

def clear_bucket_events(bucket_id, events_to_be_removed):
    try:
        for i in events_to_be_removed:
            url = f"http://127.0.0.1:5600/api/0/buckets/{bucket_id}/events/{i}"
            response = requests.delete(url)
            if response.status_code == 200:
                print(f"Cleared bucket: {bucket_id} event {i}")
    except Exception as e:
        print(f"Error clearing bucket {bucket_id}: {e}")

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

def remove_all_events():
    window_bucket, afk_bucket = get_bucket_ids()
    clear_bucket_events(window_bucket, range(1000, 1083))
    #clear_bucket_events(afk_bucket, range(1, 1000))

remove_all_events()