# --------------------- WEBHOOK URLS ---------------------
# Fallback webhook - used when STATE_WEBHOOKS is not configured
# This can also be used as a single webhook for all notifications (original behavior)
WEBHOOK = "https://discord.com/api/webhooks/1429181362169974848/h44prs1hsqDyvq9HRh1Qi0eZIsFJsUaLZnfrTYWDOZuRhxh64BRCQCavBu_hDgUcN4bh"

# --------------------- STATE-SPECIFIC WEBHOOKS (OPTIONAL) ---------------------
# Configure different Discord webhooks for each Australian state
# Each state's notifications will go to its own Discord channel (e.g., #target-nsw, #target-vic)
#
# To set up:
# 1. Create Discord channels: #target-nsw, #target-vic, #target-qld, etc.
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
    'NSW': "https://discord.com/api/webhooks/1429856592916119633/2eg9InBsY3NVJz6JM7eZALpVb7NA-TXxaJMPr-ERLCXtXTg6tD4v2ebt4GE9VlwTriug",
    'VIC': "https://discord.com/api/webhooks/1429856928544198839/w--sSDmNH7CRvESDqf7jLKRFMNV41To-YFg1Paw2N_YVC6MPmSzlIZFu8-N_I5jfC_73",
    'QLD': "https://discord.com/api/webhooks/1429857085235138752/NJIY497pG6jfAG1UDlpBTvsPOyzK9dmgGGiLWtNIlvgx_TRVbvPq3e2sS69laK1chaYo",
    'SA': "https://discord.com/api/webhooks/1429857296229601301/alH0FT08PlQ3r0kWOQ9C_RLFHr5iZFV4krNcQepJpHEA8U3oigheJD2h6DbF8LY3fT8u",
    'WA': "https://discord.com/api/webhooks/1429857445840158742/wPIp8yRQlZFW_iAIN3go3TMzBeqlaV2ElPE-bHvecCNiDp52cWdhw6d-bwj37CD6hoXU",
    'TAS': "https://discord.com/api/webhooks/1429857588412944506/-j95t_dPrXQd3VbYuy21ISQnswEU24AGTJHQL1NBIAbRVPDzf8z-Fd0xnph4WRN0EAM2",
    'NT': "https://discord.com/api/webhooks/1429857777039179929/d7lTqxNB4CthO8VXsgQ-Fk_MC1zoHZ2nRau-ZYtBM4qeL9jBPdpN2qvehU97Xfbw9xZ4",
    'ACT': "https://discord.com/api/webhooks/1429857942877896735/cVqjhIjCJ5KS5X23e9VyFWFYjvb2c_3jmqCqtOfWr9pacQU_RqlG2Rwk8p8MoG1DTv9H",
}

# --------------------- TARGET SEARCH URL ---------------------
# Base URL for Target Australia search (keywords will be appended automatically)
BASE_URL = "https://www.target.com.au/search?sEngine=c&text="

# --------------------- DELAY ---------------------
# Delay between site requests (in seconds)
DELAY = 30

# --------------------- KEYWORDS ---------------------
# Products matching these keywords will be monitored
# E.G. KEYWORDS = ["pokemon cards", "lego"]
KEYWORDS = ["pokemon cards"]

# --------------------- CARD PRODUCT FILTERS ---------------------
# For Pokemon card searches, only products containing these keywords will be included
# These help ensure we only notify about actual card products, not toys/plush/etc
CARD_INCLUDE_KEYWORDS = ['tcg', 'booster', 'pack', 'card', 'deck', 'tin', 'box', 'collection', 'elite trainer', 'bundle', 'blister']

# Products containing these keywords will be EXCLUDED from notifications
# These filter out non-card Pokemon products like toys, clothing, etc
# Also excludes other trading card games (Yu-Gi-Oh!, NBA, FIFA, etc.)
CARD_EXCLUDE_KEYWORDS = [
    # Non-card Pokemon products
    'plush', 'toy', 'figure', 'figurine', 'book', 'dvd', 'blu-ray', 'clothing', 'shirt', 't-shirt',
    'hoodie', 'backpack', 'bag', 'lunchbox', 'bottle', 'cup', 'mug', 'poster', 'sticker', 'puzzle',
    'game', 'switch', 'console', 'controller',
    # Other trading card games (NOT Pokemon)
    'yu-gi-oh', 'yugioh', 'nba', 'basketball', 'soccer', 'football', 'fifa', 'premier league',
    'panini', 'donruss', 'prizm', 'topps', 'adrenalyn', 'cricket', 'baseball', 'hockey', 'nfl',
    'nrl', 'afl', 'formula 1', 'f1', 'wwe', 'ufc', 'one piece', 'dragon ball', 'magic the gathering',
    'mtg', 'flesh and blood', 'fab', 'marvel', 'digimon', 'lorcana'
]

# --------------------- EBAY LINKS ---------------------
# Enable eBay links in Discord notifications (like Kmart bot)
ENABLE_EBAY_LINKS = True

# --------------------- DISCORD BOT FEATURES ---------------------
USERNAME = "Target AU"
AVATAR_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Target_logo.svg/1200px-Target_logo.svg.png"
COLOUR = 16711680  # Red color for Target brand

# --------------------- IMPORTANT NOTE ---------------------
# Target AU has strong bot detection and blocks headless browsers.
# The monitor MUST run with a visible browser window (headless=False).
# You can minimize the window, but it must remain open while monitoring.
