# Facebook Webhook Setup Guide

## What We Just Built

✅ **Webhook endpoints** for real-time message delivery (no more polling!)
✅ **Send API** to reply to messages programmatically  
✅ **Post API** to publish to page timeline (for daily numerology content)

## Setup Steps

### 1. Configure Webhook in Facebook Developer Console

Go to your app settings: https://developers.facebook.com/apps/2188707741897079/messenger/settings/

**Webhooks Section:**

1. Click **"Add Callback URL"** (or edit existing)
2. **Callback URL:** `https://agent-api-proxy-production.up.railway.app/api/facebook/webhook`
3. **Verify Token:** `smith_webhook_verify_2026` (this is already in the .env file)
4. Click **"Verify and Save"**

### 2. Subscribe to Webhook Events

After the URL is verified, you need to subscribe to specific events:

**Required subscriptions:**
- ✅ `messages` - Get incoming messages
- ✅ `messaging_postbacks` - Get button clicks (for future)
- ✅ `message_reads` - Track read receipts (optional)

Click **"Subscribe"** for each event you want.

### 3. Test the Webhook

Send a test message to your Facebook page. Check Railway logs to see:
```
📨 Facebook message from <sender_id>: <message_text>
```

This confirms webhooks are working!

### 4. Wire Up to OpenClaw (Next Step)

Currently the webhook logs messages but doesn't forward them yet. Next steps:

**Option A: Direct integration** - Forward webhook payloads to OpenClaw gateway
**Option B: Proxy pattern** - Webhook writes to database, OpenClaw polls new messages

We'll decide based on how OpenClaw's inbound messaging works best.

## API Endpoints Available

### Webhook (Facebook calls this)
- `GET /api/facebook/webhook` - Verification endpoint
- `POST /api/facebook/webhook` - Receives messages/events

### Send Message
```bash
POST /api/facebook/send
{
  "recipient_id": "facebook_user_id",
  "message": "Your reply text"
}
```

### Post to Page Timeline
```bash
POST /api/facebook/post
{
  "message": "Daily numerology content here"
}
```

## Daily Numerology Automation

Once webhook is confirmed working, we can set up:
1. **Cron job** in OpenClaw to trigger daily posts
2. **Python script** to generate gematria content
3. **API call** to `/api/facebook/post` endpoint

Format ideas:
- Today's date breakdown (primes, Fibonacci positions)
- Historical event on this date with gematria connections
- Number of the day analysis
- Visual formatting for mobile

## Security Notes

- ⚠️ App Secret is not set (signature verification disabled for now)
- Get App Secret from Facebook Developer Console → Settings → Basic
- Add to `.env` as `FACEBOOK_APP_SECRET=<your_secret>`
- This enables cryptographic verification of incoming webhooks

## Troubleshooting

**Webhook verification fails:**
- Check callback URL is correct
- Verify token must match exactly: `smith_webhook_verify_2026`
- Railway deployment must be complete before testing

**Messages not arriving:**
- Check you subscribed to `messages` event
- Verify webhook is active (green dot in Facebook settings)
- Check Railway logs for errors

**Can't send messages:**
- Page token might be expired (Facebook tokens expire)
- Check `FACEBOOK_PAGE_TOKEN` in `.env` is current
- Regenerate from Facebook → Messenger → Settings → Access Tokens

---

**Status:** Webhook deployed, waiting for Facebook configuration ✨
