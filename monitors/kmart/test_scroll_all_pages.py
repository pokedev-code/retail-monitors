"""
Test if we need to paginate to get all 76 products
"""
import asyncio
from playwright.async_api import async_playwright

async def test_all_pages():
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

        all_products = []

        # Page 1
        print('=== PAGE 1 ===')
        # Scroll to load all on page 1
        for i in range(25):
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(1)

        page1_products = await page.evaluate('''() => {
            const grid = document.querySelector('[class*="grid" i], [class*="list" i], main');
            if (!grid) return 0;
            const cards = Array.from(grid.querySelectorAll('[data-testid*="product"], [data-product-id]')).filter(el => {
                const link = el.querySelector('a[href*="/product/"]');
                return link !== null;
            });
            return cards.length;
        }''')

        print(f'Page 1: {page1_products} products')
        all_products.extend([f'p1-{i}' for i in range(page1_products)])

        # Try to go to page 2
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)

        page2_button = await page.query_selector('button.MuiPaginationItem-page:has-text("2")')
        if page2_button and await page2_button.is_visible() and not await page2_button.is_disabled():
            print('\n=== CLICKING PAGE 2 ===')
            await page2_button.click()
            await asyncio.sleep(3)

            # Scroll page 2
            for i in range(15):
                await page.evaluate('window.scrollBy(0, 500)')
                await asyncio.sleep(1)

            page2_products = await page.evaluate('''() => {
                const grid = document.querySelector('[class*="grid" i], [class*="list" i], main');
                if (!grid) return 0;
                const cards = Array.from(grid.querySelectorAll('[data-testid*="product"], [data-product-id]')).filter(el => {
                    const link = el.querySelector('a[href*="/product/"]');
                    return link !== null;
                });
                return cards.length;
            }''')

            print(f'Page 2: {page2_products} products')
            all_products.extend([f'p2-{i}' for i in range(page2_products)])
        else:
            print('\nNo page 2 button found or disabled')

        print(f'\n{"="*60}')
        print(f'TOTAL: {len(all_products)} products')
        print(f'EXPECTED: 76 products')
        print(f'{"="*60}')

        await asyncio.sleep(3)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_all_pages())
