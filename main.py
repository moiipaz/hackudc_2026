from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import json
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="API de Notas Personales",
    description="Sistema para gestionar usuarios y sus notas privadas",
    version="2.0.0"
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
    autor: Optional[str] = Field(None, example="Juan", description="Autor de la nota")
    prioridad: Optional[int] = Field(None, ge=1, le=5, example=3, description="Prioridad 1-5")

class NotaBase(BaseModel):
    usuario_id: str = Field(..., example="uuid-del-usuario")
    descripcion: str = Field(..., example="Comprar leche")
    metadato: Metadato

class Nota(NotaBase):
    identificador: str
    fecha: datetime

class NotaCreate(NotaBase):
    pass

class UsuarioBase(BaseModel):
    nombre: str = Field(..., example="Ana García")
    email: EmailStr = Field(..., example="ana@email.com")

class Usuario(UsuarioBase):
    identificador: str
    fecha_registro: datetime

class UsuarioCreate(UsuarioBase):
    pass

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

# =========================
# 📌 ENDPOINTS - USUARIOS
# =========================

@app.get("/usuarios", response_model=List[Usuario], tags=["Usuarios"])
def obtener_usuarios():
    return leer_json(USUARIOS_FILE)

@app.get("/usuarios/{identificador}", response_model=Usuario, tags=["Usuarios"])
def obtener_usuario(identificador: str):
    for usuario in leer_json(USUARIOS_FILE):
        if usuario["identificador"] == identificador:
            return usuario
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
        "fecha_registro": datetime.now().isoformat()
    }
    usuarios.append(nuevo)
    guardar_json(USUARIOS_FILE, usuarios)
    return nuevo

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
