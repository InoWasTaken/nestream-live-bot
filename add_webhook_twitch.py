import os
import requests
import sys

TWITCH_SECRET = os.getenv('TWITCH_SECRET')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_TOKEN = os.getenv('TWITCH_TOKEN')
TWITCH_HEADERS = {
    "Client-ID": TWITCH_CLIENT_ID,
    "Authorization": f"Bearer {TWITCH_TOKEN}",
    "Content-Type": "application/json"
}
TWITCH_URL = "https://api.twitch.tv/helix/eventsub"
NESTREAM_URL = "https://raid.nestream.fr/api/user_list"
CALLBACK_URL = sys.argv[1]


def list_broadcasters():
    res = requests.get(url=NESTREAM_URL)
    broadcasters = res.json()
    if broadcasters["success"] is False:
        return None
    return broadcasters["data"]


def remove_subscription(sub_id):
    requests.delete(f"{TWITCH_URL}/subscriptions?id={sub_id}",
                    headers=TWITCH_HEADERS)


def list_subscriptions():
    r = requests.get(f"{TWITCH_URL}/subscriptions",
                     headers=TWITCH_HEADERS).json()
    return r["data"], r["total"]


def add_subscription(broad_id):
    body = {
        "type": "stream.online",
        "version": "1",
        "condition": {
            "broadcaster_user_id": broad_id
        },
        "transport": {
            "method": "webhook",
            "callback": CALLBACK_URL,
            "secret": TWITCH_SECRET
        }
    }
    req = requests.post(f"{TWITCH_URL}/subscriptions",
                        headers=TWITCH_HEADERS, json=body)
    return req.status_code


def update_subscription_callback(sub_id, broad_id):
    remove_subscription(sub_id)
    return add_subscription(broad_id)


def handle_new_sub(status, name):
    if status == 202:
        print("Subscription request done for", name)
    elif status == 409:
        print("Subscription request already done for", name)
    else:
        print(f"Error in subscription request for {name}: {status}")


subscriptions, total_subs = list_subscriptions()
broadcasters = list_broadcasters()
if broadcasters is None:
    exit(1)

for broadcaster in broadcasters:
    broad_id = broadcaster["id"]
    subscription = next(
        (sub for sub in subscriptions if sub["condition"]["broadcaster_user_id"] == broad_id), False)
    if subscription is False:
        status = add_subscription(broad_id)
        handle_new_sub(status, broadcaster["name"])
        continue
    if subscription["status"] != 'enabled' or CALLBACK_URL != subscription["transport"]["callback"]:
        update_subscription_callback(subscription["id"], broad_id)
        print(f"Subscription recreated for {broadcaster['name']}")
        continue
    print(f"Nothing to do for {broadcaster['name']}")

if len(broadcasters) != total_subs:
    for subscription in subscriptions:
        broad_id = subscription["condition"]["broadcaster_user_id"]
        broadcaster = next(
            (b for b in broadcasters if b["id"] == broad_id), False)
        if broadcaster is False:
            remove_subscription(subscription["id"])
            print(f"Subscription deleted for {broadcaster['name']}")
