# 云记账项目技术手册

> 本手册面向初学者，用通俗易懂的语言描述项目中每个代码文件的作用和功能。

---

## 一、项目整体架构

### 1.1 项目是什么？

云记账是一个**个人财务管理应用**，可以帮助你：
- 记录每天的支出（吃饭、交通、购物等）
- 记录每月的收入（工资、额外收入等）
- 查看统计图表（花钱趋势、分类占比等）
- 导入/导出数据（备份和恢复）

### 1.2 项目由哪些部分组成？

```
云记账项目
├── backend/        ← 后端（Python，提供API接口）
├── pc/             ← PC端网页（Vue3，电脑浏览器用）
├── mobile/         ← 移动端网页（Vue3，手机浏览器用）
├── deploy/         ← 部署配置（Nginx反向代理）
├── scripts/        ← 运维脚本（启动/停止服务）
└── logs/           ← 日志文件（运行时自动生成）
```

### 1.3 前后端如何通信？

```
用户浏览器（PC端/移动端）
    │
    │  HTTP请求（带JWT令牌）
    ▼
后端API（FastAPI）
    │
    │  SQL查询
    ▼
数据库（SQLite或MySQL）
```

- **前端**负责展示界面、接收用户操作
- **后端**负责处理业务逻辑、存取数据
- **数据库**负责持久化存储数据
- 前后端通过 **RESTful API** 通信，使用 **JWT令牌** 验证身份

---

## 二、后端代码详解（backend/）

### 2.1 入口与配置

#### `backend/app/main.py` — 应用入口

**作用**：整个后端的启动文件，相当于"总开关"。

**做了什么**：
1. 创建 FastAPI 应用实例
2. 配置 CORS（跨域资源共享），允许前端网页访问后端API
3. 注册5个路由模块：
   - `auth` — 用户认证（注册、登录）
   - `expenses` — 支出管理
   - `incomes` — 收入管理
   - `stats` — 统计分析
   - `data_transfer` — 数据导入导出
4. 提供 `/health` 和 `/health/database` 健康检查端点，用于监控服务是否正常运行

**关键代码理解**：
```python
app = FastAPI(title="云记账API")          # 创建应用
app.add_middleware(CORSMiddleware, ...)    # 允许跨域
app.include_router(auth.router, ...)      # 注册路由
```

---

#### `backend/app/core/config.py` — 配置管理

**作用**：集中管理所有配置项，从环境变量或 `.env` 文件中读取。

**配置项说明**：
| 配置项 | 含义 | 默认值 |
|--------|------|--------|
| `PROJECT_NAME` | 项目名称 | "云记账" |
| `DATABASE_NAME` | 数据库名称 | "yun_accounting" |
| `SECRET_KEY` | JWT加密密钥 | 随机生成 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 令牌过期时间 | 1440分钟(24小时) |
| `CORS_ORIGINS` | 允许的跨域来源 | 本地开发地址 |

**为什么需要这个文件**：把配置集中管理，避免在代码中硬编码（写死）敏感信息如密钥、数据库地址等。

---

#### `backend/app/core/security.py` — 安全模块

**作用**：处理密码加密和令牌生成，是用户认证的核心。

**两个关键函数**：
1. `verify_password(plain_password, hashed_password)` — 验证密码是否正确
   - 用 bcrypt 算法比对明文密码和哈希密码
2. `create_access_token(data, expires_delta)` — 创建JWT访问令牌
   - 将用户信息（如用户ID）编码为JWT令牌
   - 令牌有过期时间，过期后需重新登录

**什么是JWT**：JWT（JSON Web Token）就像一张"电子通行证"，用户登录后获得令牌，之后每次请求都带上令牌，后端通过验证令牌确认身份。

---

### 2.2 数据库层

#### `backend/app/db/session.py` — 数据库连接

**作用**：创建数据库引擎和会话工厂。

