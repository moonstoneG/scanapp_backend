from datetime import datetime
import json
from sqlalchemy import Column, DateTime, Integer, String, Float, Boolean, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    full_name = Column(String, nullable=True)   # 新增姓名字段
    department = Column(String, nullable=True)  # 新增部门字段
class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

class Product(Base):
    __tablename__ = "products"
     
    id = Column(Integer, primary_key=True, index=True) 
    sku = Column(String, unique=True, nullable=True)  # 可选、可唯一、可编辑
    name = Column(String, index=True, nullable=False)
    manufacturer = Column(String, nullable=True)
    price = Column(Float, default=0.0)
    unit = Column(String, nullable=True)  # 扩展字段
     # 在 Product 模型里新增一列

class CollabRoom(Base):
    __tablename__ = "collab_rooms"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(16), unique=True, index=True)  # 协作码，比如 6 位短码
    data_json = Column(Text, nullable=False)            # 存整个清单 JSON
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_list(self) -> dict:
        return json.loads(self.data_json)

    def set_list(self, data: dict):
        self.data_json = json.dumps(data, ensure_ascii=False)

class CollabSubmission(Base):
    __tablename__ = "collab_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, index=True)        # 协作码
    items_json = Column(Text, nullable=False)  # 用户提交的本地 items
    created_at = Column(DateTime, server_default=func.now())