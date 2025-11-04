"""
Test Discord notification with new emoji format
"""
import requests
import json

# Use your main webhook
WEBHOOK_URL = "https://discord.com/api/webhooks/1429181362169974848/h44prs1hsqDyvq9HRh1Qi0eZIsFJsUaLZnfrTYWDOZuRhxh64BRCQCavBu_hDgUcN4bh"

# Create a test notification with the new format
embed = {
    "title": "TEST: Pokemon Trading Card Game Booster Pack",
    "url": "https://www.target.com.au/p/pokemon-tcg-test/12345678",
    "description": "This is a test notification showing the new format",
    "color": 16711680,  # Red (Target brand color)
    "thumbnail": {
        "url": "https://upload.wikimedia.org/wikipedia/en/3/3b/Pokemon_Trading_Card_Game_cardback.jpg"
    },
    "fields": [
        {
            "name": "Price",
            "value": "$25.00",
            "inline": True
        },
        {
            "name": "Product ID",
            "value": "12345678",
            "inline": True
        },
        {
            "name": "Delivery Options",
            "value": "\U0001F7E2 Home Delivery\n\U0001F534 Click & Collect",
            "inline": True
        },
        {
            "name": "Stores with Stock (NSW)",
            "value": "Subiaco, Ararat, Yass (3 stores)",
            "inline": False
        }
    ],
    "footer": {
        "text": "TEST NOTIFICATION - New format with green/red circles"
    }
}

payload = {
    "username": "Target AU",
    "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Target_logo.svg/1200px-Target_logo.svg.png",
    "embeds": [embed]
}

print("Sending test notification to Discord...")
print(f"Webhook URL: ...{WEBHOOK_URL[-20:]}")
print()

try:
    response = requests.post(WEBHOOK_URL, json=payload)

    if response.status_code == 204:
        print("[SUCCESS] Test notification sent to Discord!")
        print()
        print("Check your Discord channel to see:")
        print("  - Green circle for Home Delivery (in stock)")
        print("  - Red circle for Click & Collect (out of stock)")
        print("  - No Express Delivery option")
        print()
    else:
        print(f"[ERROR] Status code: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"[ERROR] Exception: {e}")