**关键概念**：
- `engine` — 数据库引擎，负责与数据库建立连接
- `SessionLocal` — 会话工厂，每次需要操作数据库时创建一个会话
- 支持 SQLite（开发用，文件数据库）和 MySQL（生产用，服务器数据库）

---

#### `backend/app/db/base.py` — ORM基类

**作用**：定义 SQLAlchemy 的 DeclarativeBase，所有数据模型都继承这个基类。
- 相当于给所有数据表定义一个"模板"

---

### 2.3 数据模型（Models）

数据模型定义了数据库中表的结构，每个模型类对应数据库中的一张表。

#### `backend/app/models/user.py` — 用户模型

**对应的数据库表**：`users`

| 字段 | 类型 | 含义 |
|------|------|------|
| `id` | Integer | 用户唯一ID（主键，自增） |
| `email` | String | 邮箱（唯一，用于登录） |
| `username` | String | 用户昵称 |
| `default_salary_income` | Float | 预设月工资（方便快速录入） |
| `hashed_password` | String | 加密后的密码 |
| `created_at` | DateTime | 注册时间 |

**关系**：一个用户可以有多条支出记录和多条月收入记录。

---

#### `backend/app/models/expense.py` — 支出模型

**对应的数据库表**：`expenses`

| 字段 | 类型 | 含义 |
|------|------|------|
| `id` | Integer | 记录唯一ID |
| `user_id` | Integer | 所属用户ID（外键） |
| `amount` | Float | 金额 |
| `category` | String | 分类（如"餐饮"、"交通"） |
| `note` | String | 备注 |
| `spent_at` | DateTime | 消费日期 |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 更新时间 |

---

#### `backend/app/models/monthly_income.py` — 月收入模型

**对应的数据库表**：`monthly_incomes`

| 字段 | 类型 | 含义 |
|------|------|------|
| `id` | Integer | 记录唯一ID |
| `user_id` | Integer | 所属用户ID（外键） |
| `year` | Integer | 年份 |
| `month` | Integer | 月份 |
| `salary_income` | Float | 工资收入 |
| `extra_income` | Float | 额外收入总额 |
| `extra_income_items` | JSON | 额外收入明细列表 |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 更新时间 |

**唯一约束**：每个用户每个月只能有一条收入记录（user_id + year + month 组合唯一）。

**extra_income_items 的数据结构**：
```json
[
  {"name": "兼职收入", "amount": 500},
  {"name": "红包", "amount": 200}
]
```

---

### 2.4 数据校验（Schemas）

Schema 用 Pydantic 定义，负责：
1. **数据校验** — 确保传入的数据格式正确
2. **数据转换** — 将数据库对象转为API返回的JSON格式

#### `backend/app/schemas/auth.py` — 认证Schema

| Schema名 | 用途 |
|----------|------|
| `UserCreate` | 注册时提交的数据（邮箱+用户名+密码） |
| `LoginRequest` | 登录时提交的数据（邮箱+密码） |
| `UserUpdate` | 更新用户信息（用户名+预设工资） |
| `UserRead` | 返回给前端的用户信息（不含密码） |
| `TokenResponse` | 登录成功返回的令牌 |

---

#### `backend/app/schemas/expense.py` — 支出Schema

| Schema名 | 用途 |
|----------|------|
| `ExpenseCreate` | 创建支出记录（金额+分类+备注+日期） |
| `ExpenseUpdate` | 更新支出记录（所有字段可选） |
| `ExpenseRead` | 返回完整的支出记录 |
| `ExpenseList` | 支出列表（含分页信息） |

**特殊处理**：
- `category`（分类）和 `note`（备注）字段会自动去除首尾空格
- 空字符串会被转为 `None`

---

#### `backend/app/schemas/income.py` — 收入Schema

| Schema名 | 用途 |
|----------|------|
| `ExtraIncomeItem` | 单条额外收入（名称+金额） |
| `MonthlyIncomeUpsert` | 创建或更新月收入（工资+额外收入列表） |
| `MonthlyIncomeRead` | 返回月收入数据 |

