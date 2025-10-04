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

class Estoque(Base):
    __tablename__ = "estoque"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    produto_id: Mapped[str] = mapped_column(String)
    cnpj_empresa: Mapped[str] = mapped_column(String)  # CNPJ da empresa
    quantidade: Mapped[float] = mapped_column(Float, default=0.0)
    quantidade_reservada: Mapped[float] = mapped_column(Float, default=0.0)
    estoque_minimo: Mapped[float] = mapped_column(Float, default=0.0)
    localizacao: Mapped[Optional[str]] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EstoqueMovimento(Base):
    __tablename__ = "estoque_movimentos"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    produto_id: Mapped[str] = mapped_column(String)
    cnpj_empresa: Mapped[str] = mapped_column(String)
    tipo: Mapped[str] = mapped_column(String)  # entrada, saida, ajuste, transferencia
    quantidade: Mapped[float] = mapped_column(Float)
    quantidade_anterior: Mapped[float] = mapped_column(Float)
    valor_unitario: Mapped[float] = mapped_column(Float)
    observacao: Mapped[Optional[str]] = mapped_column(String)
    documento: Mapped[Optional[str]] = mapped_column(String)
    usuario: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ContaBanco(Base):
    __tablename__ = "contas_banco"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nome: Mapped[str] = mapped_column(String)
    banco: Mapped[str] = mapped_column(String)
    agencia: Mapped[Optional[str]] = mapped_column(String)
    conta: Mapped[Optional[str]] = mapped_column(String)
    tipo: Mapped[str] = mapped_column(String)  # conta_corrente, poupanca, caixa
    saldo_inicial: Mapped[float] = mapped_column(Float, default=0.0)
    saldo_atual: Mapped[float] = mapped_column(Float, default=0.0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ContaRecebePaga(Base):
    __tablename__ = "contas_recebe_paga"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tipo: Mapped[str] = mapped_column(String)  # receber, pagar
    descricao: Mapped[str] = mapped_column(String)
    valor: Mapped[float] = mapped_column(Float)
    data_vencimento: Mapped[date] = mapped_column(Date)
    data_pagamento: Mapped[Optional[date]] = mapped_column(Date)
    valor_pago: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="pendente")  # pendente, pago, vencido
    categoria: Mapped[Optional[str]] = mapped_column(String)
    cliente_fornecedor_id: Mapped[Optional[str]] = mapped_column(String)
    conta_banco_id: Mapped[Optional[str]] = mapped_column(String)
    observacoes: Mapped[Optional[str]] = mapped_column(Text)
    documento: Mapped[Optional[str]] = mapped_column(String)
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

# Função para buscar empresas cadastradas
async def get_empresas_config():
    """Retorna configuração de empresas do banco de dados"""
    async with async_session() as session:
        result = await session.execute(select(Empresa).where(Empresa.ativo == True))
        empresas = result.scalars().all()
        config = {}
        for empresa in empresas:
            config[empresa.cnpj] = {
                "nome": empresa.nome_fantasia or empresa.razao_social, 
                "uf": empresa.uf
            }
        return config

# Dependency para sessão do banco
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Pydantic Models
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class EmpresaCreate(BaseModel):
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: str
    cep: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None

class EmpresaResponse(BaseModel):
    id: str
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str]
    endereco: Optional[str]
    cidade: Optional[str]
    uf: str
    cep: Optional[str]
    telefone: Optional[str]
    email: Optional[str]
    ativo: bool
    created_at: datetime

class ClienteCreate(BaseModel):
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    observacoes: Optional[str] = None

class ClienteResponse(BaseModel):
    id: str
    nome: str
    email: Optional[str]
    telefone: Optional[str]
    cpf_cnpj: Optional[str]
    endereco: Optional[str]
    cidade: Optional[str]
    uf: Optional[str]
    cep: Optional[str]
    ativo: bool
    observacoes: Optional[str]
    created_at: datetime

