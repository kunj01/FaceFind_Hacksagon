import traceback
from deepface import DeepFace
import numpy as np

if not hasattr(np, 'float8_e4m3fn'):
    np.float8_e4m3fn = np.float16
    np.float8_e5m2 = np.float16
    np.object_ = object
    np.bool_ = bool
    np.complex_ = complex

try:
    result = DeepFace.represent(
        img_path=r'data\uploads\2026\passport photo.jpg',
        model_name='ArcFace',
        detector_backend='opencv',
        enforce_detection=False,
        align=True
    )
    print("Success! Found", len(result), "faces")
except Exception as e:
    print("Failed")
    traceback.print_exc()
