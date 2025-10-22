"""
Exploration script to analyze Big W website structure
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def explore_bigw():
    """Explore Big W's website to understand its structure"""

    url = "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        # Capture network requests
        api_requests = []

        async def log_request(request):
            if any(keyword in request.url for keyword in ['api', 'graphql', 'product', 'search', 'stock']):
                api_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'resource_type': request.resource_type
                })
                print(f"[API] {request.method} {request.url}")

        page.on('request', log_request)

        print("=" * 80)
        print("Exploring Big W Pokemon Cards Page")
        print("=" * 80)

        try:
            # Navigate to page
            print("\n[1] Loading page...")
            await page.goto(url, wait_until='networkidle', timeout=60000)

            # Wait for products to load
            await asyncio.sleep(5)

            # Check for products
            print("\n[2] Analyzing page structure...")

            # Try to find product elements
            products = await page.evaluate('''() => {
                // Try various selectors
                const selectors = [
                    'div[data-testid*="product"]',
                    'article[data-testid*="product"]',
                    '.product-tile',
                    '.product-card',
                    '[class*="ProductTile"]',
                    '[class*="ProductCard"]',
                    '[data-product-id]'
                ];

                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        return {
                            selector: selector,
                            count: elements.length,
                            sample: elements[0].outerHTML.substring(0, 500)
                        };
                    }
                }

                return null;
            }''')

            if products:
                print(f"\n   Found products using selector: {products['selector']}")
                print(f"   Product count: {products['count']}")
                print(f"   Sample HTML: {products['sample']}...")
            else:
                print("\n   Could not find products with common selectors")

            # Try to extract product data
            print("\n[3] Extracting product data...")

            product_data = await page.evaluate('''() => {
                const products = [];

                // Try to find product containers
                const productElements = document.querySelectorAll(
                    'div[data-testid*="product"], article, [class*="Product"], [data-product-id]'
                );

                for (let i = 0; i < Math.min(3, productElements.length); i++) {
                    const el = productElements[i];

                    // Try to extract data
                    const titleEl = el.querySelector('h2, h3, [class*="title"], [class*="Title"], [class*="name"], [class*="Name"]');
                    const priceEl = el.querySelector('[class*="price"], [class*="Price"], [data-testid*="price"]');
                    const imageEl = el.querySelector('img');
                    const linkEl = el.querySelector('a[href*="product"]');

                    products.push({
                        title: titleEl ? titleEl.textContent.trim() : 'N/A',
                        price: priceEl ? priceEl.textContent.trim() : 'N/A',
                        image: imageEl ? imageEl.src : 'N/A',
                        link: linkEl ? linkEl.href : 'N/A',
                        html_classes: el.className
                    });
                }

                return products;
            }''')

            print(f"\n   Extracted {len(product_data)} product samples:")
            for i, product in enumerate(product_data):
                print(f"\n   Product {i+1}:")
                print(f"      Title: {product['title'][:60]}")
                print(f"      Price: {product['price']}")
                print(f"      Link: {product['link'][:80]}")
                print(f"      Classes: {product['html_classes'][:80]}")

            # Check for pagination
            print("\n[4] Checking pagination...")
            pagination = await page.evaluate('''() => {
                const paginationSelectors = [
                    'nav[aria-label*="pagination"]',
                    '.pagination',
                    '[class*="Pagination"]',
                    'button[aria-label*="next"]'
                ];

                for (const selector of paginationSelectors) {
                    const el = document.querySelector(selector);
                    if (el) {
                        return {
                            selector: selector,
                            html: el.outerHTML.substring(0, 300)
                        };
                    }
                }

                return null;
            }''')

            if pagination:
                print(f"   Found pagination: {pagination['selector']}")
            else:
                print("   No pagination found")

            # Summary of API calls
            print("\n[5] API Calls Summary:")
            print(f"   Total API-related requests: {len(api_requests)}")

            # Group by domain
            domains = {}
            for req in api_requests:
                domain = req['url'].split('/')[2] if '/' in req['url'] else req['url']
                if domain not in domains:
                    domains[domain] = []
                domains[domain].append(req['url'])

            for domain, urls in domains.items():
                print(f"\n   {domain}:")
                for url in urls[:3]:  # Show first 3
                    print(f"      {url}")
                if len(urls) > 3:
                    print(f"      ... and {len(urls) - 3} more")

            # Save API requests to file
            with open('monitors/bigw/api_requests.json', 'w') as f:
                json.dump(api_requests, f, indent=2)

            print("\n[SUCCESS] Exploration complete!")
            print("   API requests saved to: monitors/bigw/api_requests.json")
            print("\n   Press Ctrl+C to close browser...")

            # Keep browser open for manual inspection
            await asyncio.sleep(60)

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(explore_bigw())
