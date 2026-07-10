# MySQL 部署检查

后端固定使用 MySQL 数据库：

```text
mysql+pymysql://root:root@127.0.0.1:3306/finance_data?charset=utf8mb4
```

服务器部署时，请确认 `.env` 里是：

```env
DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/finance_data?charset=utf8mb4
```

## 1. 创建数据库

```bash
mysql -uroot -proot -e "CREATE DATABASE IF NOT EXISTS finance_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

## 2. 安装依赖

```bash
pip install -r requirements.txt
```

依赖里必须包含：

```text
PyMySQL
```

## 3. 创建数据表

在 `backend` 目录执行：

```bash
alembic upgrade head
```

执行后应该有这些表：

```text
alembic_version
users
expenses
monthly_incomes
```

## 4. 重启后端

如果是 systemd：

```bash
systemctl restart finance-mobile-backend
```

如果是手动启动：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## 5. 验证接口

本地服务器验证：

```bash
curl http://127.0.0.1:8002/health/database
```

通过 Nginx 验证：

```bash
curl http://114.67.226.81/mobile-api/health/database
```

正常结果里应该看到：

```json
{
  "status": "ok",
  "database": "finance_data",
  "required_tables_ready": true
}
```

如果登录接口返回 500，而本地测试返回 401，通常是服务器后端没有连上 MySQL、数据库不是 `finance_data`、表没迁移，或者后端代码没有重启到最新版。
