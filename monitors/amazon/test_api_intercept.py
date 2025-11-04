"""
Test script to intercept and analyze Amazon.com.au API requests
Monitors network traffic to identify any GraphQL/REST API endpoints
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def intercept_requests():
    """Intercept and log all network requests from Amazon search page"""

    api_calls = []

    def handle_request(request):
        """Log API requests"""
        url = request.url
        method = request.method
        resource_type = request.resource_type

        # Look for XHR/Fetch requests (potential API calls)
        if resource_type in ['xhr', 'fetch']:
            print(f"\n[API CALL] {method} {url}")
            api_calls.append({
                'method': method,
                'url': url,
                'type': resource_type,
                'headers': request.headers
            })

    def handle_response(response):
        """Log API responses"""
        url = response.url

        # Check if it's a JSON response
        if 'json' in response.headers.get('content-type', ''):
            print(f"[JSON RESPONSE] {url}")
            print(f"  Status: {response.status}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        # Attach event listeners
        page.on('request', handle_request)
        page.on('response', handle_response)

        print("=" * 80)
        print("AMAZON API INTERCEPTOR - Looking for API endpoints...")
        print("=" * 80)
        print("\nLoading Amazon search page...")

        # Navigate to Amazon search
        await page.goto('https://www.amazon.com.au/s?k=pokemon+cards', wait_until='networkidle')

        print("\n" + "=" * 80)
        print("Network activity captured!")
        print("=" * 80)

        # Analyze captured API calls
        if api_calls:
            print(f"\n[ANALYSIS] Found {len(api_calls)} API calls:")

            # Look for GraphQL
            graphql_calls = [c for c in api_calls if 'graphql' in c['url'].lower()]
            if graphql_calls:
                print(f"\n✓ FOUND {len(graphql_calls)} GraphQL endpoints:")
                for call in graphql_calls:
                    print(f"  - {call['method']} {call['url']}")

            # Look for API endpoints
            api_endpoints = [c for c in api_calls if '/api/' in c['url'] or 'api.' in c['url']]
            if api_endpoints:
                print(f"\n✓ FOUND {len(api_endpoints)} API endpoints:")
                for call in api_endpoints:
                    print(f"  - {call['method']} {call['url']}")

            # Look for search-related calls
            search_calls = [c for c in api_calls if 'search' in c['url'].lower() or 's?k=' in c['url']]
            if search_calls:
                print(f"\n✓ FOUND {len(search_calls)} search-related calls:")
                for call in search_calls:
                    print(f"  - {call['method']} {call['url']}")

            # Save all API calls to file
            with open('amazon_api_calls.json', 'w') as f:
                json.dump(api_calls, f, indent=2)
            print(f"\n[SAVED] All API calls saved to amazon_api_calls.json")

        else:
            print("\n[NO API CALLS] No XHR/Fetch requests detected.")
            print("Amazon may be using server-side rendering without client-side API calls.")

        print("\nBrowser will close in 30 seconds...")
        print("Review the output above to see if any API endpoints were found.\n")
        await asyncio.sleep(30)

        await browser.close()

if __name__ == '__main__':
    print("\nThis script will:")
    print("1. Open Amazon.com.au search page")
    print("2. Monitor all network requests")
    print("3. Identify any API endpoints (GraphQL, REST, etc.)")
    print("4. Save results to amazon_api_calls.json")
    print("\nStarting in 3 seconds...\n")

    asyncio.run(intercept_requests())
