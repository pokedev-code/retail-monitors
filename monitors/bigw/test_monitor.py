"""
Test script for Big W monitor
Tests product scraping and Discord notification
"""
import asyncio
import sys
from monitor import scrape_products_requests, discord_webhook, matches_filters, matches_keywords
import config

def test_scraping():
    """Test product scraping"""
    print("=" * 80)
    print("Testing Big W Monitor")
    print("=" * 80)

    print(f"\n[1] Testing scrape from: {config.CATEGORY_URL}")

    products = scrape_products_requests()

    if not products:
        print("[ERROR] No products found!")
        return False

    print(f"\n[SUCCESS] Found {len(products)} in-stock products")

    # Show first 3 products
    print("\n[2] Sample products:")
    for i, product in enumerate(products[:3]):
        print(f"\n   Product {i+1}:")
        print(f"      Code: {product['code']}")
        print(f"      Title: {product['title']}")
        print(f"      Brand: {product['brand']}")
        print(f"      Price: {product['price']}")
        print(f"      URL: {product['url'][:80]}...")

    # Test filters
    print("\n[3] Testing filters:")
    filtered_products = [p for p in products if matches_filters(p['title']) and matches_keywords(p['title'])]
    print(f"   Total products: {len(products)}")
    print(f"   After filters: {len(filtered_products)}")

    if config.INCLUDE_KEYWORDS:
        print(f"   Include keywords: {config.INCLUDE_KEYWORDS[:5]}...")
    if config.EXCLUDE_KEYWORDS:
        print(f"   Exclude keywords: {config.EXCLUDE_KEYWORDS[:5]}...")

    # Test webhook
    print("\n[4] Testing Discord webhook:")

    if config.WEBHOOK == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("   [SKIP] Webhook not configured in config.py")
        print("   Please set your Discord webhook URL to test notifications")
    else:
        if filtered_products:
            test_product = filtered_products[0]
            print(f"   Sending test notification for: {test_product['title']}")
            discord_webhook(test_product)
            print("   [SUCCESS] Webhook sent! Check your Discord channel.")
        else:
            print("   [SKIP] No products match filters")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)

    return True


if __name__ == '__main__':
    success = test_scraping()
    sys.exit(0 if success else 1)
