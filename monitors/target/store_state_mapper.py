"""
Target Store State Mapper
Fetches all Target stores and maps store numbers to Australian states
"""
import requests
import json
import logging
from typing import Dict

# Postcode ranges for Australian states/territories
POSTCODE_RANGES = {
    'VIC': [(3000, 3999), (8000, 8999)],
    'QLD': [(4000, 4999), (9000, 9999)],
    'SA': [(5000, 5799), (5800, 5999)],
    'NSW': [(1000, 1999), (2000, 2599), (2911, 2999)],  # Exclude ACT range 2600-2910
    'WA': [(6000, 6799), (6900, 6999)],
    'TAS': [(7000, 7999)],
    'NT': [(800, 899), (900, 999)],
    'ACT': [(200, 299), (2600, 2910)],
}


def postcode_to_state(postcode: str) -> str:
    """
    Convert postcode to state code using postcode ranges
    """
    try:
        postcode_int = int(postcode)
    except (ValueError, TypeError):
        return 'UNKNOWN'

    for state, ranges in POSTCODE_RANGES.items():
        for min_code, max_code in ranges:
            if min_code <= postcode_int <= max_code:
                return state

    return 'UNKNOWN'


def fetch_all_stores() -> Dict[str, Dict]:
    """
    Fetch all Target stores and create store number -> state/name mapping
    Returns: {storeNumber: {'state': 'NSW', 'name': 'Sydney'}}
    """
    store_state_map = {}

    # Target stores API endpoint
    base_url = "https://www.target.com.au/rest/v2/target/stores/"

    # Headers to mimic browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-AU,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://www.target.com.au/',
        'Origin': 'https://www.target.com.au'
    }

    # Search terms to get stores from all states
    # Use state names to get comprehensive coverage
    search_terms = [
        'NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT',
        'Sydney', 'Melbourne', 'Brisbane', 'Adelaide', 'Perth', 'Hobart', 'Darwin', 'Canberra'
    ]

    try:
        print(f'[STORE MAPPER] Fetching stores from {len(search_terms)} search queries...')

        for search_term in search_terms:
            params = {
                'fields': 'FULL',
                'query': search_term,
                'pageSize': 1000  # Get as many as possible per query
            }

            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()

                stores = data.get('stores', [])
                logging.info(f'[STORE MAPPER] Query "{search_term}": Found {len(stores)} stores')
                print(f'  Query "{search_term}": {len(stores)} stores')

                for store in stores:
                    store_number = store.get('storeNumber')
                    store_name = store.get('name', 'Unknown Store')

                    # Skip if already mapped (avoid duplicates)
                    if store_number in store_state_map:
                        continue

                    # Try to get state from address
                    address = store.get('address', {})
                    state = address.get('state') or address.get('district')
                    postcode = address.get('postalCode')

                    if store_number:
                        # Normalize state format
                        if state:
                            # Convert "Wa", "WA", "wa" -> "WA"
                            state = state.upper()
                            # Handle full state names
                            state_mapping = {
                                'VICTORIA': 'VIC',
                                'QUEENSLAND': 'QLD',
                                'SOUTH AUSTRALIA': 'SA',
                                'NEW SOUTH WALES': 'NSW',
                                'WESTERN AUSTRALIA': 'WA',
                                'TASMANIA': 'TAS',
                                'NORTHERN TERRITORY': 'NT',
                                'AUSTRALIAN CAPITAL TERRITORY': 'ACT'
                            }
                            state = state_mapping.get(state, state)

                        # Fallback to postcode if state is missing or invalid
                        if not state or len(state) > 3:
                            if postcode:
                                state = postcode_to_state(str(postcode))

                        store_state_map[store_number] = {
                            'state': state,
                            'name': store_name
                        }

            except Exception as e:
                logging.warning(f'[STORE MAPPER] Error querying "{search_term}": {e}')
                continue

            # Small delay to avoid rate limiting
            import time
            time.sleep(0.5)

        print(f'\n[STORE MAPPER] Successfully mapped {len(store_state_map)} stores to states')

        # Log state distribution
        state_counts = {}
        for store_info in store_state_map.values():
            state = store_info['state']
            state_counts[state] = state_counts.get(state, 0) + 1

        print('[STORE MAPPER] State distribution:')
        for state in sorted(state_counts.keys()):
            print(f'  {state}: {state_counts[state]} stores')

        return store_state_map

    except requests.RequestException as e:
        logging.error(f'[STORE MAPPER] Error fetching stores: {e}')
        print(f'[ERROR] Failed to fetch stores: {e}')
        return {}


def save_store_mapping(mapping: Dict[str, str], filename: str = 'store_state_mapping.json'):
    """Save store mapping to file for caching"""
    try:
        with open(filename, 'w') as f:
            json.dump(mapping, f, indent=2)
        logging.info(f'[STORE MAPPER] Saved mapping to {filename}')
        print(f'[STORE MAPPER] Saved mapping to {filename}')
    except Exception as e:
        logging.error(f'[STORE MAPPER] Error saving mapping: {e}')


def load_store_mapping(filename: str = 'store_state_mapping.json') -> Dict[str, str]:
    """Load store mapping from file"""
    try:
        with open(filename, 'r') as f:
            mapping = json.load(f)
        logging.info(f'[STORE MAPPER] Loaded {len(mapping)} stores from {filename}')
        print(f'[STORE MAPPER] Loaded {len(mapping)} stores from cache')
        return mapping
    except FileNotFoundError:
        logging.warning(f'[STORE MAPPER] Mapping file {filename} not found')
        return {}
    except Exception as e:
        logging.error(f'[STORE MAPPER] Error loading mapping: {e}')
        return {}


if __name__ == '__main__':
    # Test the mapper
    logging.basicConfig(level=logging.INFO)

    print('Testing Target Store State Mapper')
    print('=' * 60)

    # Fetch stores
    mapping = fetch_all_stores()

    if mapping:
        # Save to file
        save_store_mapping(mapping)

        # Show some examples
        print('\n[EXAMPLES] Store number -> State + Name:')
        for store_num in list(mapping.keys())[:10]:
            store_info = mapping[store_num]
            print(f'  Store {store_num}: {store_info["state"]} - {store_info["name"]}')
