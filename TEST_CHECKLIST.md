# Testing Checklist

Use this checklist to verify everything works before deployment.

## Pre-Flight Checks

- [ ] Python 3.11+ installed
- [ ] pip installed and updated
- [ ] Reddit API credentials obtained
- [ ] SendGrid API key obtained
- [ ] SendGrid sender email verified

## Setup

- [ ] Created `.env` file from `.env.example`
- [ ] Added Reddit credentials to `.env`
- [ ] Added SendGrid credentials to `.env`
- [ ] Installed dependencies: `pip install -r requirements.txt`
- [ ] Setup script passes: `python setup.py`

## Server Startup

- [ ] Server starts without errors: `uvicorn app.main:app --reload`
- [ ] No import errors
- [ ] Database created automatically
- [ ] Landing page loads: http://localhost:8000
- [ ] API docs load: http://localhost:8000/docs

## API Key Management

- [ ] Can create API key: `POST /admin/create-api-key?user_id=test`
- [ ] API key format correct: `sk_xxxxx`
- [ ] API key stored in database
- [ ] Can query API key from database

## Authentication

- [ ] Request without API key returns 401
- [ ] Request with invalid API key returns 401
- [ ] Request with valid API key succeeds
- [ ] Bearer token format works

## Rate Limiting

- [ ] Rate limiter initialized
- [ ] Can make 30 requests in a minute
- [ ] 31st request returns 429
- [ ] Rate limit resets after 1 minute

## Reddit Search Endpoint

- [ ] Returns 401 without auth
- [ ] Accepts valid API key
- [ ] Can search all of Reddit (no subreddit param)
- [ ] Can search specific subreddit
- [ ] Limit parameter works (1-100)
- [ ] Returns correct JSON structure
- [ ] Logs usage in database
- [ ] Charges correct cost (5 cents)
- [ ] Handles errors gracefully
- [ ] Error doesn't charge cost

## Reddit Post Endpoint

⚠️ **Be careful - this creates real posts!**

- [ ] Returns 401 without auth
- [ ] Accepts valid API key
- [ ] Validates title length
- [ ] Validates text length
- [ ] Validates subreddit name
- [ ] Creates post successfully
- [ ] Returns post URL
- [ ] Returns post ID
- [ ] Logs usage in database
- [ ] Charges correct cost (10 cents)
- [ ] Handles errors gracefully
- [ ] Error doesn't charge cost

## Email Send Endpoint

⚠️ **Be careful - this sends real emails!**

- [ ] Returns 401 without auth
- [ ] Accepts valid API key
- [ ] Validates email address format
- [ ] Validates subject length
- [ ] Validates body length
- [ ] Sends email successfully
- [ ] Returns message ID
- [ ] Logs usage in database
- [ ] Charges correct cost (15 cents)
- [ ] Handles errors gracefully
- [ ] Error doesn't charge cost

## Usage Tracking

- [ ] All requests logged in database
- [ ] User ID recorded correctly
- [ ] Endpoint recorded correctly
- [ ] Timestamp recorded
- [ ] Cost recorded correctly
- [ ] Success status recorded
- [ ] Error messages recorded on failure
- [ ] Can query usage by user
- [ ] Can filter by date range
- [ ] Endpoint breakdown correct

## Admin Endpoints

- [ ] Create API key works
- [ ] Returns JSON response
- [ ] Usage endpoint works
- [ ] Returns correct statistics
- [ ] Total cost calculated correctly
- [ ] Endpoint breakdown accurate
- [ ] Date filtering works

## Error Handling

- [ ] Invalid JSON returns 400
- [ ] Missing required fields returns 422
- [ ] Invalid API key returns 401
- [ ] Rate limit exceeded returns 429
- [ ] Server errors return 500
- [ ] Error messages are helpful

## Database

- [ ] Database file created
- [ ] api_keys table exists
- [ ] usage_logs table exists
- [ ] Can insert records
- [ ] Can query records
- [ ] Indexes working
- [ ] No corruption after server restart

## Performance

- [ ] Health check responds quickly
- [ ] Search requests < 2 seconds
- [ ] Post requests < 3 seconds
- [ ] Email requests < 2 seconds
- [ ] Can handle 10 concurrent requests

## Documentation

- [ ] README is accurate
- [ ] QUICKSTART guide works
- [ ] Example Python script works
- [ ] Example cURL script works
- [ ] API docs are complete
- [ ] Landing page displays correctly

## Docker (Optional)

- [ ] Dockerfile builds: `docker build -t agent-api-proxy .`
- [ ] Container runs: `docker run -p 8000:8000 agent-api-proxy`
- [ ] Environment variables work
- [ ] Volume mounting works
- [ ] Docker Compose works

## Production Ready

- [ ] All endpoints tested
- [ ] All error cases handled
- [ ] Documentation complete
- [ ] Examples working
- [ ] Performance acceptable
- [ ] Security measures in place
- [ ] Deployment strategy chosen

## Known Limitations (Expected)

- [ ] Admin endpoints not protected (by design for MVP)
- [ ] No payment integration (manual billing)
- [ ] SQLite not suitable for high traffic (can upgrade to PostgreSQL)
- [ ] No user registration UI (can add later)
- [ ] No API key expiration (can add later)

## Sign Off

- [ ] All critical tests passed
- [ ] Documentation reviewed
- [ ] Ready for deployment
- [ ] Team notified

---

**Tested by:** _______________  
**Date:** _______________  
**Status:** ☐ PASS ☐ FAIL  
**Notes:** _______________
