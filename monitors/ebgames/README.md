# EB Games Stock Monitor

Monitors EB Games search/category pages for new products and restocks using Playwright browser automation.

## ⚠️ Important Note - Performance

**This monitor uses Playwright (headless browser)** which is slower than the API-based monitors (Kmart, Big W, Target) because:
- EB Games has strong bot protection that blocks simple HTTP requests
- Requires full browser automation to bypass detection
- Each scrape takes 5-10 seconds vs 1-2 seconds for API monitors

**Recommended delay: 60-120 seconds** between requests to avoid detection and reduce resource usage.

## How It Works

EB Games doesn't provide accessible APIs and has bot protection. The monitor:

1. Launches a headless Chrome browser using Playwright
2. Navigates to the search/category page
3. Extracts product information from HTML using JavaScript
4. Tracks products and sends Discord notifications for new/restocked items

## Configuration

Edit `config.py`:

```python
# Your Discord webhook URL
WEBHOOK = "YOUR_DISCORD_WEBHOOK_URL_HERE"

# Search URL to monitor (Pokemon cards example)
SEARCH_URL = "https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards&attributes=franchise%3Apokemon"

# Delay between requests (seconds) - recommended 60-120
DELAY = 60

# Keywords to filter products (leave empty [] for all)
KEYWORDS = []

# Product filters
INCLUDE_KEYWORDS = ['tcg', 'booster', 'pack', 'card', ...]
EXCLUDE_KEYWORDS = ['plush', 'toy', 'figure', ...]

# Run browser in headless mode
HEADLESS = True
```

## Finding Search URLs

1. Go to https://www.ebgames.com.au/
2. Navigate to the category you want to monitor (e.g., Toys & Hobbies → Trading Cards)
3. Apply filters (e.g., Franchise: Pokemon)
4. Copy the URL from your browser's address bar
5. Paste it into `SEARCH_URL` in config.py

**Examples:**
- Pokemon Cards: `https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards&attributes=franchise%3Apokemon`
- All Trading Cards: `https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards`

## Running the Monitor

```bash
cd monitors/ebgames
python monitor.py
```

## Testing

```bash
python test_monitor.py
```

## Performance Comparison

| Monitor | Method | Speed | Reliability |
|---------|--------|-------|-------------|
| Kmart | GraphQL API | ⚡ Fast (1-2s) | ✅ Excellent |
| Big W | REST API + HTML | ⚡ Fast (1-2s) | ✅ Excellent |
| Target | GraphQL API | ⚡ Fast (1-2s) | ✅ Excellent |
| **EB Games** | **Playwright** | 🐌 **Slow (5-10s)** | ⚠️ **Good** |

## Limitations

- **Slower than API monitors** - Each scrape takes 5-10 seconds
- **Higher resource usage** - Runs a full Chrome browser
- **Bot detection risk** - May get blocked if running too frequently
- **No per-store stock** - Only shows online availability

## Troubleshooting

**Monitor is slow**
- This is expected - Playwright launches a full browser
- Increase `DELAY` to reduce frequency
- Consider using API-based monitors (Kmart, Big W) instead

**Browser crashes or timeout errors**
- Increase timeout in monitor.py
- Check your internet connection
- Try running with `HEADLESS = False` to see what's happening

**No products found**
- Verify `SEARCH_URL` is correct
- Check that the page loads in a regular browser
- Try running test_monitor.py with `headless=False`

**Webhook not sending**
- Verify your WEBHOOK URL is correct
- Check Discord server permissions
- Review the log file: `ebgames-monitor.log`

## Files

- `monitor.py` - Main monitor script (Playwright-based)
- `config.py` - Configuration file
- `test_monitor.py` - Test script
- `README.md` - This file

## Notes

- EB Games uses strong bot protection (similar to Cloudflare)
- Simple HTTP requests are blocked with 403 Forbidden
- Playwright bypasses this by using a real browser
- Stock status shows "Available", "PreOrder", or "Out of Stock"
- Product titles may include extra text (price, preorder dates) - this is extracted from the HTML
