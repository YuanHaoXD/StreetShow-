import os
from huggingface_hub import snapshot_download
# 设置镜像站环境变量
from huggingface_hub import login
login(token=os.getenv("HF_TOKEN", ""))  # 从环境变量读取，不要硬编码

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
# 下载整个模型文件到指定路径
snapshot_download(repo_id="Qwen/Qwen3-VL-8B-Instruct", local_dir=".Qwen/Qwen3-VL-8B-Instruct", local_dir_use_symlinks=False, resume_download=True)