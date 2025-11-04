"""
Test to find and click "Load More" button or pagination
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def test_load_more():
    """Check for Load More button or pagination"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        logging.info('Loading Kmart Pokemon cards page...')
        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(3)

        # Scroll down to trigger lazy loading
        logging.info('\nScrolling to bottom to reveal Load More button...')
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(3)

        # Look for Load More buttons with various selectors
        load_more_selectors = [
            'button:has-text("Load More")',
            'button:has-text("Show More")',
            'button:has-text("View More")',
            '[data-testid="load-more"]',
            '[class*="load-more"]',
            '[class*="LoadMore"]',
            'button[class*="show-more"]',
            'button[class*="view-more"]',
        ]

        found_button = None
        for selector in load_more_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        text = await element.inner_text()
                        logging.info(f'\nFound button: "{text}" (selector: {selector})')
                        found_button = element
                        break
            except:
                pass

        if found_button:
            logging.info('\nClicking Load More button...')
            await found_button.click()
            await asyncio.sleep(3)

            # Check new count
            jsonld_count = await page.evaluate('''() => {
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
            logging.info(f'After clicking: {jsonld_count} items in JSON-LD')
        else:
            logging.info('\nNo Load More button found!')

            # Check for pagination
            logging.info('\nLooking for pagination...')
            pagination = await page.query_selector('nav[aria-label="pagination"], .pagination, [class*="Pagination"]')
            if pagination:
                html = await pagination.inner_html()
                logging.info(f'Found pagination: {html[:200]}...')
            else:
                logging.info('No pagination found either!')

            # Take a screenshot of the bottom of the page
            logging.info('\nTaking screenshot of bottom section...')
            await page.screenshot(path='kmart_bottom.png', full_page=False)
            logging.info('Saved as kmart_bottom.png')

        # Get all button text on page
        logging.info('\nAll buttons on page:')
        buttons = await page.query_selector_all('button')
        for btn in buttons[:20]:  # First 20 buttons
            try:
                text = await btn.inner_text()
                is_visible = await btn.is_visible()
                if text.strip() and is_visible:
                    logging.info(f'  - "{text.strip()}"')
            except:
                pass

        await asyncio.sleep(5)  # Keep browser open to inspect
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_load_more())
