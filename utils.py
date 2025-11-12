
import os
import json
import time
import typing
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def ensure_upload_folder():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_uploaded_file(uploaded_file):
    """
    Save an uploaded file to the uploads directory and return path and local filename.
    """
    ensure_upload_folder()
    ts = int(time.time())
    safe_name = f"{ts}_{uploaded_file.name}"
    path = os.path.join(UPLOAD_FOLDER, safe_name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return safe_name, path

def generate_local_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

# --- Gemini helpers (generic, configurable) ---
def gemini_chat(system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
    """
    Generic helper to send a chat request to an LLM (Gemini or other).
    This function is intentionally generic — set GEMINI_API_KEY in .env to use a real endpoint.
    If no API key is present, returns a simple deterministic fallback response.

    NOTE: Adjust implementation to match your chosen LLM provider's API.
    """
    if not GEMINI_API_KEY:
        # Simple deterministic fallback to enable offline testing
        combined = f"{system_prompt}\n\nUSER: {user_prompt}"
        # Create a pseudo-response by hashing input (keeps deterministic)
        h = hashlib.sha256(combined.encode("utf-8")).hexdigest()[:160]
        return f"(local-fallback) Generated response preview: {h}\n\n[No GEMINI_API_KEY set — set GEMINI_API_KEY in .env to call a real LLM.]"
    # If an API key exists, call the provider.
    # NOTE: The actual HTTP call is left intentionally generic so that you can adapt it to the provider.
    # Example (pseudo):
    # headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}
    # payload = { "model": "gemini-1.5", "prompt": [{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}], "max_tokens": max_tokens }
    # r = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload)
    # return r.json()["choices"][0]["message"]["content"]
    # Since we don't call external services here, return a placeholder:
    return f"(API-key present) Received prompt. Would send to Gemini-like API. Prompt snippet: {user_prompt[:240]}"

def gemini_explain_file(filepath: str) -> str:
    """
    Extract a simple textual explanation or metadata summary for a file using LLM.
    If GEMINI_API_KEY not set, returns a fallback summary from file metadata.
    """
    if not os.path.exists(filepath):
        return "File not found."

    if not GEMINI_API_KEY:
        size = os.path.getsize(filepath)
        mtime = datetime.utcfromtimestamp(os.path.getmtime(filepath)).isoformat() + "Z"
        return f"(local-fallback) File: {os.path.basename(filepath)} — size: {size} bytes — last modified: {mtime}"

    # With a real key you'd send content or metadata to the LLM for summarization.
    return f"(API-key present) Would analyze file at {filepath} with Gemini-like API."

# Small helper for simple safe filenames
def sanitize_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in "-_. ").strip()
