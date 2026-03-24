# MBTI 深度测试系统 - 快速开始

## 5分钟快速上手

### 1. 准备工作

确保你已安装：
- Python 3.9+
- Node.js 18+
- DeepSeek API Key（可在 https://platform.deepseek.com 申请）

### 2. 克隆/下载项目

```bash
cd mbti_project
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY
```

### 4. 一键启动

```bash
python run.py
```

脚本会自动：
- ✅ 检查环境
- ✅ 安装依赖（首次）
- ✅ 初始化数据库
- ✅ 启动前后端服务器

### 5. 访问系统

打开浏览器：
- **测试页面**：http://localhost:3000
- **API 文档**：http://localhost:8000/docs

### 6. 邀请朋友测试

告诉你的朋友：
1. 访问 http://localhost:3000（如果是本地，需要配置内网穿透）
2. 或者直接分享你的 Vercel 部署链接

---

## 部署到线上（Vercel）

### 方式一：使用部署脚本

```bash
chmod +x deploy.sh
./deploy.sh
```

### 方式二：手动部署

1. 推送到 GitHub
2. 在 Vercel 导入项目
3. 添加环境变量 `DEEPSEEK_API_KEY`
4. 点击 Deploy

---

## 项目结构

```
mbti_project/
├── frontend/          # Vue 3 前端
│   ├── src/
│   │   ├── App.vue    # 主页面（答题）
│   │   ├── Admin.vue  # 管理面板
│   │   └── main.js    # 入口
│   └── index.html
├── backend/           # FastAPI 后端
│   ├── app.py         # 主应用
│   ├── evaluator.py   # 评估引擎
│   ├── models.py      # 数据模型
│   └── requirements.txt
├── data/
│   └── mbti_93_questions.json  # 93题题库
├── .env.example       # 环境变量模板
├── run.py             # 本地启动脚本
├── deploy.sh          # 一键部署脚本
├── vercel.json        # Vercel 配置
└── README.md          # 详细文档
```

---

## 功能特性

- ✅ **93道论述题**：基于标准 MBTI Step I 改编
- ✅ **双层LLM评估**：单题分析 + 综合报告
- ✅ **分批处理**：避免上下文过长，性能优化
- ✅ **进度保存**：支持中断续答
- ✅ **管理员控制**：可随时开关API、查看统计
- ✅ **成本监控**：记录每次API调用和费用
- ✅ **响应式设计**：手机/电脑都能用
- ✅ **一键部署**：Vercel 自动配置

---

## 常见问题

### Q: API调用失败？
A: 检查 `.env` 中的 `DEEPSEEK_API_KEY` 是否正确，API余额是否充足。

### Q: 部署后无法访问？
A: 确保在 Vercel 环境变量中设置了 `DEEPSEEK_API_KEY`，并检查 `API_ENABLED=true`。

### Q: 如何重置测试？
A: 点击结果页的"重新测试"按钮，或清除浏览器本地存储。

### Q: 支持哪些浏览器？
A: 所有现代浏览器（Chrome, Firefox, Safari, Edge）

---

## 技术支持

- 查看详细文档：[README.md](./README.md)
- 部署指南：[DEPLOY.md](./DEPLOY.md)
- 问题反馈：创建 GitHub Issue

---

祝你测试愉快！🎉
