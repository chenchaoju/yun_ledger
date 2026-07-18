# app_stack 部署说明

云记账上云后应由服务器的 `/opt/app_stack/docker-compose.yml` 统一启动。

不要在 `/opt/yun_ledger` 单独执行 `docker compose up`，否则容易重复创建 MySQL、Nginx 和 API 容器，端口、数据卷和网络也会混乱。

常用命令：

```bash
cd /opt/app_stack
docker compose up -d --build
docker compose ps
docker compose logs -f api
```

云记账相关路径：

- 后端构建目录：`/opt/yun_ledger/backend`
- PC 前端静态文件：`/opt/yun_ledger/pc_frontend/dist`
- 手机端静态文件：`/opt/yun_ledger/mobile_frontend/dist`
- Nginx 配置：`/opt/app_stack/nginx/default.conf`
- MySQL 数据卷：`/opt/app_stack/mysql_data`

本目录的 `docker-compose.cloud.yml` 是 app_stack 的模板副本，需要同步到服务器 `/opt/app_stack/docker-compose.yml`。
