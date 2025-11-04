"""
Test the product filtering to verify non-Pokemon cards are excluded
"""
import sys
sys.path.insert(0, '.')
import config

def is_pokemon_card_product(title: str) -> bool:
    """Filter logic to determine if product is a Pokemon card product"""
    title_lower = title.lower()

    # First check if it's actually a Pokemon product
    is_pokemon = 'pokemon' in title_lower or 'pokémon' in title_lower
    if not is_pokemon:
        # If it's not a Pokemon product at all, exclude it
        return False

    # Check if it's a card product (has card-related keywords)
    is_card_product = any(keyword in title_lower for keyword in config.CARD_INCLUDE_KEYWORDS)
    if not is_card_product:
        # It's Pokemon but not a card product (e.g., plush, toy)
        return False

    # Check for exclusions, but ignore "game" since "Trading Card Game" is valid for Pokemon TCG
    exclusions_to_check = [kw for kw in config.CARD_EXCLUDE_KEYWORDS if kw != 'game']
    is_excluded = any(keyword in title_lower for keyword in exclusions_to_check)

    return not is_excluded


# Test cases from user's output
test_products = [
    "Panini NBA Prizm Basketball 2024-25 Trading Cards",
    "Panini NBA Donruss Basketball 2024-25 Trading Cards",
    "Yu-Gi-Oh! TCG: Duelist's Advance Blister Pack - Assorted",
    "Topps Premier League 2026 Mega Tin - Assorted",
    "Yu-Gi-Oh! TCG Justice Hunters 7 x Card Blister Pack - Assorted",
    "Panini FIFA Top Class Soccer 2025 - Trading Card Booster Pack",
    "Panini Adrenalyn XL Plus 2025 EPL Soccer Trading Cards - Assorted",
    # Pokemon cards (should PASS)
    "Pokemon Trading Card Game: Scarlet & Violet Booster Pack",
    "Pokemon TCG Elite Trainer Box",
    "Pokemon Trading Cards - Sword & Shield Blister Pack"
]

print("=" * 80)
print("TESTING PRODUCT FILTERS")
print("=" * 80)

for product in test_products:
    result = is_pokemon_card_product(product)
    status = "[PASS - Pokemon card]" if result else "[FILTERED OUT]"
    print(f"\n{status}")
    print(f"  {product}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total products tested: {len(test_products)}")
print(f"Pokemon cards (should pass): 3")
print(f"Other cards (should be filtered): {len(test_products) - 3}")
print("\nExpected: Only the last 3 products should PASS")
print("=" * 80)
