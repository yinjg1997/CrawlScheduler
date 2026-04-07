# API 测试用例

本目录包含了 CrawlScheduler 后端 API 的测试用例。

## 运行测试

### 安装测试依赖

```bash
pip install -r requirements.txt
```

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
pytest tests/test_auth.py
```

### 运行特定测试用例

```bash
pytest tests/test_auth.py::test_login_success
```

### 运行特定模块的所有测试

```bash
pytest tests/ -k "test_create"
```

### 查看测试覆盖率（需要安装 pytest-cov）

```bash
pytest --cov=app --cov-report=html
```

## 测试结构

```
tests/
├── conftest.py          # 测试配置和 fixtures
├── test_auth.py         # 认证相关测试
├── test_projects.py     # 项目管理测试
├── test_crawlers.py     # 爬虫管理测试
├── test_schedules.py    # 调度管理测试
└── test_tasks.py        # 任务管理测试
```

## 测试覆盖的功能

### 认证 (test_auth.py)
- 用户登录
- 无效凭据处理
- 非活跃用户处理
- 获取当前用户信息
- Token 验证

### 项目管理 (test_projects.py)
- 创建项目
- 获取项目列表（分页、过滤）
- 获取单个项目
- 更新项目
- 删除项目
- 获取活跃项目

### 爬虫管理 (test_crawlers.py)
- 创建爬虫
- 获取爬虫列表（按项目过滤）
- 获取单个爬虫
- 更新爬虫
- 删除爬虫
- 手动执行爬虫

### 调度管理 (test_schedules.py)
- 创建调度
- 获取调度列表
- 获取单个调度
- 更新调度
- 删除调度
- 切换调度状态
- 预览下次运行时间
- 获取调度历史

### 任务管理 (test_tasks.py)
- 获取任务列表（按爬虫、状态过滤）
- 获取任务统计
- 获取任务日志
- 取消任务
- 获取任务状态
- 删除任务
- 批量删除任务

## Fixtures

测试中使用了以下 fixtures：

- `db_session`: 数据库会话
- `client`: 测试客户端
- `test_user`: 测试用户
- `test_superuser`: 测试超级用户
- `auth_headers`: 普通用户认证头
- `admin_headers`: 超级用户认证头
- `test_project`: 测试项目
- `test_crawler`: 测试爬虫
- `test_schedule`: 测试调度

## 注意事项

1. 测试使用内存 SQLite 数据库，不需要实际数据库连接
2. 测试数据在每个测试后自动回滚，保持测试独立性
3. 所有需要认证的接口都使用 fixture 提供的认证头
4. 异步测试使用 pytest-asyncio 插件
