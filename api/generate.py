from http.server import BaseHTTPRequestHandler
import json
import requests
import os
import random

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
            
            words = data.get('words', [])
            gen_type = data.get('type', 'lyrics')
            
            style = random.choice(['suspenseful', 'heartwarming', 'humorous', 'mysterious', 'adventurous'])
            
            if gen_type == 'story':
                prompt = (
                    f"As a creative writer, write a coherent and {style} English short story using these keywords: {', '.join(words)}. "
                    f"The story should be engaging and help the reader remember the words in context. "
                    f"You MUST output a valid JSON object with a single key 'results', "
                    f"where 'results' is an array of objects. Each object should represent a meaningful paragraph or section of the story, "
                    f"with 'en' (the English text) and 'zh' (the natural Chinese translation). "
                    f"Do not include any other text or markdown formatting. Just the json content."
                )
            else:
                prompt = (
                    f"As a creative writer, write English song lyrics using these keywords: {', '.join(words)}. "
                    f"You are encouraged to reorder the words freely to make the lyrics more harmonious, creative, and rhythmic. "
                    f"You MUST output a valid JSON object with a single key 'results', "
                    f"where 'results' is an array of objects, each with 'en' (the English line) and 'zh' (the natural Chinese translation). "
                    f"Do not include any other text or markdown formatting. Just the json content."
                )

            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "response_format": {"type": "json_object"}
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }

            response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=45)
            response.raise_for_status()
            
            result = response.json()
            content_json = json.loads(result['choices'][0]['message']['content'])
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(content_json).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
