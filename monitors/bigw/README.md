# Big W Stock Monitor - Playwright Enhanced

Monitors Big W product categories for new restocks and sends Discord notifications.

## ⚠️ Important Note - Bot Detection

**Big W has VERY strong bot detection** that actively blocks automated requests. This monitor now uses:
- ✅ **Playwright** with anti-detection features
- ✅ **HTTP/2 disabled** to avoid protocol errors
- ✅ **Browser fingerprint masking** (webdriver, plugins, languages)
- ✅ **Proxy support** with automatic rotation

**However**, Big W may still block you without residential proxies. This monitor provides the foundation - you'll likely need to add proxies to use it reliably

## How It Works

Big W uses Next.js and embeds product data directly in the HTML within a `<script id="__NEXT_DATA__">` tag. The monitor:

1. Fetches the category page HTML
2. Extracts the `__NEXT_DATA__` JSON object
3. Parses product information (code, name, price, stock, images)
4. Tracks products using the `INSTOCK` array
5. Sends Discord notifications for newly in-stock products

## Configuration

Edit `config.py`:

### Basic Settings

```python
# Your Discord webhook URL
WEBHOOK = "YOUR_DISCORD_WEBHOOK_URL_HERE"

# Category URL to monitor
CATEGORY_URL = "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201"

# Delay between requests (seconds)
DELAY = 30

# Keywords to filter products (leave empty [] for all)
KEYWORDS = []

# Product filters
INCLUDE_KEYWORDS = ['tcg', 'booster', 'pack', 'card', ...]
EXCLUDE_KEYWORDS = ['plush', 'toy', 'figure', ...]
```

### Proxy Configuration (Recommended)

To bypass Big W's bot detection, you'll need residential proxies. Edit `config.py`:

```python
# Enable proxy support
PROXY_ENABLED = True

# Option 1: Use a single proxy
SINGLE_PROXY = "http://username:password@proxy.example.com:8080"

# Option 2: Use multiple proxies (will rotate)
PROXY_LIST = [
    "http://user:pass@proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:8080",
    "http://user:pass@proxy3.example.com:8080",
]

# Proxy settings
ROTATE_PROXY_ON_ERROR = True  # Auto-rotate if proxy fails
PROXY_RETRY_LIMIT = 3  # Try 3 different proxies before giving up
```

### Browser Settings

```python
# Show browser window (useful for debugging/CAPTCHA solving)
HEADLESS = False  # Set to True to hide browser

# Logging
LOG_FILE = "bigw-monitor.log"
```

## Running the Monitor

```bash
cd monitors/bigw
python monitor.py
```

## Testing

```bash
python test_monitor.py
```

## Data Structure

Products in `__NEXT_DATA__` are structured as:

```json
{
  "props": {
    "pageProps": {
      "results": {
        "organic": {
          "results": [
            {
              "code": "6047808",
              "information": {
                "name": "Pokemon TCG: Triple Whammy Tin",
                "brand": "Pokemon"
              },
              "derived": {
                "stock": true,
                "soldOut": false,
                "priceRange": {
                  "min": {
                    "amount": 3000  // cents
                  }
                },
                "media": {
                  "images": [...]
                }
              }
            }
          ]
        }
      }
    }
  }
}
```

## Proxy Setup Guide

### Recommended Proxy Providers (Residential)

Big W's bot detection requires **residential proxies** (not datacenter). Here are some options:

1. **Bright Data** (formerly Luminati)
   - https://brightdata.com
   - Cost: ~$8.40/GB for residential
   - Format: `http://username-session-[random]:password@brd.superproxy.io:22225`

2. **Smartproxy**
   - https://smartproxy.com
   - Cost: ~$8/GB for residential
   - Format: `http://user:pass@gate.smartproxy.com:7000`

3. **Oxylabs**
   - https://oxylabs.io
   - Cost: ~$15/GB for residential
   - Format: `http://customer-user:pass@pr.oxylabs.io:7777`

