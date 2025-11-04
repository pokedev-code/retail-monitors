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
- `bigw` - Big W Australia (Playwright-enhanced with proxy support, multi-page scraping, Next.js data extraction)
- `ebgames` - EB Games Australia (Playwright-based with product filtering, eBay integration)
- `amazon` - Amazon Australia (Playwright-based with advanced filtering, Prime detection, rating tracking)

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

**Architecture:**
- Uses Playwright (async Chromium browser automation) with anti-detection features
- Extracts product data from Next.js `__NEXT_DATA__` embedded in HTML across all category pages
- HTTP/2 disabled to avoid protocol errors
- Binary stock tracking (in-stock/out-of-stock only, no per-state data)
- Supports proxy rotation (free, single, or custom proxy lists)

**Key Features:**
- **Next.js data extraction**: Parses `<script id="__NEXT_DATA__">` JSON from HTML
- **Multi-page scraping**: Automatically detects page count and loads all pages in parallel for complete product coverage
- **Marketplace filtering**: Automatically filters out marketplace items (productChannel == "IMP"), only monitors Big W products
- **Proxy support**: Supports free proxies, single proxy, or custom proxy lists with automatic rotation
- **Anti-detection**: Browser fingerprint masking, HTTP/2 disabled, stealth scripts
- **Product filtering**: Include/exclude keywords for card products
- **eBay integration**: Optional eBay current/sold listings links in notifications

**Proxy Configuration:**
- **Free proxies**: Set `USE_FREE_PROXIES = True` for automatic proxy fetching (slow, unreliable)
- **Single proxy**: Set `SINGLE_PROXY = "http://user:pass@host:port"` for one proxy
- **Proxy list**: Add multiple proxies to `PROXY_LIST` array for rotation
- **Proxy formats**: Supports HTTP (`http://`), SOCKS5 (`socks5://`), with or without authentication
- **Auto-rotation**: Set `ROTATE_PROXY_ON_ERROR = True` to rotate proxies on failures

**Limitations:**
- **Bot detection**: Big W has VERY strong bot detection - residential proxies highly recommended
- **No state-specific stock**: Only shows if product is in-stock or out-of-stock (not per-state like Kmart)
- **Proxy cost**: Residential proxies required (~$1.75-$15/GB depending on provider)

**Files:**
- `monitor.py` - Main monitor using Playwright with proxy support
- `config.py` - Configuration including filters, webhooks, and proxy settings
- `test_monitor.py` - Test script
- `README.md` - Detailed setup, proxy configuration, and troubleshooting guide

**Data Source:**
- Scrapes category pages (e.g., https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201)
- Automatically detects total page count from first page
- Loads all pages in parallel using Playwright context
- Extracts Next.js data: `props.pageProps.results.organic.results[]`
- Product structure: `{code, information: {name, brand}, derived: {stock, soldOut, priceRange, media}, fulfillment: {productChannel}}`

**Setup:**
1. Install Playwright: `pip install playwright && playwright install chromium`
2. Edit `config.py` with webhook URL and category URL
3. Configure proxy settings (residential proxies recommended):
   - Option 1: Set `SINGLE_PROXY` for one proxy
   - Option 2: Add proxies to `PROXY_LIST` for rotation
   - Option 3: Set `USE_FREE_PROXIES = True` (not recommended, high failure rate)
4. Configure keyword filters if needed
5. Set `HEADLESS = False` initially to watch browser behavior
6. Run `python monitor.py` to start monitoring

**Proxy Providers (Residential):**
- **IPRoyal**: ~$1.75/GB (cheapest)
- **Smartproxy**: ~$8/GB
- **Bright Data**: ~$8.40/GB
- **Oxylabs**: ~$15/GB

**Cost Estimates:**
- Light monitoring (60s delay): ~$1.75-$8/day
- Normal monitoring (30s delay): ~$3.50-$17/day
- Aggressive monitoring (10s delay): ~$10-$50/day

**Note**: Big W's bot detection is very strong. This monitor provides anti-detection features (HTTP/2 disabled, fingerprint masking, stealth scripts), but **residential proxies are highly recommended** for reliable operation. Free proxies typically don't work. See README.md for detailed proxy setup guide.

### EB Games Monitor (`monitors/ebgames/`)

**Architecture:**
- Uses Playwright (Chromium browser automation) for anti-bot protection bypass
- Scrapes search/category pages using JavaScript evaluation
- Tracks products by unique product IDs extracted from URLs or data attributes
- No API available - pure HTML scraping with multiple selector fallbacks

**Key Features:**
- **Playwright automation**: Uses real browser to bypass EB Games bot protection
- **Flexible selectors**: Multiple fallback selectors for product cards, titles, prices, stock status
- **Title cleaning**: Automatically removes prices, "PREORDER" text, and delivery info from titles
- **Stock status tracking**: Detects "Available", "PreOrder", and "Out of Stock" statuses
- **Product filtering**: Include/exclude keywords for card products
- **eBay integration**: Optional eBay current/sold listings links in notifications
- **Image extraction**: Captures product images from img tags with data-src fallback

