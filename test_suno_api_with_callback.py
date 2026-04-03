import urllib.request
import urllib.error
import json
import os

SUNO_API_KEY = os.environ.get("SUNO_API_KEY", "e051ee77fc78bcfa4f95e2105ad80dc6")
SUNO_API_BASE = os.environ.get("SUNO_API_BASE", "https://api.sunoapi.org").rstrip("/")

def test_generate_with_callback():
    print(f"Testing Suno API with callBackUrl...")
    
    payload = {
        "prompt": "Test prompt",
        "title": "Test Title",
        "tags": "pop",
        "model": "V3_5",
        "instrumental": False,
        "customMode": True,
        "callBackUrl": "http://example.com/callback"
    }
    
    url = f"{SUNO_API_BASE}/api/v1/generate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SUNO_API_KEY}",
        "X-API-KEY": SUNO_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            body = res.read().decode('utf-8')
            print(f"Status: {res.status}")
            print(f"Response: {body}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(f"Error body: {error_body}")
        return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_generate_with_callback()
    if success:
        print("✓ Test passed!")
    else:
        print("✗ Test failed")
