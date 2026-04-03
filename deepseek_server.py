import http.server
import json
import urllib.request
import os
import sys

# DeepSeek API configuration
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-49611edadff0471d868e49c1f18aba6d")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

class DeepSeekProxyHandler(http.server.BaseHTTPRequestHandler):
    # Disable internal logging for cleaner output
    def log_message(self, format, *args):
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/generate':
            self.handle_generate_stream()
        elif self.path == '/api/translate':
            self.handle_translate()
        else:
            self.send_error(404)

    def handle_generate_stream(self):
        print("Handling /api/generate request...")
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        words = data.get('words', [])
        gen_type = data.get('type', 'lyrics')
        print(f"Keywords: {words}, Type: {gen_type}")
        
        # Using a more strict JSON object structure to reduce model thinking time
        prompt = (
            f"As a creative writer, write an English {gen_type} using these keywords: {', '.join(words)}. "
            f"You MUST output a valid JSON object with a single key 'results', "
            f"where 'results' is an array of objects, each with 'en' (the English line) and 'zh' (the natural Chinese translation). "
            f"Do not include any other text or markdown formatting. Just the json content."
        )

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "stream": True,
            "response_format": {"type": "json_object"} # Force JSON mode
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()

        print("Calling DeepSeek API...")
        req = urllib.request.Request(
            DEEPSEEK_API_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
        )
        
        try:
            # Setting a timeout and ensuring we read unbuffered
            with urllib.request.urlopen(req, timeout=30) as res:
                print("DeepSeek API connection established, starting stream...")
                while True:
                    line = res.readline()
                    if not line:
                        print("Stream finished.")
                        break
                    # Send each chunk immediately
                    self.wfile.write(line)
                    self.wfile.flush()
        except Exception as e:
            print(f"Streaming Error: {e}", file=sys.stderr)
            # Ensure it's a valid data: line for the client
            error_json = json.dumps({"error": str(e)})
            self.wfile.write(f"data: {error_json}\n\n".encode('utf-8'))
            self.wfile.flush()

    def handle_translate(self):
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
        
        req = urllib.request.Request(
            DEEPSEEK_API_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                body = res.read().decode('utf-8')
                result = json.loads(body)
                content_json = json.loads(result['choices'][0]['message']['content'])
                self.send_json_response(content_json.get('translations', []))
        except Exception as e:
            self.send_json_response({"error": str(e)})

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

if __name__ == '__main__':
    port = 8001
    try:
        server = http.server.HTTPServer(('0.0.0.0', port), DeepSeekProxyHandler)
        print(f"DeepSeek Optimized Proxy Server running on port {port}...", flush=True)
        server.serve_forever()
    except Exception as e:
        import traceback
        print(f"Server crash: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
