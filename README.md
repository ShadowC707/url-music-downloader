# 🎵 URL Music Downloader & Audio Trimmer

A fast, asynchronous web application that allows users to download audio tracks from online URLs and trim them to specific time intervals. 

Built with a high-performance **FastAPI** backend and powered by **yt-dlp**, this tool provides a lightweight frontend interface for quick media processing without requiring complex desktop software.

---

## ✨ Features

- **Direct URL Downloading:** Extracts high-quality audio streams from supported media URLs via integrated `yt-dlp`.
- **Audio Trimming:** Built-in audio cutting functionality (`trimmer.py`) allowing users to crop tracks by specifying start and end timestamps.
- **Asynchronous File Handling:** Utilizes non-blocking I/O operations (`aiofiles`) for smooth media processing and streaming.
- **Lightweight Frontend:** Simple, responsive HTML/JS user interface (`frontend/index.html`) to input URLs, manage trim parameters, and trigger downloads.
- **Docker Ready:** Includes a Docker setup for seamless backend deployment.

---

## 🛠️ Tech Stack

- **Backend:**
  - **Framework:** [FastAPI](https://fastapi.tiangolo.com/) with Uvicorn server
  - **Media Extraction:** [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)
  - **Async I/O:** `aiofiles`, `python-multipart`
- **Frontend:**
  - Custom HTML5 / CSS / Vanilla JavaScript (`frontend/index.html`)
- **DevOps:**
  - Docker (`backend/Dockerfile`)

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- *(Optional)* **FFmpeg**: Required on your system path if advanced audio conversion or trimming requires external encoding support.

---
### 1. Local Installation & Run

#### Step 1: Set up the Backend
1. **Clone the repository:**
```bash
   git clone [https://github.com/ShadowC707/url-music-downloader.git](https://github.com/ShadowC707/url-music-downloader.git)
   cd url-music-downloader/backend
```

2. **Create and activate a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```


3. **Install dependencies:**
```bash
pip install -r requirements.txt
```


4. **Start the FastAPI API server:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```


*The interactive Swagger API documentation will be available at `http://localhost:8000/docs`.*

#### Step 2: Launch the Frontend

Simply open `frontend/index.html` in any web browser, or serve the directory using a lightweight HTTP server:

```bash
# From the project root
python -m http.server 3000
```

Then navigate to `http://localhost:3000/frontend/index.html`.

---

### 2. Running with Docker

You can easily containerize and run the backend API service using the included Dockerfile:

```bash
# Navigate to the backend directory
cd backend

# Build the Docker image
docker build -t url-music-downloader-backend .

# Run the container on port 8000
docker run -p 8000:8000 url-music-downloader-backend
```

---
## 📁 Project Structure

```text
├── backend/
│   ├── Dockerfile         # Container configuration for API service
│   ├── main.py            # FastAPI application entry point & endpoints
│   ├── downloader.py      # Audio extraction logic using yt-dlp
│   ├── trimmer.py         # Media cutting and interval trimming logic
│   └── requirements.txt   # Backend dependencies
└── frontend/
    └── index.html         # User Interface
```

---
## 🔌 API Endpoints (Overview)

When the FastAPI server is running, you can inspect and test endpoints directly via the OpenAPI UI at `/docs`. Core features include:

* `POST /download` — Accepts a target media URL and downloads the processed audio stream.
* `POST /trim` — Trims an audio file based on custom timestamps.

---
## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page or submit a pull request.