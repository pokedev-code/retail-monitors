# State-Specific Webhooks Configuration Guide

## Overview

The Kmart monitor now supports sending notifications to different Discord channels based on the Australian state. This allows you to organize stock notifications by region (e.g., `#kmart-nsw`, `#kmart-vic`, `#kmart-qld`).

## How It Works

When the monitor detects stock for a product in a specific state, it will:
1. Check if a webhook is configured for that state in `STATE_WEBHOOKS`
2. If configured, send the notification to that state's Discord channel
3. If not configured, send to the fallback `WEBHOOK`

## Setup Instructions

### Step 1: Create Discord Channels

Create separate text channels in your Discord server for each state you want to monitor:
- `#kmart-nsw` (New South Wales)
- `#kmart-vic` (Victoria)
- `#kmart-qld` (Queensland)
- `#kmart-sa` (South Australia)
- `#kmart-wa` (Western Australia)
- `#kmart-tas` (Tasmania)
- `#kmart-nt` (Northern Territory)
- `#kmart-act` (Australian Capital Territory)

### Step 2: Create Webhooks for Each Channel

For each Discord channel:

1. Right-click on the channel name
2. Select **Edit Channel** → **Integrations** → **Webhooks**
3. Click **New Webhook**
4. Name it (e.g., "Kmart NSW Monitor")
5. Copy the **Webhook URL**
6. Repeat for all state channels

### Step 3: Update config.py

Open `monitors/kmart/config.py` and update the `STATE_WEBHOOKS` dictionary with your webhook URLs:

```python
STATE_WEBHOOKS = {
    'NSW': "https://discord.com/api/webhooks/1234567890/your-nsw-webhook-token",
    'VIC': "https://discord.com/api/webhooks/1234567890/your-vic-webhook-token",
    'QLD': "https://discord.com/api/webhooks/1234567890/your-qld-webhook-token",
    'SA': "https://discord.com/api/webhooks/1234567890/your-sa-webhook-token",
    'WA': "https://discord.com/api/webhooks/1234567890/your-wa-webhook-token",
    'TAS': "https://discord.com/api/webhooks/1234567890/your-tas-webhook-token",
    'NT': "https://discord.com/api/webhooks/1234567890/your-nt-webhook-token",
    'ACT': "https://discord.com/api/webhooks/1234567890/your-act-webhook-token",
}
```

### Step 4: Test Configuration

Run the test script to verify webhooks are configured correctly:

```bash
python test_state_webhooks.py
```

This will:
- Show which states have webhooks configured
- Send test notifications to 2 states (to avoid spam)
- Verify the notifications appear in the correct Discord channels

## Configuration Options

### Option 1: Monitor All States (Separate Channels)

Configure all 8 state webhooks - each state gets its own channel:

```python
STATE_WEBHOOKS = {
    'NSW': "webhook-url-1",
    'VIC': "webhook-url-2",
    'QLD': "webhook-url-3",
    # ... etc
}
```

### Option 2: Monitor Specific States Only

Only configure webhooks for states you care about. Others will use the fallback webhook:

```python
STATE_WEBHOOKS = {
    'NSW': "webhook-url-1",
    'VIC': "webhook-url-2",
    'QLD': None,  # Will use fallback
    'SA': None,   # Will use fallback
    # ... etc
}
```

### Option 3: Single Channel (Original Behavior)

Leave all STATE_WEBHOOKS as placeholder URLs or None. All notifications will use the fallback `WEBHOOK`:

```python
STATE_WEBHOOKS = {
    'NSW': None,
    'VIC': None,
    # ... etc
}

WEBHOOK = "your-single-webhook-url"  # All notifications go here
```

## How Notifications Work

### When Monitor Runs:

1. **Scrapes category page** for products matching KEYWORDS
2. **Fetches stock data** for all 8 Australian states for each product
3. **Compares stock levels** against previous scrape
4. **Sends notifications** when stock increases:
   - NSW stock increased → Notification to `#kmart-nsw`
   - VIC stock increased → Notification to `#kmart-vic`
   - QLD stock increased → Notification to `#kmart-qld`
   - etc.

### Notification Format:

Each notification includes:
- **Title**: Product name (clickable link)
- **Thumbnail**: Product image
- **State**: The specific Australian state (NSW, VIC, etc.)
- **Stock Change**: Online and In-Store quantities
- **Store**: Kmart
- **eBay Links**: Current/Sold listings (if enabled)
- **Footer**: "Kmart Stock Monitor"

## Example Scenario

**Product**: Pokemon TCG Booster Pack
**Stock Change**: NSW online stock goes from 0 → 25

**Result**:
- Notification sent to `#kmart-nsw` channel only
- Shows: "State: NSW, Online: 25, In-Store: 0"
- Other state channels don't get notified (their stock didn't change)

## Troubleshooting

### Problem: All notifications go to fallback webhook

**Solution**:
- Check that STATE_WEBHOOKS URLs are valid Discord webhook URLs
- Verify they start with `https://discord.com/api/webhooks/`
- Ensure no typos in state codes (must be uppercase: NSW, VIC, etc.)

### Problem: No notifications received

**Solution**:
- Check Discord channel webhook permissions
- Verify webhook URLs are not expired
- Check `kmart-monitor.log` for errors
- Run `test_state_webhooks.py` to test configuration

### Problem: Want to skip notifications for certain states

**Solution**:
- Set that state's webhook to `None` or empty string `""`
- Notifications for that state will use fallback webhook

## Benefits of State-Specific Channels

1. **Better Organization**: Each state has its own channel
2. **Targeted Notifications**: Users can subscribe to their state only
3. **Less Noise**: Don't get notified about interstate stock
4. **Easier Tracking**: See regional availability patterns
5. **Custom Roles**: Assign Discord roles per state channel

## Running the Monitor

Once configured, run the monitor normally:

```bash
python monitor_enhanced.py
```

The monitor will automatically use state-specific webhooks when sending notifications.
