"""
Debug script to see exactly what's being scraped from Kmart
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def debug_scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Show browser
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
            timezone_id='Australia/Sydney',
            extra_http_headers={
                'Accept-Language': 'en-AU,en-US;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
        )

        page = await context.new_page()

        url = "https://www.kmart.com.au/category/toys/pokemon-trading-cards/"
        print(f"\n[1] Loading URL: {url}\n")

        await page.goto(url, wait_until='domcontentloaded', timeout=30000)

        print("[2] Waiting for selectors...\n")
        try:
            await page.wait_for_selector('script[type="application/ld+json"], a[href*="/product/"]', timeout=15000)
            print("✅ Selector found!\n")
        except Exception as e:
            print(f"❌ Selector timeout: {e}\n")

        await asyncio.sleep(3)

        print("[3] Extracting JSON-LD data...\n")

        # Extract JSON-LD (same as monitor)
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

        items = []
        for idx, data in enumerate(json_ld_data):
            print(f"\n--- JSON-LD Block {idx + 1} ---")
            print(f"Type: {data.get('@type')}")

            if isinstance(data, dict) and data.get('@type') == 'ItemList':
                products = data.get('itemListElement', [])
                print(f"ItemList found with {len(products)} products\n")

                for i, product in enumerate(products[:3]):  # Show first 3
                    if product.get('@type') == 'ListItem':
                        item_data = product.get('item', {})

                        title = item_data.get('name', '')
                        url = item_data.get('url', '')
                        image = item_data.get('image', '')

                        # Extract product ID from URL
                        product_id = None
                        if url:
                            import re
                            match = re.search(r'-(\d+)/?$', url)
                            if match:
                                product_id = match.group(1)

                        print(f"  Product {i+1}:")
                        print(f"    Title: {title}")
                        print(f"    ID: {product_id}")
                        print(f"    URL: {url}")
                        print(f"    Image: {image[:80]}..." if image else "    Image: None")
                        print()

                        if title and url and product_id:
                            items.append({
                                'title': title,
                                'url': url,
                                'image': image,
                                'product_id': product_id,
                                'position': product.get('position')
                            })

        print(f"\n[4] TOTAL ITEMS PARSED: {len(items)}\n")

        # Test keyword filter
        KEYWORDS = ['pokemon', 'card', 'TCG', 'pokemon TCG']
        print(f"[5] Testing keyword filter: {KEYWORDS}\n")

        matched = 0
        for product in items[:5]:  # Test first 5
            title_lower = product['title'].lower()
            matches = []
            for key in KEYWORDS:
                if key.lower() in title_lower:
                    matches.append(key)

            if matches:
                matched += 1
                print(f"  ✅ MATCH: '{product['title']}' -> matched: {matches}")
            else:
                print(f"  ❌ NO MATCH: '{product['title']}'")

        print(f"\n{matched}/{len(items[:5])} products matched keywords\n")

        print("\nBrowser will stay open for 10 seconds...")
        await asyncio.sleep(10)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_scrape())
