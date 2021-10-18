import hashlib
import hmac
import json
import os
import requests
import sys

TWITCH_SECRET = os.getenv('TWITCH_SECRET')

body = json.load(open(sys.argv[1], 'r'))
headers = {
    "Twitch-Eventsub-Message-Id": "befa7b53-d79d-478f-86b9-120f112b044e",
    "Twitch-Eventsub-Message-Timestamp": "2019-11-16T10:11:12.123Z",
}

message_id = headers.get('Twitch-Eventsub-Message-Id')
message_timestamp = headers.get('Twitch-Eventsub-Message-Timestamp')
hmac_message = message_id + message_timestamp + json.dumps(body)
signature = hmac.new(TWITCH_SECRET.encode(),
                     hmac_message.encode(), hashlib.sha256)
expected_signature_header = 'sha256=' + signature.hexdigest()

headers["Twitch-Eventsub-Message-Signature"] = expected_signature_header

requests.post("http://localhost:5000/", headers=headers, json=body)
