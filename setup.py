"""
Quick setup script for Agent API Proxy
Run this to verify everything is ready to go!
"""
import os
import sys

def check_file(path):
    """Check if file exists"""
    if os.path.exists(path):
        print(f"[OK] {path}")
        return True
    else:
        print(f"[MISSING] {path}")
        return False

def main():
    print("=" * 60)
    print("Agent API Proxy - Setup Check")
    print("=" * 60)
    print()
    
    # Check all required files
    files = [
        "requirements.txt",
        ".env.example",
        "README.md",
        "Dockerfile",
        "docker-compose.yml",
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/database.py",
        "app/auth.py",
        "app/rate_limiter.py",
        "app/routers/__init__.py",
        "app/routers/reddit.py",
        "app/routers/email.py",
        "static/index.html",
        "examples/test_api.py",
        "examples/curl_examples.sh"
    ]
    
    print("Checking files...")
    all_good = all(check_file(f) for f in files)
    print()
    
    # Check if .env exists
    if os.path.exists(".env"):
        print("[OK] .env file found")
    else:
        print("[WARNING] .env file not found")
        print("   Run: copy .env.example .env")
        print("   Then edit .env with your API credentials")
        all_good = False
    
    print()
    print("=" * 60)
    
    if all_good:
        print("[SUCCESS] All files present! Ready to run.")
        print()
        print("Next steps:")
        print("1. Edit .env with your API credentials")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run the server: uvicorn app.main:app --reload")
        print("4. Visit http://localhost:8000/docs")
    else:
        print("[ERROR] Some files are missing. Check the output above.")
        sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main()