---

#### `backend/app/schemas/stats.py` — 统计Schema

| Schema名 | 用途 |
|----------|------|
| `CategorySummary` | 分类汇总（分类名+金额+占比） |
| `StructureSummary` | 收支结构（总支出+总收入+余额） |
| `TrendPoint` | 趋势数据点（月份+金额） |
| `DailyExpensePoint` | 每日支出数据点 |
| `MonthlyIncomeSummary` | 月收入汇总 |
| `OverviewStats` | 概览统计（汇总所有统计维度） |

---

### 2.5 依赖注入

#### `backend/app/api/deps.py` — 依赖注入函数

**作用**：提供可复用的依赖函数，被路由函数调用。

**两个关键函数**：
1. `get_db()` — 获取数据库会话
   - 每次请求创建一个数据库会话，请求结束后自动关闭
2. `get_current_user(token, db)` — 获取当前登录用户
   - 从请求头中提取JWT令牌
   - 解码令牌获取用户ID
   - 从数据库查询用户信息
   - 如果令牌无效或用户不存在，抛出401错误

**什么是依赖注入**：FastAPI的特色功能，把常用逻辑写成函数，在路由中通过参数声明自动调用，避免重复代码。

---

### 2.6 API路由（Routes）

路由定义了前端可以调用的API接口。

#### `backend/app/api/routes/auth.py` — 认证路由

**前缀**：`/api/auth`

| 接口 | 方法 | 功能 | 是否需要登录 |
|------|------|------|-------------|
| `/register` | POST | 用户注册 | 否 |
| `/login` | POST | 用户登录 | 否 |
| `/me` | GET | 获取当前用户信息 | 是 |
| `/me` | PUT | 更新用户信息 | 是 |

**注册流程**：
1. 接收邮箱、用户名、密码
2. 检查邮箱是否已注册
3. 用 bcrypt 加密密码
4. 创建用户记录
5. 返回用户信息和JWT令牌

**登录流程**：
1. 接收邮箱、密码
2. 查找用户并验证密码
3. 生成JWT令牌
4. 返回令牌

---

#### `backend/app/api/routes/expenses.py` — 支出路由

**前缀**：`/api/expenses`

| 接口 | 方法 | 功能 | 是否需要登录 |
|------|------|------|-------------|
| `/` | GET | 获取支出列表 | 是 |
| `/` | POST | 创建支出记录 | 是 |
| `/{id}` | GET | 获取单条支出详情 | 是 |
| `/{id}` | PUT | 更新支出记录 | 是 |
| `/{id}` | DELETE | 删除支出记录 | 是 |

**列表查询支持**：
- 分页（skip/limit参数）
- 日期范围筛选（start_date/end_date）
- 分类筛选（category）

---

#### `backend/app/api/routes/incomes.py` — 收入路由

**前缀**：`/api/incomes`

| 接口 | 方法 | 功能 | 是否需要登录 |
|------|------|------|-------------|
| `/monthly` | GET | 获取月收入 | 是 |
| `/monthly` | PUT | 创建或更新月收入 | 是 |

**Upsert逻辑**：如果该月已有收入记录则更新，否则创建新记录。

**默认工资回退**：如果用户没有填写工资收入，自动使用用户预设的 `default_salary_income`。

---

#### `backend/app/api/routes/stats.py` — 统计路由

**前缀**：`/api/stats`

| 接口 | 方法 | 功能 |
|------|------|------|
| `/overview` | GET | 获取综合统计概览 |

**返回的统计数据**：
1. **月/年支出汇总** — 当月和当年总支出
2. **分类统计** — 各分类支出金额和占比
3. **月度趋势** — 近几个月的支出变化
4. **每日支出** — 当月每天的支出金额
5. **最近记录** — 最近5条支出记录
6. **收入与余额** — 当月收入和结余

