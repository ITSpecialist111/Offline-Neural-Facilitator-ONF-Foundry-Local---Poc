
import os
import zipfile
import urllib.request
import shutil

url = "https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip"
target_dir = r"c:\Users\graham\Documents\GitHub\Speech-to-rag-OpenvoiceV2-V1-MeloTTS\modules\OpenVoice"
zip_path = os.path.join(target_dir, "checkpoints.zip")

def progress_hook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = downloaded * 100 / total_size
        print(f"\rDownloading: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB)", end="")
    else:
        print(f"\rDownloading: {downloaded / (1024*1024):.1f} MB", end="")

print(f"Downloading checkpoints to {target_dir}")
urllib.request.urlretrieve(url, zip_path, progress_hook)
print("\nDownload complete. Extracting...")

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(target_dir)

print("Extraction complete.")
os.remove(zip_path)
print("Cleaned up zip file.")
