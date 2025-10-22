# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a collection of web monitors that track and alert about restocks or releases on sneaker retail websites through Discord webhooks. Each monitor continuously polls specific retailer APIs/websites and sends notifications when products become available.

**Note**: This project is no longer actively maintained by the original author but should still function.

## Running Monitors

Each monitor is self-contained in its own directory under `monitors/`. To run a specific monitor:

1. Navigate to the monitor directory (e.g., `monitors/shopify/`)
2. Edit the `config.py` file with your settings (webhook URL, keywords, proxies, etc.)
3. Run the monitor:
   ```
   python monitor.py
   ```

The monitor script needs to run continuously to keep tracking websites. For production use, these should be hosted on a server.

## Installation

Install dependencies with:
```
pip install -r requirements.txt
```

Dependencies include: requests, beautifulsoup4, pyppeteer, pyppeteer-stealth, random-user-agent, free-proxy, lxml, and others.

## Architecture

### Monitor Structure

Each monitor follows a similar pattern:
- `config.py` - Configuration file where users set webhook URLs, delays, proxies, keywords, etc.
- `monitor.py` - Main monitoring script with an infinite loop that scrapes and compares product availability
- `locations.py` (for Nike/SNKRS/Footlocker) - Region-specific API implementations

### Core Monitor Pattern

All monitors follow this general flow:
1. **Initial scrape** - Populate `INSTOCK` array with currently available products (without sending notifications)
2. **Continuous monitoring loop** - Repeatedly scrape the site every `DELAY` seconds
3. **Comparison logic** - Compare current scrape against `INSTOCK` array
4. **State management**:
   - If product becomes available and not in `INSTOCK`: add to array and send Discord notification
   - If product becomes unavailable but in `INSTOCK`: remove from array
5. **Error handling** - Rotate user agents and proxies on request failures

### Available Monitors

- `shopify` - Works with any Shopify-based store (e.g., Palace, Hanon, Travis Scott stores)
- `snkrs` - Nike SNKRS app (supports 42+ countries via different APIs)
- `nike` - Nike website monitor
- `footlocker` - Footlocker UK, US, and AU
- `supreme` - Supreme store
- `ssense` - Ssense
- `zalando` - Zalando UK
- `offspring` - Off-Spring UK
- `snipes` - Snipes
- `sivasdescalzo` - Sivasdescalzo
- `kmart` - Kmart Australia (enhanced with Playwright and GraphQL API, state-specific stock tracking)
- `target` - Target Australia (enhanced with Playwright and stock API interception, state-specific notifications)
- `bigw` - Big W Australia (**experimental** - strong bot detection, Next.js data extraction)

### Region Handling (Nike/SNKRS)

Nike and SNKRS monitors support multiple countries through `locations.py`:
- Most countries use a `standard_api()` function that queries Nike's product feed API
- Special implementations exist for Brazil (`brazil()`) and Chile (`chile()`) which use different endpoints/scraping methods
- The `___standard_api___` list contains all country codes that use the standard approach
- Region is configured via 2-letter country code (e.g., 'GB', 'US') and language code (e.g., 'en-GB', 'en')

### Discord Webhook Integration

All monitors send notifications via Discord webhooks. The `discord_webhook()` function:
- Constructs embed objects with product details (title, image, price, style code, sizes)
- Includes "Add to Cart" links for Shopify stores
- Uses configured username, avatar URL, and embed color
- Includes footer attribution to the original developer

#### State-Specific Webhooks (Kmart & Target Australia)

