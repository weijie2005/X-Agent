"""
数据库迁移脚本：添加知识库相关表

执行方式：
    python -m migrations.add_knowledge_base_tables
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import engine, SessionLocal
from app.models.tables import Base, KnowledgeBase, Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """
    执行数据库迁移
    
    创建知识库和文档表
    """
    logger.info("Starting database migration...")
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # 验证表是否创建成功
        db = SessionLocal()
        try:
            # 尝试查询知识库表
            db.query(KnowledgeBase).first()
            logger.info("KnowledgeBase table verified")
            
            # 尝试查询文档表
            db.query(Document).first()
            logger.info("Document table verified")
            
            logger.info("Migration completed successfully!")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    migrate()