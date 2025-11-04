"""
Target Australia Monitor - Enhanced Playwright Version
Monitors Target AU for product restocks with optimized Playwright usage
"""

import config
import logging
import asyncio
import re
import urllib.parse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth
import requests
from datetime import datetime
from typing import List, Dict, Optional
import json
from store_state_mapper import load_store_mapping, fetch_all_stores, save_store_mapping
import os

# Logging
logging.basicConfig(
    filename='target-monitor.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(message)s',
    level=logging.DEBUG
)

# In-stock tracking
INSTOCK = []

# Cache for product details
PRODUCT_CACHE = {}

# Request counters for monitoring
REQUEST_COUNT = 0
ERROR_COUNT = 0

# Store number to state mapping
STORE_STATE_MAP = {}


def group_stores_by_state(stores_with_stock: List[str]) -> Dict[str, List[Dict]]:
    """Group store numbers by their state and include store names

    Returns: {state: [{'number': '5429', 'name': 'Subiaco'}, ...]}
    """
    state_stores = {}

    for store_num in stores_with_stock:
        store_info = STORE_STATE_MAP.get(store_num)

        if store_info:
            # New format: {'state': 'WA', 'name': 'Subiaco'}
            if isinstance(store_info, dict):
                state = store_info.get('state', 'UNKNOWN')
                name = store_info.get('name', f'Store {store_num}')
            else:
                # Old format: just state string
                state = store_info
                name = f'Store {store_num}'
        else:
            state = 'UNKNOWN'
            name = f'Store {store_num}'

        if state not in state_stores:
            state_stores[state] = []

        state_stores[state].append({
            'number': store_num,
            'name': name
        })

    return state_stores


def discord_webhook(product_info: Dict, state_name: Optional[str] = None,
                    state_stores: Optional[List[Dict]] = None) -> None:
    """Send Discord notification for new product

    Args:
        product_info: Product information dictionary
        state_name: Optional state code (NSW, VIC, etc.) for state-specific notifications
        state_stores: Optional list of store dicts [{'number': '5429', 'name': 'Subiaco'}, ...]
    """
    try:
        # Determine which webhook to use
        webhook_url = config.WEBHOOK  # Default fallback
        webhook_type = "main/fallback"

        if state_name and hasattr(config, 'STATE_WEBHOOKS'):
            state_webhook = config.STATE_WEBHOOKS.get(state_name)
            if state_webhook:
                webhook_url = state_webhook
                webhook_type = f"{state_name} state-specific"
                logging.info(f'Using state-specific webhook for {state_name}')

        fields = []

        # Add state field if this is a state-specific notification
        if state_name:
            fields.append({
                "name": "State",
                "value": state_name,
                "inline": True
            })

        if product_info.get('price'):
            fields.append({
                "name": "Price",
                "value": product_info['price'],
                "inline": True
            })

        fields.append({"name": "Store", "value": "Target AU", "inline": True})
        fields.append({"name": "Product ID", "value": product_info['id'], "inline": True})

        if product_info.get('availability'):
            fields.append({
                "name": "Availability",
                "value": product_info['availability'],
                "inline": False
            })

        # Stock information from API
        stock_info = product_info.get('stock_info')
        if stock_info:
            # Delivery mode status
            delivery_modes = stock_info.get('delivery_modes', {})
            if delivery_modes:
                delivery_text = []
                for mode, status in delivery_modes.items():
                    if status == 'inStock':
                        # Green circle emoji (should work in Discord)
                        delivery_text.append(f"\U0001F7E2 {mode}")
                    elif status == 'outOfStock':
                        # Red circle emoji (should work in Discord)
                        delivery_text.append(f"\U0001F534 {mode}")

                if delivery_text:
                    fields.append({
                        "name": "Delivery Options",
                        "value": "\n".join(delivery_text),
                        "inline": True
                    })

            # Store stock status - use state_stores if provided, otherwise use all stores
            stores_to_display = state_stores if state_stores else stock_info.get('stores_with_stock', [])
            consolidated = stock_info.get('consolidated_stock', 'unknown')

            if stores_to_display:
                store_count = len(stores_to_display)

                # Format store list - check if it's the new dict format or old string format
                if store_count > 0 and isinstance(stores_to_display[0], dict):
                    # New format with names: [{'number': '5429', 'name': 'Subiaco'}, ...]
                    if store_count <= 10:
                        store_list = ", ".join([f"{s['name']}" for s in stores_to_display])
                    else:
                        store_list = ", ".join([f"{s['name']}" for s in stores_to_display[:10]])
                else:
                    # Old format: just store numbers
                    if store_count <= 10:
                        store_list = ", ".join(stores_to_display)
                    else:
                        store_list = ", ".join(stores_to_display[:10])

                field_name = f"Stores with Stock in {state_name} ({store_count})" if state_name else f"Stores with Stock ({store_count})"

                if store_count <= 10:
                    fields.append({
                        "name": field_name,
                        "value": store_list,
                        "inline": False
                    })
                else:
                    fields.append({
                        "name": field_name,
                        "value": f"{store_list}... and {store_count - 10} more",
                        "inline": False
                    })
            elif consolidated == 'inStock':
                fields.append({
                    "name": "Store Availability",
                    "value": "Available in some stores",
                    "inline": False
                })
            else:
                fields.append({
                    "name": "Store Availability",
                    "value": "Not available in stores",
                    "inline": False
                })

        # eBay links
        if config.ENABLE_EBAY_LINKS:
            search_query = product_info['title'].replace(' ', '+')
            ebay_current = f"https://www.ebay.com.au/sch/i.html?_nkw={search_query}&LH_BIN=1"
            ebay_sold = f"https://www.ebay.com.au/sch/i.html?_nkw={search_query}&LH_Complete=1&LH_Sold=1"

            fields.append({
                "name": "eBay Links",
                "value": f"[Current Listings]({ebay_current}) | [Sold Listings]({ebay_sold})",
                "inline": False
            })

        data = {
            "username": config.USERNAME,
            "avatar_url": config.AVATAR_URL,
            "embeds": [{
                "title": product_info['title'],
                "url": product_info['url'],
                "thumbnail": {"url": product_info['image']} if product_info.get('image') else None,
                "fields": fields,
                "color": int(config.COLOUR),
                "footer": {"text": "Target AU Stock Monitor"},
                "timestamp": datetime.now().isoformat()
            }]
        }

        response = requests.post(webhook_url, json=data, timeout=10)

        if response.status_code == 204:
            print(f'      [OK] Sent to {webhook_type} webhook (URL ending: ...{webhook_url[-20:]})')
            logging.info(f'[SUCCESS] Sent Discord notification for: {product_info["title"]} to {webhook_type}')
        else:
            print(f'      [FAIL] Failed to send to {webhook_type} webhook: {response.status_code}')
            logging.error(f'[ERROR] Discord webhook failed: {response.status_code}')

    except Exception as e:
        logging.error(f'[ERROR] Discord webhook error: {str(e)}')


