"""
Test just the JavaScript extraction to see what's failing
"""
import asyncio
from playwright.async_api import async_playwright

async def test_extraction():
    """Test JavaScript extraction"""

    url = "https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards&attributes=franchise%3Apokemon"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-AU',
            timezone_id='Australia/Sydney'
        )

        page = await context.new_page()

        try:
            print("Loading page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)

            print("\nTesting extraction...")

            # Test extraction with title cleaning
            products_data = await page.evaluate('''() => {
                const products = [];

                const productElements = Array.from(document.querySelectorAll('.product-tile'));
                console.log(`Found ${productElements.length} product elements`);

                productElements.forEach((card, index) => {
                    try {
                        // Extract title
                        let title = '';
                        const titleSelectors = [
                            '.product-name',
                            '.product-title',
                            '[class*="product-name"]',
                            'a[class*="name"]',
                            'h3',
                            'h2',
                            'h4'
                        ];

                        for (const sel of titleSelectors) {
                            const elem = card.querySelector(sel);
                            if (elem && elem.textContent.trim()) {
                                let text = elem.textContent.trim();

                                if (text.length > 10) {
                                    title = text;
                                    break;
                                }
                            }
                        }

                        // Clean up title after extraction
                        if (title) {
                            console.log(`BEFORE CLEANING: "${title}"`);

                            // Remove prices at the start
                            title = title.replace(/^\\$[\\d.]+\\s*(\\([^)]+\\))?\\s*/, '');
                            // Remove PREORDER and everything after it
                            title = title.replace(/\\s*PREORDER.*$/i, '');
                            // Remove delivery/collect at the end
                            title = title.replace(/\\s*Delivery\\s*Collect\\s*$/i, '');
                            // Remove "Trading Cards" text
                            title = title.replace(/\\s*Trading Cards\\s*/i, ' ');
                            // Clean up extra whitespace
                            title = title.replace(/\\s+/g, ' ').trim();

                            console.log(`AFTER CLEANING: "${title}"`);
                        }

                        // Extract URL
                        const linkElem = card.querySelector('a[href]');
                        let url = linkElem ? linkElem.href : '';

                        // Extract product ID
                        let productId = card.getAttribute('data-product-id');
                        if (!productId && url) {
                            const match = url.match(/\\/(\\d+)-/);
                            if (match) productId = match[1];
                        }

                        if (title && url && productId) {
                            products.push({
                                title: title,
                                url: url,
                                product_id: productId
                            });
                        } else {
                            console.log(`Skipped product ${index}: title="${title}", url="${url}", id="${productId}"`);
                        }
                    } catch (e) {
                        console.error('Error parsing product:', e);
                    }
                });

                console.log(`Returning ${products.length} products`);
                return products;
            }''')

            print(f"\n\nExtracted {len(products_data)} products\n")

            if products_data:
                for i, product in enumerate(products_data[:3]):
                    print(f"\nProduct {i+1}:")
                    print(f"   ID: {product['product_id']}")
                    print(f"   Title: {product['title']}")
                    print(f"   URL: {product['url'][:80]}...")

            print("\n\nWaiting 10 seconds...")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_extraction())
