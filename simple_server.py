import http.server
import socketserver
import json

PORT = 9292

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.date_time_string()}] {format % args}", flush=True)
    
    def do_GET(self):
        if self.path == '/test':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Server is running"}).encode('utf-8'))
        else:
            super().do_GET()

def main():
    print(f"Starting simple server on port {PORT}...")
    try:
        with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
            print(f"Server running at http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()