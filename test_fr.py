import face_recognition
import numpy as np

img_path = r'data\uploads\annual 2026\IMG-20250503-WA0017.jpg'
image = face_recognition.load_image_file(img_path)
face_locations = face_recognition.face_locations(image)
encodings = face_recognition.face_encodings(image, face_locations)

print("Detected faces:", len(encodings))
if encodings:
    print("Embedding size:", len(encodings[0]))
    print("First embedding sample:", encodings[0][:5])
