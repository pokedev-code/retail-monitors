"""
Intercept Kmart's network requests to find the product API
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def investigate_api():
    captured_requests = []

    async def capture_request(request):
        url = request.url
        # Look for API calls
        if any(keyword in url.lower() for keyword in ['api', 'graphql', 'products', 'search', 'query', 'getproduct']):
            captured_requests.append({
                'url': url,
                'method': request.method,
                'resource_type': request.resource_type
            })
            print(f'\n[REQUEST] {request.method} {url[:100]}...')

    async def capture_response(response):
        url = response.url
        # Look for API responses with product data
        if any(keyword in url.lower() for keyword in ['api', 'graphql', 'products', 'search', 'query']):
            try:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        body = await response.json()
                        print(f'\n[RESPONSE] {url[:100]}...')
                        print(f'Status: {response.status}')

                        # Check if it contains product data
                        body_str = json.dumps(body)[:500]
                        if 'pokemon' in body_str.lower() or 'product' in body_str.lower():
                            print(f'Contains product data!')
                            print(f'Sample: {body_str[:200]}...')
            except:
                pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Set up request/response interception
        page.on('request', capture_request)
        page.on('response', capture_response)

        print('Loading Kmart Pokemon cards page...')
        print('Watching for API calls...\n')

        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')

        # Close popup
        await asyncio.sleep(3)
        try:
            close_btn = await page.query_selector('button[aria-label*="close" i]')
            if close_btn:
                await close_btn.click()
        except:
            pass

        # Scroll a bit to trigger more API calls
        print('\nScrolling to trigger more API calls...')
        for i in range(5):
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(2)

        # Click page 2 to see if it makes a different API call
        print('\nClicking page 2...')
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)

        page2_btn = await page.query_selector('button.MuiPaginationItem-page:has-text("2")')
        if page2_btn:
            await page2_btn.click()
            await asyncio.sleep(3)

        print('\n' + '='*60)
        print(f'Captured {len(captured_requests)} API requests')
        print('='*60)

        # Show unique API endpoints
        unique_apis = set(req['url'].split('?')[0] for req in captured_requests)
        print('\nUnique API endpoints:')
        for api in unique_apis:
            print(f'  - {api}')

        await asyncio.sleep(5)
        await browser.close()

        # Save captured requests to file
        with open('kmart_api_requests.json', 'w') as f:
            json.dump(captured_requests, f, indent=2)
        print('\nSaved all requests to kmart_api_requests.json')

if __name__ == '__main__':
    asyncio.run(investigate_api())
