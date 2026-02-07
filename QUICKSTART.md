# Quick Start Guide

Get the Agent API Proxy running in 5 minutes!

## Step 1: Setup Environment

```bash
cd agent-api-proxy
copy .env.example .env
```

Edit `.env` and add your API credentials:

### Get Reddit API Credentials
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" type
4. Fill in the details:
   - name: AgentAPIProxy
   - redirect uri: http://localhost:8000
5. Copy the client ID and secret
6. Add to `.env`:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_secret
   REDDIT_USERNAME=your_reddit_username
   REDDIT_PASSWORD=your_reddit_password
   ```

### Get SendGrid API Key
1. Sign up at https://sendgrid.com
2. Go to Settings > API Keys
3. Create a new API key with "Full Access"
4. Copy the key (you'll only see it once!)
5. Verify a sender email address in SendGrid
6. Add to `.env`:
   ```
   SENDGRID_API_KEY=your_api_key
   SENDGRID_FROM_EMAIL=verified@yourdomain.com
   ```

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Run the Server

```bash
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## Step 4: Create an API Key

Open a new terminal and run:

```bash
curl -X POST "http://localhost:8000/admin/create-api-key?user_id=test_user"
```

You'll get a response like:
```json
{
  "success": true,
  "user_id": "test_user",
  "api_key": "sk_xxxxxxxxxxxxxxxxx",
  "message": "API key created successfully. Keep it secure!"
}
```

**SAVE THIS API KEY!** You'll need it for all API calls.

## Step 5: Test the API

### View the Landing Page
Open your browser: http://localhost:8000

### View API Documentation
Open your browser: http://localhost:8000/docs

### Test with cURL

Replace `YOUR_API_KEY` with the key from Step 4:

```bash
# Health check (no auth needed)
curl http://localhost:8000/health

# Search Reddit
curl -X GET "http://localhost:8000/api/reddit/search?query=python&limit=3" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Post to Reddit (be careful!)
curl -X POST "http://localhost:8000/api/reddit/post" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Test Post\", \"text\": \"Testing API\", \"subreddit\": \"test\"}"

# Send email (be careful!)
curl -X POST "http://localhost:8000/api/email/send" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"to\": \"test@example.com\", \"subject\": \"Test\", \"body\": \"Hello!\"}"

# Check your usage
curl "http://localhost:8000/admin/usage/test_user?days=30"
```

### Test with Python

```python
import requests

API_KEY = "YOUR_API_KEY"
BASE_URL = "http://localhost:8000"

headers = {"Authorization": f"Bearer {API_KEY}"}

# Search Reddit
response = requests.get(
    f"{BASE_URL}/api/reddit/search",
    headers=headers,
    params={"query": "python", "limit": 5}
)
print(response.json())
```

## Step 6: Check Usage

```bash
curl "http://localhost:8000/admin/usage/test_user?days=7"
```

You'll see:
```json
{
  "user_id": "test_user",
  "period_days": 7,
  "total_requests": 5,
  "successful_requests": 5,
  "failed_requests": 0,
  "total_cost_cents": 25,
  "total_cost_dollars": 0.25,
  "endpoint_breakdown": {
    "/api/reddit/search": {
      "count": 5,
      "cost": 25,
      "success": 5,
      "failed": 0
    }
  }
}
```

## What's Next?

- **Deploy to production** - See `DEPLOYMENT.md`
- **Customize pricing** - Edit `COST_*` in `.env`
- **Add more users** - Create more API keys
- **Monitor usage** - Check the `/admin/usage` endpoint
- **Scale up** - Switch to PostgreSQL, add Redis caching

## Troubleshooting

### Port already in use
```bash
# Use a different port
uvicorn app.main:app --reload --port 8080
```

### Module not found
```bash
# Make sure you're in the right directory
cd agent-api-proxy
pip install -r requirements.txt
```

### Reddit API errors
- Verify your credentials in `.env`
- Make sure your Reddit account has verified email
- Try a different subreddit

### SendGrid errors
- Verify your API key
- Make sure `SENDGRID_FROM_EMAIL` is verified in SendGrid
- Check SendGrid dashboard for error details

### Database errors
```bash
# Delete and recreate the database
del agent_api_proxy.db
# Restart the server - it will recreate automatically
```

## Need Help?

1. Check the full README.md
2. View `/docs` for interactive API documentation
3. Check the example scripts in `examples/`
4. Review the database schema in `DATABASE_SCHEMA.sql`

---

**You're ready to go! 🚀**
