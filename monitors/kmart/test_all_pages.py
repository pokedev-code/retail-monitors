"""
Manually test clicking through all visible page numbers
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

        total_products = []

        for page_num in range(1, 6):  # Try pages 1-5
            print(f'\n--- Attempting Page {page_num} ---')

            # Scroll to pagination
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)

            # Get current page's products
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

            print(f'Found {len(products)} products on page {page_num}')
            total_products.extend(products)

            # Try to click next page
            next_num = page_num + 1
            button = await page.query_selector(f'button.MuiPaginationItem-page:has-text("{next_num}")')

            if button:
                is_visible = await button.is_visible()
                is_disabled = await button.is_disabled()
                print(f'Page {next_num} button: visible={is_visible}, disabled={is_disabled}')

                if is_visible and not is_disabled:
                    print(f'Clicking page {next_num}...')
                    await button.click()
                    await asyncio.sleep(3)
                else:
                    print(f'Cannot click page {next_num} - stopping')
                    break
            else:
                print(f'No page {next_num} button found - stopping')
                break

        print('\n' + '='*60)
        print(f'TOTAL PRODUCTS COLLECTED: {len(total_products)}')
        print(f'EXPECTED: 76')
        print('='*60)

        await asyncio.sleep(3)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_all_pages())
