# CrawlScheduler

一个基于 FastAPI 和 Vue 3 的爬虫任务调度平台，类似 Crawlab。

## 功能特性

- 🕷️ **爬虫管理** - 创建、编辑、删除爬虫配置
- 📋 **任务执行** - 手动执行和自动调度爬虫任务
- ⏰ **定时调度** - Cron 表达式配置定时任务
- 📊 **任务监控** - 实时查看任务执行状态和日志
- 🔐 **用户认证** - JWT 身份认证和授权（默认账号提供）
- 👥 **用户管理** - 管理员可创建、编辑、删除用户，修改密码
- 🐍 **Python 环境** - 管理多个 Python 环境
- 📡 **实时日志** - WebSocket 推送任务执行日志
- 🛡️ **权限控制** - 管理员和普通用户权限分离

## 技术栈

### 后端
- FastAPI - 现代、快速的 Web 框架
- SQLAlchemy + Alembic - ORM 和数据库迁移
- APScheduler - 任务调度
- WebSocket - 实时日志推送
- JWT + Bcrypt - 用户认证和密码加密
- PostgreSQL - 生产数据库（开发使用 SQLite）

### 前端
- Vue 3 + TypeScript
- Vite
- Element Plus
- Vue Router - 路由守卫
- Pinia - 状态管理
- Axios - HTTP 请求拦截器

## 项目结构

```
crawlscheduler/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/     # API 路由
│   │   │   ├── auth.py          # 认证端点
│   │   │   ├── users.py         # 用户管理（仅管理员）
│   │   │   ├── crawlers.py     # 爬虫管理
│   │   │   ├── tasks.py        # 任务管理
│   │   │   ├── schedules.py    # 定时任务
│   │   │   └── ...
│   │   ├── models/  # 数据模型
│   │   │   └── user.py         # 用户模型
│   │   ├── schemas/ # Pydantic 模型
│   │   │   └── user.py         # 用户 Schema
│   │   ├── services/ # 业务逻辑
│   │   │   └── user_service.py # 用户服务
│   │   ├── auth.py   # 认证依赖
│   │   ├── security.py # 安全工具（JWT、密码）
│   │   └── ...
│   ├── alembic/      # 数据库迁移
│   └── requirements.txt
├── frontend/          # Vue 3 前端
│   └── src/
│       ├── api/      # API 客户端
│       │   ├── auth.ts         # 认证 API
│       │   ├── users.ts        # 用户管理 API
│       │   └── client.ts       # HTTP 客户端
│       ├── store/    # Pinia 状态管理
│       │   ├── auth.ts         # 认证状态
│       │   └── index.ts       # 应用状态
│       ├── views/    # 页面组件
│       │   ├── Login.vue       # 登录页面
│       │   ├── Users.vue       # 用户管理（仅管理员）
│       │   └── ...
│       ├── router/   # 路由配置
│       │   └── index.ts       # 路由守卫
│       └── ...
└── data/             # 运行时数据
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+
- npm 或 yarn

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 访问地址

- **前端应用**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 用户认证

系统已启用用户认证，所有业务功能都需要登录后使用。

#### 默认账号

系统提供了以下默认账号用于登录：

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| `admin` | `admin123` | 管理员 | 可访问用户管理功能 |
| `user` | `user123` | 普通用户 | 仅访问基础功能 |

**权限说明**：
- 管理员可以访问所有功能，包括用户管理
- 普通用户可以访问爬虫管理、任务调度等基础功能
- 只有管理员能看到"用户管理"菜单项
- 用户管理 API 端点仅对管理员开放

**重要提示**：
- 🔴 **生产环境部署时，必须立即修改默认密码**
- 🔴 建议在首次登录后修改密码
- 🔴 如果不需要账号，可以删除这些默认账号

#### 登录

使用上述默认账号或管理员创建的账号登录即可访问系统功能。

#### 用户管理

管理员可以通过用户管理界面（仅管理员可见）执行以下操作：

- **创建用户**：添加新用户到系统
- **编辑用户**：修改用户邮箱、启用/禁用状态
- **修改密码**：重置用户密码
- **删除用户**：删除用户（不能删除自己）

**注意**：创建用户时，默认为普通用户，如需设为管理员需通过数据库或 API 修改。

#### Token 说明

- JWT Token 有效期：24小时
- Token 过期后需要重新登录
- Token 存储在浏览器 localStorage 中

## 环境变量

### 后端

可以在项目根目录创建 `.env` 文件配置环境变量：

```bash
# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./data/crawlscheduler.db

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=True

# 时区配置
TIMEZONE=Asia/Shanghai

# 安全配置
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 路径配置
CRAWLERS_DIR=./data/crawlers
LOGS_DIR=./data/logs

