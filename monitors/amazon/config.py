# --------------------- WEBHOOK URL ---------------------
# Discord webhook URL - Get this from your Discord server
# Channel Settings → Integrations → Webhooks → New Webhook
WEBHOOK = "YOUR_DISCORD_WEBHOOK_URL_HERE"

# --------------------- AMAZON SEARCH URL ---------------------
# The Amazon.com.au search URL to monitor
# Examples:
#   Pokemon Cards: https://www.amazon.com.au/s?k=pokemon+cards
#   Specific category: https://www.amazon.com.au/s?k=pokemon+booster+box&rh=n:4998428051
#
# Tips for building search URLs:
# 1. Go to Amazon.com.au and search for your product
# 2. Apply filters (Prime, price range, ratings, etc.)
# 3. Copy the URL from the address bar
# 4. Paste it below
SEARCH_URL = "https://www.amazon.com.au/s?k=pokemon+cards"

# --------------------- DELAY ---------------------
# Delay between site requests (in seconds)
# Recommended: 60-120 seconds (Amazon has strong bot detection)
DELAY = 60

# --------------------- KEYWORDS ---------------------
# Products matching these keywords will be monitored
# Leave empty [] to monitor ALL products in the search
# Case-insensitive substring matching
# Examples: ["booster box", "elite trainer"], ["pikachu", "charizard"]
KEYWORDS = []

# --------------------- PRODUCT FILTERS ---------------------
# Only products containing these keywords will be included
# Helps filter for specific product types (e.g., only card products, not plush)
INCLUDE_KEYWORDS = ['tcg', 'booster', 'pack', 'card', 'deck', 'tin', 'box', 'collection', 'elite trainer', 'bundle', 'blister']

# Products containing these keywords will be EXCLUDED from notifications
# Filters out non-card Pokemon products
EXCLUDE_KEYWORDS = ['plush', 'toy', 'figure', 'figurine', 'book', 'dvd', 'blu-ray', 'clothing', 'shirt', 't-shirt', 'hoodie', 'backpack', 'bag', 'lunchbox', 'bottle', 'cup', 'mug', 'poster', 'sticker', 'puzzle', 'game', 'switch', 'console', 'controller', 'sleeve', 'binder', 'case', 'playmat']

# --------------------- PRICE FILTERS ---------------------
# Minimum and maximum price range (in AUD)
# Set to None to disable price filtering
# Examples: MIN_PRICE = 10, MAX_PRICE = 200
MIN_PRICE = None  # Minimum price in AUD (e.g., 10)
MAX_PRICE = None  # Maximum price in AUD (e.g., 500)

# --------------------- STOCK FILTERS ---------------------
# Only monitor products that are in stock and available for purchase
# Set to False to monitor all products including out-of-stock
ONLY_IN_STOCK = True

# Only monitor products with Amazon Prime shipping
# Set to False to include all sellers
PRIME_ONLY = False

# --------------------- EBAY LINKS ---------------------
# Enable eBay links in Discord notifications
ENABLE_EBAY_LINKS = True

# --------------------- DISCORD BOT FEATURES ---------------------
USERNAME = "Amazon AU"
AVATAR_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/1200px-Amazon_logo.svg.png"
COLOUR = 0xFF9900  # Amazon orange color

# --------------------- BROWSER SETTINGS ---------------------
# Run browser in headless mode (no visible window)
# Set to False if you want to see the browser window
# NOTE: Amazon has strong bot detection - try headless=False first to test
HEADLESS = True

# --------------------- PAGINATION ---------------------
# Maximum number of pages to scrape (Amazon shows ~48 products per page)
# Set to 1 to only scrape first page, or higher for more products
# Recommended: 1-3 pages to avoid long scraping times
MAX_PAGES = 1

# --------------------- LOGGING ---------------------
# Log file name
LOG_FILE = "amazon-monitor.log"
