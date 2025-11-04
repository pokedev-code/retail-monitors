"""
Test script to verify the updated scrolling logic finds all 76 products
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def test_scrolling():
    """Test Kmart scrolling to load all products"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        logging.info('Loading Kmart Pokemon cards page...')
        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(2)

        logging.info('Starting scroll test...')
        previous_items = 0
        scroll_attempts = 0
        max_scrolls = 15
        no_change_count = 0

        for scroll_attempt in range(max_scrolls):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(3)

            current_items = await page.evaluate('''() => {
                const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                for (const script of scripts) {
                    try {
                        const data = JSON.parse(script.textContent);
                        if (data['@type'] === 'ItemList') {
                            return data.itemListElement ? data.itemListElement.length : 0;
                        }
                    } catch(e) {}
                }
                return 0;
            }''')

            scroll_attempts += 1
            logging.info(f'Scroll {scroll_attempts}: {current_items} items in JSON-LD')

            if current_items == previous_items and current_items > 0:
                no_change_count += 1
                logging.info(f'  → No change count: {no_change_count}/3')
                if no_change_count >= 3:
                    logging.info(f'\n✓ All products loaded after {scroll_attempts} scrolls ({current_items} items)')
                    break
            else:
                if no_change_count > 0:
                    logging.info(f'  → Item count increased! Resetting no_change_count')
                no_change_count = 0

            previous_items = current_items

        if no_change_count < 3:
            logging.warning(f'\n⚠ Reached max scrolls ({max_scrolls}) - found {current_items} items')

        await browser.close()

        return current_items

if __name__ == '__main__':
    total_items = asyncio.run(test_scrolling())
    print(f'\n{"="*60}')
    print(f'RESULT: Found {total_items} products')
    print(f'EXPECTED: 76 products')
    print(f'STATUS: {"✓ SUCCESS" if total_items == 76 else "✗ FAILED"}')
    print(f'{"="*60}')
