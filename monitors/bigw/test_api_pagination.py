"""
Test if Big W has an API endpoint we can call directly for all pages
"""
import requests
import json

# Try to find the API endpoint by checking network requests
# Big W might use an API like /api/products?page=1&category=681510201

CATEGORY_ID = "681510201"

# Test different possible API patterns
api_patterns = [
    f"https://www.bigw.com.au/api/products?category={CATEGORY_ID}",
    f"https://www.bigw.com.au/api/search?category={CATEGORY_ID}",
    f"https://api.bigw.com.au/products?category={CATEGORY_ID}",
    f"https://www.bigw.com.au/_next/data/products?category={CATEGORY_ID}",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print("Testing possible API endpoints...\n")

for url in api_patterns:
    print(f"Trying: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  [FOUND] Possible API endpoint!")
            print(f"  Content length: {len(response.text)} bytes")
            # Try to parse as JSON
            try:
                data = response.json()
                print(f"  JSON keys: {list(data.keys())[:5]}")
            except:
                print(f"  Not JSON, first 200 chars: {response.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

print("\n" + "="*60)
print("CONCLUSION:")
print("If no API found, we need to load each page URL separately")
print("  e.g., https://www.bigw.com.au/...?page=1, ?page=2, etc.")
print("="*60)