---

#### `backend/app/api/routes/data_transfer.py` — 数据迁移路由

**前缀**：`/api/data`

| 接口 | 方法 | 功能 | 是否需要登录 |
|------|------|------|-------------|
| `/export` | GET | 导出全部数据为JSON | 是 |
| `/import` | POST | 导入JSON数据并覆盖 | 是 |

**导出格式**：
```json
{
  "expenses": [...],
  "monthly_incomes": [...]
}
```

**导入逻辑**：
1. 开启数据库事务
2. 删除用户现有的所有支出和收入记录
3. 插入导入的数据
4. 提交事务（如果出错则回滚）

---

### 2.7 服务层

#### `backend/app/services/income_items.py` — 额外收入处理服务

**作用**：处理额外收入明细列表的业务逻辑。

**主要功能**：
1. 金额精度处理 — 将浮点数转为Decimal，避免精度丢失
2. 明细规范化 — 清洗名称（去空格）、过滤零金额项
3. 回退兼容 — 如果旧数据没有items字段，自动初始化为空列表
4. 合计计算 — 根据明细列表计算额外收入总额

---

### 2.8 数据库迁移

#### `backend/alembic/` — 数据库迁移工具

**作用**：管理数据库表结构的版本变更，类似Git但针对数据库。

**常用命令**：
- `alembic revision --autogenerate` — 自动生成迁移脚本（检测模型变更）
- `alembic upgrade head` — 执行迁移，更新数据库表结构

---

### 2.9 其他后端文件

| 文件 | 作用 |
|------|------|
| `backend/requirements.txt` | Python依赖包列表 |
| `backend/.env` / `.env.example` | 环境变量配置文件 |
| `backend/Dockerfile` | Docker镜像构建文件 |
| `backend/alembic.ini` | Alembic迁移工具配置 |

---

## 三、PC端前端代码详解（pc/）

### 3.1 应用入口与配置

#### `pc/src/main.js` — 应用入口

**作用**：Vue应用的启动文件，挂载所有插件。

**做了什么**：
1. 创建Vue应用实例
2. 注册 Pinia（状态管理）
3. 注册 Vue Router（路由）
4. 注册 Element Plus（UI组件库）
5. 挂载到 `#app` DOM节点

---

#### `pc/src/router/index.js` — 路由配置

**作用**：定义页面URL与组件的映射关系。

**路由表**：
| 路径 | 组件 | 需要登录 | 说明 |
|------|------|---------|------|
| `/login` | LoginPage | 否 | 登录页 |
| `/` | AppLayout | 是 | 主布局（含侧边栏） |
| `/dashboard` | DashboardView | 是 | 概览页 |
| `/records` | RecordsView | 是 | 记录页 |
| `/analysis` | AnalysisView | 是 | 分析页 |
| `/settings` | SettingsView | 是 | 设置页 |

**路由守卫**：`beforeEach` 钩子检查用户是否已登录，未登录则跳转到登录页。

---

#### `pc/vite.config.js` — Vite构建配置

**作用**：配置开发服务器和构建选项。

**关键配置**：
- 开发服务器代理：将 `/api` 请求代理到后端 `http://localhost:8000`
- 避免开发时的跨域问题

---

### 3.2 状态管理

#### `pc/src/stores/auth.js` — 认证状态Store

**作用**：管理用户登录状态，是前端最核心的状态。

**状态**：
- `token` — JWT令牌（持久化到localStorage）
- `user` — 当前用户信息

**动作**：
| 动作 | 功能 |
|------|------|
| `login(email, password)` | 调用登录API，保存令牌和用户信息 |
| `register(data)` | 调用注册API，保存令牌和用户信息 |
| `fetchMe()` | 获取当前用户信息 |
| `updateProfile(data)` | 更新用户资料 |
| `logout()` | 清除令牌和用户信息，跳转登录页 |

