# 🎬 NanoPro Reel Maker

> **Automated 9:16 Vertical 2D Tech Video Generator for Instagram Reels & YouTube Shorts**  
> *AWS • Snowflake • SQL • Python • Cloud • AI*

---

## 🌟 Key Highlights

- **Zero Hardcoding / Zero Fixed Templates**: Dynamically constructs architecture flowcharts, interactive SQL tables, dark-mode code editors, and metric cards based on the technical subject matter.
- **Natural Human Cadence**: Scripts designed with real conversational pacing, analogies, and deliberate pauses.
- **Microsecond Word-Level Sync**: Powered by Groq Whisper Large v3 to synchronize karaoke-style glowing subtitles and visual triggers.
- **60-Second Full-Length Reels**: No 5-second generative cutoff. Programmatic 1080x1920 30FPS MP4 rendering.
- **Zero Cloud Rendering Costs**: Runs locally on your laptop's CPU/GPU with FFmpeg.
- **Cloudflare R2 Integration**: Automatic upload to Cloudflare R2 (10 GB free forever with zero egress fees).

---

## 🏗️ Architecture Pipeline

```text
User Topic Prompt (e.g. "AWS DMS in 60s")
       │
       ▼
[ 1. AI Director (Gemini 2.5 Flash / Groq) ]
       │ ──► Generates Scene Timeline JSON Contract
       ▼
[ 2. Voice & Alignment Engine ]
       │ ──► Edge-TTS (Natural human voice)
       │ ──► Groq Whisper Large v3 (Word-level timestamps)
       ▼
[ 3. Generative 2D Visual Engine ]
       │ ──► Dynamic Architecture Nodes, SQL Tables, Code Terminal
       ▼
[ 4. FFmpeg Video Compositor ]
       │ ──► Stitches 1080x1920 MP4 + Karaoke Subtitles
       ▼
[ 5. Cloudflare R2 CDN ]
       │ ──► Public video streaming link
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
Make sure Python 3.10+ is installed.

### 2. Clone the Repository
```bash
git clone https://github.com/mangeshbagul15/nanopro-reel-maker.git
cd nanopro-reel-maker
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Configure your `.env` file:
```env
GEMINI_API_KEY="your-gemini-key"
GROQ_API_KEY="your-groq-key"
CLOUDFLARE_ACCOUNT_ID="your-cf-account-id"
CLOUDFLARE_R2_ACCESS_KEY="your-r2-access-key"
CLOUDFLARE_R2_SECRET_KEY="your-r2-secret-key"
CLOUDFLARE_R2_BUCKET="nanopro-reels"
```

### 5. Launch the Web Studio
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser!

---

## 📂 Project Structure

```text
nanopro-reel-maker/
├── app.py              # Streamlit Web UI & Live Reel Generator
├── requirements.txt    # Minimal dependencies
├── .env                # API configuration
├── README.md           # Documentation
│
├── core/
│   ├── config.py       # Configuration and paths
│   ├── director.py     # AI Director & JSON timeline generation
│   ├── voice.py        # Voice synthesis & Whisper alignment
│   ├── animator.py     # 2D Generative Graphics Engine (Pillow/Canvas)
│   ├── subtitles.py    # Karaoke-style ASS subtitle generator
│   ├── renderer.py     # High-speed FFmpeg video assembler
│   └── uploader.py     # Cloudflare R2 object storage uploader
│
└── output/             # Generated MP4 videos and assets
```

---

## 📜 License
MIT License. Created by [Mangesh Bagul](https://github.com/mangeshbagul15).
