"""
Test Big W marketplace filtering with force click
"""
import asyncio
from playwright.async_api import async_playwright
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CATEGORY_URL = "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201"

async def test_force_click():
    """Test marketplace filter with force=True"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            # Load page
            logging.info('[1] Loading page...')
            await page.goto(CATEGORY_URL, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)

            # Get initial stats
            next_data_script = await page.query_selector('script#__NEXT_DATA__')
            next_data_text = await next_data_script.inner_text()
            next_data = json.loads(next_data_text)
            results_before = next_data['props']['pageProps']['results']['organic']['results']

            bigw_before = sum(1 for p in results_before if p.get('fulfillment', {}).get('productChannel') == 'BIGW')
            marketplace_before = sum(1 for p in results_before if p.get('fulfillment', {}).get('productChannel') == 'IMP')

            logging.info(f'[BEFORE] Total={len(results_before)}, Big W={bigw_before}, Marketplace={marketplace_before}')

            # Apply filter
            logging.info('[2] Opening filter panel...')
            filter_btn = await page.query_selector('button[data-testid="filter-btn-type-filter"]')
            await filter_btn.click()
            await asyncio.sleep(2)

            logging.info('[3] Clicking marketplace toggle...')
            marketplace_toggle = await page.query_selector('button#marketplace-items')
            is_checked = await marketplace_toggle.get_attribute('aria-checked')
            logging.info(f'[TOGGLE] Before: aria-checked={is_checked}')

            await marketplace_toggle.click()
            await asyncio.sleep(1)

            new_state = await marketplace_toggle.get_attribute('aria-checked')
            logging.info(f'[TOGGLE] After: aria-checked={new_state}')

            # Click Show button with force=True
            logging.info('[4] Clicking Show button with force=True...')
            show_btn = await page.query_selector('button:has-text("Show")')
            btn_text = await show_btn.inner_text()
            logging.info(f'[BUTTON] Text: "{btn_text}"')

            await show_btn.click(force=True)
            await asyncio.sleep(5)

            # Get stats after filter
            next_data_script = await page.query_selector('script#__NEXT_DATA__')
            next_data_text = await next_data_script.inner_text()
            next_data = json.loads(next_data_text)
            results_after = next_data['props']['pageProps']['results']['organic']['results']

            bigw_after = sum(1 for p in results_after if p.get('fulfillment', {}).get('productChannel') == 'BIGW')
            marketplace_after = sum(1 for p in results_after if p.get('fulfillment', {}).get('productChannel') == 'IMP')

            logging.info(f'[AFTER] Total={len(results_after)}, Big W={bigw_after}, Marketplace={marketplace_after}')

            # Results
            logging.info('\n' + '='*60)
            if marketplace_after == 0 and bigw_after == bigw_before:
                logging.info('[SUCCESS] ✓ Filter removed all marketplace items!')
                logging.info(f'  Only showing {bigw_after} Big W products (was {bigw_before})')
            elif marketplace_after < marketplace_before:
                logging.info(f'[PARTIAL] Reduced marketplace from {marketplace_before} to {marketplace_after}')
            else:
                logging.warning('[FAILED] Filter did not work')
            logging.info('='*60)

            # Keep browser open
            logging.info('\nKeeping browser open for 10 seconds...')
            await asyncio.sleep(10)

        except Exception as e:
            logging.error(f'Test failed: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_force_click())
