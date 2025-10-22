"""
Test script to send a single notification with image to verify Discord display
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor_enhanced import get_stock_for_all_states, discord_webhook
from playwright.async_api import async_playwright
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

async def test_single_notification_with_image():
    """Send a single test notification with image for VIC only"""

    test_url = "https://www.kmart.com.au/product/pokemon-trading-card-game:-mega-evolution-blister-pack-assorted-43648146/"
    test_sku = "43648146"

    print("Testing Single Notification with Image")
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
            print("\n[1] Navigating to product page...")
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)

            # Extract image
            print("[2] Extracting product image...")
            image_url = await page.evaluate('''() => {
                const selectors = [
                    'meta[property="og:image"]',
                    'img[class*="ProductImage"]',
                    'img[class*="product-image"]',
                    'img[data-testid*="product"]',
                    '.product-image img',
                    'picture img'
                ];

                for (const sel of selectors) {
                    const elem = document.querySelector(sel);
                    if (elem) {
                        if (elem.tagName === 'META') {
                            return elem.content;
                        } else {
                            return elem.src || elem.dataset.src || elem.getAttribute('data-src');
                        }
                    }
                }
                return null;
            }''')

            if not image_url:
                print("   [WARNING] No image found, using placeholder")
                image_url = "https://via.placeholder.com/300x300.png?text=No+Image"
            else:
                print(f"   [SUCCESS] Image URL: {image_url}")

            # Extract title
            title = await page.evaluate('''() => {
                const titleElem = document.querySelector('h1, meta[property="og:title"]');
                if (titleElem) {
                    return titleElem.tagName === 'META' ? titleElem.content : titleElem.textContent.trim();
                }
                return 'Unknown Product';
            }''')

            print(f"\n[3] Product Title: {title}")

            # Get stock for VIC only
            print("\n[4] Fetching stock data for VIC...")
            all_states_stock = await get_stock_for_all_states(page, test_url, test_sku)

            if 'VIC' in all_states_stock:
                vic_stock = all_states_stock['VIC']
                print(f"   VIC Stock: Online={vic_stock.get('online', 0)}, In-Store={vic_stock.get('instore', 0)}")

                # Send notification for VIC only
                print("\n[5] Sending Discord notification...")
                discord_webhook(
                    title=title,
                    url=test_url,
                    thumbnail=image_url,
                    price="10.00",
                    stock_info=vic_stock,
                    state_name="VIC"
                )

                print("\n[SUCCESS] Notification sent!")
                print("   Check your Discord channel to verify:")
                print("   - Product image appears in the top-right corner")
                print("   - Image is clear and high quality")
                print("   - State shows 'VIC'")
                print("   - Stock levels are displayed correctly")
            else:
                print("   [ERROR] No VIC stock data available")

        except Exception as e:
            print(f"[ERROR] Error during test: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await context.close()
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_single_notification_with_image())
