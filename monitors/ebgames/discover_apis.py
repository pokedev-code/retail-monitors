"""
Discover EB Games APIs by monitoring network requests
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def discover_apis():
    """Monitor all API calls when loading a product page"""

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

        # Capture all requests and responses
        api_calls = []

        async def log_request(request):
            url = request.url
            if any(keyword in url.lower() for keyword in ['api', 'graphql', 'product', 'stock', 'price', 'inventory', 'availability']):
                api_calls.append({
                    'type': 'request',
                    'method': request.method,
                    'url': url,
                    'headers': dict(request.headers)
                })
                print(f"[REQUEST] {request.method} {url}")

        async def log_response(response):
            url = response.url
            if any(keyword in url.lower() for keyword in ['api', 'graphql', 'product', 'stock', 'price', 'inventory', 'availability']):
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
        print("Discovering EB Games APIs")
        print("=" * 80)
        print(f"Product URL: {product_url}")
        print("=" * 80)

        try:
            print("\n[1] Loading product page...")
            await page.goto(product_url, wait_until='networkidle', timeout=60000)

            print("\n[2] Waiting for additional requests...")
            await asyncio.sleep(10)

            print(f"\n[3] Summary: Captured {len(api_calls)} API calls")

            # Save all API calls to file
            if api_calls:
                with open('monitors/ebgames/api_calls.json', 'w', encoding='utf-8') as f:
                    json.dump(api_calls, f, indent=2)
                print("   Saved to: monitors/ebgames/api_calls.json")

            print("\n[4] Keeping browser open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(discover_apis())
