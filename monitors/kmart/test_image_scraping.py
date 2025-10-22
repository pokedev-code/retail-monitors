"""
Test script to verify image scraping works correctly
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor_enhanced import get_stock_for_all_states
from playwright.async_api import async_playwright
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

async def test_image_scraping():
    """Test that we can extract product images from the page"""

    test_url = "https://www.kmart.com.au/product/pokemon-trading-card-game:-mega-evolution-blister-pack-assorted-43648146/"
    test_sku = "43648146"

    print("Testing Image Scraping")
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
            # Navigate to product page
            print("\n[1] Navigating to product page...")
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)

            # Try to extract image using multiple methods
            print("\n[2] Extracting product image...")

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
                            console.log('Found image via:', sel, elem.content);
                            return elem.content;
                        } else {
                            const url = elem.src || elem.dataset.src || elem.getAttribute('data-src');
                            console.log('Found image via:', sel, url);
                            return url;
                        }
                    }
                }
                return null;
            }''')

            if image_url:
                print(f"   [SUCCESS] Image URL found: {image_url}")
                print(f"   Image is {'VALID' if image_url.startswith('http') else 'INVALID'}")
            else:
                print("   [ERROR] No image URL found!")

            # Also get the title from the page
            title = await page.evaluate('''() => {
                const titleElem = document.querySelector('h1, meta[property="og:title"]');
                if (titleElem) {
                    return titleElem.tagName === 'META' ? titleElem.content : titleElem.textContent.trim();
                }
                return 'Unknown Product';
            }''')

            print(f"\n[3] Product Title: {title}")

        except Exception as e:
            print(f"[ERROR] Error during test: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await context.close()
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_image_scraping())
