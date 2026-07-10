# Yun Accounting Backend Docker Deploy

Build on the cloud server after uploading this backend source directory:

```bash
docker build --no-cache -t yun-accounting-backend .
```

Run example:

```bash
docker rm -f yun-accounting-backend || true
docker run -d --name yun-accounting-backend \
  -p 8002:8002 \
  -e DATABASE_URL='mysql+pymysql://root:root@mysql:3306/finance_data?charset=utf8mb4' \
  -e SECRET_KEY='change-this-secret-key' \
  -e CORS_ORIGINS='http://117.72.246.88,http://117.72.246.88:80' \
  yun-accounting-backend
```

If MySQL is not in Docker, do not use `127.0.0.1` inside the container unless MySQL is also inside that same container. Use the database container name, host gateway, or server private IP instead.

Verify:

```bash
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8002/health/database
curl http://127.0.0.1:8002/health/routes
```

`/health/routes` should include:

```text
/api/auth/register
/api/auth/login
/api/expenses
/api/incomes/monthly
/api/stats/overview
/api/data/export
/api/data/import
```

If `/health/routes` only shows `/health`, the container was not built from the current backend source or it is not starting `uvicorn app.main:app`.
