"""
DuckDB database layer for FaceFind.
Handles schema creation and all CRUD operations.
Thread-safe: uses a threading.Lock for all connection access.
"""

import duckdb
import os
import uuid
import bcrypt
import threading
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "data/facefind.duckdb")
_lock = threading.Lock()


def get_connection():
    """Open a fresh DuckDB connection (DuckDB handles WAL internally)."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return duckdb.connect(DB_PATH)


def init_db():
    """Initialize all tables if they don't exist and seed the default admin."""
    with _lock:
        conn = get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id          VARCHAR PRIMARY KEY,
                    email       VARCHAR UNIQUE NOT NULL,
                    name        VARCHAR,
                    password_hash VARCHAR NOT NULL,
                    role        VARCHAR DEFAULT 'user',
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS photos (
                    id                VARCHAR PRIMARY KEY,
                    filename          VARCHAR NOT NULL,
                    local_path        VARCHAR,
                    event_name        VARCHAR,
                    scene_label       VARCHAR,
                    scene_confidence  FLOAT,
                    detected_objects  VARCHAR,
                    face_count        INTEGER DEFAULT 0,
                    uploaded_by       VARCHAR,
                    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS face_matches (
                    id          VARCHAR PRIMARY KEY,
                    user_id     VARCHAR,
                    photo_id    VARCHAR,
                    confidence  FLOAT,
                    matched_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_logs (
                    id              VARCHAR PRIMARY KEY,
                    user_id         VARCHAR,
                    results_count   INTEGER,
                    scene_filter    VARCHAR,
                    searched_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Seed default admin
            admin_email = os.getenv("ADMIN_EMAIL", "admin@facefind.ai")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ?", [admin_email]
            ).fetchone()
            if not existing:
                pw_hash = bcrypt.hashpw(
                    admin_password.encode(), bcrypt.gensalt()
                ).decode()
                conn.execute(
                    "INSERT INTO users (id, email, name, password_hash, role) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [str(uuid.uuid4()), admin_email, "Admin", pw_hash, "admin"]
                )
        finally:
            conn.close()


# ── User helpers ──────────────────────────────────────────────────────────────

def create_user(email: str, name: str, password: str, role: str = "user") -> dict | None:
    with _lock:
        conn = get_connection()
        try:
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ?", [email]
            ).fetchone()
            if existing:
                return None
            uid = str(uuid.uuid4())
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO users (id, email, name, password_hash, role) "
                "VALUES (?, ?, ?, ?, ?)",
                [uid, email, name, pw_hash, role]
            )
            return {"id": uid, "email": email, "name": name, "role": role}
        finally:
            conn.close()


def verify_user(email: str, password: str) -> dict | None:
    with _lock:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT id, email, name, password_hash, role FROM users WHERE email = ?",
                [email]
            ).fetchone()
        finally:
            conn.close()
    if not row:
        return None
    uid, em, name, pw_hash, role = row
    if bcrypt.checkpw(password.encode(), pw_hash.encode()):
        return {"id": uid, "email": em, "name": name, "role": role}
    return None


# ── Photo helpers ─────────────────────────────────────────────────────────────

def insert_photo(filename: str, local_path: str, event_name: str,
                 scene_label: str, scene_confidence: float,
                 detected_objects: list, face_count: int,
                 uploaded_by: str) -> str:
    with _lock:
        conn = get_connection()
        try:
            photo_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO photos
                   (id, filename, local_path, event_name, scene_label,
                    scene_confidence, detected_objects, face_count, uploaded_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [photo_id, filename, local_path, event_name, scene_label,
                 scene_confidence, ",".join(detected_objects) if detected_objects else "",
                 face_count, uploaded_by]
            )
            return photo_id
        finally:
            conn.close()


def update_photo_face_count(photo_id: str, face_count: int):
    """Update the face_count on an already-inserted photo row."""
    with _lock:
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE photos SET face_count = ? WHERE id = ?",
                [face_count, photo_id]
            )
        finally:
            conn.close()


def get_photos_by_ids(photo_ids: list) -> list:
    if not photo_ids:
        return []
    with _lock:
        conn = get_connection()
        try:
            placeholders = ",".join(["?" for _ in photo_ids])
            rows = conn.execute(
                f"SELECT id, filename, local_path, event_name, scene_label, "
                f"detected_objects FROM photos WHERE id IN ({placeholders})",
                photo_ids
            ).fetchall()
        finally:
            conn.close()
    return [
        {
            "id": r[0], "filename": r[1], "local_path": r[2],
            "event_name": r[3], "scene_label": r[4],
            "detected_objects": r[5].split(",") if r[5] else []
        }
        for r in rows
    ]


