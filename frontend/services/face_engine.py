"""
Face Recognition Engine for FaceFind.
Uses face_recognition (ResNet-34 model) for face embeddings and
FAISS IndexFlatL2 for fast similarity search.
Thread-safe: uses a threading.Lock for index mutations.
"""

import os
import pickle
import threading
import numpy as np
import faiss
from pathlib import Path

FAISS_INDEX_PATH   = os.getenv("FAISS_INDEX_PATH",  "data/faiss_index.bin")
PHOTO_ID_MAP_PATH  = os.getenv("PHOTO_ID_MAP_PATH", "data/photo_id_map.pkl")

# ArcFace produces 512-dim embeddings
EMBEDDING_DIM      = 512
# L2 distance threshold — lower is stricter
DISTANCE_THRESHOLD = 0.6


class FaceEngine:
    def __init__(self):
        self._index        = None
        self._photo_id_map = []   # FAISS position → photo_id
        self._loaded       = False
        self._lock         = threading.Lock()

    # ── Private helpers ────────────────────────────────────────────────────

    def _load(self):
        """Lazy-load or create the FAISS index. Must be called inside self._lock."""
        if self._loaded:
            return
        import faiss
        data_dir = os.path.dirname(FAISS_INDEX_PATH)
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)

        try:
            if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(PHOTO_ID_MAP_PATH):
                self._index = faiss.read_index(FAISS_INDEX_PATH)
                with open(PHOTO_ID_MAP_PATH, "rb") as f:
                    self._photo_id_map = pickle.load(f)
                # Sanity check: sizes must match
                if self._index.ntotal != len(self._photo_id_map):
                    raise ValueError("FAISS index / map size mismatch — rebuilding fresh index")
            else:
                raise FileNotFoundError("No existing index")
        except Exception:
            self._index        = faiss.IndexFlatL2(EMBEDDING_DIM)
            self._photo_id_map = []

        self._loaded = True

    def _save(self):
        """Persist FAISS index and ID map to disk. Must be called inside self._lock."""
        import faiss
        faiss.write_index(self._index, FAISS_INDEX_PATH)
        with open(PHOTO_ID_MAP_PATH, "wb") as f:
            pickle.dump(self._photo_id_map, f)

    # ── Embedding Extraction ───────────────────────────────────────────────

    def extract_embeddings(self, image_path: str) -> list:
        """
        Extract face embeddings from an image using ArcFace.
        Returns a list of 512-d numpy arrays (one per detected face).
        """
        # NumPy 2.x compatibility patch for TensorFlow / DeepFace
        import numpy as np
        if not hasattr(np, "float8_e4m3fn"):
            np.float8_e4m3fn = np.float16
            np.float8_e5m2   = np.float16
            np.object_       = object
            np.bool_         = bool
            np.complex_      = complex

        try:
            from deepface import DeepFace
            result = DeepFace.represent(
                img_path=image_path,
                model_name="ArcFace",
                detector_backend="opencv",
                enforce_detection=False,
                align=True
            )
            embeddings = []
            for face in result:
                emb = face.get("embedding", [])
                if emb and len(emb) == EMBEDDING_DIM:
                    embeddings.append(np.array(emb, dtype=np.float32))
            return embeddings
        except Exception:
            return []


    # ── Index Management ───────────────────────────────────────────────────

    def add_to_index(self, embeddings: list, photo_id: str) -> int:
        """
        Add face embeddings to the FAISS index.
        Returns number of embeddings added.
        """
        if not embeddings:
            return 0
        with self._lock:
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
        with self._lock:
            self._load()
            return self._index.ntotal

    def reset_index(self):
        """Reset the FAISS index (called when deleting events or re-processing)."""
        import faiss
        with self._lock:
            self._index        = faiss.IndexFlatL2(EMBEDDING_DIM)
            self._photo_id_map = []
            self._save()
            self._loaded = True

    def rebuild_index_from_photos(self, photos: list) -> int:
        """
        Full rebuild of the FAISS index from a list of {id, local_path} dicts.
        Returns total embeddings indexed.
        """
        self.reset_index()
        total_added = 0
        for photo in photos:
            try:
                embeddings = self.extract_embeddings(photo["local_path"])
                added = self.add_to_index(embeddings, photo["id"])
                total_added += added
            except Exception:
                pass
        return total_added

    # ── Search ─────────────────────────────────────────────────────────────

    def search(self, selfie_path: str, top_k: int = 50,
               allowed_photo_ids: set = None) -> list:
        """
        Search for matching photos given a selfie image path.

        Args:
            selfie_path: Path to the selfie image
            top_k: Maximum candidates to retrieve from FAISS
            allowed_photo_ids: Optional set of photo IDs to restrict search to

        Returns:
            List of {photo_id, distance, confidence} dicts, sorted by confidence desc
        """
        with self._lock:
            self._load()
            if self._index.ntotal == 0:
                return []

            embeddings = self.extract_embeddings(selfie_path)
            if not embeddings:
                return []

            query_vec = embeddings[0].reshape(1, -1).astype(np.float32)
            k = min(top_k, self._index.ntotal)
            distances, indices = self._index.search(query_vec, k)

            matched = {}
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0:
                    continue
                if dist > DISTANCE_THRESHOLD:
                    continue
                if idx >= len(self._photo_id_map):
                    continue
                photo_id = self._photo_id_map[idx]
                if allowed_photo_ids is not None and photo_id not in allowed_photo_ids:
                    continue
                # Keep best (lowest) distance per photo
                if photo_id not in matched or dist < matched[photo_id]["distance"]:
                    confidence = max(0.0, 1.0 - float(dist) / DISTANCE_THRESHOLD)
                    matched[photo_id] = {
                        "photo_id":   photo_id,
                        "distance":   float(dist),
                        "confidence": round(confidence, 4)
                    }

        return sorted(matched.values(), key=lambda x: x["confidence"], reverse=True)

    # ── Batch Processing ───────────────────────────────────────────────────

    def process_image(self, image_path: str, photo_id: str) -> int:
        """Extract embeddings from one image and add them to the index."""
        # Standard extraction (no jittering for batch processing)
        embeddings = self.extract_embeddings(image_path, is_search=False)
        return self.add_to_index(embeddings, photo_id)


# Singleton
face_engine = FaceEngine()
