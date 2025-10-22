"""
EB Games Stock Monitor - Playwright Version
Monitors EB Games search pages for new products/restocks
Uses Playwright for browser automation to bypass bot protection
"""
import asyncio
import logging
import re
import requests
from datetime import datetime
from playwright.async_api import async_playwright
from typing import Dict, List

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
INSTOCK = []  # List of product IDs currently in stock


def discord_webhook(product: Dict) -> None:
    """Send Discord notification for new product - matches Kmart/Big W layout"""
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
        stock_status = product.get('stock_status', 'Available')
        fields.append({
            "name": "Stock Change",
            "value": stock_status,
            "inline": False
        })

        # Store field
        fields.append({
            "name": "Store",
            "value": "EB Games",
            "inline": False
        })

        # Product Code field
        if product.get('product_id'):
            fields.append({
                "name": "Product Code",
                "value": product['product_id'],
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
            "footer": {"text": "EB Games Stock Monitor"},
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


def clean_title(title: str) -> str:
    """Clean up product title by removing price, preorder text, and delivery info"""
    # Remove prices at the start (e.g., "$65.00" or "$65.00 ($10.00 deposit)")
    title = re.sub(r'^\$[\d.]+\s*(\([^)]+\))?\s*', '', title)
    # Remove PREORDER and everything after it
    title = re.sub(r'\s*PREORDER.*$', '', title, flags=re.IGNORECASE)
    # Remove delivery/collect at the end
    title = re.sub(r'\s*Delivery\s*Collect\s*$', '', title, flags=re.IGNORECASE)
    # Remove "Trading Cards" text
    title = re.sub(r'\s*Trading Cards\s*', ' ', title, flags=re.IGNORECASE)
    # Clean up extra whitespace
    title = re.sub(r'\s+', ' ', title).strip()
    return title


async def scrape_products(page) -> List[Dict]:
    """Scrape products from EB Games search page"""
    products = []

    try:
        logging.info(f'[SCRAPE] Loading {config.SEARCH_URL}')

        # Navigate to search page
        await page.goto(config.SEARCH_URL, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(3)  # Wait for dynamic content

        # Extract products using JavaScript
        products_data = await page.evaluate('''() => {
            const products = [];

            // Try to find product cards - EB Games uses various selectors
            const selectors = [
                '.product-tile',
                '.product-card',
                '[data-product-id]',
                'article',
                '.product-item'
            ];

            let productElements = [];
            for (const selector of selectors) {
                productElements = Array.from(document.querySelectorAll(selector));
                if (productElements.length > 0) break;
            }

            productElements.forEach(card => {
                try {
                    // Extract title - look for specific title element, not all text
                    let title = '';
                    const titleSelectors = [
                        '.name',                    // EB Games uses div.name
                        '.product-name',
                        '.product-title',
                        '[class*="product-name"]',
                        'a[class*="name"]',
                        'h3',
                        'h2',
                        'h4'
                    ];

                    for (const sel of titleSelectors) {
                        const elem = card.querySelector(sel);
                        if (elem && elem.textContent.trim()) {
                            let text = elem.textContent.trim();

                            if (text.length > 10) {
                                title = text;
                                break;
                            }
                        }
                    }


                    // Extract URL
                    const linkElem = card.querySelector('a[href]');
                    let url = linkElem ? linkElem.href : '';

                    // Extract product ID from URL or data attribute
                    let productId = card.getAttribute('data-product-id');
                    if (!productId && url) {
                        const match = url.match(/\\/(\\d+)-/);
                        if (match) productId = match[1];
                    }

                    // Extract price
                    let price = null;
                    const priceSelectors = ['.price', '[class*="price"]', '[data-price]'];
                    for (const sel of priceSelectors) {
                        const priceElem = card.querySelector(sel);
                        if (priceElem) {
                            const priceText = priceElem.textContent.trim();
                            const match = priceText.match(/\\$?(\\d+\\.?\\d*)/);
                            if (match) {
                                price = `$${match[1]}`;
                                break;
                            }
                        }
                    }

                    // Extract stock status
                    let stockStatus = 'Available';
                    const stockSelectors = [
                        'button[class*="preorder"]',
                        '[class*="availability"]',
                        '[class*="stock"]',
                        'button'
                    ];

                    for (const sel of stockSelectors) {
                        const elem = card.querySelector(sel);
                        if (elem) {
                            const text = elem.textContent.trim().toLowerCase();
                            if (text.includes('preorder') || text.includes('pre-order')) {
                                stockStatus = 'PreOrder';
                                break;
                            } else if (text.includes('out of stock')) {
                                stockStatus = 'Out of Stock';
                                break;
                            } else if (text.includes('add to cart')) {
                                stockStatus = 'In Stock';
                                break;
                            }
                        }
                    }

                    // Extract image
                    let image = null;
                    const imgElem = card.querySelector('img');
                    if (imgElem) {
                        image = imgElem.src || imgElem.getAttribute('data-src');
                    }

                    if (title && url && productId) {
                        products.push({
                            title: title,
                            url: url,
                            product_id: productId,
                            price: price,
                            stock_status: stockStatus,
                            image: image
                        });
                    }
                } catch (e) {
                    console.error('Error parsing product:', e);
                }
            });

            return products;
        }''')

        logging.info(f'[SCRAPE] Found {len(products_data)} products')

        # Filter products and clean titles
        for product in products_data:
            if matches_filters(product['title']) and matches_keywords(product['title']):
                # Clean up the title
                product['title'] = clean_title(product['title'])
                products.append(product)

        logging.info(f'[FILTER] {len(products)} products after filtering')

        return products

    except Exception as e:
        logging.error(f'[ERROR] Scraping failed: {e}')
        return []


def comparitor(product: Dict, start: bool) -> None:
    """Compare product against INSTOCK list and send notifications"""
    product_id = product['product_id']

    if product_id not in INSTOCK:
        # New product or restock
        INSTOCK.append(product_id)

        if not start:
            # Don't send notifications on initial scrape
            logging.info(f'[RESTOCK] {product["title"]} - {product["stock_status"]}')
            discord_webhook(product)
        else:
            logging.info(f'[INITIAL] {product["title"]} - {product["stock_status"]}')


async def monitor():
    """Main monitoring loop"""
    global INSTOCK

    logging.info('=' * 80)
    logging.info('EB Games Monitor Starting')
    logging.info('=' * 80)
    logging.info(f'Monitoring: {config.SEARCH_URL}')
    logging.info(f'Delay: {config.DELAY} seconds')
    logging.info(f'Headless: {config.HEADLESS}')
    logging.info('=' * 80)

    start = True

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=config.HEADLESS)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        try:
            while True:
                try:
                    # Scrape products
                    products = await scrape_products(page)

                    if products:
                        # Check for new/restocked products
                        current_ids = [p['product_id'] for p in products]

                        # Remove products no longer in stock
                        INSTOCK[:] = [pid for pid in INSTOCK if pid in current_ids]

                        # Check for new products
                        for product in products:
                            comparitor(product, start)

                        if start:
                            start = False
                            logging.info(f'[INITIAL] Loaded {len(INSTOCK)} products into tracking')

                    else:
                        logging.warning('[WARNING] No products found')

                    # Wait before next scrape
                    logging.info(f'[SLEEP] Waiting {config.DELAY} seconds...')
                    await asyncio.sleep(config.DELAY)

                except Exception as e:
                    logging.error(f'[ERROR] Monitor loop error: {e}')
                    await asyncio.sleep(30)  # Wait before retrying

        finally:
            await browser.close()


if __name__ == '__main__':
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        logging.info('\n[EXIT] Monitor stopped by user')
    except Exception as e:
        logging.error(f'[ERROR] Fatal error: {e}')
