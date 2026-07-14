# 云记账（Yun Accounting）Code Wiki

> 本文档是对「云记账」项目仓库的结构化代码百科（Code Wiki），基于实际源码梳理而成。
> 内容涵盖：项目整体架构、目录结构、各模块职责、关键类与函数说明、数据模型与依赖关系、API 接口参考、数据流，以及项目运行与部署方式。
>
> 适用读者：项目维护者、新接手开发者、代码审查者。
> 最后更新：2026-07-14

---

## 目录

- [一、项目概览](#一项目概览)
- [二、整体架构](#二整体架构)
- [三、目录结构](#三目录结构)
- [四、后端模块详解（backend/）](#四后端模块详解backend)
  - [4.1 应用入口 app/main.py](#41-应用入口-appmainpy)
  - [4.2 配置与安全 app/core/](#42-配置与安全-appcore)
  - [4.3 数据库层 app/db/](#43-数据库层-appdb)
  - [4.4 数据模型 app/models/](#44-数据模型-appmodels)
  - [4.5 数据校验 app/schemas/](#45-数据校验-appschemas)
  - [4.6 依赖注入 app/api/deps.py](#46-依赖注入-appapidepspy)
  - [4.7 API 路由 app/api/routes/](#47-api-路由-appapiroutes)
  - [4.8 服务层 app/services/](#48-服务层-appservices)
  - [4.9 数据库迁移 alembic/](#49-数据库迁移-alembic)
- [五、PC 端前端模块详解（pc/）](#五pc-端前端模块详解pc)
- [六、移动端前端模块详解（mobile/）](#六移动端前端模块详解mobile)
- [七、数据模型与关系](#七数据模型与关系)
- [八、API 接口参考](#八api-接口参考)
- [九、依赖关系](#九依赖关系)
- [十、核心数据流](#十核心数据流)
- [十一、项目运行方式](#十一项目运行方式)
- [十二、部署方式](#十二部署方式)
- [附录：技术栈速查表](#附录技术栈速查表)

---

## 一、项目概览

**云记账**是一个个人财务管理应用，由两个独立项目合并而成：

- `finance-analysis-system`：原 PC 版前端
- `财务管理系统-手机版本`：原手机版前端 + 较新的后端

合并后保留 **两套前端**（PC 端 + 移动端），共享 **同一个 FastAPI 后端** 与 **同一个 MySQL 数据库**（`finance_data`），实现 PC 版与手机版数据互通。

### 核心功能

| 功能域 | 说明 |
|--------|------|
| 用户认证 | 注册 / 登录 / 个人资料维护，基于 JWT |
| 支出管理 | 支出记录的增删改查，支持日期范围与分类筛选 |
| 收入管理 | 月度收入（工资 + 额外收入明细）的录入与回退 |
| 统计分析 | 月/年支出汇总、分类占比、月度趋势、每日支出、年度账单 |
| 数据迁移 | 全量数据导出为 JSON、从 JSON 覆盖导入（事务保护） |
| 移动端增强 | 自定义分类管理、头像设置、记住密码/自动登录、悬浮快捷记账 |

---

## 二、整体架构

### 2.1 分层架构

```
┌──────────────────────────────────────────────────────────┐
│                     浏览器（用户终端）                       │
│   PC 端 (Element Plus)      移动端 (Element Plus + 移动样式)  │
└───────────────┬──────────────────────┬───────────────────┘
                │  HTTP + JWT(Bearer)  │
                ▼                      ▼
┌──────────────────────────────────────────────────────────┐
│              后端 API（FastAPI，统一 /api 前缀）              │
│   routes: auth / expenses / incomes / stats / data        │
│   依赖注入 · Pydantic 校验 · 服务层 · ORM 模型              │
└───────────────┬──────────────────────────┬───────────────┘
                │  SQLAlchemy 2.0 ORM       │ Alembic 迁移
                ▼                          ▼
┌──────────────────────────────────────────────────────────┐
│        数据库（MySQL finance_data，开发可回退 SQLite）        │
│        users · expenses · monthly_incomes · alembic_version │
└──────────────────────────────────────────────────────────┘
```

### 2.2 通信约定

- **协议**：RESTful HTTP，JSON 数据格式。
- **鉴权**：除注册/登录外，所有接口需在请求头携带 `Authorization: Bearer <token>`。
- **令牌**：JWT（HS256），载荷 `sub` 为用户 ID 字符串，有效期默认 7 天。
- **跨域**：后端通过 `CORSMiddleware` 放行 PC/移动端开发地址；生产由 Nginx 同源代理。
- **开发代理**：前端 Vite 将 `/api` 代理到后端 `http://127.0.0.1:8024`，规避开发期跨域。

### 2.3 两套前端的差异定位

| 维度 | PC 端 (`pc/`) | 移动端 (`mobile/`) |
|------|---------------|--------------------|
| UI 框架 | Element Plus | Element Plus（同 PC，配合移动样式） |
| base 路径 | `/pc/` | `/mobile/` |
| 开发端口 | 5173 | 8023 |
| 布局 | 侧边栏 + 顶栏 | 侧边栏 + 顶栏 + 悬浮快捷按钮 |
| 分类管理 | 仅使用内置分类 | 内置 + 自定义分类 + 隐藏分类（localStorage） |
| 头像 | 无 | 有（localStorage 持久化） |
| 登录增强 | 基础登录 | 记住密码 / 自动登录 |
| 快捷记账 | 列表内新增 | 全局悬浮 `QuickAddButton`（带数字键盘） |

> 说明：移动端与 PC 端共用 Element Plus 组件库，差异通过 CSS 响应式与移动端专属组件（如数字键盘、悬浮按钮、自定义分类）体现，而非更换 UI 框架。

---

## 三、目录结构

```text
yun-accounting/
├── backend/                      # FastAPI 后端
│   ├── alembic/                  # 数据库迁移
│   │   ├── env.py                # Alembic 运行环境配置
│   │   └── versions/             # 迁移脚本（0001~0006）
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py           # 依赖注入（DB 会话、当前用户）
│   │   │   └── routes/           # 路由模块
│   │   │       ├── auth.py
│   │   │       ├── expenses.py
│   │   │       ├── incomes.py
│   │   │       ├── stats.py
│   │   │       └── data_transfer.py
│   │   ├── core/
│   │   │   ├── config.py         # Settings 配置
│   │   │   └── security.py       # 密码哈希 / JWT
│   │   ├── db/
│   │   │   ├── base.py           # DeclarativeBase
│   │   │   └── session.py        # engine / SessionLocal
│   │   ├── models/               # SQLAlchemy 模型
│   │   ├── schemas/              # Pydantic 模型
│   │   ├── services/
│   │   │   └── income_items.py   # 额外收入明细处理
│   │   └── main.py               # 应用入口
│   ├── Dockerfile
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
├── pc/                           # PC 端 Vue3 前端
│   ├── src/
│   │   ├── components/           # 公共组件
│   │   ├── constants/            # 分类常量
│   │   ├── router/               # 路由
│   │   ├── stores/               # Pinia 状态
│   │   ├── styles/               # 样式
│   │   ├── utils/                # 工具函数
│   │   ├── views/                # 页面
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── mobile/                       # 移动端 Vue3 前端
│   ├── public/                   # 默认头像等静态资源
│   ├── src/                      # 结构同 pc/，含移动端专属组件
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── deploy/
│   └── nginx-yun-accounting.conf # Nginx 反向代理配置
├── scripts/                      # 本地启动/停止脚本（PowerShell）
│   ├── start.ps1
│   ├── stop.ps1
│   ├── dev-frontend.ps1
│   └── quick-start.bat
├── package.json                  # 根级脚本（pc/mobile 构建）
├── README.md
└── CODE_WIKI.md                  # 本文档
```

---

## 四、后端模块详解（backend/）

后端基于 **FastAPI + SQLAlchemy 2.0 + Pydantic v2**，采用「路由 → 服务 → 模型」分层。所有金额使用 `Decimal`/`Numeric(12, 2)` 存储以避免浮点精度问题。

### 4.1 应用入口 `app/main.py`

**职责**：创建 FastAPI 应用实例，注册中间件、路由与健康检查端点。

**关键逻辑**：
- `FastAPI(title=settings.app_name)` 创建应用；
- `CORSMiddleware` 按 `settings.cors_origin_list` 放行跨域；
- 以 `settings.api_prefix`（`/api`）为统一前缀注册 5 个路由模块；
- 提供 3 个健康检查端点。

**健康检查端点**：

| 路径 | 方法 | 作用 |
|------|------|------|
| `/health` | GET | 返回 `{"status": "ok"}` |
| `/health/database` | GET | 检查数据库连接、列出表、校验必备表是否就绪 |
| `/health/routes` | GET | 列出应用已注册的全部路由（排除 HEAD/OPTIONS） |

### 4.2 配置与安全 `app/core/`

#### `app/core/config.py` — Settings 配置类

**职责**：集中管理配置项，从 `backend/.env` 读取，`lru_cache` 单例化。

**类**：`Settings(BaseSettings)`

**配置项**：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `app_name` | str | `"云记账"` | 应用名称 |
| `environment` | str | `"development"` | 环境标识 |
| `api_prefix` | str | `"/api"` | API 路由统一前缀 |
| `secret_key` | str | `"change-this-secret-key"` | JWT 签名密钥 |
| `access_token_expire_minutes` | int | `10080`（7 天） | 令牌有效期（分钟） |
| `database_url` | str | `mysql+pymysql://root:root@127.0.0.1:3306/finance_data?charset=utf8mb4` | 数据库连接串 |
| `cors_origins` | str | 本地 PC/移动端地址 | 逗号分隔的跨域来源 |

**关键方法/属性**：
- `cors_origin_list -> list[str]`：将 `cors_origins` 拆分为列表。
- `get_settings() -> Settings`：`@lru_cache` 缓存的工厂函数。
- `model_config`：指定 `.env` 文件位置为 `backend/.env`，UTF-8 编码，大小写不敏感。

#### `app/core/security.py` — 安全模块

**职责**：密码哈希与 JWT 编解码。

| 函数 | 签名 | 说明 |
|------|------|------|
| `verify_password` | `(plain_password: str, password_hash: str) -> bool` | 用 bcrypt 校验明文密码 |
| `get_password_hash` | `(password: str) -> str` | 生成 bcrypt 哈希 |
| `create_access_token` | `(subject: str) -> str` | 以 `subject` 为 `sub` 生成 JWT（含过期时间） |
| `decode_access_token` | `(token: str) -> dict` | 解码 JWT，失败抛 `ValueError("Invalid token")` |

- 算法：`ALGORITHM = "HS256"`；
- 哈希上下文：`CryptContext(schemes=["bcrypt"], deprecated="auto")`。

### 4.3 数据库层 `app/db/`

#### `app/db/base.py`

```python
class Base(DeclarativeBase):
    pass
```
所有 ORM 模型的公共基类，承载 `Base.metadata` 供 Alembic 使用。

#### `app/db/session.py`

**职责**：创建全局 `engine` 与 `SessionLocal` 会话工厂。

- 读取 `settings.database_url` 创建 `create_engine(..., pool_pre_ping=True)`；
- 若为 SQLite，附加 `connect_args={"check_same_thread": False}`；
- `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`。

### 4.4 数据模型 `app/models/`

详见 [七、数据模型与关系](#七数据模型与关系)。`app/models/__init__.py` 统一导出 `Expense`、`MonthlyIncome`、`User`，供 Alembic `env.py` 导入以注册元数据。

### 4.5 数据校验 `app/schemas/`

基于 **Pydantic v2**，承担请求体校验与响应序列化。

#### `schemas/auth.py`

| Schema | 用途 | 关键约束 |
|--------|------|---------|
| `UserCreate` | 注册请求 | `email: 3~255`，`password: 8~128` |
| `LoginRequest` | 登录请求 | `email: 3~255`，`password: 1~128` |
| `UserUpdate` | 更新资料 | `username?`、`default_salary_income?`（≥0） |
| `UserRead` | 返回用户信息 | 含 `id/email/username/default_salary_income/created_at`，`from_attributes=True` |
| `TokenResponse` | 登录/注册返回 | `access_token` + `token_type="bearer"` + `user: UserRead` |

#### `schemas/expense.py`

| Schema | 用途 | 关键约束 |
|--------|------|---------|
| `ExpenseBase` | 支出基类 | `amount: Decimal >0`（12,2），`category: 1~60`，`spent_at: date`，`note?`；`category`/`note` 自动 `strip()`，空串转 `None` |
| `ExpenseCreate` | 创建 | 继承 `ExpenseBase` |
| `ExpenseUpdate` | 更新 | 所有字段可选 |
| `ExpenseRead` | 返回 | 含 `id/user_id/created_at/updated_at` |
| `ExpenseList` | 列表 | `items: list[ExpenseRead]` + `total: int` |

#### `schemas/income.py`

| Schema | 用途 | 关键约束 |
|--------|------|---------|
| `ExtraIncomeItem` | 单条额外收入 | `name: 1~60`（默认"额外收入"，before 校验清洗），`amount: Decimal >0` |
| `ExtraIncomeItemRead` | 返回额外收入明细 | `name: str`, `amount: float` |
| `MonthlyIncomeUpsert` | 月收入 upsert | `year: 1970~2100`，`month: 1~12`，`salary_income ≥0`，`extra_income?`，`extra_income_items: list` |
| `MonthlyIncomeRead` | 返回月收入 | 含 `total_income`，`id` 可空（无记录时） |

#### `schemas/stats.py`

| Schema | 用途 |
|--------|------|
| `CategorySummary` | 分类汇总（`category/total/count`） |
| `StructureSummary` | 收支结构（`name/type/total/count`） |
| `ExtraIncomeSummary` | 额外收入汇总（`name/amount`） |
| `TrendPoint` | 月度趋势点（含工资/额外/总收入、结余、是否超支） |
| `DailyExpensePoint` | 每日支出点（`day/total`） |
| `MonthlyIncomeSummary` | 月收入汇总（含 `balance`、`salary_balance`、`is_over_salary`） |
| `OverviewStats` | 概览聚合（月/年总额、均日、收入、分类、结构、趋势、每日、最近记录） |

### 4.6 依赖注入 `app/api/deps.py`

**职责**：提供可复用的 FastAPI 依赖函数。

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_db` | `() -> Generator[Session]` | 每请求创建会话，结束自动关闭 |
| `get_current_user` | `(token, db) -> User` | 解码 JWT 取 `sub` → 查 `User`；无效则抛 401 |

- `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")`；
- 401 错误信息为「登录状态已失效」，并带 `WWW-Authenticate: Bearer` 头。

### 4.7 API 路由 `app/api/routes/`

#### `routes/auth.py`（前缀 `/api/auth`，tags: auth）

| 函数 | 方法·路径 | 响应模型 | 说明 |
|------|-----------|---------|------|
| `register` | POST `/register` | `TokenResponse`（201） | 邮箱转小写；若已存在但无密码则补设密码；否则新建用户并返回令牌 |
| `login` | POST `/login` | `TokenResponse` | 校验密码，返回令牌 |
| `read_me` | GET `/me` | `UserRead` | 返回当前用户 |
| `update_me` | PUT `/me` | `UserRead` | 更新 `username`/`default_salary_income` |

- 辅助函数 `build_token_response(user)`：组装 `TokenResponse`。

#### `routes/expenses.py`（前缀 `/api/expenses`，tags: expenses）

| 函数 | 方法·路径 | 说明 |
|------|-----------|------|
| `list_expenses` | GET `` | 分页（`limit ≤100`、`offset`）+ 日期范围 + 分类筛选，按 `spent_at`、`id` 倒序 |
| `create_expense` | POST `` | 201 创建 |
| `read_expense` | GET `/{id}` | 取详情（仅本人） |
| `update_expense` | PUT `/{id}` | 部分更新（`exclude_unset`） |
| `delete_expense` | DELETE `/{id}` | 204 删除 |

- 辅助函数 `get_owned_expense(expense_id, user_id, db)`：查询并校验归属，不存在抛 404「记录不存在」。

#### `routes/incomes.py`（前缀 `/api/incomes`，tags: incomes）

| 函数 | 方法·路径 | 说明 |
|------|-----------|------|
| `get_monthly_income` | GET `/monthly` | 查询参数 `year/month`；无记录时回退用户 `default_salary_income` |
| `upsert_monthly_income` | PUT `/monthly` | Upsert：存在则更新，否则创建；明细经 `normalize_extra_income_items` 规范化 |

- 辅助函数：
  - `to_float(value)`：安全转 `float` 并保留 2 位。
  - `read_or_default(user, year, month, db)`：返回 `MonthlyIncomeRead`，无记录则构造默认值。

#### `routes/stats.py`（前缀 `/api/stats`，tags: stats）

| 函数 | 方法·路径 | 说明 |
|------|-----------|------|
| `overview` | GET `/overview` | 查询参数 `year?/month?`（缺省取今天）；返回 `OverviewStats` |

**`overview` 计算内容**：
1. 当月/当年支出总额与笔数；
2. 当月分类汇总（按金额降序）；
3. 当年逐月趋势（1~12 月，含收入与结余）；
4. 当月每日支出（1~月末天数）；
5. 最近 6 条支出记录；
6. 月收入汇总（含 `is_over_salary` 超支标记）；
7. 日均支出（当月取今日天数，否则取整月天数）。

#### `routes/data_transfer.py`（前缀 `/api/data`，tags: data）

| 函数 | 方法·路径 | 说明 |
|------|-----------|------|
| `export_data` | GET `/export` | 导出当前用户全部支出 + 月收入，含 `version=1` 与 `exported_at` |
| `import_data` | POST `/import` | 事务内删除旧数据 → 插入新数据；失败回滚；返回导入计数 |

**内部 Schema**：`DataTransferExpense`、`DataTransferMonthlyIncome`、`DataTransferPayload`（`version=1`）、`DataImportResult`。
**导入注意**：月收入按 `(year, month)` 去重后写入；导入前会校验 `version == 1`，否则 400。

### 4.8 服务层 `app/services/`

#### `app/services/income_items.py` — 额外收入明细处理

**职责**：统一处理「额外收入明细列表」的精度、规范化与合计。

| 函数 | 签名 | 说明 |
|------|------|------|
| `amount_to_decimal` | `(value: Any) -> Decimal` | 转 `Decimal` 并 `quantize("0.01", ROUND_HALF_UP)`，异常归零 |
| `item_value` | `(item, key, default) -> Any` | 兼容 dict / 对象取值 |
| `normalize_extra_income_items` | `(items, fallback_extra_income) -> list[dict[str, float]]` | 清洗名称、过滤金额≤0、限长 60；列表为空时回退 `fallback_extra_income` 生成单项 |
| `extra_income_total` | `(items) -> Decimal` | 汇总明细金额，2 位精度 |

- 常量：`DEFAULT_EXTRA_INCOME_NAME = "额外收入"`，`AMOUNT_QUANT = Decimal("0.01")`。

### 4.9 数据库迁移 `alembic/`

- `alembic.ini`：Alembic 配置（`script_location` 指向 `alembic/`）。
- `alembic/env.py`：将 `sys.path` 加入 backend 根，导入 `app.models` 注册元数据；`get_url()` 从 `Settings` 取库地址（`%` 转义为 `%%`）；`compare_type=True`。
- `alembic/versions/`：迁移脚本链。
  - `0001_initial`：初始建表（`users`/`expenses`/`monthly_incomes`，含 MySQL 字符集处理与索引幂等创建）；
  - `0002_align_postgresql_users`：对齐 PG 用户表；
  - `0003_monthly_incomes`：月收入表结构；
  - `0004_extra_income_items`：新增 `extra_income_items` JSON 字段；
  - `0005_user_username`：用户表新增 `username`；
  - `0006_user_default_salary`：用户表新增 `default_salary_income`。

**常用命令**：
```bash
alembic revision --autogenerate -m "描述"
alembic upgrade head
alembic current
```

---

## 五、PC 端前端模块详解（pc/）

技术栈：Vue 3（`<script setup>`）+ Vite 6 + Pinia + Vue Router 4 + Element Plus + ECharts + Axios + Day.js。

### 5.1 入口与配置

| 文件 | 职责 |
|------|------|
| `pc/src/main.js` | 创建 Vue 应用，注册 Pinia / Router / Element Plus，挂载 `#app` |
| `pc/src/App.vue` | 根组件，仅渲染 `<RouterView />` |
| `pc/vite.config.js` | `base: '/pc/'`；dev 端口 5173；`/api` 代理到 `VITE_API_PROXY_TARGET \|\| http://127.0.0.1:8024` |
| `pc/package.json` | 依赖与 PC 端 `dev/build/preview` 脚本 |

### 5.2 路由 `pc/src/router/index.js`

| 路径 | 组件 | 需登录 | 说明 |
|------|------|--------|------|
| `/login` | LoginView | 否 | 登录/注册页 |
| `/` | AppLayout | 是 | 主布局（含子路由） |
| `/`（子） | DashboardView | 是 | 概览 |
| `/records` | RecordsView | 是 | 记录 |
| `/analysis` | AnalysisView | 是 | 分析 |
| `/settings` | SettingsView | 是 | 设置 |

**路由守卫**：`beforeEach` 中检查 `requiresAuth` 与 `isAuthenticated`，未登录跳 `/login`（带 `redirect`）；已登录访问 `/login` 跳概览。

### 5.3 状态管理 `pc/src/stores/auth.js`

Pinia store `auth`：
- **state**：`token`（localStorage `access_token`）、`user`（localStorage `current_user`）；
- **getter**：`isAuthenticated`；
- **actions**：`setSession`、`login`、`register`、`fetchMe`、`updateProfile`、`logout`。

### 5.4 工具函数 `pc/src/utils/`

| 文件 | 关键导出 | 说明 |
|------|---------|------|
| `http.js` | 默认导出 axios 实例 | `baseURL` 取 `VITE_API_BASE_URL` 或 `/api`；请求拦截注入 `Bearer`；响应拦截 401 清登录态并跳登录页，其它错误 `ElMessage` 提示 |
| `format.js` | `currency(value)`、`percent(value)` | 人民币（`Intl.NumberFormat zh-CN CNY`）与百分比格式化 |
| `events.js` | `FINANCE_DATA_CHANGED`、`notifyFinanceDataChanged()` | 基于 `window.dispatchEvent` 的事件总线，通知数据变更 |
| `authPreferences.js` | 记住密码/自动登录偏好（localStorage） | — |
| `userPreferences.js` | 头像等用户偏好（localStorage） | — |

### 5.5 常量 `pc/src/constants/categories.js`

定义内置支出分类（中文 `label`/`value`、`color`、`icon`），并提供分类颜色映射。

### 5.6 组件 `pc/src/components/`

| 组件 | 职责 |
|------|------|
| `AppLayout.vue` | 主布局：侧边栏（`el-menu` 概览/记录/分析/设置）+ 顶栏（标题、日期）+ `<RouterView />` |
| `BaseChart.vue` | ECharts 封装；接收 `option`/`loading`，`ResizeObserver` 自适应，卸载时 `dispose` |
| `DataTransferButton.vue` | 数据导入导出（导出支持 `showSaveFilePicker`，导入前确认覆盖） |
| `ExpenseFormDialog.vue` | 支出新增/编辑对话框 |
| `IncomeFormDialog.vue` | 月收入录入对话框 |

### 5.7 页面 `pc/src/views/`

| 视图 | 职责 |
|------|------|
| `LoginView.vue` | 登录/注册 Tab 切换、表单校验、登录后跳转 |
| `DashboardView.vue` | 月份选择、收支余额卡片、分类饼图、月度趋势、最近记录 |
| `RecordsView.vue` | 支出列表（筛选/分页/增删改） |
| `AnalysisView.vue` | 分类饼图、月度趋势、每日支出柱状图 |
| `SettingsView.vue` | 用户名/预设工资维护、数据导入导出、退出登录 |

---

## 六、移动端前端模块详解（mobile/）

技术栈与 PC 端一致（Vue 3 + Vite + Pinia + Vue Router + Element Plus + ECharts + Axios + Day.js），针对手机交互做了增强。

### 6.1 入口与配置

| 文件 | 职责 |
|------|------|
| `mobile/src/main.js` | 同 PC：注册 Pinia / Router / Element Plus |
| `mobile/src/App.vue` | 根组件，仅 `<RouterView />` |
| `mobile/vite.config.js` | `base: '/mobile/'`；dev 端口 8023；`/api` 代理到后端 8024 |
| `mobile/package.json` | 名为 `yun-accounting-mobile`，`dev` 监听 `0.0.0.0:8023` |

### 6.2 路由 `mobile/src/router/index.js`

| 路径 | 组件 | 说明 |
|------|------|------|
| `/login` | LoginView | 登录/注册页（带记住密码/自动登录） |
| `/` | AppLayout | 主布局（requiresAuth） |
| `/`（子） | DashboardView | 今日概览 |
| `/records` | RecordsView | 记账明细 |
| `/analysis` | AnalysisView | 收支分析 |
| `/settings` | SettingsView | 个人设置 |

> 注：移动端**没有**独立的 `/categories` 路由页面；分类管理以对话框形式内嵌于 `SettingsView`。

### 6.3 状态管理 `mobile/src/stores/auth.js`

结构与 PC 端一致，`logout` 时额外调用 `disableAutoLoginForSession()` 以抑制自动登录。

### 6.4 工具函数 `mobile/src/utils/`

| 文件 | 关键导出 | 说明 |
|------|---------|------|
| `http.js` | axios 实例 | 同 PC；401 跳转目标路径根据 `BASE_URL` 计算，避免与移动端 `/mobile/` 前缀冲突 |
| `format.js` | `currency`、`percent` | 同 PC |
| `events.js` | `FINANCE_DATA_CHANGED`、`notifyFinanceDataChanged` | 同 PC |
| `authPreferences.js` | `loadAuthPreferences`/`saveAuthPreferences`/`disableAutoLoginForSession`/`clearAutoLoginSkip`/`shouldSkipAutoLogin` | 记住密码与自动登录，使用 localStorage + sessionStorage 协同 |
| `userPreferences.js` | `loadAvatarPreference`/`saveAvatarPreference` | 头像偏好（兼容旧 key `finance_mobile_avatar`） |

### 6.5 常量 `mobile/src/constants/`

#### `categories.js`
- `expenseCategories`：11 个内置分类（餐饮/交通/购物/网购/服务/居住/送礼/娱乐/医疗/教育/其他），含 `color` 与 `icon`。
- 自定义分类：`loadCustomCategories`/`saveCustomCategories`/`buildCustomCategory`（localStorage `finance_mobile_custom_categories`）。
- 隐藏分类：`loadHiddenCategoryValues`/`saveHiddenCategoryValues`（localStorage `finance_mobile_hidden_categories`）。
- `allExpenseCategories({ includeHidden })`：合并内置 + 自定义并按需过滤隐藏项。
- `categoryColorMap` / `categoryColorMapFrom`：分类 → 颜色映射。
- `categoryChangedEvent`：分类变更广播事件。

#### `categoryIcons.js`
- 基于 `@element-plus/icons-vue` 的 17 个图标映射（`categoryIconOptions`）。
- `categoryIconComponents` 与 `categoryIconComponent(icon)`：按图标名取组件，缺省 `MoreFilled`。

### 6.6 组件 `mobile/src/components/`

| 组件 | 职责 |
|------|------|
| `AppLayout.vue` | 主布局：侧边栏（`el-menu` 概览/记录/分析/设置）+ 顶栏（标题、今日日期）+ `<RouterView />` + `QuickAddButton` |
| `BaseChart.vue` | ECharts 封装（同 PC） |
| `QuickAddButton.vue` | **移动端专属**：悬浮快捷记账按钮，打开 `ExpenseFormDialog`，保存后触发 `notifyFinanceDataChanged` |
| `ExpenseFormDialog.vue` | **移动端专属**：两步式记账（金额数字键盘 → 分类/日期/备注），宽度自适应 `min(520px, 100vw-24px)` |
| `IncomeFormDialog.vue` | 月收入录入对话框 |
| `DataTransferButton.vue` | 数据导入导出（导出优先 `showSaveFilePicker`，回退 `<a download>`；导入前二次确认；导入后推断最近期间） |

### 6.7 页面 `mobile/src/views/`

| 视图 | 职责 |
|------|------|
| `LoginView.vue` | 登录/注册 Tab、记住密码/自动登录、自动登录跳过逻辑（基于 `shouldSkipAutoLogin`） |
| `DashboardView.vue` | 月份选择、超支告警（`el-alert`）、收支卡片、本月分类结构图、年度趋势图、快捷新增/收入入口 |
| `RecordsView.vue` | 月份+分类筛选、表格（桌面）与卡片（移动）双视图、新增/编辑/删除 |
| `AnalysisView.vue` | 年度选择、年度账单（结余/收入/支出汇总 + 逐月表格）、超支告警、多 Tab 分析 |
| `SettingsView.vue` | 头像/用户名/预设工资/分类管理（对话框）/数据管理/退出登录 |

---

## 七、数据模型与关系

### 7.1 ER 关系

```
users (1) ──── (N) expenses
users (1) ──── (N) monthly_incomes
```

- `User` 与 `Expense`、`MonthlyIncome` 为一对多，`cascade="all, delete-orphan"`，删除用户级联删除其记录。
- 外键均带 `ondelete="CASCADE"`。

### 7.2 表结构

#### `users`（[app/models/user.py](backend/app/models/user.py)）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, 自增, index | 用户 ID |
| `email` | String(255) | unique, index, not null | 账号（手机号或邮箱） |
| `username` | String(80) | nullable | 用户昵称 |
| `default_salary_income` | Numeric(12,2) | not null, default 0 | 预设月工资（回退用） |
| `password_hash` | String(255) | not null | bcrypt 哈希 |
| `created_at` | DateTime(tz) | server_default now | 注册时间 |

> 关系：`expenses`、`monthly_incomes`（back_populates）。

#### `expenses`（[app/models/expense.py](backend/app/models/expense.py)）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | 记录 ID |
| `user_id` | Integer | FK(users.id, CASCADE), index | 所属用户 |
| `amount` | Numeric(12,2) | not null | 金额 |
| `category` | String(60) | not null | 分类（中文） |
| `note` | String(255) | nullable | 备注 |
| `spent_at` | Date | index, not null | 消费日期 |
| `created_at` | DateTime(tz) | server_default now | 创建时间 |
| `updated_at` | DateTime(tz) | server_default now, onupdate now | 更新时间 |

#### `monthly_incomes`（[app/models/monthly_income.py](backend/app/models/monthly_income.py)）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | 记录 ID |
| `user_id` | Integer | FK(users.id, CASCADE), index | 所属用户 |
| `year` | Integer | not null | 年份 |
| `month` | Integer | not null | 月份 |
| `salary_income` | Numeric(12,2) | not null, default 0 | 工资收入 |
| `extra_income` | Numeric(12,2) | not null, default 0 | 额外收入总额 |
| `extra_income_items` | JSON | not null, default list | 额外收入明细 `[{name, amount}]` |
| `created_at` | DateTime(tz) | server_default now | 创建时间 |
| `updated_at` | DateTime(tz) | server_default now, onupdate now | 更新时间 |

- **唯一约束**：`UniqueConstraint(user_id, year, month, name="uq_monthly_incomes_user_period")`，每用户每月仅一条。

### 7.3 `extra_income_items` 数据结构

```json
[
  { "name": "兼职收入", "amount": 500.00 },
  { "name": "红包", "amount": 200.00 }
]
```

---

## 八、API 接口参考

> 所有接口前缀 `/api`；除标注外均需 `Authorization: Bearer <token>`。

### 8.1 认证 `/api/auth`

| 方法 | 路径 | 鉴权 | 说明 | 响应 |
|------|------|------|------|------|
| POST | `/auth/register` | 否 | 注册（或为已存在无密码账号补设密码） | `TokenResponse`（201） |
| POST | `/auth/login` | 否 | 登录 | `TokenResponse` |
| GET | `/auth/me` | 是 | 当前用户 | `UserRead` |
| PUT | `/auth/me` | 是 | 更新 `username`/`default_salary_income` | `UserRead` |

### 8.2 支出 `/api/expenses`

| 方法 | 路径 | 查询参数 | 说明 |
|------|------|---------|------|
| GET | `/expenses` | `start_date?/end_date?/category?/limit(≤100)/offset` | 列表 + 总数 |
| POST | `/expenses` | — | 创建（201） |
| GET | `/expenses/{id}` | — | 详情 |
| PUT | `/expenses/{id}` | — | 更新 |
| DELETE | `/expenses/{id}` | — | 删除（204） |

### 8.3 收入 `/api/incomes`

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| GET | `/incomes/monthly` | `year/month` | 月收入（无记录回退默认工资） |
| PUT | `/incomes/monthly` | body | Upsert 月收入 |

### 8.4 统计 `/api/stats`

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| GET | `/stats/overview` | `year?/month?` | 综合统计概览（`OverviewStats`） |

### 8.5 数据迁移 `/api/data`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/data/export` | 导出全量 JSON（`version=1`） |
| POST | `/data/import` | 覆盖导入（事务保护，返回计数） |

### 8.6 健康检查

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/health` | 否 | 服务存活 |
| GET | `/health/database` | 否 | 数据库与表就绪检查 |
| GET | `/health/routes` | 否 | 路由清单 |

---

## 九、依赖关系

### 9.1 后端依赖（[backend/requirements.txt](backend/requirements.txt)）

| 包 | 版本约束 | 用途 |
|----|---------|------|
| `fastapi` | `>=0.111,<1.0` | Web 框架 |
| `uvicorn` | `>=0.29,<1.0` | ASGI 服务器 |
| `sqlalchemy` | `>=2.0,<3.0` | ORM |
| `alembic` | `>=1.13,<2.0` | 数据库迁移 |
| `pydantic-settings` | `>=2.2,<3.0` | 配置管理 |
| `python-jose` | `>=3.3,<4.0` | JWT |
| `passlib[bcrypt]` | `>=1.7,<2.0` | 密码哈希 |
| `bcrypt` | `>=4.0,<4.1` | bcrypt 后端 |
| `psycopg2-binary` | `>=2.9,<3.0` | PostgreSQL 驱动 |
| `PyMySQL` | `>=1.1,<2.0` | MySQL 驱动 |
| `python-multipart` | `>=0.0.9,<1.0` | 表单解析 |
| `email-validator` | `>=2.1,<3.0` | 邮箱校验 |

### 9.2 前端依赖（pc / mobile 共用）

| 包 | 版本 | 用途 |
|----|------|------|
| `vue` | `^3.5.13` | 前端框架 |
| `vue-router` | `^4.5.0` | 路由 |
| `pinia` | `^2.3.1` | 状态管理 |
| `element-plus` | `^2.9.3` | UI 组件库 |
| `@element-plus/icons-vue` | `^2.3.1` | 图标 |
| `axios` | `^1.7.9` | HTTP 客户端 |
| `echarts` | `^5.6.0` | 图表 |
| `dayjs` | `^1.11.13` | 日期处理 |
| `vite` | `^6.0.7`（dev） | 构建/开发服务器 |
| `@vitejs/plugin-vue` | `^5.2.1`（dev） | Vue 插件 |

### 9.3 模块依赖图（后端）

```
main.py
 ├── core.config (get_settings)
 ├── core.config → db.session (engine)
 ├── api.routes.{auth, expenses, incomes, stats, data_transfer}
 │     ├── api.deps (get_db, get_current_user)
 │     │     ├── core.security (decode_access_token)
 │     │     ├── db.session (SessionLocal)
 │     │     └── models.user (User)
 │     ├── models.{user, expense, monthly_income}
 │     ├── schemas.{auth, expense, income, stats}
 │     └── services.income_items (normalize_extra_income_items, extra_income_total)
 └── db.session (engine) → core.config
```

### 9.4 前端依赖图（移动端示例）

```
main.js
 ├── pinia (stores/auth)
 ├── router (router/index) → stores/auth (守卫)
 ├── element-plus
 └── App.vue → RouterView
      └── AppLayout → QuickAddButton → ExpenseFormDialog
           └── views/{Dashboard, Records, Analysis, Settings, Login}
                ├── utils/http (axios, 注入 token, 401 处理)
                ├── utils/format (currency/percent)
                ├── utils/events (FINANCE_DATA_CHANGED)
                ├── utils/authPreferences, userPreferences
                ├── constants/categories, categoryIcons
                └── components/{BaseChart, DataTransferButton, IncomeFormDialog}
```

---

## 十、核心数据流

### 10.1 登录流程

```
用户输入账号密码
  └─ LoginView.submit()
       └─ authStore.login() → POST /api/auth/login
            └─ 后端 verify_password → create_access_token(user.id)
       └─ setSession: token/user 写入 Pinia + localStorage
       └─ 跳转概览页（requiresAuth 守卫放行）
后续请求: http 拦截器注入 Authorization: Bearer <token>
```

### 10.2 记账流程

```
QuickAddButton 点击 → ExpenseFormDialog（金额键盘 → 分类/日期/备注）
  └─ POST /api/expenses（ExpenseCreate 校验）
       └─ 后端 create_expense 写库
  └─ notifyFinanceDataChanged() → window 广播 FINANCE_DATA_CHANGED
       └─ DashboardView/AnalysisView 监听 → 重新拉取 /api/stats/overview
```

### 10.3 统计流程

```
进入概览/分析页（或月份切换）
  └─ GET /api/stats/overview?year=YYYY&month=M
       └─ 后端 overview(): 聚合当月/当年支出、分类、趋势、每日、收入、最近记录
       └─ 返回 OverviewStats
  └─ BaseChart 渲染 ECharts（饼图/折线/柱状）
```

### 10.4 数据导入导出流程

```
导出: GET /api/data/export
  └─ 后端查询用户全部 expenses + monthly_incomes
  └─ 返回 DataTransferPayload(version=1, exported_at, expenses[], monthly_incomes[])
  └─ 前端优先 showSaveFilePicker 保存 JSON，回退 <a download>

导入: 选择 JSON → 二次确认 → POST /api/data/import
  └─ 后端事务: delete 旧 expenses/monthly_incomes → insert 新数据 → commit（失败 rollback）
  └─ 返回 { expenses: N, monthly_incomes: M }
  └─ 前端 notifyFinanceDataChanged() 刷新全局数据
```

---

## 十一、项目运行方式

### 11.1 环境要求

- **后端**：Python 3.12+、MySQL（开发可回退 SQLite）
- **前端**：Node.js（支持 Vite 6 / ESM）
- **本地脚本**：Windows PowerShell（`scripts/*.ps1`）

### 11.2 数据库准备

```sql
CREATE DATABASE IF NOT EXISTS finance_data
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

若账号非 `root/root`，复制并修改 `backend/.env`：

```powershell
Copy-Item backend\.env.example backend\.env
# 编辑 backend\.env 的 DATABASE_URL / SECRET_KEY / CORS_ORIGINS
```

`backend/.env` 关键变量：

```env
APP_NAME=Yun Accounting
ENVIRONMENT=production
API_PREFIX=/api
SECRET_KEY=<请替换为强随机串>
ACCESS_TOKEN_EXPIRE_MINUTES=10080
DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/finance_data?charset=utf8mb4
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8023,http://127.0.0.1:8023
```

### 11.3 一键启动（Windows）

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

脚本行为：
1. 在 `backend/.venv` 创建虚拟环境（如不存在）；
2. 复制 `.env.example` → `.env`（如不存在）；
3. `pip install -r requirements.txt`；
4. `alembic upgrade head` 执行迁移；
5. 分别在新窗口启动后端（8024）、PC（5173）、移动端（8023）。

启动后地址：

| 服务 | 地址 |
|------|------|
| PC 版 | http://127.0.0.1:5173/pc/ |
| 移动版 | http://127.0.0.1:8023/mobile/ |
| 后端 API 文档 | http://127.0.0.1:8024/docs |
| 健康检查 | http://127.0.0.1:8024/health |

停止服务：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop.ps1
```

### 11.4 手动启动

**后端**：

```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\python
# Linux/macOS: ./.venv/bin/python
python -m pip install -r requirements.txt
cp .env.example .env          # 按需修改
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8024
```

**前端**（任一）：

```bash
cd pc        # 或 cd mobile
npm install
npm run dev
```

### 11.5 构建

根目录提供统一构建脚本（[package.json](package.json)）：

```bash
npm run build          # 同时构建 pc + mobile
npm run pc:build       # 仅 PC
npm run mobile:build   # 仅移动端
```

或分别在各前端目录执行 `npm run build`，产物输出到对应 `dist/`。

---

## 十二、部署方式

### 12.1 Docker 部署（后端）

`backend/Dockerfile` 要点：
- 基础镜像 `python:3.12-slim`；
- 拷贝 `requirements.txt`、`alembic.ini`、`alembic/`、`app/`；
- 暴露 `8002`；
- 启动命令：`alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8002}`。

部署时通过环境变量覆盖 `DATABASE_URL`、`SECRET_KEY`、`CORS_ORIGINS` 等（见 [backend/.env.example](backend/.env.example)）。

### 12.2 Nginx 反向代理（[deploy/nginx-yun-accounting.conf](deploy/nginx-yun-accounting.conf)）

| location | 转发目标 | 说明 |
|----------|---------|------|
| `/api/` | `http://127.0.0.1:8002` | 后端 API（原样转发） |
| `/health`、`/docs`、`/openapi.json`、`/redoc` | `http://127.0.0.1:8002` | 后端健康检查与文档 |
| `/pc/` | 静态 `alias /var/www/yun-accounting/pc/` | PC 前端（base `/pc/`，SPA 回退 `/pc/index.html`） |
| `/mobile/` | 静态 `alias /var/www/yun-accounting/mobile/` | 移动前端（base `/mobile/`，SPA 回退 `/mobile/index.html`） |
| `= /` | `302 /mobile/` | 默认跳转移动端 |

- `client_max_body_size 20m`；
- 代理转发 `X-Real-IP`、`X-Forwarded-For`、`X-Forwarded-Proto`。

### 12.3 生产部署流程概要

1. 构建前端：`npm run build`，将 `pc/dist`、`mobile/dist` 分别部署到 `/var/www/yun-accounting/pc/` 与 `/var/www/yun-accounting/mobile/`；
2. 后端用 Docker 或 systemd 运行 uvicorn（端口 8002），执行迁移；
3. 配置 MySQL `finance_data` 与 `.env`；
4. Nginx 加载 `nginx-yun-accounting.conf`，统一对外 80 端口。

---

## 附录：技术栈速查表

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端框架 | FastAPI | RESTful API |
| ORM | SQLAlchemy 2.0 | 数据库操作（`Decimal`/`Numeric` 金额） |
| 数据库 | MySQL（开发可 SQLite） | 数据存储（`finance_data`） |
| 数据校验 | Pydantic v2 | 请求/响应模型与校验 |
| 配置管理 | pydantic-settings | `.env` 读取 |
| 认证 | JWT（python-jose, HS256）+ bcrypt（passlib） | 身份认证与密码加密 |
| 数据库迁移 | Alembic | 表结构版本管理 |
| 前端框架 | Vue 3（`<script setup>`） | PC + 移动端界面 |
| UI 组件库 | Element Plus + @element-plus/icons-vue | 组件与图标（两端共用） |
| 状态管理 | Pinia | 前端状态（auth store） |
| 路由 | Vue Router 4 | SPA 路由 + 守卫 |
| 图表 | ECharts 5 | 数据可视化 |
| HTTP 客户端 | Axios | API 请求 + 拦截器 |
| 日期处理 | Day.js | 日期格式化 |
| 构建工具 | Vite 6 | 开发服务器与打包 |
| 容器化 | Docker | 后端镜像 |
| 反向代理 | Nginx | 同源分发 + 静态托管 + API 代理 |
| 本地脚本 | PowerShell | 一键启停 |

---

> 本 Wiki 基于仓库当前源码生成，若代码结构发生变更，请同步更新对应章节。
