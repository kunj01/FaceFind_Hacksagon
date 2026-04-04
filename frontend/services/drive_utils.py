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


# ── Single-file download (handles virus-scan confirmation) ────────────────────

def _download_file_with_confirm(file_id: str, dest_path: str) -> bool:
    """
    Download a single Drive file, handling Google's virus-scan warning page.
    Returns True on success.
    """
    # Try gdown first (handles confirm token automatically)
    try:
        result = gdown.download(
            id=file_id,
            output=dest_path,
            quiet=True,
            fuzzy=True,
        )
        if result and Path(result).exists() and Path(result).stat().st_size > 0:
            return True
    except Exception:
        pass

    # Fallback: requests with confirm token
    try:
        session = requests.Session()
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = session.get(url, stream=True, timeout=30)

        # Check for virus-scan confirmation page
        if "confirm=" in response.text or "download_warning" in response.url:
            confirm_match = re.search(r"confirm=([0-9A-Za-z_]+)", response.text)
            if confirm_match:
                confirm_token = confirm_match.group(1)
                url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={confirm_token}"
                response = session.get(url, stream=True, timeout=60)

        # Write file if content looks like an image
        content_type = response.headers.get("Content-Type", "")
        if response.status_code == 200 and (
            "image" in content_type or "octet-stream" in content_type
        ):
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=32768):
                    f.write(chunk)
            if Path(dest_path).stat().st_size > 1000:
                return True
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
    Download all images from a Google Drive folder URL.

    Tries these strategies in order:
      1. gdown.download_folder (bulk, fastest)
      2. Per-file download using folder listing
      3. Raises RuntimeError if nothing downloaded

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

    # Always clean orphaned .part files before starting (avoids WinError 32)
    _cleanup_partial_files(str(dest_dir))

    downloaded_paths: list[str] = []

    # ── Strategy 1: gdown.download_folder ────────────────────────────────
    try:
        gdown.download_folder(
            id=folder_id,
            output=str(dest_dir),
            quiet=False,
            use_cookies=False,
            remaining_ok=True,
        )
        for f in dest_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                downloaded_paths.append(str(f))
    except OSError as e:
        if e.winerror == 32:   # file locked (WinError 32) — clean and continue
            _cleanup_partial_files(str(dest_dir))
        downloaded_paths = []  # reset, try per-file strategy
    except Exception:
        downloaded_paths = []  # reset, try per-file strategy

    if downloaded_paths:
        if progress_callback:
            for i, p in enumerate(downloaded_paths):
                progress_callback(i + 1, len(downloaded_paths), Path(p).name)
        return sorted(downloaded_paths)

    # ── Strategy 2: Per-file with confirmation handling ───────────────────
    file_list = _list_folder_files(folder_id)

    if not file_list:
        # Last-ditch: try fetching the folder HTML and scraping IDs
        try:
            resp = requests.get(
                f"https://drive.google.com/drive/folders/{folder_id}",
                timeout=20,
            )
            # Drive embeds file IDs in JSON-like data attributes
            raw_ids = re.findall(r'"([a-zA-Z0-9_-]{25,40})"', resp.text)
            seen = set()
            for fid in raw_ids:
                if fid not in seen and fid != folder_id:
                    seen.add(fid)
                    file_list.append({"id": fid, "name": f"image_{len(file_list)}.jpg"})
                if len(file_list) >= 200:
                    break
        except Exception:
            pass

    total = len(file_list)
    for i, f_info in enumerate(file_list):
        name = f_info.get("name", f"photo_{i}.jpg")
        # Ensure has image extension
        if not any(name.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
            name += ".jpg"
        dest_path = str(dest_dir / name)
        success = _download_file_with_confirm(f_info["id"], dest_path)
        if success:
            downloaded_paths.append(dest_path)
        if progress_callback:
            progress_callback(i + 1, total or 1, name)

    if not downloaded_paths:
        raise RuntimeError(
            "No images could be downloaded from Google Drive.\n\n"
            "Common fixes:\n"
            "• Make sure the folder is set to 'Anyone with the link can view'\n"
            "• Try the 'Upload from Computer' tab (more reliable for demos)\n"
            "• Avoid folders with >100 files on first attempt (Drive rate-limits)\n"
            f"\nDirect folder link tested: "
            f"https://drive.google.com/drive/folders/{folder_id}"
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
