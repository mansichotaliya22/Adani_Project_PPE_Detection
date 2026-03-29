import requests
import os

def download_file(url, filename):
    print(f"Downloading {filename} from {url}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Download complete: {filename}")
    else:
        print(f"Failed to download. Status code: {response.status_code}")

if __name__ == "__main__":
    # Switching to YOLOv8n (Nano) for much better CPU performance
    # Nano models are ~5x faster than Small models on typical laptop CPUs
    MODEL_URL = "https://huggingface.co/Hansung-Cho/yolov8-ppe-detection/resolve/main/best.pt"
    # Note: We keep the filename the same in the code to avoid mass-renaming, 
    # but the source model is optimized for speed.
    MODEL_PATH = os.path.join("models", "ppe_yolov8s.pt")
    
    if not os.path.exists("models"):
        os.makedirs("models")
        
    download_file(MODEL_URL, MODEL_PATH)
