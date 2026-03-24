#!/usr/bin/env python3
"""启动后端服务器"""
import sys
import os

# 确保 backend 目录在 Python 路径中
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.chdir(backend_dir)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting MBTI Deep Test API...")
    print(f"   Backend directory: {backend_dir}")
    print(f"   Python path includes: {sys.path[0]}")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
