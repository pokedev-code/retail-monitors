"""
Test combined approach: UI filter + __NEXT_DATA__ scraping
"""
import asyncio
from playwright.async_api import async_playwright
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CATEGORY_URL = "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201"

async def test_combined_approach():
    """Test UI filter then scrape __NEXT_DATA__ from filtered page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            # Step 1: Load page
            logging.info('[1] Loading initial page...')
            await page.goto(CATEGORY_URL, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)

            # Get initial stats from __NEXT_DATA__
            next_data_script = await page.query_selector('script#__NEXT_DATA__')
            next_data_text = await next_data_script.inner_text()
            next_data = json.loads(next_data_text)
            results_before = next_data['props']['pageProps']['results']['organic']['results']

            bigw_before = sum(1 for p in results_before if p.get('fulfillment', {}).get('productChannel') == 'BIGW')
            marketplace_before = sum(1 for p in results_before if p.get('fulfillment', {}).get('productChannel') == 'IMP')

            logging.info(f'[BEFORE FILTER] Total={len(results_before)}, Big W={bigw_before}, Marketplace={marketplace_before}')

            # Step 2: Apply UI filter
            logging.info('[2] Opening filter panel...')
            filter_btn = await page.query_selector('button[data-testid="filter-btn-type-filter"]')
            await filter_btn.click()
            await asyncio.sleep(2)

            logging.info('[3] Clicking marketplace toggle...')
            marketplace_toggle = await page.query_selector('button#marketplace-items')
            await marketplace_toggle.click()
            await asyncio.sleep(2)  # Wait for button text to update

            # Check button text AFTER waiting
            show_btn = await page.query_selector('button:has-text("Show")')
            btn_text = await show_btn.inner_text()
            logging.info(f'[BUTTON] Text after waiting: "{btn_text}"')

            # Step 3: Click Show button to apply filter
            logging.info('[4] Clicking Show button...')
            await show_btn.click(force=True)

            # IMPORTANT: Wait for page to reload/update
            logging.info('[5] Waiting for page to update with filtered results...')
            await asyncio.sleep(5)

            # Step 4: Scrape __NEXT_DATA__ from FILTERED page
            logging.info('[6] Scraping __NEXT_DATA__ from filtered page...')
            next_data_script = await page.query_selector('script#__NEXT_DATA__')
            next_data_text = await next_data_script.inner_text()
            next_data = json.loads(next_data_text)
            results_after = next_data['props']['pageProps']['results']['organic']['results']

            bigw_after = sum(1 for p in results_after if p.get('fulfillment', {}).get('productChannel') == 'BIGW')
            marketplace_after = sum(1 for p in results_after if p.get('fulfillment', {}).get('productChannel') == 'IMP')

            logging.info(f'[AFTER FILTER] Total={len(results_after)}, Big W={bigw_after}, Marketplace={marketplace_after}')

            # Results
            logging.info('\n' + '='*60)
            logging.info('RESULTS:')
            logging.info(f'  Before: {len(results_before)} products ({bigw_before} Big W, {marketplace_before} Marketplace)')
            logging.info(f'  After:  {len(results_after)} products ({bigw_after} Big W, {marketplace_after} Marketplace)')

            if marketplace_after == 0 and bigw_after > 0:
                logging.info(f'\n[SUCCESS] UI filter + __NEXT_DATA__ works! Only {bigw_after} Big W products!')
                logging.info(f'  Reduced from {len(results_before)} to {len(results_after)} products')
            elif marketplace_after < marketplace_before:
                logging.info(f'\n[PARTIAL] Reduced marketplace from {marketplace_before} to {marketplace_after}')
            else:
                logging.warning('\n[FAILED] __NEXT_DATA__ did not update after filter')

            logging.info('='*60)

            # Show first few products
            if results_after:
                logging.info('\nFirst 3 products from filtered __NEXT_DATA__:')
                for i, prod in enumerate(results_after[:3], 1):
                    name = prod.get('information', {}).get('name', 'Unknown')
                    channel = prod.get('fulfillment', {}).get('productChannel', 'Unknown')
                    logging.info(f'  {i}. {name} | Channel: {channel}')

            # Keep browser open for inspection
            logging.info('\nKeeping browser open for 15 seconds...')
            await asyncio.sleep(15)

        except Exception as e:
            logging.error(f'Test failed: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_combined_approach())
