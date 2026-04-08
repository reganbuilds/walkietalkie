#!/bin/bash
# WalkieTalkie installer

set -e

echo "🎙️  WalkieTalkie — Local Voice Journal"
echo "======================================="

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 not found. Install from https://python.org"
  exit 1
fi
echo "✅ Python $(python3 --version)"

# Install Python deps
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt
echo "✅ openai-whisper installed"

# Check ffmpeg
if ! command -v ffmpeg &>/dev/null; then
  echo ""
  echo "⚠️  ffmpeg not found — needed for audio decoding."
  echo "   macOS:   brew install ffmpeg"
  echo "   Ubuntu:  sudo apt install ffmpeg"
  echo "   Windows: https://ffmpeg.org/download.html"
  echo ""
else
  echo "✅ ffmpeg found"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "▶️  Start the server:"
echo "   python3 server.py"
echo ""
echo "📱 Then set up your iOS Shortcut:"
echo "   POST audio/m4a to http://[your-mac-ip]:5050/journal"
echo ""
echo "📖 Full setup guide: https://github.com/reganbuilds/walkietalkie"
