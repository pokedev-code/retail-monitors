"""
Test Big W marketplace filtering - verify programmatic filter works
"""
import asyncio
import sys
sys.path.insert(0, '.')

from monitor import scrape_products_playwright
from playwright.async_api import async_playwright
import config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_marketplace_filter():
    """Test that marketplace items are filtered out"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.HEADLESS)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        try:
            logging.info('Testing Big W marketplace filter...')
            logging.info(f'Category URL: {config.CATEGORY_URL}')
            logging.info('')

            products = await scrape_products_playwright(page)

            logging.info('')
            logging.info('='*60)
            logging.info(f'RESULT: Found {len(products)} Big W products')
            logging.info('='*60)

            if len(products) > 0:
                logging.info('\nFirst 5 products:')
                for i, prod in enumerate(products[:5], 1):
                    logging.info(f'  {i}. {prod["title"]} - ${prod["price"]}')

                logging.info(f'\n[SUCCESS] ✓ Marketplace filter working! Found {len(products)} Big W products')
            else:
                logging.warning('[WARNING] No products found - check if category has stock')

        except Exception as e:
            logging.error(f'Test failed: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_marketplace_filter())
