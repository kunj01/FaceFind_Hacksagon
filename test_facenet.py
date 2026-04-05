import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from deepface import DeepFace

test_img = r'data\uploads\annual 2026\IMG-20250503-WA0017.jpg'
print('Testing with Facenet512...')

try:
    result = DeepFace.represent(
        img_path=test_img,
        model_name='Facenet512',
        detector_backend='opencv',
        enforce_detection=False,
        align=True
    )
    valid = [r for r in result if r.get('embedding') and len(r.get('embedding', [])) == 512]
    print(f'SUCCESS! Raw results: {len(result)}, Valid embeddings: {len(valid)}')
except Exception as e:
    import traceback
    print('FAILED:')
    traceback.print_exc()
