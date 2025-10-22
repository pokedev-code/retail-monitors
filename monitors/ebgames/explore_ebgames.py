"""
Explore EB Games website structure
"""
import asyncio
from playwright.async_api import async_playwright
import json
import re

async def explore_ebgames():
    """Explore EB Games product page structure"""

    product_url = "https://www.ebgames.com.au/product/toys-and-collectibles/334666-pokemon-tcg-dec-25-collectors-chest"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        print("=" * 80)
        print("Exploring EB Games Product Page")
        print("=" * 80)
        print(f"URL: {product_url}")
        print("=" * 80)

        try:
            print("\n[1] Loading page...")
            await page.goto(product_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)

            print("\n[2] Checking for __NEXT_DATA__...")
            next_data = await page.evaluate('''() => {
                const script = document.querySelector('script#__NEXT_DATA__');
                return script ? script.textContent : null;
            }''')

            if next_data:
                print("   Found __NEXT_DATA__!")
                data = json.loads(next_data)
                with open('monitors/ebgames/next_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                print("   Saved to: monitors/ebgames/next_data.json")

                # Try to find product data
                print("\n[3] Looking for product data in __NEXT_DATA__...")
                if 'props' in data and 'pageProps' in data['props']:
                    props = data['props']['pageProps']
                    print(f"   pageProps keys: {list(props.keys())}")
            else:
                print("   No __NEXT_DATA__ found")

            print("\n[4] Checking for JSON-LD...")
            json_ld = await page.evaluate('''() => {
                const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                return scripts.map(s => s.textContent);
            }''')

            if json_ld:
                print(f"   Found {len(json_ld)} JSON-LD scripts")
                for i, ld in enumerate(json_ld):
                    try:
                        data = json.loads(ld)
                        if data.get('@type') == 'Product':
                            print(f"   Script {i+1}: Product schema found!")
                            print(f"      Keys: {list(data.keys())}")
                    except:
                        pass

            print("\n[5] Extracting product info from page...")
            product_info = await page.evaluate('''() => {
                return {
                    title: document.title,
                    h1: document.querySelector('h1')?.textContent,
                    price: document.querySelector('[class*="price"]')?.textContent,
                    stock: document.querySelector('[class*="stock"]')?.textContent,
                    imageUrl: document.querySelector('img[class*="product"]')?.src,
                    allMeta: Array.from(document.querySelectorAll('meta[property]')).map(m => ({
                        property: m.getAttribute('property'),
                        content: m.content
                    }))
                };
            }''')

            print(f"   Title: {product_info['title']}")
            print(f"   H1: {product_info['h1']}")
            print(f"   Price: {product_info['price']}")
            print(f"   Stock: {product_info['stock']}")
            print(f"   Image: {product_info['imageUrl'][:80] if product_info['imageUrl'] else 'None'}...")

            print("\n[6] Keeping browser open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(explore_ebgames())
