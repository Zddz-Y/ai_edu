from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import concurrent
import PyPDF2
import pandas as pd
import base64
import os

client = OpenAI(api_key=os.environ.get("deepseek_api_key"), base_url="https://api.deepseek.com")

1# 测试 DeepSeek API 基本连接
try:
    models = client.models.list()
    print("Available models:", [model.id for model in models.data])
    print("API connection successful")
except Exception as e:
    print(f"API connection error: {e}")