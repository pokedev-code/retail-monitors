# Australian Retailer Monitoring - Implementation Guide

## Project Extension Summary

This project has been extended from sneaker monitoring to support monitoring ANY products (Pokemon cards, electronics, toys, etc.) across Australian retailers.

## Supported Retailers

### 1. Shopify-Based Stores (Use existing Shopify monitor)
Many smaller Australian retailers use Shopify. The existing `monitors/shopify/` monitor works for ANY Shopify store.

**How to use:**
1. Find a Shopify store's products.json endpoint
2. Update `monitors/shopify/config.py` with the URL
3. Set keywords for Pokemon cards, toys, or whatever you want to monitor

### 2. Kmart Australia ✅ IMPLEMENTED
- **Monitor Location:** `monitors/kmart/`
- **Platform:** Commercetools (headless commerce)
- **Status:** Base implementation complete
- **Note:** Kmart uses JavaScript rendering, may require browser automation (Selenium/Puppeteer) for full functionality

**Configuration:**
```python
URL = "https://www.kmart.com.au/category/toys/pokemon-trading-cards/"
KEYWORDS = ["Scarlet", "Violet", "Booster"]
```

### 3. Target Australia
- **Platform:** Commercetools (same as Kmart)
- **Status:** Can reuse Kmart monitor with URL changes
- **Pokemon Cards URL:** `https://www.target.com.au/c/toys/trading-card-games/pokemon-cards/`

### 4. Big W
- **Platform:** Custom (Woolworths Group)
- **Status:** Requires custom implementation
- **Pokemon Cards URL:** `https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/`

### 5. Amazon Australia
- **Platform:** Amazon proprietary
- **Status:** Requires custom implementation or Amazon API
- **Pokemon Cards URL:** `https://www.amazon.com.au/pokemon-cards/s?k=pokemon+cards`

## Implementation Challenges

### JavaScript-Rendered Sites
Modern retailers (Kmart, Target, Big W) use Single Page Applications (SPAs) that load product data dynamically via JavaScript. This means:

**Challenge:** Simple HTTP requests don't get the product data
**Solutions:**
1. **Browser Automation:** Use Selenium or Puppeteer to load the page and wait for JavaScript
2. **API Discovery:** Find the internal API endpoints the site uses to fetch products
3. **Reverse Engineering:** Analyze network requests in browser dev tools

### Recommended Approach for Dynamic Sites

Use Selenium or Pyppeteer to load pages:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

driver.get(url)
# Wait for products to load
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
)

# Now scrape the rendered HTML
soup = BeautifulSoup(driver.page_source, 'lxml')
```

## Quick Start for Pokemon Card Monitoring

### Option 1: Find Shopify Stores
Many Pokemon card retailers use Shopify:
1. Search for "pokemon cards australia shopify"
2. Test if `[store-url]/products.json` works
3. Use the existing Shopify monitor!

### Option 2: Use Kmart Monitor (Needs Enhancement)
The Kmart monitor is implemented but needs browser automation added for full functionality.

### Option 3: Create Custom API Monitors
Research each retailer's internal APIs:
1. Open browser dev tools (F12)
2. Go to Network tab
3. Load the Pokemon cards category page
4. Look for XHR/Fetch requests that return product JSON
5. Create monitor using those API endpoints

## Next Steps

### To Complete This Project:

1. **Add Browser Automation to Kmart Monitor**
   - Install Selenium: `pip install selenium webdriver-manager`
   - Update scraping logic to use headless Chrome
   - Test with Pokemon cards category

2. **Create Big W Monitor**
   - Analyze Big W's product loading mechanism
   - Implement similar to Kmart monitor

3. **Create Amazon AU Monitor**
   - Consider using Amazon Product Advertising API
   - Or scrape with browser automation (check ToS)

4. **Add More Australian Retailers**
   - EB Games (games/Pokemon)
   - JB Hi-Fi
   - Catch.com.au
   - Many more!

## Configuration Template

For any new monitor, follow this config structure:

```python
# Webhook
WEBHOOK = "your-discord-webhook-url"

# Retailer URL (category or search page)
URL = "https://retailer.com.au/category/pokemon-cards/"

# Product Filters
KEYWORDS = ["Pokemon", "Scarlet", "Violet", "Booster"]  # Or [] for all

# Monitoring Settings
DELAY = 30  # seconds between checks

# Proxy Settings (optional)
ENABLE_FREE_PROXY = False
PROXY = []

# Discord Appearance
USERNAME = "Retailer Monitor"
AVATAR_URL = "logo-url"
COLOUR = 16711680  # Hex color
```

## Testing Your Monitors

1. **Test Discord webhook first:**
   ```bash
   cd monitors/shopify
   python test_discord.py
   ```

2. **Run monitor with short delay:**
   - Set `DELAY = 10` for testing
   - Watch for products being detected
   - Check Discord for notifications

3. **Increase delay for production:**
   - Set `DELAY = 30-60` to be respectful
   - Run continuously on a server

## Tips

- **Start with Shopify stores** - they're easiest to monitor
- **Check robots.txt** - respect retailer scraping policies
- **Use delays** - don't hammer servers with requests
- **Rotate user agents** - built into monitors
- **Consider proxies** - for high-frequency monitoring
- **Test thoroughly** - before running 24/7

## Resources

- [Shopify products.json endpoint docs](https://shopify.dev/docs/api/liquid/objects/product)
- [Beautiful Soup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Selenium Python docs](https://selenium-python.readthedocs.io/)
- [Discord webhooks](https://discord.com/developers/docs/resources/webhook)
