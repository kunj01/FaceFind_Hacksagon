<div align="center">

<img src="https://img.shields.io/badge/FaceFind-AI%20Photo%20Discovery-FF7BBB?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0wIDE4Yy00LjQxIDAtOC0zLjU5LTgtOHMzLjU5LTggOC04IDggMy41OSA4IDgtMy41OSA4LTggOHoiLz48L3N2Zz4=&labelColor=0F1030"/>

# 🔍 FaceFind
### AI-Powered Smart Photo Discovery Platform

**Find yourself in thousands of event photos — in seconds.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![DeepFace](https://img.shields.io/badge/DeepFace-ArcFace-FF7BBB?style=flat-square)](https://github.com/serengil/deepface)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-A7CDFF?style=flat-square)](https://github.com/facebookresearch/faiss)
[![DuckDB](https://img.shields.io/badge/DuckDB-In--Process-FFF000?style=flat-square&logo=duckdb&logoColor=black)](https://duckdb.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<br/>

> Built for **Nirma Hackathon 2025** · Team **Code Titans**  
> Track: Software — Data Science & Machine Learning

<br/>

</div>

---

## 📌 The Problem

Large organizations — universities, corporate offices, event companies, public institutions — generate **thousands of photos** across multiple events. These are dumped into shared drives with no organization.

Users must **manually scroll through thousands of images** to find photos of themselves. This is:

- ❌ Inefficient and time-consuming
- ❌ Frustrating at scale (500+ attendees per event)
- ❌ Results in duplicate downloads wasting storage
- ❌ Completely unscalable across multiple events

**There is no intelligent system to help individuals find only their own photos.**

---

## 💡 The Solution

FaceFind is an **AI-powered Smart Photo Discovery Platform** that lets users find every photo of themselves across massive event collections using a single selfie.

```
Upload one selfie  →  AI scans thousands of photos  →  Get only YOUR photos
```

Instead of browsing 10,000 images manually, users get their results **in seconds**.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      ADMIN FLOW                          │
│                                                         │
│  Google Drive Link  →  Download Photos  →  AI Pipeline  │
│                              │                          │
│              ┌───────────────┴───────────────┐          │
│              ▼                               ▼          │
│      ┌──────────────┐              ┌──────────────────┐ │
│      │ Scene Engine │              │   Face Engine    │ │
│      │ CLIP + YOLO  │              │ ArcFace + FAISS  │ │
│      │ 10 categories│              │  512-d vectors   │ │
│      └──────┬───────┘              └────────┬─────────┘ │
│             └──────────────┬────────────────┘           │
│                            ▼                            │
│                    ┌──────────────┐                     │
│                    │   DuckDB     │                     │
│                    │  photos      │                     │
│                    │  users       │                     │
│                    │  embeddings  │                     │
│                    │  matches     │                     │
│                    └──────────────┘                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                      USER FLOW                           │
│                                                         │
│  Login  →  Upload Selfie  →  FAISS Global Search        │
│                                      │                  │
│                              Cosine Similarity          │
│                              Threshold Filter           │
│                                      │                  │
│                              ┌───────┴────────┐         │
│                              │ Matched Photos │         │
│                              │ Grouped by     │         │
│                              │ Event + Scene  │         │
│                              └───────┬────────┘         │
│                                      ▼                  │
│                            Display + Download           │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 🛠️ Admin Dashboard
| Feature | Description |
|---|---|
| 📁 Google Drive Upload | Paste any public Drive folder URL — bulk download instantly |
| 🧠 Scene Understanding | Auto-classifies photos into 10 scene types using CLIP + YOLOv8 |
| 👤 Face Embeddings | Extracts & indexes all faces with ArcFace (512-d vectors) |
| 📊 Live Progress | Real-time per-photo processing with scene breakdown analytics |
| 🗂️ Event Manager | Create, view, browse, and delete events |
| 📈 Platform Analytics | Global stats — photos, users, searches, match rates |

### 👤 User Dashboard
| Feature | Description |
|---|---|
| 🔐 Secure Auth | Register/Login with bcrypt password hashing |
| 🤳 Selfie Search | Upload one photo → find all your matches instantly |
| 🌍 Global Search | Search across ALL events simultaneously with one query |
| 🎭 Scene Filter | Narrow results by scene type (Award, Group Photo, Outdoor...) |
| 🎪 Event Filter | Search within a specific event |
| 🎚️ Sensitivity Slider | Adjustable match threshold for precision control |
| 📚 My Library | All previously matched photos in one place |
| ⬇️ Download | Per-photo and bulk ZIP download |

---

## 🧠 AI Stack

```
Face Recognition:  DeepFace (ArcFace backend) — 512-dimensional embeddings
Vector Search:     FAISS IndexFlatIP — cosine similarity, sub-second search
Scene Analysis:    CLIP ViT-B/32 — semantic scene understanding
Object Detection:  YOLOv8n — person/object detection for scene context
Database:          DuckDB — embedded SQL, zero infrastructure needed
```

### Why ArcFace?
ArcFace uses **Additive Angular Margin Loss** making it one of the most accurate face recognition models. It generates embeddings that are geometrically meaningful — faces of the same person cluster tightly in 512-d space regardless of lighting, angle, or expression.

### Why FAISS?
Facebook AI Similarity Search allows **sub-second nearest-neighbor search** across millions of face embeddings. Our global index searches ALL events simultaneously — one query, complete results.

---

## 🎭 Scene Categories

| Scene | Description |
|---|---|
| 🎤 Stage Performance | Person on stage with microphone and lights |
| 🏆 Award Ceremony | Trophy presentation and formal dress |
| 👥 Group Photo | Large group posing together |
| 🍽️ Dining Event | People eating at social gathering |
| 🌳 Outdoor Event | People gathered in outdoor setting |
| ⚽ Sports Event | Athletic activities and competitions |
| 🎓 Seminar / Talk | Listening to speaker or presentation |
| 📸 Candid Moment | Natural informal conversations |
| 🎭 Cultural Event | Dance, music, cultural performance |
| 🚪 Entrance / Lobby | Near entrance or registration desk |

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/facefind.git
cd facefind
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

> ⚠️ **First run downloads AI models (~1.5 GB)**  
> CLIP ViT-B/32, YOLOv8n, ArcFace — be patient on first launch.

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run the app
```bash
streamlit run app.py
```

Open → **http://localhost:8501**

---

## ⚙️ Environment Variables

```env
ADMIN_EMAIL=admin@facefind.ai
ADMIN_PASSWORD=admin123
DB_PATH=data/facefind.duckdb
FAISS_INDEX_PATH=data/faiss_index.bin
FAISS_GLOBAL_INDEX_PATH=data/faiss_global.bin
UPLOAD_DIR=data/uploads
```

---

## 📁 Project Structure

```
facefind/
├── app.py                      # Streamlit entry point + routing
├── requirements.txt
├── .env.example
│
├── pages/
│   ├── landing.py              # Landing page UI
│   ├── admin_dashboard.py      # Admin upload + analytics
│   └── user_dashboard.py       # User selfie search + library
│
├── services/
│   ├── face_engine.py          # DeepFace ArcFace + FAISS
│   ├── scene_engine.py         # CLIP + YOLOv8 scene classifier
│   └── drive_utils.py          # Google Drive bulk downloader
│
├── database/
│   └── db.py                   # DuckDB schema + all CRUD ops
│
├── components/
│   └── ui.py                   # Reusable UI components
│
└── data/                       # Auto-created on first run
    ├── facefind.duckdb
    ├── faiss_index.bin
    ├── faiss_global.bin
    └── uploads/
```

---

## 🎯 Demo Script (For Judges)

**Total demo time: ~3 minutes**

```
1. ADMIN TAB
   → Login with admin credentials
   → Paste a public Google Drive folder link
   → Watch live AI pipeline process photos
   → See scene breakdown chart populate in real time

2. USER TAB  
   → Register new account
   → Upload a selfie
   → Click "Find My Photos"
   → Watch FAISS return matched photos in <1 second

3. GLOBAL SEARCH
   → Upload any face photo
   → See results grouped by event across ALL uploads
   → Show match confidence percentage per photo

4. FILTERS
   → Select "Award Ceremony" scene filter
   → Search again — see filtered results
   → Download matched photos
```

---

## 🔐 Default Credentials

```
Admin Email:    admin@facefind.ai
Admin Password: admin123
```

---

## 📊 Performance

| Metric | Value |
|---|---|
| Face embedding generation | ~0.8s per photo |
| FAISS search (10K faces) | <50ms |
| FAISS search (100K faces) | <200ms |
| Scene classification | ~0.5s per photo |
| Bulk processing (100 photos) | ~2-3 minutes |

---

## 🔮 Future Roadmap

- [ ] Next.js full-stack rebuild with TypeScript
- [ ] Real-time processing with WebSocket progress
- [ ] AWS Rekognition integration for enterprise scale
- [ ] Mobile app with camera capture
- [ ] Privacy controls — right to be forgotten
- [ ] Multi-tenant organization accounts
- [ ] Automated duplicate detection and deduplication
- [ ] Export to ZIP with metadata

---

## ⚠️ Limitations & Ethical Considerations

**Technical Limitations:**
- Face recognition accuracy reduces with low-quality or poorly lit images
- Initial processing time is high for very large photo datasets (1000+ photos)
- Requires significant compute for large-scale deployment

**Ethical Considerations:**
- Privacy and data protection require explicit user consent
- Biometric data usage is subject to regional regulations (GDPR, etc.)
- System should never be used for surveillance or tracking without consent
- All facial data should be encrypted at rest

---

## 👥 Team — Code Titans

| Member | Role |
|---|---|
| **Kunj** | AI/ML + Backend + Full Stack |
| **Riya Navadia** | UI/UX + Frontend |
| **Disha Vekaria** | Research + Documentation |

---

## 🏆 Built For

**Nirma Hackathon 2025**  
Track: Software — Data Science & Machine Learning  
Theme: AI-powered solutions for real-world organizational problems

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ by Code Titans**

*FaceFind — Because every moment deserves to be found.*

[![Star this repo](https://img.shields.io/github/stars/YOUR_USERNAME/facefind?style=social)](https://github.com/YOUR_USERNAME/facefind)

</div>
