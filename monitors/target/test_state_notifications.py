"""
Test script to verify Target state-specific webhook notifications
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from store_state_mapper import load_store_mapping
from monitor_enhanced import discord_webhook, group_stores_by_state, STORE_STATE_MAP
import config

# Load the store mapping
print("Testing Target State-Specific Notifications")
print("=" * 60)

print("\n[1] Loading store-to-state mapping...")
store_mapping = load_store_mapping()

if not store_mapping:
    print("[ERROR] No store mapping found. Run store_state_mapper.py first!")
    sys.exit(1)

print(f"   Loaded {len(store_mapping)} stores")

# Update global mapping
import monitor_enhanced
monitor_enhanced.STORE_STATE_MAP = store_mapping

print("\n[2] Checking webhook configuration...")
configured_states = []
for state, webhook in config.STATE_WEBHOOKS.items():
    if webhook and webhook.startswith('https://discord.com/api/webhooks/'):
        configured_states.append(state)
        print(f"   {state}: Configured [OK]")
    else:
        print(f"   {state}: Not configured (will use fallback)")

if not configured_states:
    print("\n[WARNING] No state-specific webhooks configured!")
    print("All notifications will use fallback webhook.")
else:
    print(f"\n   {len(configured_states)} state(s) configured")

print("\n[3] Creating test product with multi-state stock...")

# Create a mock product with stores from different states
# Using real store numbers from our mapping
test_stores = []
states_to_test = []

# Pick 2-3 stores from different states for testing
for state in ['NSW', 'VIC', 'WA']:
    # Find stores in this state
    # Handle new format: {'state': 'NSW', 'name': 'Sydney'}
    stores_in_state = []
    for store_num, store_info in store_mapping.items():
        if isinstance(store_info, dict):
            if store_info.get('state') == state:
                stores_in_state.append(store_num)
        elif store_info == state:  # Old format
            stores_in_state.append(store_num)

    if stores_in_state:
        test_stores.append(stores_in_state[0])
        states_to_test.append(state)

print(f"   Test stores: {test_stores}")
print(f"   States represented: {states_to_test}")

# Group by state
state_groups = group_stores_by_state(test_stores)
print(f"\n   Grouped by state:")
for state, stores in state_groups.items():
    print(f"      {state}: {stores}")

# Create mock product
test_product = {
    'id': '71824284',
    'title': 'TEST: Pokemon TCG Mega Evolution Blister (State Notification Test)',
    'url': 'https://www.target.com.au/p/pokemon-tcg-mega-evolution-blister-assorted/71824284',
    'price': '$8.50',
    'image': 'https://target.scene7.com/is/image/Target/71824284',
    'availability': 'In Stock',
    'stock_info': {
        'delivery_modes': {
            'Home Delivery': 'outOfStock',
            'Express Delivery': 'outOfStock',
            'Click & Collect': 'inStock'
        },
        'stores_with_stock': test_stores,
        'consolidated_stock': 'inStock'
    }
}

print(f"\n[4] Sending test notifications...")
print(f"    This will send 1 main + {len(state_groups)} state-specific notifications\n")

# First: Send to main unfiltered webhook (all stores)
print(f"   [MAIN] Sending to unfiltered webhook (all states combined)...")
print(f"      All stores: {test_stores}")
discord_webhook(test_product)  # No state_name = uses fallback WEBHOOK

print()

# Then: Send to state-specific webhooks
for state, stores in state_groups.items():
    print(f"   [{state}] Sending to state-specific webhook...")
    print(f"      Stores: {stores}")
    discord_webhook(test_product, state_name=state, state_stores=stores)

print("\n[SUCCESS] Test complete!")
print(f"   - Sent 1 main notification (unfiltered)")
print(f"   - Sent {len(state_groups)} state-specific notifications")
print("\n   Check your Discord channels:")
print(f"     * Main unfiltered channel should show ALL stores: {', '.join([s['name'] for stores in state_groups.values() for s in stores])}")
for state in state_groups.keys():
    if state in configured_states:
        print(f"     * #{state.lower()} (target-{state.lower()}) should have a notification")
    else:
        print(f"     * {state} notification went to fallback webhook")

print("\nExpected notification format:")
print("   Main webhook: Shows all stores across all states")
print("   State webhooks: Shows only stores in that specific state")
print("   - Price: $8.50")
print("   - Store: Target AU")
print("   - Product ID: 71824284")
print("   - Delivery Options: [checkmark]/[X] for each mode")
print("   - eBay Links")