def get_scene_counts(event_name: str = None) -> list:
    with _lock:
        conn = get_connection()
        try:
            if event_name:
                rows = conn.execute(
                    "SELECT scene_label, COUNT(*) as cnt FROM photos "
                    "WHERE event_name = ? GROUP BY scene_label ORDER BY cnt DESC",
                    [event_name]
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT scene_label, COUNT(*) as cnt FROM photos "
                    "GROUP BY scene_label ORDER BY cnt DESC"
                ).fetchall()
        finally:
            conn.close()
    return [{"scene": r[0], "count": r[1]} for r in rows]


def get_photos_by_scene(scene_label: str, event_name: str = None) -> list:
    with _lock:
        conn = get_connection()
        try:
            if event_name:
                rows = conn.execute(
                    "SELECT id, filename, local_path, event_name, scene_label, detected_objects "
                    "FROM photos WHERE scene_label = ? AND event_name = ?",
                    [scene_label, event_name]
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, filename, local_path, event_name, scene_label, detected_objects "
                    "FROM photos WHERE scene_label = ?",
                    [scene_label]
                ).fetchall()
        finally:
            conn.close()
    return [
        {
            "id": r[0], "filename": r[1], "local_path": r[2],
            "event_name": r[3], "scene_label": r[4],
            "detected_objects": r[5].split(",") if r[5] else []
        }
        for r in rows
    ]


def get_all_events() -> list:
    with _lock:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT event_name, COUNT(*) as photo_count, MIN(created_at) as created_at "
                "FROM photos GROUP BY event_name ORDER BY created_at DESC"
            ).fetchall()
        finally:
            conn.close()
    return [{"name": r[0], "photo_count": r[1], "created_at": str(r[2])} for r in rows]


def delete_event_photos(event_name: str):
    with _lock:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM face_matches WHERE photo_id IN "
                         "(SELECT id FROM photos WHERE event_name = ?)", [event_name])
            conn.execute("DELETE FROM photos WHERE event_name = ?", [event_name])
        finally:
            conn.close()


def get_photo_stats() -> dict:
    with _lock:
        conn = get_connection()
        try:
            total_photos   = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
            total_users    = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'user'").fetchone()[0]
            total_searches = conn.execute("SELECT COUNT(*) FROM search_logs").fetchone()[0]
            total_matches  = conn.execute("SELECT COUNT(*) FROM face_matches").fetchone()[0]
        finally:
            conn.close()
    return {
        "total_photos":   total_photos,
        "total_users":    total_users,
        "total_searches": total_searches,
        "total_matches":  total_matches
    }


def get_all_photo_ids_for_event(event_name: str) -> list:
    """Return all photo IDs for an event (used to rebuild FAISS)."""
    with _lock:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT id, local_path FROM photos WHERE event_name = ?", [event_name]
            ).fetchall()
        finally:
            conn.close()
    return [{"id": r[0], "local_path": r[1]} for r in rows]


def get_all_photos() -> list:
    """Return all photos (used to rebuild FAISS index from scratch)."""
    with _lock:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT id, local_path FROM photos ORDER BY created_at ASC"
            ).fetchall()
        finally:
            conn.close()
    return [{"id": r[0], "local_path": r[1]} for r in rows]


# ── Match / Log helpers ───────────────────────────────────────────────────────

def insert_face_match(user_id: str, photo_id: str, confidence: float):
    with _lock:
        conn = get_connection()
        try:
            existing = conn.execute(
                "SELECT id FROM face_matches WHERE user_id = ? AND photo_id = ?",
                [user_id, photo_id]
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO face_matches (id, user_id, photo_id, confidence) "
                    "VALUES (?, ?, ?, ?)",
                    [str(uuid.uuid4()), user_id, photo_id, confidence]
                )
        finally:
            conn.close()


def get_user_matched_photos(user_id: str) -> list:
    with _lock:
        conn = get_connection()
        try:
            rows = conn.execute(
                """SELECT p.id, p.filename, p.local_path, p.event_name, p.scene_label,
                          p.detected_objects, fm.confidence
                   FROM face_matches fm
                   JOIN photos p ON p.id = fm.photo_id
                   WHERE fm.user_id = ?
                   ORDER BY fm.matched_at DESC""",
                [user_id]
            ).fetchall()
        finally:
            conn.close()
    return [
        {
            "id": r[0], "filename": r[1], "local_path": r[2],
            "event_name": r[3], "scene_label": r[4],
            "detected_objects": r[5].split(",") if r[5] else [],
            "confidence": r[6]
        }
        for r in rows
    ]


def log_search(user_id: str, results_count: int, scene_filter: str = None):
    with _lock:
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO search_logs (id, user_id, results_count, scene_filter) "
                "VALUES (?, ?, ?, ?)",
                [str(uuid.uuid4()), user_id, results_count, scene_filter or ""]
            )
        finally:
            conn.close()
