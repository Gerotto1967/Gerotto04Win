from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import jwt
from passlib.context import CryptContext

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
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class Cliente(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    email: str
    telefone: str
    endereco: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ClienteCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    endereco: str

class Produto(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    descricao: str
    preco: float
    categoria: str
    estoque: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProdutoCreate(BaseModel):
    nome: str
    descricao: str
    preco: float
    categoria: str
    estoque: int

class Financeiro(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: str  # "receita" ou "despesa"
    descricao: str
    valor: float
    categoria: str
    data: datetime = Field(default_factory=datetime.utcnow)
    cliente_id: Optional[str] = None

class FinanceiroCreate(BaseModel):
    tipo: str
    descricao: str
    valor: float
    categoria: str
    cliente_id: Optional[str] = None

# Auth functions
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

# Auth routes
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # Simple auth - admin/admin123
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

# Cliente routes
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
    await db.clientes.update_one({"id": cliente_id}, {"$set": cliente.dict()})
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

# Produto routes
@api_router.post("/produtos", response_model=Produto)
async def create_produto(produto: ProdutoCreate, current_user: str = Depends(get_current_user)):
    produto_dict = produto.dict()
    produto_obj = Produto(**produto_dict)
    await db.produtos.insert_one(produto_obj.dict())
    return produto_obj

@api_router.get("/produtos", response_model=List[Produto])
async def get_produtos(current_user: str = Depends(get_current_user)):
    produtos = await db.produtos.find().to_list(1000)
    return [Produto(**produto) for produto in produtos]

@api_router.get("/produtos/{produto_id}", response_model=Produto)
async def get_produto(produto_id: str, current_user: str = Depends(get_current_user)):
    produto = await db.produtos.find_one({"id": produto_id})
    if produto:
        return Produto(**produto)
    raise HTTPException(status_code=404, detail="Produto não encontrado")

@api_router.put("/produtos/{produto_id}", response_model=Produto)
async def update_produto(produto_id: str, produto: ProdutoCreate, current_user: str = Depends(get_current_user)):
    await db.produtos.update_one({"id": produto_id}, {"$set": produto.dict()})
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

# Financeiro routes
@api_router.post("/financeiro", response_model=Financeiro)
async def create_financeiro(financeiro: FinanceiroCreate, current_user: str = Depends(get_current_user)):
    financeiro_dict = financeiro.dict()
    financeiro_obj = Financeiro(**financeiro_dict)
    await db.financeiro.insert_one(financeiro_obj.dict())
    return financeiro_obj

@api_router.get("/financeiro", response_model=List[Financeiro])
async def get_financeiro(current_user: str = Depends(get_current_user)):
    financeiro = await db.financeiro.find().to_list(1000)
    return [Financeiro(**item) for item in financeiro]

@api_router.get("/financeiro/historico")
async def get_historico_financeiro(current_user: str = Depends(get_current_user)):
    # Histórico com resumos mensais
    pipeline = [
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$data"},
                    "month": {"$month": "$data"},
                    "tipo": "$tipo"
                },
                "total": {"$sum": "$valor"},
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id.year": -1, "_id.month": -1}
        }
    ]
    
    historico = await db.financeiro.aggregate(pipeline).to_list(100)
    return {"historico": historico}

@api_router.get("/financeiro/relatorios")
async def get_relatorios_financeiros(current_user: str = Depends(get_current_user)):
    # Relatórios e estatísticas
    total_receitas = await db.financeiro.aggregate([
        {"$match": {"tipo": "receita"}},
        {"$group": {"_id": None, "total": {"$sum": "$valor"}}}
    ]).to_list(1)
    
    total_despesas = await db.financeiro.aggregate([
        {"$match": {"tipo": "despesa"}},
        {"$group": {"_id": None, "total": {"$sum": "$valor"}}}
    ]).to_list(1)
    
    receitas = total_receitas[0]["total"] if total_receitas else 0
    despesas = total_despesas[0]["total"] if total_despesas else 0
    
    return {
        "receitas": receitas,
        "despesas": despesas,
        "saldo": receitas - despesas
    }

# Dashboard
@api_router.get("/dashboard")
async def get_dashboard(current_user: str = Depends(get_current_user)):
    # Contadores gerais
    total_clientes = await db.clientes.count_documents({})
    total_produtos = await db.produtos.count_documents({})
    
    # Financeiro do mês atual
    from datetime import datetime, date
    today = date.today()
    start_month = datetime(today.year, today.month, 1)
    
    receitas_mes = await db.financeiro.aggregate([
        {"$match": {"tipo": "receita", "data": {"$gte": start_month}}},
        {"$group": {"_id": None, "total": {"$sum": "$valor"}}}
    ]).to_list(1)
    
    despesas_mes = await db.financeiro.aggregate([
        {"$match": {"tipo": "despesa", "data": {"$gte": start_month}}},
        {"$group": {"_id": None, "total": {"$sum": "$valor"}}}
    ]).to_list(1)
    
    receitas = receitas_mes[0]["total"] if receitas_mes else 0
    despesas = despesas_mes[0]["total"] if despesas_mes else 0
    
    return {
        "total_clientes": total_clientes,
        "total_produtos": total_produtos,
        "receitas_mes": receitas,
        "despesas_mes": despesas,
        "saldo_mes": receitas - despesas
    }

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "ERP System API", "version": "1.0"}

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