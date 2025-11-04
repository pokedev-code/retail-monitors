"""
Quick test of the updated scroll + DOM extraction logic
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

async def test_monitor():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        logging.info('Loading Kmart Pokemon cards page...')
        await page.goto('https://www.kmart.com.au/category/toys/pokemon-trading-cards/')
        await asyncio.sleep(3)

        # Close popups
        try:
            close_btn = await page.query_selector('button[aria-label*="close" i]')
            if close_btn:
                await close_btn.click()
                await asyncio.sleep(1)
        except:
            pass

        logging.info('Scrolling to load all products via infinite scroll...')

        prev_product_count = 0
        no_change_count = 0
        max_scrolls = 40

        for scroll_num in range(max_scrolls):
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(1.5)

            current_product_count = await page.evaluate('''() => {
                const products = document.querySelectorAll('a[href*="/product/"]');
                const unique = new Set();
                products.forEach(p => {
                    if (p.href.includes('/product/')) {
                        unique.add(p.href);
                    }
                });
                return unique.size;
            }''')

            if current_product_count != prev_product_count:
                logging.info(f'Scroll {scroll_num + 1}: {current_product_count} products loaded')
                no_change_count = 0
                prev_product_count = current_product_count
            else:
                no_change_count += 1
                if no_change_count >= 5:
                    logging.info(f'No new products after 5 scrolls - all products loaded ({current_product_count} total)')
                    break

        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(1)

        logging.info('Extracting product data from DOM...')
        dom_products = await page.evaluate('''() => {
            const productLinks = document.querySelectorAll('a[href*="/product/"]');
            const products = [];
            const seen = new Set();

            productLinks.forEach(link => {
                const url = link.href;
                if (!url.includes('/product/') || seen.has(url)) return;
                seen.add(url);

                const card = link.closest('article, div[class*="Product"], div[class*="Tile"]') || link;
                const titleEl = card.querySelector('[class*="title" i], h2, h3, [class*="name" i]');
                const priceEl = card.querySelector('[class*="price" i], [class*="Price"]');
                const imageEl = card.querySelector('img');

                products.push({
                    url: url,
                    title: titleEl ? titleEl.innerText.trim() : '',
                    price: priceEl ? priceEl.innerText.trim() : '',
                    image: imageEl ? (imageEl.src || imageEl.dataset.src || '') : ''
                });
            });

            return products;
        }''')

        logging.info(f'Extracted {len(dom_products)} products from DOM')

        print('\n' + '='*60)
        print(f'SUCCESS: Found {len(dom_products)} Pokemon card products')
        print(f'Expected: ~76-120 products')
        print('='*60)

        if len(dom_products) > 0:
            print(f'\nFirst 5 products:')
            for i, p in enumerate(dom_products[:5]):
                print(f'  {i+1}. {p["title"][:50]}... (${p["price"]})')

        await asyncio.sleep(3)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_monitor())
