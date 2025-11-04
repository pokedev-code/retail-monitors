"""
Test scrolling FIRST on each page to load all products, THEN extract JSON-LD
"""
import asyncio
from playwright.async_api import async_playwright

async def test_scroll_per_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(3)

        total_products = []

        for page_num in [1, 2]:
            print(f'\n--- Page {page_num} ---')

            # FIRST: Scroll to load all products on this page
            print('Scrolling to load all products...')
            for scroll in range(10):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)

                # Check how many items in JSON-LD now
                item_count = await page.evaluate('''() => {
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

                print(f'  Scroll {scroll+1}: {item_count} items in JSON-LD')

                # If we've reached the pagination, stop scrolling this page
                pagination_visible = await page.evaluate('''() => {
                    const pagination = document.querySelector('.MuiPagination-ul');
                    if (!pagination) return false;
                    const rect = pagination.getBoundingClientRect();
                    return rect.top < window.innerHeight;
                }''')

                if pagination_visible:
                    print(f'  Reached pagination after {scroll+1} scrolls')
                    break

            # Scroll back to top
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(1)

            # NOW extract all products from JSON-LD
            products = await page.evaluate('''() => {
                const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                for (const script of scripts) {
                    try {
                        const data = JSON.parse(script.textContent);
                        if (data['@type'] === 'ItemList') {
                            return data.itemListElement || [];
                        }
                    } catch(e) {}
                }
                return [];
            }''')

            print(f'FINAL: Extracted {len(products)} products from page {page_num}')
            total_products.extend(products)

            if page_num == 1:
                # Click to page 2
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(1)
                page2_btn = await page.query_selector('button.MuiPaginationItem-page:has-text("2")')
                if page2_btn:
                    print('\nClicking page 2...')
                    await page2_btn.click()
                    await asyncio.sleep(3)

        print('\n' + '='*60)
        print(f'TOTAL PRODUCTS: {len(total_products)}')
        print(f'EXPECTED: 76 (60 from page 1 + 16 from page 2)')
        print('='*60)

        await asyncio.sleep(3)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_scroll_per_page())