4. **IPRoyal**
   - https://iproyal.com
   - Cost: ~$1.75/GB for residential (cheaper!)
   - Format: `http://user:pass@geo.iproyal.com:12321`

### Proxy Format Examples

The monitor supports multiple proxy formats:

```python
# HTTP proxy with authentication
"http://username:password@proxy.example.com:8080"

# SOCKS5 proxy with authentication
"socks5://username:password@proxy.example.com:1080"

# HTTP proxy without authentication
"http://proxy.example.com:8080"
```

### Testing Your Proxies

Before running the monitor, test your proxies:

```python
# config.py
PROXY_ENABLED = True
SINGLE_PROXY = "http://your-user:your-pass@proxy.example.com:8080"
HEADLESS = False  # Watch it work
DELAY = 60  # Slow it down for testing
```

Then run `python monitor.py` and watch the browser window to see if it loads Big W successfully.

### Free Proxies (Not Recommended)

Free proxies typically don't work with Big W because:
- They're datacenter IPs (easily detected)
- They're slow and unreliable
- They're often already blacklisted

If you want to try anyway, use services like:
- https://www.proxy-list.download/
- https://free-proxy-list.net/

But expect high failure rates.

## Files

- `monitor.py` - Main monitor script
- `config.py` - Configuration file
- `test_monitor.py` - Test script
- `discover_api.py` - API exploration script
- `README.md` - This file

## Notes

- Big W doesn't provide per-state stock information like Kmart
- Stock is binary: in-stock or out-of-stock
- The monitor now uses **Playwright** (not simple requests) for better anti-detection
- Product URLs are generated as: `/product/{name-slug}/p/{code}`
- HTTP/2 is **disabled** to avoid protocol errors with Big W's servers

## Troubleshooting

### Page Load Timeout / ERR_HTTP2_PROTOCOL_ERROR
**Cause:** Big W is blocking your requests with bot detection.

**Solutions:**
1. ✅ **Add residential proxies** (see Proxy Setup Guide above)
2. Set `HEADLESS = False` to watch what's happening
3. Increase `DELAY` to 60+ seconds between requests
4. Check if you need to solve a CAPTCHA manually (when headless=False)

### No products found / Empty scrape
**Possible causes:**
- Bot detection is blocking the page load
- The CATEGORY_URL is incorrect
- Next.js data structure changed (rare)

**Solutions:**
1. Open the URL in a regular browser and check if products load
2. Try with `HEADLESS = False` to see the actual page
3. Check `bigw-monitor.log` for detailed error messages
4. Add proxies if you haven't already

### Proxy errors
**`[PROXY] Failed after 3 attempts`**
- Your proxies aren't working or are blocked
- Try different proxy provider
- Make sure proxies are **residential** (not datacenter)
- Check proxy credentials are correct

### Webhook not sending
**Possible causes:**
- Webhook URL is incorrect
- Discord server permissions
- Monitor not detecting new products

**Solutions:**
1. Verify your webhook URL in config.py
2. Check Discord channel settings → Integrations → Webhooks
3. Review `bigw-monitor.log` for webhook errors
4. Test with a product you know is in stock

## Cost Estimates (with Proxies)

Assuming you use residential proxies:

- **Light monitoring** (every 60 seconds): ~500MB-1GB/day = **$1.75-$8/day**
- **Normal monitoring** (every 30 seconds): ~1-2GB/day = **$3.50-$17/day**
- **Aggressive monitoring** (every 10 seconds): ~3-6GB/day = **$10-$50/day**

Costs vary by proxy provider. IPRoyal is cheapest (~$1.75/GB), while Oxylabs is most expensive (~$15/GB).

## Alternative: Use Bright Data MCP for Manual Checks

If continuous monitoring is too expensive, you can:
1. Keep this monitor code as-is (without proxies)
2. When it gets blocked, ask Claude (with Bright Data MCP) to scrape the page manually
3. Cost: ~$0.0015 per manual check (practically free)

This is best for occasional checking rather than 24/7 monitoring.
