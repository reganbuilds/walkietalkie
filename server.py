#!/usr/bin/env python3
"""
WalkieTalkie — Local Voice Journal Server
Record thoughts on the go, think out loud, transcribe privately.

Receives audio from iPhone → transcribes with Whisper → appends to daily memory.
Runs at http://[mac-mini-ip]:5050

100% local. Nothing leaves your network.
"""

import http.server
import json
import os
import tempfile
import re
import threading
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
PORT = int(os.environ.get("WALKIETALKIE_PORT", 5050))
BIND_HOST = os.environ.get("WALKIETALKIE_HOST", "0.0.0.0")  # Set to "127.0.0.1" for localhost-only
MAX_AUDIO_BYTES = 100 * 1024 * 1024  # 100 MB max upload
ALLOWED_CONTENT_TYPES = {"audio/m4a", "audio/mp4", "audio/wav", "audio/mpeg", "audio/ogg", "audio/aac", "application/octet-stream"}
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL", "base")  # tiny, base, small, medium
MEMORY_DIR = Path(os.environ.get("WALKIETALKIE_MEMORY_DIR", os.path.expanduser("~/.openclaw/workspace/memory")))

# ── Load Whisper once at startup (not per-request) ────────────────────────────
print(f"Loading Whisper '{WHISPER_MODEL_SIZE}' model...")
try:
    import whisper as _whisper
    _model = _whisper.load_model(WHISPER_MODEL_SIZE)
    _model_lock = threading.Lock()
    print("Whisper model loaded.")
except ImportError:
    print("ERROR: whisper not installed. Run: pip3 install openai-whisper")
    raise

# ── Core functions ────────────────────────────────────────────────────────────

def transcribe(audio_path: str) -> str:
    """Transcribe audio file. Thread-safe via lock."""
    with _model_lock:
        result = _model.transcribe(str(audio_path), language="en", fp16=False)
    text = result.get("text", "").strip()
    if not text:
        raise ValueError("Whisper returned an empty transcript. Was the audio too short or silent?")
    return text


def summarize(transcript: str) -> str:
    """Simple extractive summary — first 2 sentences."""
    normalized = transcript.replace("!", ".").replace("?", ".")
    sentences = [s.strip() for s in normalized.split(".") if len(s.strip()) > 10]
    summary = ". ".join(sentences[:2])
    return (summary + ".") if summary else transcript[:200]


def sanitize_for_markdown(text: str, max_len: int = 10000) -> str:
    """Prevent markdown injection and limit length."""
    # Remove any lines that look like markdown headers injected by user
    text = re.sub(r'^#{1,6}\s', '', text, flags=re.MULTILINE)
    # Strip null bytes and control chars (except newlines/tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text[:max_len]


def append_to_memory(transcript: str, summary: str, duration_secs: int = 0) -> Path:
    """Append voice journal entry to today's memory file."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%I:%M %p")
    memory_file = MEMORY_DIR / f"{today}.md"

    duration_str = ""
    if duration_secs and isinstance(duration_secs, int) and 0 < duration_secs < 86400:
        m, s = divmod(duration_secs, 60)
        duration_str = f" ({m}m {s}s)" if m else f" ({s}s)"

    clean_transcript = sanitize_for_markdown(transcript)
    clean_summary = sanitize_for_markdown(summary, max_len=500)

    entry = (
        f"\n## 🎙️ WalkieTalkie — {time_str}{duration_str}\n\n"
        f"**Summary:** {clean_summary}\n\n"
        f"**Transcript:**\n> {clean_transcript.replace(chr(10), chr(10) + '> ')}\n"
    )

    with open(memory_file, "a", encoding="utf-8") as f:
        f.write(entry)

    return memory_file


# ── HTTP Handler ──────────────────────────────────────────────────────────────

class WalkieTalkieHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {self.address_string()} {fmt % args}")

    def send_json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {
                "status": "ok",
                "service": "WalkieTalkie",
                "model": WHISPER_MODEL_SIZE,
            })
        else:
            self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/journal":
            self.send_json(404, {"error": "Not found. POST to /journal"})
            return

        # Validate Content-Length
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            self.send_json(400, {"error": "Invalid Content-Length"})
            return

        if content_length <= 0:
            self.send_json(400, {"error": "No audio data received"})
            return

        if content_length > MAX_AUDIO_BYTES:
            self.send_json(413, {"error": f"Audio file too large. Max {MAX_AUDIO_BYTES // 1024 // 1024}MB"})
            return

        # Validate Content-Type
        content_type = (self.headers.get("Content-Type", "") or "").lower().split(";")[0].strip()
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            self.send_json(415, {"error": f"Unsupported audio type: {content_type}"})
            return

        # Parse duration header safely
        duration_secs = 0
        try:
            raw_duration = self.headers.get("X-Duration-Seconds", "")
            if raw_duration:
                duration_secs = max(0, min(int(raw_duration), 86400))
        except (ValueError, TypeError):
            pass

        # Determine file extension from content type
        ext_map = {
            "audio/m4a": ".m4a", "audio/mp4": ".m4a", "audio/wav": ".wav",
            "audio/mpeg": ".mp3", "audio/ogg": ".ogg", "audio/aac": ".aac",
        }
        ext = ext_map.get(content_type, ".m4a")

        # Read audio data
        try:
            audio_data = self.rfile.read(content_length)
        except Exception as e:
            self.send_json(500, {"error": f"Failed to read audio: {e}"})
            return

        if len(audio_data) < 100:
            self.send_json(400, {"error": "Audio data too small — was the recording empty?"})
            return

        print(f"Received audio: {len(audio_data) / 1024:.1f} KB, type: {content_type or 'unknown'}")

        # Write to temp file, transcribe, clean up
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False, prefix="walkietalkie_") as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            transcript = transcribe(tmp_path)
            print(f"Transcript ({len(transcript)} chars): {transcript[:80]}...")

            summary = summarize(transcript)
            memory_file = append_to_memory(transcript, summary, duration_secs)
            print(f"Saved to: {memory_file}")

            self.send_json(200, {
                "status": "ok",
                "transcript": transcript,
                "summary": summary,
                "saved_to": str(memory_file),
                "chars": len(transcript),
            })

        except ValueError as e:
            self.send_json(422, {"error": str(e)})

        except Exception as e:
            print(f"ERROR: {e}")
            self.send_json(500, {"error": f"Transcription failed: {e}"})

        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass  # Already gone or permission issue — not critical


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n🎙️  WalkieTalkie — Local Voice Journal")
    print(f"   Whisper model : {WHISPER_MODEL_SIZE}")
    print(f"   Memory dir    : {MEMORY_DIR}")
    print(f"   Listening on  : http://{BIND_HOST}:{PORT}")
    print(f"   Max upload    : {MAX_AUDIO_BYTES // 1024 // 1024}MB")
    print(f"\n   POST audio to : http://[your-ip]:{PORT}/journal")
    print(f"   Health check  : http://[your-ip]:{PORT}/health\n")

    server = http.server.HTTPServer((BIND_HOST, PORT), WalkieTalkieHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down WalkieTalkie.")
        server.shutdown()
