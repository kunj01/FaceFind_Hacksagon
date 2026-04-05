"""
Google Drive utilities for FaceFind.
Downloads images from a public Google Drive folder link.

Strategy (most-reliable first):
  1. gdown.download_folder  — works for most public folders
  2. gdown per-file fallback — for virus-scan-blocked files
  3. requests direct download — plain public files
"""

import os
import re
import requests
import gdown
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


# ── URL helpers ───────────────────────────────────────────────────────────────

def extract_folder_id(drive_url: str) -> str | None:
    """Extract Google Drive folder ID from various URL formats."""
    patterns = [
        r"folders/([a-zA-Z0-9_-]{25,})",
        r"id=([a-zA-Z0-9_-]{25,})",
        r"open\?id=([a-zA-Z0-9_-]{25,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, drive_url)
        if match:
            return match.group(1)
    return None


def extract_file_id(drive_url: str) -> str | None:
    """Extract file ID from a Google Drive file URL."""
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]{25,})",
        r"id=([a-zA-Z0-9_-]{25,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, drive_url)
        if match:
            return match.group(1)
    return None


# ── Session pool for faster downloads ─────────────────────────────────────────

_session_lock = threading.Lock()
_sessions = {}

def _get_session():
    """Get or create a thread-local requests session with aggressive connection pooling."""
    thread_id = threading.get_ident()
    if thread_id not in _sessions:
        session = requests.Session()
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        # AGGRESSIVE retry strategy
        retry = Retry(
            total=1,  # Only 1 retry
            backoff_factor=0.1,  # Very short backoff
            status_forcelist=[429, 500, 502, 503, 504]
        )
        # MASSIVE connection pooling
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=20,  # Up from 10
            pool_maxsize=20  # Up from 10
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        _sessions[thread_id] = session
    return _sessions[thread_id]


# ── Single-file download (handles virus-scan confirmation) ────────────────────

def _download_file_with_confirm(file_id: str, dest_path: str) -> bool:
    """
    Download a single Drive file using PURE REQUESTS (no gdown overhead).
    Returns True on success. ULTRA-OPTIMIZED for speed.
    """
    try:
        session = _get_session()
        
        # Direct Google Drive download URL
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        # First request with NO timeout initially, then check response
        response = session.get(url, stream=True, timeout=8, allow_redirects=True)

        # If HTML response (virus scan page), extract confirm token
        if response.status_code == 200 and "text/html" in response.headers.get("Content-Type", ""):
            # Try to extract confirm token from HTML
            confirm_match = re.search(r'confirm=([0-9A-Za-z_]+)', response.text)
            if confirm_match:
                confirm_token = confirm_match.group(1)
                url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={confirm_token}"
                response = session.get(url, stream=True, timeout=12, allow_redirects=True)

        # Check if we got the file
        content_type = response.headers.get("Content-Type", "")
        content_length = response.headers.get("Content-Length", 0)
        
        if response.status_code == 200:
            # Write file with LARGE chunks
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1048576):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
            
            # Verify file size
            size = Path(dest_path).stat().st_size
            if size > 500:  # At least 500 bytes
                return True
            else:
                try:
                    os.unlink(dest_path)
                except:
                    pass
    except Exception:
        pass

    return False


# ── Folder listing via gdown internals ────────────────────────────────────────

