# Target AU Monitor - Anti-Detection Implementation

## Overview

Target Australia employs strong bot detection measures that require advanced evasion techniques. This document explains the implemented solutions.

## The Challenge

Target AU blocks:
- ❌ Headless browsers
- ❌ Default Playwright fingerprints
- ❌ Automation detection via `navigator.webdriver`
- ❌ Missing browser features (plugins, WebGL, etc.)
- ❌ HTTP/2 connections from automation tools

## Implemented Solutions

### 1. **Non-Headless Mode (Required)**

```python
headless=False  # MUST be False for Target AU
```

Target AU's bot detection **cannot be bypassed in headless mode**. The monitor runs with a visible browser window that can be minimized but must remain open.

### 2. **Advanced Browser Arguments**

```python
args=[
    '--no-sandbox',
    '--disable-http2',                    # Avoid HTTP/2 protocol errors
    '--enable-webgl',                     # Enable WebGL fingerprinting
    '--use-gl=swiftshader',               # Software GL rendering
    '--enable-accelerated-2d-canvas',     # Canvas fingerprinting
    '--disable-blink-features=AutomationControlled',
    '--disable-features=IsolateOrigins,site-per-process',
    '--window-size=1920,1080',
]
```

### 3. **Comprehensive Browser Context**

**Geolocation**: Sydney, Australia coordinates
```python
geolocation={'longitude': 151.2093, 'latitude': -33.8688}
```

**Device Characteristics**:
- Desktop user agent (Chrome 131 on Windows 10)
- 1920x1080 viewport
- Australian locale (en-AU)
- Australia/Sydney timezone
- Device scale factor: 1
- No touch/mobile emulation

**Headers**: Complete set of modern browser headers including:
- Sec-Fetch-* headers
- sec-ch-ua client hints
- Proper Accept headers with avif/webp support

### 4. **Playwright Stealth Plugin**

Uses `playwright-stealth` to patch common detection vectors:
- navigator.webdriver
- Chrome runtime
- Plugin detection
- WebGL vendor/renderer
- Navigator properties

### 5. **Custom JavaScript Injections**

```javascript
// Override navigator.webdriver
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// Add Chrome object
window.chrome = { runtime: {} };

// Add realistic plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [/* Chrome PDF Plugin */]
});

// Set proper languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-AU', 'en-US', 'en']
});
```

### 6. **Human-Like Behavior**

- `slow_mo=50`: 50ms delay between actions
- `wait_until='load'`: Don't wait for complete network idle
- 3-second delays after page load for JS rendering
- Random user behavior simulation via stealth plugin

## Results

✅ **Successfully bypasses Target AU bot detection**
✅ **Can scrape product listings**
✅ **Can extract product details (price, images, availability)**
✅ **Stable for continuous monitoring**

⚠️ **Requires visible browser window** - cannot run truly headless

## Performance Impact

- **Startup**: ~3-5 seconds (browser launch)
- **Per-page load**: ~5-8 seconds (with waits)
- **Memory**: ~200-300MB (Chrome instance)
- **CPU**: Minimal when idle, moderate during scraping

## Limitations

### What We CANNOT Do:

1. **True Headless Operation**: Must run with visible window
2. **Stock Quantities**: Target doesn't expose exact stock numbers
3. **Per-State Tracking**: No API for state-specific stock like Kmart
4. **Fast Scraping**: Must maintain realistic delays to avoid detection

### What We CAN Do:

1. **Availability Tracking**: In Stock / Out of Stock status
2. **Price Monitoring**: Track price changes
3. **Product Detection**: Find new products and restocks
4. **Image Scraping**: Extract product images
5. **Continuous Monitoring**: Run 24/7 with proper delays

## Comparison: Kmart vs Target

| Feature | Kmart | Target AU |
|---------|-------|-----------|
| **Headless Mode** | ✅ Yes | ❌ No (blocked) |
| **API Access** | ✅ GraphQL API | ❌ No public API |
| **Stock Quantities** | ✅ Exact numbers | ❌ Only status |
| **Per-State Stock** | ✅ Yes (8 states) | ❌ No |
| **Bot Detection** | 🟡 Moderate | 🔴 Strong |
| **Scraping Speed** | ⚡ Fast (API) | 🐢 Slow (rendering) |

## Recommendations

### For Production Use:

1. **Run on Dedicated Machine**: Keep browser window open on a server/VM
2. **Use VNC/RDP**: Access the machine remotely to see the browser
3. **Monitor Memory**: Chrome instances can leak memory over time
4. **Implement Restarts**: Restart monitor every 24 hours to clear state
5. **Increase Delays**: If getting blocked, increase `DELAY` in config
6. **Consider Proxies**: Rotate residential proxies if needed

### Alternative Approaches:

If the non-headless requirement is unacceptable:

1. **Use Residential Proxies**: May allow headless mode
2. **Try Different Times**: Detection may be weaker during off-peak hours
3. **Accept Limitations**: Only check occasionally instead of continuous monitoring
4. **Contact Target**: Request official API access (unlikely for competitors)

## Maintenance

As Target's bot detection evolves, you may need to:

- Update browser version (Playwright auto-updates)
- Adjust fingerprint parameters
- Add new evasion techniques
- Monitor success/failure rates

## Conclusion

The current implementation successfully bypasses Target AU's bot detection using a **comprehensive multi-layered approach**. The main trade-off is requiring a visible browser window, which is necessary given Target's aggressive detection of headless automation.

For comparison, the Kmart monitor has much easier access since Kmart provides a GraphQL API and has weaker bot detection measures.
