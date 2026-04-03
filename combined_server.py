import http.server
import json
import urllib.request
import os
import sys
import socketserver
import random
import urllib.error
import urllib.parse
import datetime
import re
import socket
import time

# DeepSeek API configuration
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-49611edadff0471d868e49c1f18aba6d")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
SUNO_API_KEY = os.environ.get("SUNO_API_KEY", "e051ee77fc78bcfa4f95e2105ad80dc6")
SUNO_API_BASE = os.environ.get("SUNO_API_BASE", "https://api.sunoapi.org").rstrip("/")

SUCCESS_STATES = {"success", "completed", "done", "finished"}
FAIL_STATES = {"failed", "error", "cancelled", "canceled"}


def parse_title_and_prompt(lyrics):
    lines = [line.strip() for line in lyrics.splitlines()]
    title = "WordMelody Song"
    body_lines = []
    for line in lines:
        if not line: continue
        match = re.match(r'^【标题】\s*(.+)$', line)
        if match and match.group(1).strip():
            title = match.group(1).strip()
            continue
        body_lines.append(line)
    prompt = '\n'.join(body_lines).strip() or lyrics.strip()
    return title, prompt

def send_json(handler, data, status=200):
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode('utf-8'))


def _normalize_status(raw):
    if raw is None:
        return "pending"
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        for k in ("status", "state", "phase"):
            if k in raw:
                return _normalize_status(raw.get(k))
        for v in raw.values():
            if isinstance(v, str):
                return v.strip()
        return "pending"
    return str(raw).strip()


def _extract_audio_url(obj, depth=0, max_depth=8):
    if obj is None or depth > max_depth:
        return None

    if isinstance(obj, str):
        s = obj.strip()
        if not s:
            return None
        low = s.lower()
        if low.startswith("http://") or low.startswith("https://"):
            return s
        if ("mp3" in low or "mp4" in low) and ("//" in s or s.startswith("/")):
            return s
        return None

    if isinstance(obj, list):
        for item in obj:
            u = _extract_audio_url(item, depth=depth + 1, max_depth=max_depth)
            if u:
                return u
        return None

    if isinstance(obj, dict):
        direct_keys = [
            "audio_url",
            "audioUrl",
            "audio",
            "url",
            "download_url",
            "mp3_url",
            "mp4_url",
            "mp3",
            "mp4",
            "media_url",
        ]
        for k in direct_keys:
            if k in obj:
                u = _extract_audio_url(obj.get(k), depth=depth + 1, max_depth=max_depth)
                if u:
                    return u

        for v in obj.values():
            u = _extract_audio_url(v, depth=depth + 1, max_depth=max_depth)
            if u:
                return u
        return None

    return None


def _map_record_info_status(raw):
    """
    Suno record-info status is uppercase like PENDING/SUCCESS/CREATE_TASK_FAILED...
    Convert it to frontend-friendly lowercase buckets.
    """
    s = str(raw or "").strip().upper()
    if not s:
        return "pending"
    if s in {"SUCCESS", "FIRST_SUCCESS"}:
        return "success"
    if s in {"PENDING", "TEXT_SUCCESS"}:
        return "pending"
    if s in {
        "CREATE_TASK_FAILED",
        "GENERATE_AUDIO_FAILED",
        "CALLBACK_EXCEPTION",
        "SENSITIVE_WORD_ERROR",
    }:
        return "failed"
    return s.lower()


def _extract_audio_url_from_record_info(record_info_json):
    if not isinstance(record_info_json, dict):
        return None
    data = record_info_json.get("data")
    if not isinstance(data, dict):
        return None
    response = data.get("response")
    if not isinstance(response, dict):
        return None
    suno_data = response.get("sunoData") or []
    if not isinstance(suno_data, list):
        return None

    for item in suno_data:
        if not isinstance(item, dict):
            continue
        audio_url = item.get("audioUrl") or item.get("streamAudioUrl")
        if audio_url:
            return audio_url
    return None