def _list_folder_files(folder_id: str) -> list[dict]:
    """
    Return list of {name, id} dicts for image files in a public Drive folder.
    Uses gdown's internal folder listing (no API key needed).
    """
    try:
        import gdown.download_folder as gdf
        # gdown >= 4.7 exposes _get_session and _parse_google_drive_file
        files_and_dirs = gdf._parse_google_drive_file(
            url=f"https://drive.google.com/drive/folders/{folder_id}",
            remaining_ok=True,
        )
        result = []
        if files_and_dirs:
            for item in files_and_dirs:
                # item is a GoogleDriveFile namedtuple: (id, name, mime_type, ...)
                name = getattr(item, "name", "")
                fid  = getattr(item, "id", "")
                if any(name.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                    result.append({"id": fid, "name": name})
        return result
    except Exception:
        return []


# ── Main downloader ───────────────────────────────────────────────────────────

def _cleanup_partial_files(directory: str):
    """Remove any leftover .part temp files that gdown leaves on Windows."""
    try:
        for f in Path(directory).rglob("*.part"):
            try:
                f.unlink()
            except Exception:
                pass
    except Exception:
        pass


def download_drive_folder(
    drive_url: str,
    event_name: str,
    progress_callback=None,
) -> list[str]:
    """
    Download all images from a Google Drive folder URL (ULTRA-FAST).

    Strategy:
      1. Scrape folder HTML for file IDs (no gdown overhead)
      2. Parallel download with 8-12 concurrent workers
      3. Aggressive timeout handling with fallback retries

    Args:
        drive_url: Publicly shared Google Drive folder URL
        event_name: Organise downloads under this event sub-directory
        progress_callback: Optional callable(current, total, filename)

    Returns:
        Sorted list of local image file paths
    """
    folder_id = extract_folder_id(drive_url)
    if not folder_id:
        raise ValueError(f"Could not extract folder ID from URL: {drive_url}")

    dest_dir = Path(UPLOAD_DIR) / event_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Always clean orphaned .part files before starting
    _cleanup_partial_files(str(dest_dir))

    downloaded_paths: list[str] = []

    # ── Strategy 1: FAST folder scraping (no gdown overhead) ───────────────
    file_list = []
    
    try:
        resp = _get_session().get(
            f"https://drive.google.com/drive/folders/{folder_id}",
            timeout=8,
        )
        # Extract all file IDs from Drive's embedded JSON
        raw_ids = re.findall(r'"([a-zA-Z0-9_-]{25,40})"', resp.text)
        seen = set()
        for fid in raw_ids:
            if fid not in seen and fid != folder_id:
                seen.add(fid)
                file_list.append({"id": fid, "name": f"photo_{len(file_list)}.jpg"})
            if len(file_list) >= 500:  # Cap at 500 files
                break
    except Exception as e:
        pass

    if not file_list:
        raise RuntimeError(
            "No images found or folder is not accessible.\n\n"
            "Common fixes:\n"
            "• Make sure folder is set to 'Anyone with the link can view'\n"
            "• Try the 'Upload from Computer' tab (faster & more reliable)\n"
            f"\nFolder tested: https://drive.google.com/drive/folders/{folder_id}"
        )

    # ── Aggressive Parallel Download (16-20 concurrent workers) ────────────
    download_lock = threading.Lock()
    completed_count = [0]
    
    def download_task(f_info: dict, index: int) -> tuple[str | None, str]:
        """Download single file - returns (path, name) or (None, name)."""
        name = f_info.get("name", f"photo_{index}.jpg")
        if not any(name.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
            name += ".jpg"
        
        dest_path = str(dest_dir / name)
        
        # Try twice quickly, fail fast
        for attempt in range(2):
            try:
                success = _download_file_with_confirm(f_info["id"], dest_path)
                if success:
                    with download_lock:
                        completed_count[0] += 1
                        if progress_callback:
                            progress_callback(completed_count[0], len(file_list), name)
                    return (dest_path, name)
            except Exception:
                pass
        
        with download_lock:
            completed_count[0] += 1
        return (None, name)

    # Use 16-20 workers for ULTRA-AGGRESSIVE parallel downloads
    max_workers = min(20, len(file_list))  # Up to 20 concurrent downloads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_task, f_info, i): f_info
            for i, f_info in enumerate(file_list)
        }
        
        for future in as_completed(futures):
            try:
                path, name = future.result()
                if path:
                    downloaded_paths.append(path)
            except Exception:
                pass

    if not downloaded_paths:
        raise RuntimeError(
            "Download failed. Possible reasons:\n"
            "• Google Drive rate limiting (try again in 1 hour)\n"
            "• Network connection too slow\n"
            "• Use 'Upload from Computer' tab instead\n"
            f"\nFolder: https://drive.google.com/drive/folders/{folder_id}"
        )

    return sorted(downloaded_paths)


# ── Single-image download (selfie via Drive link) ─────────────────────────────

def download_single_image(drive_url: str, save_dir: str, filename: str = "selfie.jpg") -> str:
    """Download a single image from a Google Drive file URL."""
    file_id = extract_file_id(drive_url)
    if not file_id:
        raise ValueError(f"Could not extract file ID from: {drive_url}")
    os.makedirs(save_dir, exist_ok=True)
    output_path = os.path.join(save_dir, filename)
    _download_file_with_confirm(file_id, output_path)
    return output_path


def get_event_image_count(event_name: str) -> int:
    """Count images already downloaded for an event."""
    dest_dir = Path(UPLOAD_DIR) / event_name
    if not dest_dir.exists():
        return 0
    return sum(
        1 for f in dest_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    )
