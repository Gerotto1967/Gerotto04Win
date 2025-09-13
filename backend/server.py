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

# ============= FINANCEIRO ROUTES =============

@api_router.post("/contas-banco", response_model=ContaBanco)
async def create_conta_banco(conta: ContaBancoCreate, current_user: str = Depends(get_current_user)):
    conta_dict = conta.dict()
    conta_obj = ContaBanco(**conta_dict)
    await db.contas_banco.insert_one(conta_obj.dict())
    return conta_obj

@api_router.get("/contas-banco", response_model=List[ContaBanco])
async def get_contas_banco(current_user: str = Depends(get_current_user)):
    contas = await db.contas_banco.find().to_list(100)
    return [ContaBanco(**conta) for conta in contas]

@api_router.post("/financeiro", response_model=ContaFinanceira)
async def create_conta_financeira(conta: ContaFinanceiraCreate, current_user: str = Depends(get_current_user)):
    conta_dict = conta.dict()
    
    # Se tem parcelas, criar múltiplas contas
    if conta_dict.get("parcelas", 1) > 1:
        contas_criadas = []
        valor_parcela = conta_dict["valor"] / conta_dict["parcelas"]
        
        for i in range(conta_dict["parcelas"]):
            conta_parcela = conta_dict.copy()
            conta_parcela["valor"] = round(valor_parcela, 2)
            conta_parcela["parcela"] = i + 1
            conta_parcela["total_parcelas"] = conta_dict["parcelas"]
            conta_parcela["descricao"] = f"{conta_dict['descricao']} - Parcela {i+1}/{conta_dict['parcelas']}"
            
            # Ajustar data de vencimento
            from dateutil.relativedelta import relativedelta
            data_base = datetime.strptime(str(conta_dict["data_vencimento"]), "%Y-%m-%d").date()
            conta_parcela["data_vencimento"] = data_base + relativedelta(months=i)
            
            del conta_parcela["parcelas"]
            conta_obj = ContaFinanceira(**conta_parcela)
            await db.contas_financeiras.insert_one(conta_obj.dict())
            contas_criadas.append(conta_obj)
        
        return contas_criadas[0]  # Retorna a primeira parcela
    else:
        del conta_dict["parcelas"]
        conta_obj = ContaFinanceira(**conta_dict)
        await db.contas_financeiras.insert_one(conta_obj.dict())
        return conta_obj

@api_router.get("/financeiro")
async def get_contas_financeiras(tipo: str = None, status: str = None, current_user: str = Depends(get_current_user)):
    filter_query = {}
    if tipo:
        filter_query["tipo"] = tipo
    if status:
        filter_query["status"] = status
    
    contas = await db.contas_financeiras.find(filter_query).sort("data_vencimento", 1).to_list(1000)
    return contas

@api_router.post("/financeiro/{conta_id}/pagar")
async def pagar_conta(conta_id: str, conta_banco_id: str, valor_pago: float, data_pagamento: str, current_user: str = Depends(get_current_user)):
    """Baixa uma conta como paga"""
    conta = await db.contas_financeiras.find_one({"id": conta_id})
    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    
    # Atualizar conta
    update_data = {
        "valor_pago": valor_pago,
        "data_pagamento": datetime.strptime(data_pagamento, "%Y-%m-%d").date(),
        "status": "PAGO",
        "conta_banco_id": conta_banco_id
    }
    
    await db.contas_financeiras.update_one({"id": conta_id}, {"$set": update_data})
    
    # Atualizar saldo da conta bancária
    conta_banco = await db.contas_banco.find_one({"id": conta_banco_id})
    if conta_banco:
        if conta["tipo"] == "PAGAR":
            novo_saldo = conta_banco["saldo_atual"] - valor_pago
        else:  # RECEBER
            novo_saldo = conta_banco["saldo_atual"] + valor_pago
        
        await db.contas_banco.update_one({"id": conta_banco_id}, {"$set": {"saldo_atual": novo_saldo}})
    
    return {"message": "Conta baixada com sucesso"}

