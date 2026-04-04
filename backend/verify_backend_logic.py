import os
import sys
from database import init_db, SessionLocal, Photo
from face_engine import face_engine
import numpy as np

def verify():
    print("--- 1. Initializing DB ---")
    init_db()
    db = SessionLocal()
    
    print("--- 2. Testing Face Engine Extraction ---")
    test_img = "data/uploads/2026/23IT136_Photo.jpg"
    if not os.path.exists(test_img):
        print(f"Test image not found: {test_img}")
        return
        
    embeddings = face_engine.extract_embeddings(test_img)
    print(f"Extracted {len(embeddings)} faces from {test_img}")
    
    if len(embeddings) > 0:
        print(f"First embedding shape: {embeddings[0].shape}")
        
    print("--- 3. Testing Index Addition ---")
    face_engine.add_photo("test_photo_id", embeddings)
    print(f"Index size: {face_engine.index.ntotal}")
    
    print("--- 4. Testing Search ---")
    results = face_engine.search(test_img)
    print(f"Search results for same image: {results}")
    
    print("--- 5. Testing DB Insertion ---")
    new_photo = Photo(id="test_photo_id", image_path=test_img, face_count=len(embeddings))
    db.add(new_photo)
    db.commit()
    print("Photo inserted into DB.")
    
    db.close()
    print("--- Verification Complete ---")

if __name__ == "__main__":
    verify()
