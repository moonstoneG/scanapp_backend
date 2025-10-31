from fastapi import Body, FastAPI, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Union
import requests
import json
from pydantic import BaseModel
from urllib.parse import urlparse
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from docx import Document
import os, uuid
from auth import get_password_hash
import models, schemas, auth
from database import get_db, engine
from fastapi.security import OAuth2PasswordRequestForm
from models import User
from fastapi import File, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
import io
import pandas as pd
from sqlalchemy.orm import Session
from typing import Dict, Any
import auth
import models
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Form, Depends
from fastapi.responses import StreamingResponse
from typing import List
import io
import auth
from doc_generate import Payload, Item, generate_doc_local,iter_all_paragraphs, simple_run_replace,replace_core_placeholders,merge_items
import cn2an
from doc_generate2 import Payload as PayloadPricing, Item as ItemPricing, generate_doc_pricing
from users import router as users_router
import logging
from passlib.context import CryptContext

logging.basicConfig(level=logging.INFO)

# ---------------- 数据库初始化 ----------------
models.Base.metadata.create_all(bind=engine)
# --- 放在 main.py 里 ---
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

import auth, schemas  # 如果你在用相对导入，改成: from . import auth, schemas
from database import get_db            # 相对导入版：from .database import get_db

VERSION_FILE = os.path.join(os.path.dirname(__file__), "version.json")
ACCESS_EXPIRE_MINUTES = getattr(auth, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)
# 确保有默认 admin 用户
from auth import get_password_hash

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 密码哈希
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 密码验证
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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

# --------- Pydantic 模型 ---------
class ItemModel(BaseModel):
    name: str
    unit: str
    qty: float

class DocPayload(BaseModel):
    bureau: str
    suspect: str
    behavior: str
    items: List[ItemModel]


class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False
    full_name: str = None    # 新增字段：人名
    department: str = None   # 新增字段：部门
    
    
# ---------------- FastAPI 初始化 ----------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix="/api/users")

app.mount("/scanapp/static", StaticFiles(directory="static"), name="static")
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


@app.post("/api/doc/generate1")
def generate_doc1(
    bureau: str = Form(...),
    suspect: str = Form(...),
    behavior: str = Form(...),
    items: str = Form(...),  # 前端传 JSON 字符串
    _=Depends(auth.get_current_user)
):
    try:
        items_data = json.loads(items)  # list[dict]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法解析 items JSON: {e}")
    
    def convert_qty(unit: str, qty: float) -> float:
        unit = (unit or "").strip()
        if unit in ["盒", "包"]:
            return round(qty * 0.1, 1)
        elif unit in ["箱", "件"]:
            return round(qty * 50, 1)
        else:
            return round(qty, 1)

    payload_items = []
    logging.info(f"👉 前端传来 items 数量: {len(items_data)}")
    for it in items_data:  # it 是 dict
        name = it.get("name", "")
        unit = it.get("unit", "")
        qty = it.get("qty", 0)

        try:
            qty_val = float(qty)
        except Exception:
            raise HTTPException(status_code=400, detail=f"数量不是有效数字: {qty}")

        qty_converted = convert_qty(unit, qty_val)
        payload_items.append(Item(name, "条", qty_converted))  # ✅ 统一为条
        payload_items = merge_items(payload_items)
        payload = Payload(
        bureau=bureau,
        suspect=suspect,
        behavior=behavior,
        items=payload_items
    )

    buf = io.BytesIO()
    generate_doc_local(payload, output=buf)  # 写入内存
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="preserve.docx"'}
    )
