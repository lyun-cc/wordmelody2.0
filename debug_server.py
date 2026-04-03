import http.server
import socketserver
import json

PORT = 8888

class DebugHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.date_time_string()}] {format % args}", flush=True)
    
    def do_GET(self):
        print(f"Received GET request for: {self.path}", flush=True)
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Debug Server</h1><p>Server is running!</p></body></html>")
        else:
            super().do_GET()

def main():
    print(f"Starting debug server on port {PORT}...")
    try:
        with socketserver.TCPServer(("", PORT), DebugHandler) as httpd:
            print(f"Server running at http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()