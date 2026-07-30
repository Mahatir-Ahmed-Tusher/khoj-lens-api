from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Any
import os
import asyncio
import traceback

# Import the library's public classes
# Note: This wrapper expects PicImageSearch package to be available in the environment.
# If your repo includes PicImageSearch as a submodule or dependency, ensure it's installed.
from PicImageSearch import (
    Network,
    SauceNAO,
    Yandex,
    Bing,
    GoogleLens,
    TraceMoe,
    Tineye,
    Ascii2D,
    Iqdb,
    BaiDu,
    Copyseeker,
    EHentai,
    Lenso,
    AnimeTrace,
)

app = FastAPI(title="PicimageSearch API")

# Map string names to classes exposed by the package
ENGINE_MAP = {
    "saucenao": SauceNAO,
    "yandex": Yandex,
    "bing": Bing,
    "google_lens": GoogleLens,
    "tracemoe": TraceMoe,
    "tineye": Tineye,
    "ascii2d": Ascii2D,
    "iqdb": Iqdb,
    "baidu": BaiDu,
    "copyseeker": Copyseeker,
    "ehentai": EHentai,
    "lenso": Lenso,
    "animetrace": AnimeTrace,
}

# Helper: turn objects into JSON-serializable data
def to_primitive(obj: Any):
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: to_primitive(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_primitive(i) for i in obj]
    # Try dataclass / model-like object
    if hasattr(obj, "__dict__"):
        data = {}
        for k, v in vars(obj).items():
            data[k] = to_primitive(v)
        return data
    # Fallback to string
    return str(obj)


async def run_engine_search(engine_name: str, engine_kwargs: dict, url: Optional[str], file_bytes: Optional[bytes]):
    """Instantiate engine and run search. Returns (engine_name, result_or_error)."""
    cls = ENGINE_MAP.get(engine_name.lower())
    if cls is None:
        return engine_name, {"error": f"Unsupported engine: {engine_name}"}

    # Merge environment-provided API keys into engine kwargs when present
    # e.g., SAUCENAO_API_KEY -> api_key
    # Common patterns: <ENGINE>_API_KEY
    env_key = os.getenv(engine_name.upper() + "_API_KEY")
    if env_key and "api_key" not in engine_kwargs:
        engine_kwargs["api_key"] = env_key

    # For Google Lens the repo uses `cookies` param in demos
    if engine_name.lower() == "google_lens":
        google_cookies = os.getenv("GOOGLE_COOKIES")
        if google_cookies:
            engine_kwargs.setdefault("cookies", google_cookies)

    # If proxies are provided globally, pass them
    proxies = os.getenv("PROXIES")
    if proxies:
        engine_kwargs.setdefault("proxies", proxies)

    try:
        engine = cls(**engine_kwargs)
        # If the engine's search method expects async, call it directly (it is async)
        if url:
            resp = await engine.search(url=url)
        else:
            # pass raw bytes; library accepts bytes for `file`
            resp = await engine.search(file=file_bytes)
        return engine_name, to_primitive(resp)
    except Exception as e:
        tb = traceback.format_exc()
        return engine_name, {"error": str(e), "traceback": tb}


@app.post("/search")
async def search(
    engines: Optional[str] = Form("all"),
    image_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    timeout_seconds: Optional[int] = Form(30),
):
    """Search image using one or multiple engines.

    Form fields:
    - engines: comma-separated engine names (default "all")
    - image_url: URL to image
    - file: multipart file upload
    - timeout_seconds: how long to wait for all engines (per request)

    Returns JSON mapping engine -> result (or error).
    """

    # Sanitize and validate image_url input
    if image_url:
        image_url = image_url.strip()
        if image_url.lower() in ("string", "") or not (image_url.startswith("http://") or image_url.startswith("https://")):
            image_url = None

    if not image_url and (file is None or not file.filename):
        raise HTTPException(
            status_code=400, 
            detail="Either a valid image_url (starting with http:// or https://) or an uploaded file must be provided"
        )


    if engines == "all":
        engine_list = list(ENGINE_MAP.keys())
    else:
        engine_list = [e.strip() for e in engines.split(",") if e.strip()]

    file_bytes = None
    if file is not None:
        file_bytes = await file.read()

    # Create tasks for all requested engines. Each engine will be invoked with optional API key loaded from env.
    tasks = [run_engine_search(e, {}, image_url, file_bytes) for e in engine_list]

    # Run with timeout
    try:
        results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        # If timeout, cancel pending tasks and return partial results
        for t in tasks:
            try:
                t.cancel()
            except Exception:
                pass
        raise HTTPException(status_code=504, detail="Search timeout")

    # Convert to dict
    out = {name: result for (name, result) in results}
    return JSONResponse(out)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Welcome to Khoj Lens API!",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}

