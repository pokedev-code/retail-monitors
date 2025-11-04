"""
Quick test to see if free proxies can be fetched and work with Big W
"""
import sys
sys.path.insert(0, '..')

try:
    from fp.fp import FreeProxy
    print("[OK] Free proxy library loaded")

    print("\n[1/3] Fetching 3 free proxies...")
    proxies = []
    for i in range(3):
        try:
            proxy_obj = FreeProxy(timeout=5, rand=True, https=True)
            proxy = proxy_obj.get()
            if proxy:
                proxies.append(proxy)
                print(f"  [OK] Proxy {i+1}: {proxy}")
        except Exception as e:
            print(f"  [FAIL] Failed to fetch proxy {i+1}: {e}")

    if not proxies:
        print("\n[FAIL] Could not fetch any free proxies")
        sys.exit(1)

    print(f"\n[OK] Successfully fetched {len(proxies)} proxies")

    # Test one proxy with a simple request
    print("\n[2/3] Testing first proxy with a simple HTTP request...")
    import requests
    test_proxy = proxies[0]

    try:
        proxies_dict = {
            'http': test_proxy,
            'https': test_proxy
        }
        response = requests.get('http://httpbin.org/ip', proxies=proxies_dict, timeout=10)
        print(f"  [OK] Proxy works! Response: {response.json()}")
    except Exception as e:
        print(f"  [FAIL] Proxy failed: {e}")

    # Test with Big W
    print("\n[3/3] Testing proxy with Big W (this will likely fail)...")
    try:
        response = requests.get(
            'https://www.bigw.com.au/toys/trading-cards/pokemon-trading-cards/c/681510201',
            proxies=proxies_dict,
            timeout=15
        )
        if response.status_code == 200:
            print(f"  [OK] SUCCESS! Proxy works with Big W!")
        else:
            print(f"  [FAIL] Big W returned status {response.status_code}")
    except Exception as e:
        print(f"  [FAIL] Big W request failed: {e}")

    print("\n" + "="*60)
    print("CONCLUSION:")
    print("Free proxies can be fetched, but likely won't work with Big W")
    print("Big W's bot detection blocks most free/datacenter proxies")
    print("You'll need residential proxies for reliable monitoring")
    print("="*60)

except ImportError:
    print("[FAIL] free-proxy library not installed")
    print("Install with: pip install free-proxy")
