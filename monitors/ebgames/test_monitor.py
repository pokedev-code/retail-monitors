"""
Test script for EB Games monitor
Tests product scraping from search page
"""
import asyncio
import sys
from playwright.async_api import async_playwright
from monitor import scrape_products, matches_filters, matches_keywords, discord_webhook
import config

async def test_scraping():
    """Test product scraping"""
    print("=" * 80)
    print("Testing EB Games Monitor")
    print("=" * 80)

    print(f"\n[1] Testing scrape from: {config.SEARCH_URL}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        try:
            products = await scrape_products(page)

            if not products:
                print("[ERROR] No products found!")
                return False

            print(f"\n[SUCCESS] Found {len(products)} products after filtering")

            # Show first 3 products
            print("\n[2] Sample products:")
            for i, product in enumerate(products[:3]):
                print(f"\n   Product {i+1}:")
                print(f"      ID: {product['product_id']}")
                print(f"      Title: {product['title']}")
                print(f"      Price: {product['price']}")
                print(f"      Stock: {product['stock_status']}")
                print(f"      URL: {product['url'][:80]}...")

            # Test webhook
            print("\n[3] Testing Discord webhook:")

            if config.WEBHOOK == "YOUR_DISCORD_WEBHOOK_URL_HERE":
                print("   [SKIP] Webhook not configured in config.py")
                print("   Please set your Discord webhook URL to test notifications")
            else:
                if products:
                    test_product = products[0]
                    print(f"   Sending test notification for: {test_product['title']}")
                    discord_webhook(test_product)
                    print("   [SUCCESS] Webhook sent! Check your Discord channel.")
                else:
                    print("   [SKIP] No products to test")

            print("\n" + "=" * 80)
            print("Test Complete!")
            print("=" * 80)

            return True

        except Exception as e:
            print(f"[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            await browser.close()


if __name__ == '__main__':
    success = asyncio.run(test_scraping())
    sys.exit(0 if success else 1)
