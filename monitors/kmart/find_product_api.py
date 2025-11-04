"""
Deep dive into finding the actual product loading mechanism
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def find_api():
    all_responses = []

    async def handle_response(response):
        url = response.url

        # Capture ALL responses to analyze
        try:
            if response.status == 200:
                content_type = response.headers.get('content-type', '')

                # Look for JSON responses
                if 'json' in content_type:
                    try:
                        body = await response.json()
                        body_str = json.dumps(body)

                        # Check if contains product data with article numbers
                        if any(keyword in body_str.lower() for keyword in ['43612208', '43615735', 'pokemon', 'article']):
                            all_responses.append({
                                'url': url,
                                'body': body,
                                'size': len(body_str)
                            })
                            print(f'\n[FOUND] {url}')
                            print(f'Size: {len(body_str)} bytes')
                            print(f'Sample: {body_str[:200]}...\n')
                    except:
                        pass
        except:
            pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Intercept all responses
        page.on('response', handle_response)

        print('Loading page and watching for product API calls...\n')

        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(5)

        # Close popup
        try:
            close_btn = await page.query_selector('button[aria-label*="close" i]')
            if close_btn:
                await close_btn.click()
        except:
            pass

        # Scroll to trigger lazy loading
        print('Scrolling to trigger more API calls...\n')
        for i in range(15):
            await page.evaluate('window.scrollBy(0, 1000)')
            await asyncio.sleep(0.5)

        # Click page 2
        print('Clicking page 2...\n')
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)

        page2_btn = await page.query_selector('button.MuiPaginationItem-page:has-text("2")')
        if page2_btn:
            await page2_btn.click()
            await asyncio.sleep(5)

        print(f'\n{"="*60}')
        print(f'Captured {len(all_responses)} product-related API responses')
        print(f'{"="*60}\n')

        # Analyze the responses
        for i, resp in enumerate(all_responses):
            print(f'\n--- Response {i+1} ---')
            print(f'URL: {resp["url"]}')
            print(f'Size: {resp["size"]} bytes')

            # Try to find product arrays
            body = resp['body']

            def find_products(obj, path=''):
                """Recursively find arrays that look like product lists"""
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        new_path = f'{path}.{key}' if path else key
                        find_products(value, new_path)
                elif isinstance(obj, list):
                    if len(obj) > 10 and isinstance(obj[0], dict):
                        # Might be a product list
                        first_item = obj[0]
                        if any(k in str(first_item.keys()).lower() for k in ['name', 'title', 'price', 'product', 'article']):
                            print(f'  Possible product array at: {path}')
                            print(f'  Length: {len(obj)} items')
                            print(f'  First item keys: {list(first_item.keys())[:10]}')

                    for item in obj:
                        find_products(item, path)

            find_products(body)

        await asyncio.sleep(5)
        await browser.close()

        # Save all responses
        with open('product_api_responses.json', 'w') as f:
            json.dump(all_responses, f, indent=2, default=str)
        print('\nSaved all responses to product_api_responses.json')

if __name__ == '__main__':
    asyncio.run(find_api())