# 调度器配置
SCHEDULER_ENABLED=True
```

**重要提示**：生产环境必须修改 `SECRET_KEY` 为随机生成的强密钥。

## API 端点

### 认证端点（无需认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/login` | 用户登录 |
| GET | `/api/v1/auth/me` | 获取当前用户信息（需要登录） |

> 注意：用户注册功能已禁用，需要通过管理员创建用户。

### 受保护端点（需要认证）

所有以下端点都需要在请求头中携带 JWT Token：

```
Authorization: Bearer <your_token>
```

所有以下端点都需要在请求头中携带 JWT Token：

```
Authorization: Bearer <your_token>
```

#### 用户管理（仅管理员）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/users/` | 获取用户列表（分页） |
| POST | `/api/v1/users/` | 创建新用户 |
| GET | `/api/v1/users/{id}` | 获取用户详情 |
| PUT | `/api/v1/users/{id}` | 更新用户信息 |
| PUT | `/api/v1/users/{id}/password` | 修改用户密码 |
| DELETE | `/api/v1/users/{id}` | 删除用户 |

> 注意：所有用户管理端点都需要管理员权限。

#### 爬虫管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/crawlers/` | 获取爬虫列表 |
| POST | `/api/v1/crawlers/` | 创建爬虫 |
| GET | `/api/v1/crawlers/{id}` | 获取爬虫详情 |
| PUT | `/api/v1/crawlers/{id}` | 更新爬虫 |
| DELETE | `/api/v1/crawlers/{id}` | 删除爬虫 |
| POST | `/api/v1/crawlers/{id}/execute` | 执行爬虫 |

#### 任务管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/tasks/` | 获取任务列表 |
| GET | `/api/v1/tasks/{id}` | 获取任务详情 |
| GET | `/api/v1/tasks/{id}/logs` | 获取任务日志 |
| POST | `/api/v1/tasks/{id}/cancel` | 取消任务 |
| POST | `/api/v1/tasks/{id}/retry` | 重试任务 |
| DELETE | `/api/v1/tasks/{id}` | 删除任务 |

#### 定时任务

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/schedules/` | 获取调度列表 |
| POST | `/api/v1/schedules/` | 创建调度 |
| GET | `/api/v1/schedules/{id}` | 获取调度详情 |
| PUT | `/api/v1/schedules/{id}` | 更新调度 |
| DELETE | `/api/v1/schedules/{id}` | 删除调度 |
| PUT | `/api/v1/schedules/{id}/toggle` | 切换调度状态 |
| GET | `/api/v1/schedules/_preview_next_run` | 预览下次执行时间 |

#### Python 环境

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/python-environments/` | 获取环境列表 |
| POST | `/api/v1/python-environments/` | 创建环境 |
| GET | `/api/v1/python-environments/{id}` | 获取环境详情 |
| PUT | `/api/v1/python-environments/{id}` | 更新环境 |
| DELETE | `/api/v1/python-environments/{id}` | 删除环境 |

## 开发指南

### 添加新的 API 端点

1. 在 `backend/app/api/` 创建路由文件
2. 使用认证依赖保护端点：

```python
from ..auth import get_current_active_user, get_current_superuser

# 普通用户认证
@router.get("/", dependencies=[Depends(get_current_active_user)])
async def get_data():
    return {"data": "protected"}

# 管理员认证
@router.get("/admin", dependencies=[Depends(get_current_superuser)])
async def get_admin_data():
    return {"data": "admin only"}
```

3. 在 `backend/app/api/__init__.py` 导入路由
4. 在 `backend/app/main.py` 注册路由

### 添加新的前端页面

1. 在 `frontend/src/views/` 创建 Vue 组件
2. 在 `frontend/src/router/index.ts` 添加路由：

```typescript
{
  path: '/new-page',
  name: 'NewPage',
  component: () => import('@/views/NewPage.vue'),
  meta: {
    requiresAuth: true,      // 需要认证
    requiresAdmin: false      // 需要管理员（可选）
  }
}
```

路由守卫会自动处理认证和权限检查。

3. 如需在菜单中控制显示，在 `frontend/src/App.vue` 中根据权限条件渲染菜单项：

```vue
<el-menu-item v-if="authStore.isSuperuser" index="/admin-page">
  <el-icon><Setting /></el-icon>
  <span>管理员功能</span>
</el-menu-item>
```

## 安全建议

1. **生产环境必须修改 SECRET_KEY**
2. **使用 HTTPS** 部署到生产环境
3. **定期更新依赖** 保持系统安全
4. **限制数据库访问** 使用强密码和访问控制
5. **定期备份数据** 防止数据丢失

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请提交 Issue。
