import urllib.request
import urllib.error
import json
import os

SUNO_API_KEY = os.environ.get("SUNO_API_KEY", "e051ee77fc78bcfa4f95e2105ad80dc6")
SUNO_API_BASE = os.environ.get("SUNO_API_BASE", "https://api.sunoapi.org").rstrip("/")

def test_fetch_task(task_id):
    print(f"Testing Suno API fetch with task_id: {task_id}")
    
    # Test different endpoints
    endpoints = [
        f"/api/v1/fetch/{task_id}",
        f"/api/v1/fetch?taskId={task_id}",
        f"/api/v1/get/{task_id}",
        f"/api/get?id={task_id}",
        f"/api/fetch?taskId={task_id}"
    ]
    
    for endpoint in endpoints:
        url = f"{SUNO_API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {SUNO_API_KEY}",
            "X-API-KEY": SUNO_API_KEY,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                body = res.read().decode('utf-8')
                print(f"Success with endpoint: {endpoint}")
                print(f"Status: {res.status}")
                print(f"Response: {body}")
                return True
        except urllib.error.HTTPError as e:
            print(f"HTTP Error with endpoint {endpoint}: {e.code}")
        except Exception as e:
            print(f"Exception with endpoint {endpoint}: {e}")
    
    return False

if __name__ == "__main__":
    task_id = "dc932525c0bba470be6863f26ef86b03"
    success = test_fetch_task(task_id)
    if success:
        print("✓ Fetch test passed!")
    else:
        print("✗ Fetch test failed")
