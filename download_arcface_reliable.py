import urllib.request
import os

url = "https://github.com/serengil/deepface_models/releases/download/v1.0/arcface_weights.h5"
dest_dir = os.path.expanduser(r"~\.deepface\weights")
os.makedirs(dest_dir, exist_ok=True)
dest_path = os.path.join(dest_dir, "arcface_weights.h5")

def report(block_num, block_size, total_size):
    downloaded = block_num * block_size
    percent = downloaded * 100 / total_size if total_size > 0 else 0
    if downloaded % (block_size * 50) == 0 or downloaded >= total_size:
        print(f"\rDownloading: {downloaded/1024/1024:.2f} MB / {total_size/1024/1024:.2f} MB ({percent:.1f}%)", end="")

print(f"Downloading {url} to {dest_path}")
urllib.request.urlretrieve(url, dest_path, reporthook=report)
print("\nDownload complete!")
