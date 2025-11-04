"""
Test Big W UI filter clicking to verify marketplace items are filtered out
"""
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CATEGORY_URL = "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201"

async def test_ui_filter():
    """Test the UI filter implementation"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            logging.info('[TEST] Loading Big W category page...')
            await page.goto(CATEGORY_URL, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)

            # Get initial product count
            try:
                next_data_script = await page.query_selector('script#__NEXT_DATA__')
                if next_data_script:
                    import json
                    next_data_text = await next_data_script.inner_text()
                    next_data = json.loads(next_data_text)
                    initial_count = len(next_data['props']['pageProps']['results']['organic']['results'])
                    logging.info(f'[TEST] Initial product count: {initial_count}')
            except Exception as e:
                logging.warning(f'[TEST] Could not get initial count: {e}')

            # Click Filter button
            logging.info('[TEST] Clicking filter button...')
            filter_btn = await page.query_selector('button[data-testid="filter-btn-type-filter"]')

            if filter_btn and await filter_btn.is_visible():
                await filter_btn.click()
                logging.info('[TEST] Filter button clicked')
                await asyncio.sleep(2)

                # Click marketplace toggle
                logging.info('[TEST] Looking for marketplace toggle...')
                marketplace_toggle = await page.query_selector('button#marketplace-items')

                if marketplace_toggle and await marketplace_toggle.is_visible():
                    is_checked = await marketplace_toggle.get_attribute('aria-checked')
                    logging.info(f'[TEST] Marketplace toggle found, aria-checked={is_checked}')

                    # The toggle is inverted:
                    # aria-checked="true" = marketplace items INCLUDED (we want to click to EXCLUDE them)
                    # aria-checked="false" = marketplace items EXCLUDED (already filtered out)

                    if is_checked == 'true':
                        logging.info('[TEST] Marketplace items currently INCLUDED, clicking to EXCLUDE...')
                        await marketplace_toggle.click()
                        await asyncio.sleep(1)

                        # Check new state after clicking
                        new_state = await marketplace_toggle.get_attribute('aria-checked')
                        logging.info(f'[TEST] After click, aria-checked={new_state}')
                    elif is_checked == 'false':
                        logging.info('[TEST] Marketplace items already EXCLUDED, clicking to INCLUDE (to test)...')
                        await marketplace_toggle.click()
                        await asyncio.sleep(1)

                        new_state = await marketplace_toggle.get_attribute('aria-checked')
                        logging.info(f'[TEST] After click, aria-checked={new_state}')

                    # Click "Show X results" button
                    logging.info('[TEST] Looking for Show results button...')
                    show_btn = await page.query_selector('button:has-text("Show")')

                    if show_btn and await show_btn.is_visible():
                        btn_text = await show_btn.inner_text()
                        logging.info(f'[TEST] Found button: "{btn_text}"')
                        await show_btn.click()
                        await asyncio.sleep(3)
                        logging.info('[TEST] Show button clicked, waiting for page to update...')

                        # Get filtered product count
                        try:
                            next_data_script = await page.query_selector('script#__NEXT_DATA__')
                            if next_data_script:
                                next_data_text = await next_data_script.inner_text()
                                next_data = json.loads(next_data_text)
                                results = next_data['props']['pageProps']['results']['organic']['results']
                                filtered_count = len(results)

                                # Count marketplace items
                                bigw_count = 0
                                marketplace_count = 0

                                for prod in results:
                                    channel = prod.get('fulfillment', {}).get('productChannel', '')
                                    if channel == 'BIGW':
                                        bigw_count += 1
                                    elif channel == 'IMP':
                                        marketplace_count += 1

                                logging.info(f'[TEST] Filtered product count: {filtered_count}')
                                logging.info(f'[TEST] Big W products: {bigw_count}')
                                logging.info(f'[TEST] Marketplace products: {marketplace_count}')

                                if marketplace_count == 0:
                                    logging.info('[SUCCESS] ✓ UI filter successfully removed all marketplace items!')
                                else:
                                    logging.warning(f'[WARNING] Still found {marketplace_count} marketplace items')

                        except Exception as e:
                            logging.error(f'[TEST] Could not get filtered count: {e}')
                    else:
                        logging.error('[TEST] Show button not found or not visible')
                else:
                    logging.error('[TEST] Marketplace toggle not found or not visible')
            else:
                logging.error('[TEST] Filter button not found or not visible')

            logging.info('[TEST] Keeping browser open for 10 seconds for visual inspection...')
            await asyncio.sleep(10)

        except Exception as e:
            logging.error(f'[ERROR] Test failed: {e}')
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_ui_filter())
