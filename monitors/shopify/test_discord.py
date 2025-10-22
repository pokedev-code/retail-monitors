import requests
import json
from datetime import datetime
from config import WEBHOOK, USERNAME, AVATAR_URL, COLOUR, URL

def send_test_notification():
    """
    Sends a test Discord webhook notification
    """
    # Test data
    test_product = {
        'title': 'TEST - Nike Air Jordan 1 Retro High OG',
        'handle': 'nike-air-jordan-1-retro-high-og',
        'image': 'https://raw.githubusercontent.com/yasserqureshi1/Sneaker-Monitors/master/monitors/shopify/logo.png'
    }

    test_sizes = [
        {'title': 'US 8.5', 'url': '[ATC](https://kith.com/cart/12345:1)'},
        {'title': 'US 9', 'url': '[ATC](https://kith.com/cart/12346:1)'},
        {'title': 'US 9.5', 'url': '[ATC](https://kith.com/cart/12347:1)'},
        {'title': 'US 10', 'url': '[ATC](https://kith.com/cart/12348:1)'},
        {'title': 'US 10.5', 'url': '[ATC](https://kith.com/cart/12349:1)'},
    ]

    # Build fields
    fields = []
    for size in test_sizes:
        fields.append({"name": size['title'], "value": size['url'], "inline": True})

    # Build webhook data
    data = {
        "username": USERNAME,
        "avatar_url": AVATAR_URL,
        "embeds": [{
            "title": test_product['title'] + " [TEST NOTIFICATION]",
            "url": URL.replace('.json', '/') + test_product['handle'],
            "thumbnail": {"url": test_product['image']},
            "fields": fields,
            "color": int(COLOUR),
            "footer": {"text": "TEST - Shopify Monitor by GitHub:yasserqureshi1"},
            "timestamp": str(datetime.utcnow()),
        }]
    }

    print("Sending test notification to Discord...")
    result = requests.post(WEBHOOK, data=json.dumps(data), headers={"Content-Type": "application/json"})

    try:
        result.raise_for_status()
        print(f"[SUCCESS] Test notification sent successfully! (Status code: {result.status_code})")
        print(f"Check your Discord channel for the test message.")
    except requests.exceptions.HTTPError as err:
        print(f"[ERROR] Failed to send notification: {err}")
        print(f"Response: {result.text}")

if __name__ == '__main__':
    send_test_notification()
