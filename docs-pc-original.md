# 个人消费记录与统计分析网站

这是一个面向个人用户的支出记录网站，包含账户登录、日常消费记录、分类统计、月度结构分析和年度趋势图表。不包含投资、理财产品推荐或收益预测功能。

## 技术栈

- 前端：Vue 3、Vite、Vue Router、Pinia、Axios、Element Plus、ECharts、Day.js
- 后端：Python、FastAPI、Uvicorn、SQLAlchemy、Alembic、Pydantic、JWT、Passlib / bcrypt
- 数据库：PostgreSQL

## 本地启动

1. 准备 PostgreSQL 数据库 `data`。
2. 复制 `backend/.env.example` 为 `backend/.env`，按需修改 `DATABASE_URL` 和 `SECRET_KEY`。
3. 推荐直接运行一键启动脚本：

```bat
start.bat
```

脚本会安装缺失依赖、执行 Alembic 迁移，并启动前后端服务。

也可以手动安装后端依赖并迁移数据库：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. 安装并启动前端：

```bash
cd frontend
npm install
npm run dev
```

前端默认地址是 `http://localhost:5173`，接口通过 Vite 代理转发到 `http://127.0.0.1:8000`。
