# --------------------- WEBHOOK URLS ---------------------
# Fallback webhook - used when STATE_WEBHOOKS is not configured
# This can also be used as a single webhook for all notifications (original behavior)
WEBHOOK = "https://discord.com/api/webhooks/1428801182532632728/VvLx8EJVLQBFv9MZMO4XRnTxtA7C2nYy01-_-qcHHwwDImMvWCKaUFBsc_YTn1TI8pVK"

# --------------------- STATE-SPECIFIC WEBHOOKS (OPTIONAL) ---------------------
# Configure different Discord webhooks for each Australian state
# Each state's notifications will go to its own Discord channel (e.g., #kmart-nsw, #kmart-vic)
#
# To set up:
# 1. Create Discord channels: #kmart-nsw, #kmart-vic, #kmart-qld, etc.
# 2. Create a webhook for each channel (Channel Settings → Integrations → Webhooks)
# 3. Copy each webhook URL and paste below
# 4. Set any state to None to use the fallback WEBHOOK instead
#
# Example configuration:
# STATE_WEBHOOKS = {
#     'NSW': "https://discord.com/api/webhooks/123456789/your-nsw-webhook-token-here",
#     'VIC': "https://discord.com/api/webhooks/123456789/your-vic-webhook-token-here",
#     'QLD': "https://discord.com/api/webhooks/123456789/your-qld-webhook-token-here",
#     'SA': None,  # Will use fallback WEBHOOK
#     'WA': None,  # Will use fallback WEBHOOK
#     'TAS': None,  # Will use fallback WEBHOOK
#     'NT': None,  # Will use fallback WEBHOOK
#     'ACT': None,  # Will use fallback WEBHOOK
# }

# Default: All states use the fallback WEBHOOK (single channel for all notifications)
STATE_WEBHOOKS = {
    'NSW': "https://discord.com/api/webhooks/1429832903650574499/3tVczYS6dvzFR8C7e9XcO7BWnG33tfHJToTIxZyUZhHxAyiJQ6-KU-A6sSoD2ovFrxoi",
    'VIC': "https://discord.com/api/webhooks/1429834231160242268/7Sb9a5jv_o34yB5rFp0UaQDwCDU-vIjVS0_ufZee6fZFI3OVo6zCnXLm9jMi-tJ0oKvL",
    'QLD': "https://discord.com/api/webhooks/1429834465080774780/ZLB-wFCFvcs0HxgowGkk4-2XSWVJgL3vUt1REAJspKVgDYx1335u2yz_JRooeknbHtW4",
    'SA': "https://discord.com/api/webhooks/1429834613068529827/MdYlwTmWfU76FzbeSKD6xz1SSYAh-5vlHajhumm2VTEnBT9loL-6jhTpkqKlbNfMbdFX",
    'WA': "https://discord.com/api/webhooks/1429834773869756597/SM3C8G_bn5IrhLdQvddMAEAPvC7EIzL1kku-6s3hhZ7gvJSEfJoqbT6I76bmBybMAwbn",
    'TAS': "https://discord.com/api/webhooks/1429834946155122780/6E5Q7qEa68Az6sl2wbd-EK2dFAk0CV16TPpknh5tw0FZRWeoZ5bu84FohKYvZ0XuzVsV",
    'NT': "https://discord.com/api/webhooks/1429835183355330792/T3T8Vsto9kQZCCvwBfa7gNGL5-ywdx9rl9ig6QNAgSQB2mKjztJhEjvc2RqrrogbEWl4",
    'ACT': "https://discord.com/api/webhooks/1429835338116890767/r8TpsaCL4rq-ByH_n_AH7eGwT5wzAzGLhtVFUXgB3OpW3flsnclex0jXMeHUQwG6UKZc",
}

# --------------------- PRODUCT CONFIGURATION ---------------------
# Option 1: Monitor specific products by ID (recommended for reliability)
# Add product dicts with 'id', 'title', and 'url'
# To get product ID: visit product page, ID is in URL (e.g., /product/pokemon-...-43350070/)
PRODUCTS = [
    # Leave empty to monitor entire category page instead
]

# Option 2: Scrape category page (ENABLED - monitors ALL Pokemon cards)
# Leave PRODUCTS list empty to use this method
# Kmart category page URL (e.g., Pokemon cards, toys, electronics, etc.)
# Examples:
#   Pokemon Cards: https://www.kmart.com.au/category/toys/pokemon-trading-cards/
#   Trading Cards: https://www.kmart.com.au/category/sports-leisure/games-puzzles/trading-cards/342177
URL = "https://www.kmart.com.au/category/toys/pokemon-trading-cards/"

# --------------------- FREE PROXY ---------------------
# A single or multiple locations can be added in the array (e.g. ["AU"] or ["AU", "US"])
ENABLE_FREE_PROXY = False
FREE_PROXY_LOCATION = ["AU"]

# --------------------- DELAY ---------------------
# Delay between site requests (in seconds)
DELAY = 30

# --------------------- OPTIONAL PROXY ---------------------
# Proxies must follow this format: "<proxy>:<port>" OR "<proxy_username>:<proxy_password>@<proxy_domain>:<port>")
# If you want to use multiple proxies, please create an array
# E.G. PROXY = ["proxy1:proxy1port", "proxy2:proxy2port"]
PROXY = []

# --------------------- OPTIONAL KEYWORDS ---------------------
# Keywords to filter products (case-insensitive)
# E.G. KEYWORDS = ["Scarlet","Violet","Booster"]
# Leave empty to monitor all products
# Note: Match partial keywords like "pokemon" or "card" for broader matching
KEYWORDS = ["pokemon", "card", "TCG", "pokemon TCG"]

# --------------------- STORE LOCATION ---------------------
# Your state/region (e.g., VIC, NSW, QLD, etc.)
# Set to "All States" to monitor nationally
STATE = "All States"

# --------------------- DISCORD BOT FEATURES ---------------------
USERNAME = "Pokemon Card Monitor"
AVATAR_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Kmart_Australia_logo.svg/1200px-Kmart_Australia_logo.svg.png"
COLOUR = 3447003  # Blue color matching screenshot

# --------------------- EBAY INTEGRATION ---------------------
# Enable eBay price comparison links
ENABLE_EBAY_LINKS = True
