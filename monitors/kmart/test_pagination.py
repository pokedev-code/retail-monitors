"""
Test script to verify pagination logic finds all 76 products
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def test_pagination():
    """Test Kmart pagination to load all products"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        logging.info('Loading Kmart Pokemon cards page...')
        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(2)

        logging.info('\nCollecting products from all pagination pages...')
        all_page_items = []
        current_page = 1
        max_pages = 10

        while current_page <= max_pages:
            await asyncio.sleep(2)

            # Extract JSON-LD from current page
            page_items = await page.evaluate('''() => {
                const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                for (const script of scripts) {
                    try {
                        const data = JSON.parse(script.textContent);
                        if (data['@type'] === 'ItemList') {
                            return data.itemListElement || [];
                        }
                    } catch(e) {}
                }
                return [];
            }''')

            if page_items:
                all_page_items.extend(page_items)
                logging.info(f'Page {current_page}: Found {len(page_items)} products (total: {len(all_page_items)})')
            else:
                logging.warning(f'Page {current_page}: No products found')
                break

            # Try to find and click next page button
            try:
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(1)

                next_page_num = current_page + 1
                next_button = await page.query_selector(f'button.MuiPaginationItem-page:has-text("{next_page_num}")')

                if next_button and await next_button.is_visible() and not await next_button.is_disabled():
                    logging.info(f'Clicking page {next_page_num} button...')
                    await next_button.click()
                    await asyncio.sleep(2)
                    current_page += 1
                else:
                    logging.info(f'No more pages (completed {current_page} pages)')
                    break
            except Exception as e:
                logging.info(f'Pagination ended: {e}')
                break

        await browser.close()

        print('\n' + '='*60)
        print(f'RESULT: Found {len(all_page_items)} products from {current_page} pages')
        print(f'EXPECTED: 76 products')
        print(f'STATUS: {"SUCCESS" if len(all_page_items) >= 76 else "FAILED"}')
        print('='*60)

        return len(all_page_items)

if __name__ == '__main__':
    asyncio.run(test_pagination())
