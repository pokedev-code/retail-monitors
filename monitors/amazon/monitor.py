"""
Amazon Australia Stock Monitor - Playwright Version
Monitors Amazon.com.au search pages for new products/restocks
Uses Playwright for browser automation to bypass bot detection
"""
import asyncio
import logging
import re
import requests
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Dict, List, Optional
from urllib.parse import urljoin

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
INSTOCK = []  # List of product ASINs currently in stock


def discord_webhook(product: Dict) -> None:
    """Send Discord notification for new product - matches other monitors layout"""
    try:
        fields = []

        # Price field (first)
        if product.get('price'):
            fields.append({
                "name": "Price",
                "value": product['price'],
                "inline": False
            })

        # Rating field
        if product.get('rating'):
            fields.append({
                "name": "Rating",
                "value": f"⭐ {product['rating']} ({product.get('reviews', 'N/A')} reviews)",
                "inline": False
            })

        # Prime status
        if product.get('is_prime'):
            fields.append({
                "name": "Shipping",
                "value": "✓ Prime Eligible",
                "inline": False
            })

        # Stock Change field
        stock_status = product.get('stock_status', 'In Stock')
        fields.append({
            "name": "Stock Change",
            "value": stock_status,
            "inline": False
        })

        # Store field
        fields.append({
            "name": "Store",
            "value": "Amazon AU",
            "inline": False
        })

        # ASIN field
        if product.get('asin'):
            fields.append({
                "name": "ASIN",
                "value": product['asin'],
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
            "footer": {"text": "Amazon AU Stock Monitor"},
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add image if available
        if product.get('image'):
            embed["thumbnail"] = {"url": product['image']}

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


def matches_price_filter(price_str: Optional[str]) -> bool:
    """Check if product price is within configured range"""
    if not price_str:
        return config.MIN_PRICE is None and config.MAX_PRICE is None

    # Extract numeric price from string (e.g., "$45.99" -> 45.99)
    match = re.search(r'\$?([\d,]+\.?\d*)', price_str.replace(',', ''))
    if not match:
        return True  # Can't parse price, allow it

    try:
        price = float(match.group(1))

        if config.MIN_PRICE is not None and price < config.MIN_PRICE:
            logging.debug(f'[FILTER] Price too low: ${price} < ${config.MIN_PRICE}')
            return False

        if config.MAX_PRICE is not None and price > config.MAX_PRICE:
            logging.debug(f'[FILTER] Price too high: ${price} > ${config.MAX_PRICE}')
            return False

        return True
    except ValueError:
        return True  # Can't parse, allow it


async def scrape_products(page) -> List[Dict]:
    """Scrape products from Amazon search page"""
    all_products = []

    try:
        for page_num in range(1, config.MAX_PAGES + 1):
            # Build URL with page number
            if page_num == 1:
                url = config.SEARCH_URL
            else:
                # Amazon uses &page=N for pagination
                if '&page=' in config.SEARCH_URL:
                    url = re.sub(r'&page=\d+', f'&page={page_num}', config.SEARCH_URL)
                else:
                    url = f"{config.SEARCH_URL}&page={page_num}"

            logging.info(f'[SCRAPE] Loading page {page_num}: {url}')

            # Navigate to search page
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)  # Wait for dynamic content

            # Extract products using JavaScript
            products_data = await page.evaluate('''() => {
                const products = [];

                // Amazon uses div[data-asin] for product containers
                const productContainers = document.querySelectorAll('div[data-asin]:not([data-asin=""])');

                productContainers.forEach(container => {
                    try {
                        const asin = container.getAttribute('data-asin');
                        if (!asin) return;

                        // Extract title
                        let title = '';
                        const titleSelectors = [
                            'h2 a span',
                            'h2 span',
                            '.a-size-base-plus',
                            '.a-size-medium'
                        ];

                        for (const sel of titleSelectors) {
                            const elem = container.querySelector(sel);
                            if (elem && elem.textContent.trim()) {
                                title = elem.textContent.trim();
                                break;
                            }
                        }

                        if (!title) return;

                        // Extract URL
                        const linkElem = container.querySelector('h2 a, a.a-link-normal');
                        const url = linkElem ? linkElem.href : '';

                        // Extract price
                        let price = null;
                        const priceSelectors = [
                            '.a-price .a-offscreen',
                            '.a-price-whole',
                            'span.a-price'
                        ];

                        for (const sel of priceSelectors) {
                            const priceElem = container.querySelector(sel);
                            if (priceElem) {
                                let priceText = priceElem.textContent.trim();
                                if (sel === '.a-price .a-offscreen') {
                                    price = priceText;
                                    break;
                                } else {
                                    const match = priceText.match(/\\$?([\\d,]+\\.?\\d*)/);
                                    if (match) {
                                        price = `$${match[1]}`;
                                        break;
                                    }
                                }
                            }
                        }

                        // Extract rating
                        let rating = null;
                        let reviews = null;
                        const ratingElem = container.querySelector('span.a-icon-alt');
                        if (ratingElem) {
                            const ratingText = ratingElem.textContent.trim();
                            const match = ratingText.match(/([\\d.]+) out of 5/);
                            if (match) rating = match[1];
                        }

                        // Extract review count
                        const reviewElem = container.querySelector('span.a-size-base.s-underline-text, span[aria-label*="stars"]');
                        if (reviewElem) {
                            const reviewText = reviewElem.textContent.trim();
                            const match = reviewText.match(/([\\d,]+)/);
                            if (match) reviews = match[1];
                        }

                        // Check if Prime
                        const isPrime = container.querySelector('i.a-icon-prime, span.a-icon-prime') !== null;

                        // Check stock status
                        let stockStatus = 'In Stock';
                        const stockElem = container.querySelector('.a-color-price, .a-color-secondary');
                        if (stockElem) {
                            const stockText = stockElem.textContent.toLowerCase();
                            if (stockText.includes('out of stock') || stockText.includes('unavailable')) {
                                stockStatus = 'Out of Stock';
                            }
                        }

                        // Extract image
                        let image = null;
                        const imgElem = container.querySelector('img.s-image');
                        if (imgElem) {
                            image = imgElem.src || imgElem.getAttribute('data-src');
                        }

                        products.push({
                            asin: asin,
                            title: title,
                            url: url,
                            price: price,
                            rating: rating,
                            reviews: reviews,
                            is_prime: isPrime,
                            stock_status: stockStatus,
                            image: image
                        });

                    } catch (e) {
                        console.error('Error parsing product:', e);
                    }
                });

                return products;
            }''')

            logging.info(f'[SCRAPE] Page {page_num}: Found {len(products_data)} products')
            all_products.extend(products_data)

            # Don't navigate to next page if we didn't find any products (end of results)
            if len(products_data) == 0:
                logging.info(f'[SCRAPE] No products on page {page_num}, stopping pagination')
                break

            # Add delay between pages to avoid rate limiting
            if page_num < config.MAX_PAGES:
                await asyncio.sleep(2)

        logging.info(f'[SCRAPE] Total products found: {len(all_products)}')

        # Filter products
        filtered_products = []
        for product in all_products:
            # Skip if only monitoring in-stock and product is out of stock
            if config.ONLY_IN_STOCK and product['stock_status'] == 'Out of Stock':
                continue

            # Skip if only monitoring Prime and product is not Prime
            if config.PRIME_ONLY and not product['is_prime']:
                continue

            # Apply keyword filters
            if not matches_filters(product['title']) or not matches_keywords(product['title']):
                continue

            # Apply price filter
            if not matches_price_filter(product['price']):
                continue

            filtered_products.append(product)

        logging.info(f'[FILTER] {len(filtered_products)} products after filtering')
        return filtered_products

    except PlaywrightTimeout:
        logging.error('[ERROR] Page load timeout')
        return []
    except Exception as e:
        logging.error(f'[ERROR] Scraping failed: {e}')
        import traceback
        traceback.print_exc()
        return []


async def monitor():
    """Main monitoring loop"""
    global INSTOCK

    start = True  # Skip notifications on first run
    iteration = 0

    print("=" * 80)
    print("AMAZON AU STOCK MONITOR - PLAYWRIGHT VERSION")
    print("=" * 80)
    print(f"Search URL: {config.SEARCH_URL}")
    print(f"Delay: {config.DELAY} seconds")
    print(f"Keywords: {config.KEYWORDS if config.KEYWORDS else 'ALL'}")
    print(f"Prime Only: {config.PRIME_ONLY}")
    print(f"In Stock Only: {config.ONLY_IN_STOCK}")
    print(f"Max Pages: {config.MAX_PAGES}")
    if config.MIN_PRICE or config.MAX_PRICE:
        print(f"Price Range: ${config.MIN_PRICE or 0} - ${config.MAX_PRICE or '∞'}")
    print(f"Webhook: {'Configured' if config.WEBHOOK != 'YOUR_DISCORD_WEBHOOK_URL_HERE' else 'NOT CONFIGURED!'}")
    print(f"Headless: {config.HEADLESS}")
    print("=" * 80)

    if config.WEBHOOK == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        print("[ERROR] Please configure your Discord webhook URL in config.py!")
        return

    async with async_playwright() as p:
        # Launch browser with anti-detection settings
        print("[BROWSER] Launching browser...")
        browser = await p.chromium.launch(
            headless=config.HEADLESS,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
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

        # Create context with realistic browser fingerprint
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney',
            permissions=['geolocation']
        )

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
            while True:
                try:
                    iteration += 1
                    print(f"\n[MONITOR] Iteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                    # Scrape products
                    products = await scrape_products(page)

                    if not products:
                        logging.warning('[WARNING] No products found in scrape')
                        await asyncio.sleep(config.DELAY)
                        continue

                    # Process each product
                    current_asins = []
                    for product in products:
                        asin = product['asin']
                        current_asins.append(asin)

                        # Check if new product
                        if asin not in INSTOCK:
                            INSTOCK.append(asin)

                            if not start:
                                logging.info(f'[NEW] {product["title"]} - {product["price"]}')
                                print(f'[NEW] {product["title"]} - {product["price"]}')
                                discord_webhook(product)
                            else:
                                logging.info(f'[INITIAL] Tracking: {product["title"]}')

                    # Remove products no longer in stock
                    removed = [asin for asin in INSTOCK if asin not in current_asins]
                    for asin in removed:
                        INSTOCK.remove(asin)
                        logging.info(f'[OOS] Product removed from tracking: {asin}')

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