@api_router.get("/financeiro/relatorios")
async def get_relatorios_financeiros(current_user: str = Depends(get_current_user)):
    """Relatórios financeiros gerais"""
    # Contas a pagar
    total_pagar = await db.contas_financeiras.aggregate([
        {"$match": {"tipo": "PAGAR", "status": "PENDENTE"}},
        {"$group": {"_id": None, "total": {"$sum": "$valor"}}}
    ]).to_list(1)
    
    # Contas a receber
    total_receber = await db.contas_financeiras.aggregate([
        {"$match": {"tipo": "RECEBER", "status": "PENDENTE"}},
        {"$group": {"_id": None, "total": {"$sum": "$valor"}}}
    ]).to_list(1)
    
    # Saldo total das contas bancárias
    saldo_bancos = await db.contas_banco.aggregate([
        {"$match": {"ativo": True}},
        {"$group": {"_id": None, "total": {"$sum": "$saldo_atual"}}}
    ]).to_list(1)
    
    pagar = total_pagar[0]["total"] if total_pagar else 0
    receber = total_receber[0]["total"] if total_receber else 0
    saldo = saldo_bancos[0]["total"] if saldo_bancos else 0
    
    return {
        "contas_pagar": pagar,
        "contas_receber": receber,
        "saldo_bancos": saldo,
        "patrimonio_liquido": saldo + receber - pagar
    }

# ============= XML PROCESSING ROUTES =============

@api_router.post("/xml/upload")
async def upload_xml(file: UploadFile = File(...), cnpj_destino: str = Form(...), current_user: str = Depends(get_current_user)):
    """Upload e processamento de XML de compra"""
    if not file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser XML")
    
    # Ler conteúdo do arquivo
    content = await file.read()
    
    try:
        # Parse do XML
        root = ET.fromstring(content)
        
        # Extrair dados básicos da NF
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}  # Namespace padrão NFe
        
        # Dados do emitente (fornecedor)
        emit = root.find('.//nfe:emit', ns) or root.find('.//emit')
        fornecedor_cnpj = emit.find('.//CNPJ').text if emit is not None and emit.find('.//CNPJ') is not None else ""
        fornecedor_nome = emit.find('.//xNome').text if emit is not None and emit.find('.//xNome') is not None else ""
        
        # Dados da NF
        ide = root.find('.//nfe:ide', ns) or root.find('.//ide')
        numero_nf = ide.find('.//nNF').text if ide is not None and ide.find('.//nNF') is not None else ""
        
        # Totais
        total = root.find('.//nfe:total//nfe:ICMSTot', ns) or root.find('.//total//ICMSTot')
        valor_total = float(total.find('.//vNF').text) if total is not None and total.find('.//vNF') is not None else 0.0
        valor_produtos = float(total.find('.//vProd').text) if total is not None and total.find('.//vProd') is not None else 0.0
        valor_icms = float(total.find('.//vICMS').text) if total is not None and total.find('.//vICMS') is not None else 0.0
        
        # Itens da NF
        itens = []
        for det in root.findall('.//nfe:det', ns) or root.findall('.//det'):
            prod = det.find('.//nfe:prod', ns) or det.find('.//prod')
            if prod is not None:
                item = {
                    "codigo": prod.find('.//cProd').text if prod.find('.//cProd') is not None else "",
                    "descricao": prod.find('.//xProd').text if prod.find('.//xProd') is not None else "",
                    "ean": prod.find('.//cEAN').text if prod.find('.//cEAN') is not None else "",
                    "quantidade": float(prod.find('.//qCom').text) if prod.find('.//qCom') is not None else 0.0,
                    "valor_unitario": float(prod.find('.//vUnCom').text) if prod.find('.//vUnCom') is not None else 0.0,
                    "valor_total": float(prod.find('.//vProd').text) if prod.find('.//vProd') is not None else 0.0
                }
                itens.append(item)
        
        # Criar registro de processamento
        xml_proc = XMLProcessamento(
            arquivo_nome=file.filename,
            fornecedor_cnpj=fornecedor_cnpj,
            fornecedor_nome=fornecedor_nome,
            numero_nf=numero_nf,
            valor_total=valor_total,
            valor_produtos=valor_produtos,
            valor_icms=valor_icms,
            itens=itens,
            cnpj_destino=cnpj_destino
        )
        
        await db.xml_processamentos.insert_one(xml_proc.dict())
        
        return {
            "message": "XML processado com sucesso",
            "dados": xml_proc.dict()
        }
        
    except ET.ParseError:
        raise HTTPException(status_code=400, detail="Arquivo XML inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar XML: {str(e)}")

