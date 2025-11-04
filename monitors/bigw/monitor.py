"""
Big W Stock Monitor - Enhanced Playwright Version
Monitors Big W product categories for new restocks
Extracts product data from Next.js embedded data (__NEXT_DATA__)
Uses Playwright with stealth mode to bypass bot detection
"""
import asyncio
import logging
import re
import json
from datetime import datetime
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import requests

import config

# Import free-proxy library if needed
if config.PROXY_ENABLED and config.USE_FREE_PROXIES:
    try:
        from fp.fp import FreeProxy
        FREE_PROXY_AVAILABLE = True
        logging.info('[PROXY] Free proxy library loaded')
    except ImportError:
        FREE_PROXY_AVAILABLE = False
        logging.warning('[PROXY] free-proxy library not available, install with: pip install free-proxy')
else:
    FREE_PROXY_AVAILABLE = False

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
current_proxy_index = 0  # Track which proxy we're currently using
free_proxy_pool = []  # Pool of fetched free proxies

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


def fetch_free_proxies() -> List[str]:
    """Fetch a batch of free proxies"""
    global free_proxy_pool

    if not FREE_PROXY_AVAILABLE:
        logging.error('[PROXY] Free proxy library not available')
        return []

    try:
        print(f"[PROXY] Fetching {config.FREE_PROXY_FETCH_COUNT} free proxies (this may take 30-60 seconds)...")
        logging.info(f'[PROXY] Fetching {config.FREE_PROXY_FETCH_COUNT} free proxies')

        proxies = []
        attempts = 0
        max_attempts = config.FREE_PROXY_FETCH_COUNT * 3  # Try 3x as many times

        while len(proxies) < config.FREE_PROXY_FETCH_COUNT and attempts < max_attempts:
            attempts += 1
            try:
                print(f"[PROXY] Attempt {attempts}/{max_attempts} (found {len(proxies)} so far)...")

                # Get random free proxy with short timeout
                proxy_obj = FreeProxy(timeout=3, rand=True, https=False)  # Use http for speed
                proxy = proxy_obj.get()

                if proxy and proxy not in proxies:
                    proxies.append(proxy)
                    print(f"[PROXY] ✓ Fetched ({len(proxies)}/{config.FREE_PROXY_FETCH_COUNT}): {proxy}")
                    logging.info(f'[PROXY] Fetched free proxy {len(proxies)}/{config.FREE_PROXY_FETCH_COUNT}: {proxy}')

            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.debug(f'[PROXY] Attempt {attempts} failed: {e}')
                continue

        if proxies:
            print(f"[PROXY] ✓ Successfully fetched {len(proxies)} free proxies")
            logging.info(f'[PROXY] Successfully fetched {len(proxies)} free proxies')
        else:
            print("[PROXY] ✗ Failed to fetch any free proxies - will try without proxy")
            logging.warning('[PROXY] Failed to fetch any free proxies')

        return proxies

    except KeyboardInterrupt:
        print("\n[PROXY] Proxy fetching interrupted by user")
        raise
    except Exception as e:
        logging.error(f'[PROXY] Error fetching free proxies: {e}')
        print(f"[PROXY] ✗ Error fetching proxies: {e}")
        return []


def get_next_proxy() -> Optional[str]:
    """Get next proxy from the list (rotating)"""
    global current_proxy_index, free_proxy_pool

    if not config.PROXY_ENABLED:
        return None

    # Priority 1: Use single proxy if configured
    if config.SINGLE_PROXY:
        return config.SINGLE_PROXY

    # Priority 2: Use custom proxy list
    if config.PROXY_LIST:
        proxy = config.PROXY_LIST[current_proxy_index % len(config.PROXY_LIST)]
        current_proxy_index += 1
        return proxy

    # Priority 3: Use free proxies
    if config.USE_FREE_PROXIES and FREE_PROXY_AVAILABLE:
        # Fetch new proxies if pool is empty
        if not free_proxy_pool:
            free_proxy_pool = fetch_free_proxies()

        # Get next proxy from pool
        if free_proxy_pool:
            proxy = free_proxy_pool[current_proxy_index % len(free_proxy_pool)]
            current_proxy_index += 1
            return proxy

    logging.warning('[PROXY] PROXY_ENABLED=True but no proxies configured or available!')
    return None


