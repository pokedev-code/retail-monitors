# Amazon Australia Stock Monitor

Monitors Amazon.com.au search pages for new products and restocks using Playwright browser automation.

## ⚠️ Important Note - Bot Detection

**Amazon has VERY strong bot detection** that actively blocks automated requests. This monitor uses:
- ✅ **Playwright** with anti-detection features
- ✅ **Browser fingerprint masking** (webdriver, plugins, languages)
- ✅ **Realistic browser behavior** with delays and scrolling

**However**, Amazon may still detect and block you, especially with:
- High-frequency scraping (< 60 seconds)
- Multiple pages being scraped
- Running for extended periods

**Recommendations:**
- Start with `HEADLESS = False` to see what Amazon sees
- Use delays of 60-120 seconds minimum
- Limit `MAX_PAGES` to 1-2 pages
- Consider using proxies for long-term monitoring
- Don't run multiple instances simultaneously

## How It Works

Amazon doesn't provide accessible APIs and has strong bot protection. The monitor:

1. Launches a Chrome browser using Playwright with anti-detection features
2. Navigates to the Amazon search page
3. Extracts product information from HTML using JavaScript (data-asin attributes)
4. Tracks products by ASIN and sends Discord notifications for new/restocked items
5. Supports pagination to scrape multiple result pages

## Configuration

Edit `config.py`:

### Basic Settings

```python
# Your Discord webhook URL
WEBHOOK = "YOUR_DISCORD_WEBHOOK_URL_HERE"

# Amazon search URL to monitor
SEARCH_URL = "https://www.amazon.com.au/s?k=pokemon+cards"

# Delay between requests (seconds) - recommended 60-120
DELAY = 60

# Keywords to filter products (leave empty [] for all)
KEYWORDS = []
```

### Product Filters

```python
# Only include products with these keywords
INCLUDE_KEYWORDS = ['tcg', 'booster', 'pack', 'card', 'deck', 'tin', 'box', ...]

# Exclude products with these keywords
EXCLUDE_KEYWORDS = ['plush', 'toy', 'figure', 'book', 'dvd', ...]
```

### Advanced Filters

```python
# Price range (set to None to disable)
MIN_PRICE = 10   # Minimum price in AUD
MAX_PRICE = 500  # Maximum price in AUD

# Stock filters
ONLY_IN_STOCK = True   # Only monitor in-stock products
PRIME_ONLY = False     # Only monitor Prime-eligible products
```

### Pagination

```python
# Maximum pages to scrape (Amazon shows ~48 products/page)
MAX_PAGES = 1  # Recommended: 1-3 to avoid detection
```

### Browser Settings

```python
# Show browser window (useful for debugging)
HEADLESS = False  # Set to True to hide browser

# Logging
LOG_FILE = "amazon-monitor.log"
```

## Building Search URLs

1. Go to https://www.amazon.com.au/
2. Search for your product (e.g., "pokemon cards")
3. Apply filters:
   - **Department**: Select category (e.g., Toys & Games)
   - **Prime**: Check Prime box if you want Prime-only
   - **Price**: Set price range
   - **Customer Review**: Filter by rating
   - **Brand**: Select specific brands
4. Copy the URL from your browser's address bar
5. Paste it into `SEARCH_URL` in config.py

**Example URLs:**

```
# Basic search
https://www.amazon.com.au/s?k=pokemon+cards

# With category filter
https://www.amazon.com.au/s?k=pokemon+booster+box&rh=n:4998428051

# With Prime and price filter
https://www.amazon.com.au/s?k=pokemon+cards&rh=p_85:5408138051,p_36:1000-5000

# With department and brand
https://www.amazon.com.au/s?k=pokemon+cards&i=toys&rh=p_89:Pokemon
```

**URL Parameter Guide:**
- `k=` - Search keywords
- `rh=` - Refinements (filters)
- `n:` - Category/node ID
- `p_85:` - Prime eligible
- `p_36:` - Price range (in cents: 1000-5000 = $10-$50)
- `p_89:` - Brand
- `i=` - Department

## Running the Monitor

```bash
cd monitors/amazon
python monitor.py
```

## Testing

```bash
python test_monitor.py
```

This will:
1. Launch browser (visible window)
2. Scrape the first page
3. Print products found
4. Show what would be tracked (no Discord notifications)

## Features

### Product Data Extracted
- **ASIN** - Amazon Standard Identification Number (unique product ID)
- **Title** - Product name
- **Price** - Current price in AUD
- **Rating** - Star rating (e.g., 4.5 out of 5)
- **Reviews** - Number of customer reviews
- **Prime** - Whether product has Prime shipping
- **Stock Status** - In Stock / Out of Stock
- **Image** - Product image URL

### Discord Notifications Include
- Product title with link to Amazon page
- Price
- Rating and review count
- Prime eligibility badge
- Stock status
- ASIN
- eBay comparison links (optional)
- Product thumbnail image

## Performance Comparison