@app.post("/api/doc/generate2")
def generate_doc2(
    bureau: str = Form(...),
    suspect: str = Form(...),
    behavior: str = Form(...),
    items: str = Form(...),  # 前端还是传 JSON 字符串
    _=Depends(auth.get_current_user)
):
    try:
        items_data = json.loads(items)  # list[dict]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法解析 items JSON: {e}")

    def convert_qty(unit: str, qty: float) -> float:
        unit = (unit or "").strip()
        if unit in ["盒", "包"]:
            return round(qty * 0.1, 1)
        elif unit in ["箱", "件"]:
            return round(qty * 50, 1)
        else:
            return round(qty, 1)
    
    payload_items = []
    
    for it in items_data:
        name = it.get("name", "")
        unit = it.get("unit", "")
        qty = it.get("qty", 0)
        qty_val = float(qty)
        qty_converted = convert_qty(unit, qty_val)
        payload_items.append(Item(name, "条", qty_converted))
    payload_items = merge_items(payload_items)
    payload = Payload(
        bureau=bureau,
        suspect=suspect,
        behavior=behavior,
        items=payload_items,
    )

    # === 新增的 Scene Transcript 替换逻辑 ===
    def replace_scene_transcript(doc: Document, items: List[Item]):
        parts = []
        for it in items:
            qty_cn = cn2an.an2cn(str(float(it.qty)), "up")
            parts.append(f"{it.name}{qty_cn}{it.unit}")
        transcript = "、".join(parts)

        kinds = len(items)
        total_qty = sum(it.qty for it in items)
        kinds_cn = cn2an.an2cn(str(kinds), "up")
        qty_cn   = cn2an.an2cn(str(float(total_qty)), "up")

        for p in iter_all_paragraphs(doc):
            simple_run_replace(p, "{{Scene Transcript}}", transcript)
            simple_run_replace(p, "{{Kind}}", kinds_cn)
            simple_run_replace(p, "{{Qty}}", qty_cn)

    # === 生成文档 ===
    doc = Document("现场笔录.docx")  # ⚠️ 新模板文件
    replace_core_placeholders(doc, payload)
    replace_scene_transcript(doc, payload.items)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="scene.docx"'}
    )

@app.post("/api/doc/generate3")
def generate_doc3(
    bureau: str = Form(...),
    suspect: str = Form(...),
    behavior: str = Form(...),
    items: str = Form(...),  # 前端传 JSON 字符串
    _=Depends(auth.get_current_user)
):
    try:
        items_data = json.loads(items)  # list[dict]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法解析 items JSON: {e}")
    
    def convert_qty(unit: str, qty: float) -> float:
        unit = (unit or "").strip()
        if unit in ["盒", "包"]:
            return round(qty * 0.1, 1)
        elif unit in ["箱", "件"]:
            return round(qty * 50, 1)
        else:
            return round(qty, 1)

    payload_items = []
    logging.info(f"👉 前端传来 items 数量: {len(items_data)}")
    for it in items_data:  # it 是 dict
        name = it.get("name", "")
        unit = it.get("unit", "")
        qty = it.get("qty", 0)

        try:
            qty_val = float(qty)
        except Exception:
            raise HTTPException(status_code=400, detail=f"数量不是有效数字: {qty}")

        qty_converted = convert_qty(unit, qty_val)
        payload_items.append(Item(name, "条", qty_converted))  # ✅ 统一为条
    payload_items = merge_items(payload_items)
    payload = Payload(
        bureau=bureau,
        suspect=suspect,
        behavior=behavior,
        items=payload_items
    )

    buf = io.BytesIO()
    generate_doc_local(payload,template = "证据先行登记保存通知书.docx" ,output=buf)  # 写入内存
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="preserve.docx"'}
    )

@app.post("/api/doc/generate4")
def generate_doc4(
    bureau: str = Form(...),
    items: str = Form(...),   # 前端还是传 JSON 字符串
    _=Depends(auth.get_current_user)
):
    try:
        items_data = json.loads(items)  # 解析成 list[dict]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法解析 items JSON: {e}")

    def convert_qty(unit: str, qty: float) -> float:
        unit = (unit or "").strip()
        if unit in ["盒", "包"]:
            return round(qty * 0.1, 1)
        elif unit in ["箱", "件"]:
            return round(qty * 50, 1)
        else:
            return round(qty, 1)

    payload_items = []
    for it in items_data:
        name = it.get("name", "")
        unit = it.get("unit", "")
        qty = it.get("qty", 0)
        price = it.get("price", 0)
        qty_val = float(qty)
        qty_converted = convert_qty(unit, qty_val)
        payload_items.append(ItemPricing(name, "条", qty_converted, float(price)))
    payload_items = merge_items(payload_items)
    payload = Payload(
        bureau=bureau,
        suspect=" ",
        behavior=" ",
        items=payload_items
    )

    buf = io.BytesIO()
    generate_doc_pricing(payload, template="涉案物品核价表.docx", output=buf)  # 写入内存
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="pricing.docx"'}
    )
