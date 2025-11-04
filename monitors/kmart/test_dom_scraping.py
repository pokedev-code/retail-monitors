"""
Test scraping products directly from DOM after scrolling
"""
import asyncio
from playwright.async_api import async_playwright
import re

async def test_dom_scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = "https://www.kmart.com.au/category/toys/pokemon-trading-cards/"
        print(f"Loading: {url}\n")

        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(3)

        # Scroll to load all products
        print("Scrolling to load all products...\n")
        for i in range(6):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)

            # Count product links
            count = await page.evaluate('document.querySelectorAll("a[href*=\\"/product/\\"]").length')
            print(f"  Scroll {i+1}: {count} product links found")

        print("\nExtracting product data from DOM...\n")

        # Extract all product links
        products = await page.evaluate('''() => {
            const productLinks = Array.from(document.querySelectorAll('a[href*="/product/"]'));
            const seen = new Set();
            const products = [];

            productLinks.forEach(link => {
                const url = link.href;

                // Extract product ID from URL
                const match = url.match(/-(\d+)\/?$/);
                if (!match) return;

                const productId = match[1];

                // Skip duplicates
                if (seen.has(productId)) return;
                seen.add(productId);

                // Try to find title
                let title = link.getAttribute('aria-label') || link.textContent.trim();

                // Clean up title
                title = title.replace(/^Add\\s+/i, '').replace(/\\s+to\\s+(bag|cart).*$/i, '').trim();

                if (!title || title.length < 5) {
                    // Try to find title in nearby elements
                    const parent = link.closest('[class*="product"], [class*="card"], li, article');
                    if (parent) {
                        const titleElem = parent.querySelector('h2, h3, h4, [class*="title"], [class*="name"]');
                        if (titleElem) {
                            title = titleElem.textContent.trim();
                        }
                    }
                }

                // Find image
                let image = '';
                const img = link.querySelector('img');
                if (img) {
                    image = img.src || img.dataset.src || img.getAttribute('data-src') || '';
                }

                if (productId && title && title.length > 5) {
                    products.push({
                        product_id: productId,
                        title: title,
                        url: url,
                        image: image
                    });
                }
            });

            return products;
        }''')

        print(f"Found {len(products)} unique products\n")

        # Show first 5
        for i, product in enumerate(products[:5]):
            print(f"Product {i+1}:")
            print(f"  ID: {product['product_id']}")
            print(f"  Title: {product['title'][:80]}")
            print(f"  URL: {product['url'][:100]}...")
            print()

        print(f"\nTOTAL: {len(products)} products")

        await asyncio.sleep(5)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_dom_scrape())