**持久化策略**：token保存在localStorage，页面刷新后仍保持登录状态。

---

### 3.3 工具函数

#### `pc/src/utils/http.js` — HTTP请求封装

**作用**：封装Axios，统一处理请求和响应。

**请求拦截器**：
- 自动在请求头添加 `Authorization: Bearer <token>`

**响应拦截器**：
- 401状态码 → 清除登录状态，跳转登录页
- 其他错误 → 弹出Element Plus错误提示

---

#### `pc/src/utils/format.js` — 格式化工具

**作用**：提供数据格式化函数。

| 函数 | 功能 | 示例 |
|------|------|------|
| `currency(amount)` | 格式化为人民币 | `currency(1234.5)` → `"¥1,234.50"` |
| `percent(value)` | 格式化为百分比 | `percent(0.156)` → `"15.6%"` |

---

#### `pc/src/utils/events.js` — 事件总线

**作用**：组件间通信的桥梁。

**事件**：
- `FINANCE_DATA_CHANGED` — 财务数据变更通知

**使用场景**：当用户添加/编辑/删除记录后，通知其他组件刷新数据。

---

### 3.4 常量定义

#### `pc/src/constants/categories.js` — 支出分类

**作用**：定义11个支出分类及其显示属性。

| 分类键 | 中文名 | 颜色 |
|--------|--------|------|
| `food` | 餐饮 | #FF6B6B |
| `transport` | 交通 | #4ECDC4 |
| `shopping` | 购物 | #45B7D1 |
| `online_shopping` | 网购 | #96CEB4 |
| `service` | 服务 | #FFEAA7 |
| `housing` | 居住 | #DDA0DD |
| `gift` | 送礼 | #98D8C8 |
| `entertainment` | 娱乐 | #F7DC6F |
| `medical` | 医疗 | #BB8FCE |
| `education` | 教育 | #85C1E9 |
| `other` | 其他 | #AEB6BF |

---

### 3.5 公共组件

#### `pc/src/components/AppLayout.vue` — 主布局

**作用**：登录后的页面框架，包含侧边栏和顶部栏。

**布局结构**：
```
┌──────────────────────────────────────┐
│ 顶部栏（标题 | 日期 | 用户名 | 退出） │
├────────┬─────────────────────────────┤
│ 侧边栏 │                             │
│ 概览   │     主内容区域               │
│ 记录   │     （路由组件渲染区）        │
│ 分析   │                             │
│ 设置   │                             │
└────────┴─────────────────────────────┘
```

---

#### `pc/src/components/BaseChart.vue` — 图表基础组件

**作用**：封装ECharts，提供统一的图表渲染能力。

**特性**：
- 接收 `option` prop，自动渲染ECharts图表
- 使用 ResizeObserver 监听容器大小变化，自动调整图表尺寸
- 组件销毁时自动清理ECharts实例

---

#### `pc/src/components/DataTransferButton.vue` — 数据导入导出

**作用**：提供数据备份和恢复功能。

**导出**：调用后端 `/api/data/export`，将返回的JSON保存为文件下载。

**导入**：选择JSON文件，确认后调用后端 `/api/data/import`，覆盖现有数据。

---

### 3.6 页面组件

#### `pc/src/views/LoginView.vue` — 登录/注册页

**作用**：用户身份认证页面。

**功能**：
- 登录表单（邮箱+密码）
- 注册表单（邮箱+用户名+密码+确认密码）
- 表单验证（必填、格式校验）
- 登录成功后跳转概览页

---

#### `pc/src/views/DashboardView.vue` — 概览页

**作用**：展示财务数据的综合概览。

**展示内容**：
1. 支出/收入/余额卡片
2. 支出分类饼图
3. 月度趋势折线图
4. 最近支出记录列表

---

#### `pc/src/views/RecordsView.vue` — 记录页

**作用**：支出记录的增删改查页面。

