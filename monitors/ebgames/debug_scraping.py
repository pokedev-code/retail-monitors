"""
Debug script to see what's actually on the EB Games page
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_page():
    """Debug what's on the page"""

    url = "https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards&attributes=franchise%3Apokemon"

    print("=" * 80)
    print("Debugging EB Games Page Structure")
    print("=" * 80)
    print(f"\nURL: {url}\n")

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
            print("[1] Loading page...")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)  # Wait longer for dynamic content

            print("[2] Checking for product containers...")

            # Try all possible selectors
            selectors_to_test = [
                '.product-tile',
                '.product-card',
                '[data-product-id]',
                'article',
                '.product-item',
                '[class*="product"]',
                '[class*="item"]'
            ]

            for selector in selectors_to_test:
                count = await page.evaluate(f'''() => {{
                    return document.querySelectorAll('{selector}').length;
                }}''')
                print(f"   {selector}: {count} elements")

            print("\n[3] Looking at first element from each selector...")

            for selector in selectors_to_test:
                print(f"\n   Selector: {selector}")
                element_info = await page.evaluate(f'''() => {{
                    const elem = document.querySelector('{selector}');
                    if (!elem) return null;

                    return {{
                        html: elem.innerHTML.substring(0, 500),
                        classes: elem.className,
                        tagName: elem.tagName
                    }};
                }}''')

                if element_info:
                    print(f"      Tag: {element_info['tagName']}")
                    print(f"      Classes: {element_info['classes']}")
                    print(f"      HTML (first 500 chars):\n{element_info['html'][:200]}...")
                else:
                    print(f"      No elements found")

            print("\n[4] Dumping all text content from page...")
            all_text = await page.evaluate('''() => {
                return document.body.innerText.substring(0, 2000);
            }''')
            print(all_text[:500])

            print("\n\n[5] Waiting 30 seconds for manual inspection...")
            print("    Check the browser window to see what's on the page")
            await asyncio.sleep(30)

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_page())
