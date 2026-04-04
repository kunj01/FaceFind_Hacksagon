"""
Download ArcFace weights and test face detection on admin-uploaded photos.
Run: python download_weights.py
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from deepface import DeepFace

test_img = r'data\uploads\annual 2026\IMG-20250503-WA0017.jpg'
print('Testing with:', test_img, '| exists:', os.path.exists(test_img))
print('Downloading ArcFace weights and running represent (may take several minutes)...')

try:
    result = DeepFace.represent(
        img_path=test_img,
        model_name='ArcFace',
        detector_backend='opencv',
        enforce_detection=False,
        align=True
    )
    valid = [r for r in result if r.get('embedding') and len(r.get('embedding', [])) == 512]
    print(f'SUCCESS! Raw results: {len(result)}, Valid embeddings: {len(valid)}')
    for i, r in enumerate(valid):
        emb = r.get('embedding', [])
        region = r.get('facial_area', {})
        print(f'  Face {i+1}: dim={len(emb)}, region={region}')
except Exception as e:
    import traceback
    print('FAILED:')
    traceback.print_exc()
