"""
DuckDB database layer for FaceFind.
Handles schema creation and all CRUD operations.
"""

import duckdb
import os
import uuid
import bcrypt
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "data/facefind.duckdb")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = duckdb.connect(DB_PATH)
    conn.execute("PRAGMA memory_limit='2GB'")
    conn.execute("PRAGMA threads=4")
    return conn


def init_db():
    """Initialize all tables if they don't exist."""
    conn = get_connection()
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

    # Ensure default admin exists
    admin_email = os.getenv("ADMIN_EMAIL", "admin@facefind.ai")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", [admin_email]
    ).fetchone()
    if not existing:
        pw_hash = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (id, email, name, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            [str(uuid.uuid4()), admin_email, "Admin", pw_hash, "admin"]
        )
    conn.close()


# ── User helpers ─────────────────────────────────────────────────────────────

def create_user(email: str, name: str, password: str, role: str = "user") -> dict | None:
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", [email]).fetchone()
    if existing:
        conn.close()
        return None
    uid = str(uuid.uuid4())
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT INTO users (id, email, name, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        [uid, email, name, pw_hash, role]
    )
    conn.close()
    return {"id": uid, "email": email, "name": name, "role": role}


def verify_user(email: str, password: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT id, email, name, password_hash, role FROM users WHERE email = ?", [email]
    ).fetchone()
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
    conn = get_connection()
    photo_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO photos
           (id, filename, local_path, event_name, scene_label, scene_confidence,
            detected_objects, face_count, uploaded_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [photo_id, filename, local_path, event_name, scene_label,
         scene_confidence, ",".join(detected_objects), face_count, uploaded_by]
    )
    conn.close()
    return photo_id


def get_photos_by_ids(photo_ids: list) -> list:
    if not photo_ids:
        return []
    conn = get_connection()
    placeholders = ",".join(["?" for _ in photo_ids])
    rows = conn.execute(
        f"SELECT id, filename, local_path, event_name, scene_label, detected_objects "
        f"FROM photos WHERE id IN ({placeholders})",
        photo_ids
    ).fetchall()
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
    conn = get_connection()
    if event_name:
        rows = conn.execute(
            "SELECT scene_label, COUNT(*) as cnt FROM photos WHERE event_name = ? GROUP BY scene_label ORDER BY cnt DESC",
            [event_name]
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT scene_label, COUNT(*) as cnt FROM photos GROUP BY scene_label ORDER BY cnt DESC"
        ).fetchall()
    conn.close()
    return [{"scene": r[0], "count": r[1]} for r in rows]


def get_photos_by_scene(scene_label: str, event_name: str = None) -> list:
    conn = get_connection()
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
    conn = get_connection()
    rows = conn.execute(
        "SELECT event_name, COUNT(*) as photo_count, MIN(created_at) as created_at "
        "FROM photos GROUP BY event_name ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [{"name": r[0], "photo_count": r[1], "created_at": str(r[2])} for r in rows]


def delete_event_photos(event_name: str):
    conn = get_connection()
    conn.execute("DELETE FROM photos WHERE event_name = ?", [event_name])
    conn.close()


def get_photo_stats() -> dict:
    conn = get_connection()
    total_photos = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    total_users = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'user'").fetchone()[0]
    total_searches = conn.execute("SELECT COUNT(*) FROM search_logs").fetchone()[0]
    total_matches = conn.execute("SELECT COUNT(*) FROM face_matches").fetchone()[0]
    conn.close()
    return {
        "total_photos": total_photos,
        "total_users": total_users,
        "total_searches": total_searches,
        "total_matches": total_matches
    }


# ── Match / Log helpers ───────────────────────────────────────────────────────

def insert_face_match(user_id: str, photo_id: str, confidence: float):
    conn = get_connection()
    mid = str(uuid.uuid4())
    # avoid duplicate matches
    existing = conn.execute(
        "SELECT id FROM face_matches WHERE user_id = ? AND photo_id = ?",
        [user_id, photo_id]
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO face_matches (id, user_id, photo_id, confidence) VALUES (?, ?, ?, ?)",
            [mid, user_id, photo_id, confidence]
        )
    conn.close()


def get_user_matched_photos(user_id: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.id, p.filename, p.local_path, p.event_name, p.scene_label,
                  p.detected_objects, fm.confidence
           FROM face_matches fm
           JOIN photos p ON p.id = fm.photo_id
           WHERE fm.user_id = ?
           ORDER BY fm.matched_at DESC""",
        [user_id]
    ).fetchall()
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
    conn = get_connection()
    conn.execute(
        "INSERT INTO search_logs (id, user_id, results_count, scene_filter) VALUES (?, ?, ?, ?)",
        [str(uuid.uuid4()), user_id, results_count, scene_filter or ""]
    )
    conn.close()
