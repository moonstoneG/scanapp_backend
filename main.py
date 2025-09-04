from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import requests
import json
from urllib.parse import urlparse

from auth import get_password_hash
import models, schemas, auth
from database import get_db, engine
from fastapi.security import OAuth2PasswordRequestForm

# ---------------- 数据库初始化 ----------------
models.Base.metadata.create_all(bind=engine)
# --- 放在 main.py 里 ---
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

import auth, schemas  # 如果你在用相对导入，改成: from . import auth, schemas
from database import get_db            # 相对导入版：from .database import get_db

ACCESS_EXPIRE_MINUTES = getattr(auth, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)
# 确保有默认 admin 用户
from auth import get_password_hash
db = next(get_db())
if not db.query(models.User).filter(models.User.username == "admin").first():
    db_user = models.User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        is_admin=True
    )
    db.add(db_user)
    db.commit()
db.close()

# ---------------- FastAPI 初始化 ----------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- 登录 ----------------
@app.post("/api/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# ---------------- 单位管理 ----------------
@app.get("/api/units", response_model=List[schemas.UnitOut])
def list_units(db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    return db.query(models.Unit).all()

@app.post("/api/units", response_model=schemas.UnitOut)
def create_unit(unit: schemas.UnitCreate, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    db_unit = models.Unit(name=unit.name)
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit

@app.put("/api/units/{unit_id}", response_model=schemas.UnitOut)
def update_unit(unit_id: int, unit: schemas.UnitCreate, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    db_unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    db_unit.name = unit.name
    db.commit()
    db.refresh(db_unit)
    return db_unit

@app.delete("/api/units/{unit_id}")
def delete_unit(unit_id: int, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    db_unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    db.delete(db_unit)
    db.commit()
    return {"ok": True}

# ---------------- 商品管理 ----------------
@app.get("/api/products", response_model=List[schemas.ProductOut])
def list_products(db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    return db.query(models.Product).all()

@app.post("/api/products", response_model=schemas.ProductOut)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.put("/api/products/{product_id}", response_model=schemas.ProductOut)
def update_product(product_id: int, product: schemas.ProductCreate, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"ok": True}

@app.get("/api/products/{sku}", response_model=schemas.ProductOut)
def get_product_by_sku(sku: str, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    product = db.query(models.Product).filter(models.Product.sku == sku).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
# ---------------- 扫码接口 ----------------
BASE = "https://y2wm.cn"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": BASE,
    "Referer": BASE + "/",
}

@app.post("/api/scan")
def scan_code(code: str, db: Session = Depends(get_db), _=Depends(auth.get_current_user)):
    # 判断是否二维码（y2wm.cn 域名），否则按 SKU 查本地 DB
    parsed = urlparse(code)
    if parsed.netloc == "y2wm.cn":
        url = BASE + "/CigaretteQrcodeQuery/CodeQuery/scanCode/v1"
        payload = {
            "qrcode": code,
            "clientInfo": HEADERS["User-Agent"].lower(),
            "latitude": None,
            "longitude": None,
            "ip": ""
        }
        r = requests.post(url, data=json.dumps(payload), headers=HEADERS, timeout=20, verify=False)
        if not r.ok:
            raise HTTPException(status_code=500, detail="External API error")
        resp = r.json()
        if not resp.get("success"):
            raise HTTPException(status_code=400, detail=resp.get("message", "API error"))
        meta = resp.get("data", {}).get("codeData", {}).get("meta", {})
        return {
            "source": "qrcode",
            "sku": None,  # 外部接口没有 SKU，可留空
            "name": meta.get("spuName"),
            "manufacturer": meta.get("ownerName"),
            "price": None,
            "unit": None,
        }
    else:
        # 本地 SKU -> 查数据库
        product = db.query(models.Product).filter(models.Product.sku == code).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return {
            "source": "sku",
            "sku": product.sku,
            "name": product.name,
            "manufacturer": product.manufacturer,
            "price": product.price,
            "unit": product.unit,
        }

@app.post("/api/auth/login")
async def login_unified(request: Request, db: Session = Depends(get_db)):
    """
    统一登录接口：同时支持 JSON 和 x-www-form-urlencoded 表单两种方式。
    JSON:   { "username": "...", "password": "..." }
    表单:   username=...&password=...
    返回:   { "access_token": "...", "token_type": "bearer" }
    """
    username = None
    password = None

    ctype = request.headers.get("content-type", "")
    try:
        if ctype.startswith("application/json"):
            data = await request.json()
            username = (data.get("username") or "").strip()
            password = data.get("password") or ""
        else:
            form = await request.form()
            # 兼容 OAuth2PasswordRequestForm 的字段名
            username = (form.get("username") or form.get("email") or "").strip()
            password = form.get("password") or form.get("pass") or ""
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid login payload")

    if not username or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing username or password")

    user = auth.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/me", response_model=schemas.UserOut)
def read_me(current_user=Depends(auth.get_current_user)):
    """
    返回当前登录用户信息（依赖 Authorization: Bearer <token>）
    """
    return current_user  # schemas.UserOut 已 from_attributes=True，可直接返回 ORM 对象
# ---------------- Admin 页面 ----------------
@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(content=open("admin.html", "r", encoding="utf-8").read())