# iPhone Shortcut Setup

This guide shows you how to build the WalkieTalkie shortcut on iPhone and how to export/share it after it's working.

## Import the ready-made shortcut

Use the shareable iCloud shortcut here:

<https://www.icloud.com/shortcuts/e41ce4b181d048d2b601714464a5c6b7>

After importing it, replace:

`http://YOUR-MAC-IP:5050/journal`

with your own Mac's local IP.

That is the fastest path.

---

## What the shortcut does

1. Records audio on your iPhone
2. Sends it to your Mac at `http://[your-mac-ip]:5050/journal`
3. Gets back the transcript + summary
4. Shows a confirmation result

---

## Before you start

Make sure:

- WalkieTalkie is running on your Mac
- Your iPhone and Mac are on the same Wi‑Fi network
- You know your Mac's local IP address

To test the server, open this in Safari on your iPhone:

```text
http://[your-mac-ip]:5050/health
```

If you see JSON, you're good.

---

## Build the shortcut

Open the **Shortcuts** app on iPhone and create a new shortcut.

### Action 1: Record Audio

- Add action: **Record Audio**
- Suggested settings:
  - **Quality:** Normal or High
  - **Start Recording:** On Tap
  - **Finish Recording:** On Tap

This gives you an audio file as the next action's input.

### Action 2: Get Contents of URL

- Add action: **Get Contents of URL**
- Set:
  - **URL:** `http://[your-mac-ip]:5050/journal`
  - **Method:** `POST`
  - **Request Body:** `File`
  - **File:** `Recorded Audio`

### Headers

Add this header:

- `Content-Type` → `audio/m4a`

Optional header:

- `X-Duration-Seconds` → duration in seconds if you want it logged in the memory entry

If you want to keep it simple, skip the duration header. WalkieTalkie works fine without it.

### Action 3: Show the summary (optional)

If you want a cleaner success message:

- Add action: **Get Dictionary from Input**
- Then add **Get Dictionary Value** for `summary`
- Then add **Show Content** (or **Show Result**, depending on iOS version)

That way the shortcut ends by showing the summary returned by the server.

If you want the raw response instead, just use **Quick Look** or **Show Content** directly on the response.

---

## Suggested shortcut names

- WalkieTalkie
- Journal Walk
- Voice to Memory
- Walk Notes

---

## Good ways to trigger it

After you've built it, you can make it easy to use:

- Add it to your iPhone Home Screen
- Pin it in the Shortcuts widget
- Use **Back Tap**
- Trigger it with Siri: "Hey Siri, WalkieTalkie"

---

## Export / share your shortcut

Once the shortcut is working:

1. Open the shortcut in the **Shortcuts** app
2. Tap the **Share** button
3. Choose **Copy iCloud Link** or **Share**
4. Save that link in your README, tweet, or docs

That gives people a one-click install for the shortcut itself.

For this repo, the current shared shortcut is:

<https://www.icloud.com/shortcuts/e41ce4b181d048d2b601714464a5c6b7>

## Important note for sharing

Anyone who installs your shortcut will still need to change the URL to their own Mac's IP address unless they are using your exact local setup.

So the best pattern is:

- Share the shortcut structure
- Tell users to replace `http://[your-mac-ip]:5050/journal` with their own machine's IP

---

## Troubleshooting

### Shortcut hangs or fails

- Make sure the server is running
- Make sure your Mac and iPhone are on the same network
- Make sure you're using your Mac's local IP, not `localhost`

### Health check works but upload fails

- Confirm the URL ends in `/journal`
- Confirm the method is `POST`
- Confirm request body is the recorded audio file
- Confirm header is `Content-Type: audio/m4a`

### Can't reach the server from iPhone

If you started the server with localhost-only binding, your iPhone won't be able to connect.

Use:

```bash
python server.py
```

or explicitly:

```bash
WALKIETALKIE_HOST=0.0.0.0 python server.py
```

### No transcript saved

Check the terminal output from the server. If Whisper or ffmpeg is missing, the request will fail there first.

---

## Quick test with curl

You can also test the endpoint from your Mac:

```bash
curl -X POST http://127.0.0.1:5050/journal \
  -H "Content-Type: audio/m4a" \
  --data-binary @test.m4a
```

---

## Built for OpenClaw

By default, WalkieTalkie writes to:

```text
~/.openclaw/workspace/memory
```

So your AI can read your walk notes automatically in future sessions.
