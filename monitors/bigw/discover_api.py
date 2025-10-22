"""
Direct API exploration for Big W
Trying to find the product listing endpoint
"""
import requests
import json

def test_bigw_apis():
    """Test various Big W API endpoints"""

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-AU,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://www.bigw.com.au/',
        'Origin': 'https://www.bigw.com.au'
    }

    print("=" * 80)
    print("Testing Big W API Endpoints")
    print("=" * 80)

    # Based on network logs, try these endpoints
    test_urls = [
        # Adobe AEM endpoints
        "https://publish-p16597-e60686.adobeaemcloud.com/content/bigw/au/en/api/top-selling-products.model.all.flatten.json",

        # Try category/product endpoints
        "https://www.bigw.com.au/api/products/pokemon",
        "https://www.bigw.com.au/api/search?q=pokemon",
        "https://www.bigw.com.au/api/category/681510201",

        # Try Next.js data endpoint
        "https://www.bigw.com.au/_next/data/build-id/toys/trading-cards/pokemon-trading-cards/c/681510201.json",

        # Try direct product page for HTML analysis
        "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201"
    ]

    for url in test_urls:
        print(f"\n[TEST] {url}")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                print(f"   Content-Type: {content_type}")

                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"   JSON Keys: {list(data.keys()) if isinstance(data, dict) else 'List/Other'}")

                        # Save successful responses
                        filename = url.split('/')[-1].replace('?', '_').replace('=', '_')[:50]
                        with open(f'monitors/bigw/response_{filename}.json', 'w') as f:
                            json.dump(data, f, indent=2)
                        print(f"   Saved to: response_{filename}.json")

                    except:
                        print(f"   Body (first 200 chars): {response.text[:200]}")
                elif 'html' in content_type:
                    # Check for __NEXT_DATA__
                    if '__NEXT_DATA__' in response.text:
                        print("   [FOUND] __NEXT_DATA__ in HTML!")

                        # Try to extract it
                        import re
                        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', response.text, re.DOTALL)
                        if match:
                            try:
                                next_data = json.loads(match.group(1))
                                print(f"   Next.js Data Keys: {list(next_data.keys())}")

                                import os
                                os.makedirs('monitors/bigw', exist_ok=True)
                                with open('monitors/bigw/next_data_extracted.json', 'w', encoding='utf-8') as f:
                                    json.dump(next_data, f, indent=2)
                                print("   Saved to: next_data_extracted.json")

                            except Exception as e:
                                print(f"   Error parsing Next.js data: {e}")

        except requests.RequestException as e:
            print(f"   Error: {e}")

    print("\n" + "=" * 80)
    print("Exploration Complete")
    print("=" * 80)

if __name__ == '__main__':
    test_bigw_apis()
