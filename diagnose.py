import sys, os
sys.path.insert(0, '.')

# Check FAISS index
faiss_path = 'data/faiss_index.bin'
pkl_path = 'data/photo_id_map.pkl'
print('FAISS index exists:', os.path.exists(faiss_path))
print('Photo ID map exists:', os.path.exists(pkl_path))

if os.path.exists(faiss_path):
    import faiss, pickle
    idx = faiss.read_index(faiss_path)
    print('FAISS index size (total vectors):', idx.ntotal)
    with open(pkl_path, 'rb') as f:
        pid_map = pickle.load(f)
    print('Photo ID map length:', len(pid_map))
    print('Sample photo IDs:', pid_map[:3])
else:
    print('NO FAISS INDEX - face search will always return empty!')

# Check DB
import duckdb
conn = duckdb.connect('data/facefind.duckdb')
total = conn.execute('SELECT COUNT(*) FROM photos').fetchone()[0]
faces = conn.execute('SELECT SUM(face_count) FROM photos').fetchone()[0]
print(f'Photos in DB: {total}, Total face embeddings stored: {faces}')
rows = conn.execute('SELECT filename, event_name, face_count FROM photos LIMIT 10').fetchall()
for r in rows:
    print(f'  {r[0]} | event={r[1]} | faces={r[2]}')
conn.close()
