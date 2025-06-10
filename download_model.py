from huggingface_hub import snapshot_download
import os
import logging

logging.basicConfig(level=logging.INFO)

os.makedirs("ocr_model", exist_ok=True)

if os.listdir("ocr_model"):
    print("ocr_model directory is not empty. Skipping download.")
else:
    print("Downloading model...")
    snapshot_download(repo_id="allenai/olmOCR-7B-0225-preview", local_dir="ocr_model")
    print("Model downloaded to ocr_model.")