Kmart and Target monitors support state-specific Discord webhooks for Australian states:
- **Dual webhook system**: Sends notifications to BOTH a main unfiltered webhook AND state-specific webhooks
- **Main webhook** (`WEBHOOK` in config.py): Receives all notifications with combined/aggregated data across all states
- **State webhooks** (`STATE_WEBHOOKS` dict in config.py): Each Australian state (NSW, VIC, QLD, SA, WA, TAS, NT, ACT) can have its own webhook
- **Kmart**: Main webhook shows combined stock totals (sum of all states), state webhooks show per-state stock
- **Target**: Main webhook shows all stores across all states, state webhooks show only stores in that specific state with store names (e.g., "Subiaco") instead of numbers
- **Store mapping** (Target only): Uses `store_state_mapper.py` to fetch and cache all Target stores with their states and names in `store_state_mapping.json`
- Configure by creating separate Discord channels (e.g., #kmart-nsw, #target-vic) and adding webhook URLs to `STATE_WEBHOOKS` dict

### Proxy Support

Monitors support three proxy modes:
1. **Free proxies** - When `ENABLE_FREE_PROXY = True`, uses `free-proxy` library to get random proxies
2. **Custom proxies** - Configured via `PROXY` array with rotation on request failures
3. **No proxy** - Direct connections

User agents are randomized on each request using `random-user-agent` library with mobile Chrome user agents.

### Keyword Filtering

All monitors support optional keyword filtering via `KEYWORDS` config array:
- If empty: monitor all products
- If populated: only notify for products matching keywords (case-insensitive substring match)

### Shopify Specifics

Shopify monitors scrape `products.json` endpoints with pagination:
- Fetches up to 250 products per page
- Continues until empty response
- Generates ATC (Add To Cart) links from variant IDs: `/cart/{variant_id}:1`
- Must ensure config URL points to a valid `/products.json` endpoint

### Logging

All monitors use Python's logging module to write to monitor-specific log files (e.g., `shopify-monitor.log`, `snkrs-monitor.log`) with timestamps and debug-level logging.

## Testing

No formal test suite exists. To test a monitor:
1. Configure it with a valid Discord webhook
2. Set a short delay (5-10 seconds)
3. Run locally and verify notifications appear in Discord
4. Check the log file for errors

## Common Patterns

When modifying monitors:
- The `INSTOCK` global array tracks product state - handle carefully to avoid memory leaks
- Always use the `start` flag pattern to prevent notification spam on initial scrape
- Wrap API requests in try-except blocks with header/proxy rotation on failure
- Use `urllib3.disable_warnings()` when disabling SSL verification
- Product identity typically combines title + variant/size for granular tracking

## Australian Retail Monitors (Kmart & Target)

### Kmart Monitor (`monitors/kmart/`)

**Architecture:**
- Uses Playwright (async Chromium browser automation) for anti-bot evasion
- Queries GraphQL API (`https://api.kmart.com.au/gateway/graphql`) for precise per-state stock data
- Tracks stock for all 8 Australian states/territories simultaneously
- Product image scraping from page DOM with multiple selector fallbacks

**Key Features:**
- **Per-state stock tracking**: Queries stock for NSW, VIC, QLD, SA, WA, TAS, NT, ACT in a single GraphQL request
- **Dual notifications**: Sends to main webhook (combined totals) + individual state webhooks
- **Stock types**: Tracks both online and in-store availability separately
- **State-based comparisons**: Maintains `INSTOCK` dict with per-state stock levels, only notifies on changes per state

**Files:**
- `monitor_enhanced.py` - Main monitor with Playwright and GraphQL integration
- `config.py` - Configuration including `STATE_WEBHOOKS` dict
- `test_state_webhooks.py` - Test script for state-specific notifications

**GraphQL Query:**
```graphql
query ($articleNumber: String!, $state: String!) {
  product(articleNumber: $articleNumber) {
    stockLevel(state: $state) {
      online { status }
      instore { status }
    }
  }
}
```

### Target Monitor (`monitors/target/`)

**Architecture:**
- Uses Playwright for browser automation with API response interception
- Intercepts Target's stock API (`lz3inventory/stockStatus`) to get exact store-level inventory
- Maps store numbers to Australian states using postcode ranges
- Displays human-readable store names instead of numbers in notifications

**Key Features:**
- **Store-to-state mapping**: Fetches all Target stores via API and maps to states using postcode ranges
- **Store name display**: Shows "Yass, Ararat, Subiaco" instead of store numbers
- **API interception**: Captures stock API responses during page load to avoid separate API calls
- **Dual notifications**: Main webhook shows all stores, state webhooks show filtered stores
- **Click & Collect tracking**: Monitors Home Delivery, Express Delivery, and Click & Collect availability

**Files:**
- `monitor_enhanced.py` - Main monitor with Playwright and API interception
- `store_state_mapper.py` - Utility to fetch and map all Target stores to states
- `store_state_mapping.json` - Cached mapping of 179 stores (store number → state + name)
- `config.py` - Configuration including `STATE_WEBHOOKS` dict
- `test_state_notifications.py` - Test script for state-specific notifications

**Store Mapping:**
- Fetches stores from `https://www.target.com.au/rest/v2/target/stores/`
- Uses Australian postcode ranges to determine state
- Cached to avoid repeated API calls on monitor startup
- Format: `{"3316": {"state": "VIC", "name": "Ararat"}}`

**Setup:**
1. Run `python store_state_mapper.py` to generate initial store mapping
2. Configure webhooks in `config.py` (`WEBHOOK` + `STATE_WEBHOOKS`)
3. Run `python test_state_notifications.py` to verify notifications
4. Run `python monitor_enhanced.py` to start monitoring

### Big W Monitor (`monitors/bigw/`)

**⚠️ Experimental - Strong Bot Detection**

**Architecture:**
- Uses simple HTTP requests (requests library) to avoid detection footprint
- Extracts product data from Next.js `__NEXT_DATA__` embedded in HTML
- No Playwright/browser automation to reduce bot detection surface
- Binary stock tracking (in-stock/out-of-stock only, no per-state data)

**Key Features:**
- **Next.js data extraction**: Parses `<script id="__NEXT_DATA__">` JSON from HTML
- **Lightweight**: Uses requests library only, no browser automation
- **Product filtering**: Include/exclude keywords for card products
- **Simple stock tracking**: Tracks product codes in `INSTOCK` array

**Limitations:**
- **Bot detection**: Big W actively blocks automated requests with HTTP2 protocol errors and connection resets
- **No state-specific stock**: Only shows if product is in-stock or out-of-stock (not per-state like Kmart)
- **Requires workarounds**: May need residential proxies, VPN, or other anti-detection measures

**Files:**
- `monitor.py` - Main monitor using requests library
- `config.py` - Configuration including filters and webhooks
- `test_monitor.py` - Test script
- `README.md` - Detailed setup and troubleshooting guide

**Data Source:**
- Scrapes category pages (e.g., https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201)
- Extracts Next.js data: `props.pageProps.results.organic.results[]`
- Product structure: `{code, information: {name, brand}, derived: {stock, soldOut, priceRange, media}}`

**Setup:**
1. Edit `config.py` with webhook URL and category URL
2. Configure keyword filters if needed
3. Run `python test_monitor.py` (may fail due to bot detection)
4. Implement workarounds (proxies, VPN, etc.) if needed
5. Run `python monitor.py` to start monitoring

**Note**: This monitor is provided as a starting point. Due to Big W's strong bot detection, it may not work without additional anti-detection measures such as residential proxies, session management, or running less frequently.
