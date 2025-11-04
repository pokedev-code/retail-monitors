"""
Quick test to see what selectors are available on Kmart category page
"""
import asyncio
from playwright.async_api import async_playwright

async def test_selectors():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        url = "https://www.kmart.com.au/category/toys/pokemon-trading-cards/"
        print(f"Loading: {url}")

        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(3)  # Wait for JS to load

        # Test selectors
        print("\n=== TESTING SELECTORS ===\n")

        # JSON-LD
        json_ld = await page.query_selector_all('script[type="application/ld+json"]')
        print(f"1. JSON-LD scripts: {len(json_ld)} found")

        # Product links
        product_links = await page.query_selector_all('a[href*="/product/"]')
        print(f"2. Product links (a[href*=\"/product/\"]): {len(product_links)} found")

        # Alternative: /p/ links
        p_links = await page.query_selector_all('a[href*="/p/"]')
        print(f"3. /p/ links: {len(p_links)} found")

        # Get page content sample
        print("\n=== CHECKING PAGE HTML ===\n")

        # Check for product cards
        content_check = await page.evaluate('''() => {
            const results = {
                hasJsonLd: document.querySelectorAll('script[type="application/ld+json"]').length,
                hasProductLinks: document.querySelectorAll('a[href*="/product/"]').length,
                hasPLinks: document.querySelectorAll('a[href*="/p/"]').length,

                // Try various product card selectors
                productCards: document.querySelectorAll('div[class*="ProductCard"]').length,
                productCardAlt: document.querySelectorAll('div[class*="product-card"]').length,
                productDivs: document.querySelectorAll('div[class*="product"]').length,

                // Get first product link if exists
                firstProductLink: '',
                firstProductTitle: ''
            };

            const firstLink = document.querySelector('a[href*="/product/"]');
            if (firstLink) {
                results.firstProductLink = firstLink.href;
                results.firstProductTitle = firstLink.textContent.trim();
            }

            return results;
        }''')

        print(f"JSON-LD scripts: {content_check['hasJsonLd']}")
        print(f"Product links: {content_check['hasProductLinks']}")
        print(f"/p/ links: {content_check['hasPLinks']}")
        print(f"ProductCard divs: {content_check['productCards']}")
        print(f"product-card divs: {content_check['productCardAlt']}")
        print(f"Product divs (generic): {content_check['productDivs']}")

        if content_check['firstProductLink']:
            print(f"\nFirst product found:")
            print(f"  Title: {content_check['firstProductTitle'][:100]}")
            print(f"  URL: {content_check['firstProductLink']}")

        # Get JSON-LD content if exists
        if content_check['hasJsonLd'] > 0:
            print("\n=== JSON-LD CONTENT ===\n")
            json_content = await page.evaluate('''() => {
                const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                return scripts.map(s => s.textContent).join('\\n---\\n');
            }''')
            print(json_content[:1000])  # First 1000 chars

        print("\n\nBrowser will stay open for 10 seconds for manual inspection...")
        await asyncio.sleep(10)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_selectors())
