from http.server import BaseHTTPRequestHandler
import json
import requests
import os
import datetime
import re
import time
import urllib.parse

SUCCESS_STATES = {"success", "completed", "done", "finished"}
FAIL_STATES = {"failed", "error", "cancelled", "canceled"}


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
        # Prefer audioUrl (mp3/mp4), fallback to streamAudioUrl
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
        resp = requests.get(url, headers=headers, timeout=45)
        record_info_json = resp.json()
        data = record_info_json.get("data") if isinstance(record_info_json, dict) else None
        raw_status = data.get("status") if isinstance(data, dict) else None
        status = _map_record_info_status(raw_status)
        audio_url = _extract_audio_url_from_record_info(record_info_json) or _extract_audio_url(record_info_json)
        error = None
        if isinstance(data, dict):
            error = data.get("errorMessage") or data.get("error") or data.get("msg")
        if not error and isinstance(record_info_json, dict):
            error = record_info_json.get("errorMessage") or record_info_json.get("error") or record_info_json.get("msg")
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
        # 优先：只要拿到了可用媒体链接，且并非明确失败，就直接返回。
        if last_audio_url and status_l not in FAIL_STATES and not any(s in status_l for s in FAIL_STATES):
            if any(s in status_l for s in SUCCESS_STATES) or status_l not in ("pending", "processing", "in_progress", "queued", "running", ""):
                return last_status, last_audio_url, None

        if last_audio_url and any(s in status_l for s in SUCCESS_STATES):
            return last_status, last_audio_url, None

        if str(last_status).lower() in SUCCESS_STATES and last_audio_url:
            return last_status, last_audio_url, None

        if status_l in FAIL_STATES or any(s in status_l for s in FAIL_STATES):
            return last_status, None, last_error or "歌曲生成失败"

        time.sleep(interval_seconds)

    return last_status, last_audio_url, last_error or "生成超时"

SUNO_API_KEY = os.environ.get("SUNO_API_KEY")
SUNO_API_BASE = os.environ.get("SUNO_API_BASE", "https://api.sunoapi.org").rstrip("/")


def parse_title_and_prompt(lyrics):
    lines = [line.strip() for line in lyrics.splitlines()]
    title = "WordMelody Song"
    body_lines = []
    for line in lines:
        if not line:
            continue
        match = re.match(r'^【标题】\s*(.+)$', line)
        if match and match.group(1).strip():
            title = match.group(1).strip()
            continue
        body_lines.append(line)
    prompt = '\n'.join(body_lines).strip() or lyrics.strip()
    return title, prompt


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not SUNO_API_KEY:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Environment variable SUNO_API_KEY is not set on Vercel"}).encode('utf-8'))
            return

        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            lyrics = str(data.get('lyrics', '')).strip()
            style = str(data.get('style', 'pop')).strip() or 'pop'

            if not lyrics:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "歌词不能为空"}).encode('utf-8'))
                return

            title, prompt = parse_title_and_prompt(lyrics)
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
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {SUNO_API_KEY}",
                "X-API-KEY": SUNO_API_KEY,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
            response = requests.post(f"{SUNO_API_BASE}/api/v1/generate", json=payload, headers=headers, timeout=30)
            
            result = response.json()
            if result.get("code") and result.get("code") != 200:
                raise ValueError(result.get("msg", "Suno API 请求失败"))
            
            task_data = result.get("data") or {}
            task_id = task_data.get("taskId") or result.get("task_id") or result.get("id")
            
            if not task_id:
                raise ValueError("Suno 返回缺少 task_id")

            # 关键：后端轮询直到拿到真实媒体地址（audio_url）
            status, audio_url, poll_error = _poll_suno_until_done(task_id, max_wait_seconds=180, interval_seconds=3)

            resp_payload = {
                "task_id": task_id,
                "status": status,
                "audio_url": audio_url,
            }
            if poll_error:
                resp_payload["error"] = poll_error

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8'))
