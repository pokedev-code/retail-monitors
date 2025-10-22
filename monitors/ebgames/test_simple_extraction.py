"""
Simple test to see if basic JavaScript extraction is working
"""
import asyncio
from playwright.async_api import async_playwright

async def test():
    """Test basic extraction"""

    url = "https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards&attributes=franchise%3Apokemon"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        try:
            print("Loading page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)

            print("Testing SIMPLE extraction...")

            # Simple test - just count product tiles
            count = await page.evaluate('''() => {
                return document.querySelectorAll('.product-tile').length;
            }''')

            print(f"Found {count} product tiles")

            # Try to extract just ONE product
            first_product = await page.evaluate('''() => {
                const card = document.querySelector('.product-tile');
                if (!card) return null;

                const link = card.querySelector('a[href]');
                const url = link ? link.href : '';

                // Try h3
                const h3 = card.querySelector('h3');
                const title = h3 ? h3.textContent.trim() : 'NO TITLE';

                return {title, url};
            }''')

            print(f"\nFirst product: {first_product}")

            await browser.close()

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test())
