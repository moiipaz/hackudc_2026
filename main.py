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

# Configurar CORS para tu frontend en GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://moiipaz.github.io",
        "http://moiipaz.github.io",
        "http://localhost:5500",  # Para desarrollo local
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos de base de datos
NOTAS_FILE = "notas.json"
USUARIOS_FILE = "usuarios.json"

# =========================
# 📌 MODELOS
# =========================

class Metadato(BaseModel):
    """Metadatos de una nota"""
    tipo: str = Field(..., example="personal", description="Tipo: personal, trabajo, estudio")
    autor: Optional[str] = Field(None, example="Juan", description="Autor de la nota")
    prioridad: Optional[int] = Field(None, ge=1, le=5, example=3, description="Prioridad 1-5")

class NotaBase(BaseModel):
    """Base para crear una nota"""
    usuario_id: str = Field(..., example="uuid-del-usuario", description="ID del dueño de la nota")
    descripcion: str = Field(..., example="Comprar leche", description="Contenido de la nota")
    metadato: Metadato

class Nota(NotaBase):
    """Nota completa"""
    identificador: str = Field(..., example="uuid-unico", description="ID único de la nota")
    fecha: datetime = Field(..., description="Fecha de creación")

class NotaCreate(NotaBase):
    """Datos para crear una nota (sin ID ni fecha)"""
    pass

class UsuarioBase(BaseModel):
    """Base para crear un usuario"""
    nombre: str = Field(..., example="Ana García", description="Nombre completo")
    email: EmailStr = Field(..., example="ana@email.com", description="Email único")

class Usuario(UsuarioBase):
    """Usuario completo"""
    identificador: str = Field(..., example="uuid-unico", description="ID único del usuario")
    fecha_registro: datetime = Field(..., description="Fecha de registro")

class UsuarioCreate(UsuarioBase):
    """Datos para crear un usuario (sin ID ni fecha)"""
    pass

# =========================
# 📌 FUNCIONES AUXILIARES
# =========================

def leer_json(filepath: str) -> list:
    """Lee un archivo JSON y devuelve su contenido como lista"""
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump([], f)
    with open(filepath, "r") as f:
        return json.load(f)

def guardar_json(filepath: str, data: list) -> None:
    """Guarda datos en un archivo JSON"""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4, default=str)

# =========================
# 📌 ENDPOINTS - USUARIOS
# =========================

@app.get(
    "/usuarios",
    response_model=List[Usuario],
    summary="Obtener todos los usuarios",
    tags=["Usuarios"]
)
def obtener_usuarios():
    """Devuelve la lista completa de usuarios registrados"""
    return leer_json(USUARIOS_FILE)

@app.get(
    "/usuarios/{identificador}",
    response_model=Usuario,
    summary="Obtener un usuario por ID",
    tags=["Usuarios"]
)
def obtener_usuario(identificador: str):
    """Devuelve los datos de un usuario específico"""
    usuarios = leer_json(USUARIOS_FILE)
    for usuario in usuarios:
        if usuario["identificador"] == identificador:
            return usuario
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.post(
    "/usuarios",
    response_model=Usuario,
    summary="Crear un nuevo usuario",
    tags=["Usuarios"],
    status_code=201
)
def crear_usuario(usuario: UsuarioCreate):
    """Registra un nuevo usuario con email único"""
    usuarios = leer_json(USUARIOS_FILE)
    
    # Verificar email duplicado
    for u in usuarios:
        if u["email"] == usuario.email:
            raise HTTPException(
                status_code=400, 
                detail="Ya existe un usuario con ese email"
            )
    
    # Crear nuevo usuario
    nuevo_usuario = {
        "identificador": str(uuid4()),
        "nombre": usuario.nombre,
        "email": usuario.email,
        "fecha_registro": datetime.now().isoformat()
    }
    
    usuarios.append(nuevo_usuario)
    guardar_json(USUARIOS_FILE, usuarios)
    return nuevo_usuario