| Monitor | Method | Speed | Reliability | Scraping Difficulty |
|---------|--------|-------|-------------|---------------------|
| Kmart | GraphQL API | ⚡ Fast (1-2s) | ✅ Excellent | ⭐ Easy |
| Target | API Intercept | ⚡ Fast (1-2s) | ✅ Excellent | ⭐ Easy |
| Big W | Next.js + Playwright | ⚡ Fast (1-2s) | ✅ Good | ⭐⭐ Medium |
| EB Games | Playwright HTML | 🐌 Slow (5-10s) | ⚠️ Good | ⭐⭐ Medium |
| **Amazon** | **Playwright HTML** | 🐌 **Slow (5-10s)** | ⚠️ **Fair** | ⭐⭐⭐ **Hard** |

## Limitations

- **Strong bot detection** - May get blocked without proxies
- **Slower than API monitors** - Each page takes 5-10 seconds
- **No seller filtering** - Can't filter by specific sellers (except Prime)
- **No detailed stock data** - Binary in-stock/out-of-stock only
- **Rate limiting** - Amazon may throttle/block if scraping too frequently
- **CAPTCHA risk** - May encounter CAPTCHAs during scraping

## Troubleshooting

### CAPTCHA appears
**Cause:** Amazon detected automated browser activity.

**Solutions:**
1. Increase `DELAY` to 120+ seconds
2. Reduce `MAX_PAGES` to 1
3. Set `HEADLESS = False` and solve CAPTCHA manually
4. Add residential proxies (see Big W README for proxy setup)
5. Take breaks - don't run 24/7

### Page load timeout / No products found
**Possible causes:**
- Bot detection blocking the page
- Incorrect `SEARCH_URL`
- Network issues

**Solutions:**
1. Try with `HEADLESS = False` to see what's happening
2. Check if the search URL works in a regular browser
3. Verify you're not being blocked (check for CAPTCHA)
4. Check `amazon-monitor.log` for errors

### Monitor is slow
**Expected behavior** - Playwright launches a full browser.

**Ways to improve:**
- Set `HEADLESS = True` (slightly faster)
- Reduce `MAX_PAGES` to 1
- Increase `DELAY` to reduce scraping frequency
- Accept that Amazon scraping is inherently slow

### Products not triggering notifications
**Check:**
1. Are products matching your filters? (INCLUDE_KEYWORDS, EXCLUDE_KEYWORDS)
2. Is price within MIN_PRICE/MAX_PRICE range?
3. If ONLY_IN_STOCK=True, are products actually in stock?
4. If PRIME_ONLY=True, are products Prime eligible?
5. Check `amazon-monitor.log` for filter messages

### Webhook not sending
**Solutions:**
1. Verify WEBHOOK URL in config.py
2. Check Discord channel settings → Integrations → Webhooks
3. Review `amazon-monitor.log` for webhook errors
4. Test webhook with a simple curl/Postman request

## Amazon-Specific Tips

### Finding Category/Department IDs
1. Navigate to a category on Amazon (e.g., Toys & Games → Trading Cards)
2. Look at URL - the `n:` number is the category ID
3. Add to search URL: `&rh=n:4998428051`

### Understanding Prime Filter
- `rh=p_85:5408138051` = Prime eligible in Australia
- Enable in config: `PRIME_ONLY = True`

### Price Range Format
- Prices in Amazon URLs are in cents
- Example: `p_36:1000-5000` = $10 to $50
- Or use MIN_PRICE/MAX_PRICE in config for easier filtering

### Dealing with Sponsored Results
The monitor automatically filters out sponsored products (ads) by only tracking products with valid ASINs from organic search results.

## Files

- `monitor.py` - Main monitor using Playwright
- `config.py` - Configuration file
- `test_monitor.py` - Test script
- `README.md` - This file
- `amazon-monitor.log` - Log file (auto-created)

## Notes

- Amazon's search results typically show ~48 products per page
- ASIN is the unique identifier (e.g., B01234ABCD)
- Sponsored/ad products are automatically filtered out
- Stock status is binary (In Stock / Out of Stock) - no quantity data
- Prices may fluctuate - monitor tracks when products appear/disappear from search
- Prime eligibility is detected from the Prime badge icon
- Review count and ratings help identify popular/reputable products

## Legal & Ethical Considerations

**Important:**
- This monitor is for personal use only
- Respect Amazon's Terms of Service
- Don't scrape too aggressively (use 60-120s delays minimum)
- Don't use for commercial reselling/scalping operations
- Amazon may block your IP if they detect scraping
- Consider using this for price alerts on products you actually want to buy

## Alternative: Amazon Product Advertising API

For commercial/high-volume use, consider Amazon's official **Product Advertising API**:
- https://affiliate-program.amazon.com.au/help/operating/api
- Legal and supported by Amazon
- No bot detection issues
- Requires approval and affiliate account
- Rate limits and usage fees may apply

This monitor is a proof-of-concept for personal use when the official API is not available or practical.
