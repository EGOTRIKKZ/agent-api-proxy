# 🤖 Agent API Proxy

A minimal MVP API proxy service that allows AI agents to access external APIs (Reddit, Email) with authentication, usage tracking, and rate limiting.

## Features

- ✅ **FastAPI Backend** - Fast, modern Python web framework
- ✅ **Reddit Integration** - Post and search Reddit
- ✅ **Email Integration** - Send emails via SendGrid
- ✅ **API Key Authentication** - Simple Bearer token auth
- ✅ **Usage Tracking** - SQLite database with cost tracking
- ✅ **Rate Limiting** - 30 requests/minute per API key
- ✅ **Admin Endpoints** - Create keys and view usage
- ✅ **Docker Support** - Easy deployment with Docker
- ✅ **Landing Page** - Simple UI explaining the service

## Quick Start

### 1. Install Dependencies

```bash
cd agent-api-proxy
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and fill in your API credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

- **Reddit API**: Get credentials at https://www.reddit.com/prefs/apps
- **SendGrid API**: Get API key at https://app.sendgrid.com/settings/api_keys

### 3. Run the Server

```bash
uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`

### 4. Create an API Key

```bash
curl -X POST "http://localhost:8000/admin/create-api-key?user_id=test_user"
```

Save the returned API key - you'll need it for authentication!

### 5. Test the API

Visit the interactive API docs at `http://localhost:8000/docs`

Or use cURL:

```bash
# Search Reddit
curl -X GET "http://localhost:8000/api/reddit/search?query=python&limit=5" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Post to Reddit (be careful!)
curl -X POST "http://localhost:8000/api/reddit/post" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Post",
    "text": "This is a test",
    "subreddit": "test"
  }'

# Send Email (be careful!)
curl -X POST "http://localhost:8000/api/email/send" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "subject": "Test Email",
    "body": "Hello from Agent API Proxy!"
  }'
```

## API Endpoints

### Public Endpoints

- `GET /` - Landing page
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### Reddit Endpoints

- `GET /api/reddit/search` - Search Reddit posts
  - Query params: `query`, `subreddit` (optional), `limit` (default: 10)
  - Cost: $0.05 per search

- `POST /api/reddit/post` - Create a Reddit post
  - Body: `title`, `text`, `subreddit`
  - Cost: $0.10 per post

### Email Endpoints

- `POST /api/email/send` - Send an email via SendGrid
  - Body: `to`, `subject`, `body`
  - Cost: $0.15 per email

### Admin Endpoints

⚠️ **Warning**: These endpoints should be protected in production!

- `POST /admin/create-api-key?user_id={user_id}` - Create a new API key
- `GET /admin/usage/{user_id}?days={days}` - Get usage statistics

## Authentication

All API endpoints (except admin and public endpoints) require authentication via Bearer token:

```bash
Authorization: Bearer YOUR_API_KEY
```

## Usage Tracking

All API calls are logged in the SQLite database with:
- User ID
- Endpoint called
- Timestamp
- Cost (in cents)
- Success/failure status
- Error message (if failed)

View usage statistics:

```bash
curl "http://localhost:8000/admin/usage/test_user?days=30"
```

## Rate Limiting

Default: 30 requests per minute per API key

Rate limits are enforced per API key. If exceeded, you'll receive a 429 error.

## Database Schema

### `api_keys` Table

```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);
```

### `usage_logs` Table

```sql
CREATE TABLE usage_logs (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cost INTEGER NOT NULL,
    success INTEGER DEFAULT 1,
    error_message TEXT
);
```

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t agent-api-proxy .

# Run the container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --name agent-api-proxy \
  agent-api-proxy
```

### Using Docker Compose

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Project Structure

```
agent-api-proxy/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app and main endpoints
│   ├── config.py            # Configuration management
│   ├── database.py          # Database models and functions
│   ├── auth.py              # Authentication logic
│   ├── rate_limiter.py      # Rate limiting setup
│   └── routers/
│       ├── __init__.py
│       ├── reddit.py        # Reddit endpoints
│       └── email.py         # Email endpoints
├── static/
│   └── index.html           # Landing page
├── examples/
│   ├── test_api.py          # Python test script
│   └── curl_examples.sh     # cURL examples
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment variables
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # This file
```

## Configuration

All configuration is done via environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite:///./agent_api_proxy.db` |
| `REDDIT_CLIENT_ID` | Reddit API client ID | (required) |
| `REDDIT_CLIENT_SECRET` | Reddit API secret | (required) |
| `REDDIT_USERNAME` | Reddit account username | (required) |
| `REDDIT_PASSWORD` | Reddit account password | (required) |
| `SENDGRID_API_KEY` | SendGrid API key | (required) |
| `SENDGRID_FROM_EMAIL` | Sender email address | (required) |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per API key | 30 |
| `COST_REDDIT_POST` | Cost per Reddit post (cents) | 10 |
| `COST_REDDIT_SEARCH` | Cost per Reddit search (cents) | 5 |
| `COST_EMAIL_SEND` | Cost per email (cents) | 15 |

## Development

### Run in Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
# Using Python
python examples/test_api.py

# Using bash
bash examples/curl_examples.sh
```

## Security Considerations

⚠️ **This is an MVP - NOT production-ready!**

Before deploying to production, you should:

1. **Protect admin endpoints** - Add proper authentication
2. **Use HTTPS** - Never send API keys over HTTP
3. **Implement proper user management** - Registration, login, etc.
4. **Add payment integration** - Stripe, PayPal, etc.
5. **Set up monitoring** - Track errors, performance
6. **Add logging** - Proper logging with rotation
7. **Rate limiting by user tier** - Different limits for different plans
8. **Input validation** - More robust validation
9. **Error handling** - Better error messages
10. **Database migrations** - Use Alembic for schema changes

## Troubleshooting

### Database Issues

If you encounter database errors, delete the database and restart:

```bash
rm agent_api_proxy.db
uvicorn app.main:app --reload
```

### Reddit API Errors

- Verify your Reddit credentials in `.env`
- Make sure your Reddit account has verified email
- Check Reddit API rate limits

### SendGrid Errors

- Verify your SendGrid API key
- Check that `SENDGRID_FROM_EMAIL` is verified in SendGrid
- Check SendGrid API rate limits

## Pricing

Current pricing (configurable in `.env`):

- Reddit Post: $0.10
- Reddit Search: $0.05
- Email Send: $0.15

**Note**: Costs are tracked but not collected. Manual billing only in this MVP.

## License

MIT License - feel free to use and modify as needed.

## Support

For issues or questions:
1. Check the interactive docs at `/docs`
2. Review the example scripts in `examples/`
3. Check the troubleshooting section above

## Roadmap

Future enhancements:
- [ ] More API integrations (Twitter, Discord, etc.)
- [ ] Payment integration (Stripe)
- [ ] User dashboard
- [ ] Webhook support
- [ ] API key permissions/scopes
- [ ] Usage alerts
- [ ] Better admin interface

---

**Built with ❤️ for AI agents**
