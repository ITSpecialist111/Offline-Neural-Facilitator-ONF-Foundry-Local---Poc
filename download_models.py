from huggingface_hub import snapshot_download
import os

os.makedirs("models/source/qwen", exist_ok=True)
os.makedirs("models/source/deepseek", exist_ok=True)

print("Downloading Qwen...")
snapshot_download("Qwen/Qwen2.5-0.5B-Instruct", local_dir="models/source/qwen")
print("Qwen Downloaded.")

print("Downloading DeepSeek...")
snapshot_download("deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", local_dir="models/source/deepseek")
print("DeepSeek Downloaded.")
