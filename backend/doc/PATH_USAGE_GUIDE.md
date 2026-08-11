# 项目路径使用规范

## 📋 概述

为了确保项目代码的可移植性和可维护性，所有代码中不得硬编码绝对路径。必须使用动态路径获取方法。

---

## ✅ 正确的路径使用方式

### 1. 在 Python 脚本中获取当前脚本路径

```python
import os
from pathlib import Path

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)

# 获取脚本所在的目录
current_directory = os.path.dirname(script_path)

# 或者使用 Path（推荐）
current_directory = Path(__file__).parent
```

### 2. 使用路径工具模块（推荐）

```python
from app.utils.path_utils import (
    get_project_root,
    get_backend_root,
    get_env_file_path,
    get_data_dir,
    get_logs_dir
)

# 获取项目根目录
project_root = get_project_root()

# 获取 backend 目录
backend_root = get_backend_root()

# 获取 .env 文件路径
env_file = get_env_file_path()

# 获取数据目录
data_dir = get_data_dir()

# 获取日志目录
logs_dir = get_logs_dir()
```

---

## ❌ 错误的路径使用方式

### 1. 硬编码绝对路径

```python
# ❌ 错误：硬编码路径
sys.path.insert(0, '/home/s8066/agent-project/backend')

# ✅ 正确：动态获取路径
from pathlib import Path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))
```

### 2. 使用用户目录

```python
# ❌ 错误：硬编码用户目录
config_file = '/home/s8066/agent-project/.env'

# ✅ 正确：动态获取
from app.utils.path_utils import get_env_file_path
config_file = get_env_file_path()
```

---

## 📁 路径工具模块 API

### `get_project_root() -> Path`

获取项目根目录。

**返回**: 项目根目录路径

**示例**:
```python
from app.utils.path_utils import get_project_root

root = get_project_root()
# 返回: /home/user/agent-project
```

---

### `get_backend_root() -> Path`

获取 backend 目录路径。

**返回**: backend 目录路径

**示例**:
```python
from app.utils.path_utils import get_backend_root

backend = get_backend_root()
# 返回: /home/user/agent-project/backend
```

---

### `get_env_file_path() -> str`

获取 .env 文件的绝对路径。

**返回**: .env 文件的绝对路径（字符串）

**示例**:
```python
from app.utils.path_utils import get_env_file_path

env_file = get_env_file_path()
# 返回: /home/user/agent-project/.env
```

---

### `get_data_dir() -> Path`

获取数据目录路径。如果目录不存在，会自动创建。

**返回**: 数据目录路径

**示例**:
```python
from app.utils.path_utils import get_data_dir

data_dir = get_data_dir()
# 返回: /home/user/agent-project/data
```

---

### `get_logs_dir() -> Path`

获取日志目录路径。如果目录不存在，会自动创建。

**返回**: 日志目录路径

**示例**:
```python
from app.utils.path_utils import get_logs_dir

logs_dir = get_logs_dir()
# 返回: /home/user/agent-project/logs
```

---

### `ensure_dir(path: Union[str, Path]) -> Path`

确保目录存在，如果不存在则创建。

**参数**:
- `path`: 目录路径

**返回**: 目录路径对象

**示例**:
```python
from app.utils.path_utils import ensure_dir

my_dir = ensure_dir('/tmp/my_dir')
# 如果 /tmp/my_dir 不存在，会自动创建
```

---

### `get_relative_path(absolute_path: Union[str, Path]) -> Path`

获取相对于项目根目录的相对路径。

**参数**:
- `absolute_path`: 绝对路径

**返回**: 相对路径

**示例**:
```python
from app.utils.path_utils import get_relative_path

rel_path = get_relative_path('/home/user/agent-project/backend/app/main.py')
# 返回: backend/app/main.py
```

---

## 📝 常见场景示例

### 1. 测试脚本中添加项目路径

```python
import sys
from pathlib import Path

# 获取当前脚本的绝对路径
script_path = Path(__file__).resolve()
# 获取项目根目录
project_root = script_path.parent.parent

# 添加到 Python 路径
sys.path.insert(0, str(project_root / 'backend'))
```

### 2. 配置文件中引用 .env 文件

```python
from pydantic_settings import BaseSettings
from app.utils.path_utils import get_env_file_path

class Settings(BaseSettings):
    class Config:
        env_file = get_env_file_path()
```

### 3. 日志文件路径

```python
from app.utils.path_utils import get_logs_dir

logs_dir = get_logs_dir()
log_file = logs_dir / 'app.log'
```

### 4. 数据文件路径

```python
from app.utils.path_utils import get_data_dir

data_dir = get_data_dir()
data_file = data_dir / 'users.json'
```

---

## 🔍 检查清单

在提交代码前，请检查：

- [ ] 没有硬编码的绝对路径（如 `/home/user/...`）
- [ ] 使用 `Path(__file__)` 或 `os.path.abspath(__file__)` 获取当前路径
- [ ] 使用路径工具模块获取项目路径
- [ ] 配置文件使用动态路径
- [ ] 测试脚本使用动态路径

---

## 📚 参考资料

- [Python pathlib 文档](https://docs.python.org/3/library/pathlib.html)
- [Python os.path 文档](https://docs.python.org/3/library/os.path.html)

---

**最后更新**: 2026-08-06