# Deployment Guide

## Quick Deploy (Local Testing)

1. **Setup**
   ```bash
   cd agent-api-proxy
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Run**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Test**
   - Visit: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Create API key: `curl -X POST "http://localhost:8000/admin/create-api-key?user_id=test"`

## Docker Deployment

### Option 1: Docker Run

```bash
# Build
docker build -t agent-api-proxy .

# Run
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --name agent-api-proxy \
  agent-api-proxy

# View logs
docker logs -f agent-api-proxy
```

### Option 2: Docker Compose

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Cloud Deployment

### Heroku

1. Create a `Procfile`:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   heroku config:set REDDIT_CLIENT_ID=your_id
   heroku config:set REDDIT_CLIENT_SECRET=your_secret
   # ... set other env vars
   git push heroku main
   ```

### DigitalOcean App Platform

1. Fork the repo or push to GitHub
2. Create new app in DigitalOcean
3. Connect your repo
4. Set environment variables in the dashboard
5. Deploy!

### AWS EC2

1. Launch Ubuntu instance
2. SSH and install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3-pip
   git clone your-repo
   cd agent-api-proxy
   pip3 install -r requirements.txt
   ```

3. Set up systemd service:
   ```bash
   sudo nano /etc/systemd/system/agent-api-proxy.service
   ```
   
   ```ini
   [Unit]
   Description=Agent API Proxy
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/agent-api-proxy
   Environment="PATH=/home/ubuntu/.local/bin"
   ExecStart=/home/ubuntu/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. Start service:
   ```bash
   sudo systemctl enable agent-api-proxy
   sudo systemctl start agent-api-proxy
   ```

### Render

1. Create new Web Service
2. Connect your repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables
6. Deploy!

## Production Checklist

Before going live:

- [ ] Set up HTTPS (Let's Encrypt, Cloudflare, etc.)
- [ ] Protect admin endpoints with authentication
- [ ] Set up monitoring (Sentry, LogRocket, etc.)
- [ ] Configure proper logging
- [ ] Set up database backups
- [ ] Add rate limiting by IP in addition to API key
- [ ] Set up firewall rules
- [ ] Review security settings
- [ ] Set up CI/CD pipeline
- [ ] Load test the API

## Environment Variables

Make sure these are set in production:

```bash
DATABASE_URL=sqlite:///./agent_api_proxy.db
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
SENDGRID_API_KEY=your_key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
RATE_LIMIT_PER_MINUTE=30
```

## Monitoring

### Health Check Endpoint

Monitor: `GET /health`

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### Usage Tracking

Check usage via: `GET /admin/usage/{user_id}?days=30`

### Database Size

Monitor SQLite database size:
```bash
ls -lh agent_api_proxy.db
```

Consider archiving old logs periodically.

## Scaling

For high traffic:

1. **Use PostgreSQL** instead of SQLite
   - Update `DATABASE_URL` in .env
   - Install psycopg2: `pip install psycopg2-binary`

2. **Use Redis** for rate limiting
   - Install Redis
   - Update rate_limiter.py to use Redis backend

3. **Load Balancer**
   - Deploy multiple instances
   - Use nginx or cloud load balancer

4. **Caching**
   - Add Redis caching for frequent queries
   - Cache Reddit search results

## Troubleshooting

### Database locked errors
- Switch to PostgreSQL for concurrent access
- Or use WAL mode for SQLite:
  ```python
  engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30})
  ```

### High memory usage
- Limit response sizes
- Add pagination to search results
- Monitor with `htop` or similar

### Slow responses
- Add caching layer
- Optimize database queries
- Use async Reddit client

## Backup Strategy

```bash
# Backup database
cp agent_api_proxy.db backups/agent_api_proxy_$(date +%Y%m%d).db

# Automated daily backup (cron)
0 2 * * * cp /path/to/agent_api_proxy.db /path/to/backups/agent_api_proxy_$(date +\%Y\%m\%d).db
```

## Security Hardening

1. **API Key Security**
   - Store hashed keys in database
   - Use secure random generation
   - Implement key rotation

2. **Rate Limiting**
   - Multiple tiers (IP, API key, endpoint)
   - Adaptive rate limiting
   - CAPTCHA for suspicious activity

3. **Input Validation**
   - Sanitize all inputs
   - Validate email addresses
   - Check subreddit names

4. **Monitoring**
   - Log all admin actions
   - Alert on suspicious patterns
   - Track failed authentication attempts
