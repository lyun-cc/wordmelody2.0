from http.server import BaseHTTPRequestHandler
import json
import requests
import os

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not DEEPSEEK_API_KEY:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Environment variable DEEPSEEK_API_KEY is not set on Vercel"}).encode('utf-8'))
            return

        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            lines = data.get('lines', [])
            prompt = (
                f"Translate the following English lines into natural Chinese. "
                f"Output a JSON object with a key 'translations' which is an array of strings in the same order. "
                f"Lines: {json.dumps(lines)}. Only return the json content."
            )

            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }

            response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content_json = json.loads(result['choices'][0]['message']['content'])
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(content_json.get('translations', [])).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
