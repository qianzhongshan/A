#!/usr/bin/env python3
import sys
import os

# 添加 backend 目录到 Python 路径
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 设置环境变量
os.environ['PYTHONPATH'] = backend_dir

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[os.path.join(os.path.dirname(__file__), 'backend')]
    )
