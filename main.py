from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import json
import os
import bcrypt
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="API de Notas Personales",
    description="Sistema para gestionar usuarios y sus notas privadas",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

NOTAS_FILE = "notas.json"
USUARIOS_FILE = "usuarios.json"

# =========================
# 📌 MODELOS
# =========================

class Metadato(BaseModel):
    tipo: str = Field(..., example="personal", description="Tipo: personal, trabajo, estudio")
    autor: Optional[str] = Field(None, example="Juan")
    prioridad: Optional[int] = Field(None, ge=1, le=5, example=3)

class NotaBase(BaseModel):
    usuario_id: str
    descripcion: str
    metadato: Metadato

class Nota(NotaBase):
    identificador: str
    fecha: datetime

class NotaCreate(NotaBase):
    pass

class UsuarioBase(BaseModel):
    nombre: str = Field(..., example="Ana García")
    email: EmailStr = Field(..., example="ana@email.com")

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., example="micontraseña123", min_length=6)

class Usuario(UsuarioBase):
    identificador: str
    fecha_registro: datetime

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

# =========================
# 📌 FUNCIONES AUXILIARES
# =========================

def leer_json(filepath: str) -> list:
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump([], f)
    with open(filepath, "r") as f:
        return json.load(f)

def guardar_json(filepath: str, data: list) -> None:
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4, default=str)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# =========================
# 📌 ENDPOINTS - USUARIOS
# =========================

@app.get("/usuarios", response_model=List[Usuario], tags=["Usuarios"])
def obtener_usuarios():
    return [
        {k: v for k, v in u.items() if k != "password_hash"}
        for u in leer_json(USUARIOS_FILE)
    ]

@app.get("/usuarios/{identificador}", response_model=Usuario, tags=["Usuarios"])
def obtener_usuario(identificador: str):
    for u in leer_json(USUARIOS_FILE):
        if u["identificador"] == identificador:
            return {k: v for k, v in u.items() if k != "password_hash"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.post("/usuarios", response_model=Usuario, tags=["Usuarios"], status_code=201)
def crear_usuario(usuario: UsuarioCreate):
    usuarios = leer_json(USUARIOS_FILE)
    for u in usuarios:
        if u["email"] == usuario.email:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")

    nuevo = {
        "identificador": str(uuid4()),
        "nombre": usuario.nombre,
        "email": usuario.email,
        "password_hash": hash_password(usuario.password),
        "fecha_registro": datetime.now().isoformat()
    }
    usuarios.append(nuevo)
    guardar_json(USUARIOS_FILE, usuarios)
    return {k: v for k, v in nuevo.items() if k != "password_hash"}

@app.post("/usuarios/login", tags=["Usuarios"])
def login_usuario(datos: UsuarioLogin):
    for u in leer_json(USUARIOS_FILE):
        if u["email"] == datos.email:
            if verify_password(datos.password, u["password_hash"]):
                return {
                    "mensaje": "Login correcto",
                    "identificador": u["identificador"],
                    "nombre": u["nombre"],
                    "email": u["email"]
                }
            else:
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.delete("/usuarios/{identificador}", tags=["Usuarios"])
def eliminar_usuario(identificador: str):
    usuarios = leer_json(USUARIOS_FILE)
    for i, u in enumerate(usuarios):
        if u["identificador"] == identificador:
            usuarios.pop(i)
            guardar_json(USUARIOS_FILE, usuarios)
            notas = [n for n in leer_json(NOTAS_FILE) if n["usuario_id"] != identificador]
            guardar_json(NOTAS_FILE, notas)
            return {"mensaje": "Usuario y sus notas eliminados correctamente"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

# =========================
# 📌 ENDPOINTS - NOTAS
# =========================

@app.get("/notas", response_model=List[Nota], tags=["Notas"])
def obtener_notas():
    return leer_json(NOTAS_FILE)

@app.get("/notas/{identificador}", response_model=Nota, tags=["Notas"])
def obtener_nota(identificador: str):
    for nota in leer_json(NOTAS_FILE):
        if nota["identificador"] == identificador:
            return nota
    raise HTTPException(status_code=404, detail="Nota no encontrada")

@app.get("/usuarios/{usuario_id}/notas", response_model=List[Nota], tags=["Notas"])
def obtener_notas_de_usuario(usuario_id: str):
    if not any(u["identificador"] == usuario_id for u in leer_json(USUARIOS_FILE)):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return [n for n in leer_json(NOTAS_FILE) if n["usuario_id"] == usuario_id]

@app.post("/notas", response_model=Nota, tags=["Notas"], status_code=201)
def crear_nota(nota: NotaCreate):
    if not any(u["identificador"] == nota.usuario_id for u in leer_json(USUARIOS_FILE)):
        raise HTTPException(status_code=404, detail="No se puede crear la nota: el usuario no existe")

    notas = leer_json(NOTAS_FILE)
    nueva = {
        "identificador": str(uuid4()),
        "usuario_id": nota.usuario_id,
        "descripcion": nota.descripcion,
        "fecha": datetime.now().isoformat(),
        "metadato": nota.metadato.model_dump()
    }
    notas.append(nueva)
    guardar_json(NOTAS_FILE, notas)
    return nueva

@app.delete("/notas/{identificador}", tags=["Notas"])
def eliminar_nota(identificador: str):
    notas = leer_json(NOTAS_FILE)
    for i, n in enumerate(notas):
        if n["identificador"] == identificador:
            notas.pop(i)
            guardar_json(NOTAS_FILE, notas)
            return {"mensaje": "Nota eliminada correctamente"}
    raise HTTPException(status_code=404, detail="Nota no encontrada")

# =========================
# 📌 ENDPOINTS - EXTRA
# =========================

@app.get("/estadisticas", tags=["Utilidades"])
def obtener_estadisticas():
    usuarios = leer_json(USUARIOS_FILE)
    notas = leer_json(NOTAS_FILE)
    return {
        "total_usuarios": len(usuarios),
        "total_notas": len(notas),
        "notas_por_usuario": {
            "con_notas": len(set(n["usuario_id"] for n in notas)),
            "sin_notas": len(usuarios) - len(set(n["usuario_id"] for n in notas))
        }
    }

@app.get("/")
def root():
    return {
        "status": "ok",
        "docs": "/docs",
        "endpoints": ["/usuarios", "/notas", "/estadisticas"]
    }