class FornecedorCreate(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    contato: Optional[str] = None
    prazo_pagamento: Optional[int] = 30

class FornecedorResponse(BaseModel):
    id: str
    nome: str
    cnpj: Optional[str]
    email: Optional[str]
    telefone: Optional[str]
    endereco: Optional[str]
    cidade: Optional[str]
    uf: Optional[str]
    cep: Optional[str]
    contato: Optional[str]
    prazo_pagamento: Optional[int]
    ativo: bool
    created_at: datetime

class ProdutoCreate(BaseModel):
    nome: str
    codigo: Optional[str] = None
    codigo_barras: Optional[str] = None
    categoria: Optional[str] = None
    descricao: Optional[str] = None
    preco_venda: float = 0.0
    valor_pago: float = 0.0
    unidade_medida: str = "UN"
    peso: Optional[float] = None
    imagem: Optional[str] = None

class ProdutoResponse(BaseModel):
    id: str
    nome: str
    codigo: Optional[str]
    codigo_barras: Optional[str]
    categoria: Optional[str]
    descricao: Optional[str]
    preco_venda: float
    valor_pago: float
    custo_medio: float
    unidade_medida: str
    peso: Optional[float]
    imagem: Optional[str]
    ativo: bool
    created_at: datetime

class EstoqueResponse(BaseModel):
    produto_id: str
    cnpj_empresa: str
    quantidade: float
    quantidade_reservada: float
    estoque_minimo: float
    localizacao: Optional[str]

class ContaBancoCreate(BaseModel):
    nome: str
    banco: str
    agencia: Optional[str] = None
    conta: Optional[str] = None
    tipo: str
    saldo_inicial: float = 0.0

class ContaBancoResponse(BaseModel):
    id: str
    nome: str
    banco: str
    agencia: Optional[str]
    conta: Optional[str]
    tipo: str
    saldo_inicial: float
    saldo_atual: float
    ativo: bool
    created_at: datetime

class ContaRecebePageCreate(BaseModel):
    tipo: str  # receber, pagar
    descricao: str
    valor: float
    data_vencimento: date
    categoria: Optional[str] = None
    cliente_fornecedor_id: Optional[str] = None
    conta_banco_id: Optional[str] = None
    observacoes: Optional[str] = None
    documento: Optional[str] = None

class ContaRecebePageResponse(BaseModel):
    id: str
    tipo: str
    descricao: str
    valor: float
    data_vencimento: date
    data_pagamento: Optional[date]
    valor_pago: Optional[float]
    status: str
    categoria: Optional[str]
    cliente_fornecedor_id: Optional[str]
    conta_banco_id: Optional[str]
    observacoes: Optional[str]
    documento: Optional[str]
    created_at: datetime

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

# Authentication Routes
@api_router.post("/auth/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "id": current_user.id}

# Empresas Routes
@api_router.post("/empresas", response_model=EmpresaResponse)
async def criar_empresa(empresa: EmpresaCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_empresa = Empresa(**empresa.dict())
    db.add(new_empresa)
    await db.commit()
    await db.refresh(new_empresa)
    return new_empresa

@api_router.get("/empresas", response_model=List[EmpresaResponse])
async def listar_empresas(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Empresa).where(Empresa.ativo == True))
    return result.scalars().all()

@api_router.get("/empresas/{empresa_id}", response_model=EmpresaResponse)
async def obter_empresa(empresa_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return empresa

@api_router.put("/empresas/{empresa_id}", response_model=EmpresaResponse)
async def atualizar_empresa(empresa_id: str, empresa_data: EmpresaCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    for key, value in empresa_data.dict(exclude_unset=True).items():
        setattr(empresa, key, value)
    
    await db.commit()
    await db.refresh(empresa)
    return empresa

@api_router.delete("/empresas/{empresa_id}")
async def deletar_empresa(empresa_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    empresa = result.scalar_one_or_none()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    empresa.ativo = False
    await db.commit()
    return {"message": "Empresa desativada com sucesso"}

# Clientes Routes
@api_router.post("/clientes", response_model=ClienteResponse)
async def criar_cliente(cliente: ClienteCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_cliente = Cliente(**cliente.dict())
    db.add(new_cliente)
    await db.commit()
    await db.refresh(new_cliente)
    return new_cliente

@api_router.get("/clientes", response_model=List[ClienteResponse])
async def listar_clientes(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Cliente).where(Cliente.ativo == True))
    return result.scalars().all()

@api_router.get("/clientes/{cliente_id}", response_model=ClienteResponse)
async def obter_cliente(cliente_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

@api_router.put("/clientes/{cliente_id}", response_model=ClienteResponse)
async def atualizar_cliente(cliente_id: str, cliente_data: ClienteCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    for key, value in cliente_data.dict(exclude_unset=True).items():
        setattr(cliente, key, value)
    
    await db.commit()
    await db.refresh(cliente)
    return cliente

@api_router.delete("/clientes/{cliente_id}")
async def deletar_cliente(cliente_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    cliente.ativo = False
    await db.commit()
    return {"message": "Cliente desativado com sucesso"}

# Fornecedores Routes
@api_router.post("/fornecedores", response_model=FornecedorResponse)
async def criar_fornecedor(fornecedor: FornecedorCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_fornecedor = Fornecedor(**fornecedor.dict())
    db.add(new_fornecedor)
    await db.commit()
    await db.refresh(new_fornecedor)
    return new_fornecedor

@api_router.get("/fornecedores", response_model=List[FornecedorResponse])
async def listar_fornecedores(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Fornecedor).where(Fornecedor.ativo == True))
    return result.scalars().all()

@api_router.get("/fornecedores/{fornecedor_id}", response_model=FornecedorResponse)
async def obter_fornecedor(fornecedor_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Fornecedor).where(Fornecedor.id == fornecedor_id))
    fornecedor = result.scalar_one_or_none()
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    return fornecedor

@api_router.put("/fornecedores/{fornecedor_id}", response_model=FornecedorResponse)
async def atualizar_fornecedor(fornecedor_id: str, fornecedor_data: FornecedorCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Fornecedor).where(Fornecedor.id == fornecedor_id))
    fornecedor = result.scalar_one_or_none()
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    
    for key, value in fornecedor_data.dict(exclude_unset=True).items():
        setattr(fornecedor, key, value)
    
    await db.commit()
    await db.refresh(fornecedor)
    return fornecedor

@api_router.delete("/fornecedores/{fornecedor_id}")
async def deletar_fornecedor(fornecedor_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Fornecedor).where(Fornecedor.id == fornecedor_id))
    fornecedor = result.scalar_one_or_none()
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    
    fornecedor.ativo = False
    await db.commit()
    return {"message": "Fornecedor desativado com sucesso"}

# Produtos Routes
@api_router.post("/produtos", response_model=ProdutoResponse)
async def criar_produto(produto: ProdutoCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_produto = Produto(**produto.dict())
    new_produto.custo_medio = produto.valor_pago  # Inicializa custo médio
    db.add(new_produto)
    await db.commit()
    await db.refresh(new_produto)
    return new_produto

@api_router.get("/produtos", response_model=List[ProdutoResponse])
async def listar_produtos(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Produto).where(Produto.ativo == True))
    return result.scalars().all()

@api_router.get("/produtos/{produto_id}", response_model=ProdutoResponse)
async def obter_produto(produto_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Produto).where(Produto.id == produto_id))
    produto = result.scalar_one_or_none()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@api_router.put("/produtos/{produto_id}", response_model=ProdutoResponse)
async def atualizar_produto(produto_id: str, produto_data: ProdutoCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Produto).where(Produto.id == produto_id))
    produto = result.scalar_one_or_none()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    for key, value in produto_data.dict(exclude_unset=True).items():
        setattr(produto, key, value)
    
    # Recalcula custo médio se valor_pago mudou
    if hasattr(produto_data, 'valor_pago') and produto_data.valor_pago:
        produto.custo_medio = produto_data.valor_pago
    
    await db.commit()
    await db.refresh(produto)
    return produto

@api_router.delete("/produtos/{produto_id}")
async def deletar_produto(produto_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Produto).where(Produto.id == produto_id))
    produto = result.scalar_one_or_none()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    produto.ativo = False
    await db.commit()
    return {"message": "Produto desativado com sucesso"}

# Estoque Routes
@api_router.get("/estoque/{produto_id}")
async def obter_estoque_produto(produto_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Estoque).where(Estoque.produto_id == produto_id))
    estoques = result.scalars().all()
    
    # Busca informações das empresas
    empresas_config = await get_empresas_config()
    
    estoque_por_empresa = []
    total_quantidade = 0
    
    for estoque in estoques:
        empresa_info = empresas_config.get(estoque.cnpj_empresa, {"nome": "Empresa não encontrada"})
        estoque_por_empresa.append({
            "cnpj": estoque.cnpj_empresa,
            "nome_empresa": empresa_info["nome"],
            "quantidade": estoque.quantidade,
            "quantidade_reservada": estoque.quantidade_reservada,
            "estoque_minimo": estoque.estoque_minimo,
            "localizacao": estoque.localizacao
        })
        total_quantidade += estoque.quantidade
    
    return {
        "produto_id": produto_id,
        "estoque_por_empresa": estoque_por_empresa,
        "total_quantidade": total_quantidade
    }

@api_router.post("/estoque/ajuste")
async def ajustar_estoque(
    produto_id: str = Form(...),
    cnpj_empresa: str = Form(...),
    quantidade: float = Form(...),
    tipo: str = Form(...),  # entrada, saida, ajuste
    observacao: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Busca ou cria registro de estoque
    result = await db.execute(select(Estoque).where(
        and_(Estoque.produto_id == produto_id, Estoque.cnpj_empresa == cnpj_empresa)
    ))
    estoque = result.scalar_one_or_none()
    
    if not estoque:
        estoque = Estoque(
            produto_id=produto_id,
            cnpj_empresa=cnpj_empresa,
            quantidade=0.0
        )
        db.add(estoque)
    
    quantidade_anterior = estoque.quantidade
    
    # Aplica ajuste
    if tipo == "entrada" or tipo == "ajuste":
        estoque.quantidade += quantidade
    elif tipo == "saida":
        estoque.quantidade -= quantidade
    
    # Registra movimento
    movimento = EstoqueMovimento(
        produto_id=produto_id,
        cnpj_empresa=cnpj_empresa,
        tipo=tipo,
        quantidade=quantidade,
        quantidade_anterior=quantidade_anterior,
        valor_unitario=0.0,  # TODO: implementar valor
        observacao=observacao,
        usuario=current_user.email
    )
    db.add(movimento)
    
    await db.commit()
    return {"message": "Estoque ajustado com sucesso"}

# Contas Bancárias Routes
@api_router.post("/contas-banco", response_model=ContaBancoResponse)
async def criar_conta_banco(conta: ContaBancoCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_conta = ContaBanco(**conta.dict())
    new_conta.saldo_atual = conta.saldo_inicial
    db.add(new_conta)
    await db.commit()
    await db.refresh(new_conta)
    return new_conta

@api_router.get("/contas-banco", response_model=List[ContaBancoResponse])
async def listar_contas_banco(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ContaBanco).where(ContaBanco.ativo == True))
    return result.scalars().all()

# Contas a Receber/Pagar Routes
@api_router.post("/financeiro/contas", response_model=ContaRecebePageResponse)
async def criar_conta_recebe_paga(conta: ContaRecebePageCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_conta = ContaRecebePaga(**conta.dict())
    db.add(new_conta)
    await db.commit()
    await db.refresh(new_conta)
    return new_conta

@api_router.get("/financeiro/contas")
async def listar_contas_recebe_paga(tipo: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(ContaRecebePaga)
    if tipo:
        query = query.where(ContaRecebePaga.tipo == tipo)
    
    result = await db.execute(query.order_by(ContaRecebePaga.data_vencimento))
    contas = result.scalars().all()
    
    return [
        {
            "id": conta.id,
            "tipo": conta.tipo,
            "descricao": conta.descricao,
            "valor": conta.valor,
            "data_vencimento": conta.data_vencimento.isoformat(),
            "data_pagamento": conta.data_pagamento.isoformat() if conta.data_pagamento else None,
            "valor_pago": conta.valor_pago,
            "status": conta.status,
            "categoria": conta.categoria,
            "cliente_fornecedor_id": conta.cliente_fornecedor_id,
            "conta_banco_id": conta.conta_banco_id,
            "observacoes": conta.observacoes,
            "documento": conta.documento,
            "created_at": conta.created_at.isoformat()
        } for conta in contas
    ]

# Dashboard
@api_router.get("/dashboard/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Conta clientes
    result = await db.execute(select(func.count(Cliente.id)).where(Cliente.ativo == True))
    total_clientes = result.scalar()
    
    # Conta fornecedores  
    result = await db.execute(select(func.count(Fornecedor.id)).where(Fornecedor.ativo == True))
    total_fornecedores = result.scalar()
    
    # Conta produtos
    result = await db.execute(select(func.count(Produto.id)).where(Produto.ativo == True))
    total_produtos = result.scalar()
    
    # Conta empresas
    result = await db.execute(select(func.count(Empresa.id)).where(Empresa.ativo == True))
    total_empresas = result.scalar()
    
    # Soma contas a receber pendentes
    result = await db.execute(select(func.sum(ContaRecebePaga.valor)).where(
        and_(ContaRecebePaga.tipo == "receber", ContaRecebePaga.status == "pendente")
    ))
    total_receber = result.scalar() or 0
    
    # Soma contas a pagar pendentes
    result = await db.execute(select(func.sum(ContaRecebePaga.valor)).where(
        and_(ContaRecebePaga.tipo == "pagar", ContaRecebePaga.status == "pendente")
    ))
    total_pagar = result.scalar() or 0
    
    # Saldo total das contas bancárias
    result = await db.execute(select(func.sum(ContaBanco.saldo_atual)).where(ContaBanco.ativo == True))
    saldo_bancos = result.scalar() or 0
    
    return {
        "clientes": total_clientes,
        "fornecedores": total_fornecedores,
        "produtos": total_produtos,
        "empresas": total_empresas,
        "contas_receber": total_receber,
        "contas_pagar": total_pagar,
        "saldo_bancos": saldo_bancos,
        "saldo_liquido": saldo_bancos + total_receber - total_pagar
    }

# XML Processing (placeholder)
@api_router.post("/xml/processar")
async def processar_xml(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # TODO: Implementar processamento real de XML
    return {"message": "XML processado com sucesso", "filename": file.filename}

# Upseller Integration (simulated)
@api_router.post("/upseller/sync")
async def sync_upseller(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # TODO: Implementar integração real com Upseller
    return {"message": "Sincronização com Upseller simulada"}

@api_router.get("/upseller/produtos")
async def listar_produtos_upseller(current_user: User = Depends(get_current_user)):
    # TODO: Implementar listagem real de produtos do Upseller
    return {"produtos": [], "message": "Integração simulada"}

# Include router
app.include_router(api_router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "ERP System API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)