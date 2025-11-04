"""
Test using Next arrow button instead of numbered buttons
"""
import asyncio
from playwright.async_api import async_playwright

async def test_next_arrow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(3)

        total_products = []
        page_num = 1

        while page_num <= 10:
            print(f'\n--- Page {page_num} ---')

            # Get products
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

            print(f'Found {len(products)} products')
            total_products.extend(products)

            # Scroll to pagination
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)

            # List ALL pagination buttons to see what's available
            all_buttons = await page.evaluate('''() => {
                const buttons = Array.from(document.querySelectorAll('.MuiPagination-ul button'));
                return buttons.map(btn => ({
                    text: btn.innerText.trim(),
                    ariaLabel: btn.getAttribute('aria-label'),
                    disabled: btn.disabled,
                    className: btn.className
                }));
            }''')

            print(f'All pagination buttons:')
            for btn in all_buttons:
                print(f'  - Text: "{btn["text"]}", Label: {btn["ariaLabel"]}, Disabled: {btn["disabled"]}')

            # Try to find and click "Next" button (using aria-label or icon)
            next_clicked = False

            # Method 1: Try aria-label
            next_button = await page.query_selector('button[aria-label*="next" i]:not([disabled])')
            if next_button and await next_button.is_visible():
                print('Clicking Next button (via aria-label)...')
                await next_button.click()
                await asyncio.sleep(3)
                next_clicked = True

            if not next_clicked:
                # Method 2: Try the last non-disabled button (usually Next arrow)
                next_button = await page.query_selector('.MuiPagination-ul li:last-child button:not([disabled])')
                if next_button and await next_button.is_visible():
                    print('Clicking last button (likely Next arrow)...')
                    await next_button.click()
                    await asyncio.sleep(3)
                    next_clicked = True

            if not next_clicked:
                print('No more pages available')
                break

            page_num += 1

        print('\n' + '='*60)
        print(f'TOTAL PRODUCTS: {len(total_products)} (visited {page_num} pages)')
        print('='*60)

        await asyncio.sleep(3)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_next_arrow())
