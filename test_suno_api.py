import urllib.request
import urllib.error
import json
import os

SUNO_API_KEY = os.environ.get("SUNO_API_KEY", "e051ee77fc78bcfa4f95e2105ad80dc6")
SUNO_API_BASE = os.environ.get("SUNO_API_BASE", "https://api.sunoapi.org").rstrip("/")

def test_suno_connection():
    print(f"Testing Suno API connection...")
    print(f"SUNO_API_KEY: {SUNO_API_KEY[:8]}****")
    print(f"SUNO_API_BASE: {SUNO_API_BASE}")
    
    # Test basic connectivity - try a simple GET request
    test_endpoint = f"{SUNO_API_BASE}/api/v1/fetch/test"
    req = urllib.request.Request(
        test_endpoint,
        headers={
            "Authorization": f"Bearer {SUNO_API_KEY}",
            "X-API-KEY": SUNO_API_KEY,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            body = res.read().decode('utf-8')
            print(f"Response status: {res.status}")
            print(f"Response body: {body[:500]}")
            return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"Error body: {error_body}")
        except:
            pass
        return False
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_suno_connection()
    if success:
        print("✓ Suno API connection test PASSED")
    else:
        print("✗ Suno API connection test FAILED")
