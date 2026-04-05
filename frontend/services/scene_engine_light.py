"""
LIGHTWEIGHT Scene Understanding Engine - NO YOLO/CLIP (instant results)
Analyzes image properties for fast scene categorization
"""

from PIL import Image
import numpy as np
from pathlib import Path

# Scene categories
SCENE_CATEGORIES = {
    "group_photo": "Multiple people together",
    "portrait": "Person/few people close-up",
    "outdoor": "Outside/natural light",
    "indoor": "Indoor/artificial light",
    "stage_event": "Bright lights, performance setup",
    "casual_gathering": "People in relaxed setting",
    "formal_event": "Formal attire/dressed up",
}

SCENE_EMOJIS = {
    "group_photo": "👥",
    "portrait": "🤳",
    "outdoor": "🌳",
    "indoor": "🏠",
    "stage_event": "🎤",
    "casual_gathering": "👫",
    "formal_event": "🎩",
    "unknown": "❓",
}

class LightWeightSceneEngine:
    """Ultra-fast scene detection using image properties only"""
    
    def analyze(self, image_path: str) -> dict:
        """Analyze scene from image properties (NO ML models needed)"""
        try:
            img = Image.open(image_path)
            img_array = np.array(img)
            
            # Get image properties
            height, width = img_array.shape[:2]
            brightness = np.mean(img_array)
            
            # Detect scene based on properties
            scene, confidence = self._detect_scene(img_array, brightness, width, height)
            
            return {
                "scene": scene,
                "scene_label": scene.replace("_", " ").title(),
                "confidence": confidence,
                "objects": [],  # Skip object detection
                "object_count": 0,
                "emoji": SCENE_EMOJIS.get(scene, "❓")
            }
        except Exception as e:
            return self._unknown_result()
    
    def _detect_scene(self, img_array, brightness, width, height):
        """Detect scene type from image properties"""
        
        # Aspect ratio
        aspect = width / height if height > 0 else 1
        
        # Color analysis
        if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
            r = np.mean(img_array[:,:,0])
            g = np.mean(img_array[:,:,1])
            b = np.mean(img_array[:,:,2])
            
            # Red channel dominance = stage/bright lights
            if r > g and r > b and brightness > 150:
                return "stage_event", 0.85
            
            # Green dominance = outdoor
            if g > r and g > b and brightness > 120:
                return "outdoor", 0.80
        
        # Brightness-based detection
        if brightness > 160:  # Bright = stage/outdoor/formal
            return "formal_event", 0.70
        elif brightness < 80:  # Dark = indoor
            return "indoor", 0.65
        
        # Portrait detection: square aspect ratio, medium brightness
        if 0.8 < aspect < 1.2 and 80 < brightness < 150:
            return "portrait", 0.75
        
        # Group photo: wider aspect, medium brightness
        if aspect > 1.2 and 90 < brightness < 140:
            return "group_photo", 0.70
        
        return "casual_gathering", 0.60
    
    def _unknown_result(self):
        return {
            "scene": "unknown",
            "scene_label": "Unknown",
            "confidence": 0.0,
            "objects": [],
            "object_count": 0,
            "emoji": "❓"
        }

# Singleton instance
scene_engine = LightWeightSceneEngine()
