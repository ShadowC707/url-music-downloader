# URL Music Downloader

A client-server application for downloading and processing audio from URLs.

## Architecture

*   **Frontend:** Static web interface hosted on GitHub Pages.
*   **Backend:** Asynchronous REST API built with Python and FastAPI, exposed via Localtunnel.
*   **Core Libraries:** `yt-dlp` (audio extraction), `aiofiles` (asynchronous I/O), `python-multipart` (form data parsing).

## Project Structure

```text
├── index.html                 # Frontend client interface (GitHub Pages)
└── backend/
    ├── Dockerfile             # Containerization configuration (optional)
    ├── downloader.py          # yt-dlp integration logic
    ├── main.py                # FastAPI application entry point and routing
    ├── requirements.txt       # Backend dependencies
    └── trimmer.py             # Audio processing and manipulation logic
```

## Setup and Execution

The current infrastructure relies on GitHub Pages serving the frontend static files, while the backend is executed locally and exposed to the public internet using `localtunnel`.


### 1. Backend Initialization

Navigate to the backend directory and install the required dependencies:

```Bash
cd backend
pip install -r requirements.txt
```

Start the FastAPI server:

```Bash
python -m uvicorn main:app --port 8000
```

### 2. Exposing the API

In a separate terminal, establish a tunnel to expose the local port 8000 to the public web. This is required for the GitHub Pages frontend to successfully route requests to your local machine.

```bash
npx localtunnel --port 8000 --subdomain url-music-dl
```

_Note: The frontend must be configured to point its API requests to the resulting Localtunnel URL (e.g., `https://url-music-dl.loca.lt`)._

### 3. Frontend Access

The frontend is deployed automatically via GitHub Pages. Navigate to your repository's GitHub Pages URL to access the client interface. Ensure the backend tunnel is running beforehand.