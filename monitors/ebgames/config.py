# --------------------- WEBHOOK URL ---------------------
# Discord webhook URL - Get this from your Discord server
# Channel Settings → Integrations → Webhooks → New Webhook
WEBHOOK = "https://discord.com/api/webhooks/1429941714893668505/sHU6_xN0mPFEk5p1Gops_2WdPeCV-N30_TMfpz5kXgwHLhadc-kgG6VoJYXHx9YsBV6z"

# --------------------- EB GAMES SEARCH URL ---------------------
# The EB Games search/category page to monitor
# Examples:
#   Pokemon Cards: https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards&attributes=franchise%3Apokemon
#   All Trading Cards: https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards
SEARCH_URL = "https://www.ebgames.com.au/search?category=toys-hobbies&subcategory=toys-hobbies-trading-cards&attributes=franchise%3Apokemon"

# --------------------- DELAY ---------------------
# Delay between site requests (in seconds)
# Recommended: 60-120 seconds (Playwright is slower, avoid rate limiting)
DELAY = 60

# --------------------- KEYWORDS ---------------------
# Products matching these keywords will be monitored
# Leave empty [] to monitor ALL products in the category
# Case-insensitive substring matching
# Examples: ["booster", "elite trainer"], ["pikachu", "charizard"]
KEYWORDS = []

# --------------------- PRODUCT FILTERS ---------------------
# Only products containing these keywords will be included
# Helps filter for specific product types
INCLUDE_KEYWORDS = ['tcg', 'booster', 'pack', 'card', 'deck', 'tin', 'box', 'collection', 'elite trainer', 'bundle', 'blister', 'chest']

# Products containing these keywords will be EXCLUDED from notifications
EXCLUDE_KEYWORDS = ['plush', 'toy', 'figure', 'figurine', 'book', 'dvd', 'blu-ray', 'clothing', 'shirt', 't-shirt', 'hoodie', 'backpack', 'bag', 'lunchbox', 'bottle', 'cup', 'mug', 'poster', 'sticker', 'puzzle', 'game', 'switch', 'console', 'controller']

# --------------------- EBAY LINKS ---------------------
# Enable eBay links in Discord notifications
ENABLE_EBAY_LINKS = True

# --------------------- DISCORD BOT FEATURES ---------------------
USERNAME = "EB Games"
AVATAR_URL = "https://www.ebgames.com.au/on/demandware.static/Sites-ebgames-Site/-/default/dw9c0c5e1f/images/logo.svg"
COLOUR = 0xE32526  # EB Games red color

# --------------------- BROWSER SETTINGS ---------------------
# Run browser in headless mode (no visible window)
# Set to False if you want to see the browser window
HEADLESS = True

# --------------------- LOGGING ---------------------
# Log file name
LOG_FILE = "ebgames-monitor.log"
