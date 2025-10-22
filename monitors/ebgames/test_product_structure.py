"""
Test to see the actual structure of a product tile
"""
import asyncio
from playwright.async_api import async_playwright

async def test():
    """Test product structure"""

    url = "https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards&attributes=franchise%3Apokemon"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # visible

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
            await asyncio.sleep(5)  # Wait longer for dynamic content

            print("Getting first product tile HTML...")

            html = await page.evaluate('''() => {
                const card = document.querySelector('.product-tile');
                return card ? card.innerHTML : 'NO CARD';
            }''')

            print("\n" + "="*80)
            print("FIRST PRODUCT TILE HTML:")
            print("="*80)
            print(html[:2000])  # First 2000 chars
            print("="*80)

            # Also try to find ALL text in the card
            all_text = await page.evaluate('''() => {
                const card = document.querySelector('.product-tile');
                return card ? card.innerText : 'NO CARD';
            }''')

            print("\nALL TEXT IN CARD:")
            print("="*80)
            print(all_text)
            print("="*80)

            print("\nWaiting 20 seconds for inspection...")
            await asyncio.sleep(20)

            await browser.close()

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test())
