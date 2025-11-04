"""
Test to compare DOM product count vs JSON-LD count
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def test_product_counts():
    """Compare product counts in DOM vs JSON-LD"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        logging.info('Loading Kmart Pokemon cards page...')
        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(3)

        # Scroll to load everything
        logging.info('\nScrolling to bottom...')
        for i in range(10):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)
            logging.info(f'  Scroll {i+1}/10')

        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(2)

        # Count JSON-LD items
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

        # Count DOM product elements (try multiple selectors)
        dom_counts = {}

        # Try common product selectors
        selectors = [
            'article[data-testid="product-tile"]',
            '[data-testid="product-tile"]',
            'article.product-tile',
            '.product-tile',
            'article[class*="ProductTile"]',
            '[class*="ProductTile"]',
            'a[href*="/product/"]',
        ]

        for selector in selectors:
            count = await page.evaluate(f'''() => {{
                return document.querySelectorAll('{selector}').length;
            }}''')
            if count > 0:
                dom_counts[selector] = count

        print('\n' + '='*60)
        print('PRODUCT COUNT COMPARISON')
        print('='*60)
        print(f'\nJSON-LD items: {jsonld_count}')
        print(f'\nDOM element counts:')
        for selector, count in dom_counts.items():
            print(f'  {selector}: {count}')

        # Also check what the page says
        page_text = await page.evaluate('''() => {
            return document.body.innerText;
        }''')

        # Look for "showing X of Y" type text
        import re
        result_text = re.search(r'showing.*?(\d+).*?of.*?(\d+)', page_text.lower())
        if result_text:
            print(f'\nPage shows: "{result_text.group(0)}"')

        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_product_counts())
