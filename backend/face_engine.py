import os
import pickle
import numpy as np
import faiss
from typing import List, Tuple

# Configuration
FAISS_INDEX_PATH = "data/faiss_index.bin"
PHOTO_ID_MAP_PATH = "data/photo_id_map.pkl"
EMBEDDING_DIM = 128  # face_recognition ResNet-34 dimension
# Distance threshold — lower is stricter (0.6 is default for face_recognition)
DISTANCE_THRESHOLD = 0.45 

class FaceEngine:
    def __init__(self):
        self.index = None
        self.photo_id_map = []  # FAISS index position -> photo_id
        self._initialize_faiss()

    def _initialize_faiss(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(FAISS_INDEX_PATH):
            try:
                self.index = faiss.read_index(FAISS_INDEX_PATH)
                with open(PHOTO_ID_MAP_PATH, "rb") as f:
                    self.photo_id_map = pickle.load(f)
                print(f"Loaded FAISS index with {self.index.ntotal} vectors.")
            except Exception as e:
                print(f"Error loading index: {e}. Creating new index.")
                self.index = faiss.IndexFlatL2(EMBEDDING_DIM)
        else:
            self.index = faiss.IndexFlatL2(EMBEDDING_DIM)
            self.photo_id_map = []

    def save_index(self):
        faiss.write_index(self.index, FAISS_INDEX_PATH)
        with open(PHOTO_ID_MAP_PATH, "wb") as f:
            pickle.dump(self.photo_id_map, f)

    def extract_embeddings(self, img_path: str, is_search: bool = False) -> List[np.ndarray]:
        """
        Extract face embeddings using the face-recognition library (Dlib ResNet-34).
        """
        import face_recognition
        try:
            image = face_recognition.load_image_file(img_path)
            # Find face locations and landmarks (upsample once for accuracy)
            face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=1)
            
            # Use jittering only for the query selfie to improve accuracy
            jitters = 10 if is_search else 1
            face_encodings = face_recognition.face_encodings(image, face_locations, num_jitters=jitters)
            
            embeddings = []
            for enc in face_encodings:
                embeddings.append(np.array(enc, dtype=np.float32))
            return embeddings
        except Exception as e:
            print(f"Error in embedding extraction for {img_path}: {e}")
            return []

    def add_photo(self, photo_id: str, embeddings: List[np.ndarray]):
        if not embeddings:
            return
        
        vectors = np.vstack(embeddings).astype(np.float32)
        self.index.add(vectors)
        # Store photo_id for each face found in this image
        for _ in range(len(embeddings)):
            self.photo_id_map.append(photo_id)
        
        self.save_index()

    def search(self, selfie_path: str, top_k: int = 50) -> List[dict]:
        """
        Search for matching photos.
        """
        # High-precision scan for the query selfie
        query_embeddings = self.extract_embeddings(selfie_path, is_search=True)
        if not query_embeddings:
            return []

        # Take the primary face from the selfie
        query_vec = query_embeddings[0].reshape(1, -1).astype(np.float32)
        
        # FAISS Euclidean distance search
        distances, indices = self.index.search(query_vec, min(top_k, self.index.ntotal))
        
        results = []
        seen_photos = set()
        
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1: continue
            
            float_dist = float(dist)
            if float_dist > DISTANCE_THRESHOLD:
                continue
                
            photo_id = self.photo_id_map[idx]
            if photo_id not in seen_photos:
                # Standard confidence scaled to 0.6 distance (industry standard for face_recognition match)
                confidence = max(0.0, 1.0 - float_dist / 0.6)
                results.append({
                    "photo_id": photo_id,
                    "distance": float_dist,
                    "similarity": round(confidence, 4) # Renamed to similarity for backend API compat
                })
                seen_photos.add(photo_id)
        
        # Sort by best similarity
        results = sorted(results, key=lambda x: x["similarity"], reverse=True)
        return results

# Singleton instance
face_engine = FaceEngine()