**功能**：
- 记录列表（表格展示，支持分页）
- 添加记录对话框
- 编辑记录对话框
- 删除确认
- 日期范围和分类筛选

---

#### `pc/src/views/AnalysisView.vue` — 分析页

**作用**：详细的财务数据分析页面。

**图表**：
1. 支出分类饼图
2. 月度趋势折线图
3. 每日支出柱状图

---

#### `pc/src/views/SettingsView.vue` — 设置页

**作用**：用户个人设置。

**功能**：
- 修改用户名
- 设置预设月工资
- 数据导入导出
- 退出登录

---

## 四、移动端前端代码详解（mobile/）

移动端与PC端共享同一套后端API，但前端界面针对手机屏幕做了优化，并增加了一些移动端特有的功能。

### 4.1 应用入口与配置

#### `mobile/src/main.js` — 应用入口

**作用**：与PC端类似，Vue应用的启动文件。

**差异**：
- 使用 Vant 4 UI组件库（专为移动端设计）而非 Element Plus
- 同样注册 Pinia + Vue Router

---

#### `mobile/src/router/index.js` — 路由配置

**作用**：定义移动端的页面路由。

**路由表**：
| 路径 | 组件 | 需要登录 | 说明 |
|------|------|---------|------|
| `/login` | LoginPage | 否 | 登录页 |
| `/` | AppLayout | 是 | 主布局（底部Tab栏） |
| `/dashboard` | DashboardView | 是 | 概览页 |
| `/records` | RecordsView | 是 | 记录页 |
| `/analysis` | AnalysisView | 是 | 分析页 |
| `/settings` | SettingsView | 是 | 设置页 |
| `/categories` | CategoriesView | 是 | 分类管理页（移动端特有） |

**布局特点**：移动端使用底部Tab导航栏而非侧边栏。

---

#### `mobile/vite.config.js` — Vite构建配置

**作用**：与PC端类似，配置开发代理。

**差异**：端口可能不同，避免与PC端开发服务器冲突。

---

### 4.2 状态管理

#### `mobile/src/stores/auth.js` — 认证状态Store

**作用**：与PC端功能一致，管理登录状态。

**差异**：移动端可能增加头像相关的状态管理。

---

### 4.3 工具函数

#### `mobile/src/utils/http.js` — HTTP请求封装

**作用**：与PC端功能一致，封装Axios请求。

---

#### `mobile/src/utils/format.js` — 格式化工具

**作用**：与PC端功能一致，提供金额和百分比格式化。

---

### 4.4 常量定义

#### `mobile/src/constants/categories.js` — 支出分类

**作用**：与PC端一致，定义11个支出分类。

**差异**：移动端可能增加分类的图标定义（Vant图标名），方便在移动端界面中显示。

---

### 4.5 公共组件

#### `mobile/src/components/AppLayout.vue` — 主布局

**作用**：移动端页面框架。

**布局结构**：
```
┌─────────────────────┐
│    顶部标题栏        │
├─────────────────────┤
│                     │
│   主内容区域        │
│   （路由组件渲染区） │
│                     │
├─────────────────────┤
│ 概览 记录 分析 设置  │  ← 底部Tab栏
└─────────────────────┘
```

**与PC端差异**：
- 底部Tab导航替代侧边栏
- 更紧凑的布局适配小屏幕

---

#### `mobile/src/components/BaseChart.vue` — 图表基础组件

**作用**：与PC端功能一致，封装ECharts。

**差异**：移动端图表可能使用更小的字体和更紧凑的布局。

---

### 4.6 页面组件

#### `mobile/src/views/LoginView.vue` — 登录/注册页

**作用**：移动端认证页面。

**差异**：
- 使用Vant表单组件替代Element Plus
- 更大的触摸区域，适配手机操作

---

#### `mobile/src/views/DashboardView.vue` — 概览页

**作用**：移动端财务概览。

