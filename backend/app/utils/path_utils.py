"""
路径工具模块

提供项目路径相关的工具函数，确保代码可移植性。

使用方式：
    from app.utils.path_utils import get_project_root, get_env_file_path
    
    project_root = get_project_root()
    env_file = get_env_file_path()
"""
from pathlib import Path
from typing import Union


def get_project_root() -> Path:
    """
    获取项目根目录
    
    Returns:
        Path: 项目根目录路径
    
    说明：
        从当前文件向上两级找到项目根目录
        backend/app/utils/path_utils.py -> backend -> agent-project
    
    使用示例：
        >>> from app.utils.path_utils import get_project_root
        >>> root = get_project_root()
        >>> print(root)
        PosixPath('/home/user/agent-project')
    """
    return Path(__file__).parent.parent.parent.parent


def get_backend_root() -> Path:
    """
    获取 backend 目录路径
    
    Returns:
        Path: backend 目录路径
    
    使用示例：
        >>> from app.utils.path_utils import get_backend_root
        >>> backend = get_backend_root()
        >>> print(backend)
        PosixPath('/home/user/agent-project/backend')
    """
    return get_project_root() / 'backend'


def get_env_file_path() -> str:
    """
    获取 .env 文件的绝对路径
    
    Returns:
        str: .env 文件的绝对路径
    
    使用示例：
        >>> from app.utils.path_utils import get_env_file_path
        >>> env_file = get_env_file_path()
        >>> print(env_file)
        '/home/user/agent-project/.env'
    """
    return str(get_project_root() / '.env')


def get_data_dir() -> Path:
    """
    获取数据目录路径
    
    如果目录不存在，会自动创建。
    
    Returns:
        Path: 数据目录路径
    
    使用示例：
        >>> from app.utils.path_utils import get_data_dir
        >>> data_dir = get_data_dir()
        >>> print(data_dir)
        PosixPath('/home/user/agent-project/data')
    """
    data_dir = get_project_root() / 'data'
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    """
    获取日志目录路径
    
    如果目录不存在，会自动创建。
    
    Returns:
        Path: 日志目录路径
    
    使用示例：
        >>> from app.utils.path_utils import get_logs_dir
        >>> logs_dir = get_logs_dir()
        >>> print(logs_dir)
        PosixPath('/home/user/agent-project/logs')
    """
    logs_dir = get_project_root() / 'logs'
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
    
    Returns:
        Path: 目录路径对象
    
    使用示例：
        >>> from app.utils.path_utils import ensure_dir
        >>> my_dir = ensure_dir('/tmp/my_dir')
        >>> print(my_dir.exists())
        True
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_relative_path(absolute_path: Union[str, Path]) -> Path:
    """
    获取相对于项目根目录的相对路径
    
    Args:
        absolute_path: 绝对路径
    
    Returns:
        Path: 相对路径
    
    使用示例：
        >>> from app.utils.path_utils import get_relative_path
        >>> rel_path = get_relative_path('/home/user/agent-project/backend/app/main.py')
        >>> print(rel_path)
        PosixPath('backend/app/main.py')
    """
    absolute_path = Path(absolute_path)
    project_root = get_project_root()
    
    try:
        return absolute_path.relative_to(project_root)
    except ValueError:
        # 如果路径不在项目根目录下，返回原路径
        return absolute_path


# ==================== 常用路径常量 ====================

PROJECT_ROOT = get_project_root()
"""项目根目录"""

BACKEND_ROOT = get_backend_root()
"""Backend 目录"""

ENV_FILE = get_env_file_path()
""".env 文件路径"""

DATA_DIR = get_data_dir()
"""数据目录"""

LOGS_DIR = get_logs_dir()
"""日志目录"""