# Kmart Australia Monitor

Monitor Kmart Australia for product restocks and new releases across ANY category including Pokemon cards, trading cards, toys, electronics, and more!

## Features

- Monitors any Kmart AU category page
- Supports keyword filtering for specific products
- Discord webhook notifications with product images
- Proxy support (free and custom)
- Automatic retry with user agent rotation

## Setup

1. Edit `config.py` with your settings:
   - `WEBHOOK`: Your Discord webhook URL
   - `URL`: Kmart category page URL
   - `DELAY`: Seconds between checks (recommended: 30-60)
   - `KEYWORDS`: Filter for specific products (optional)

2. Run the monitor:
   ```bash
   python monitor.py
   ```

## Example Category URLs

### Pokemon & Trading Cards
- Pokemon Cards: `https://www.kmart.com.au/category/toys/pokemon-trading-cards/`
- Card Games: `https://www.kmart.com.au/category/toys/toys-by-category/board-games-&-puzzles/activity-&-card-games/card-games/252088/`

### Other Categories
- All Toys: `https://www.kmart.com.au/category/toys/`
- Electronics: `https://www.kmart.com.au/category/electronics/`
- Gaming: `https://www.kmart.com.au/category/electronics/gaming/`

## Keyword Examples

To monitor specific products, add keywords to the `KEYWORDS` array in `config.py`:

```python
# Monitor only Scarlet & Violet cards
KEYWORDS = ["Scarlet", "Violet"]

# Monitor booster packs
KEYWORDS = ["Booster"]

# Monitor multiple types
KEYWORDS = ["Elite Trainer", "Booster Bundle", "Collection Box"]
```

## Notes

- The monitor tracks products by title and URL
- First run will not send notifications (builds initial inventory)
- Subsequent runs will notify about new products appearing
- Respects Kmart's servers with configurable delays