**Limitations:**
- **Slower than API monitors**: Each scrape takes 5-10 seconds (vs 1-2s for Kmart/Target/Big W)
- **Higher resource usage**: Runs full Chrome browser
- **Bot detection risk**: May get blocked if running too frequently (recommended: 60-120s delay)
- **No per-store stock**: Only shows online availability
- **No state-specific stock**: Binary in-stock/out-of-stock tracking

**Files:**
- `monitor.py` - Main monitor using Playwright
- `config.py` - Configuration including filters and webhooks
- `test_monitor.py` - Test script
- `README.md` - Detailed setup and troubleshooting guide
- `ebgames-monitor.log` - Log file

**Data Source:**
- Scrapes search/category pages (e.g., https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards&attributes=franchise%3Apokemon)
- Extracts data via JavaScript evaluation in browser
- Multiple selector fallbacks: `.product-tile`, `.product-card`, `[data-product-id]`, `article`, `.product-item`
- Product ID extraction from URL pattern: `/(\d+)-` or `data-product-id` attribute

**Setup:**
1. Install Playwright: `pip install playwright && playwright install chromium`
2. Find your search URL:
   - Go to https://www.ebgames.com.au/
   - Navigate to category (e.g., Toys & Hobbies → Trading Cards)
   - Apply filters (e.g., Franchise: Pokemon)
   - Copy the URL from address bar
3. Edit `config.py`:
   - Set `WEBHOOK` to your Discord webhook URL
   - Set `SEARCH_URL` to the copied URL
   - Set `DELAY` to 60-120 seconds (recommended to avoid detection)
   - Configure `INCLUDE_KEYWORDS` and `EXCLUDE_KEYWORDS` for filtering
4. Set `HEADLESS = False` initially to watch browser behavior
5. Run `python monitor.py` to start monitoring

**Performance Comparison:**

| Monitor | Method | Speed | Reliability |
|---------|--------|-------|-------------|
| Kmart | GraphQL API | ⚡ Fast (1-2s) | ✅ Excellent |
| Target | API Intercept | ⚡ Fast (1-2s) | ✅ Excellent |
| Big W | Next.js + Playwright | ⚡ Fast (1-2s) | ✅ Good (needs proxies) |
| **EB Games** | **Playwright HTML** | 🐌 **Slow (5-10s)** | ⚠️ **Good** |

**Finding Search URLs:**
- Pokemon Cards: `https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards&attributes=franchise%3Apokemon`
- All Trading Cards: `https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards`

**Note**: EB Games blocks simple HTTP requests (403 Forbidden) and requires Playwright browser automation. The monitor is significantly slower than API-based monitors but more reliable than early Big W attempts. Recommended delay: 60-120 seconds to avoid rate limiting and bot detection.

### Amazon Australia Monitor (`monitors/amazon/`)

**Architecture:**
- Uses Playwright (Chromium browser automation) for anti-bot protection bypass
- Scrapes search result pages using JavaScript evaluation
- Tracks products by ASIN (Amazon Standard Identification Number)
- Supports pagination to scrape multiple result pages
- No API available - pure HTML scraping with data-asin attribute targeting

**Key Features:**
- **ASIN-based tracking**: Tracks products by unique Amazon identifier
- **Advanced filtering**: Price range, Prime eligibility, stock status, keyword matching
- **Rating & review tracking**: Captures star ratings and review counts
- **Prime detection**: Identifies Prime-eligible products
- **Multi-page scraping**: Configurable pagination (MAX_PAGES setting)
- **Product filtering**: Include/exclude keywords for targeted monitoring
- **eBay integration**: Optional eBay current/sold listings links in notifications
- **Image extraction**: Captures product thumbnail images

**Filtering Options:**
- **Price range**: MIN_PRICE / MAX_PRICE in AUD
- **Stock status**: ONLY_IN_STOCK (filter out unavailable products)
- **Prime only**: PRIME_ONLY (only track Prime-eligible items)
- **Keywords**: INCLUDE_KEYWORDS / EXCLUDE_KEYWORDS for product name filtering
- **Custom search**: Use Amazon's own filters in the search URL

**Limitations:**
- **VERY strong bot detection** - Strongest of all monitors, may encounter CAPTCHAs
- **Slower than API monitors** - Each page takes 5-10 seconds
- **Higher detection risk** - Amazon actively blocks scrapers more than other retailers
- **Rate limiting** - Must use 60-120s delays to avoid blocks
- **No seller filtering** - Can't filter by specific sellers (except Prime checkbox)
- **Binary stock data** - No quantity information, only in-stock/out-of-stock
- **CAPTCHA risk** - May require manual solving or proxy rotation

