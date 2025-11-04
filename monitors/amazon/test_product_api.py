"""
Test Amazon's internal product data API
Found endpoint: https://data.amazon.com.au/api/marketplaces/A39IBJ37TRP1C6/products/{asins}
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test_product_api():
    """Test the discovered product data API"""

    print("=" * 80)
    print("TESTING AMAZON PRODUCT DATA API")
    print("=" * 80)
    print("\nEndpoint found: data.amazon.com.au/api/marketplaces/A39IBJ37TRP1C6/products")
    print("This API fetches product data by ASIN(s)\n")

    # Sample ASINs from Pokemon cards
    test_asins = [
        "B0FJX86YTG",  # Pokemon product
        "B0C8Y7SDJW",  # Pokemon product
        "B0DMNFRYVD"   # Pokemon product
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        # First, visit Amazon to get cookies/session
        print("[1/3] Loading Amazon.com.au to establish session...")
        await page.goto('https://www.amazon.com.au/', wait_until='domcontentloaded')
        await asyncio.sleep(3)

        print("[2/3] Testing product API with ASINs:", ", ".join(test_asins))

        # Test the product API endpoint
        asins_param = ",".join(test_asins)
        api_url = f"https://data.amazon.com.au/api/marketplaces/A39IBJ37TRP1C6/products/{asins_param}?dexAgsDeepCheckPromiseParamsMap=%7BisAgsDeepCheckPromiseEnabled:true%7D"

        print(f"\n[3/3] Fetching: {api_url}\n")

        response = await page.goto(api_url, wait_until='domcontentloaded')

        # Get response body
        try:
            response_text = await response.text()
            response_json = json.loads(response_text)

            print("=" * 80)
            print("API RESPONSE:")
            print("=" * 80)
            print(json.dumps(response_json, indent=2))

            # Save to file
            with open('amazon_product_api_response.json', 'w') as f:
                json.dump(response_json, f, indent=2)

            print("\n" + "=" * 80)
            print(f"✓ SUCCESS! API returned {len(response_json)} products")
            print("✓ Response saved to amazon_product_api_response.json")
            print("=" * 80)

            # Analyze structure
            print("\n[ANALYSIS] Product data structure:")
            if response_json:
                first_product = list(response_json.values())[0] if response_json else {}
                print(f"\nAvailable fields: {list(first_product.keys())}")

                # Show sample product
                print("\n[SAMPLE] First product:")
                for key, value in first_product.items():
                    print(f"  {key}: {value}")

        except json.JSONDecodeError:
            print(f"[ERROR] Response is not JSON:")
            print(response_text[:500])

        print("\nBrowser will close in 30 seconds...")
        await asyncio.sleep(30)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_product_api())
