"""
Test script to verify state-specific webhooks work correctly
This will send test notifications to different state-specific Discord channels
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor_enhanced import get_stock_for_all_states, discord_webhook
from playwright.async_api import async_playwright
import logging

# Import config to check STATE_WEBHOOKS
from config import STATE_WEBHOOKS, WEBHOOK

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

async def test_state_specific_webhooks():
    """Test that notifications are sent to state-specific webhooks"""

    test_url = "https://www.kmart.com.au/product/pokemon-trading-card-game:-mega-evolution-blister-pack-assorted-43648146/"
    test_sku = "43648146"

    print("Testing State-Specific Webhooks")
    print("=" * 60)
    print(f"Test Product: {test_url}")
    print("=" * 60)

    # Check webhook configuration
    print("\n[1] Checking webhook configuration...")
    configured_states = []
    for state, webhook in STATE_WEBHOOKS.items():
        if webhook and webhook.startswith('https://discord.com/api/webhooks/'):
            configured_states.append(state)
            print(f"   {state}: Configured")
        else:
            print(f"   {state}: Not configured (will use fallback webhook)")

    if not configured_states:
        print("\n   [WARNING] No state-specific webhooks configured!")
        print("   All notifications will use the fallback webhook.")
        print("   To configure state-specific webhooks, edit config.py and update STATE_WEBHOOKS")
    else:
        print(f"\n   {len(configured_states)} state(s) configured with specific webhooks")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        try:
            # Navigate to product page and get image
            print("\n[2] Fetching product data...")
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)

            # Extract image
            image_url = await page.evaluate('''() => {
                const selectors = [
                    'meta[property="og:image"]',
                    'img[class*="ProductImage"]',
                    'img[class*="product-image"]',
                ];

                for (const sel of selectors) {
                    const elem = document.querySelector(sel);
                    if (elem) {
                        if (elem.tagName === 'META') {
                            return elem.content;
                        } else {
                            return elem.src || elem.dataset.src;
                        }
                    }
                }
                return 'https://via.placeholder.com/300x300.png?text=No+Image';
            }''')

            # Extract title
            title = await page.evaluate('''() => {
                const titleElem = document.querySelector('h1, meta[property="og:title"]');
                if (titleElem) {
                    return titleElem.tagName === 'META' ? titleElem.content : titleElem.textContent.trim();
                }
                return 'Test Product';
            }''')

            print(f"   Product: {title}")
            print(f"   Image: {image_url[:80]}...")

            # Get stock for all states
            print("\n[3] Fetching stock data for all states...")
            all_states_stock = await get_stock_for_all_states(page, test_url, test_sku)

            if not all_states_stock:
                print("   [ERROR] Could not fetch stock data")
                return

            print(f"   Retrieved stock data for {len(all_states_stock)} states")

            # Send test notifications - limit to 2 states to avoid spam
            print("\n[4] Sending test notifications...")
            print("    This will send 1 main + 2 state-specific notifications (limited to avoid spam)\n")
            test_states = list(all_states_stock.keys())[:2]

            # First: Send to main unfiltered webhook with combined totals
            total_online = sum(stock.get('online', 0) for stock in all_states_stock.values())
            total_instore = sum(stock.get('instore', 0) for stock in all_states_stock.values())

            combined_stock_info = {
                'online': total_online,
                'instore': total_instore,
                'state': 'All States'
            }

            print(f"   [MAIN] Sending to unfiltered webhook (all states combined)...")
            print(f"      Online: {total_online}, In-Store: {total_instore}")

            discord_webhook(
                title=title,
                url=test_url,
                thumbnail=image_url,
                price="10.00",
                stock_info=combined_stock_info,
                state_name=None  # No state name for main webhook
            )

            print()

            # Then: Send to state-specific webhooks
            for state in test_states:
                stock_info = all_states_stock[state]
                print(f"   [{state}] Sending to state-specific webhook...")
                print(f"      Online: {stock_info.get('online', 0)}, In-Store: {stock_info.get('instore', 0)}")

                discord_webhook(
                    title=title,
                    url=test_url,
                    thumbnail=image_url,
                    price="10.00",
                    stock_info=stock_info,
                    state_name=state
                )

            print("\n[SUCCESS] Test complete!")
            print(f"   - Sent 1 main notification (unfiltered)")
            print(f"   - Sent {len(test_states)} state-specific notifications")
            print("\n   Check your Discord channels:")
            print(f"     * Main unfiltered channel should show combined totals:")
            print(f"       Online: {total_online}, In-Store: {total_instore}")
            for state in test_states:
                if state in configured_states:
                    print(f"     * #{state.lower()} (kmart-{state.lower()}) should have a notification")
                else:
                    print(f"     * {state} notification went to fallback webhook")
            print("\n   Expected notification format:")
            print("     Main webhook: Shows combined stock across all states")
            print("     State webhooks: Shows only that state's stock")
            print("\n   Note: Only tested 2 states to avoid spam.")
            print("   When monitor runs, all 8 states will be checked automatically.")

        except Exception as e:
            print(f"[ERROR] Error during test: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await context.close()
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_state_specific_webhooks())
