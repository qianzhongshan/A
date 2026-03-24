#!/usr/bin/env python3
"""
MBTI 深度测试系统 - 启动脚本
"""
import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """检查环境要求"""
    print("🔍 检查环境要求...")

    # 检查 Python
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print(f"✅ Python: {result.stdout.strip()}")
    except:
        print("❌ Python 未安装")
        return False

    # 检查 Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"✅ Node.js: {result.stdout.strip()}")
    except:
        print("❌ Node.js 未安装")
        return False

    # 检查 npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        print(f"✅ npm: {result.stdout.strip()}")
    except:
        print("❌ npm 未安装")
        return False

    return True

def install_backend_deps():
    """安装后端依赖"""
    print("\n📦 安装后端依赖...")
    os.chdir("backend")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    os.chdir("..")
    print("✅ 后端依赖安装完成")

def install_frontend_deps():
    """安装前端依赖"""
    print("\n📦 安装前端依赖...")
    os.chdir("frontend")
    subprocess.run(["npm", "install"], check=True)
    os.chdir("..")
    print("✅ 前端依赖安装完成")

def init_database():
    """初始化数据库"""
    print("\n🗄️  初始化数据库...")
    os.chdir("backend")
    subprocess.run([sys.executable, "-c", "from database import init_db; init_db()"], check=True)
    os.chdir("..")
    print("✅ 数据库初始化完成")

def start_dev():
    """启动开发服务器"""
    print("\n🚀 启动开发服务器...")
    print("前端: http://localhost:3000")
    print("后端: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务\n")

    # 使用 concurrently 启动前后端
    subprocess.run(["npm", "run", "dev"], check=True)

def main():
    """主函数"""
    print("=" * 50)
    print("MBTI 深度测试系统 - 启动脚本")
    print("=" * 50)

    # 检查是否在正确的目录
    if not Path("backend/app.py").exists():
        print("❌ 请在项目根目录（mbti_project）下运行此脚本")
        sys.exit(1)

    # 检查环境
    if not check_requirements():
        print("\n❌ 环境检查失败，请安装缺失的依赖")
        sys.exit(1)

    # 安装依赖（如果 node_modules 不存在）
    if not Path("frontend/node_modules").exists():
        install_frontend_deps()

    if not Path("backend/requirements.txt").exists():
        install_backend_deps()

    # 初始化数据库
    if not Path("mbti_test.db").exists():
        init_database()

    # 检查 .env 文件
    if not Path(".env").exists():
        print("\n⚠️  未找到 .env 文件")
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("已复制 .env.example 为 .env")
            print("⚠️  请编辑 .env 文件，填入 DEEPSEEK_API_KEY")
            sys.exit(1)

    # 启动开发服务器
    try:
        start_dev()
    except KeyboardInterrupt:
        print("\n\n✅ 服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
