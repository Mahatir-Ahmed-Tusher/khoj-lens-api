# Khoj Lens API

A FastAPI wrapper for `PicImageSearch`, providing a unified reverse image search API (Google Lens, Yandex, Bing, TinEye, SauceNAO, etc.).

## Requirements
- Python 3.10+
- Dependencies listed in `requirements.txt`

## Local Setup & Run

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run API server:**
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

3. **Access API docs:**
   Open http://localhost:8000/docs in your browser.

## Docker Setup

1. **Build Docker image:**
   ```bash
   docker build -t khoj-lens-api .
   ```

2. **Run container:**
   ```bash
   docker run -p 8000:8000 khoj-lens-api
   ```

## Deploying to Koyeb

1. Push this repository to GitHub.
2. Log in to [Koyeb](https://app.koyeb.com/).
3. Click **Create App** and select **GitHub**.
4. Choose your repository and set the Builder to **Dockerfile**.
5. Change the exposed Port to **8000**.
6. Set any optional Environment Variables (e.g., `SAUCENAO_API_KEY`, `GOOGLE_COOKIES`).
7. Click **Deploy**.
