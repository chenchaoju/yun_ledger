# 财务管理系统-手机版本

这是基于 `finance-analysis-system` 创建的手机版独立项目，前端和后端都放在当前目录里。

手机版独立后端：

```text
D:\pycharmproject\pythonProject\财务管理系统-手机版本\backend
```

收纳箱里单独注册为 `finance-mobile-backend`，本地端口是 `8024`，连接 MySQL `finance_data` 数据库。

## 本地启动

上云部署时不再依赖 `finance-analysis-system\backend`，直接上传本项目里的 `backend` 和前端 `dist` 即可。

```powershell
"C:\Users\Administrator\AppData\Local\OpenAI\Codex\bin\node.exe" node_modules\vite\bin\vite.js --host 0.0.0.0 --port 8023
```

默认通过 Vite 代理把 `/api` 和 `/mobile-api` 转发到：

```text
http://127.0.0.1:8024
```

## 收纳箱端口

- 手机版前端：`http://127.0.0.1:8023/mobile/`
- 内网手机访问：`http://10.10.3.37:8023/mobile/`
- 手机版后端：`finance-mobile-backend`，端口 `8024`
- 本地 API：`http://127.0.0.1:8023/api`

## 上云路径

服务器如果按下面方式访问：

```text
http://服务器IP/mobile/
http://服务器IP/mobile-api/docs
```

前端生产构建默认会请求：

```text
/mobile-api/api
```

也就是登录接口会请求：

```text
/mobile-api/api/auth/login
```

如果你的 Nginx 已经把 `/mobile-api` 直接转发到了后端的 `/api` 路由，也可以在构建时指定：

```powershell
$env:VITE_API_BASE_URL='/mobile-api'
npm run build
```

## 设计目标

- 手机优先布局
- 底部导航
- 记录列表卡片化
- 弹窗宽度适配小屏幕
- 桌面打开时也以手机宽度预览
