"""
Verify the actual number of products Kmart has
"""
import asyncio
from playwright.async_api import async_playwright

async def verify_count():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(3)

        # Scroll to top to see the product count text
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(1)

        # Look for "X-Y of Z Products" text
        page_text = await page.evaluate('''() => {
            // Find all text on the page
            const body = document.body.innerText;

            // Also try to find the specific element showing count
            const countElements = document.querySelectorAll('[class*="ProductCount"], [class*="product-count"], [class*="Result"]');
            let countText = '';
            for (const el of countElements) {
                if (el.innerText.match(/\d+.*of.*\d+/i)) {
                    countText = el.innerText;
                    break;
                }
            }

            return {
                fullText: body,
                countText: countText
            };
        }''')

        # Extract product count from text
        import re
        full_text = page_text['fullText']

        # Look for patterns like "1-60 of 76 Products" or "40 Products"
        patterns = [
            r'(\d+)-(\d+)\s+of\s+(\d+)\s+[Pp]roducts?',
            r'(\d+)\s+of\s+(\d+)\s+[Pp]roducts?',
            r'[Ss]howing\s+(\d+)\s+[Pp]roducts?',
        ]

        total_products = None
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                print(f'Found match: {match.group(0)}')
                # Last captured group is usually the total
                groups = match.groups()
                if len(groups) == 3:  # "X-Y of Z Products"
                    total_products = int(groups[2])
                elif len(groups) == 2:  # "X of Y Products"
                    total_products = int(groups[1])
                else:
                    total_products = int(groups[0])
                break

        # Also check JSON-LD schema
        schema_data = await page.evaluate('''() => {
            const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
            for (const script of scripts) {
                try {
                    const data = JSON.parse(script.textContent);
                    if (data['@type'] === 'ItemList') {
                        return {
                            numberOfItems: data.numberOfItems,
                            actualItems: data.itemListElement ? data.itemListElement.length : 0
                        };
                    }
                } catch(e) {}
            }
            return null;
        }''')

        print('\n' + '='*60)
        print('KMART POKEMON CARDS PRODUCT COUNT')
        print('='*60)
        if total_products:
            print(f'\nPage text says: {total_products} total products')
        if schema_data:
            print(f'JSON-LD schema says: {schema_data["numberOfItems"]} total items')
            print(f'JSON-LD page 1 has: {schema_data["actualItems"]} items')

        if page_text['countText']:
            print(f'\nCount element text: "{page_text["countText"]}"')

        # Take screenshot of top
        await page.screenshot(path='kmart_top.png', full_page=False)
        print('\nScreenshot saved as kmart_top.png')

        await asyncio.sleep(3)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(verify_count())
