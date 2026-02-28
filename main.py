from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from uuid import uuid4
from datetime import datetime
import json
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NOTAS_FILE = "notas.json"
USUARIOS_FILE = "usuarios.json"


# =========================
# 📌 MODELOS
# =========================

class Metadato(BaseModel):
    tipo: str = Field(..., example="personal")
    autor: str | None = None
    prioridad: int | None = None


class Nota(BaseModel):
    identificador: str
    usuario_id: str
    descripcion: str
    fecha: datetime
    metadato: Metadato


class NotaCreate(BaseModel):
    usuario_id: str
    descripcion: str
    metadato: Metadato


class Usuario(BaseModel):
    identificador: str
    nombre: str
    email: str
    fecha_registro: datetime


class UsuarioCreate(BaseModel):
    nombre: str
    email: str


# =========================
# 📌 FUNCIONES AUXILIARES
# =========================

def leer_json(filepath):
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump([], f)
    with open(filepath, "r") as f:
        return json.load(f)


def guardar_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4, default=str)


# =========================
# 📌 ENDPOINTS - USUARIOS
# =========================

@app.get("/usuarios", response_model=List[Usuario])
def obtener_usuarios():
    return leer_json(USUARIOS_FILE)


@app.get("/usuarios/{identificador}", response_model=Usuario)
def obtener_usuario(identificador: str):
    usuarios = leer_json(USUARIOS_FILE)
    for usuario in usuarios:
        if usuario["identificador"] == identificador:
            return usuario
    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@app.post("/usuarios", response_model=Usuario)
def crear_usuario(usuario: UsuarioCreate):
    usuarios = leer_json(USUARIOS_FILE)

    # Comprobar email duplicado
    for u in usuarios:
        if u["email"] == usuario.email:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")

    nuevo_usuario = Usuario(
        identificador=str(uuid4()),
        nombre=usuario.nombre,
        email=usuario.email,
        fecha_registro=datetime.now()
    )
    usuarios.append(nuevo_usuario.model_dump())
    guardar_json(USUARIOS_FILE, usuarios)
    return nuevo_usuario


@app.delete("/usuarios/{identificador}")
def eliminar_usuario(identificador: str):
    usuarios = leer_json(USUARIOS_FILE)
    for usuario in usuarios:
        if usuario["identificador"] == identificador:
            usuarios.remove(usuario)
            guardar_json(USUARIOS_FILE, usuarios)

            # Eliminar también las notas del usuario
            notas = leer_json(NOTAS_FILE)
            notas = [n for n in notas if n["usuario_id"] != identificador]
            guardar_json(NOTAS_FILE, notas)

            return {"mensaje": "Usuario y sus notas eliminados"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")


# =========================
# 📌 ENDPOINTS - NOTAS
# =========================

@app.get("/notas", response_model=List[Nota])
def obtener_notas():
    return leer_json(NOTAS_FILE)


@app.get("/notas/{identificador}", response_model=Nota)
def obtener_nota(identificador: str):
    notas = leer_json(NOTAS_FILE)
    for nota in notas:
        if nota["identificador"] == identificador:
            return nota
    raise HTTPException(status_code=404, detail="Nota no encontrada")


@app.get("/usuarios/{usuario_id}/notas", response_model=List[Nota])
def obtener_notas_de_usuario(usuario_id: str):
    # Verificar que el usuario existe
    usuarios = leer_json(USUARIOS_FILE)
    if not any(u["identificador"] == usuario_id for u in usuarios):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    notas = leer_json(NOTAS_FILE)
    return [n for n in notas if n["usuario_id"] == usuario_id]


@app.post("/notas", response_model=Nota)
def crear_nota(nota: NotaCreate):
    # Verificar que el usuario existe
    usuarios = leer_json(USUARIOS_FILE)
    if not any(u["identificador"] == nota.usuario_id for u in usuarios):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    notas = leer_json(NOTAS_FILE)
    nueva_nota = Nota(
        identificador=str(uuid4()),
        usuario_id=nota.usuario_id,
        descripcion=nota.descripcion,
        fecha=datetime.now(),
        metadato=nota.metadato
    )
    notas.append(nueva_nota.model_dump())
    guardar_json(NOTAS_FILE, notas)
    return nueva_nota


@app.delete("/notas/{identificador}")
def eliminar_nota(identificador: str):
    notas = leer_json(NOTAS_FILE)
    for nota in notas:
        if nota["identificador"] == identificador:
            notas.remove(nota)
            guardar_json(NOTAS_FILE, notas)
            return {"mensaje": "Nota eliminada"}
    raise HTTPException(status_code=404, detail="Nota no encontrada")
