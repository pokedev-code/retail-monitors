"""
Script to explore Big W's API structure
Based on network analysis, Big W uses Adobe AEM backend
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def explore_bigw_api():
    """Explore Big W's category page to find product listing API"""

    url = "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        # Capture API responses
        api_responses = []
        product_api_response = None

        async def capture_response(response):
            nonlocal product_api_response
            url = response.url

            # Look for product/category API calls
            if any(keyword in url for keyword in ['product', 'category', 'search', 'api', '.json']):
                if '/product' not in response.request.resource_type:  # Avoid JS/CSS files
                    try:
                        if 'json' in response.headers.get('content-type', ''):
                            data = await response.json()
                            api_responses.append({
                                'url': url,
                                'status': response.status,
                                'data_sample': str(data)[:500]
                            })

                            # If it looks like a product listing response
                            if isinstance(data, dict) and ('products' in data or 'items' in data or 'results' in data):
                                product_api_response = {
                                    'url': url,
                                    'data': data
                                }
                                print(f"[FOUND] Product API: {url}")

                    except:
                        pass

        page.on('response', capture_response)

        print("=" * 80)
        print("Exploring Big W API")
        print("=" * 80)

        try:
            print("\n[1] Loading page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)

            # Wait for products to load
            await asyncio.sleep(10)

            print("\n[2] Analyzing page content...")

            # Try to extract product data from page
            products = await page.evaluate('''() => {
                const productElements = document.querySelectorAll('[data-testid*="product"], [class*="Product"]');
                const products = [];

                for (let i = 0; i < Math.min(5, productElements.length); i++) {
                    const el = productElements[i];
                    const title = el.querySelector('[data-testid*="title"], h2, h3')?.textContent?.trim();
                    const price = el.querySelector('[data-testid*="price"], [class*="price"]')?.textContent?.trim();
                    const link = el.querySelector('a')?.href;

                    if (title) {
                        products.push({ title, price, link });
                    }
                }

                return products;
            }''')

            if products:
                print(f"\n   Found {len(products)} products on page:")
                for i, p in enumerate(products[:3]):
                    print(f"   {i+1}. {p['title'][:60]} - {p['price']}")

            # Check __NEXT_DATA__ (Next.js data)
            next_data = await page.evaluate('''() => {
                const scriptEl = document.getElementById('__NEXT_DATA__');
                if (scriptEl) {
                    try {
                        return JSON.parse(scriptEl.textContent);
                    } catch (e) {
                        return null;
                    }
                }
                return null;
            }''')

            if next_data:
                print("\n[3] Found Next.js data object!")
                print(f"   Keys: {list(next_data.keys()) if isinstance(next_data, dict) else 'N/A'}")

                # Save Next.js data
                with open('monitors/bigw/next_data.json', 'w') as f:
                    json.dump(next_data, f, indent=2)
                print("   Saved to: monitors/bigw/next_data.json")

            if product_api_response:
                print("\n[4] Product API Response Found!")
                print(f"   URL: {product_api_response['url']}")

                with open('monitors/bigw/product_api_response.json', 'w') as f:
                    json.dump(product_api_response, f, indent=2)
                print("   Saved to: monitors/bigw/product_api_response.json")

            print("\n[5] All API Responses:")
            for i, resp in enumerate(api_responses):
                print(f"\n   {i+1}. {resp['url']}")
                print(f"      Status: {resp['status']}")
                print(f"      Sample: {resp['data_sample'][:100]}...")

            with open('monitors/bigw/api_responses.json', 'w') as f:
                json.dump(api_responses, f, indent=2)

            print("\n[SUCCESS] Exploration complete!")
            print("   Check monitors/bigw/ for saved JSON files")

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(explore_bigw_api())
