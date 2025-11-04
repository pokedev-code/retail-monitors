# --------------------- WEBHOOK URL ---------------------
# Discord webhook URL - Get this from your Discord server
# Channel Settings → Integrations → Webhooks → New Webhook
WEBHOOK = "https://discord.com/api/webhooks/1429889030622806058/LEBbtjCcHlb3O3G1CrO6bBSq9f5z9cbWe3Dvh41qzDMIBxiXMyYi1mZvlQ44SbaXhR0l"

# --------------------- BIG W CATEGORY URL ---------------------
# The Big W category page to monitor (Pokemon cards, Lego, etc.)
# Examples:
#   Pokemon Cards: https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201
#   Trading Cards (all): https://www.bigw.com.au/toys/trading-cards/c/6815102
#
# Note: Marketplace items are filtered out automatically in the code (productChannel == "IMP")
CATEGORY_URL = "https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201"

# --------------------- DELAY ---------------------
# Delay between site requests (in seconds)
# Recommended: 30-60 seconds to avoid being rate limited
DELAY = 30

# --------------------- KEYWORDS ---------------------
# Products matching these keywords will be monitored
# Leave empty [] to monitor ALL products in the category
# Case-insensitive substring matching
# Examples: ["booster", "elite trainer"], ["pikachu", "charizard"]
KEYWORDS = []

# --------------------- PRODUCT FILTERS ---------------------
# Only products containing these keywords will be included
# Helps filter for specific product types (e.g., only card products, not plush)
INCLUDE_KEYWORDS = ['tcg', 'booster', 'pack', 'card', 'deck', 'tin', 'box', 'collection', 'elite trainer', 'bundle', 'blister']

# Products containing these keywords will be EXCLUDED from notifications
# Filters out non-card Pokemon products
EXCLUDE_KEYWORDS = ['plush', 'toy', 'figure', 'figurine', 'book', 'dvd', 'blu-ray', 'clothing', 'shirt', 't-shirt', 'hoodie', 'backpack', 'bag', 'lunchbox', 'bottle', 'cup', 'mug', 'poster', 'sticker', 'puzzle', 'game', 'switch', 'console', 'controller']

# --------------------- EBAY LINKS ---------------------
# Enable eBay links in Discord notifications
ENABLE_EBAY_LINKS = True

# --------------------- DISCORD BOT FEATURES ---------------------
USERNAME = "BIG W"
AVATAR_URL = "https://www.bigw.com.au/medias/sys_master/root/h16/h26/34654850818078/new-logo-192x144.png"
COLOUR = 0xFF0000  # Red color for Big W brand

# --------------------- PROXY SETTINGS ---------------------
# Proxy configuration to bypass bot detection
# Set PROXY_ENABLED = True to use proxies

PROXY_ENABLED = False  # Set to True to enable proxy support

# Option 1: Use FREE proxies (automatic fetching)
# NOTE: Free proxies are often slow, unreliable, and may not work with Big W
# But it's worth trying before buying residential proxies!
USE_FREE_PROXIES = False  # Automatically fetch free proxies

# Option 2: Custom proxy list (recommended for residential proxies)
# Format: "protocol://username:password@host:port" or "protocol://host:port"
# Examples:
#   HTTP: "http://user:pass@proxy.example.com:8080"
#   SOCKS5: "socks5://user:pass@proxy.example.com:1080"
PROXY_LIST = [
    # Add your proxies here, one per line
    # "http://user:pass@proxy1.example.com:8080",
    # "http://user:pass@proxy2.example.com:8080",
]

# Option 3: Single proxy (if you only have one)
SINGLE_PROXY = None  # Example: "http://user:pass@proxy.example.com:8080"

# Free proxy settings
FREE_PROXY_TIMEOUT = 5  # Seconds to wait for free proxy to respond
FREE_PROXY_FETCH_COUNT = 5  # How many free proxies to fetch at once (reduced for speed)

# Proxy rotation settings
ROTATE_PROXY_ON_ERROR = True  # Rotate to next proxy if current one fails
PROXY_RETRY_LIMIT = 3  # How many proxies to try before giving up

# --------------------- BROWSER SETTINGS ---------------------
# Run browser in headless mode (no visible window)
# Set to False if you want to see the browser window
# NOTE: Big W has strong bot detection - try headless=False first to test
HEADLESS = False

# --------------------- LOGGING ---------------------
# Log file name
LOG_FILE = "bigw-monitor.log"
