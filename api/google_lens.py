import os
from typing import Optional, Dict, Any, List
import httpx
from loguru import logger
from dotenv import load_dotenv

# Ensure environment variables from .env are loaded
load_dotenv()

IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")

SERP_API_KEYS: List[str] = []
for i in range(1, 12):
    key = os.getenv(f"SERP_API_KEY_{i}")
    if key and key.strip():
        SERP_API_KEYS.append(key.strip())

# Fallback check if single SERP_API_KEY is provided
if not SERP_API_KEYS:
    fallback_key = os.getenv("SERP_API_KEY")
    if fallback_key:
        SERP_API_KEYS.append(fallback_key.strip())

# Shared persistent HTTP client instance
http_client = httpx.AsyncClient(timeout=20.0, follow_redirects=True)


async def upload_to_imgbb(file_bytes: bytes) -> str:
    """Uploads local image bytes to ImgBB and returns the public image URL.
    
    Raises Exception if upload fails or key is missing.
    """
    if not IMGBB_API_KEY:
        raise ValueError("IMGBB_API_KEY is missing in environment variables.")

    url = f"https://api.imgbb.com/1/upload?expiration=600&key={IMGBB_API_KEY}"
    files = {"image": ("search_image.jpg", file_bytes, "image/jpeg")}
    
    response = await http_client.post(url, files=files)
    if response.status_code != 200:
        raise RuntimeError(f"ImgBB upload failed with HTTP {response.status_code}: {response.text}")
    
    res_json = response.json()
    if not res_json.get("success"):
        raise RuntimeError(f"ImgBB upload rejected: {res_json}")
    
    public_url = res_json.get("data", {}).get("url")
    if not public_url:
        raise RuntimeError("ImgBB upload succeeded but no URL was returned.")
        
    return public_url


async def search_google_lens(url: Optional[str] = None, file_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """Executes Google Lens reverse search via SerpApi with automated 11-key fallback.
    
    Uploads local image bytes to ImgBB once if no direct URL is provided.
    Returns dict formatted as: {"visual_matches": [{ "title": ..., "url": ..., "thumbnail": ..., "source": ... }]}
    """
    if not SERP_API_KEYS:
        return {"error": "No SERP_API_KEY entries found in environment."}

    # Step 1: Resolve public image URL
    public_image_url = url
    if not public_image_url and file_bytes:
        try:
            logger.info("Uploading image file to ImgBB for Google Lens search...")
            public_image_url = await upload_to_imgbb(file_bytes)
            logger.info(f"ImgBB upload successful: {public_image_url}")
        except Exception as e:
            logger.error(f"ImgBB upload error: {e}")
            return {"error": f"Failed to upload image for Google Lens: {str(e)}"}

    if not public_image_url:
        return {"error": "Neither image_url nor valid uploaded file was provided for Google Lens search."}

    # Step 2: Sequential SerpApi Key Fallback Rotation
    for index, api_key in enumerate(SERP_API_KEYS, start=1):
        logger.info(f"Attempting SerpApi Google Lens search with Key #{index} ({api_key[:8]}...)")
        
        try:
            params = {
                "engine": "google_lens",
                "url": public_image_url,
                "api_key": api_key
            }
            resp = await http_client.get("https://serpapi.com/search.json", params=params)

            if resp.status_code == 200:
                data = resp.json()
                
                # Check if SerpApi returned an error in payload
                if "error" in data:
                    err_msg = str(data["error"])
                    err_lower = err_msg.lower()
                    
                    # Quota / Key invalid / rate limit failure -> Try next key
                    if any(term in err_lower for term in ["key", "limit", "quota", "searches", "unauthorized", "invalid", "run out"]):
                        logger.warning(f"SerpApi Key #{index} failed with quota/key error: '{err_msg}'. Rotating to next key...")
                        continue
                    else:
                        # Malformed request -> Do not retry other keys
                        logger.error(f"SerpApi Bad Request: '{err_msg}'")
                        return {"error": f"SerpApi Error: {err_msg}"}

                # Extract and format visual matches
                raw_matches = data.get("visual_matches", [])
                formatted_matches = []
                for match in raw_matches:
                    if not isinstance(match, dict):
                        continue
                    formatted_matches.append({
                        "title": match.get("title", ""),
                        "url": match.get("link", "") or match.get("url", ""),
                        "thumbnail": match.get("thumbnail") or match.get("image", ""),
                        "source": match.get("source", ""),
                        "similarity": None
                    })

                logger.info(f"SerpApi Google Lens search successful with Key #{index}. Found {len(formatted_matches)} visual matches.")
                return {
                    "visual_matches": formatted_matches,
                    "raw": formatted_matches,
                    "results": formatted_matches
                }


            elif resp.status_code in (401, 402, 403, 429):
                logger.warning(f"SerpApi Key #{index} returned HTTP {resp.status_code}. Rotating to next key...")
                continue
            elif resp.status_code == 400:
                logger.error(f"SerpApi HTTP 400 Bad Request: {resp.text}")
                return {"error": f"SerpApi Bad Request (400): {resp.text}"}
            else:
                logger.warning(f"SerpApi Key #{index} returned unexpected HTTP {resp.status_code}. Rotating to next key...")
                continue

        except Exception as e:
            logger.warning(f"Network error querying SerpApi with Key #{index}: {e}. Trying next key...")
            continue

    return {"error": "All configured SERP_API_KEY entries failed or reached their query limits."}
