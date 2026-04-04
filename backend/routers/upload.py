import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db, Photo, Embedding
from face_engine import face_engine
import json

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/bulk")
async def bulk_upload(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """
    Upload multiple event images, store in DB, and index embeddings in FAISS.
    """
    uploaded_photos = []
    
    for file in files:
        try:
            # Generate unique ID and save file
            photo_id = str(uuid.uuid4())
            extension = os.path.splitext(file.filename)[1]
            file_path = os.path.join(UPLOAD_DIR, f"{photo_id}{extension}")
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract embeddings
            embeddings = face_engine.extract_embeddings(file_path)
            face_count = len(embeddings)
            
            # Save to Database
            new_photo = Photo(
                id=photo_id,
                image_path=file_path,
                face_count=face_count,
                scene_label="unknown" # CLIP classification could be added later
            )
            db.add(new_photo)
            
            # Save embeddings to DB (for future index rebuilding)
            for emb in embeddings:
                new_emb = Embedding(
                    photo_id=photo_id,
                    embedding_vector=",".join(map(str, emb.tolist()))
                )
                db.add(new_emb)
            
            # Add to FAISS index
            face_engine.add_photo(photo_id, embeddings)
            
            db.commit()
            uploaded_photos.append({
                "id": photo_id,
                "filename": file.filename,
                "face_count": face_count
            })
            
        except Exception as e:
            print(f"Error uploading {file.filename}: {e}")
            continue

    return {
        "status": "success",
        "count": len(uploaded_photos),
        "photos": uploaded_photos
    }
