# 云记账

这是从以下两个项目合并出的新项目：

- `D:\pycharmproject\pythonProject\finance-analysis-system`：PC 版前端
- `D:\pycharmproject\pythonProject\财务管理系统-手机版本`：手机版前端和较新的后端

新项目保留两套前端界面，统一使用一个后端和同一个 MySQL 数据库。

## 目录

```text
backend/  共享 FastAPI 后端，统一连接 MySQL finance_data
pc/       PC 版 Vue 前端，默认 http://127.0.0.1:5173/
mobile/   手机版 Vue 前端，默认 http://127.0.0.1:8023/mobile/
scripts/  本地启动脚本
```

## 数据库合并

两个原项目默认都连接 `finance_data`，所以新项目继续使用这一个数据库，达到 PC 版和手机版数据共用。后端采用手机版较新的迁移版本，包含 PC 版已有表结构，并额外包含 `users.default_salary_income` 字段。

首次运行前请确认 MySQL 已有数据库：

```sql
CREATE DATABASE IF NOT EXISTS finance_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

如果数据库账号不是 `root/root`，复制并修改：

```powershell
Copy-Item backend\.env.example backend\.env
```

然后编辑 `backend\.env` 里的 `DATABASE_URL`。

## 一键启动

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

脚本会安装依赖、执行 Alembic 迁移，并分别启动后端、PC 版和手机版。

启动地址：

- PC 版：`http://127.0.0.1:5173/`
- 手机版：`http://127.0.0.1:8023/mobile/`
- 后端接口：`http://127.0.0.1:8024/docs`

停止本地服务：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop.ps1
```

## 手动启动

后端：

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8024
```

PC 版：

```powershell
cd pc
npm install
npm run dev
```

手机版：

```powershell
cd mobile
npm install
npm run dev
```

## 构建

```powershell
npm run build
```

也可以分别构建：

```powershell
npm run pc:build
npm run mobile:build
```
