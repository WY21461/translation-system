import streamlit as st  # Hugging Face Space 自动检测 SDK 类型
import runpy
from pathlib import Path
import sys

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# 代理运行 src/app.py
runpy.run_path(str(ROOT / "src" / "app.py"), run_name="__main__")