@app.delete(
    "/usuarios/{identificador}",
    summary="Eliminar un usuario",
    tags=["Usuarios"]
)
def eliminar_usuario(identificador: str):
    """Elimina un usuario y todas sus notas asociadas"""
    usuarios = leer_json(USUARIOS_FILE)
    
    for i, usuario in enumerate(usuarios):
        if usuario["identificador"] == identificador:
            # Eliminar usuario
            usuarios.pop(i)
            guardar_json(USUARIOS_FILE, usuarios)
            
            # Eliminar todas sus notas
            notas = leer_json(NOTAS_FILE)
            notas = [n for n in notas if n["usuario_id"] != identificador]
            guardar_json(NOTAS_FILE, notas)
            
            return {"mensaje": "Usuario y sus notas eliminados correctamente"}
    
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

# =========================
# 📌 ENDPOINTS - NOTAS
# =========================

@app.get(
    "/notas",
    response_model=List[Nota],
    summary="Obtener todas las notas",
    tags=["Notas"]
)
def obtener_notas():
    """Devuelve todas las notas del sistema"""
    return leer_json(NOTAS_FILE)

@app.get(
    "/notas/{identificador}",
    response_model=Nota,
    summary="Obtener una nota por ID",
    tags=["Notas"]
)
def obtener_nota(identificador: str):
    """Devuelve una nota específica por su ID"""
    notas = leer_json(NOTAS_FILE)
    for nota in notas:
        if nota["identificador"] == identificador:
            return nota
    raise HTTPException(status_code=404, detail="Nota no encontrada")

@app.get(
    "/usuarios/{usuario_id}/notas",
    response_model=List[Nota],
    summary="Obtener notas de un usuario",
    tags=["Notas"]
)
def obtener_notas_de_usuario(usuario_id: str):
    """Devuelve todas las notas de un usuario específico (privacidad)"""
    # Verificar que el usuario existe
    usuarios = leer_json(USUARIOS_FILE)
    if not any(u["identificador"] == usuario_id for u in usuarios):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Devolver solo sus notas
    notas = leer_json(NOTAS_FILE)
    return [n for n in notas if n["usuario_id"] == usuario_id]

@app.post(
    "/notas",
    response_model=Nota,
    summary="Crear una nueva nota",
    tags=["Notas"],
    status_code=201
)
def crear_nota(nota: NotaCreate):
    """Crea una nueva nota asociada a un usuario"""
    # Verificar que el usuario existe
    usuarios = leer_json(USUARIOS_FILE)
    if not any(u["identificador"] == nota.usuario_id for u in usuarios):
        raise HTTPException(
            status_code=404, 
            detail="No se puede crear la nota: el usuario no existe"
        )
    
    # Crear la nota
    notas = leer_json(NOTAS_FILE)
    nueva_nota = {
        "identificador": str(uuid4()),
        "usuario_id": nota.usuario_id,
        "descripcion": nota.descripcion,
        "fecha": datetime.now().isoformat(),
        "metadato": nota.metadato.model_dump()
    }
    
    notas.append(nueva_nota)
    guardar_json(NOTAS_FILE, notas)
    return nueva_nota

@app.delete(
    "/notas/{identificador}",
    summary="Eliminar una nota",
    tags=["Notas"]
)
def eliminar_nota(identificador: str):
    """Elimina una nota específica"""
    notas = leer_json(NOTAS_FILE)
    
    for i, nota in enumerate(notas):
        if nota["identificador"] == identificador:
            notas.pop(i)
            guardar_json(NOTAS_FILE, notas)
            return {"mensaje": "Nota eliminada correctamente"}
    
    raise HTTPException(status_code=404, detail="Nota no encontrada")

# =========================
# 📌 ENDPOINT - ESTADÍSTICAS
# =========================

@app.get(
    "/estadisticas",
    summary="Estadísticas del sistema",
    tags=["Utilidades"]
)
def obtener_estadisticas():
    """Muestra estadísticas básicas del sistema"""
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
