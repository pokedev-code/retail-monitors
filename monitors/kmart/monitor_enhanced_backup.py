"""
Kmart Australia Monitor - Enhanced Playwright Version with GraphQL Stock API
Monitors Kmart category pages and uses GraphQL API for exact stock quantities
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import List, Dict, Optional
import requests

from config import (WEBHOOK, DELAY, KEYWORDS, USERNAME, AVATAR_URL, COLOUR,
                   URL, STATE, ENABLE_EBAY_LINKS, STATE_WEBHOOKS)

logging.basicConfig(
    filename='kmart-monitor.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(message)s',
    level=logging.DEBUG
)

INSTOCK = {}  # Changed to dict to track per-state stock: {product_key: {state: stock_info}}
REQUEST_COUNT = 0
ERROR_COUNT = 0


def check_url(url: str) -> bool:
    """Checks whether the supplied URL is valid for Kmart"""
    return 'kmart.com.au' in url


async def get_stock_for_all_states(page, product_url: str, product_id: str) -> Dict[str, Dict]:
    """
    Fetch exact stock quantities for ALL Australian states
    Returns dict with state as key and stock info as value
    """
    # Postcode mapping for each Australian state
    STATE_POSTCODES = {
        'NSW': '2000',
        'VIC': '3000',
        'QLD': '4000',
        'SA': '5000',
        'WA': '6000',
        'TAS': '7000',
        'NT': '0800',
        'ACT': '2600'
    }

    all_states_stock = {}

    try:
        logging.info(f'[GraphQL] Fetching stock for all states for product {product_id}')

        for state, postcode in STATE_POSTCODES.items():
            graphql_data = {}
            graphql_received = asyncio.Event()

            # Set up GraphQL response interceptor
            async def handle_graphql_response(response):
                nonlocal graphql_data
                if 'graphql' in response.url and response.status == 200:
                    try:
                        data = await response.json()
                        if 'getProductAvailability' in str(data):
                            graphql_data = data
                            graphql_received.set()
                            logging.info(f'[GraphQL] Captured stock API response for {state}')
                    except Exception as e:
                        logging.debug(f'[GraphQL] Could not parse response: {e}')

            page.on('response', handle_graphql_response)

            # Navigate to product page with state-specific postcode
            try:
                # Add postcode to URL to get state-specific stock
                url_with_postcode = f"{product_url}?postcode={postcode}"
                await page.goto(url_with_postcode, wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(2)  # Wait for API calls

                # Wait for GraphQL response (with timeout)
                try:
                    await asyncio.wait_for(graphql_received.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logging.warning(f'[GraphQL] Timeout waiting for stock API for {product_id} in {state}')
                    page.remove_listener('response', handle_graphql_response)
                    continue

            except Exception as e:
                logging.error(f'[GraphQL] Error fetching stock for {state}: {e}')
                page.remove_listener('response', handle_graphql_response)
                continue

            page.remove_listener('response', handle_graphql_response)

            # Parse GraphQL response for this state
            if graphql_data:
                availability = graphql_data.get('data', {}).get('getProductAvailability', {}).get('availability', {})

                # Extract stock data
                stock_info = {
                    'online': 0,
                    'instore': 0,
                    'locations': [],
                    'state': state,
                    'postcode': postcode
                }

                # Home Delivery (Online)
                home_delivery = availability.get('HOME_DELIVERY', [])
                if home_delivery:
                    stock_info['online'] = home_delivery[0].get('stock', {}).get('available', 0)

                # Click & Collect (In-Store)
                click_collect = availability.get('CLICK_AND_COLLECT', [])
                if click_collect:
                    stock_info['instore'] = click_collect[0].get('stock', {}).get('totalAvailable', 0)

                    # Get per-location stock
                    locations = click_collect[0].get('locations', [])
                    for loc in locations:
                        loc_id = loc.get('fulfilment', {}).get('locationId')
                        loc_stock = loc.get('fulfilment', {}).get('stock', {}).get('available', 0)
                        if loc_stock > 0:
                            stock_info['locations'].append({
                                'id': loc_id,
                                'stock': loc_stock
                            })

                all_states_stock[state] = stock_info
                logging.info(f'[GraphQL] {state} Stock for {product_id}: Online={stock_info["online"]}, In-Store={stock_info["instore"]}')
            else:
                logging.warning(f'[GraphQL] No stock data received for {product_id} in {state}')

        return all_states_stock

    except Exception as e:
        logging.error(f'[GraphQL] Error fetching stock for all states: {e}')
        return {}


async def scrape_site(page, url: str, retry_count: int = 0) -> List[Dict]:
    """
    Scrapes Kmart category page and fetches stock data via GraphQL
    """
    global REQUEST_COUNT, ERROR_COUNT
    items = []
    max_retries = 2

    try:
        logging.info(f'Scraping: {url} (attempt {retry_count + 1})')
        REQUEST_COUNT += 1

        # Navigate with optimized wait strategy
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        except PlaywrightTimeout:
            logging.warning(f'Page load timeout for {url}')
            if retry_count < max_retries:
                await asyncio.sleep(2)
                return await scrape_site(page, url, retry_count + 1)
            ERROR_COUNT += 1
            raise

        # Wait for content to be present (script tags are hidden by default)
        try:
            await page.wait_for_selector('script[type="application/ld+json"]', state='attached', timeout=15000)
        except PlaywrightTimeout:
            logging.warning('No products found on page')
            return []

        # Kmart uses PAGINATION + INFINITE SCROLL per page
        # Need to: 1) Scroll each page to load all products, 2) Click through pages, 3) Extract from DOM
        logging.info('Collecting products from all pages...')

        all_dom_products = []
        current_page = 1
        max_pages = 5

        while current_page <= max_pages:
            logging.info(f'Processing page {current_page}...')

            # Fast scroll to load all products (scroll to bottom in large chunks)
            for _ in range(10):
                await page.evaluate('window.scrollBy(0, 1000)')
                await asyncio.sleep(0.4)  # Slightly longer for reliability

            # Final check - scroll to absolute bottom twice to ensure everything loaded
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(0.5)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(0.5)

            # Count products
            count = await page.evaluate('''() => {
                const grid = document.querySelector('[class*="grid" i], [class*="list" i], main');
                if (!grid) return 0;
                return grid.querySelectorAll('[data-testid*="product"], [data-product-id]').length;
            }''')

            logging.info(f'Page {current_page}: Loaded {count} products')

            # Extract products from this page
            page_products = await page.evaluate('''() => {
                const grid = document.querySelector('[class*="grid" i], [class*="list" i], main');
                if (!grid) return [];

                const productCards = Array.from(grid.querySelectorAll('[data-testid*="product"], [data-product-id]')).filter(el => {
                    return el.querySelector('a[href*="/product/"]') !== null;
                });

                const products = [];
                const seen = new Set();

                productCards.forEach(card => {
                    const link = card.querySelector('a[href*="/product/"]') || (card.tagName === 'A' ? card : null);
                    if (!link) return;

                    const url = link.href;
                    if (seen.has(url)) return;
                    seen.add(url);

                    const titleEl = card.querySelector('[class*="title" i], h2, h3, [data-testid*="title"]');
                    const priceEl = card.querySelector('[class*="price" i], [data-testid*="price"]');
                    const imageEl = card.querySelector('img[data-testid*="image"], img');

                    products.push({
                        url: url,
                        title: titleEl ? titleEl.innerText.trim() : '',
                        price: priceEl ? priceEl.innerText.trim() : '',
                        image: imageEl ? (imageEl.src || imageEl.dataset.src || '') : ''
                    });
                });

                return products;
            }''')

            all_dom_products.extend(page_products)
            logging.info(f'Page {current_page}: Extracted {len(page_products)} products (total so far: {len(all_dom_products)})')

            # Try to go to next page
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)

            next_page_num = current_page + 1
            next_button = await page.query_selector(f'button.MuiPaginationItem-page:has-text("{next_page_num}")')

            if next_button and await next_button.is_visible() and not await next_button.is_disabled():
                logging.info(f'Clicking page {next_page_num}...')
                await next_button.click()
                await asyncio.sleep(3)
                current_page += 1
            else:
                logging.info(f'No more pages (completed {current_page} pages)')
                break

        dom_products = all_dom_products
        logging.info(f'Total products extracted from {current_page} pages: {len(dom_products)}')

        # Convert DOM products to our format and process them
        for dom_product in dom_products:
            try:
                product_item = {
                    'title': dom_product.get('title', 'Unknown'),
                    'url': dom_product.get('url', ''),
                    'image': dom_product.get('image', ''),
                    'price': dom_product.get('price'),
                    'stock_info': None,
                    'sku': None
                }

                # Extract SKU from URL
                url_match = re.search(r'/(\d+)/?$', product_item['url'])
                if url_match:
                    sku = url_match.group(1)
                    product_item['sku'] = sku

                    # Fetch stock data for ALL states from GraphQL API
                    full_url = product_item['url'] if product_item['url'].startswith('http') else f"https://www.kmart.com.au{product_item['url']}"
                    all_states_stock = await get_stock_for_all_states(page, full_url, sku)
                    if all_states_stock:
                        product_item['all_states_stock'] = all_states_stock

                items.append(product_item)

            except (KeyError, AttributeError) as e:
                logging.error(f"Error parsing product: {e}")
                continue

        # Fallback: Scrape product cards if JSON-LD didn't work
        if not items:
            logging.info('JSON-LD not found, using fallback scraping')

            cards = await page.evaluate('''() => {
                const products = [];
                const selectors = [
                    'div[class*="ProductCard"]',
                    'div[class*="product-card"]',
                    'div[data-testid*="product"]',
                    'article',
                    'li[class*="product"]',
                    'div[class*="product"]'
                ];

                let productCards = [];
                for (const selector of selectors) {
                    productCards = Array.from(document.querySelectorAll(selector));
                    if (productCards.length > 0) break;
                }

                productCards.forEach((card, index) => {
                    try {
                        let title = '';
                        const titleSelectors = [
                            '[class*="title"]', '[class*="name"]', '[class*="product"]',
                            'h2', 'h3', 'h4', 'a'
                        ];

                        for (const sel of titleSelectors) {
                            const elem = card.querySelector(sel);
                            if (elem && elem.textContent.trim()) {
                                title = elem.textContent.trim();
                                if (title.length > 3) break;
                            }
                        }

                        const link = card.querySelector('a[href]');
                        let url = link ? link.href : '';

                        const img = card.querySelector('img');
                        const image = img ? (img.src || img.dataset.src || img.getAttribute('data-src') || '') : '';

                        let price = null;
                        const priceSelectors = [
                            '[class*="price"]', '[class*="amount"]',
                            '[class*="cost"]', '[data-testid*="price"]'
                        ];

                        for (const sel of priceSelectors) {
                            const priceElem = card.querySelector(sel);
                            if (priceElem) {
                                const priceText = priceElem.textContent.trim();
                                const match = priceText.match(/\\$?(\\d+(?:\\.\\d{2})?)/)
                                if (match) {
                                    price = match[1];
                                    break;
                                }
                            }
                        }

                        if (url && !url.startsWith('http')) {
                            url = 'https://www.kmart.com.au' + url;
                        }

                        if (title && url) {
                            products.push({
                                title: title,
                                url: url,
                                image: image,
                                position: index + 1,
                                price: price
                            });
                        }
                    } catch(e) {
                        console.error('Error parsing card:', e);
                    }
                });

                return products;
            }''')

            # Fetch stock for fallback products
            for product in cards:
                url_match = re.search(r'/(\d+)/?$', product['url'])
                if url_match:
                    sku = url_match.group(1)
                    product['sku'] = sku
                    all_states_stock = await get_stock_for_all_states(page, product['url'], sku)
                    if all_states_stock:
                        product['all_states_stock'] = all_states_stock

                    # Try to get better quality image from product page if image is missing
                    if not product.get('image') or 'placeholder' in product.get('image', '').lower():
                        try:
                            better_image = await page.evaluate('''() => {
                                const selectors = [
                                    'meta[property="og:image"]',
                                    'img[class*="ProductImage"]',
                                    'img[class*="product-image"]',
                                    'img[data-testid*="product"]',
                                    '.product-image img',
                                    'picture img'
                                ];

                                for (const sel of selectors) {
                                    const elem = document.querySelector(sel);
                                    if (elem) {
                                        if (elem.tagName === 'META') {
                                            return elem.content;
                                        } else {
                                            return elem.src || elem.dataset.src || elem.getAttribute('data-src');
                                        }
                                    }
                                }
                                return null;
                            }''')

                            if better_image:
                                product['image'] = better_image
                        except Exception as e:
                            logging.debug(f'Could not extract better image for fallback product: {e}')

            items = cards

        logging.info(f'Successfully scraped {len(items)} products')
        return items

    except Exception as e:
        ERROR_COUNT += 1
        logging.error(f'Error scraping site: {str(e)}')

        # Retry with exponential backoff
        if retry_count < max_retries:
            await asyncio.sleep(2 ** retry_count)
            return await scrape_site(page, url, retry_count + 1)

        return []


def get_product_key(product: Dict) -> str:
    """Generate a unique key for the product"""
    return f"{product['title']}|{product['url']}"


def discord_webhook(title: str, url: str, thumbnail: str, price: Optional[str] = None,
                    stock_info: Optional[Dict] = None, state_name: Optional[str] = None,
                    webhook_url: Optional[str] = None) -> None:
    """Sends a Discord webhook notification matching the reference format"""

    # Determine which webhook to use
    if webhook_url:
        # Use provided webhook URL
        target_webhook = webhook_url
    elif state_name and STATE_WEBHOOKS and state_name in STATE_WEBHOOKS:
        # Use state-specific webhook if available
        target_webhook = STATE_WEBHOOKS.get(state_name)
        # If state webhook is None or empty, use fallback
        if not target_webhook:
            target_webhook = WEBHOOK
            logging.info(f"No webhook configured for {state_name}, using fallback webhook")
    else:
        # Use default webhook
        target_webhook = WEBHOOK

    fields = []

    # State field - use state_name if provided, otherwise fall back to config STATE
    fields.append({
        "name": "State",
        "value": state_name if state_name else STATE,
        "inline": False
    })

    # Stock Change field with exact quantities
    if stock_info:
        online_qty = stock_info.get('online', 0)
        instore_qty = stock_info.get('instore', 0)

        fields.append({
            "name": "Stock Change",
            "value": f"Online: {online_qty}\nIn-Store: {instore_qty}",
            "inline": False
        })
    else:
        # Fallback if no stock info
        fields.append({
            "name": "Stock Change",
            "value": "Online: Checking...\nIn-Store: Checking...",
            "inline": False
        })

    # Store
    fields.append({
        "name": "Store",
        "value": "Kmart",
        "inline": False
    })

    # eBay Links
    if ENABLE_EBAY_LINKS:
        search_query = title.replace(' ', '+')
        ebay_current = f"https://www.ebay.com.au/sch/i.html?_nkw={search_query}&LH_BIN=1"
        ebay_sold = f"https://www.ebay.com.au/sch/i.html?_nkw={search_query}&LH_Complete=1&LH_Sold=1"

        fields.append({
            "name": "eBay Links",
            "value": f"[Current Listings]({ebay_current}) | [Sold Listings]({ebay_sold})",
            "inline": False
        })

    data = {
        "username": USERNAME,
        "avatar_url": AVATAR_URL,
        "embeds": [{
            "title": title,
            "url": url,
            "thumbnail": {"url": thumbnail},
            "fields": fields,
            "color": int(COLOUR),
            "footer": {"text": "Kmart Stock Monitor"},
            "timestamp": datetime.utcnow().isoformat(),
        }]
    }

    try:
        result = requests.post(target_webhook, json=data, timeout=10)
        result.raise_for_status()
        print(f"Notification sent successfully to {state_name if state_name else 'default'} webhook, code {result.status_code}")
        logging.info(f"Notification sent successfully to {state_name if state_name else 'default'} webhook, code {result.status_code}")
    except requests.exceptions.HTTPError as err:
        logging.error(f"Webhook error for {state_name if state_name else 'default'}: {err}")
    except requests.exceptions.Timeout:
        logging.error(f"Webhook timeout for {state_name if state_name else 'default'}")


def comparitor(product: Dict, start: bool) -> None:
    """Compares product against INSTOCK dict and detects per-state stock changes"""
    product_key = get_product_key(product)
    all_states_stock = product.get('all_states_stock', {})

    # Initialize product entry if it doesn't exist
    if product_key not in INSTOCK:
        INSTOCK[product_key] = {}

    # Track if we should send a main notification (for new products or overall stock changes)
    should_notify_main = False
    states_with_changes = []

    # Process each state individually
    for state, current_stock_info in all_states_stock.items():
        state_had_stock_before = state in INSTOCK[product_key]

        if not state_had_stock_before:
            # New state or new product for this state
            INSTOCK[product_key][state] = current_stock_info

            if not start:
                # Check if there's actually stock to notify about
                online_qty = current_stock_info.get('online', 0)
                instore_qty = current_stock_info.get('instore', 0)

                if online_qty > 0 or instore_qty > 0:
                    print(f"NEW PRODUCT [{state}]: {product['title']} - Online: {online_qty}, In-Store: {instore_qty}")
                    should_notify_main = True
                    states_with_changes.append((state, current_stock_info))

        else:
            # State exists, check if stock changed
            old_stock_info = INSTOCK[product_key][state]

            if current_stock_info != old_stock_info:
                # Stock changed for this state
                old_online = old_stock_info.get('online', 0)
                old_instore = old_stock_info.get('instore', 0)
                new_online = current_stock_info.get('online', 0)
                new_instore = current_stock_info.get('instore', 0)

                # Update stored stock
                INSTOCK[product_key][state] = current_stock_info

                if not start:
                    # Only notify if stock increased
                    if new_online > old_online or new_instore > old_instore:
                        print(f"STOCK CHANGE [{state}]: {product['title']} - Online: {old_online}→{new_online}, In-Store: {old_instore}→{new_instore}")
                        should_notify_main = True
                        states_with_changes.append((state, current_stock_info))

    # Send notifications
    if should_notify_main and not start:
        # First, send to main unfiltered webhook (combined stock from all states)
        # Calculate total stock across all states
        total_online = sum(stock.get('online', 0) for stock in all_states_stock.values())
        total_instore = sum(stock.get('instore', 0) for stock in all_states_stock.values())

        combined_stock_info = {
            'online': total_online,
            'instore': total_instore,
            'state': 'All States'
        }

        print(f"  → Main channel: All States (Online: {total_online}, In-Store: {total_instore})")
        discord_webhook(
            title=product['title'],
            url=product['url'],
            thumbnail=product['image'],
            price=product.get('price'),
            stock_info=combined_stock_info,
            state_name=None  # No state name for main webhook
        )
        logging.info(f'Sent notification to main webhook for: {product["title"]}')

        # Then send state-specific notifications
        for state, stock_info in states_with_changes:
            discord_webhook(
                title=product['title'],
                url=product['url'],
                thumbnail=product['image'],
                price=product.get('price'),
                stock_info=stock_info,
                state_name=state
            )
            logging.info(f'Sent notification for: {product["title"]} in {state}')


async def monitor():
    """Initiates the enhanced monitor with Playwright and GraphQL stock API"""
    global REQUEST_COUNT, ERROR_COUNT

    print('''\n-----------------------------------
--- KMART AU MONITOR (ENHANCED) ---
---     WITH GRAPHQL STOCK API    ---
-----------------------------------\n''')
    logging.info('Started Kmart AU monitor (Enhanced Version with GraphQL)')

    if not check_url(URL):
        print('Store URL not in correct format. Please ensure that it is a Kmart Australia URL')
        logging.error(f'Store URL formatting incorrect for: {URL}')
        return

    print(f'Monitoring: {URL}')
    print(f'Keywords: {KEYWORDS if KEYWORDS else "ALL PRODUCTS"}')
    print(f'State: {STATE}')
    print(f'Delay: {DELAY}s\n')

    start = True

    async with async_playwright() as p:
        # Launch browser with optimized settings
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # Create context with proper configuration
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney',
            extra_http_headers={
                'Accept-Language': 'en-AU,en-US;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
        )

        page = await context.new_page()

        try:
            iteration = 0
            while True:
                iteration += 1
                try:
                    # Scrape the site
                    items = await scrape_site(page, URL)

                    # Filter by keywords
                    for product in items:
                        if KEYWORDS == []:
                            # No keywords, monitor all products
                            comparitor(product, start)
                        else:
                            # Check if any keyword matches
                            for key in KEYWORDS:
                                if key.lower() in product['title'].lower():
                                    comparitor(product, start)
                                    break  # Only process once per product

                    start = False

                    # Performance metrics
                    error_rate = (ERROR_COUNT / REQUEST_COUNT * 100) if REQUEST_COUNT > 0 else 0
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] Iteration {iteration} | Products: {len(items)} | Requests: {REQUEST_COUNT} | Errors: {ERROR_COUNT} ({error_rate:.1f}%)")

                except Exception as e:
                    print(f"Error during monitoring: {e}")
                    logging.error(f"Error: {e}")

                await asyncio.sleep(float(DELAY))

        except KeyboardInterrupt:
            print('\n[MONITOR] Stopped by user')
            logging.info('[MONITOR] Stopped by user')
        finally:
            await context.close()
            await browser.close()


if __name__ == '__main__':
    asyncio.run(monitor())
