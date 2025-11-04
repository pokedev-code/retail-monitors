"""
Test to inspect pagination buttons on page 2
"""
import asyncio
from playwright.async_api import async_playwright

async def inspect_pagination():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(2)

        # Go to page 2
        print('Clicking page 2...')
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)
        page2_button = await page.query_selector('button.MuiPaginationItem-page:has-text("2")')
        if page2_button:
            await page2_button.click()
            await asyncio.sleep(3)
            print('On page 2 now\n')

        # Inspect pagination structure
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)

        # Get all pagination buttons
        all_buttons = await page.query_selector_all('button.MuiPaginationItem-page')
        print(f'Found {len(all_buttons)} pagination buttons:')
        for btn in all_buttons:
            text = await btn.inner_text()
            is_disabled = await btn.is_disabled()
            is_visible = await btn.is_visible()
            print(f'  - Text: "{text}", Disabled: {is_disabled}, Visible: {is_visible}')

        # Check for next button
        print('\nLooking for next/arrow buttons...')
        next_buttons = await page.query_selector_all('button[aria-label*="next"], button[aria-label*="Go to next"]')
        for btn in next_buttons:
            aria_label = await btn.get_attribute('aria-label')
            is_disabled = await btn.is_disabled()
            print(f'  - Aria-label: "{aria_label}", Disabled: {is_disabled}')

        # Take screenshot
        await page.screenshot(path='pagination_page2.png', full_page=False)
        print('\nScreenshot saved as pagination_page2.png')

        await asyncio.sleep(5)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(inspect_pagination())
