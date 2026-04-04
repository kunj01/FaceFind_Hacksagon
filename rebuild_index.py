"""
Rebuild FAISS index from all photos already stored in the DB using the FaceEngine.
Run: python rebuild_index.py
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

import duckdb
from pathlib import Path
from services.face_engine import face_engine

DB_PATH = "data/facefind.duckdb"

print("=" * 60)
print("FaceFind -- FAISS Index Rebuilder (face_recognition)")
print("=" * 60)

# Reset index to completely fresh state
face_engine.reset_index()

conn = duckdb.connect(DB_PATH)
rows = conn.execute(
    "SELECT id, filename, event_name, face_count, local_path FROM photos ORDER BY event_name"
).fetchall()
print(f"Photos in database: {len(rows)}\n")

total_faces = 0
skipped = []

for r in rows:
    photo_id, filename, event_name, _, local_path = r

    if not local_path or not Path(local_path).exists():
        print(f"  [MISSING] {filename}  (path={local_path})")
        skipped.append(filename)
        continue

    try:
        added = face_engine.process_image(local_path, photo_id)
        # Update face_count in DB
        conn.execute("UPDATE photos SET face_count = ? WHERE id = ?", [added, photo_id])
        total_faces += added
        status = "[OK]" if added > 0 else "[NO-FACE]"
        print(f"  {status} {filename:<40} faces={added}")
    except Exception as e:
        print(f"  [ERROR] {filename}: {e}")
        skipped.append(filename)

conn.close()

print(f"\n{'=' * 60}")
print(f"FAISS index rebuilt!")
print(f"  Total vectors in index : {face_engine.index_size()}")
print(f"  Unique photos mapped   : {len(set(face_engine._photo_id_map))}")
print(f"  Total face embeddings  : {total_faces}")
if skipped:
    print(f"  Skipped/failed files   : {skipped}")
print(f"{'=' * 60}")

if face_engine.index_size() == 0:
    print("\nWARNING: Index has 0 vectors!")
    print("  No faces were detected in any uploaded photo.")
else:
    print(f"\nSearch should now work. Restart the Streamlit app and try again.")
