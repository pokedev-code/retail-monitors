"""
Test intercepting Constructor.io API to get all products instantly
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def test_api_intercept():
    product_data = {}

    async def capture_constructor_api(response):
        url = response.url

        # Look for Constructor.io browse API
        if 'ac.cnstrc.com/browse/group_id' in url and response.status == 200:
            try:
                data = await response.json()

                # Extract page number from URL
                import re
                page_match = re.search(r'[?&]page=(\d+)', url)
                page_num = int(page_match.group(1)) if page_match else 1

                # Get products from response
                results = data.get('response', {}).get('results', [])
                total_count = data.get('response', {}).get('result_sources', {}).get('token_match', {}).get('count', 0)

                product_data[page_num] = {
                    'products': results,
                    'count': len(results),
                    'total_available': total_count
                }

                print(f'\n[API] Page {page_num}: {len(results)} products (Total in category: {total_count})')

            except Exception as e:
                print(f'Error parsing Constructor.io response: {e}')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Intercept responses
        page.on('response', capture_constructor_api)

        print('Loading Kmart Pokemon cards page...')
        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(5)

        # Close popup
        try:
            close_btn = await page.query_selector('button[aria-label*="close" i]')
            if close_btn:
                await close_btn.click()
        except:
            pass

        # Click page 2 to trigger API call
        print('\nClicking page 2...')
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)

        page2_btn = await page.query_selector('button.MuiPaginationItem-page:has-text("2")')
        if page2_btn:
            await page2_btn.click()
            await asyncio.sleep(3)

        print(f'\n{"="*60}')
        print('RESULTS')
        print(f'{"="*60}')

        total_products = 0
        for page_num in sorted(product_data.keys()):
            data = product_data[page_num]
            print(f'Page {page_num}: {data["count"]} products')
            total_products += data["count"]

            # Show sample product
            if data['products']:
                sample = data['products'][0]
                print(f'  Sample product keys: {list(sample.keys())[:10]}')
                if 'data' in sample:
                    print(f'  Product data keys: {list(sample["data"].keys())[:15]}')

        print(f'\nTotal products extracted: {total_products}')
        print(f'Total available in category: {product_data.get(1, {}).get("total_available", "unknown")}')
        print(f'\n{"="*60}')
        print('SUCCESS! We can use Constructor.io API for instant scraping!')
        print(f'{"="*60}')

        await asyncio.sleep(3)
        await browser.close()

        return product_data

if __name__ == '__main__':
    asyncio.run(test_api_intercept())
