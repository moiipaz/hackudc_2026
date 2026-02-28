from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import json
import os
import bcrypt
import httpx
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()  # 👈 carga el .env automáticamente

app = FastAPI(
    title="API de Notas Personales",
    description="Sistema para gestionar usuarios y sus notas privadas",
    version="4.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

NOTAS_FILE    = "notas.json"
USUARIOS_FILE = "usuarios.json"

CATEGORIAS = [
    "youtube", "audios", "recordatorios", "codigo", "personal",
    "trabajo", "estudios", "salud", "compra", "tareas", "ideas",
    "lectura", "peliculas_series", "eventos", "contactos", "recetas",
    "musica", "metas", "tecnologia", "inspiraciones", "otras"
]

class Metadato(BaseModel):
    tipo: str = Field(default="otras", description="Categoría de la nota")
    autor: Optional[str] = Field(None, example="Juan")
    prioridad: Optional[int] = Field(None, ge=1, le=5, example=3)

class NotaBase(BaseModel):
    usuario_id: str
    descripcion: str
    metadato: Metadato

class Nota(NotaBase):
    identificador: str
    fecha: datetime

class NotaCreate(BaseModel):
    usuario_id: str
    descripcion: str
    metadato: Optional[Metadato] = None

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

class ClasificarRequest(BaseModel):
    texto: str

GEMINI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

SYSTEM_PROMPT = """Eres un clasificador de notas personales.
Dada una descripción, devuelve SOLO un JSON con este formato exacto (sin texto adicional, sin markdown):
{"tipo": "<categoria>", "confianza": <0.0-1.0>, "motivo": "<texto corto>"}

Categorías disponibles (elige SOLO una):
youtube, audios, recordatorios, codigo, personal, trabajo, estudios, salud,
compra, tareas, ideas, lectura, peliculas_series, eventos, contactos,
recetas, musica, metas, tecnologia, inspiraciones, otras

Reglas de clasificación:
- Link youtube.com o youtu.be → youtube
- Menciona audio, nota de voz, mp3, grabación, podcast → audios
- Lista de compras, supermercado, ingredientes a comprar → compra
- Tarea TO-DO pendiente sin fecha concreta → tareas
- Fecha, cita, evento, reunión, plan concreto con hora/día → eventos
- Código, stacktrace, bug, comando, programación, script → codigo
- Salud, médico, medicamento, síntoma, ejercicio, dieta → salud
- Película, serie, show, episodio, temporada → peliculas_series
- Canción, álbum, artista, playlist, letra → musica
- Contacto, teléfono, email de alguien, dirección → contactos
- Receta de cocina, ingredientes con cantidades, pasos de preparación → recetas
- Meta, objetivo, propósito, plan a largo plazo → metas
- Idea creativa, concepto, brainstorm, ocurrencia → ideas
- Inspiración, cita, frase motivacional, reflexión → inspiraciones
- Gadgets, software, hardware, tech en general → tecnologia
- Libro, artículo, blog, leer, lectura → lectura
- Recordatorio con urgencia, alarma, no olvidar → recordatorios
- Ámbito profesional, trabajo, empresa, cliente, proyecto laboral → trabajo
- Universidad, clase, apuntes, examen, estudiar → estudios
- Algo personal/íntimo que no encaja en otras → personal
- Nada encaja bien → otras

Devuelve SOLO el JSON válido, sin backticks ni texto extra."""

async def classify_note(descripcion: str) -> dict:
    if not GEMINI_API_KEY:
        return {"tipo": "otras", "confianza": 0.0, "motivo": "Sin OPENAI_API_KEY en entorno"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {GEMINI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GEMINI_MODEL,
                    "temperature": 0,
                    "max_tokens": 150,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": descripcion},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        result = json.loads(content)
        tipo = result.get("tipo", "otras").strip().lower()
        if tipo not in CATEGORIAS:
            tipo = "otras"
        return {
            "tipo":      tipo,
            "confianza": float(result.get("confianza", 0.8)),
            "motivo":    result.get("motivo", ""),
        }
    except json.JSONDecodeError as e:
        return {"tipo": "otras", "confianza": 0.0, "motivo": f"JSON inválido: {str(e)[:60]}"}
    except Exception as e:
        return {"tipo": "otras", "confianza": 0.0, "motivo": f"Error: {str(e)[:80]}"}

def leer_json(filepath: str) -> list:
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump([], f)
        return []
    with open(filepath, "r") as f:
        content = f.read().strip()
        if not content:
            return []
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return []

def guardar_json(filepath: str, data: list) -> None:
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4, default=str)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


@app.get("/usuarios", response_model=List[Usuario], tags=["Usuarios"])
def obtener_usuarios():
    return [{k: v for k, v in u.items() if k != "password_hash"} for u in leer_json(USUARIOS_FILE)]

@app.post("/usuarios/login", tags=["Usuarios"])
def login_usuario(datos: UsuarioLogin):
    for u in leer_json(USUARIOS_FILE):
        if u["email"] == datos.email:
            if verify_password(datos.password, u["password_hash"]):
                return {"mensaje": "Login correcto", "identificador": u["identificador"], "nombre": u["nombre"], "email": u["email"]}
            else:
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.post("/usuarios", response_model=Usuario, tags=["Usuarios"], status_code=201)
def crear_usuario(usuario: UsuarioCreate):
    usuarios = leer_json(USUARIOS_FILE)
    for u in usuarios:
        if u["email"] == usuario.email:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")
    nuevo = {
        "identificador":  str(uuid4()),
        "nombre":         usuario.nombre,
        "email":          usuario.email,
        "password_hash":  hash_password(usuario.password),
        "fecha_registro": datetime.now().isoformat()
    }
    usuarios.append(nuevo)
    guardar_json(USUARIOS_FILE, usuarios)
    return {k: v for k, v in nuevo.items() if k != "password_hash"}

@app.get("/usuarios/{identificador}", response_model=Usuario, tags=["Usuarios"])
def obtener_usuario(identificador: str):
    for u in leer_json(USUARIOS_FILE):
        if u["identificador"] == identificador:
            return {k: v for k, v in u.items() if k != "password_hash"}
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

@app.get("/usuarios/{usuario_id}/notas", response_model=List[Nota], tags=["Notas"])
def obtener_notas_de_usuario(usuario_id: str):
    if not any(u["identificador"] == usuario_id for u in leer_json(USUARIOS_FILE)):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return [n for n in leer_json(NOTAS_FILE) if n["usuario_id"] == usuario_id]

@app.get("/notas", response_model=List[Nota], tags=["Notas"])
def obtener_notas():
    return leer_json(NOTAS_FILE)

@app.get("/notas/{identificador}", response_model=Nota, tags=["Notas"])
def obtener_nota(identificador: str):
    for nota in leer_json(NOTAS_FILE):
        if nota["identificador"] == identificador:
            return nota
    raise HTTPException(status_code=404, detail="Nota no encontrada")

@app.post("/notas", response_model=Nota, tags=["Notas"], status_code=201)
async def crear_nota(nota: NotaCreate):
    if not any(u["identificador"] == nota.usuario_id for u in leer_json(USUARIOS_FILE)):
        raise HTTPException(status_code=404, detail="No se puede crear la nota: el usuario no existe")

    clasificacion = await classify_note(nota.descripcion)

    meta_base = nota.metadato.model_dump() if nota.metadato else {}
    metadato = {
        "tipo":         clasificacion["tipo"],
        "autor":        meta_base.get("autor"),
        "prioridad":    meta_base.get("prioridad"),
        "ia_confianza": clasificacion["confianza"],
        "ia_motivo":    clasificacion["motivo"],
    }

    notas = leer_json(NOTAS_FILE)
    nueva = {
        "identificador": str(uuid4()),
        "usuario_id":    nota.usuario_id,
        "descripcion":   nota.descripcion,
        "fecha":         datetime.now().isoformat(),
        "metadato":      metadato,
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

@app.post("/clasificar", tags=["Utilidades"])
async def clasificar_texto(req: ClasificarRequest):
    return await classify_note(req.texto)

@app.get("/categorias", tags=["Utilidades"])
def obtener_categorias():
    return {"categorias": CATEGORIAS}

@app.get("/estadisticas", tags=["Utilidades"])
def obtener_estadisticas():
    usuarios = leer_json(USUARIOS_FILE)
    notas    = leer_json(NOTAS_FILE)
    return {
        "total_usuarios": len(usuarios),
        "total_notas":    len(notas),
        "notas_por_usuario": {
            "con_notas":  len(set(n["usuario_id"] for n in notas)),
            "sin_notas":  len(usuarios) - len(set(n["usuario_id"] for n in notas)),
        }
    }

@app.get("/")
def root():
    return {
        "status":    "ok",
        "docs":      "/docs",
        "modelo":    GEMINI_MODEL,
        "ia_activa": bool(GEMINI_API_KEY),
        "endpoints": ["/usuarios", "/notas", "/estadisticas", "/clasificar", "/categorias"]
    }
