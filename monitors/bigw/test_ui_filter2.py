"""
Test Big W marketplace filtering - check if UI filter actually works
"""
import asyncio
from playwright.async_api import async_playwright
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CATEGORY_URL = "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201"

async def get_product_stats(page):
    """Get product statistics from __NEXT_DATA__"""
    try:
        next_data_script = await page.query_selector('script#__NEXT_DATA__')
        if next_data_script:
            next_data_text = await next_data_script.inner_text()
            next_data = json.loads(next_data_text)
            results = next_data['props']['pageProps']['results']['organic']['results']

            total = len(results)
            bigw_count = 0
            marketplace_count = 0

            for prod in results:
                channel = prod.get('fulfillment', {}).get('productChannel', '')
                if channel == 'BIGW':
                    bigw_count += 1
                elif channel == 'IMP':
                    marketplace_count += 1

            return {
                'total': total,
                'bigw': bigw_count,
                'marketplace': marketplace_count
            }
    except Exception as e:
        logging.error(f'Could not get stats: {e}')
        return None

async def test_ui_filter():
    """Test marketplace filter"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # Load page
            logging.info('[1] Loading page WITHOUT filter...')
            await page.goto(CATEGORY_URL, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)

            stats_before = await get_product_stats(page)
            logging.info(f'[BEFORE] Total={stats_before["total"]}, Big W={stats_before["bigw"]}, Marketplace={stats_before["marketplace"]}')

            # Now apply filter via UI
            logging.info('[2] Clicking filter button...')
            filter_btn = await page.query_selector('button[data-testid="filter-btn-type-filter"]')
            if not filter_btn:
                logging.error('Filter button not found')
                return

            await filter_btn.click()
            await asyncio.sleep(2)

            # Get button text BEFORE clicking toggle
            show_btn_before = await page.query_selector('button:has-text("Show")')
            if show_btn_before:
                text_before = await show_btn_before.inner_text()
                logging.info(f'[BEFORE TOGGLE] Show button text: "{text_before}"')

            # Click marketplace toggle
            logging.info('[3] Clicking marketplace toggle...')
            marketplace_toggle = await page.query_selector('button#marketplace-items')
            if not marketplace_toggle:
                logging.error('Marketplace toggle not found')
                return

            is_checked_before = await marketplace_toggle.get_attribute('aria-checked')
            logging.info(f'[BEFORE TOGGLE] aria-checked={is_checked_before}')

            await marketplace_toggle.click()
            await asyncio.sleep(2)

            is_checked_after = await marketplace_toggle.get_attribute('aria-checked')
            logging.info(f'[AFTER TOGGLE] aria-checked={is_checked_after}')

            # Get button text AFTER clicking toggle
            show_btn_after = await page.query_selector('button:has-text("Show")')
            if show_btn_after:
                text_after = await show_btn_after.inner_text()
                logging.info(f'[AFTER TOGGLE] Show button text: "{text_after}"')

            # Click Show button
            logging.info('[4] Clicking Show button...')
            await show_btn_after.click()
            await asyncio.sleep(5)

            # Get stats AFTER filter applied
            stats_after = await get_product_stats(page)
            logging.info(f'[AFTER] Total={stats_after["total"]}, Big W={stats_after["bigw"]}, Marketplace={stats_after["marketplace"]}')

            # Compare
            logging.info('\n' + '='*60)
            logging.info('COMPARISON:')
            logging.info(f'  Before: {stats_before["total"]} products ({stats_before["bigw"]} Big W, {stats_before["marketplace"]} Marketplace)')
            logging.info(f'  After:  {stats_after["total"]} products ({stats_after["bigw"]} Big W, {stats_after["marketplace"]} Marketplace)')

            if stats_after["marketplace"] == 0 and stats_after["bigw"] > 0:
                logging.info('\n[SUCCESS] ✓ UI filter successfully removed marketplace items!')
            elif stats_after["marketplace"] < stats_before["marketplace"]:
                logging.info(f'\n[PARTIAL] Filter reduced marketplace items from {stats_before["marketplace"]} to {stats_after["marketplace"]}')
            else:
                logging.warning('\n[FAILED] Filter did not reduce marketplace items')

            logging.info('='*60)

            # Keep browser open
            logging.info('\nKeeping browser open for 15 seconds...')
            await asyncio.sleep(15)

        except Exception as e:
            logging.error(f'Test failed: {e}')
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_ui_filter())
