"""
Example Python script to test the Agent API Proxy
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your_api_key_here"  # Replace with your actual API key

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def test_reddit_search():
    """Test Reddit search endpoint"""
    print("\n=== Testing Reddit Search ===")
    
    params = {
        "query": "python programming",
        "subreddit": "learnpython",
        "limit": 5
    }
    
    response = requests.get(
        f"{BASE_URL}/api/reddit/search",
        headers=headers,
        params=params
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_reddit_post():
    """Test Reddit post endpoint"""
    print("\n=== Testing Reddit Post ===")
    
    data = {
        "title": "Test post from Agent API Proxy",
        "text": "This is a test post created via the API proxy service.",
        "subreddit": "test"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/reddit/post",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_email_send():
    """Test email send endpoint"""
    print("\n=== Testing Email Send ===")
    
    data = {
        "to": "test@example.com",
        "subject": "Test Email from Agent API Proxy",
        "body": "This is a test email sent via the API proxy service.\n\nBest regards,\nAgent API Proxy"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/email/send",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def check_usage():
    """Check usage statistics"""
    print("\n=== Checking Usage Statistics ===")
    
    # Extract user_id from your API key or use known user_id
    user_id = "test_user"  # Replace with your actual user_id
    
    response = requests.get(
        f"{BASE_URL}/admin/usage/{user_id}",
        params={"days": 7}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def health_check():
    """Test health endpoint"""
    print("\n=== Health Check ===")
    
    response = requests.get(f"{BASE_URL}/health")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


if __name__ == "__main__":
    print("Agent API Proxy - Test Suite")
    print("=" * 50)
    
    # Run tests
    health_check()
    
    # Uncomment the tests you want to run:
    # test_reddit_search()
    # test_reddit_post()  # Be careful with this - it will create a real post!
    # test_email_send()   # Be careful with this - it will send a real email!
    # check_usage()
    
    print("\n" + "=" * 50)
    print("Tests complete!")
