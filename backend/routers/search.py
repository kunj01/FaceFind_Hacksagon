import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db, Photo
from face_engine import face_engine
import numpy as np

router = APIRouter(prefix="/search", tags=["Search"])

SEARCH_DIR = "data/search"
os.makedirs(SEARCH_DIR, exist_ok=True)

@router.post("/face")
async def search_face(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Search for matching photos using a selfie.
    """
    try:
        # Save temporary selfie
        selfie_id = str(uuid.uuid4())
        extension = os.path.splitext(file.filename)[1]
        selfie_path = os.path.join(SEARCH_DIR, f"{selfie_id}{extension}")
        
        with open(selfie_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Search using face_engine
        results = face_engine.search(selfie_path)
        
        # Fetch photo details from DB
        matched_photos = []
        for res in results:
            photo = db.query(Photo).filter(Photo.id == res["photo_id"]).first()
            if photo:
                matched_photos.append({
                    "image_url": f"/photos/{photo.id}", # Placeholder for frontend
                    "image_path": photo.image_path,
                    "similarity": round(res["similarity"], 4),
                    "face_count": photo.face_count,
                    "scene_label": photo.scene_label
                })
        
        # Cleanup temporary selfie
        os.remove(selfie_path)
        
        return {
            "found": len(matched_photos),
            "photos": matched_photos
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
