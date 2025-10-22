"""
Big W Stock Monitor
Monitors Big W product categories for new restocks
Extracts product data from Next.js embedded data (__NEXT_DATA__)
"""
import asyncio
import requests
import logging
import re
import json
from datetime import datetime
from typing import Dict, List
from playwright.async_api import async_playwright

import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

# Global state tracking
INSTOCK = []  # List of product codes currently in stock

def discord_webhook(product: Dict) -> None:
    """Send Discord notification for new product - matches Kmart layout"""
    try:
        fields = []

        # Price field (first)
        if product.get('price'):
            fields.append({
                "name": "Price",
                "value": product['price'],
                "inline": False
            })

        # Stock Change field
        stock_status = product.get('stock_status', 'Unknown')
        fields.append({
            "name": "Stock Change",
            "value": stock_status,
            "inline": False
        })

        # Store field
        fields.append({
            "name": "Store",
            "value": "Big W",
            "inline": False
        })

        # Product Code field
        if product.get('code'):
            fields.append({
                "name": "Product Code",
                "value": product['code'],
                "inline": False
            })

        # eBay links
        if config.ENABLE_EBAY_LINKS:
            search_query = product['title'].replace(' ', '+')
            ebay_current = f"https://www.ebay.com.au/sch/i.html?_nkw={search_query}&LH_BIN=1"
            ebay_sold = f"https://www.ebay.com.au/sch/i.html?_nkw={search_query}&LH_Complete=1&LH_Sold=1"

            fields.append({
                "name": "eBay Links",
                "value": f"[Current Listings]({ebay_current}) | [Sold Listings]({ebay_sold})",
                "inline": False
            })

        embed = {
            "title": product['title'],
            "url": product['url'],
            "fields": fields,
            "color": config.COLOUR,
            "footer": {"text": "Big W Stock Monitor"},
            "timestamp": datetime.utcnow().isoformat()
        }

        data = {
            "username": config.USERNAME,
            "avatar_url": config.AVATAR_URL,
            "embeds": [embed]
        }

        response = requests.post(config.WEBHOOK, json=data, timeout=10)

        if response.status_code in [200, 204]:
            logging.info(f'[SUCCESS] Sent Discord notification for: {product["title"]}')
        else:
            logging.error(f'[ERROR] Discord webhook failed: {response.status_code} - {response.text}')

    except Exception as e:
        logging.error(f'[ERROR] Discord webhook error: {str(e)}')


def matches_filters(product_name: str) -> bool:
    """Check if product matches include/exclude filters"""
    name_lower = product_name.lower()

    # Check exclude keywords first
    if config.EXCLUDE_KEYWORDS:
        for keyword in config.EXCLUDE_KEYWORDS:
            if keyword.lower() in name_lower:
                logging.debug(f'[FILTER] Excluded: {product_name} (matched: {keyword})')
                return False

    # Check include keywords
    if config.INCLUDE_KEYWORDS:
        for keyword in config.INCLUDE_KEYWORDS:
            if keyword.lower() in name_lower:
                return True
        logging.debug(f'[FILTER] Not included: {product_name}')
        return False

    # If no include keywords specified, include all (that passed exclude filter)
    return True


def matches_keywords(product_name: str) -> bool:
    """Check if product matches configured keywords"""
    if not config.KEYWORDS:
        return True  # No keywords = monitor all

    name_lower = product_name.lower()
    for keyword in config.KEYWORDS:
        if keyword.lower() in name_lower:
            return True

    return False


