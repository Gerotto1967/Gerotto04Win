from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, insert, update, delete, and_, or_, func, text
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime, date
import jwt
from passlib.context import CryptContext
import xml.etree.ElementTree as ET
from decimal import Decimal
import json
import asyncio
from collections import defaultdict
import requests

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database setup
DATABASE_URL = os.environ['DATABASE_URL']
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# SQLAlchemy Base
class Base(DeclarativeBase):
    pass

# Database Models
from sqlalchemy import String, DateTime, Boolean, Integer, Float, JSON, Date, Time, Text

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Empresa(Base):
    __tablename__ = "empresas"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cnpj: Mapped[str] = mapped_column(String, unique=True)
    razao_social: Mapped[str] = mapped_column(String)
    nome_fantasia: Mapped[Optional[str]] = mapped_column(String)
    endereco: Mapped[Optional[str]] = mapped_column(String)
    cidade: Mapped[Optional[str]] = mapped_column(String)
    uf: Mapped[str] = mapped_column(String)
    cep: Mapped[Optional[str]] = mapped_column(String)
    telefone: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Cliente(Base):
    __tablename__ = "clientes"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome: Mapped[str] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)
    telefone: Mapped[Optional[str]] = mapped_column(String)
    cpf_cnpj: Mapped[Optional[str]] = mapped_column(String)
    endereco: Mapped[Optional[str]] = mapped_column(String)
    cidade: Mapped[Optional[str]] = mapped_column(String)
    uf: Mapped[Optional[str]] = mapped_column(String)
    cep: Mapped[Optional[str]] = mapped_column(String)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Fornecedor(Base):
    __tablename__ = "fornecedores"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome: Mapped[str] = mapped_column(String)
    cnpj: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)
    telefone: Mapped[Optional[str]] = mapped_column(String)
    endereco: Mapped[Optional[str]] = mapped_column(String)
    cidade: Mapped[Optional[str]] = mapped_column(String)
    uf: Mapped[Optional[str]] = mapped_column(String)
    cep: Mapped[Optional[str]] = mapped_column(String)
    contato: Mapped[Optional[str]] = mapped_column(String)
    prazo_pagamento: Mapped[Optional[int]] = mapped_column(Integer, default=30)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Produto(Base):
    __tablename__ = "produtos"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome: Mapped[str] = mapped_column(String)
    codigo: Mapped[Optional[str]] = mapped_column(String)
    codigo_barras: Mapped[Optional[str]] = mapped_column(String)
    categoria: Mapped[Optional[str]] = mapped_column(String)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    preco_venda: Mapped[float] = mapped_column(Float, default=0.0)
    valor_pago: Mapped[float] = mapped_column(Float, default=0.0)  # Último valor pago
    custo_medio: Mapped[float] = mapped_column(Float, default=0.0)  # Custo médio calculado
    unidade_medida: Mapped[str] = mapped_column(String, default="UN")
    peso: Mapped[Optional[float]] = mapped_column(Float)
    imagem: Mapped[Optional[str]] = mapped_column(String)  # URL ou base64 da imagem
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# Security
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create the main app without a prefix
app = FastAPI(title="ERP System", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Dependency para sessão do banco
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Create tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def startup():
    await create_tables()
    
    # Create default user if not exists
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == "admin"))
        user = result.scalar_one_or_none()
        if not user:
            hashed_password = get_password_hash("admin123")
            new_user = User(
                email="admin",
                hashed_password=hashed_password,
                is_active=True
            )
            session.add(new_user)
            await session.commit()
            print("Default admin user created")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class UserLogin(BaseModel):
    email: str
    password: str

# Authentication Routes
@api_router.post("/auth/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {"email": user.email, "role": "administrator"}
    }

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "id": current_user.id}

# Dashboard
@api_router.get("/dashboard/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mock stats - implementar conforme necessário
    return {
        "clientes": 0,
        "fornecedores": 0,
        "produtos": 0,
        "empresas": 0,
        "contas_receber": 0,
        "contas_pagar": 0,
        "saldo_bancos": 0,
        "saldo_liquido": 0
    }

# Empresas Routes (básico para demonstração)
@api_router.get("/empresas")
async def listar_empresas(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Empresa).where(Empresa.ativo == True))
    return result.scalars().all()

# Outros endpoints básicos (clientes, fornecedores, etc.)
@api_router.get("/clientes")
async def listar_clientes(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@api_router.get("/fornecedores") 
async def listar_fornecedores(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@api_router.get("/produtos")
async def listar_produtos(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@api_router.get("/financeiro/contas")
async def listar_contas_financeiras(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@api_router.get("/contas-banco")
async def listar_contas_banco(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

# Include router
app.include_router(api_router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "ERP System API", "status": "running", "database": "PostgreSQL"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)