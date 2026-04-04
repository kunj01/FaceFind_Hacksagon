import sys
import os
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from services.face_engine import face_engine
from database.db import get_connection

def rebuild():
    print("--- FaceFind Index Rebuild Tool ---")
    print(f"Time: {time.ctime()}")
    
    print("Step 1: Resetting existing FAISS index...")
    face_engine.reset_index()

    try:
        conn = get_connection()
        photos = conn.execute("SELECT id, local_path, filename FROM photos").fetchall()
        
        total = len(photos)
        print(f"Step 2: Found {total} photos in database to process.")
        
        success_count = 0
        fail_count = 0
        
        for i, row in enumerate(photos):
            photo_id, local_path, filename = row
            print(f"[{i+1}/{total}] Processing: {filename}...")
            
            if not os.path.exists(local_path):
                print(f"   ⚠️ ERROR: File not found at {local_path}")
                fail_count += 1
                continue
                
            try:
                # Extract embeddings and add to FAISS
                added = face_engine.process_image(local_path, photo_id)
                
                # Update database with face count
                conn.execute("UPDATE photos SET face_count = ? WHERE id = ?", [added, photo_id])
                
                print(f"   ✅ SUCCESS: {added} faces detected and indexed.")
                success_count += 1
            except Exception as e:
                print(f"   ❌ FAILED: {str(e)}")
                import traceback
                traceback.print_exc()
                conn.execute("UPDATE photos SET face_count = 0 WHERE id = ?", [photo_id])
                fail_count += 1
                
        print("\n--- Summary ---")
        print(f"Total Photos: {total}")
        print(f"Successfully Indexed: {success_count}")
        print(f"Failed: {fail_count}")
        print(f"FAISS Index Size: {face_engine.index_size()}")
        print("Done!")
        
        conn.close()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    rebuild()
