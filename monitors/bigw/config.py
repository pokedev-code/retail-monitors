# --------------------- WEBHOOK URL ---------------------
# Discord webhook URL - Get this from your Discord server
# Channel Settings → Integrations → Webhooks → New Webhook
WEBHOOK = "https://discord.com/api/webhooks/1429889030622806058/LEBbtjCcHlb3O3G1CrO6bBSq9f5z9cbWe3Dvh41qzDMIBxiXMyYi1mZvlQ44SbaXhR0l"

# --------------------- BIG W CATEGORY URL ---------------------
# The Big W category page to monitor (Pokemon cards, Lego, etc.)
# Examples:
#   Pokemon Cards: https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201
#   Trading Cards (all): https://www.bigw.com.au/toys/trading-cards/c/6815102
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

# --------------------- BROWSER SETTINGS ---------------------
# Run browser in headless mode (no visible window)
# Set to False if you want to see the browser window
HEADLESS = True

# --------------------- LOGGING ---------------------
# Log file name
LOG_FILE = "bigw-monitor.log"
