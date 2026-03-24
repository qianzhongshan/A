#!/bin/bash
# MBTI 深度测试系统 - 一键部署脚本

set -e

echo "🚀 开始部署 MBTI 深度测试系统..."

# 检查必要工具
command -v git >/dev/null 2>&1 || { echo "❌ 需要 git，请先安装"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ 需要 Node.js，请先安装"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ 需要 Python3，请先安装"; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "❌ 需要 pip3，请先安装"; exit 1; }

# 检查是否安装了 vercel
if ! command -v vercel &> /dev/null; then
    echo "📦 安装 Vercel CLI..."
    npm install -g vercel
fi

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，请复制 .env.example 为 .env 并填入配置"
    cp .env.example .env
    echo "请编辑 .env 文件后重新运行部署脚本"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
npm run install:all

# 检查 DeepSeek API Key
if grep -q "your_deepseek_api_key_here" .env; then
    echo "❌ 请先在 .env 文件中设置有效的 DEEPSEEK_API_KEY"
    exit 1
fi

# 初始化数据库
echo "🗄️  初始化数据库..."
cd backend
python3 -c "from database import init_db; init_db()"
cd ..

# 本地测试
read -p "是否进行本地测试？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 启动本地测试服务器..."
    npm run dev &
    TEST_PID=$!
    echo "测试服务器 PID: $TEST_PID"
    echo "前端: http://localhost:3000"
    echo "后端: http://localhost:8000"
    echo "API文档: http://localhost:8000/docs"
    echo "按 Ctrl+C 停止测试"
    wait $TEST_PID
    exit 0
fi

# 部署到 Vercel
read -p "准备部署到 Vercel？这需要你的确认 (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 部署到 Vercel..."
    vercel --prod
else
    echo "✅ 部署准备就绪"
    echo "你可以随时运行 'vercel --prod' 来部署"
fi
