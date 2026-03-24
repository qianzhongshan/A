# MBTI 93题论述版测试系统

一个基于深度学习的MBTI性格测试系统，使用DeepSeek API进行双层评估，支持93道开放式论述题的智能分析。

## 功能特点

- ✅ 93道论述题，覆盖四个维度（EI/SN/TF/JP）
- ✅ 双层LLM评估架构，精准分析
- ✅ 分批处理，避免上下文过长
- ✅ 进度保存，可中断续答
- ✅ 管理员控制面板，可开关API
- ✅ 成本监控，避免超额
- ✅ 响应式设计，移动端友好

## 技术栈

- **前端**: Vue 3 + Vite + TailwindCSS
- **后端**: Python FastAPI
- **数据库**: SQLite
- **LLM**: DeepSeek API
- **部署**: Vercel (全栈)

## 项目结构

```
mbti_project/
├── frontend/          # Vue 3 前端
│   ├── src/
│   │   ├── views/    # 页面组件
│   │   ├── components/
│   │   └── utils/
│   └── index.html
├── backend/           # FastAPI 后端
│   ├── app.py        # 主应用
│   ├── models.py     # 数据模型
│   ├── evaluator.py  # 评估引擎
│   ├── config.py     # 配置管理
│   └── requirements.txt
├── data/
│   ├── mbti_93_questions.json  # 题库
│   ├── sessions/              # 会话数据
│   └── logs/                  # API调用日志
├── scripts/
│   └── deploy.sh     # 部署脚本
└── README.md
```

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.9+
- DeepSeek API Key

### 安装步骤

1. 克隆或下载项目
2. 安装依赖：
   ```bash
   cd frontend && npm install
   pip install -r backend/requirements.txt
   ```
3. 配置环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env，填入 DEEPSEEK_API_KEY
   ```
4. 启动开发服务器：
   ```bash
   # 后端
   cd backend && uvicorn app:app --reload
   # 前端
   cd frontend && npm run dev
   ```

5. 访问 http://localhost:3000

## 部署到 Vercel

```bash
# 一键部署
vercel --prod
```

## 管理员控制

访问 `/admin` 路径：
- 开关API功能
- 查看使用统计
- 导出数据
- 管理会话

## 安全说明

- API密钥存储在环境变量中，不会暴露给前端
- 管理员密码使用bcrypt加密
- 所有API调用记录日志
- 可设置每日调用上限

## 成本估算

- 93题 × 2次LLM调用 ≈ 200次API调用
- DeepSeek约0.001元/千tokens
- 单用户成本约0.1-0.5元

## License

MIT