async def get_product_details(page, product_url: str, product_id: str, retry_count: int = 0) -> Dict:
    """
    Scrape product details with retry logic and API interception
    """
    global REQUEST_COUNT, ERROR_COUNT

    # Check cache first
    if product_id in PRODUCT_CACHE:
        return PRODUCT_CACHE[product_id]

    max_retries = 2

    try:
        logging.info(f'[DETAILS] Fetching details for product {product_id} (attempt {retry_count + 1})')
        REQUEST_COUNT += 1

        # Set up stock API interceptor BEFORE navigating
        stock_data = None
        stock_received = asyncio.Event()

        async def handle_stock_response(response):
            nonlocal stock_data
            if 'lz3inventory/stockStatus' in response.url and product_id in response.url:
                try:
                    data = await response.json()
                    stock_data = data
                    stock_received.set()
                    logging.info(f'[STOCK] Captured stock API response for {product_id}')
                except Exception as e:
                    logging.error(f'[STOCK] Failed to parse stock response: {e}')

        page.on('response', handle_stock_response)

        # Navigate with timeout
        try:
            await page.goto(product_url, wait_until='load', timeout=30000)
        except PlaywrightTimeout:
            logging.warning(f'[TIMEOUT] Page load timeout for {product_id}')
            if retry_count < max_retries:
                await asyncio.sleep(2)
                return await get_product_details(page, product_url, product_id, retry_count + 1)
            ERROR_COUNT += 1
            raise

        # Wait for stock API response
        try:
            await asyncio.wait_for(stock_received.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logging.warning(f'[STOCK] Timeout waiting for stock API for {product_id}')

        # Extract details using JavaScript with proper error handling
        details = await page.evaluate('''() => {
            let price = '';
            let image = '';
            let availability = 'Unknown';

            try {
                // Try to find price
                const priceSelectors = [
                    '[data-testid="product-price"]',
                    '.price',
                    '[class*="price"]',
                    '[class*="Price"]'
                ];

                for (const selector of priceSelectors) {
                    const priceEl = document.querySelector(selector);
                    if (priceEl) {
                        price = priceEl.textContent.trim();
                        if (price.includes('$')) {
                            price = price.split('$').filter(p => p.trim())[0];
                            price = '$' + price.trim().split(/\\s/)[0];
                            break;
                        }
                    }
                }

                // Try to find main product image
                const imageSelectors = [
                    'img[data-testid="product-image"]',
                    'img[alt*="Pokemon"]',
                    'img[alt*="TCG"]',
                    '.product-image img',
                    'meta[property="og:image"]'
                ];

                for (const selector of imageSelectors) {
                    const imgEl = document.querySelector(selector);
                    if (imgEl) {
                        if (selector.startsWith('meta')) {
                            image = imgEl.content;
                        } else {
                            image = imgEl.src;
                        }
                        if (image) break;
                    }
                }

                // Determine availability
                const bodyText = document.body.textContent.toLowerCase();
                if (bodyText.includes('add to cart') || bodyText.includes('buy now')) {
                    availability = 'In Stock';
                } else if (bodyText.includes('out of stock') || bodyText.includes('sold out')) {
                    availability = 'Out of Stock';
                } else if (bodyText.includes('unavailable')) {
                    availability = 'Unavailable';
                }
            } catch(e) {
                console.error('Error extracting details:', e);
            }

            return { price, image, availability };
        }''')

        # Process stock data if captured
        if stock_data and 'stock' in stock_data and len(stock_data['stock']) > 0:
            stock_item = stock_data['stock'][0]

            delivery_status = {
                'Home Delivery': stock_item.get('hd', 'unknown'),
                'Click & Collect': stock_item.get('cc', 'unknown')
            }

            stores_with_stock = []
            store_soh = stock_item.get('storeSoh', {})
            if isinstance(store_soh, dict):
                for store_num, status in store_soh.items():
                    if status == 'inStock':
                        stores_with_stock.append(store_num)

            consolidated_status = stock_item.get('consolidated_stores_soh', 'unknown')

            details['stock_info'] = {
                'delivery_modes': delivery_status,
                'stores_with_stock': stores_with_stock,
                'consolidated_stock': consolidated_status,
                'overall_ats': stock_item.get('ats', 'unknown')
            }

            logging.info(f'[STOCK] Parsed stock info: {len(stores_with_stock)} stores with stock')

        # Cache the results
        PRODUCT_CACHE[product_id] = details
        logging.info(f'[DETAILS] Found price: {details["price"]}, availability: {details["availability"]}')

        return details

    except Exception as e:
        ERROR_COUNT += 1
        logging.error(f'[ERROR] Failed to get product details: {str(e)}')

        # Retry logic
        if retry_count < max_retries:
            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
            return await get_product_details(page, product_url, product_id, retry_count + 1)

        # Return empty details and cache to avoid repeated failures
        empty_details = {'price': '', 'image': '', 'availability': ''}
        PRODUCT_CACHE[product_id] = empty_details
        return empty_details


def is_pokemon_card_product(title: str) -> bool:
    """Filter logic to determine if product is a Pokemon card product"""
    title_lower = title.lower()

    # First check if it's actually a Pokemon product
    is_pokemon = 'pokemon' in title_lower or 'pokémon' in title_lower
    if not is_pokemon:
        # If it's not a Pokemon product at all, exclude it
        return False

    # Check if it's a card product (has card-related keywords)
    is_card_product = any(keyword in title_lower for keyword in config.CARD_INCLUDE_KEYWORDS)
    if not is_card_product:
        # It's Pokemon but not a card product (e.g., plush, toy)
        return False

    # Check for exclusions, but ignore "game" since "Trading Card Game" is valid for Pokemon TCG
    exclusions_to_check = [kw for kw in config.CARD_EXCLUDE_KEYWORDS if kw != 'game']
    is_excluded = any(keyword in title_lower for keyword in exclusions_to_check)

    return not is_excluded


async def scrape_products(page, keyword: str) -> List[Dict]:
    """
    Scrape products from Target AU search page with optimized Playwright usage
    """
    products = []

    try:
        # Build search URL
        encoded_keyword = urllib.parse.quote_plus(keyword)
        search_url = f"{config.BASE_URL}{encoded_keyword}"

        logging.info(f'[SCRAPING] Loading: {search_url}')

        # Navigate with proper wait strategy
        await page.goto(search_url, wait_until='domcontentloaded', timeout=60000)

        # Wait for content to be ready
        try:
            await page.wait_for_selector('a[href*="/p/"]', timeout=10000)
        except PlaywrightTimeout:
            logging.warning(f'[SCRAPING] No products found for keyword: {keyword}')
            return []

        # Wait a bit more for JavaScript to fully render
        await asyncio.sleep(2)

        # Get all product links using JavaScript evaluation with error handling
        product_data = await page.evaluate('''() => {
            const products = [];
            try {
                const links = document.querySelectorAll('a[href*="/p/"]');

                links.forEach(link => {
                    try {
                        const href = link.href;
                        if (!href) return;

                        // Get title from img alt or link text
                        let title = '';
                        const img = link.querySelector('img');
                        if (img && img.alt) {
                            title = img.alt;
                        } else {
                            title = link.textContent.trim();
                        }

                        // Get image URL
                        let imageUrl = '';
                        if (img && img.src) {
                            imageUrl = img.src;
                        }

                        // Try to find price
                        let price = 'N/A';
                        let parent = link.parentElement;
                        for (let i = 0; i < 3; i++) {
                            if (!parent) break;
                            const priceEl = parent.querySelector('[class*="price"], [class*="Price"]');
                            if (priceEl) {
                                price = priceEl.textContent.trim();
                                break;
                            }
                            parent = parent.parentElement;
                        }

                        products.push({
                            url: href,
                            title: title,
                            image: imageUrl,
                            price: price
                        });
                    } catch(e) {
                        console.error('Error parsing product:', e);
                    }
                });
            } catch(e) {
                console.error('Error in product scraping:', e);
            }

            return products;
        }''')

        seen_ids = set()

        for item in product_data:
            try:
                href = item.get('url', '')
                if not href:
                    continue

                # Extract product ID from URL pattern
                match = re.search(r'/p/([^/]+)/(\d+)', href)
                if not match:
                    continue

                product_id = match.group(2)

                if product_id in seen_ids:
                    continue
                seen_ids.add(product_id)

                slug = match.group(1)
                title = item.get('title', '')

                if not title or len(title) < 5:
                    title = slug.replace('-', ' ').title()

                title = ' '.join(title.split())

                if len(title) < 5:
                    continue

                image_url = item.get('image', '')
                price = item.get('price', 'N/A')

                # Apply Pokemon card filtering
                if 'pokemon' in keyword.lower():
                    if not is_pokemon_card_product(title):
                        logging.debug(f'[FILTERED] Skipping non-card product: {title}')
                        continue

                products.append({
                    'id': product_id,
                    'title': title,
                    'url': href,
                    'image': image_url,
                    'price': price
                })

            except Exception as e:
                logging.error(f'[ERROR] Failed to parse product: {str(e)}')
                continue

        logging.info(f'[SCRAPING] Found {len(products)} valid products for keyword: {keyword}')

    except Exception as e:
        logging.error(f'[ERROR] Scraping failed: {str(e)}')

    return products


async def monitor():
    """Main monitoring loop with enhanced Playwright usage"""
    global REQUEST_COUNT, ERROR_COUNT, STORE_STATE_MAP

    logging.info('[MONITOR] Target AU Monitor Starting (Enhanced Version)...')
    print('[MONITOR] Target AU Monitor Starting (Enhanced Version)...')

    if not config.WEBHOOK:
        logging.error('[ERROR] No webhook URL configured')
        print('[ERROR] Please configure WEBHOOK in config.py')
        return

    if not config.KEYWORDS:
        logging.error('[ERROR] No keywords configured')
        print('[ERROR] Please configure KEYWORDS in config.py')
        return

    # Load store-to-state mapping
    print('[INIT] Loading store-to-state mapping...')
    STORE_STATE_MAP = load_store_mapping()

    if not STORE_STATE_MAP:
        print('[INIT] No cached mapping found. Fetching from Target API...')
        print('[INIT] This may take ~10 seconds...')
        STORE_STATE_MAP = fetch_all_stores()
        if STORE_STATE_MAP:
            save_store_mapping(STORE_STATE_MAP)
            print(f'[INIT] Loaded {len(STORE_STATE_MAP)} stores')
        else:
            print('[WARNING] Could not fetch store mapping. State-specific webhooks will not work.')
            logging.warning('[WARNING] Could not load store mapping')
    else:
        print(f'[INIT] Loaded {len(STORE_STATE_MAP)} stores from cache')

    print(f'[CONFIG] Monitoring keywords: {config.KEYWORDS}')
    print(f'[CONFIG] Delay: {config.DELAY} seconds')

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-http2',
                '--enable-webgl',
                '--use-gl=swiftshader',
                '--enable-accelerated-2d-canvas',
                '--disable-features=IsolateOrigins,site-per-process',
                '--window-size=1920,1080',
            ],
            slow_mo=50
        )

        # Create context
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney',
            geolocation={'longitude': 151.2093, 'latitude': -33.8688},
            permissions=['geolocation'],
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            color_scheme='light',
            extra_http_headers={
                'Accept-Language': 'en-AU,en-US;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'DNT': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
        )

        page = await context.new_page()

        # Apply stealth
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        # JavaScript injections
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [{
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    name: "Chrome PDF Plugin"
                }]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-AU', 'en-US', 'en']
            });
        """)

        # Flag to prevent notifications on first scrape
        start = True

        try:
            iteration = 0
            while True:
                iteration += 1
                try:
                    for keyword in config.KEYWORDS:
                        # Scrape products
                        products = await scrape_products(page, keyword)

                        # Check for new products or restocks
                        for product in products:
                            product_identifier = f"{product['id']}_{keyword}"

                            if product_identifier not in INSTOCK:
                                # Get detailed product information
                                details = await get_product_details(page, product['url'], product['id'])

                                # Merge details
                                product['price'] = details.get('price', product.get('price', 'N/A'))
                                # Prioritize search result image (more reliable than product page image)
                                search_image = product.get('image', '')
                                detail_image = details.get('image', '')
                                product['image'] = search_image if search_image else detail_image
                                product['availability'] = details.get('availability', 'In Stock')
                                if 'stock_info' in details:
                                    product['stock_info'] = details['stock_info']

                                # Add to in-stock list
                                INSTOCK.append(product_identifier)

                                # Send notification (skip on first run)
                                if not start:
                                    logging.info(f'[NEW] Product found: {product["title"]}')
                                    print(f'[NEW] {product["title"]} - {product["price"]}')

                                    # Check if we have stock information to group by state
                                    stock_info = product.get('stock_info')
                                    if stock_info and stock_info.get('stores_with_stock'):
                                        # Group stores by state
                                        state_groups = group_stores_by_state(stock_info['stores_with_stock'])

                                        # Send separate notification for each state
                                        if state_groups:
                                            # First, send to main unfiltered webhook (all stores)
                                            logging.info(f'[NOTIFY] Sending to main webhook (all stores)')
                                            print(f'  → Main channel: All states')
                                            discord_webhook(product)

                                            # Then send state-specific notifications
                                            for state, stores in state_groups.items():
                                                if state != 'UNKNOWN':  # Skip unknown states
                                                    logging.info(f'[NOTIFY] Sending notification for {state}: {len(stores)} stores')
                                                    print(f'  → {state}: {len(stores)} stores with stock')
                                                    discord_webhook(product, state_name=state, state_stores=stores)
                                        else:
                                            # Fallback to single notification if no state grouping
                                            discord_webhook(product)
                                    else:
                                        # No store stock info, send single notification
                                        discord_webhook(product)
                                else:
                                    logging.info(f'[INITIAL] Tracking: {product["title"]}')

                        # Remove products no longer in stock
                        current_ids = [f"{p['id']}_{keyword}" for p in products]
                        removed = [pid for pid in INSTOCK if pid.endswith(f'_{keyword}') and pid not in current_ids]
                        for pid in removed:
                            INSTOCK.remove(pid)
                            logging.info(f'[OOS] Product removed from tracking: {pid}')

                    # After first scrape, enable notifications
                    if start:
                        start = False
                        print('[MONITOR] Initial scrape complete. Now monitoring for changes...')

                    # Performance metrics
                    error_rate = (ERROR_COUNT / REQUEST_COUNT * 100) if REQUEST_COUNT > 0 else 0
                    print(f'[STATS] Iteration {iteration} | Requests: {REQUEST_COUNT} | Errors: {ERROR_COUNT} ({error_rate:.1f}%)')

                    # Wait before next scrape
                    await asyncio.sleep(config.DELAY)

                except Exception as e:
                    logging.error(f'[ERROR] Monitor loop error: {str(e)}')
                    print(f'[ERROR] {str(e)}')
                    await asyncio.sleep(config.DELAY)

        except KeyboardInterrupt:
            print('\n[MONITOR] Stopped by user')
        finally:
            await context.close()
            await browser.close()


if __name__ == '__main__':
    asyncio.run(monitor())
