"""
Test script to verify per-state notifications work correctly
"""
import asyncio
import sys
import os

# Add parent directory to path so we can import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the monitor module
from monitor_enhanced import get_stock_for_all_states, comparitor
from playwright.async_api import async_playwright
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

async def test_multistate_notifications():
    """Test that we get stock data for all states and can send per-state notifications"""

    test_url = "https://www.kmart.com.au/product/pokemon-trading-card-game:-mega-evolution-blister-pack-assorted-43648146/"
    test_sku = "43648146"
    test_title = "Pokemon Trading Card Game: Mega Evolution Blister Pack"

    print("Testing Multi-State Notifications")
    print("=" * 60)
    print(f"Test Product: {test_url}")
    print("=" * 60)

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
            print("\n[1] Fetching stock data for all 8 Australian states...")
            all_states_stock = await get_stock_for_all_states(page, test_url, test_sku)

            if not all_states_stock:
                print("[ERROR] No stock data retrieved!")
                return

            print(f"\n[2] Stock data retrieved for {len(all_states_stock)} states:")
            for state, stock_info in all_states_stock.items():
                online = stock_info.get('online', 0)
                instore = stock_info.get('instore', 0)
                print(f"   {state}: Online={online}, In-Store={instore}")

            # Create a mock product object with all_states_stock
            product = {
                'title': test_title,
                'url': test_url,
                'image': 'https://product-images.kmart.com.au/product_images/pokemon-trading-card-game-mega-evolution-blister-pack-assorted-43648146.jpg',
                'sku': test_sku,
                'price': '10.00',
                'all_states_stock': all_states_stock
            }

            # Test comparitor with start=False to trigger notifications
            states_with_stock = sum(1 for s in all_states_stock.values() if s.get('online', 0) > 0 or s.get('instore', 0) > 0)
            print(f"\n[3] Testing comparitor (this will send up to {states_with_stock} Discord notifications)...")
            print("    Each state with stock will get a separate notification!")

            # Call comparitor - this should send separate notifications for each state
            comparitor(product, start=False)

            print("\n[SUCCESS] Test complete!")
            print(f"   - Expected up to {states_with_stock} separate Discord notifications")
            print("   - Each notification should show a different state name")
            print("   - Check your Discord channel to verify!")

        except Exception as e:
            print(f"[ERROR] Error during test: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await context.close()
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_multistate_notifications())
