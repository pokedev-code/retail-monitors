# Target Australia Monitor

Monitors Target Australia for product restocks and sends Discord notifications when products become available.

## Features

- **Pokemon Card Filtering**: Smart filtering to only notify about actual Pokemon TCG products
- **Pyppeteer-based**: Uses headless Chrome with stealth mode to avoid bot detection
- **Discord Webhooks**: Sends rich embed notifications with product images and prices
- **Continuous Monitoring**: Tracks product availability changes in real-time

## Installation

1. Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

Note: On first run, pyppeteer will download Chromium (~229MB). This is a one-time download.

## Configuration

Edit `config.py` to configure your monitor:

### Required Settings

```python
# Your Discord webhook URL
WEBHOOK = "https://discord.com/api/webhooks/..."

# Keywords to search for
KEYWORDS = ["pokemon cards"]
```

### Optional Settings

```python
# Delay between scrapes (in seconds)
DELAY = 30

# Filter keywords for Pokemon cards
CARD_INCLUDE_KEYWORDS = ['tcg', 'booster', 'pack', 'card', 'deck', 'tin', 'box', 'collection', 'elite trainer', 'bundle', 'blister']
CARD_EXCLUDE_KEYWORDS = ['plush', 'toy', 'figure', 'book', 'clothing', 'bag', 'puzzle', 'game']
```

## Pokemon Card Filtering

The monitor includes intelligent filtering to ensure only Pokemon card products trigger notifications:

**Products INCLUDED** (must contain at least one keyword):
- tcg
- booster
- pack
- card
- deck
- tin
- box
- collection
- elite trainer
- bundle
- blister

**Products EXCLUDED** (filtered out if they contain):
- plush
- toy
- figure
- book
- dvd
- clothing
- bag
- puzzle
- game
- console

### Examples

✅ **WILL NOTIFY:**
- "Pokemon TCG Booster Box"
- "Pokemon Elite Trainer Box"
- "Pokemon Card Collection Tin"

❌ **WILL NOT NOTIFY:**
- "Pokemon Plush Toy"
- "Pokemon T-Shirt"
- "Pokemon Video Game"

## Testing

Before running the full monitor, test the configuration:

```bash
python test_monitor.py
```

This will:
- Scrape the Target AU search page
- Show which products would trigger notifications
- Show which products are filtered out
- Verify the filtering logic is working correctly

## Running the Monitor

```bash
python monitor.py
```

The monitor will:
1. Perform an initial scrape (no notifications sent)
2. Continue monitoring every `DELAY` seconds
3. Send Discord notifications for new products
4. Log all activity to `target-monitor.log`

## How It Works

1. **Browser Automation**: Uses pyppeteer (Python Puppeteer) with stealth mode to avoid detection
2. **Page Scraping**: Navigates to Target AU search pages and extracts product data using JavaScript evaluation
3. **Product Tracking**: Maintains an in-stock list to detect when products appear or disappear
4. **Smart Filtering**: Applies keyword filtering to only notify about relevant products
5. **Discord Notifications**: Sends rich embeds with product details when new items are found

## Technical Details

- **Headless Browser**: Chromium (auto-downloaded by pyppeteer)
- **Stealth Mode**: pyppeteer-stealth to bypass bot detection
- **HTTP2 Disabled**: Avoids protocol errors with Target's servers
- **User Agent**: Chrome 131 on Windows 10
- **Wait Strategy**: Uses `networkidle2` to ensure JavaScript has rendered

## Troubleshooting

### Connection Errors
If you see `ERR_CONNECTION_RESET` or `ERR_HTTP2_PROTOCOL_ERROR`, the stealth mode should handle this. If issues persist, try:
- Increasing the delay between scrapes
- Running in non-headless mode temporarily (change `'headless': True` to `'headless': False` in monitor.py)

### No Products Found
- Verify the search URL is correct
- Run `test_monitor.py` to see raw scraping results
- Check if Target AU has changed their page structure

### Chromium Download Issues
If pyppeteer can't download Chromium, ensure you have internet access and sufficient disk space (~300MB).

## Logs

All activity is logged to `target-monitor.log` including:
- Scraping attempts
- Products found
- Filtering decisions
- Discord webhook responses
- Errors and exceptions
