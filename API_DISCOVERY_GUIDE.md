# How to Find Retailer Internal APIs

This guide will help you discover the internal APIs that modern retailers use to load product data, so you can monitor them directly without browser automation.

## Step-by-Step: Finding Kmart's API

### 1. Open Browser Developer Tools

1. Open Google Chrome or Firefox
2. Navigate to the Kmart Pokemon cards page: `https://www.kmart.com.au/category/toys/pokemon-trading-cards/`
3. Press **F12** to open Developer Tools (or right-click > Inspect)
4. Click on the **Network** tab

### 2. Clear and Filter Network Requests

1. Click the **Clear** button (🚫) to clear existing requests
2. In the filter box, type: `json` or `api` or `fetch`
3. Alternatively, click the **XHR** filter button to show only AJAX requests

### 3. Reload the Page

1. Press **F5** or **Ctrl+R** to reload the page
2. Watch the Network tab fill with requests
3. Look for requests that:
   - Return JSON data (Content-Type: application/json)
   - Have "product" or "search" or "category" in the URL
   - Return a lot of data (large Size column)

### 4. Identify the Product API

Look for patterns like:
```
/api/products
/api/search
/api/categories
/graphql
/rest/v1/
```

**Example for Commercetools (Kmart's platform):**
```
https://api.commercetools.com/...
https://api.europe-west1.gcp.commercetools.com/...
```

### 5. Inspect the Request

1. Click on a promising request
2. Look at the **Headers** tab:
   - Request URL (this is the API endpoint!)
   - Request Method (GET, POST, etc.)
   - Query String Parameters
3. Look at the **Response** tab:
   - Should show JSON with product data
4. Look at the **Preview** tab:
   - Formatted view of the JSON

### 6. Test the API Endpoint

Once you find an API endpoint:

#### Option A: Test in Browser
1. Copy the Request URL
2. Paste it in a new browser tab
3. See if it returns JSON data

#### Option B: Test with curl
```bash
curl "https://api-endpoint-here.com/products" -H "Accept: application/json"
```

#### Option C: Test with Python
```python
import requests

url = "https://api-endpoint-here.com/products"
headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers)
print(response.json())
```

## Common API Patterns

### Pattern 1: REST API with Query Parameters
```
https://www.retailer.com/api/products?category=pokemon&page=1&limit=50
```

### Pattern 2: GraphQL
```
POST https://www.retailer.com/graphql
Body: {"query": "{ products(category: \"pokemon\") { id name price } }"}
```

### Pattern 3: Search API
```
https://www.retailer.com/api/search?q=pokemon+cards&page=1
```

### Pattern 4: Category API
```
https://www.retailer.com/api/categories/pokemon-cards/products
```

## What to Look For in the API Response

Good API responses will have:

```json
{
  "products": [
    {
      "id": "12345",
      "name": "Pokemon Booster Pack",
      "price": 9.99,
      "currency": "AUD",
      "image": "https://cdn.retailer.com/image.jpg",
      "url": "/product/pokemon-booster-pack/12345",
      "availability": true,
      "stock": 5
    }
  ],
  "pagination": {
    "page": 1,
    "total": 100
  }
}
```

## Specific Steps for Kmart

### Expected API Patterns for Kmart (Commercetools)

Kmart uses Commercetools, which typically has APIs like:

```
https://api.commercetools.com/{project-key}/product-projections/search
https://api.australia.commercetools.com/kmart-au/products
```

### How to Find It:

1. Go to: `https://www.kmart.com.au/category/toys/pokemon-trading-cards/`
2. Open DevTools > Network tab
3. Filter by **Fetch/XHR**
4. Scroll down the page (to trigger lazy loading)
5. Look for requests containing:
   - `commercetools`
   - `product`
   - `category`
   - Large JSON responses

### Parameters to Look For:

- **category ID** or **category key**
- **page** or **offset**
- **limit** or **pageSize**
- **sort** order
- **filter** parameters

## Authentication & Headers

Some APIs require authentication. Check these headers:

### Required Headers:
```python
headers = {
    "User-Agent": "Mozilla/5.0...",
    "Accept": "application/json",
    "Accept-Language": "en-AU",
    "Referer": "https://www.kmart.com.au/",
}
```

### Possible Auth Headers:
```python
# If you see these in the Network tab, copy them:
"Authorization": "Bearer ey...",
"X-API-Key": "abc123...",
"X-Client-ID": "kmart-web",
```

## Example: Complete API Discovery for Kmart

Here's what you should do right now:

### Step 1: Manual Discovery
```bash
# Open this in Chrome:
https://www.kmart.com.au/category/toys/pokemon-trading-cards/

# Then:
# 1. F12 > Network > Fetch/XHR
# 2. Reload page
# 3. Look for API calls
# 4. Copy the Request URL
```

### Step 2: Test the API
Once you find the URL, test it:

```python
import requests
import json

# Replace with the URL you found:
url = "YOUR_API_URL_HERE"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-AU,en;q=0.9",
    "Referer": "https://www.kmart.com.au/"
}

response = requests.get(url, headers=headers)

# Print the JSON to see the structure
print(json.dumps(response.json(), indent=2))
```

### Step 3: Extract Product Data
Once you understand the JSON structure, extract products:

```python
data = response.json()

# The structure will vary, but look for:
products = data.get('results') or data.get('products') or data.get('data')

for product in products:
    print(f"Name: {product.get('name')}")
    print(f"Price: {product.get('price')}")
    print(f"URL: {product.get('url')}")
    print("---")
```

## Tips & Tricks

### 1. Pagination
APIs usually return limited results. Look for:
- `page` parameter in URL
- `offset` and `limit` parameters
- `next` URL in response

### 2. Rate Limiting
Be respectful:
- Add delays between requests (5-10 seconds)
- Don't make more than 1 request per second
- Rotate user agents

### 3. Data Changes
APIs can change. Monitor for:
- Status code 404 or 403
- Changed response structure
- New authentication requirements

### 4. Legal Considerations
- Check `robots.txt`: `https://www.kmart.com.au/robots.txt`
- Read Terms of Service
- Don't abuse the API
- Use reasonable request rates

## Common Issues

### Issue: CORS Error
**Solution:** This happens in browser. Use Python/backend instead.

### Issue: 403 Forbidden
**Solution:** Add proper User-Agent and Referer headers

### Issue: Empty Response
**Solution:** You might need to authenticate or use session cookies

### Issue: Encrypted/Obfuscated Data
**Solution:** Look for a different endpoint, or use browser automation

## Next Steps After Finding API

Once you find the API endpoint:

1. **Document it:**
   ```python
   # Kmart Pokemon Cards API
   # URL: https://api.example.com/products
   # Method: GET
   # Params: category=pokemon, page=1
   ```

2. **Update the monitor:**
   ```python
   def scrape_site(url, headers, proxy):
       api_url = "https://api.kmart.com.au/products"
       params = {"category": "pokemon", "page": 1}
       response = requests.get(api_url, params=params, headers=headers)
       return parse_api_response(response.json())
   ```

3. **Test thoroughly:**
   - Multiple pages
   - Different categories
   - Edge cases (no results, errors)

## Need Help?

If you're stuck finding the API:

1. Share a screenshot of the Network tab
2. Look for any request that returns a large JSON response
3. Try filtering by file size (look for largest requests)
4. Check the Response tab for product-like data

## Alternative: Use Browser Automation

If you can't find a stable API, use Selenium:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://www.kmart.com.au/category/toys/pokemon-trading-cards/")

# Wait for products to load
products = driver.find_elements(By.CLASS_NAME, "product-card")

for product in products:
    title = product.find_element(By.CLASS_NAME, "title").text
    price = product.find_element(By.CLASS_NAME, "price").text
    print(f"{title}: {price}")
```

---

**Pro Tip:** The best time to look for APIs is when the page first loads. That initial burst of requests often includes the main product data API!
