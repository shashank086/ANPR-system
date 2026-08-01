# 🚗 SmartFuel ANPR System

> **Automatic Number Plate Recognition** — An AI-powered vehicle management and fueling system with real-time license plate detection, OCR, web dashboard, and cloud database sync.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Running the System](#-running-the-system)
- [Admin Account Setup](#-admin-account-setup)
- [Environment Variables](#-environment-variables)
- [API Endpoints](#-api-endpoints)
- [License](#-license)

---

## 🔍 Overview

SmartFuel ANPR is a complete, full-stack Automatic Number Plate Recognition system built for intelligent fuel station management. It uses **YOLOv8** for real-time vehicle/plate detection, **Tesseract OCR** + **EasyOCR** for plate reading, **Flask** as the web backend, and **MongoDB Atlas** for cloud data persistence.

The system supports live camera feeds, a web-based admin dashboard with analytics, user authentication, and a vehicle registry — all accessible through a browser.

---

## ✨ Features

- 🎯 **Real-time License Plate Detection** using YOLOv8
- 🔤 **Dual OCR Engine** — Tesseract OCR + EasyOCR for maximum accuracy
- 🌐 **Web Dashboard** — Live monitoring, analytics, and vehicle management
- ☁️ **MongoDB Atlas Integration** — Cloud-synced database with local JSON fallback
- 👤 **User Authentication** — Role-based access (Admin / User)
- 📊 **Performance Metrics API** — System health and detection statistics
- 🤖 **AI Integration** — Optional Google Gemini / Groq AI support
- 📅 **Scheduled Sync** — Automated background Atlas service
- 📁 **Structured Logging** — Full activity and error logging

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **AI / Detection** | YOLOv8 (Ultralytics), PyTorch, TorchVision |
| **OCR** | Tesseract OCR, EasyOCR |
| **Backend** | Python 3.11+, Flask |
| **Database** | MongoDB Atlas (cloud), JSON (local fallback) |
| **Image Processing** | OpenCV, Pillow, NumPy, SciPy, imutils |
| **AI Assistants** | Google Gemini API, Groq API (optional) |
| **Frontend** | HTML, CSS, JavaScript (Jinja2 templates) |
| **Utilities** | python-dotenv, pandas, psutil, schedule |

---

## 📁 Project Structure

```
ANPR/
├── backend/
│   ├── api/
│   │   ├── web_app.py          # Main Flask web application
│   │   └── app.py              # Flask app factory
│   ├── capture/                # Camera capture modules
│   ├── config/                 # Backend configuration
│   ├── database/               # Database connection & models
│   ├── models/                 # Data models
│   ├── processing/             # ANPR detection & OCR pipeline
│   ├── services/
│   │   └── atlas_service.py    # MongoDB Atlas sync service
│   ├── utils/                  # Helper utilities (user store, etc.)
│   └── main.py                 # Backend entry point
├── frontend/
│   ├── static/                 # CSS, JS, images
│   └── templates/              # Jinja2 HTML templates
├── config/                     # App-level configuration files
├── data/                       # Local data storage (users.json, etc.)
├── docs/                       # Documentation
├── logs/                       # Application logs
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
├── .env                        # Environment variables (not committed)
├── requirements.txt            # Python dependencies
├── start_anpr_system.bat       # One-click startup script
├── start_atlas_service.bat     # Atlas service startup script
├── update_admin.py             # Admin management utility
└── yolov8n.pt                  # YOLOv8 model weights
```

---

## ✅ Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.11+** — [Download here](https://www.python.org/downloads/)
2. **Tesseract OCR** — [Download here](https://github.com/UB-Mannheim/tesseract/wiki)
   - After installing, note the path (default: `C:\Program Files\Tesseract-OCR\tesseract.exe`) and add it to your `.env` file.
3. **Git** (optional, for cloning)
4. **MongoDB Atlas account** (optional, for cloud sync) — [Register here](https://www.mongodb.com/cloud/atlas)

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/shashank086/ANPR-system.git
cd ANPR-system
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

- **Windows:** `.venv\Scripts\activate.bat`
- **macOS/Linux:** `source .venv/bin/activate`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the `.env` template and fill in your values:

```bash
copy .env .env.backup   # optional backup
```

Edit `.env` with your settings (see [Environment Variables](#-environment-variables) below).

---

## 🚀 Running the System

### Option A — One-Click Startup (Recommended)

Simply double-click or run the startup script from the project root:

```bat
start_anpr_system.bat
```

This will automatically:
1. Activate the `.venv` virtual environment
2. Update all dependencies from `requirements.txt`
3. Launch the **MongoDB Atlas background service**
4. Start the **Flask web server** at `http://127.0.0.1:5000`

---

### Option B — Manual Startup (Two separate terminals)

**Terminal 1 — Atlas Sync Service:**

```cmd
.venv\Scripts\activate.bat
python backend/services/atlas_service.py
```

**Terminal 2 — Flask Web Application:**

```cmd
.venv\Scripts\activate.bat
python backend/api/web_app.py
```

---

### 🌐 Service URLs

| Service | URL |
|---|---|
| 🖥️ Web Dashboard | http://127.0.0.1:5000 |
| 📊 Performance Metrics API | http://127.0.0.1:5000/api/performance |
| 🔗 MongoDB Atlas Status | http://127.0.0.1:5000/api/atlas/status |

---

## 👤 Admin Account Setup

On **first startup**, the system seeds a default admin account:

| Field | Default Value |
|---|---|
| Username | `admin` |
| Password | `admin@123` |

> ⚠️ **Change the default credentials immediately after first login.**

There are multiple ways to add or promote admin accounts:

### Method 1 — Python Command Line

```python
from backend.utils.user_store import FileUserStore

store = FileUserStore()
store.create_user(
    username="your_admin_username",
    email="admin@example.com",
    date_of_birth="2000-01-01",
    password="your_secure_password",
    role="admin"   # <-- must be 'admin'
)
```

### Method 2 — Modify Default Seed

Edit `backend/utils/user_store.py` and change:

```python
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin@123"
```

### Method 3 — MongoDB Atlas (Compass / Shell)

```js
db.users.updateOne(
  { "username": "existing_username" },
  { "$set": { "role": "admin" } }
)
```

### Method 4 — Local JSON Fallback

Edit `data/users.json` and set the `"role"` field to `"admin"` for the target user.

---

## 🔐 Environment Variables

Create a `.env` file in the project root. Key variables:

```env
# Tesseract OCR path
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# MongoDB Atlas connection string
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/<dbname>

# Flask secret key
SECRET_KEY=your_secret_key_here

# Optional AI integrations
GOOGLE_API_KEY=your_google_gemini_key
GROQ_API_KEY=your_groq_api_key
```

> 🔒 The `.env` file is listed in `.gitignore` and will **never** be committed to the repository.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web dashboard home |
| `GET` | `/api/performance` | System performance metrics |
| `GET` | `/api/atlas/status` | MongoDB Atlas connection status |
| `POST` | `/login` | User authentication |
| `GET` | `/logout` | End user session |
| `GET` | `/admin` | Admin dashboard (admin only) |

---

## 📄 License

This project is intended for educational and research purposes.

---

<div align="center">
  <sub>Built with ❤️ using Python, Flask, YOLOv8, and MongoDB Atlas</sub>
</div>
