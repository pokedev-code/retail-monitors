"""
Count actual product cards visible in the DOM vs JSON-LD
"""
import asyncio
from playwright.async_api import async_playwright

async def count_dom_products():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(3)

        # Scroll entire page multiple times to load everything
        print('Scrolling page 1 to load all products...')
        for i in range(15):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)

        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(2)

        # Count products in JSON-LD
        jsonld_count = await page.evaluate('''() => {
            const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
            for (const script of scripts) {
                try {
                    const data = JSON.parse(script.textContent);
                    if (data['@type'] === 'ItemList') {
                        return data.itemListElement ? data.itemListElement.length : 0;
                    }
                } catch(e) {}
            }
            return 0;
        }''')

        # Try multiple selectors to find product cards in DOM
        dom_selectors = [
            'article[data-testid="product-tile"]',
            '[data-testid="product-tile"]',
            'article.product-tile',
            '.product-tile',
            'article',
            'a[href*="/product/pokemon"]',
            'a[href*="/product/"]',
            '[class*="ProductCard"]',
            '[class*="ProductTile"]',
        ]

        print('\nCounting products in DOM with different selectors:')
        for selector in dom_selectors:
            count = await page.evaluate(f'''() => {{
                const elements = document.querySelectorAll('{selector}');
                // Get unique products by checking href to avoid counting duplicates
                const unique = new Set();
                elements.forEach(el => {{
                    const link = el.querySelector('a[href*="/product/"]') || el;
                    if (link.href && link.href.includes('/product/')) {{
                        unique.add(link.href);
                    }}
                }});
                return unique.size || elements.length;
            }}''')
            if count > 0:
                print(f'  {selector}: {count}')

        # Get actual product links
        product_links = await page.evaluate('''() => {
            const links = document.querySelectorAll('a[href*="/product/"]');
            const unique = new Set();
            links.forEach(link => {
                if (link.href.includes('/product/')) {
                    unique.add(link.href);
                }
            });
            return Array.from(unique);
        }''')

        print(f'\n{"="*60}')
        print(f'JSON-LD items: {jsonld_count}')
        print(f'Unique product URLs in DOM: {len(product_links)}')
        print(f'{"="*60}')

        if len(product_links) > 40:
            print(f'\nFirst 10 product URLs:')
            for i, url in enumerate(product_links[:10]):
                print(f'  {i+1}. {url.split("/product/")[-1][:50]}...')

        await asyncio.sleep(3)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(count_dom_products())
