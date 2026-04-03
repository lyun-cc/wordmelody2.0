import http.server
import socketserver
import os

PORT = 9090

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.date_time_string()}] {format % args}", flush=True)

def main():
    print(f"Starting test server on port {PORT}...")
    try:
        with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
            print(f"Test server running at http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()