def scrape_products_requests():
    """Scrape products using requests (fallback method to avoid bot detection)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-AU,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://www.bigw.com.au/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        logging.info(f'[SCRAPE] Loading {config.CATEGORY_URL}')
        response = requests.get(config.CATEGORY_URL, headers=headers, timeout=30)

        if response.status_code != 200:
            logging.error(f'[ERROR] HTTP {response.status_code}')
            return []

        html = response.text

        # Extract __NEXT_DATA__ from HTML
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)

        if not match:
            logging.error('[ERROR] Could not find __NEXT_DATA__ in HTML')
            return []

        try:
            next_data = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            logging.error(f'[ERROR] Failed to parse __NEXT_DATA__: {e}')
            return []

        # Navigate to products in Next.js data structure
        try:
            results = next_data['props']['pageProps']['results']
            organic = results['organic']
            products_data = organic['results']

            logging.info(f'[SCRAPE] Found {len(products_data)} products')

        except KeyError as e:
            logging.error(f'[ERROR] Unexpected data structure: {e}')
            return []

        # Parse products
        products = []
        for prod_data in products_data:
            try:
                code = prod_data.get('code')
                name = prod_data.get('information', {}).get('name', 'Unknown')
                brand = prod_data.get('information', {}).get('brand', '')

                # Stock info
                derived = prod_data.get('derived', {})
                in_stock = derived.get('stock', False)
                sold_out = derived.get('soldOut', False)

                # Only process in-stock products
                if not in_stock or sold_out:
                    continue

                # Price (in cents, convert to dollars)
                price_data = derived.get('priceRange', {}).get('min', {})
                price_cents = price_data.get('amount', 0)
                price = f"${price_cents / 100:.2f}" if price_cents else "N/A"

                # Image
                media = derived.get('media', {})
                images = media.get('images', [])
                image_url = ""
                if images and len(images) > 0:
                    large_img = images[0].get('largeImg', {})
                    img_path = large_img.get('url', '')
                    if img_path:
                        image_url = f"https://www.bigw.com.au{img_path}"

                # Product URL
                # Format: /product/name/p/code
                name_slug = name.lower().replace(' ', '-').replace(':', '').replace(',', '')
                product_url = f"https://www.bigw.com.au/product/{name_slug}/p/{code}"

                product = {
                    'code': code,
                    'title': name,
                    'brand': brand,
                    'price': price,
                    'image': image_url,
                    'url': product_url,
                    'stock_status': 'In Stock'
                }

                products.append(product)

            except Exception as e:
                logging.error(f'[ERROR] Parsing product: {e}')
                continue

        logging.info(f'[SCRAPE] Extracted {len(products)} in-stock products')
        return products

    except Exception as e:
        logging.error(f'[ERROR] Scraping failed: {e}')
        import traceback
        traceback.print_exc()
        return []


async def monitor():
    """Main monitor loop"""
    global INSTOCK

    start = True  # Skip notifications on first run
    iteration = 0

    print("=" * 80)
    print("BIG W STOCK MONITOR")
    print("=" * 80)
    print(f"Category URL: {config.CATEGORY_URL}")
    print(f"Delay: {config.DELAY} seconds")
    print(f"Keywords: {config.KEYWORDS if config.KEYWORDS else 'ALL'}")
    print(f"Webhook: {'Configured' if config.WEBHOOK != 'YOUR_DISCORD_WEBHOOK_URL_HERE' else 'NOT CONFIGURED!'}")
    print("=" * 80)

    if config.WEBHOOK == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("[ERROR] Please configure your Discord webhook URL in config.py!")
        return

    while True:
        try:
            iteration += 1
            print(f"\n[MONITOR] Iteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Scrape products
            products = scrape_products_requests()

            if not products:
                logging.warning('[WARNING] No products found in scrape')
                await asyncio.sleep(config.DELAY)
                continue

            # Process each product
            for product in products:
                # Apply filters
                if not matches_filters(product['title']):
                    continue

                # Apply keywords
                if not matches_keywords(product['title']):
                    continue

                product_code = product['code']

                # Check if new product
                if product_code not in INSTOCK:
                    INSTOCK.append(product_code)

                    if not start:
                        logging.info(f'[NEW] {product["title"]} - {product["price"]}')
                        print(f'[NEW] {product["title"]} - {product["price"]}')
                        discord_webhook(product)
                    else:
                        logging.info(f'[INITIAL] Tracking: {product["title"]}')

            # Remove products no longer in stock
            current_codes = [p['code'] for p in products]
            removed = [code for code in INSTOCK if code not in current_codes]
            for code in removed:
                INSTOCK.remove(code)
                logging.info(f'[OOS] Product removed from tracking: {code}')

            # After first scrape, enable notifications
            if start:
                start = False
                print(f'[MONITOR] Initial scrape complete. Tracking {len(INSTOCK)} products.')
                print('[MONITOR] Now monitoring for changes...')

            print(f'[STATS] In stock: {len(INSTOCK)} | Iteration: {iteration}')

            # Wait before next scrape
            await asyncio.sleep(config.DELAY)

        except Exception as e:
            logging.error(f'[ERROR] Monitor loop error: {str(e)}')
            print(f'[ERROR] {str(e)}')
            await asyncio.sleep(config.DELAY)


if __name__ == '__main__':
    asyncio.run(monitor())
