# 🎬 Video AI Enhancer

> Enhance any low-quality video with AI — frame by frame, locally, for free.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-green?logo=ffmpeg)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey)

---

## ✨ What It Does

**Video AI Enhancer** takes any low-resolution, dark, or laggy video and produces a stunning high-quality result by:

- 🤖 **AI Upscaling ×4** — Each frame is enhanced individually using [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN), a neural network that reconstructs realistic details (skin texture, hair, fabric, etc.)
- ☀️ **Smart Brightness Fix** — Uses a photoshop-style luminosity curve to brighten shadows without blowing out highlights
- 🎞️ **Smooth Frame Interpolation** — Goes from choppy 13 fps to buttery smooth 30 fps
- 🔄 **Auto Rotation Fix** — Detects and corrects portrait/landscape orientation metadata
- 🔊 **Lossless Audio** — Original audio is preserved perfectly

---

## 📊 Before / After

| Property | Original | Enhanced |
|----------|----------|---------|
| Resolution | 640×368 | **2560×1472** (×4 AI) |
| FPS | ~13.81 fps | **30 fps** (smooth) |
| Bitrate | 465 kb/s | ~13,000 kb/s |
| Brightness | Dark / unreadable | Natural lighting |
| Orientation | Wrong rotation | Corrected |

---

## 🚀 Quick Start

### 1. Requirements

```bash
# FFmpeg (with full codecs)
sudo dnf install -y ffmpeg ffmpeg-libs   # Fedora/RHEL
# OR
sudo apt install -y ffmpeg               # Ubuntu/Debian
```

Download **Real-ESRGAN NCNN Vulkan** binary from the [official releases](https://github.com/xinntao/Real-ESRGAN/releases) and extract it.

### 2. Clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/video-ai-enhancer.git
cd video-ai-enhancer
```

### 3. Run

```bash
python3 enhance_video.py \
  --input  /path/to/your/video.mp4 \
  --output /path/to/output_enhanced.mp4 \
  --esrgan /path/to/realesrgan-ncnn-vulkan/
```

#### All options

```
--input    PATH     Input video file (required)
--output   PATH     Output video path (required)
--esrgan   PATH     Path to realesrgan-ncnn-vulkan directory (required)
--model    NAME     AI model to use (default: realesrgan-x4plus)
                      - realesrgan-x4plus         → Best for real photos/faces
                      - realesr-animevideov3-x4   → Faster, good for general video
--fps      INT      Output FPS (default: 30)
--gamma    FLOAT    Brightness gamma correction (default: 1.5)
--crf      INT      Output quality: 0=lossless, 51=worst (default: 15)
--keep     BOOL     Keep extracted frames after processing (default: False)
```

---

## 🧠 How It Works — Technical Pipeline

```
Input Video
    │
    ▼  [Step 1 — FFmpeg]
Extract real frames as PNG
(vsync=0, no duplicates)
    │
    ▼  [Step 2 — Real-ESRGAN NCNN Vulkan]
AI Enhancement × 4 per frame
  ┌─────────────────────────────┐
  │ RRDB Neural Network         │
  │ (23 Residual Dense Blocks)  │
  │                             │
  │ Input:  640×368 frame       │
  │ ↓ Encodes context           │
  │ ↓ Detects faces, textures   │
  │ ↓ Hallucinates fine details │
  │ Output: 2560×1472 frame     │
  └─────────────────────────────┘
    │
    ▼  [Step 3 — FFmpeg]
Reassemble + Audio + Fixes:
  - fps=30 (smooth interpolation)
  - curves (smart brightness)
  - libx264 CRF 15 (high quality)
    │
    ▼
Output Video (Enhanced)
```

---

## ⏱️ Processing Time

Depends on your GPU:

| Hardware | Time per frame | 300 frames total |
|----------|---------------|-----------------|
| NVIDIA RTX 3080 | ~2 sec | ~10 min |
| NVIDIA GTX 1060 | ~8 sec | ~40 min |
| Intel Iris Xe (integrated) | ~70 sec | ~6 hours |
| CPU only | ~5 min | ~25 hours |

> 💡 **Tip:** Run overnight for best results on integrated graphics.

---

## 📁 Project Structure

```
video-ai-enhancer/
├── enhance_video.py      # Main script
├── requirements.txt      # Python dependencies
├── LICENSE               # MIT License
└── README.md             # This file
```

---

## 🙏 Credits & Acknowledgments

This tool is a **wrapper/automation script** built on top of these amazing open-source projects:

| Project | Authors | License |
|---------|---------|---------|
| [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) | Xinntao Wang (Tencent ARC Lab) | BSD-3-Clause |
| [realesrgan-ncnn-vulkan](https://github.com/xinntao/Real-ESRGAN/releases) | nihui | MIT |
| [FFmpeg](https://ffmpeg.org) | FFmpeg Team | LGPL/GPL |

> **Note:** This project does NOT contain any AI model weights. Models are downloaded separately from the official Real-ESRGAN repository.

---

## 📄 License

This project (the automation script) is licensed under the MIT License — see [LICENSE](LICENSE) for details.

The AI models (Real-ESRGAN) are subject to their own licenses. Please refer to the [Real-ESRGAN repository](https://github.com/xinntao/Real-ESRGAN) for commercial use restrictions.

---

## 🌟 Star this repo if it helped you!
