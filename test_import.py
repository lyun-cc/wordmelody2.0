import sys
print("Python version:", sys.version)
print("Python executable:", sys.executable)

try:
    print("\nTesting imports...")
    import http.server
    print("http.server: OK")
    
    import socketserver
    print("socketserver: OK")
    
    import json
    print("json: OK")
    
    import urllib.request
    print("urllib.request: OK")
    
    import urllib.error
    print("urllib.error: OK")
    
    import urllib.parse
    print("urllib.parse: OK")
    
    import os
    print("os: OK")
    
    import re
    print("re: OK")
    
    import datetime
    print("datetime: OK")
    
    print("\nAll imports successful!")
    
except Exception as e:
    print(f"\nImport error: {e}")
    import traceback
    traceback.print_exc()