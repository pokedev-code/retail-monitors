"""
Kmart Pokemon Card Monitor - API Interception Method
Uses Constructor.io API interception for instant, accurate scraping (similar to Target monitor)
"""
import asyncio
import logging
import re
from typing import Dict, List
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE if hasattr(config, 'LOG_FILE') else 'kmart-monitor.log'),
        logging.StreamHandler()
    ]
)

# Global state
INSTOCK = {}
REQUEST_COUNT = 0
ERROR_COUNT = 0


async def get_stock_for_all_states(page, product_url: str, sku: str) -> Dict:
    """
    Fetch stock for ALL Australian states using Kmart's GraphQL API
    """
    states_to_check = ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT']
    all_states_stock = {}

    try:
        # Navigate to product page to set up GraphQL context
        await page.goto(product_url, wait_until='domcontentloaded', timeout=10000)
        await asyncio.sleep(0.5)

        # Query GraphQL for all states
        for state in states_to_check:
            postcode = {'NSW': '2000', 'VIC': '3000', 'QLD': '4000', 'SA': '5000',
                       'WA': '6000', 'TAS': '7000', 'NT': '0800', 'ACT': '2600'}[state]

            graphql_url = f"https://api.kmart.com.au/gateway/graphql?articleNumber={sku}&state={state}&postcode={postcode}"

            graphql_data = await page.evaluate(f'''
                fetch('{graphql_url}')
                    .then(r => r.json())
                    .catch(() => null)
            ''')

            if graphql_data:
                availability = graphql_data.get('data', {}).get('getProductAvailability', {}).get('availability', {})

                stock_info = {'online': 0, 'instore': 0, 'state': state, 'postcode': postcode}

                home_delivery = availability.get('HOME_DELIVERY', [])
                if home_delivery:
                    stock_info['online'] = home_delivery[0].get('stock', {}).get('available', 0)

                click_collect = availability.get('CLICK_AND_COLLECT', [])
                if click_collect:
                    stock_info['instore'] = click_collect[0].get('stock', {}).get('totalAvailable', 0)

                all_states_stock[state] = stock_info

        return all_states_stock
    except Exception as e:
        logging.error(f'[GraphQL] Error fetching stock: {e}')
        return {}


async def scrape_products(page, url: str) -> List[Dict]:
    """
    Scrape products using Constructor.io API interception
    """
    global REQUEST_COUNT, ERROR_COUNT
    api_products = {}

    # Set up API interceptor
    async def capture_api(response):
        nonlocal api_products
        try:
            if 'ac.cnstrc.com/browse/group_id' in response.url and response.status == 200:
                data = await response.json()
                page_match = re.search(r'[?&]page=(\d+)', response.url)
                page_num = int(page_match.group(1)) if page_match else 1
                results = data.get('response', {}).get('results', [])
                api_products[page_num] = results
                logging.info(f'[API] Captured page {page_num}: {len(results)} products')
        except:
            pass

    page.on('response', capture_api)

    try:
        REQUEST_COUNT += 1
        logging.info(f'Scraping: {url}')

        # Load page
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(3)

        # Close popup
        try:
            close_btn = await page.query_selector('button[aria-label*="close" i]')
            if close_btn and await close_btn.is_visible():
                await close_btn.click()
                await asyncio.sleep(0.5)
        except:
            pass

        # Click through pages to capture all API responses
        current_page = 1
        while current_page < 5:
            await asyncio.sleep(1)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(0.5)

            next_btn = await page.query_selector(f'button.MuiPaginationItem-page:has-text("{current_page + 1}")')
            if next_btn and await next_btn.is_visible() and not await next_btn.is_disabled():
                await next_btn.click()
                await asyncio.sleep(2)
                current_page += 1
            else:
                break

        logging.info(f'Captured {len(api_products)} pages from API')

        # Process API products
        products = []
        for page_num in sorted(api_products.keys()):
            for product in api_products[page_num]:
                try:
                    data = product.get('data', {})
                    products.append({
                        'title': product.get('value', 'Unknown'),
                        'url': f"https://www.kmart.com.au{data.get('url', '')}",
                        'sku': data.get('id', ''),
                        'image': data.get('image_url', ''),
                        'price': None
                    })
                except:
                    continue

        logging.info(f'Successfully scraped {len(products)} products')
        return products

    except Exception as e:
        ERROR_COUNT += 1
        logging.error(f'Error scraping: {e}')
        return []


async def send_discord_webhook(product: Dict, state: str = None):
    """Send Discord notification"""
    # Implementation similar to existing monitor
    pass


async def monitor():
    """Main monitoring loop"""
    global INSTOCK

    logging.info('='*50)
    logging.info('KMART AU MONITOR (API METHOD)')
    logging.info('='*50)
    logging.info(f'URL: {config.URL}')
    logging.info(f'Delay: {config.DELAY}s')
    logging.info('='*50)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        iteration = 0
        while True:
            iteration += 1

            try:
                products = await scrape_products(page, config.URL)

                logging.info(f'[{iteration:04d}] Products: {len(products)} | Requests: {REQUEST_COUNT} | Errors: {ERROR_COUNT}')

                # Process products...
                # (Stock checking logic here - similar to existing monitor)

                await asyncio.sleep(config.DELAY)

            except Exception as e:
                logging.error(f'Monitor error: {e}')
                await asyncio.sleep(10)


if __name__ == '__main__':
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        logging.info('Monitor stopped by user')
