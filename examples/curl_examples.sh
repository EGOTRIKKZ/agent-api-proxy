#!/bin/bash

# Agent API Proxy - cURL Examples
# Replace YOUR_API_KEY with your actual API key

API_KEY="your_api_key_here"
BASE_URL="http://localhost:8000"

echo "=== Agent API Proxy - cURL Examples ==="
echo ""

# Health Check
echo "1. Health Check"
curl -X GET "$BASE_URL/health"
echo -e "\n"

# Create API Key (Admin)
echo "2. Create API Key"
curl -X POST "$BASE_URL/admin/create-api-key?user_id=test_user"
echo -e "\n"

# Reddit Search
echo "3. Reddit Search"
curl -X GET "$BASE_URL/api/reddit/search?query=python&subreddit=learnpython&limit=5" \
  -H "Authorization: Bearer $API_KEY"
echo -e "\n"

# Reddit Post
echo "4. Reddit Post (commented out - uncomment to test)"
# curl -X POST "$BASE_URL/api/reddit/post" \
#   -H "Authorization: Bearer $API_KEY" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "title": "Test Post from Agent API Proxy",
#     "text": "This is a test post.",
#     "subreddit": "test"
#   }'
echo -e "\n"

# Send Email
echo "5. Send Email (commented out - uncomment to test)"
# curl -X POST "$BASE_URL/api/email/send" \
#   -H "Authorization: Bearer $API_KEY" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "to": "test@example.com",
#     "subject": "Test Email",
#     "body": "This is a test email from Agent API Proxy."
#   }'
echo -e "\n"

# Check Usage
echo "6. Check Usage Statistics"
curl -X GET "$BASE_URL/admin/usage/test_user?days=30"
echo -e "\n"

echo "=== Examples Complete ==="
