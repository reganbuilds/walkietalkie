# 🎙️ WalkieTalkie

**Record thoughts on the go. Think out loud. Let your AI remember.**

A local-first voice journaling server that transcribes your iPhone recordings using [Whisper](https://github.com/openai/whisper) and saves them directly to your AI memory files — privately, offline, and free.

> 100% local. Nothing leaves your network.

---

## How it works

1. **Record** a voice memo on your iPhone while you're on the go
2. **Send** the audio to your Mac via iOS Shortcut (one tap)
3. **Whisper** transcribes it locally on your machine
4. **Entry saved** to your daily memory file, ready for your AI to read

No cloud. No subscriptions. No data leaving your home.

---

## Install

**Requirements:** Python 3.8+, ffmpeg

```bash
# Clone
git clone https://github.com/reganbuilds/walkietalkie.git
cd walkietalkie

# Install dependencies
pip install -r requirements.txt

# Install ffmpeg (macOS)
brew install ffmpeg

# Start the server
python server.py
```

The server starts at `http://0.0.0.0:5050` by default.

---

## iPhone Shortcut

**Import the ready-made shortcut:**

<https://www.icloud.com/shortcuts/e41ce4b181d048d2b601714464a5c6b7>

After importing it, replace:

`http://YOUR-MAC-IP:5050/journal`

with your Mac's local IP address.

Then add it to your home screen, widget, Back Tap, or Siri.

For the full step-by-step setup guide, troubleshooting, and manual build instructions, see [SHORTCUT_SETUP.md](SHORTCUT_SETUP.md).

---

## Configuration

Set via environment variables:

| Variable | Default | Description |
|---|---|---|
| `WALKIETALKIE_PORT` | `5050` | Server port |
| `WALKIETALKIE_HOST` | `0.0.0.0` | Bind address (`127.0.0.1` for localhost-only) |
| `WHISPER_MODEL` | `base` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` |
| `WALKIETALKIE_MEMORY_DIR` | `~/.openclaw/workspace/memory` | Where to save journal entries |

**Example:**
```bash
WHISPER_MODEL=small WALKIETALKIE_PORT=5050 python server.py
```

---

## API

### `POST /journal`
Send audio → get transcript back.

**Headers:**
- `Content-Type: audio/m4a` (or wav, mp3, ogg, aac)
- `X-Duration-Seconds: 180` (optional, logged with entry)

**Response:**
```json
{
  "status": "ok",
  "transcript": "Today I was thinking about...",
  "summary": "Today I was thinking about the project.",
  "saved_to": "/path/to/memory/2026-04-08.md",
  "chars": 312
}
```

### `GET /health`
Check server status and config.

---

## Output format

Each entry is appended to a daily Markdown file:

```markdown
## 🎙️ WalkieTalkie — 10:34 AM (3m 12s)

**Summary:** Today I was thinking about the new project direction.

**Transcript:**
> Today I was thinking about the new project direction. I want to focus on...
```

---

## Built for OpenClaw

WalkieTalkie writes to the same memory format used by [OpenClaw](https://openclaw.ai) — so your AI assistant automatically has context from thoughts you capture on the go in every session. But it works with any system that reads Markdown files.

---

## License

MIT — see [LICENSE](LICENSE)

Made by [@reganbuilds](https://x.com/reganbuilds)