**差异**：
- 卡片纵向排列（PC端横向）
- 图表宽度适配屏幕

---

#### `mobile/src/views/RecordsView.vue` — 记录页

**作用**：移动端支出记录管理。

**差异**：
- 使用Vant列表组件（支持下拉刷新、无限滚动）
- 操作使用滑动删除等移动端交互模式

---

#### `mobile/src/views/AnalysisView.vue` — 分析页

**作用**：移动端财务分析。

**差异**：图表纵向排列，适配窄屏幕。

---

#### `mobile/src/views/SettingsView.vue` — 设置页

**作用**：移动端用户设置。

**移动端特有功能**：
- **头像设置** — 上传或更换用户头像
- **预设工资** — 设置默认月工资收入
- **分类管理** — 管理支出分类（移动端特有页面）

---

#### `mobile/src/views/CategoriesView.vue` — 分类管理页（移动端特有）

**作用**：管理支出分类。

**功能**：
- 查看所有分类列表
- 分类排序
- 分类颜色自定义

---

### 4.7 移动端与PC端对比总结

| 特性 | PC端 | 移动端 |
|------|------|--------|
| UI框架 | Element Plus | Vant 4 |
| 导航方式 | 侧边栏 | 底部Tab栏 |
| 布局方向 | 横向宽松 | 纵向紧凑 |
| 分类管理 | 无独立页面 | 有独立页面 |
| 头像设置 | 无 | 有 |
| 交互模式 | 鼠标点击 | 触摸滑动 |
| 图表展示 | 多列并排 | 单列纵向 |

---

## 五、部署与脚本配置

### 5.1 Docker部署

#### `backend/Dockerfile` — 后端Docker镜像

**作用**：定义后端应用的Docker镜像构建步骤。

**构建流程**：
1. 基于Python基础镜像
2. 安装系统依赖
3. 复制requirements.txt并安装Python依赖
4. 复制应用代码
5. 暴露端口（默认8000）
6. 启动命令（uvicorn运行FastAPI）

**什么是Docker**：Docker就像一个"集装箱"，把应用和它的所有依赖打包在一起，确保在任何环境都能一致运行。

---

#### `backend/.dockerignore` — Docker忽略文件

**作用**：指定Docker构建时忽略的文件（如 `.git`、`__pycache__`），减小镜像体积。

---

### 5.2 Nginx配置

#### `deploy/nginx-yun-accounting.conf` — Nginx反向代理配置

**作用**：配置Nginx作为反向代理，将请求转发到后端和前端。

**关键配置**：
```nginx
# 前端静态文件
location / {
    root /usr/share/nginx/html/pc;
    try_files $uri $uri/ /index.html;
}

# 移动端
location /m/ {
    root /usr/share/nginx/html/mobile;
    try_files $uri $uri/ /m/index.html;
}

# API请求转发到后端
location /api/ {
    proxy_pass http://backend:8000;
}
```

**什么是反向代理**：Nginx就像一个"前台接待"，用户所有请求先到Nginx，Nginx根据请求类型分发给后端或前端。

---

### 5.3 运维脚本

#### `scripts/start.ps1` — 启动脚本

**作用**：一键启动所有服务（后端 + PC前端 + 移动端）。

**做了什么**：
1. 启动后端服务（uvicorn）
2. 启动PC端开发服务器（vite）
3. 启动移动端开发服务器（vite）
4. 将日志输出到 `logs/` 目录

---

#### `scripts/stop.ps1` — 停止脚本

**作用**：一键停止所有服务。

---

#### `scripts/dev-frontend.ps1` — 前端开发脚本

**作用**：仅启动前端开发服务器，用于前端开发调试。

---

### 5.4 环境配置

#### `backend/.env.example` — 环境变量示例

**作用**：提供环境变量的模板文件，开发者复制为 `.env` 后修改。

**常见变量**：
```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/yun_accounting
SECRET_KEY=your-secret-key-here
```

