"""
Test Target image extraction to see what URLs are being captured
"""
import asyncio
from playwright.async_api import async_playwright
import sys
sys.path.insert(0, '.')
import config

async def test_image_extraction():
    """Test what image URLs are being captured"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # Load search page
            search_url = config.BASE_URL + '+'.join(config.KEYWORDS)
            print(f"Loading: {search_url}")
            await page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)  # Wait for lazy loading

            # Extract image information
            image_info = await page.evaluate('''() => {
                const products = [];
                const links = document.querySelectorAll('a[href*="/p/"]');

                links.forEach((link, index) => {
                    if (index >= 5) return;  // Only first 5 products

                    const img = link.querySelector('img');
                    if (img) {
                        products.push({
                            title: img.alt || 'No alt',
                            src: img.src || 'No src',
                            srcset: img.srcset || 'No srcset',
                            currentSrc: img.currentSrc || 'No currentSrc',
                            dataSrc: img.getAttribute('data-src') || 'No data-src',
                            loading: img.loading || 'No loading attr',
                            complete: img.complete,
                            naturalWidth: img.naturalWidth
                        });
                    }
                });

                return products;
            }''')

            print("\n" + "="*80)
            print("IMAGE EXTRACTION TEST RESULTS")
            print("="*80)

            for i, info in enumerate(image_info, 1):
                print(f"\nProduct {i}:")
                print(f"  Title: {info['title'][:50]}...")
                print(f"  src: {info['src'][:80]}...")
                print(f"  currentSrc: {info['currentSrc'][:80]}..." if info['currentSrc'] != 'No currentSrc' else "  currentSrc: None")
                print(f"  srcset: {info['srcset'][:80]}..." if info['srcset'] != 'No srcset' else "  srcset: None")
                print(f"  data-src: {info['dataSrc']}")
                print(f"  loading: {info['loading']}")
                print(f"  complete: {info['complete']}")
                print(f"  naturalWidth: {info['naturalWidth']} (0 = not loaded)")

            print("\n" + "="*80)
            print("ANALYSIS:")

            # Check for common patterns
            has_data_url = any('data:image' in info['src'] for info in image_info)
            has_srcset = any(info['srcset'] != 'No srcset' for info in image_info)
            all_complete = all(info['complete'] for info in image_info)

            if has_data_url:
                print("  [ISSUE] Found data: URLs (placeholder images)")
            if has_srcset:
                print("  [INFO] Images use srcset (responsive images)")
            if not all_complete:
                print("  [ISSUE] Some images not fully loaded")

            print("\nRECOMMENDATION:")
            if has_srcset:
                print("  Use img.currentSrc (the actual loaded image from srcset)")
            elif has_data_url:
                print("  Wait longer for lazy loading or use data-src attribute")
            else:
                print("  img.src should work fine")

            print("="*80)

            # Keep browser open
            print("\nKeeping browser open for 10 seconds for inspection...")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_image_extraction())
