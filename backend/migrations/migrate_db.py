"""
数据库迁移脚本 - 添加用户手机号和部门字段
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.models.database import engine

def migrate():
    """执行数据库迁移"""
    with engine.connect() as conn:
        # 添加 phone 字段
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
            print("✓ 添加 phone 字段成功")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ phone 字段已存在")
            else:
                print(f"✗ 添加 phone 字段失败: {e}")
        
        # 添加 department 字段
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(100)"))
            print("✓ 添加 department 字段成功")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ department 字段已存在")
            else:
                print(f"✗ 添加 department 字段失败: {e}")
        
        conn.commit()
        print("\n数据库迁移完成！")

if __name__ == "__main__":
    migrate()