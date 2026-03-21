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
    # Fallback pre-trained model for PPE (trained on Construction Site Safety dataset)
    # This is a public URL from Hugging Face Hansung-Cho/yolov8-ppe-detection
    MODEL_URL = "https://huggingface.co/Hansung-Cho/yolov8-ppe-detection/resolve/main/best.pt"
    MODEL_PATH = os.path.join("models", "ppe_yolov8s.pt")
    
    if not os.path.exists("models"):
        os.makedirs("models")
        
    download_file(MODEL_URL, MODEL_PATH)
