PicImageSearch API wrapper

This directory provides a minimal FastAPI HTTP wrapper for the PicImageSearch library so you can deploy it as a web service.

Environment variables
- PROXIES: optional global proxy (e.g. http://127.0.0.1:1080)
- GOOGLE_COOKIES: (optional) cookie string for Google Lens usage (see demo code)
- <ENGINE>_API_KEY: e.g., SAUCENAO_API_KEY, BAIDU_API_KEY — the wrapper will pass these to engine constructors if present.

Endpoints
- POST /search (form-data)
  - engines: comma-separated engine names (default: "all")
  - image_url: URL of image to search
  - file: multipart file upload
  - timeout_seconds: total timeout in seconds (default 30)

- GET /health

Usage
- Build Docker image and deploy to Koyeb / any container host.
