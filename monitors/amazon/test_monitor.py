"""
Test script for Amazon monitor
Runs a single scrape without sending Discord notifications
"""
import asyncio
import sys
from playwright.async_api import async_playwright

# Import config
import config

async def test_scrape():
    """Test scraping Amazon search page"""
    print("=" * 80)
    print("AMAZON AU MONITOR - TEST MODE")
    print("=" * 80)
    print(f"Search URL: {config.SEARCH_URL}")
    print(f"Max Pages: {config.MAX_PAGES}")
    print(f"Prime Only: {config.PRIME_ONLY}")
    print(f"In Stock Only: {config.ONLY_IN_STOCK}")
    if config.MIN_PRICE or config.MAX_PRICE:
        print(f"Price Range: ${config.MIN_PRICE or 0} - ${config.MAX_PRICE or '∞'}")
    print("=" * 80)
    print("\n[TEST] Launching browser (visible window)...\n")

    async with async_playwright() as p:
        # Launch browser in non-headless mode for testing
        browser = await p.chromium.launch(
            headless=False,  # Always visible for testing
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--window-size=1920,1080'
            ]
        )

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        # Add stealth scripts
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-AU', 'en-US', 'en']
            });
        """)

        page = await context.new_page()

        try:
            # Navigate to search page
            print(f"[TEST] Loading: {config.SEARCH_URL}")
            await page.goto(config.SEARCH_URL, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)

            # Extract products
            print("[TEST] Extracting products...\n")
            products = await page.evaluate('''() => {
                const products = [];
                const productContainers = document.querySelectorAll('div[data-asin]:not([data-asin=""])');

                productContainers.forEach(container => {
                    try {
                        const asin = container.getAttribute('data-asin');
                        if (!asin) return;

                        // Extract title
                        let title = '';
                        const titleElem = container.querySelector('h2 a span, h2 span');
                        if (titleElem) title = titleElem.textContent.trim();
                        if (!title) return;

                        // Extract URL
                        const linkElem = container.querySelector('h2 a');
                        const url = linkElem ? linkElem.href : '';

                        // Extract price
                        let price = null;
                        const priceElem = container.querySelector('.a-price .a-offscreen');
                        if (priceElem) price = priceElem.textContent.trim();

                        // Extract rating
                        let rating = null;
                        const ratingElem = container.querySelector('span.a-icon-alt');
                        if (ratingElem) {
                            const match = ratingElem.textContent.match(/([\\d.]+) out of 5/);
                            if (match) rating = match[1];
                        }

                        // Extract review count
                        let reviews = null;
                        const reviewElem = container.querySelector('span.a-size-base.s-underline-text');
                        if (reviewElem) {
                            const match = reviewElem.textContent.match(/([\\d,]+)/);
                            if (match) reviews = match[1];
                        }

                        // Check if Prime
                        const isPrime = container.querySelector('i.a-icon-prime') !== null;

                        // Check stock
                        let inStock = true;
                        const stockElem = container.querySelector('.a-color-price');
                        if (stockElem && stockElem.textContent.toLowerCase().includes('out of stock')) {
                            inStock = false;
                        }

                        products.push({
                            asin: asin,
                            title: title,
                            url: url,
                            price: price,
                            rating: rating,
                            reviews: reviews,
                            is_prime: isPrime,
                            in_stock: inStock
                        });
                    } catch (e) {
                        console.error('Error:', e);
                    }
                });

                return products;
            }''')

            print(f"[TEST] Found {len(products)} products\n")
            print("=" * 80)

            # Display products
            for i, product in enumerate(products, 1):
                print(f"\n[{i}] {product['title'][:80]}")
                print(f"    ASIN: {product['asin']}")
                print(f"    Price: {product['price'] or 'N/A'}")
                print(f"    Rating: {product['rating']} ⭐ ({product['reviews'] or 'N/A'} reviews)" if product['rating'] else "    Rating: N/A")
                print(f"    Prime: {'✓ Yes' if product['is_prime'] else '✗ No'}")
                print(f"    Stock: {'✓ In Stock' if product['in_stock'] else '✗ Out of Stock'}")
                print(f"    URL: {product['url'][:100]}...")

            print("\n" + "=" * 80)
            print(f"\n[TEST] Total: {len(products)} products")
            print("\n[TEST] Test complete! Browser will close in 10 seconds...")
            print("[TEST] Check if products match your expectations.")
            print("[TEST] If CAPTCHA appeared, you may need to:")
            print("        - Increase DELAY to 120+ seconds")
            print("        - Add proxies (see Big W README)")
            print("        - Reduce scraping frequency")

            await asyncio.sleep(10)

        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()
            print("\n[TEST] Browser will stay open for 30 seconds for debugging...")
            await asyncio.sleep(30)

        finally:
            await browser.close()
            print("\n[TEST] Browser closed")


if __name__ == '__main__':
    print("\nStarting test in 3 seconds...")
    print("This will open a visible browser window.\n")
    asyncio.run(test_scrape())
