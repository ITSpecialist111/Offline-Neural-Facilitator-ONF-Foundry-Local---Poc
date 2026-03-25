
import os
import urllib.request

target_dir = r"c:\Users\graham\Documents\GitHub\Speech-to-rag-OpenvoiceV2-V1-MeloTTS\modules\MeloTTS\MeloTTS-English"
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

files = ["checkpoint.pth", "config.json"]
base_url = "https://huggingface.co/myshell-ai/MeloTTS-English/resolve/main/"

def progress_hook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = downloaded * 100 / total_size
        print(f"\rDownloading: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB)", end="")
    else:
        print(f"\rDownloading: {downloaded / (1024*1024):.1f} MB", end="")

for file in files:
    url = base_url + file
    path = os.path.join(target_dir, file)
    print(f"\nDownloading {file} to {path}")
    try:
        urllib.request.urlretrieve(url, path, progress_hook)
        print("\nDownload complete.")
    except Exception as e:
        print(f"\nError downloading {file}: {e}")
