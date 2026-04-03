from http.server import BaseHTTPRequestHandler
import json
import requests
import os
import urllib.parse
import time

SUCCESS_STATES = {"success", "completed", "done", "finished"}
FAIL_STATES = {"failed", "error", "cancelled", "canceled"}


def _normalize_status(raw):
    if raw is None:
        return "pending"
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        # Common patterns: {"status": "..."} / {"state": "..."} / {"phase": "..."}
        for k in ("status", "state", "phase"):
            if k in raw:
                return _normalize_status(raw.get(k))
        # Fallback: pick first string-like value
        for v in raw.values():
            if isinstance(v, str):
                return v.strip()
        return "pending"
    return str(raw).strip()


def _extract_audio_url(obj, depth=0, max_depth=7):
    if obj is None or depth > max_depth:
        return None

    if isinstance(obj, str):
        s = obj.strip()
        if not s:
            return None
        low = s.lower()
        # Prefer real URLs; allow audio-like strings that include mp3/mp4.
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
        # 1) Direct keys first
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

        # 2) Recursive fallback (bounded depth)
        for v in obj.values():
            u = _extract_audio_url(v, depth=depth + 1, max_depth=max_depth)
            if u:
                return u
        return None

    return None


def _map_record_info_status(raw):
    """
    Suno record-info status is uppercase like PENDING/SUCCESS/CREATE_TASK_FAILED...
    Convert it to our frontend-friendly lowercase buckets.
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
    # Fallback: lower-case unknown status
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

    # Prefer audioUrl (mp3/mp4), fallback to streamAudioUrl
    for item in suno_data:
        if not isinstance(item, dict):
            continue
        audio_url = item.get("audioUrl") or item.get("streamAudioUrl")
        if audio_url:
            return audio_url
    return None

SUNO_API_KEY = os.environ.get("SUNO_API_KEY")
SUNO_API_BASE = os.environ.get("SUNO_API_BASE", "https://api.sunoapi.org").rstrip("/")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not SUNO_API_KEY:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Environment variable SUNO_API_KEY is not set on Vercel"}).encode('utf-8'))
            return

        try:
            # 提取 task_id
            parts = self.path.strip('/').split('/')
            task_id = parts[-1] if parts else ""
            if not task_id or task_id.startswith('?'):
                # 尝试从 query string 获取
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                task_id = params.get('taskId', [None])[0] or params.get('id', [None])[0]

            if not task_id:
                raise ValueError("缺少 task_id")

            encoded_task_id = urllib.parse.quote(task_id)
            headers = {
                "Authorization": f"Bearer {SUNO_API_KEY}",
                "X-API-KEY": SUNO_API_KEY,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }

            # Correct endpoint per Suno docs:
            # GET /api/v1/generate/record-info?taskId=...
            url = f"{SUNO_API_BASE}/api/v1/generate/record-info?taskId={encoded_task_id}"
            response = requests.get(url, headers=headers, timeout=45)
            record_info_json = response.json()

            data = record_info_json.get("data") if isinstance(record_info_json, dict) else None
            raw_status = data.get("status") if isinstance(data, dict) else None
            status = _map_record_info_status(raw_status)

            audio_url = _extract_audio_url_from_record_info(record_info_json) or _extract_audio_url(record_info_json)

            error = None
            if isinstance(data, dict):
                error = data.get("errorMessage") or data.get("error") or data.get("msg")
            if not error and isinstance(record_info_json, dict):
                error = record_info_json.get("error") or record_info_json.get("msg")

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "status": status,
                        "audio_url": audio_url,
                        "error": error,
                    },
                    ensure_ascii=False,
                ).encode('utf-8')
            )
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "error", "audio_url": None, "error": str(e)}, ensure_ascii=False).encode('utf-8')
            )
