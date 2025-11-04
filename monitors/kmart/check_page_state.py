"""
Check if location/filters are affecting product display
"""
import asyncio
from playwright.async_api import async_playwright

async def check_page_state():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(5)

        # Close any popups
        try:
            close_btn = await page.query_selector('button[aria-label*="close" i], button:has-text("×")')
            if close_btn:
                await close_btn.click()
                await asyncio.sleep(1)
        except:
            pass

        # Scroll down the ENTIRE page to see how many products load
        print('Scrolling through entire page...')
        prev_height = 0
        scroll_count = 0

        while scroll_count < 30:  # Max 30 scrolls
            # Scroll down
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(1)

            # Get current scroll position
            current_height = await page.evaluate('window.pageYOffset')

            scroll_count += 1

            # Count visible products
            product_count = await page.evaluate('''() => {
                const products = document.querySelectorAll('a[href*="/product/"]');
                const unique = new Set();
                products.forEach(p => {
                    if (p.href.includes('/product/')) {
                        unique.add(p.href);
                    }
                });
                return unique.size;
            }''')

            print(f'Scroll {scroll_count}: {product_count} unique products visible')

            # Check if we hit bottom
            at_bottom = await page.evaluate('''() => {
                return (window.innerHeight + window.pageYOffset) >= document.body.scrollHeight - 100;
            }''')

            if at_bottom:
                print('Reached bottom of page')
                break

        # Final count
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(2)

        final_count = await page.evaluate('''() => {
            const products = document.querySelectorAll('a[href*="/product/"]');
            const unique = new Set();
            products.forEach(p => {
                if (p.href.includes('/product/')) {
                    unique.add(p.href);
                }
            });
            return unique.size;
        }''')

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

        # Check the "X of Y Products" text
        page_text = await page.content()
        import re
        match = re.search(r'(\d+)-(\d+)\s+of\s+(\d+)\s+Products', page_text, re.IGNORECASE)

        print(f'\n{"="*60}')
        if match:
            print(f'Page header says: "{match.group(0)}"')
        print(f'Unique product URLs in DOM: {final_count}')
        print(f'JSON-LD items: {jsonld_count}')
        print(f'{"="*60}')

        # Take full page screenshot
        await page.screenshot(path='kmart_fullpage.png', full_page=True)
        print('\nFull page screenshot saved as kmart_fullpage.png')

        await asyncio.sleep(5)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(check_page_state())
