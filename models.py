from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
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
   