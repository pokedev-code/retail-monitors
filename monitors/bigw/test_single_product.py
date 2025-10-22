"""
Test script for Big W monitor - Single Product
Tests scraping a specific product page and sending notification
"""
import requests
import json
import re
from monitor import discord_webhook
from datetime import datetime
import config

def scrape_single_product(product_url):
    """Scrape a single product page from Big W"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-AU,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://www.bigw.com.au/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        print(f"[SCRAPE] Loading {product_url}")
        response = requests.get(product_url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"[ERROR] HTTP {response.status_code}")
            return None

        html = response.text

        # Extract __NEXT_DATA__ from HTML
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)

        if not match:
            print('[ERROR] Could not find __NEXT_DATA__ in HTML')
            return None

        try:
            next_data = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            print(f'[ERROR] Failed to parse __NEXT_DATA__: {e}')
            return None

        # Navigate to product data in Next.js structure
        try:
            # For product pages, the structure is different than category pages
            page_props = next_data['props']['pageProps']

            # Try to find product data
            product_data = None

            # Check if it's in serializedData
            if 'serializedData' in page_props:
                serialized = page_props['serializedData']

                # Try 'products' or '$products'
                if 'products' in serialized:
                    products = serialized['products']
                    if isinstance(products, dict):
                        # Get the product by ID from pageProps
                        product_id = page_props.get('productId')
                        if product_id and product_id in products:
                            product_data = products[product_id]
                            print(f'   Found product in products[{product_id}]')
                    elif isinstance(products, list) and len(products) > 0:
                        product_data = products[0]
                        print('   Found product in products list')

                elif '$products' in serialized:
                    products = serialized['$products']
                    if isinstance(products, dict):
                        product_id = page_props.get('productId')
                        if product_id and product_id in products:
                            product_data = products[product_id]
                            print(f'   Found product in $products[{product_id}]')
                    elif isinstance(products, list) and len(products) > 0:
                        product_data = products[0]
                        print('   Found product in $products list')

            # Check if it's directly in pageProps
            if not product_data and 'product' in page_props:
                product_data = page_props['product']

            if not product_data:
                print('[ERROR] Could not find product data in Next.js structure')
                print('Available keys in pageProps:', list(page_props.keys()))
                if 'serializedData' in page_props:
                    print('Keys in serializedData:', list(page_props['serializedData'].keys()))
                return None

            print('[SUCCESS] Found product data!')

            # Extract product information
            code = product_data.get('code', product_data.get('id', ''))

            # Try to get name from different possible locations
            name = (product_data.get('name') or
                   product_data.get('information', {}).get('name') or
                   product_data.get('title') or
                   'Unknown Product')

            # Try to get brand
            brand = (product_data.get('information', {}).get('brand') or
                    product_data.get('brand') or
                    '')

            # Stock info - check listingStatus
            # For individual product pages, stock is determined by listingStatus
            listing_status = product_data.get('listingStatus', '')
            in_stock = listing_status == 'LISTEDSELLABLE'

            # Fallback to old method if listingStatus not present
            if not listing_status:
                derived = product_data.get('derived', {})
                fulfillment = product_data.get('fulfillment', {})
                in_stock = (derived.get('stock', False) or
                           product_data.get('inStock', False) or
                           fulfillment.get('inStock', False))
                sold_out = (derived.get('soldOut', False) or
                           product_data.get('soldOut', False))
            else:
                sold_out = listing_status != 'LISTEDSELLABLE'

            # Get price from pricing API
            price = "N/A"
            try:
                pricing_url = f'https://api.bigw.com.au/api/pricing/v0/product/{code}'
                pricing_response = requests.get(pricing_url, headers=headers, timeout=30)
                if pricing_response.status_code == 200:
                    pricing_data = pricing_response.json()
                    if 'products' in pricing_data and code in pricing_data['products']:
                        product_pricing = pricing_data['products'][code]
                        price_range = product_pricing.get('priceRange', {})
                        min_price = price_range.get('min', {})
                        price_cents = min_price.get('amount', 0)
                        if price_cents:
                            price = f"${price_cents / 100:.2f}"
                            print(f'   Got price from API: {price}')
            except Exception as e:
                print(f'   [WARNING] Could not get price from API: {e}')
                # Fallback to __NEXT_DATA__ price
                price_cents = 0
                if 'derived' in product_data and 'priceRange' in derived:
                    price_data = derived.get('priceRange', {}).get('min', {})
                    price_cents = price_data.get('amount', 0)
                elif 'price' in product_data:
                    price_obj = product_data['price']
                    if isinstance(price_obj, dict):
                        price_cents = price_obj.get('amount', price_obj.get('cents', 0))
                    elif isinstance(price_obj, (int, float)):
                        price_cents = price_obj
                if price_cents:
                    price = f"${price_cents / 100:.2f}"

            # Image - try multiple locations
            image_url = ""

            # Check assets.images first (for individual product pages)
            assets = product_data.get('assets', {})
            asset_images = assets.get('images', [])

            if asset_images and len(asset_images) > 0:
                # Get the largeImg from the first image's sources
                sources = asset_images[0].get('sources', [])
                for source in sources:
                    if source.get('format') == 'largeImg':
                        img_path = source.get('url', '')
                        if img_path:
                            if not img_path.startswith('http'):
                                image_url = f"https://www.bigw.com.au{img_path}"
                            else:
                                image_url = img_path
                            break

            # Fallback to old method if no assets.images
            if not image_url:
                media = product_data.get('derived', {}).get('media', {}) or product_data.get('media', {})
                images = media.get('images', []) or product_data.get('images', [])

                if images and len(images) > 0:
                    if isinstance(images[0], dict):
                        large_img = images[0].get('largeImg', images[0].get('url', {}))
                        if isinstance(large_img, dict):
                            img_path = large_img.get('url', '')
                        else:
                            img_path = large_img
                        if img_path and not img_path.startswith('http'):
                            image_url = f"https://www.bigw.com.au{img_path}"
                        else:
                            image_url = img_path

            product = {
                'code': code,
                'title': name,
                'brand': brand,
                'price': price,
                'image': image_url,
                'url': product_url,
                'stock_status': 'In Stock' if (in_stock and not sold_out) else 'Out of Stock'
            }

            return product

        except KeyError as e:
            print(f'[ERROR] Unexpected data structure: {e}')
            return None

    except Exception as e:
        print(f'[ERROR] Scraping failed: {e}')
        import traceback
        traceback.print_exc()
        return None


def test_product():
    """Test scraping a single product"""
    print("=" * 80)
    print("Testing Big W Monitor - Single Product")
    print("=" * 80)

    product_url = "https://www.bigw.com.au/product/pokemon-tcg-triple-whammy-tin/p/6047808"

    print(f"\n[1] Scraping product: {product_url}")

    product = scrape_single_product(product_url)

    if not product:
        print("\n[ERROR] Failed to scrape product!")
        print("This is likely due to Big W's bot detection.")
        print("Try:")
        print("  - Using a VPN")
        print("  - Running from a different network")
        print("  - Adding delays between requests")
        return False

    print(f"\n[SUCCESS] Product scraped successfully!")
    print(f"   Code: {product['code']}")
    print(f"   Title: {product['title']}")
    print(f"   Brand: {product['brand']}")
    print(f"   Price: {product['price']}")
    print(f"   Stock: {product['stock_status']}")
    print(f"   Image: {product['image'][:80]}...")

    # Test webhook
    print(f"\n[2] Sending Discord webhook notification...")

    if config.WEBHOOK == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("   [SKIP] Webhook not configured in config.py")
        return False

    discord_webhook(product)
    print("   [SUCCESS] Webhook sent! Check your Discord channel.")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)

    return True


if __name__ == '__main__':
    import sys
    success = test_product()
    sys.exit(0 if success else 1)
