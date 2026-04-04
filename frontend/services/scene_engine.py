"""
Scene Understanding Engine for FaceFind.
Uses CLIP (ViT-B/32) for semantic scene classification
and YOLOv8n for object detection.
"""

import os
import torch
import numpy as np
from PIL import Image
from pathlib import Path


# Scene categories with rich descriptive prompts for CLIP
SCENE_CATEGORIES = {
    "stage_performance": "a person performing on stage with microphone and lights",
    "award_ceremony":   "an award ceremony with trophy presentation and formal dress",
    "group_photo":      "a large group of people posing together smiling for a photo",
    "dining_event":     "people sitting at tables eating food at a social event party",
    "outdoor_event":    "people gathered outdoors in an open field or park area",
    "sports_event":     "people playing sports athletic activities running field",
    "seminar_talk":     "people sitting in rows listening to a speaker presentation lecture",
    "candid_moment":    "people having natural candid conversations informal gathering",
    "cultural_event":   "traditional dance music cultural performance costume stage",
    "entrance_lobby":   "people near entrance gate registration desk hallway corridor",
}

SCENE_EMOJIS = {
    "stage_performance": "🎤",
    "award_ceremony":   "🏆",
    "group_photo":      "👥",
    "dining_event":     "🍽️",
    "outdoor_event":    "🌳",
    "sports_event":     "⚽",
    "seminar_talk":     "🎓",
    "candid_moment":    "📸",
    "cultural_event":   "🎭",
    "entrance_lobby":   "🚪",
}


class SceneEngine:
    _instance = None

    def __init__(self):
        self._clip_model = None
        self._clip_preprocess = None
        self._yolo_model = None
        self._text_features = None
        self._loaded = False

    def _load_models(self):
        """Lazy-load models (first call only)."""
        if self._loaded:
            return

        import clip
        from ultralytics import YOLO

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # CLIP
        self._clip_model, self._clip_preprocess = clip.load("ViT-B/32", device=device)
        self._clip_model.eval()

        # Encode all scene text prompts once
        texts = list(SCENE_CATEGORIES.values())
        tokens = clip.tokenize(texts).to(device)
        with torch.no_grad():
            self._text_features = self._clip_model.encode_text(tokens)
            self._text_features = self._text_features / self._text_features.norm(dim=-1, keepdim=True)

        # YOLOv8 nano (auto-downloads on first use if not found)
        # Search for model in local project first
        model_path = Path(__file__).parent.parent / "yolov8n.pt"
        if not model_path.exists():
            model_path = "yolov8n.pt" # Fallback to default search
        
        self._yolo_model = YOLO(str(model_path))

        self._loaded = True

    def analyze(self, image_path: str) -> dict:
        """
        Analyze an image and return scene classification + detected objects.
        
        Returns:
            {
                "scene": str,           # scene category key
                "scene_label": str,     # human-friendly label
                "confidence": float,    # 0-1
                "objects": list[str],   # detected object names
                "object_count": int,
                "emoji": str
            }
        """
        self._load_models()

        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            print(f"❌ Error opening image {image_path}: {e}")
            return {
                "scene": "unknown", "scene_label": "Unknown", "confidence": 0.0,
                "objects": [], "object_count": 0, "emoji": "❓"
            }

        # ── CLIP: Scene Classification ─────────────────────────────────────
        preprocessed = self._clip_preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            image_features = self._clip_model.encode_image(preprocessed)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        similarity = (image_features @ self._text_features.T).squeeze(0)
        probs = similarity.softmax(dim=-1).cpu().numpy()
        scene_idx = int(np.argmax(probs))
        scene_key = list(SCENE_CATEGORIES.keys())[scene_idx]
        confidence = float(probs[scene_idx])
        scene_label = scene_key.replace("_", " ").title()

        # ── YOLO: Object Detection ─────────────────────────────────────────
        try:
            yolo_results = self._yolo_model(image_path, verbose=False)
            detected_objects = list(set([
                yolo_results[0].names[int(cls)]
                for cls in yolo_results[0].boxes.cls
            ]))
            object_count = int(len(yolo_results[0].boxes))
        except Exception:
            detected_objects = []
            object_count = 0

        return {
            "scene": scene_key,
            "scene_label": scene_label,
            "confidence": round(confidence, 4),
            "objects": detected_objects,
            "object_count": object_count,
            "emoji": SCENE_EMOJIS.get(scene_key, "📁")
        }

    def analyze_batch(self, image_paths: list, progress_callback=None) -> list:
        """Analyze multiple images, with optional progress callback(i, total, path)."""
        results = []
        total = len(image_paths)
        for i, path in enumerate(image_paths):
            result = self.analyze(path)
            result["path"] = path
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, total, os.path.basename(path))
        return results


# Singleton
scene_engine = SceneEngine()
