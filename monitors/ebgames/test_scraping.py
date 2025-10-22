"""
Test scraping EB Games product page with BeautifulSoup
"""
import requests
from bs4 import BeautifulSoup
import json
import re

def test_scrape_product():
    """Test scraping a single product page"""

    product_url = "https://www.ebgames.com.au/product/toys-and-collectibles/334666-pokemon-tcg-dec-25-collectors-chest"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-AU,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }

    print("=" * 80)
    print("Testing EB Games Product Scraping with BeautifulSoup")
    print("=" * 80)
    print(f"URL: {product_url}\n")

    try:
        print("[1] Sending request...")
        response = requests.get(product_url, headers=headers, timeout=30)
        print(f"    Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"    [ERROR] Failed to fetch page")
            return False

        print("[2] Parsing HTML with BeautifulSoup...")
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract product information
        print("\n[3] Extracting product data...\n")

        # Title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else None
        print(f"    Title: {title}")

        # Product ID from URL
        product_id = re.search(r'/(\d+)-', product_url)
        product_id = product_id.group(1) if product_id else None
        print(f"    Product ID: {product_id}")

        # Price - try multiple selectors
        price = None
        price_selectors = [
            {'class': re.compile(r'price', re.I)},
            {'class': 'product-price'},
            {'class': 'price-value'},
            {'itemprop': 'price'}
        ]

        for selector in price_selectors:
            price_elem = soup.find(attrs=selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extract price with regex
                price_match = re.search(r'\$(\d+\.?\d*)', price_text)
                if price_match:
                    price = f"${price_match.group(1)}"
                    break

        print(f"    Price: {price}")

        # Stock/Availability
        stock_status = None
        stock_selectors = [
            {'class': re.compile(r'stock', re.I)},
            {'class': re.compile(r'availability', re.I)},
            {'class': 'product-availability'},
            {'itemprop': 'availability'}
        ]

        for selector in stock_selectors:
            stock_elem = soup.find(attrs=selector)
            if stock_elem:
                stock_status = stock_elem.get_text(strip=True)
                break

        # Also check buttons
        if not stock_status:
            button = soup.find('button', string=re.compile(r'preorder|add to cart|out of stock', re.I))
            if button:
                stock_status = button.get_text(strip=True)

        print(f"    Stock Status: {stock_status}")

        # Image
        image_url = None
        img_selectors = [
            {'class': re.compile(r'product.*image', re.I)},
            {'itemprop': 'image'},
            {'class': 'main-image'}
        ]

        for selector in img_selectors:
            img_elem = soup.find('img', attrs=selector)
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url and not image_url.startswith('http'):
                    image_url = f"https://www.ebgames.com.au{image_url}"
                break

        print(f"    Image: {image_url[:80] if image_url else 'None'}...")

        # Check for any JSON-LD structured data
        print("\n[4] Checking for JSON-LD structured data...")
        json_ld_scripts = soup.find_all('script', type='application/ld+json')

        if json_ld_scripts:
            print(f"    Found {len(json_ld_scripts)} JSON-LD scripts")
            for i, script in enumerate(json_ld_scripts):
                try:
                    data = json.loads(script.string)
                    if data.get('@type') == 'Product':
                        print(f"    Script {i+1}: Product schema!")
                        print(f"      Name: {data.get('name')}")
                        print(f"      SKU: {data.get('sku')}")

                        offers = data.get('offers', {})
                        if isinstance(offers, dict):
                            print(f"      Price: {offers.get('price')}")
                            print(f"      Currency: {offers.get('priceCurrency')}")
                            print(f"      Availability: {offers.get('availability')}")

                        image = data.get('image')
                        if image:
                            print(f"      Image: {image if isinstance(image, str) else image[0] if isinstance(image, list) else 'N/A'}")
                except:
                    pass
        else:
            print("    No JSON-LD found")

        print("\n" + "=" * 80)
        print("Test Complete!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_scrape_product()
