import urllib.request
import urllib.error
import json
import os

SUNO_API_KEY = os.environ.get("SUNO_API_KEY", "e051ee77fc78bcfa4f95e2105ad80dc6")
SUNO_API_BASE = os.environ.get("SUNO_API_BASE", "https://api.sunoapi.org").rstrip("/")

def test_endpoint(endpoint, method="GET", data=None):
    url = f"{SUNO_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {SUNO_API_KEY}",
        "X-API-KEY": SUNO_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    if method == "POST":
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method="POST"
        )
    else:
        req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            body = res.read().decode('utf-8')
            return {
                "status": "success",
                "status_code": res.status,
                "body": body
            }
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode('utf-8')
        except:
            error_body = ""
        return {
            "status": "error",
            "status_code": e.code,
            "reason": e.reason,
            "body": error_body
        }
    except Exception as e:
        return {
            "status": "exception",
            "message": str(e)
        }

def test_suno_api():
    print(f"Testing Suno API configuration...")
    print(f"SUNO_API_KEY: {SUNO_API_KEY[:8]}****")
    print(f"SUNO_API_BASE: {SUNO_API_BASE}")
    
    # Test different endpoints
    endpoints_to_test = [
        ("/api/v1/fetch/test", "GET"),
        ("/api/v1/generate", "POST", {
            "prompt": "Test prompt",
            "title": "Test Title",
            "tags": "pop",
            "model": "V3_5",
            "instrumental": False,
            "customMode": True
        }),
        ("/api/get", "GET"),
        ("/api/fetch", "GET"),
        ("/api/v1/get/test", "GET"),
    ]
    
    results = []
    for endpoint, method, *data in endpoints_to_test:
        print(f"\nTesting: {method} {endpoint}")
        data_arg = data[0] if data else None
        result = test_endpoint(endpoint, method, data_arg)
        
        if result["status"] == "success":
            print(f"✓ Success: {result['status_code']}")
            print(f"  Response: {result['body'][:300]}")
            results.append(True)
        else:
            print(f"✗ Error: {result['status']}")
            if "status_code" in result:
                print(f"  Status: {result['status_code']}")
            if "reason" in result:
                print(f"  Reason: {result['reason']}")
            if "body" in result:
                print(f"  Body: {result['body']}")
            results.append(False)
    
    # Test basic HTTP connectivity
    print(f"\nTesting basic HTTP connectivity to {SUNO_API_BASE}...")
    try:
        with urllib.request.urlopen(SUNO_API_BASE, timeout=10) as res:
            print(f"✓ HTTP connectivity successful")
            results.append(True)
    except Exception as e:
        print(f"✗ HTTP connectivity failed: {e}")
        results.append(False)
    
    print(f"\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")

if __name__ == "__main__":
    test_suno_api()
