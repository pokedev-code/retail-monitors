# Big W Stock Monitor

Monitors Big W product categories for new restocks and sends Discord notifications.

## ⚠️ Important Note - Bot Detection

**Big W has strong bot detection** that actively blocks automated requests (both Playwright and requests library). You may experience:
- `ERR_HTTP2_PROTOCOL_ERROR` with Playwright
- `ConnectionResetError` with requests library

This monitor is provided as a **starting point** for when:
1. Big W's bot detection eases
2. You find workarounds (residential proxies, session management, etc.)
3. You adapt the code for your specific use case

## How It Works

Big W uses Next.js and embeds product data directly in the HTML within a `<script id="__NEXT_DATA__">` tag. The monitor:

1. Fetches the category page HTML
2. Extracts the `__NEXT_DATA__` JSON object
3. Parses product information (code, name, price, stock, images)
4. Tracks products using the `INSTOCK` array
5. Sends Discord notifications for newly in-stock products

## Configuration

Edit `config.py`:

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

## Potential Workarounds for Bot Detection

1. **Use residential proxies** - Rotate through residential IP addresses
2. **Add delays and randomization** - Mimic human behavior
3. **Session management** - Maintain cookies and sessions
4. **Browser fingerprinting** - Use libraries like undetected-chromedriver
5. **Run less frequently** - Monitor every few minutes instead of 30 seconds
6. **Use VPN** - Change your IP address

## Files

- `monitor.py` - Main monitor script
- `config.py` - Configuration file
- `test_monitor.py` - Test script
- `discover_api.py` - API exploration script
- `README.md` - This file

## Notes

- Big W doesn't provide per-state stock information like Kmart
- Stock is binary: in-stock or out-of-stock
- The monitor uses simple HTTP requests (no Playwright) to reduce detection footprint
- Product URLs are generated as: `/product/{name-slug}/p/{code}`

## Troubleshooting

**ConnectionResetError / ERR_HTTP2_PROTOCOL_ERROR**
- This is Big W actively blocking your requests
- Try using a VPN or residential proxy
- Increase the DELAY between requests
- Consider running the monitor from a different network

**No products found**
- Check that CATEGORY_URL is correct
- Verify the Next.js data structure hasn't changed
- Try accessing the URL in a regular browser first

**Webhook not sending**
- Verify your WEBHOOK URL is correct
- Check Discord server permissions
- Review the log file: `bigw-monitor.log`
