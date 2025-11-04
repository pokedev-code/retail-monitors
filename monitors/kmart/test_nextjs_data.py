"""
Check if __NEXT_DATA__ contains all 76 products without needing to scroll
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def test_nextjs_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print('Loading Kmart Pokemon cards page...')
        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(3)

        # Close popup
        try:
            close_btn = await page.query_selector('button[aria-label*="close" i]')
            if close_btn:
                await close_btn.click()
                await asyncio.sleep(1)
        except:
            pass

        # Extract __NEXT_DATA__ from page 1
        print('\n=== PAGE 1 ===')
        nextjs_data_page1 = await page.evaluate('''() => {
            const script = document.getElementById('__NEXT_DATA__');
            if (script) {
                return JSON.parse(script.textContent);
            }
            return null;
        }''')

        if nextjs_data_page1:
            # Navigate the structure to find products
            props = nextjs_data_page1.get('props', {})
            page_props = props.get('pageProps', {})

            print(f'Top-level keys: {list(page_props.keys())}')

            # Look for product data
            if 'results' in page_props:
                results = page_props['results']
                print(f'Results keys: {list(results.keys())}')

                if 'organic' in results:
                    organic = results['organic']
                    print(f'Organic keys: {list(organic.keys())}')

                    if 'results' in organic:
                        products_page1 = organic['results']
                        print(f'\nPage 1: Found {len(products_page1)} products in __NEXT_DATA__')

                        # Show first product structure
                        if products_page1:
                            print(f'\nFirst product keys: {list(products_page1[0].keys())}')
                            print(f'Sample product: {json.dumps(products_page1[0], indent=2)[:500]}...')

        # Click to page 2
        print('\n=== CLICKING PAGE 2 ===')
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)
        page2_btn = await page.query_selector('button.MuiPaginationItem-page:has-text("2")')
        if page2_btn:
            await page2_btn.click()
            await asyncio.sleep(3)

            # Extract __NEXT_DATA__ from page 2
            nextjs_data_page2 = await page.evaluate('''() => {
                const script = document.getElementById('__NEXT_DATA__');
                if (script) {
                    return JSON.parse(script.textContent);
                }
                return null;
            }''')

            if nextjs_data_page2:
                props2 = nextjs_data_page2.get('props', {})
                page_props2 = props2.get('pageProps', {})
                results2 = page_props2.get('results', {})
                organic2 = results2.get('organic', {})
                products_page2 = organic2.get('results', [])

                print(f'Page 2: Found {len(products_page2)} products in __NEXT_DATA__')

        print('\n' + '='*60)
        print('If __NEXT_DATA__ has all products, we can skip scrolling!')
        print('='*60)

        await asyncio.sleep(3)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_nextjs_data())
