"""
Analyze the actual product card structure on Kmart
"""
import asyncio
from playwright.async_api import async_playwright

async def analyze_structure():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

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

        # Scroll to load all products
        print('Scrolling to load all products...')
        for i in range(25):
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(1.5)

        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(2)

        # Analyze the HTML structure
        print('\n=== Analyzing Product Card Structure ===\n')

        # Get the HTML of the first few product cards
        first_products_html = await page.evaluate('''() => {
            // Try different selectors to find product containers
            const selectors = [
                'article',
                '[data-testid*="product"]',
                '[class*="ProductCard"]',
                '[class*="ProductTile"]',
                'div[class*="product" i]',
            ];

            for (const sel of selectors) {
                const elements = document.querySelectorAll(sel);
                if (elements.length > 0) {
                    return {
                        selector: sel,
                        count: elements.length,
                        firstHTML: elements[0] ? elements[0].outerHTML.substring(0, 500) : '',
                        classes: elements[0] ? elements[0].className : ''
                    };
                }
            }
            return null;
        }''')

        if first_products_html:
            print(f'Best selector: {first_products_html["selector"]}')
            print(f'Count: {first_products_html["count"]}')
            print(f'Sample classes: {first_products_html["classes"]}')
            print(f'\nFirst card HTML (truncated):\n{first_products_html["firstHTML"]}\n')

        # Try to extract products with the best selector
        print('\n=== Trying Different Extraction Methods ===\n')

        # Method 1: Look for main product grid container
        products_by_grid = await page.evaluate('''() => {
            // Find the main grid/list container
            const grid = document.querySelector('[class*="grid" i], [class*="list" i], [class*="ProductGrid"]');
            if (!grid) return 0;

            // Count direct children that look like product cards
            const children = Array.from(grid.children).filter(child => {
                const hasLink = child.querySelector('a[href*="/product/"]');
                const hasImage = child.querySelector('img');
                return hasLink && hasImage;
            });

            return children.length;
        }''')
        print(f'Method 1 (Grid container children): {products_by_grid} products')

        # Method 2: Article tags
        articles = await page.evaluate('document.querySelectorAll("article").length')
        print(f'Method 2 (Article tags): {articles} articles')

        # Method 3: Unique product URLs
        unique_urls = await page.evaluate('''() => {
            const links = document.querySelectorAll('a[href*="/product/"]');
            const urls = new Set();
            links.forEach(link => {
                const href = link.href;
                // Only count product pages, not category/filter links
                if (href.match(/\/product\/[^/]+\/\d+/)) {
                    urls.add(href);
                }
            });
            return urls.size;
        }''')
        print(f'Method 3 (Unique product page URLs): {unique_urls} products')

        # Method 4: Check data attributes
        data_products = await page.evaluate('''() => {
            const elements = document.querySelectorAll('[data-product-id], [data-sku], [data-article-number]');
            return elements.length;
        }''')
        print(f'Method 4 (Elements with data-product-id/sku): {data_products} products')

        # Method 5: Look for price elements as indicators
        price_containers = await page.evaluate('''() => {
            const prices = document.querySelectorAll('[class*="price" i]');
            const unique = new Set();
            prices.forEach(price => {
                const card = price.closest('article, div[class*="card" i], div[class*="tile" i]');
                if (card) {
                    const link = card.querySelector('a[href*="/product/"]');
                    if (link) unique.add(link.href);
                }
            });
            return unique.size;
        }''')
        print(f'Method 5 (Price containers with product links): {price_containers} products')

        # Sample a few product URLs
        print('\n=== Sample Product URLs ===\n')
        sample_urls = await page.evaluate('''() => {
            const links = document.querySelectorAll('a[href*="/product/"]');
            const urls = new Set();
            links.forEach(link => {
                if (link.href.match(/\/product\/[^/]+\/\d+/)) {
                    urls.add(link.href);
                }
            });
            return Array.from(urls).slice(0, 5);
        }''')

        for i, url in enumerate(sample_urls):
            print(f'{i+1}. {url}')

        print(f'\n{"="*60}')
        print(f'MOST ACCURATE: Unique product URLs = {unique_urls}')
        print(f'{"="*60}')

        await asyncio.sleep(5)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(analyze_structure())