@api_router.post("/xml/{xml_id}/processar")
async def processar_xml_compra(xml_id: str, current_user: str = Depends(get_current_user)):
    """Processa XML confirmando entrada no estoque e financeiro"""
    xml_proc = await db.xml_processamentos.find_one({"_id": xml_id})  # Usar _id do MongoDB
    if not xml_proc:
        raise HTTPException(status_code=404, detail="XML não encontrado")
    
    if xml_proc["status"] == "PROCESSADO":
        raise HTTPException(status_code=400, detail="XML já foi processado")
    
    try:
        # Buscar ou criar fornecedor
        fornecedor = await db.fornecedores.find_one({"cnpj": xml_proc["fornecedor_cnpj"]})
        if not fornecedor:
            # Criar fornecedor automaticamente
            novo_fornecedor = Fornecedor(
                nome=xml_proc["fornecedor_nome"],
                cnpj=xml_proc["fornecedor_cnpj"]
            )
            await db.fornecedores.insert_one(novo_fornecedor.dict())
            fornecedor_id = novo_fornecedor.id
        else:
            fornecedor_id = fornecedor["id"]
        
        # Processar cada item
        for item in xml_proc["itens"]:
            # Buscar produto pelo código/EAN
            produto = await db.produtos.find_one({
                "$or": [
                    {"sku": item["codigo"]},
                    {"ean": item["ean"]}
                ]
            })
            
            if produto:
                produto_id = produto["id"]
                valor_compra = item["valor_unitario"]
                
                # Aplicar regra ICMS diferencial se produto de fora do estado
                if produto.get("fora_estado", False):
                    valor_compra *= 1.06  # Adiciona 6%
                
                # Calcular novo custo médio
                novo_custo_medio = await calcular_custo_medio(produto_id, valor_compra, int(item["quantidade"]))
                
                # Atualizar produto
                await db.produtos.update_one(
                    {"id": produto_id},
                    {
                        "$set": {
                            "valor_compra": valor_compra,
                            "custo_medio": novo_custo_medio,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                # Atualizar estoque
                await atualizar_estoque_produto(produto_id, xml_proc["cnpj_destino"], int(item["quantidade"]), "ENTRADA")
                
                # Criar movimentação de estoque
                await criar_movimentacao_estoque(
                    produto_id=produto_id,
                    cnpj=xml_proc["cnpj_destino"],
                    tipo="COMPRA",
                    quantidade_entrada=int(item["quantidade"]),
                    quantidade_saida=0,
                    documento=f"NF {xml_proc['numero_nf']}",
                    descricao=f"Compra - {item['descricao']}",
                    valor_unitario=valor_compra,
                    usuario=current_user
                )
        
        # Criar conta a pagar
        conta_pagar = ContaFinanceira(
            tipo="PAGAR",
            descricao=f"NF {xml_proc['numero_nf']} - {xml_proc['fornecedor_nome']}",
            valor=xml_proc["valor_total"],
            data_vencimento=date.today(),  # Configurar conforme necessário
            categoria="COMPRAS",
            fornecedor_id=fornecedor_id,
            documento=xml_proc["numero_nf"],
            cnpj=xml_proc["cnpj_destino"]
        )
        
        await db.contas_financeiras.insert_one(conta_pagar.dict())
        
        # Marcar XML como processado
        await db.xml_processamentos.update_one(
            {"_id": xml_id},
            {"$set": {"status": "PROCESSADO"}}
        )
        
        return {"message": "XML processado e integrado com sucesso"}
        
    except Exception as e:
        await db.xml_processamentos.update_one(
            {"_id": xml_id},
            {"$set": {"status": "ERRO"}}
        )
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")

# ============= MARKETPLACE/UPSELLER - EXPORTAÇÃO DE DADOS =============

@api_router.get("/marketplace/exportar-estoque")
async def exportar_estoque_marketplace(formato: str = "json"):
    """Exporta estoque consolidado para marketplaces (CSV, JSON, XML)"""
    produtos = await db.produtos.find({"ativo": True}).to_list(1000)
    
    dados_exportacao = []
    for produto in produtos:
        dados_exportacao.append({
            "sku": produto["sku"],
            "nome": produto["nome"],
            "descricao": produto.get("descricao", ""),
            "marca": produto.get("marca", ""),
            "categoria": produto.get("categoria", ""),
            "ean": produto.get("ean", ""),
            "estoque_disponivel": produto["estoque_total"],
            "custo_medio": round(produto["custo_medio"], 2),
            "preco_venda": round(produto["preco_venda"], 2),
            "margem_percentual": round(produto.get("margem_percentual", 0), 2),
            "ativo": produto["ativo"],
            "atualizado_em": produto["updated_at"].isoformat()
        })
    
    if formato == "csv":
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=dados_exportacao[0].keys() if dados_exportacao else [])
        writer.writeheader()
        writer.writerows(dados_exportacao)
        
        return {
            "formato": "csv",
            "dados": output.getvalue(),
            "total_produtos": len(dados_exportacao)
        }
    
    return {
        "formato": "json", 
        "produtos": dados_exportacao,
        "total_produtos": len(dados_exportacao),
        "exportado_em": datetime.utcnow().isoformat()
    }

@api_router.post("/marketplace/processar-venda")
async def processar_venda_marketplace(venda_data: dict):
    """Processa vendas vindas de marketplaces (entrada manual de dados)"""
    try:
        # Extrair dados da venda
        cnpj_vendedor = venda_data.get("cnpj_vendedor")
        marketplace = venda_data.get("marketplace", "UPSELLER")
        produtos_vendidos = venda_data.get("produtos", [])
        valor_bruto = venda_data.get("valor_bruto", 0)
        valor_liquido = venda_data.get("valor_liquido", 0)
        taxas = venda_data.get("taxas", 0)
        pedido_id = venda_data.get("pedido_id", "")
        data_venda = venda_data.get("data_venda", date.today().isoformat())
        
        if not cnpj_vendedor or not produtos_vendidos:
            raise HTTPException(status_code=400, detail="CNPJ vendedor e produtos são obrigatórios")
        
        lucro_total = 0
        produtos_processados = 0
        
        # Processar cada produto vendido
        for item in produtos_vendidos:
            sku = item.get("sku")
            quantidade = item.get("quantidade", 0)
            preco_unitario = item.get("preco_unitario", 0)
            
            if not sku or quantidade <= 0:
                continue
            
            # Buscar produto
            produto = await db.produtos.find_one({"sku": sku})
            if produto:
                produto_id = produto["id"]
                custo_medio = produto["custo_medio"]
                
                # Verificar se há estoque suficiente no CNPJ
                estoque_cnpj = next((e for e in produto.get("estoques_cnpj", []) if e["cnpj"] == cnpj_vendedor), None)
                if not estoque_cnpj or estoque_cnpj["quantidade"] < quantidade:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Estoque insuficiente para produto {sku} no CNPJ {cnpj_vendedor}"
                    )
                
                # Calcular lucro do item
                lucro_item = (preco_unitario - custo_medio) * quantidade
                lucro_total += lucro_item
                
                # Baixar estoque (do CNPJ que vendeu)
                await atualizar_estoque_produto(produto_id, cnpj_vendedor, quantidade, "SAIDA")
                
                # Criar movimentação de estoque
                await criar_movimentacao_estoque(
                    produto_id=produto_id,
                    cnpj=cnpj_vendedor,
                    tipo="VENDA",
                    quantidade_entrada=0,
                    quantidade_saida=quantidade,
                    documento=pedido_id,
                    descricao=f"Venda {marketplace} - {produto['nome']}",
                    valor_unitario=preco_unitario,
                    usuario="marketplace"
                )
                
                produtos_processados += 1
        
        # Criar conta a receber (valor líquido)
        if valor_liquido > 0:
            conta_receber = ContaFinanceira(
                tipo="RECEBER",
                descricao=f"Venda {marketplace} - Pedido {pedido_id}",
                valor=valor_liquido,
                data_vencimento=datetime.strptime(data_venda, "%Y-%m-%d").date(),
                categoria=f"VENDAS_{marketplace}",
                documento=pedido_id,
                cnpj=cnpj_vendedor
            )
            
            await db.contas_financeiras.insert_one(conta_receber.dict())
        
        # Registrar taxas como despesa se houver
        if taxas > 0:
            taxa_despesa = ContaFinanceira(
                tipo="PAGAR",
                descricao=f"Taxas {marketplace} - Pedido {pedido_id}",
                valor=taxas,
                data_vencimento=datetime.strptime(data_venda, "%Y-%m-%d").date(),
                categoria=f"TAXAS_{marketplace}",
                documento=pedido_id,
                cnpj=cnpj_vendedor,
                status="PAGO"  # Taxas já são descontadas
            )
            
            await db.contas_financeiras.insert_one(taxa_despesa.dict())
        
        return {
            "message": "Venda processada com sucesso",
            "marketplace": marketplace,
            "pedido_id": pedido_id,
            "lucro_bruto": round(lucro_total, 2),
            "valor_liquido": valor_liquido,
            "produtos_processados": produtos_processados
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar venda: {str(e)}")

@api_router.get("/marketplace/relatorio-lucros")
async def relatorio_lucros_marketplace(marketplace: str = None, periodo_dias: int = 30):
    """Relatório de lucros por marketplace"""
    data_inicio = datetime.utcnow() - relativedelta(days=periodo_dias)
    
    filter_query = {
        "tipo": "VENDA",
        "data": {"$gte": data_inicio}
    }
    
    if marketplace:
        filter_query["descricao"] = {"$regex": marketplace, "$options": "i"}
    
    # Buscar movimentações de venda
    movimentacoes = await db.movimentacoes_estoque.find(filter_query).to_list(1000)
    
    lucro_total = 0
    vendas_por_marketplace = {}
    
    for mov in movimentacoes:
        # Extrair marketplace da descrição
        desc = mov.get("descricao", "")
        if "UPSELLER" in desc:
            marketplace_nome = "UPSELLER"
        elif "MERCADO LIVRE" in desc:
            marketplace_nome = "MERCADO_LIVRE"
        else:
            marketplace_nome = "OUTROS"
        
        if marketplace_nome not in vendas_por_marketplace:
            vendas_por_marketplace[marketplace_nome] = {
                "vendas": 0,
                "quantidade": 0,
                "valor_vendido": 0,
                "lucro_estimado": 0
            }
        
        # Buscar produto para calcular lucro
        produto = await db.produtos.find_one({"id": mov["produto_id"]})
        if produto:
            custo_medio = produto.get("custo_medio", 0)
            lucro_item = (mov["valor_unitario"] - custo_medio) * mov["quantidade_saida"]
            
            vendas_por_marketplace[marketplace_nome]["vendas"] += 1
            vendas_por_marketplace[marketplace_nome]["quantidade"] += mov["quantidade_saida"]
            vendas_por_marketplace[marketplace_nome]["valor_vendido"] += mov["valor_total"]
            vendas_por_marketplace[marketplace_nome]["lucro_estimado"] += lucro_item
            
            lucro_total += lucro_item
    
    return {
        "periodo_dias": periodo_dias,
        "lucro_total": round(lucro_total, 2),
        "vendas_por_marketplace": vendas_por_marketplace,
        "gerado_em": datetime.utcnow().isoformat()
    }

# ============= DASHBOARD ROUTES =============

@api_router.get("/dashboard")
async def get_dashboard(current_user: str = Depends(get_current_user)):
    # Contadores gerais
    total_clientes = await db.clientes.count_documents({})
    total_fornecedores = await db.fornecedores.count_documents({})
    total_produtos = await db.produtos.count_documents({})
    
    # Valor do estoque (custo médio)
    pipeline_estoque = [
        {"$project": {"valor_estoque": {"$multiply": ["$estoque_total", "$custo_medio"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$valor_estoque"}}}
    ]
    valor_estoque = await db.produtos.aggregate(pipeline_estoque).to_list(1)
    estoque_valor = valor_estoque[0]["total"] if valor_estoque else 0
    
    # Financeiro
    relatorio_financeiro = await get_relatorios_financeiros(current_user)
    
    # Vendas do mês
    today = date.today()
    start_month = datetime(today.year, today.month, 1)
    
    vendas_mes = await db.movimentacoes_estoque.aggregate([
        {"$match": {"tipo": "VENDA", "data": {"$gte": start_month}}},
        {"$group": {"_id": None, "total_vendas": {"$sum": "$quantidade_saida"}, "valor_vendas": {"$sum": "$valor_total"}}}
    ]).to_list(1)
    
    vendas_mes_data = vendas_mes[0] if vendas_mes else {"total_vendas": 0, "valor_vendas": 0}
    
    return {
        "total_clientes": total_clientes,
        "total_fornecedores": total_fornecedores,
        "total_produtos": total_produtos,
        "valor_estoque": round(estoque_valor, 2),
        "vendas_mes": vendas_mes_data["total_vendas"],
        "valor_vendas_mes": round(vendas_mes_data["valor_vendas"], 2),
        "financeiro": relatorio_financeiro
    }

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "ERP System API - Fase 1", "version": "1.0.0", "features": ["Clientes", "Fornecedores", "Produtos", "Estoque Multi-CNPJ", "Financeiro", "XML Processing", "Upseller Integration"]}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()