"""
Test how many products are in the JSON-LD data
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test_jsonld():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://www.kmart.com.au/category/toys/pokemon-trading-cards/"
        print(f"Loading: {url}\n")

        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_selector('script[type="application/ld+json"]', state='attached', timeout=15000)
        await asyncio.sleep(2)

        # Extract JSON-LD data
        json_ld_data = await page.evaluate('''() => {
            const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
            return scripts.map(s => {
                try {
                    return JSON.parse(s.textContent);
                } catch(e) {
                    return null;
                }
            }).filter(d => d !== null);
        }''')

        print(f"Found {len(json_ld_data)} JSON-LD blocks\n")

        total_items = 0
        for idx, data in enumerate(json_ld_data):
            if isinstance(data, dict) and data.get('@type') == 'ItemList':
                items = data.get('itemListElement', [])
                num_items = data.get('numberOfItems', 0)
                print(f"JSON-LD Block {idx + 1}:")
                print(f"  @type: ItemList")
                print(f"  numberOfItems (metadata): {num_items}")
                print(f"  itemListElement length: {len(items)}")
                print()

                total_items += len(items)

                # Show first and last items
                if items:
                    print(f"  First item: {items[0].get('item', {}).get('name', 'N/A')}")
                    print(f"  Last item: {items[-1].get('item', {}).get('name', 'N/A')}")
                    print()

        print(f"TOTAL ITEMS PARSED: {total_items}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_jsonld())