async def scrape_single_page(context, page_url: str, page_num: int):
    """Scrape a single page and return products data"""
    page = await context.new_page()
    try:
        await page.goto(page_url, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(1)

        # Get page HTML and extract data
        html = await page.content()
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)

        if not match:
            logging.warning(f'[ERROR] Could not find __NEXT_DATA__ on page {page_num}')
            return []

        try:
            next_data = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            logging.error(f'[ERROR] Failed to parse __NEXT_DATA__ on page {page_num}: {e}')
            return []

        # Extract products from current page
        try:
            results = next_data['props']['pageProps']['results']
            organic = results['organic']
            products_data = organic['results']
            logging.info(f'[SCRAPE] Page {page_num}: Found {len(products_data)} products')
            return products_data
        except KeyError as e:
            logging.error(f'[ERROR] Unexpected data structure on page {page_num}: {e}')
            return []

    except Exception as e:
        logging.error(f'[ERROR] Failed to scrape page {page_num}: {e}')
        return []
    finally:
        await page.close()


async def scrape_products_playwright(page):
    """Scrape ALL products across all pages using Playwright (parallel loading)"""
    all_products = []

    try:
        # First, load page 1 to get total page count
        base_url = config.CATEGORY_URL
        logging.info(f'[SCRAPE] Loading page 1 to get page count...')
        await page.goto(base_url, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(2)

        # Get page count from first page
        try:
            await page.wait_for_selector('script#__NEXT_DATA__', timeout=20000)
        except PlaywrightTimeout:
            logging.warning('[SCRAPE] __NEXT_DATA__ selector timeout')

        html = await page.content()
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)

        if not match:
            logging.error('[ERROR] Could not find __NEXT_DATA__ in HTML')
            return []

        try:
            next_data = json.loads(match.group(1))
            page_count = next_data['props']['pageProps']['results']['organic'].get('pageCount', 1)
            logging.info(f'[SCRAPE] Total pages: {page_count}')
        except (KeyError, json.JSONDecodeError) as e:
            logging.error(f'[ERROR] Could not get page count: {e}')
            page_count = 1

        # Get browser context from the page
        context = page.context

        # Load all pages in parallel
        logging.info(f'[SCRAPE] Loading all {page_count} pages in parallel...')
        page_urls = [f"{base_url}?page={i}" for i in range(1, page_count + 1)]

        # Create tasks for parallel loading
        tasks = [scrape_single_page(context, url, i+1) for i, url in enumerate(page_urls)]
        all_pages_data = await asyncio.gather(*tasks)

        # Flatten all products from all pages
        all_products_data = []
        for page_data in all_pages_data:
            all_products_data.extend(page_data)

        logging.info(f'[SCRAPE] Loaded {len(all_products_data)} total products from {page_count} pages')

        # Parse products from all pages
        for prod_data in all_products_data:
            try:
                code = prod_data.get('code')
                name = prod_data.get('information', {}).get('name', 'Unknown')
                brand = prod_data.get('information', {}).get('brand', '')

                # Filter out marketplace items (productChannel == "IMP")
                # Only monitor Big W products (productChannel == "BIGW")
                fulfillment = prod_data.get('fulfillment', {})
                product_channel = fulfillment.get('productChannel', '')

                if product_channel == 'IMP':
                    logging.debug(f'[FILTER] Skipping marketplace item: {name}')
                    continue

                logging.debug(f'[PRODUCT] {name} | Channel: {product_channel}')

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

                all_products.append(product)

            except Exception as e:
                logging.error(f'[ERROR] Parsing product: {e}')
                continue

        logging.info(f'[SCRAPE] Extracted {len(all_products)} in-stock Big W products (marketplace items filtered)')
        return all_products

    except PlaywrightTimeout:
        logging.error('[ERROR] Page load timeout')
        return []
    except Exception as e:
        logging.error(f'[ERROR] Scraping failed: {e}')
        import traceback
        traceback.print_exc()
        return []


