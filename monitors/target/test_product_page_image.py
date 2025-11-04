"""
Test Target product page image extraction
"""
import asyncio
from playwright.async_api import async_playwright

# Test with a known Pokemon TCG product URL
TEST_URL = "https://www.target.com.au/p/pokemon-tcg-mega-evolution-blister-assorted/71826668"

async def test_product_page_image():
    """Test image extraction on product detail page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            print(f"Loading: {TEST_URL}")
            await page.goto(TEST_URL, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)  # Wait for content to load

            # Test the same selectors used in monitor_enhanced.py
            image_test = await page.evaluate('''() => {
                let image = '';
                const results = [];

                const imageSelectors = [
                    'img[data-testid="product-image"]',
                    'img[alt*="Pokemon"]',
                    'img[alt*="TCG"]',
                    '.product-image img',
                    'meta[property="og:image"]'
                ];

                for (const selector of imageSelectors) {
                    const imgEl = document.querySelector(selector);
                    if (imgEl) {
                        let foundImage = '';
                        if (selector.startsWith('meta')) {
                            foundImage = imgEl.content;
                        } else {
                            foundImage = imgEl.src;
                        }

                        results.push({
                            selector: selector,
                            found: !!imgEl,
                            src: foundImage,
                            currentSrc: imgEl.currentSrc || 'N/A',
                            alt: imgEl.alt || 'N/A',
                            complete: imgEl.complete || 'N/A',
                            naturalWidth: imgEl.naturalWidth || 'N/A'
                        });

                        if (foundImage) {
                            image = foundImage;
                            break;
                        }
                    } else {
                        results.push({
                            selector: selector,
                            found: false
                        });
                    }
                }

                return { image, results };
            }''')

            print("\n" + "="*80)
            print("PRODUCT PAGE IMAGE EXTRACTION TEST")
            print("="*80)

            print(f"\nFinal image chosen: {image_test['image'][:100]}..." if image_test['image'] else "\n[ERROR] No image found!")

            print("\nSelector results:")
            for i, result in enumerate(image_test['results'], 1):
                print(f"\n{i}. Selector: {result['selector']}")
                if result['found']:
                    print(f"   [FOUND]")
                    print(f"   src: {result['src'][:80]}...")
                    print(f"   alt: {result['alt'][:50]}...")
                    print(f"   complete: {result['complete']}")
                    print(f"   naturalWidth: {result['naturalWidth']}")
                else:
                    print(f"   [NOT FOUND]")

            print("\n" + "="*80)

            # Check if it's a placeholder/broken image
            if image_test['image']:
                if 'data:image' in image_test['image']:
                    print("[WARNING] Image is a data: URL (placeholder)")
                elif 'assets.target.com.au' in image_test['image']:
                    print("[SUCCESS] Valid Target CDN image URL")
                else:
                    print(f"[INFO] Image domain: {image_test['image'].split('/')[2]}")

            print("="*80)

            # Keep browser open
            print("\nKeeping browser open for 15 seconds for inspection...")
            await asyncio.sleep(15)

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_product_page_image())
