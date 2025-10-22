"""
Discover Big W product APIs by monitoring network requests
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def discover_product_apis():
    """Monitor all API calls when loading a product page"""

    product_url = "https://www.bigw.com.au/product/pokemon-tcg-triple-whammy-tin/p/6047808"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        # Capture all requests and responses
        api_calls = []

        async def log_request(request):
            url = request.url
            if any(keyword in url for keyword in ['api', 'graphql', 'product', 'stock', 'price', 'inventory', 'availability']):
                api_calls.append({
                    'type': 'request',
                    'method': request.method,
                    'url': url,
                    'headers': dict(request.headers),
                    'post_data': request.post_data
                })
                print(f"[REQUEST] {request.method} {url}")

        async def log_response(response):
            url = response.url
            if any(keyword in url for keyword in ['api', 'graphql', 'product', 'stock', 'price', 'inventory', 'availability']):
                try:
                    if 'json' in response.headers.get('content-type', ''):
                        data = await response.json()
                        api_calls.append({
                            'type': 'response',
                            'url': url,
                            'status': response.status,
                            'data': data
                        })
                        print(f"[RESPONSE] {response.status} {url}")
                        print(f"   Data keys: {list(data.keys()) if isinstance(data, dict) else 'List/Other'}")
                except:
                    pass

        page.on('request', log_request)
        page.on('response', log_response)

        print("=" * 80)
        print("Discovering Big W Product APIs")
        print("=" * 80)
        print(f"Product URL: {product_url}")
        print("=" * 80)

        try:
            print("\n[1] Loading product page...")
            await page.goto(product_url, wait_until='networkidle', timeout=60000)

            print("\n[2] Waiting for additional requests...")
            await asyncio.sleep(10)

            # Try to trigger stock/price checks by scrolling
            print("\n[3] Scrolling page to trigger lazy-loaded APIs...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(5)

            # Try clicking on elements that might trigger API calls
            print("\n[4] Looking for interactive elements...")

            # Try to find and click "Check stock" or similar buttons
            stock_button = await page.query_selector('button:has-text("Check"), button:has-text("Stock"), button:has-text("Availability")')
            if stock_button:
                print("   Found stock check button, clicking...")
                await stock_button.click()
                await asyncio.sleep(3)

            print("\n[5] Summary of API calls:")
            print(f"   Total API calls captured: {len(api_calls)}")

            # Save all API calls to file
            with open('monitors/bigw/product_api_calls.json', 'w', encoding='utf-8') as f:
                json.dump(api_calls, f, indent=2)
            print("\n   Saved to: monitors/bigw/product_api_calls.json")

            # Highlight important endpoints
            print("\n[6] Important endpoints found:")
            for call in api_calls:
                if call['type'] == 'response':
                    url = call['url']
                    if 'stock' in url.lower() or 'inventory' in url.lower() or 'price' in url.lower():
                        print(f"\n   {url}")
                        if 'data' in call:
                            print(f"   Status: {call['status']}")
                            data = call['data']
                            if isinstance(data, dict):
                                print(f"   Keys: {list(data.keys())}")

            print("\n[7] Keeping browser open for 30 seconds for manual inspection...")
            print("   Check the Network tab in DevTools for additional APIs")
            await asyncio.sleep(30)

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(discover_product_apis())
