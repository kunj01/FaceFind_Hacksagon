"""
Face Recognition Engine for FaceFind.
Uses face_recognition (ResNet-34 model) for face embeddings and
FAISS IndexFlatL2 for fast similarity search.
"""

import os
import pickle
import numpy as np
import faiss
from pathlib import Path

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss_index.bin")
PHOTO_ID_MAP_PATH = os.getenv("PHOTO_ID_MAP_PATH", "data/photo_id_map.pkl")

# face_recognition produces 128-dim embeddings
EMBEDDING_DIM = 128
# Distance threshold — lower is stricter (0.6 is default for face_recognition)
DISTANCE_THRESHOLD = 0.45


class FaceEngine:
    def __init__(self):
        self._index = None
        self._photo_id_map = []   # FAISS position → photo_id
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)

        if os.path.exists(FAISS_INDEX_PATH):
            self._index = faiss.read_index(FAISS_INDEX_PATH)
            with open(PHOTO_ID_MAP_PATH, "rb") as f:
                self._photo_id_map = pickle.load(f)
        else:
            self._index = faiss.IndexFlatL2(EMBEDDING_DIM)
            self._photo_id_map = []

        self._loaded = True

    def _save(self):
        faiss.write_index(self._index, FAISS_INDEX_PATH)
        with open(PHOTO_ID_MAP_PATH, "wb") as f:
            pickle.dump(self._photo_id_map, f)

    # ── Embedding Extraction ───────────────────────────────────────────────

    def extract_embeddings(self, image_path: str, is_search: bool = False) -> list[np.ndarray]:
        """
        Extract face embeddings from an image.
        Returns a list of 128-d numpy arrays (one per detected face).
        
        This method supports auto-rotation (EXIF) and trials multiple angles (90, 180, 270)
        if no faces are initially detected, which is common for mobile uploads.
        """
        import face_recognition
        from PIL import Image, ImageOps
        
        try:
            # Load with Pillow to handle EXIF orientation
            pil_img = Image.open(image_path).convert("RGB")
            pil_img = ImageOps.exif_transpose(pil_img)
            
            # Initial detection
            image = np.array(pil_img)
            face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=0)
            
            # If no faces found, try rotating in 90-degree increments
            # (Important for photos missing EXIF but still rotated, like the one in your screenshot)
            if not face_locations:
                for angle in [90, 180, 270]:
                    rotated_pil = pil_img.rotate(angle, expand=True)
                    rotated_img = np.array(rotated_pil)
                    face_locations = face_recognition.face_locations(rotated_img, number_of_times_to_upsample=0)
                    if face_locations:
                        image = rotated_img
                        break

            if not face_locations:
                return []
            
            # Generate 128-d embeddings for each face
            jitters = 10 if is_search else 1
            face_encodings = face_recognition.face_encodings(image, face_locations, num_jitters=jitters)
            
            return [np.array(enc, dtype=np.float32) for enc in face_encodings]
            
        except Exception as e:
            print(f"❌ Error extracting embeddings from {image_path}: {e}")
            return []


    # ── Index Management ───────────────────────────────────────────────────

    def add_to_index(self, embeddings: list[np.ndarray], photo_id: str) -> int:
        """
        Add face embeddings to the FAISS index.
        Returns number of embeddings added.
        """
        self._load()
        added = 0
        for emb in embeddings:
            vec = emb.reshape(1, -1).astype(np.float32)
            self._index.add(vec)
            self._photo_id_map.append(photo_id)
            added += 1
        if added > 0:
            self._save()
        return added

    def index_size(self) -> int:
        self._load()
        return self._index.ntotal

    def reset_index(self):
        """Reset the FAISS index (called when re-processing events)."""
        self._index = faiss.IndexFlatL2(EMBEDDING_DIM)
        self._photo_id_map = []
        self._save()
        self._loaded = True

    # ── Search ─────────────────────────────────────────────────────────────

    def search(self, selfie_path: str, top_k: int = 50,
                allowed_photo_ids: set = None) -> list[dict]:
        """
        Search for matching photos given a selfie image path.
        
        Args:
            selfie_path: Path to the selfie image
            top_k: Maximum candidates to retrieve from FAISS
            allowed_photo_ids: Optional set of photo IDs to restrict search to
                               (used for scene-filtered search)
        
        Returns:
            List of {photo_id, distance, confidence} dicts, sorted by confidence desc
        """
        self._load()

        if self._index.ntotal == 0:
            return []

        # We use jittering for the search query (is_search=True)
        embeddings = self.extract_embeddings(selfie_path, is_search=True)
        if not embeddings:
            return []

        # Use the first (primary) face embedding from the selfie
        query_vec = embeddings[0].reshape(1, -1).astype(np.float32)
        distances, indices = self._index.search(query_vec, min(top_k, self._index.ntotal))

        matched = {}
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            if dist > DISTANCE_THRESHOLD:
                continue
            photo_id = self._photo_id_map[idx]
            if allowed_photo_ids is not None and photo_id not in allowed_photo_ids:
                continue
            # Keep the best (lowest) distance per photo
            if photo_id not in matched or dist < matched[photo_id]["distance"]:
                # Confidence relative to a standard match distance of 0.6
                confidence = max(0.0, 1.0 - float(dist) / 0.6)
                matched[photo_id] = {
                    "photo_id": photo_id,
                    "distance": float(dist),
                    "confidence": round(confidence, 4)
                }

        # Sort by confidence descending
        results = sorted(matched.values(), key=lambda x: x["confidence"], reverse=True)
        return results

    # ── Batch Processing ───────────────────────────────────────────────────

    def process_image(self, image_path: str, photo_id: str) -> int:
        """Extract embeddings from one image and add them to the index."""
        # Standard extraction (no jittering for batch processing)
        embeddings = self.extract_embeddings(image_path, is_search=False)
        return self.add_to_index(embeddings, photo_id)


# Singleton
face_engine = FaceEngine()