# ---- 工具：列名映射（容错大小写 / 中英文 / 空格）----
_COLUMN_ALIASES = {
    "sku": {"sku", "货号", "编号", "SKU", "Sku"},
    "name": {"name", "商品名", "名称", "品名", "Name"},
    "manufacturer": {"manufacturer", "厂家", "品牌", "厂商", "Manufacturer"},
    "price": {"price", "价格", "单价", "Price"},
    "unit": {"unit", "单位", "Unit"},
}

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    col_map: Dict[str, str] = {}
    for tgt, aliases in _COLUMN_ALIASES.items():
        for c in df.columns:
            plain = str(c).strip()
            if plain in aliases:
                col_map[plain] = tgt
            elif plain.lower() in {a.lower() for a in aliases}:
                col_map[plain] = tgt
    # 把能识别的列统一改名为标准名
    df = df.rename(columns=col_map)
    # 只保留我们要的列
    keep = [c for c in ["sku", "name", "manufacturer", "price", "unit"] if c in df.columns]
    return df[keep]

def _safe_float(v: Any) -> float:
    if pd.isna(v) or v is None or v == "":
        return 0.0
    try:
        return float(v)
    except Exception:
        return 0.0

# ====== 导入模板下载 ======
@app.get("/api/import/template")
def download_template(_=Depends(auth.get_current_user)):  # 仅管理员
    buf = io.StringIO()
    buf.write("sku,name,manufacturer,price,unit\n")
    # 留一行示例
    buf.write("SKU001,示例商品,示例厂家,12.50,盒\n")
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="products_template.csv"'},
    )

# ====== 商品批量导入（xlsx/csv）======
@app.post("/api/import/products")
def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(auth.get_current_user)  # 仅管理员
):
    # 校验文件类型
    filename = file.filename or ""
    name_lower = filename.lower()
    try:
        if name_lower.endswith(".xlsx"):
            content = file.file.read()
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        elif name_lower.endswith(".csv"):
            content = file.file.read()
            df = pd.read_csv(io.BytesIO(content))
        else:
            return JSONResponse(status_code=400, content={"detail": "仅支持 .xlsx 或 .csv 文件"})

        if df.empty:
            return {"inserted": 0, "updated": 0, "skipped": 0, "message": "文件为空"}

        df = _normalize_columns(df)
        required = {"sku", "name"}
        if not required.issubset(set(df.columns)):
            return JSONResponse(
                status_code=400,
                content={"detail": f"缺少必要列：{required}，当前列：{list(df.columns)}"}
            )

        ins, upd, skip = 0, 0, 0

        # 预取所有 unit 列表，缺的自动加入
        from models import Unit, Product  # 根据你的项目结构
        existing_units = {u.name for u in db.query(Unit).all()}

        for _, row in df.iterrows():
            sku = str(row.get("sku", "")).strip()
            if not sku:
                skip += 1
                continue

            name = str(row.get("name", "")).strip()
            manufacturer = str(row.get("manufacturer", "")).strip() if "manufacturer" in row else None
            price = _safe_float(row.get("price"))
            unit_name = str(row.get("unit", "")).strip() if "unit" in row else None

            # 单位不存在则创建
            if unit_name and unit_name not in existing_units:
                new_u = Unit(name=unit_name)
                db.add(new_u)
                db.flush()  # 先拿到 id
                existing_units.add(unit_name)

            # upsert by sku
            p = db.query(Product).filter(Product.sku == sku).first()
            if p:
                # 更新
                p.name = name or p.name
                p.manufacturer = manufacturer if manufacturer else p.manufacturer
                p.price = price if price is not None else p.price
                p.unit = unit_name if unit_name else p.unit
                upd += 1
            else:
                # 新增
                new_p = Product(
                    sku=sku,
                    name=name,
                    manufacturer=manufacturer or None,
                    price=price,
                    unit=unit_name or None,
                )
                db.add(new_p)
                ins += 1

        db.commit()
        return {"inserted": ins, "updated": upd, "skipped": skip, "message": "导入完成"}

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail": f"导入失败：{e}"})
    
@app.get("/api/import/template")
@app.get("/api/import/template/")
def download_template(_=Depends(auth.get_current_user)):
    # 生成一个标准模板 CSV（也可以换 xlsx）
    buf = io.StringIO()
    buf.write("sku,name,manufacturer,price,unit\n")
    buf.write("TEST001,示例商品,示例厂家,12.34,盒\n")
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=product_template.csv"}
    )

@app.get("/api/version")
def get_version(_=Depends(auth.get_current_user)):
    """
    返回最新版本号和下载链接
    """
    if not os.path.exists(VERSION_FILE):
        raise HTTPException(status_code=404, detail="version.json not found")
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(data)
# ---------------- Admin 页面 ----------------
@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(content=open("admin.html", "r", encoding="utf-8").read())