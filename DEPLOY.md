# 部署指南

## 快速部署到 Vercel (推荐)

本项目可以一键部署到 Vercel，享受全球CDN和自动HTTPS。

### 前置要求
- Vercel 账号 (免费)
- GitHub 账号 (用于仓库)
- DeepSeek API Key

### 部署步骤

1. **上传代码到 GitHub**
   ```bash
   cd mbti_project
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/mbti-deep-test.git
   git push -u origin main
   ```

2. **在 Vercel 导入项目**
   - 访问 https://vercel.com/new
   - 选择 "Import Git Repository"
   - 选择你的仓库
   - Vercel 会自动检测为 Vite 项目，保持默认配置
   - 添加环境变量（见下方）
   - 点击 "Deploy"

3. **配置环境变量**
   在 Vercel 项目设置的 "Environment Variables" 中添加：
   ```
   DEEPSEEK_API_KEY=your_actual_api_key_here
   DEEPSEEK_BASE_URL=https://api.deepseek.com
   DEEPSEEK_MODEL=deepseek-chat
   API_ENABLED=true
   ```

4. **等待部署完成**
   Vercel 会自动构建和部署，完成后会给你一个类似 `https://mbti-deep-test.vercel.app` 的链接

## 环境变量配置

必需的环境变量：
- `DEEPSEEK_API_KEY` - DeepSeek API密钥
- `DEEPSEEK_BASE_URL` - API地址（默认 https://api.deepseek.com）
- `DEEPSEEK_MODEL` - 模型名称（默认 deepseek-chat）

可选的环境变量：
- `API_ENABLED` - 是否启用API评估（默认 true）
- `ADMIN_USERNAME` - 管理员用户名（默认 admin）
- `ADMIN_PASSWORD_HASH` - 管理员密码bcrypt哈希

## 本地运行

### 开发模式
```bash
# 安装所有依赖
npm run install:all

# 启动开发服务器（后端+前端）
npm run dev

# 或分别启动
# 后端：cd backend && uvicorn app:app --reload
# 前端：cd frontend && npm run dev
```

访问：
- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 生产构建
```bash
npm run build
# 构建后的文件在 frontend/dist/ 目录
```

## 数据库

默认使用 SQLite（文件 `mbti_test.db`），无需额外配置。

如需使用 PostgreSQL（更适合生产）：
1. 修改 `backend/config.py` 中的 `DATABASE_URL`
2. 安装依赖：`pip install psycopg2-binary`

## 管理员面板

部署后访问 `/admin` 路径：
- 查看系统统计
- 开关API功能
- 导出数据

## 成本控制

- 单用户约 200 次 API 调用（93题评估 + 1次报告）
- DeepSeek 约 ¥0.001/千tokens
- 单用户成本约 ¥0.1-0.5
- 可在 `config.py` 中设置 `DAILY_API_LIMIT` 限制每日调用

## 安全建议

1. **保护 API Key**：确保环境变量不泄露
2. **限制访问**：生产环境设置 `CORS_ALLOWED_ORIGINS` 限制前端域名
3. **管理员密码**：设置 `ADMIN_PASSWORD_HASH` 并启用登录
4. **HTTPS**：Vercel 自动提供 HTTPS

## 故障排除

### API调用失败
- 检查 `DEEPSEEK_API_KEY` 是否正确
- 检查 API 余额是否充足
- 查看后端日志

### 部署失败
- 确保 Vercel 构建命令正确（默认自动检测）
- 检查 Node.js 和 Python 版本要求
- 查看 Vercel 构建日志

## 更新部署

```bash
git add .
git commit -m "Update"
git push
# Vercel 会自动重新部署
```

---

有任何问题？查看项目 README.md 或提 Issue。