def _fetch_suno_task_once(task_id):
    headers = {
        "Authorization": f"Bearer {SUNO_API_KEY}",
        "X-API-KEY": SUNO_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    encoded = urllib.parse.quote(task_id)
    url = f"{SUNO_API_BASE}/api/v1/generate/record-info?taskId={encoded}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as res:
            body = res.read().decode('utf-8', errors='ignore')
            result = json.loads(body or "{}")
            data = result.get("data") if isinstance(result.get("data"), dict) else None
            raw_status = data.get("status") if isinstance(data, dict) else None
            status = _map_record_info_status(raw_status)
            audio_url = _extract_audio_url_from_record_info(result) or _extract_audio_url(result)
            error = None
            if isinstance(data, dict):
                error = data.get("errorMessage") or data.get("error") or data.get("msg")
            if not error:
                error = result.get("errorMessage") or result.get("error") or result.get("msg")
            return status, audio_url, error
    except Exception as e:
        return "pending", None, str(e) or "无法获取任务状态"


def _poll_suno_until_done(task_id, max_wait_seconds=110, interval_seconds=3):
    deadline = time.time() + max_wait_seconds
    last_status = "pending"
    last_audio_url = None
    last_error = None

    while time.time() < deadline:
        status, audio_url, error = _fetch_suno_task_once(task_id)
        last_status = status or "pending"
        last_audio_url = audio_url
        last_error = error

        status_l = str(last_status).lower()

        # 如果拿到了媒体链接，且并非明确失败，就提前结束
        if last_audio_url and status_l not in FAIL_STATES and not any(s in status_l for s in FAIL_STATES):
            return last_status, last_audio_url, None

        if status_l in FAIL_STATES or any(s in status_l for s in FAIL_STATES):
            return last_status, None, last_error or "歌曲生成失败"

        if last_audio_url and any(s in status_l for s in SUCCESS_STATES):
            return last_status, last_audio_url, None

        time.sleep(interval_seconds)

    return last_status, last_audio_url, last_error or "生成超时"

class UnifiedHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.date_time_string()}] {format % args}", flush=True)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/song-status/'):
            task_id = self.path.replace('/api/song-status/', '', 1).strip()
            self.handle_song_status(task_id)
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path == '/api/generate':
            self.handle_generate()
        elif self.path == '/api/translate':
            self.handle_translate()
        elif self.path == '/api/generate-song':
            self.handle_generate_song()
        else:
            self.send_error(404)

    def handle_generate(self):
        print(f"Handling /api/generate", flush=True)
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            words = data.get('words', [])
            gen_type = data.get('type', 'lyrics')
            
            prompt = (
                f"As a creative writer, write an English {gen_type} using these keywords: {', '.join(words)}. "
                f"You MUST output a valid JSON object with a single key 'results', "
                f"where 'results' is an array of objects, each with 'en' (the English line) and 'zh' (the natural Chinese translation). "
                f"Do not include any other text or markdown formatting. Just the json content."
            )
            
            payload = {
                "model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8, "response_format": {"type": "json_object"}
            }
            
            req = urllib.request.Request(
                DEEPSEEK_API_URL, data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
            )
            
            with urllib.request.urlopen(req, timeout=60) as res:
                body = res.read().decode('utf-8')
                result = json.loads(body)
                content_json = json.loads(result['choices'][0]['message']['content'])
                send_json(self, content_json)
        except Exception as e:
            print(f"Generate Error: {e}", flush=True)
            send_json(self, {"error": str(e)}, 500)

    def handle_translate(self):
        print(f"Handling /api/translate", flush=True)
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
                "model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3, "response_format": {"type": "json_object"}
            }
            req = urllib.request.Request(
                DEEPSEEK_API_URL, data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
            )
            with urllib.request.urlopen(req, timeout=45) as res:
                body = res.read().decode('utf-8')
                result = json.loads(body)
                content_json = json.loads(result['choices'][0]['message']['content'])
                send_json(self, content_json.get('translations', []))
        except Exception as e:
            print(f"Translate Error: {e}", flush=True)
            send_json(self, {"error": str(e)}, 500)

    def handle_generate_song(self):
        print(f"Handling /api/generate-song", flush=True)
        if not SUNO_API_KEY:
            send_json(self, {"error": "SUNO_API_KEY 未配置"}, 500)
            return
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data or b'{}')
            lyrics = str(data.get('lyrics', '')).strip()
            style = str(data.get('style', 'pop')).strip() or 'pop'
            if not lyrics:
                send_json(self, {"error": "歌词不能为空"}, 400)
                return

            title, prompt = parse_title_and_prompt(lyrics)
            # 使用新版 API 路径和参数
            payload = {
                "prompt": prompt, 
                "title": title, 
                "tags": style, 
                "model": "V3_5",
                "instrumental": False,
                "customMode": True,
            }
            # Suno 侧要求 callBackUrl 为必填字段；提供可覆盖的默认回退值。
            payload["callBackUrl"] = os.environ.get("SUNO_CALLBACK_URL", "http://example.com/callback")
            req = urllib.request.Request(
                f"{SUNO_API_BASE}/api/v1/generate",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {SUNO_API_KEY}",
                    "X-API-KEY": SUNO_API_KEY,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                }
            )
            with urllib.request.urlopen(req, timeout=45) as res:
                body = res.read().decode('utf-8')
                result = json.loads(body or "{}")
                # 兼容 code 200 但实际失败的情况
                if result.get("code") and result.get("code") != 200:
                    send_json(self, {"error": result.get("msg", "API 请求失败")}, 502)
                    return
                # 获取 taskId (注意大小写)
                task_data = result.get("data") or {}
                task_id = task_data.get("taskId") or result.get("task_id") or result.get("id")
                if not task_id:
                    send_json(self, {"error": f"Suno 返回缺少 task_id: {body}"}, 502)
                    return

                # 关键：后端轮询直到拿到真实媒体地址（audio_url）
                status, audio_url, poll_error = _poll_suno_until_done(task_id, max_wait_seconds=180, interval_seconds=3)
                resp_payload = {
                    "task_id": task_id,
                    "status": status,
                    "audio_url": audio_url,
                }
                if poll_error:
                    resp_payload["error"] = poll_error

                send_json(self, resp_payload)
        except Exception as e:
            print(f"Generate Song Error: {e}", flush=True)
            send_json(self, {"error": str(e)}, 500)

    def handle_song_status(self, task_id):
        print(f"Handling /api/song-status/{task_id}", flush=True)
        if not task_id:
            send_json(self, {"error": "缺少 task_id"}, 400)
            return

        status, audio_url, err = _fetch_suno_task_once(task_id)
        send_json(self, {"status": status, "audio_url": audio_url, "error": err})

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == "__main__":
    port = 9494
    try:
        server = ThreadingHTTPServer(('', port), UnifiedHandler)
        print(f"Server started on port {port}", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server...", flush=True)
        server.shutdown()
    except Exception as e:
        import traceback
        print(f"\n=================================")
        print(f"服务器致命启动错误 (CRASH LOG):")
        print(traceback.format_exc())
        print(f"=================================\n")
