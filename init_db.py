# init_db.py
from database import Base, engine, SessionLocal
import models   # 👈 必须导入，确保 User/Product/Unit 都注册了

# 建表
Base.metadata.create_all(bind=engine)

print("✅ 数据库初始化完成")