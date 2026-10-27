"""
API ALVO (sistema sob teste) — FastAPI.

Simula um serviço de e-commerce com autenticacao, usuarios e pedidos.
As regras de negocio reais estao implementadas aqui para que a QA Crew
possa valida-las de forma autonoma.

Regras de negocio implementadas:
  RN01 - Criar usuario exige nome e email valido; email duplicado => 409.
  RN02 - Idade minima para cadastro e 18 anos; menor => 422.
  RN03 - Login valido retorna token; credenciais invalidas => 401.
  RN04 - Endpoints de pedidos exigem token (Bearer); sem token => 401.
  RN05 - Pedido exige ao menos 1 item e valor total > 0; senao => 422.
  RN06 - Desconto so e aplicado para pedidos acima de R$ 100; senao desconto = 0.
  RN07 - Consultar pedido inexistente => 404.
"""
from __future__ import annotations

import os
import uuid
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title="E-commerce Target API", version="1.0.0")

# Modo de demonstracao de falhas: quando BUGGY=1, a API viola RN02 e RN06
# de proposito, para demonstrar ao vivo que a QA Crew DETECTA nao conformidades.
BUGGY = os.getenv("BUGGY", "0") == "1"

# Armazenamento em memoria (dados mock)
_users: dict[str, dict] = {}
_tokens: dict[str, str] = {}
_orders: dict[str, dict] = {}


class UserIn(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    age: int
    password: str = Field(min_length=6)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class OrderItem(BaseModel):
    sku: str
    qty: int = Field(gt=0)
    price: float = Field(gt=0)


class OrderIn(BaseModel):
    items: list[OrderItem]


def _auth(authorization: Optional[str] = Header(default=None)) -> str:
    # RN04 - endpoints de pedido exigem token Bearer valido
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou invalido")
    token = authorization.split(" ", 1)[1]
    if token not in _tokens:
        raise HTTPException(status_code=401, detail="Token nao reconhecido")
    return _tokens[token]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/users", status_code=201)
def create_user(user: UserIn):
    # RN02 - idade minima 18 (em modo BUGGY, a validacao e omitida de proposito)
    if not BUGGY and user.age < 18:
        raise HTTPException(status_code=422, detail="Idade minima para cadastro e 18 anos")
    # RN01 - email unico
    for u in _users.values():
        if u["email"] == user.email:
            raise HTTPException(status_code=409, detail="Email ja cadastrado")
    uid = str(uuid.uuid4())
    _users[uid] = {"id": uid, "name": user.name, "email": user.email,
                   "age": user.age, "password": user.password}
    return {"id": uid, "name": user.name, "email": user.email, "age": user.age}


@app.post("/login")
def login(body: LoginIn):
    # RN03 - login valido retorna token
    for u in _users.values():
        if u["email"] == body.email and u["password"] == body.password:
            token = str(uuid.uuid4())
            _tokens[token] = u["id"]
            return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Credenciais invalidas")


@app.post("/orders", status_code=201)
def create_order(order: OrderIn, user_id: str = Depends(_auth)):
    # RN05 - ao menos 1 item e total > 0
    if not order.items:
        raise HTTPException(status_code=422, detail="Pedido exige ao menos 1 item")
    total = sum(i.qty * i.price for i in order.items)
    if total <= 0:
        raise HTTPException(status_code=422, detail="Valor total deve ser maior que zero")
    # RN06 - desconto de 10% apenas acima de R$ 100
    # (em modo BUGGY, nunca aplica desconto, violando a regra de proposito)
    discount = 0.0 if BUGGY else (round(total * 0.10, 2) if total > 100 else 0.0)
    final = round(total - discount, 2)
    oid = str(uuid.uuid4())
    _orders[oid] = {"id": oid, "user_id": user_id, "total": round(total, 2),
                    "discount": discount, "final": final}
    return _orders[oid]


@app.get("/orders/{order_id}")
def get_order(order_id: str, user_id: str = Depends(_auth)):
    # RN07 - pedido inexistente => 404
    if order_id not in _orders:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    return _orders[order_id]