async def monitor():
    """Main monitor loop with Playwright"""
    global INSTOCK

    start = True  # Skip notifications on first run
    iteration = 0

    print("=" * 80)
    print("BIG W STOCK MONITOR - PLAYWRIGHT VERSION")
    print("=" * 80)
    print(f"Category URL: {config.CATEGORY_URL}")
    print(f"Delay: {config.DELAY} seconds")
    print(f"Keywords: {config.KEYWORDS if config.KEYWORDS else 'ALL'}")
    print(f"Webhook: {'Configured' if config.WEBHOOK != 'YOUR_DISCORD_WEBHOOK_URL_HERE' else 'NOT CONFIGURED!'}")
    print(f"Headless: {config.HEADLESS}")
    print("=" * 80)

    if config.WEBHOOK == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("[ERROR] Please configure your Discord webhook URL in config.py!")
        return

    async with async_playwright() as p:
        # Launch browser with enhanced anti-detection settings
        print("[BROWSER] Launching browser...")
        browser = await p.chromium.launch(
            headless=config.HEADLESS,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-http2',  # Disable HTTP/2 to avoid ERR_HTTP2_PROTOCOL_ERROR
                '--disable-gpu',
                '--window-size=1920,1080',
                '--disable-background-networking',
                '--disable-sync',
                '--metrics-recording-only',
                '--disable-default-apps',
                '--no-first-run',
                '--disable-setuid-sandbox',
                '--hide-scrollbars'
            ]
        )

        # Get initial proxy if enabled
        current_proxy = get_next_proxy()
        if current_proxy:
            print(f"[PROXY] Using proxy: {current_proxy}")
            logging.info(f'[PROXY] Using proxy: {current_proxy}')

        # Create context with realistic browser fingerprint
        context_options = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'en-AU',
            'timezone_id': 'Australia/Sydney',
            'permissions': ['geolocation']
        }

        # Add proxy if enabled
        if current_proxy:
            # Parse proxy URL to extract components
            if '@' in current_proxy:
                # Format: protocol://username:password@host:port
                protocol, rest = current_proxy.split('://')
                auth, server = rest.split('@')
                username, password = auth.split(':')
                context_options['proxy'] = {
                    'server': f'{protocol}://{server}',
                    'username': username,
                    'password': password
                }
            else:
                # Format: protocol://host:port
                context_options['proxy'] = {'server': current_proxy}

        context = await browser.new_context(**context_options)

        # Add stealth scripts to avoid detection
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-AU', 'en-US', 'en']
            });
        """)

        page = await context.new_page()
        print("[BROWSER] Browser ready!")

        try:
            proxy_errors = 0  # Track consecutive proxy errors

            while True:
                try:
                    iteration += 1
                    print(f"\n[MONITOR] Iteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                    # Scrape products using Playwright
                    products = await scrape_products_playwright(page)

                    if not products:
                        logging.warning('[WARNING] No products found in scrape')

                        # If proxy rotation is enabled and we hit retry limit
                        if config.PROXY_ENABLED and config.ROTATE_PROXY_ON_ERROR:
                            proxy_errors += 1
                            if proxy_errors >= config.PROXY_RETRY_LIMIT:
                                print(f"[PROXY] Failed after {proxy_errors} attempts, rotating proxy...")
                                logging.warning(f'[PROXY] Failed after {proxy_errors} attempts, rotating proxy')

                                # Declare global to modify it
                                global free_proxy_pool, current_proxy_index

                                # If using free proxies and we've tried all, fetch new batch
                                if config.USE_FREE_PROXIES and FREE_PROXY_AVAILABLE and free_proxy_pool:
                                    if current_proxy_index >= len(free_proxy_pool) * 2:  # Tried each proxy twice
                                        print("[PROXY] Exhausted free proxy pool, fetching new batch...")
                                        logging.info('[PROXY] Exhausted free proxy pool, fetching new batch')
                                        free_proxy_pool = fetch_free_proxies()
                                        current_proxy_index = 0

                                # Close current context and create new one with different proxy
                                await page.close()
                                await context.close()

                                # Get next proxy
                                current_proxy = get_next_proxy()
                                if current_proxy:
                                    print(f"[PROXY] Switching to proxy: {current_proxy}")
                                    logging.info(f'[PROXY] Switching to proxy: {current_proxy}')

                                # Create new context with new proxy
                                context_options = {
                                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                                    'viewport': {'width': 1920, 'height': 1080},
                                    'locale': 'en-AU',
                                    'timezone_id': 'Australia/Sydney',
                                    'permissions': ['geolocation']
                                }

                                if current_proxy:
                                    if '@' in current_proxy:
                                        protocol, rest = current_proxy.split('://')
                                        auth, server = rest.split('@')
                                        username, password = auth.split(':')
                                        context_options['proxy'] = {
                                            'server': f'{protocol}://{server}',
                                            'username': username,
                                            'password': password
                                        }
                                    else:
                                        context_options['proxy'] = {'server': current_proxy}

                                context = await browser.new_context(**context_options)
                                await context.add_init_script("""
                                    Object.defineProperty(navigator, 'webdriver', {
                                        get: () => undefined
                                    });
                                    Object.defineProperty(navigator, 'plugins', {
                                        get: () => [1, 2, 3, 4, 5]
                                    });
                                    Object.defineProperty(navigator, 'languages', {
                                        get: () => ['en-AU', 'en-US', 'en']
                                    });
                                """)
                                page = await context.new_page()
                                proxy_errors = 0  # Reset counter

                        await asyncio.sleep(config.DELAY)
                        continue

                    # Reset error counter on successful scrape
                    proxy_errors = 0

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

        except KeyboardInterrupt:
            print("\n[MONITOR] Stopping...")
            logging.info('[MONITOR] Stopped by user')
        finally:
            await context.close()
            await browser.close()
            print("[BROWSER] Browser closed")


if __name__ == '__main__':
    asyncio.run(monitor())
