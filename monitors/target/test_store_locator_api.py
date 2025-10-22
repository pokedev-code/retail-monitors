"""
Test script to discover Target's store locator API
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

async def discover_store_locator_api():
    """Monitor network requests to find store locator API"""

    test_url = "https://www.target.com.au/p/pokemon-tcg-mega-evolution-blister-assorted/71824284"

    print("Discovering Target Store Locator API")
    print("=" * 60)
    print(f"Test Product: {test_url}")
    print("=" * 60)

    # Track all API calls
    api_calls = []
    store_related_calls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Non-headless to see what's happening
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ]
        )

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            geolocation={'longitude': 151.2093, 'latitude': -33.8688},  # Sydney
            permissions=['geolocation'],
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        # Apply stealth
        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        # Intercept all requests and responses
        async def handle_request(request):
            url = request.url
            # Log all API-like requests
            if any(keyword in url.lower() for keyword in ['api', 'store', 'location', 'inventory', 'stock', 'postcode', 'suburb']):
                api_calls.append({
                    'type': 'request',
                    'method': request.method,
                    'url': url,
                    'headers': dict(request.headers) if hasattr(request, 'headers') else {}
                })
                print(f"[REQUEST] {request.method} {url}")

        async def handle_response(response):
            url = response.url
            # Log responses from store-related endpoints
            if any(keyword in url.lower() for keyword in ['store', 'location', 'inventory', 'stock', 'postcode', 'suburb']):
                try:
                    if response.status == 200:
                        # Try to get response body
                        try:
                            body = await response.json()
                            store_related_calls.append({
                                'type': 'response',
                                'url': url,
                                'status': response.status,
                                'body': body
                            })
                            print(f"[RESPONSE] {response.status} {url}")
                            print(f"  Body preview: {json.dumps(body, indent=2)[:500]}...")
                        except:
                            body_text = await response.text()
                            store_related_calls.append({
                                'type': 'response',
                                'url': url,
                                'status': response.status,
                                'body_text': body_text[:500]
                            })
                            print(f"[RESPONSE] {response.status} {url}")
                            print(f"  Text preview: {body_text[:200]}...")
                except Exception as e:
                    print(f"[ERROR] Could not parse response: {e}")

        page.on('request', handle_request)
        page.on('response', handle_response)

        try:
            print("\n[1] Navigating to product page...")
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)

            print("\n[2] Looking for 'Check stock in store' or similar elements...")

            # Try to find and click store locator/stock checker
            store_check_selectors = [
                'button:has-text("Check stock")',
                'button:has-text("Find in store")',
                'a:has-text("Check stock")',
                'a:has-text("Find in store")',
                '[data-testid*="store"]',
                '[class*="store-finder"]',
                '[class*="stock-checker"]',
                'button:has-text("Change store")',
                'button:has-text("Select store")',
            ]

            store_button_found = False
            for selector in store_check_selectors:
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=2000):
                        print(f"   Found button with selector: {selector}")
                        await button.click()
                        store_button_found = True
                        print("   Clicked store button, waiting for API calls...")
                        await asyncio.sleep(3)
                        break
                except:
                    continue

            if not store_button_found:
                print("   No store button found, checking page for store-related elements...")

                # Check if there's a postcode input field
                postcode_selectors = [
                    'input[name*="postcode"]',
                    'input[placeholder*="postcode"]',
                    'input[placeholder*="suburb"]',
                    'input[type="text"]',
                ]

                for selector in postcode_selectors:
                    try:
                        input_field = page.locator(selector).first
                        if await input_field.is_visible(timeout=2000):
                            print(f"   Found input field: {selector}")
                            # Try entering a postcode
                            await input_field.fill("2000")
                            await asyncio.sleep(1)

                            # Look for a search/submit button
                            await page.keyboard.press("Enter")
                            print("   Entered postcode 2000 and submitted")
                            await asyncio.sleep(3)
                            break
                    except:
                        continue

            print("\n[3] Scrolling page to trigger lazy-loaded content...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            print("\n[4] Summary of discovered API calls:")
            print(f"   Total API-related requests: {len(api_calls)}")
            print(f"   Store-related responses: {len(store_related_calls)}")

            if store_related_calls:
                print("\n[5] Store-related API endpoints found:")
                for i, call in enumerate(store_related_calls[:5], 1):
                    print(f"\n   [{i}] {call['url']}")
                    if 'body' in call:
                        print(f"       Response: {json.dumps(call['body'], indent=8)[:300]}...")

                # Save full details to file
                with open('target_store_api_discovery.json', 'w') as f:
                    json.dump(store_related_calls, f, indent=2)
                print(f"\n   Full API details saved to: target_store_api_discovery.json")
            else:
                print("\n   [WARNING] No store-related API calls detected!")
                print("   Saving all API calls for manual inspection...")
                with open('target_all_api_calls.json', 'w') as f:
                    json.dump(api_calls, f, indent=2)
                print(f"   All API calls saved to: target_all_api_calls.json")

            print("\n[6] Keeping browser open for 10 seconds for manual inspection...")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"[ERROR] Error during discovery: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await context.close()
            await browser.close()

if __name__ == '__main__':
    asyncio.run(discover_store_locator_api())