**Files:**
- `monitor.py` - Main monitor using Playwright
- `config.py` - Configuration including filters, price range, Prime settings
- `test_monitor.py` - Test script (visible browser, no notifications)
- `README.md` - Detailed setup and troubleshooting guide
- `amazon-monitor.log` - Log file

**Data Source:**
- Scrapes search pages (e.g., https://www.amazon.com.au/s?k=pokemon+cards)
- Targets `div[data-asin]` containers for product data
- Supports pagination with `&page=N` URL parameter
- Extracts: title, price, rating, reviews, Prime badge, stock status, image
- ASIN extracted from `data-asin` attribute

**Setup:**
1. Install Playwright: `pip install playwright && playwright install chromium`
2. Build your search URL:
   - Go to https://www.amazon.com.au/
   - Search for products (e.g., "pokemon cards")
   - Apply filters (department, Prime, price, brand, rating)
   - Copy URL from address bar
3. Edit `config.py`:
   - Set `WEBHOOK` to your Discord webhook URL
   - Set `SEARCH_URL` to the copied Amazon URL
   - Set `DELAY` to 60-120 seconds (important for avoiding detection!)
   - Configure filters: MIN_PRICE, MAX_PRICE, PRIME_ONLY, ONLY_IN_STOCK
   - Set `MAX_PAGES` (1-3 recommended to avoid detection)
   - Configure INCLUDE_KEYWORDS and EXCLUDE_KEYWORDS
4. Test first: `python test_monitor.py` (visible browser, no notifications)
5. If successful, run: `python monitor.py`

**Performance Comparison:**

| Monitor | Method | Speed | Reliability | Bot Detection | Scraping Difficulty |
|---------|--------|-------|-------------|---------------|---------------------|
| Kmart | GraphQL API | ⚡ Fast (1-2s) | ✅ Excellent | ✅ Low | ⭐ Easy |
| Target | API Intercept | ⚡ Fast (1-2s) | ✅ Excellent | ✅ Low | ⭐ Easy |
| Big W | Next.js + Playwright | ⚡ Fast (1-2s) | ✅ Good | ⚠️ High | ⭐⭐ Medium |
| EB Games | Playwright HTML | 🐌 Slow (5-10s) | ⚠️ Good | ⚠️ Medium | ⭐⭐ Medium |
| **Amazon** | **Playwright HTML** | 🐌 **Slow (5-10s)** | ⚠️ **Fair** | 🔴 **VERY High** | ⭐⭐⭐ **Hard** |

**Building Search URLs:**

Amazon search URLs contain filters in the query string:
- `k=` - Search keywords (e.g., `k=pokemon+cards`)
- `rh=` - Refinements/filters
  - `n:` - Category/department ID
  - `p_85:` - Prime eligible (`p_85:5408138051` for AU)
  - `p_36:` - Price range in cents (`p_36:1000-5000` = $10-$50)
  - `p_89:` - Brand filter
- `i=` - Department (e.g., `i=toys`)
- `page=` - Page number (added automatically by monitor)

**Examples:**
```
# Basic search
https://www.amazon.com.au/s?k=pokemon+cards

# With category and Prime
https://www.amazon.com.au/s?k=pokemon+booster+box&rh=n:4998428051,p_85:5408138051

# With price range ($10-$50)
https://www.amazon.com.au/s?k=pokemon+cards&rh=p_36:1000-5000

# With department and brand
https://www.amazon.com.au/s?k=pokemon+cards&i=toys&rh=p_89:Pokemon
```

**Bot Detection Mitigation:**
1. **Use long delays**: 60-120 seconds minimum between requests
2. **Limit pages**: Set MAX_PAGES to 1-2 (not 5+)
3. **Test first**: Always run test_monitor.py to check for CAPTCHAs
4. **Run headless=False initially**: Watch what Amazon sees
5. **Don't run 24/7**: Take breaks to avoid detection patterns
6. **Consider proxies**: Residential proxies help but add cost (see Big W README)
7. **Accept limitations**: Amazon scraping is inherently risky and unreliable

**Alternative - Amazon Product Advertising API:**
For commercial or high-volume use, use Amazon's official API:
- https://affiliate-program.amazon.com.au/help/operating/api
- Requires affiliate account approval
- Legal and supported by Amazon
- No bot detection issues
- Rate limits and potential fees apply

**Note**: Amazon has the strongest bot detection of all monitored retailers. This monitor is a proof-of-concept for personal use. Expect CAPTCHAs and blocks if running aggressively. For reliable long-term monitoring, use Amazon's official Product Advertising API or consider residential proxies with very conservative delays (120+ seconds). The monitor is best suited for occasional checks rather than continuous 24/7 monitoring.