---

### 5.5 项目根目录配置

#### `package.json` — 根项目配置

**作用**：定义项目级别的脚本和依赖（如果有monorepo管理需求）。

---

#### `.gitignore` — Git忽略文件

**作用**：指定Git版本控制时忽略的文件和目录（如 `node_modules`、`.env`、`__pycache__`）。

---

## 六、数据流与交互关系

### 6.1 用户登录流程

```
1. 用户在登录页输入邮箱和密码
2. 前端调用 POST /api/auth/login
3. 后端验证密码，生成JWT令牌
4. 前端保存令牌到localStorage和Pinia Store
5. 后续请求自动在Header中带上令牌
```

### 6.2 记录支出流程

```
1. 用户在记录页填写金额、分类、备注、日期
2. 前端调用 POST /api/expenses
3. 后端校验数据，存入数据库
4. 前端刷新记录列表
5. 触发 FINANCE_DATA_CHANGED 事件
6. 概览页和分析页自动刷新统计数据
```

### 6.3 数据统计流程

```
1. 用户进入概览页或分析页
2. 前端调用 GET /api/stats/overview?year=2026&month=7
3. 后端查询数据库，计算各项统计
4. 返回分类汇总、趋势、每日支出等数据
5. 前端用ECharts渲染图表
```

### 6.4 数据导入导出流程

```
导出：
1. 用户点击"导出数据"
2. 前端调用 GET /api/data/export
3. 后端查询用户所有支出和收入记录
4. 返回JSON格式数据
5. 前端触发浏览器下载JSON文件

导入：
1. 用户选择JSON文件
2. 弹出确认对话框（警告：将覆盖现有数据）
3. 用户确认后，前端调用 POST /api/data/import
4. 后端在事务中删除旧数据、插入新数据
5. 前端刷新页面数据
```

---

## 七、技术栈速查表

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端框架 | FastAPI | 提供RESTful API |
| ORM | SQLAlchemy 2.0 | 数据库操作 |
| 数据库 | SQLite / MySQL | 数据存储 |
| 数据校验 | Pydantic v2 | 请求/响应数据验证 |
| 认证 | JWT + bcrypt | 身份验证和密码加密 |
| 数据库迁移 | Alembic | 表结构版本管理 |
| PC前端框架 | Vue 3 | 构建用户界面 |
| 移动端框架 | Vue 3 | 构建移动端界面 |
| PC UI库 | Element Plus | PC端UI组件 |
| 移动端UI库 | Vant 4 | 移动端UI组件 |
| 状态管理 | Pinia | 前端状态管理 |
| 路由 | Vue Router | 页面路由 |
| 图表 | ECharts | 数据可视化 |
| HTTP客户端 | Axios | API请求 |
| 构建工具 | Vite | 前端构建和开发服务器 |
| 容器化 | Docker | 应用打包和部署 |
| 反向代理 | Nginx | 请求分发和静态文件服务 |

---

## 八、常见问题

### Q: 前端如何知道用户是否已登录？
A: 检查localStorage中是否有token。路由守卫在每次页面跳转前检查，没有token则跳转登录页。

### Q: 后端如何验证用户身份？
A: 前端每次请求在Header中带上 `Authorization: Bearer <token>`，后端的 `get_current_user` 依赖函数解码JWT令牌获取用户ID。

### Q: 数据库表结构变了怎么办？
A: 修改Model文件后，运行 `alembic revision --autogenerate` 生成迁移脚本，再运行 `alembic upgrade head` 执行迁移。

### Q: PC端和移动端能共用同一个后端吗？
A: 可以，两个前端调用同一套API接口，后端不区分请求来源。

### Q: 如何本地开发调试？
A: 运行 `scripts/start.ps1` 启动所有服务，或分别启动后端和前端开发服务器。Vite开发服务器自带热更新。

---

> 本手册最后更新：2026年7月