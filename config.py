"""项目配置管理"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent

# OpenAI 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "dall-e-3")

# 小红书配置
XHS_COOKIE_FILE = BASE_DIR / os.getenv("XHS_COOKIE_FILE", "cookies/xhs_cookies.json")

# 发布配置
PUBLISH_INTERVAL_SECONDS = int(os.getenv("PUBLISH_INTERVAL_SECONDS", "300"))
MAX_IMAGES_PER_NOTE = int(os.getenv("MAX_IMAGES_PER_NOTE", "9"))

# 输出目录
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Cookies 目录
COOKIES_DIR = BASE_DIR / "cookies"
COOKIES_DIR.mkdir(exist_ok=True)
