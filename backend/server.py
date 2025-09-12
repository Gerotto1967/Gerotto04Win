from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
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

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create the main app without a prefix
app = FastAPI(title="ERP System", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# CNPJs configurados
CNPJS_CONFIG = {
    "11111111000101": {"nome": "EMPRESA ABC LTDA", "uf": "SP"},
    "22222222000102": {"nome": "EMPRESA XYZ LTDA", "uf": "SP"}, 
    "33333333000103": {"nome": "EMPRESA 123 LTDA", "uf": "SP"},
    "44444444000104": {"nome": "EMPRESA DEF LTDA", "uf": "RJ"},
    "55555555000105": {"nome": "EMPRESA GHI LTDA", "uf": "MG"}
}

# ============= MODELS =============

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# Cliente Models
class Cliente(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    email: str
    telefone: str
    endereco: str
    cidade: str = ""
    uf: str = ""
    cep: str = ""
    cpf_cnpj: str = ""
    observacoes: str = ""
    ativo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ClienteCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    endereco: str
    cidade: str = ""
    uf: str = ""
    cep: str = ""
    cpf_cnpj: str = ""
    observacoes: str = ""
    ativo: bool = True

# Fornecedor Models
class Fornecedor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    cnpj: str
    email: str = ""
    telefone: str = ""
    endereco: str = ""
    cidade: str = ""
    uf: str = ""
    cep: str = ""
    contato: str = ""
    condicoes_pagamento: str = ""
    observacoes: str = ""
    ativo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FornecedorCreate(BaseModel):
    nome: str
    cnpj: str
    email: str = ""
    telefone: str = ""
    endereco: str = ""
    cidade: str = ""
    uf: str = ""
    cep: str = ""
    contato: str = ""
    condicoes_pagamento: str = ""
    observacoes: str = ""
    ativo: bool = True

# Produto Models
class EstoqueCNPJ(BaseModel):
    cnpj: str
    quantidade: int
    estoque_minimo: int = 0
    estoque_maximo: int = 0

class Produto(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sku: str
    ean: str = ""
    nome: str
    descricao: str = ""
    categoria: str = ""
    marca: str = ""
    unidade: str = "UN"
    valor_compra: float = 0.0
    custo_medio: float = 0.0
    preco_venda: float = 0.0
    margem_percentual: float = 0.0
    estoque_total: int = 0
    estoques_cnpj: List[EstoqueCNPJ] = []
    fornecedor_id: str = ""
    imagem_url: str = ""
    ativo: bool = True
    fora_estado: bool = False  # Para regra ICMS
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProdutoCreate(BaseModel):
    sku: str
    ean: str = ""
    nome: str
    descricao: str = ""
    categoria: str = ""
    marca: str = ""
    unidade: str = "UN"
    valor_compra: float = 0.0
    preco_venda: float = 0.0
    fornecedor_id: str = ""
    fora_estado: bool = False

# Movimentação Estoque
class MovimentacaoEstoque(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    produto_id: str
    cnpj: str
    tipo: str  # COMPRA, VENDA, AJUSTE, TRANSFERENCIA, DEVOLUCAO
    documento: str = ""
    descricao: str
    quantidade_entrada: int = 0
    quantidade_saida: int = 0
    valor_unitario: float = 0.0
    valor_total: float = 0.0
    usuario: str = ""
    data: datetime = Field(default_factory=datetime.utcnow)

# Financeiro Models  
class ContaBanco(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    tipo: str  # BANCO, CAIXA, POUPANCA, CARTAO
    banco: str = ""
    agencia: str = ""
    conta: str = ""
    saldo_atual: float = 0.0
    ativo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ContaBancoCreate(BaseModel):
    nome: str
    tipo: str
    banco: str = ""
    agencia: str = ""
    conta: str = ""
    saldo_atual: float = 0.0

class ContaFinanceira(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: str  # PAGAR, RECEBER
    descricao: str
    valor: float
    valor_pago: float = 0.0
    data_vencimento: date
    data_pagamento: Optional[date] = None
    status: str = "PENDENTE"  # PENDENTE, PAGO, VENCIDO
    categoria: str = ""
    observacoes: str = ""
    conta_banco_id: str = ""
    fornecedor_id: str = ""
    cliente_id: str = ""
    documento: str = ""
    cnpj: str = ""
    parcela: int = 1
    total_parcelas: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ContaFinanceiraCreate(BaseModel):
    tipo: str
    descricao: str
    valor: float
    data_vencimento: date
    categoria: str = ""
    observacoes: str = ""
    fornecedor_id: str = ""
    cliente_id: str = ""
    documento: str = ""
    cnpj: str = ""
    parcelas: int = 1

# XML Processing
class XMLProcessamento(BaseModel):
    arquivo_nome: str
    fornecedor_cnpj: str = ""
    fornecedor_nome: str = ""
    numero_nf: str = ""
    valor_total: float = 0.0
    valor_produtos: float = 0.0
    valor_icms: float = 0.0
    itens: List[Dict] = []
    status: str = "PENDENTE"  # PENDENTE, PROCESSADO, ERRO
    cnpj_destino: str = ""
    data_processamento: datetime = Field(default_factory=datetime.utcnow)

# ============= HELPER FUNCTIONS =============

async def calcular_custo_medio(produto_id: str, novo_custo: float, quantidade: int):
    """Calcula custo médio baseado no histórico de compras"""
    produto = await db.produtos.find_one({"id": produto_id})
    if not produto:
        return novo_custo
    
    estoque_atual = produto.get("estoque_total", 0)
    custo_atual = produto.get("custo_medio", 0.0)
    
    if estoque_atual == 0:
        return novo_custo
    
    valor_estoque_atual = estoque_atual * custo_atual
    valor_nova_compra = quantidade * novo_custo
    total_quantidade = estoque_atual + quantidade
    
    if total_quantidade == 0:
        return novo_custo
    
    custo_medio = (valor_estoque_atual + valor_nova_compra) / total_quantidade
    return round(custo_medio, 4)

async def atualizar_estoque_produto(produto_id: str, cnpj: str, quantidade: int, operacao: str = "ENTRADA"):
    """Atualiza estoque do produto por CNPJ"""
    produto = await db.produtos.find_one({"id": produto_id})
    if not produto:
        return False
    
    estoques_cnpj = produto.get("estoques_cnpj", [])
    estoque_encontrado = False
    
    for estoque in estoques_cnpj:
        if estoque["cnpj"] == cnpj:
            if operacao == "ENTRADA":
                estoque["quantidade"] += quantidade
            else:  # SAIDA
                estoque["quantidade"] -= quantidade
            estoque_encontrado = True
            break
    
    if not estoque_encontrado:
        novo_estoque = {
            "cnpj": cnpj,
            "quantidade": quantidade if operacao == "ENTRADA" else -quantidade,
            "estoque_minimo": 0,
            "estoque_maximo": 0
        }
        estoques_cnpj.append(novo_estoque)
    
    # Recalcular estoque total
    estoque_total = sum(e["quantidade"] for e in estoques_cnpj)
    
    await db.produtos.update_one(
        {"id": produto_id},
        {
            "$set": {
                "estoques_cnpj": estoques_cnpj,
                "estoque_total": estoque_total,
                "updated_at": datetime.utcnow()
            }
        }
    )
    return True

async def criar_movimentacao_estoque(produto_id: str, cnpj: str, tipo: str, quantidade_entrada: int, quantidade_saida: int, documento: str, descricao: str, valor_unitario: float, usuario: str = "sistema"):
    """Cria registro de movimentação de estoque"""
    movimentacao = MovimentacaoEstoque(
        produto_id=produto_id,
        cnpj=cnpj,
        tipo=tipo,
        documento=documento,
        descricao=descricao,
        quantidade_entrada=quantidade_entrada,
        quantidade_saida=quantidade_saida,
        valor_unitario=valor_unitario,
        valor_total=(quantidade_entrada + quantidade_saida) * valor_unitario,
        usuario=usuario
    )
    
    await db.movimentacoes_estoque.insert_one(movimentacao.dict())
    return movimentacao

# ============= AUTH FUNCTIONS =============

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============= AUTH ROUTES =============

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    if request.username == "admin" and request.password == "admin123":
        access_token = create_access_token(data={"sub": request.username})
        return LoginResponse(
            access_token=access_token,
            user={"username": "admin", "role": "administrator"}
        )
    else:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

@api_router.get("/auth/me")
async def get_me(current_user: str = Depends(get_current_user)):
    return {"username": current_user, "role": "administrator"}

# ============= CLIENTE ROUTES =============

@api_router.post("/clientes", response_model=Cliente)
async def create_cliente(cliente: ClienteCreate, current_user: str = Depends(get_current_user)):
    cliente_dict = cliente.dict()
    cliente_obj = Cliente(**cliente_dict)
    await db.clientes.insert_one(cliente_obj.dict())
    return cliente_obj

@api_router.get("/clientes", response_model=List[Cliente])
async def get_clientes(current_user: str = Depends(get_current_user)):
    clientes = await db.clientes.find().to_list(1000)
    return [Cliente(**cliente) for cliente in clientes]

@api_router.get("/clientes/{cliente_id}", response_model=Cliente)
async def get_cliente(cliente_id: str, current_user: str = Depends(get_current_user)):
    cliente = await db.clientes.find_one({"id": cliente_id})
    if cliente:
        return Cliente(**cliente)
    raise HTTPException(status_code=404, detail="Cliente não encontrado")

@api_router.put("/clientes/{cliente_id}", response_model=Cliente)
async def update_cliente(cliente_id: str, cliente: ClienteCreate, current_user: str = Depends(get_current_user)):
    update_data = cliente.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.clientes.update_one({"id": cliente_id}, {"$set": update_data})
    updated_cliente = await db.clientes.find_one({"id": cliente_id})
    if updated_cliente:
        return Cliente(**updated_cliente)
    raise HTTPException(status_code=404, detail="Cliente não encontrado")

@api_router.delete("/clientes/{cliente_id}")
async def delete_cliente(cliente_id: str, current_user: str = Depends(get_current_user)):
    result = await db.clientes.delete_one({"id": cliente_id})
    if result.deleted_count:
        return {"message": "Cliente deletado com sucesso"}
    raise HTTPException(status_code=404, detail="Cliente não encontrado")

# ============= FORNECEDOR ROUTES =============

@api_router.post("/fornecedores", response_model=Fornecedor)
async def create_fornecedor(fornecedor: FornecedorCreate, current_user: str = Depends(get_current_user)):
    fornecedor_dict = fornecedor.dict()
    fornecedor_obj = Fornecedor(**fornecedor_dict)
    await db.fornecedores.insert_one(fornecedor_obj.dict())
    return fornecedor_obj

@api_router.get("/fornecedores", response_model=List[Fornecedor])
async def get_fornecedores(current_user: str = Depends(get_current_user)):
    fornecedores = await db.fornecedores.find().to_list(1000)
    return [Fornecedor(**fornecedor) for fornecedor in fornecedores]

@api_router.get("/fornecedores/{fornecedor_id}", response_model=Fornecedor)
async def get_fornecedor(fornecedor_id: str, current_user: str = Depends(get_current_user)):
    fornecedor = await db.fornecedores.find_one({"id": fornecedor_id})
    if fornecedor:
        return Fornecedor(**fornecedor)
    raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

@api_router.put("/fornecedores/{fornecedor_id}", response_model=Fornecedor)
async def update_fornecedor(fornecedor_id: str, fornecedor: FornecedorCreate, current_user: str = Depends(get_current_user)):
    update_data = fornecedor.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.fornecedores.update_one({"id": fornecedor_id}, {"$set": update_data})
    updated_fornecedor = await db.fornecedores.find_one({"id": fornecedor_id})
    if updated_fornecedor:
        return Fornecedor(**updated_fornecedor)
    raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

@api_router.delete("/fornecedores/{fornecedor_id}")
async def delete_fornecedor(fornecedor_id: str, current_user: str = Depends(get_current_user)):
    result = await db.fornecedores.delete_one({"id": fornecedor_id})
    if result.deleted_count:
        return {"message": "Fornecedor deletado com sucesso"}
    raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

# ============= PRODUTO ROUTES =============

@api_router.post("/produtos", response_model=Produto)
async def create_produto(produto: ProdutoCreate, current_user: str = Depends(get_current_user)):
    produto_dict = produto.dict()
    
    # Inicializar estoques por CNPJ
    estoques_cnpj = []
    for cnpj in CNPJS_CONFIG.keys():
        estoques_cnpj.append({
            "cnpj": cnpj,
            "quantidade": 0,
            "estoque_minimo": 0,
            "estoque_maximo": 0
        })
    
    produto_dict["estoques_cnpj"] = estoques_cnpj
    produto_dict["custo_medio"] = produto_dict["valor_compra"]
    produto_dict["estoque_total"] = 0
    
    # Calcular margem
    if produto_dict["valor_compra"] > 0:
        produto_dict["margem_percentual"] = round(((produto_dict["preco_venda"] - produto_dict["valor_compra"]) / produto_dict["valor_compra"]) * 100, 2)
    
    produto_obj = Produto(**produto_dict)
    await db.produtos.insert_one(produto_obj.dict())
    return produto_obj

@api_router.get("/produtos")
async def get_produtos(current_user: str = Depends(get_current_user)):
    produtos = await db.produtos.find().to_list(1000)
    return produtos

@api_router.get("/produtos/{produto_id}", response_model=Produto)
async def get_produto(produto_id: str, current_user: str = Depends(get_current_user)):
    produto = await db.produtos.find_one({"id": produto_id})
    if produto:
        return Produto(**produto)
    raise HTTPException(status_code=404, detail="Produto não encontrado")

@api_router.put("/produtos/{produto_id}", response_model=Produto)
async def update_produto(produto_id: str, produto_data: dict, current_user: str = Depends(get_current_user)):
    produto_data["updated_at"] = datetime.utcnow()
    
    # Recalcular margem se necessário
    if "valor_compra" in produto_data and "preco_venda" in produto_data:
        if produto_data["valor_compra"] > 0:
            produto_data["margem_percentual"] = round(((produto_data["preco_venda"] - produto_data["valor_compra"]) / produto_data["valor_compra"]) * 100, 2)
    
    await db.produtos.update_one({"id": produto_id}, {"$set": produto_data})
    updated_produto = await db.produtos.find_one({"id": produto_id})
    if updated_produto:
        return Produto(**updated_produto)
    raise HTTPException(status_code=404, detail="Produto não encontrado")

@api_router.delete("/produtos/{produto_id}")
async def delete_produto(produto_id: str, current_user: str = Depends(get_current_user)):
    result = await db.produtos.delete_one({"id": produto_id})
    if result.deleted_count:
        return {"message": "Produto deletado com sucesso"}
    raise HTTPException(status_code=404, detail="Produto não encontrado")

# ============= ESTOQUE ROUTES =============

@api_router.get("/produtos/{produto_id}/movimentacoes")
async def get_movimentacoes_produto(produto_id: str, cnpj: str = None, current_user: str = Depends(get_current_user)):
    """Busca movimentações de estoque de um produto"""
    filter_query = {"produto_id": produto_id}
    if cnpj:
        filter_query["cnpj"] = cnpj
    
    movimentacoes = await db.movimentacoes_estoque.find(filter_query).sort("data", -1).to_list(1000)
    
    # Calcular totais
    total_entradas = sum(m.get("quantidade_entrada", 0) for m in movimentacoes)
    total_saidas = sum(m.get("quantidade_saida", 0) for m in movimentacoes)
    
    return {
        "movimentacoes": movimentacoes,
        "resumo": {
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "saldo": total_entradas - total_saidas
        }
    }

@api_router.post("/estoque/ajuste")
async def ajustar_estoque(produto_id: str, cnpj: str, quantidade: int, motivo: str, current_user: str = Depends(get_current_user)):
    """Ajusta estoque manualmente"""
    produto = await db.produtos.find_one({"id": produto_id})
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Atualizar estoque
    if quantidade > 0:
        await atualizar_estoque_produto(produto_id, cnpj, abs(quantidade), "ENTRADA")
        await criar_movimentacao_estoque(produto_id, cnpj, "AJUSTE", abs(quantidade), 0, "", f"Ajuste: {motivo}", produto.get("custo_medio", 0), current_user)
    else:
        await atualizar_estoque_produto(produto_id, cnpj, abs(quantidade), "SAIDA")
        await criar_movimentacao_estoque(produto_id, cnpj, "AJUSTE", 0, abs(quantidade), "", f"Ajuste: {motivo}", produto.get("custo_medio", 0), current_user)
    
    return {"message": "Estoque ajustado com sucesso"}

# Continua na próxima parte devido ao limite de tamanho...