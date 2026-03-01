from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import json
import os
import bcrypt
import httpx
import base64
import io
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
UPLOADS_DIR   = "uploads"

# Crear directorio de uploads si no existe
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/webm", "audio/m4a", "audio/x-m4a"}
ALLOWED_PDF_TYPES   = {"application/pdf"}

CATEGORIAS = [
    "youtube", "audios", "recordatorios", "codigo", "personal",
    "trabajo", "estudios", "salud", "compra", "tareas", "ideas",
    "lectura", "peliculas_series", "eventos", "contactos", "recetas",
    "musica", "metas", "tecnologia", "inspiraciones",
    "links", "mapas_mentales", "flashcards", "proyectos", "reflexiones", "otras"
]

PRIORIDADES = ["low", "medium", "high"]

class Metadato(BaseModel):
    tipo: str = Field(default="otras", description="Categoría de la nota")
    autor: Optional[str] = Field(None, example="Juan")
    prioridad: Optional[str] = Field(None, example="medium", description="low | medium | high")

class NotaBase(BaseModel):
    usuario_id: str
    descripcion: str
    metadato: Metadato

class Nota(NotaBase):
    identificador: str
    fecha: datetime
    procesada: bool = False

class NotaPatch(BaseModel):
    procesada: Optional[bool] = None
    tipo: Optional[str] = None
    prioridad: Optional[str] = None

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
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """Eres un clasificador de notas personales.
Dada una descripción, devuelve SOLO un JSON con este formato exacto (sin texto adicional, sin markdown):
{"tipo": "<categoria>", "confianza": <0.0-1.0>, "motivo": "<texto corto>"}

Categorías disponibles (elige SOLO una):
youtube, audios, recordatorios, codigo, personal, trabajo, estudios, salud,
compra, tareas, ideas, lectura, peliculas_series, eventos, contactos,
recetas, musica, metas, tecnologia, inspiraciones,
links, mapas_mentales, flashcards, proyectos, reflexiones, otras

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
- URL o enlace que no sea youtube → links
- Mapa mental, diagrama, representación visual de conceptos → mapas_mentales
- Tarjeta de estudio, flashcard, pregunta-respuesta, repaso activo → flashcards
- Proyecto en curso, hoja de ruta, planificación de entregables → proyectos
- Reflexión personal, introspección, diario, pensamiento abstracto → reflexiones
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
                "https://api.openai.com/v1/chat/completions",
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
        "procesada":     False,
    }
    notas.append(nueva)
    guardar_json(NOTAS_FILE, notas)
    return nueva


RESUMEN_PROMPT = """Eres un asistente que genera resúmenes concisos de notas personales.
Dado el contenido de una nota, devuelve SOLO un JSON con este formato exacto (sin texto adicional, sin markdown):
{"resumen": "<texto del resumen en 2-4 frases>", "puntos_clave": ["<punto 1>", "<punto 2>", "<punto 3>"]}

Reglas:
- El resumen debe ser claro, útil y en español
- Los puntos clave deben ser los aspectos más importantes (máximo 4)
- Si la nota es muy corta o simple, adapta el resumen a su contenido
- Devuelve SOLO el JSON válido, sin backticks ni texto extra"""

async def generate_summary(descripcion: str, tipo: str) -> dict:
    if not GEMINI_API_KEY:
        return {
            "resumen": "No disponible: falta OPENAI_API_KEY en el entorno.",
            "puntos_clave": []
        }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GEMINI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GEMINI_MODEL,
                    "temperature": 0.3,
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": RESUMEN_PROMPT},
                        {"role": "user", "content": f"Categoría: {tipo}\n\nContenido de la nota:\n{descripcion}"},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
        content_str = data["choices"][0]["message"]["content"].strip()
        result = json.loads(content_str)
        return {
            "resumen": result.get("resumen", "Sin resumen disponible."),
            "puntos_clave": result.get("puntos_clave", [])
        }
    except json.JSONDecodeError as e:
        return {"resumen": f"Error al procesar respuesta IA: {str(e)[:60]}", "puntos_clave": []}
    except Exception as e:
        return {"resumen": f"Error: {str(e)[:80]}", "puntos_clave": []}

@app.get("/notas/{identificador}/resumen", tags=["Notas"])
async def obtener_resumen_nota(identificador: str):
    """Genera un resumen con IA de una nota procesada."""
    for nota in leer_json(NOTAS_FILE):
        if nota["identificador"] == identificador:
            if not nota.get("procesada", False):
                raise HTTPException(status_code=400, detail="Solo se pueden resumir notas procesadas")
            resumen = await generate_summary(
                nota.get("descripcion", ""),
                nota.get("metadato", {}).get("tipo", "otras")
            )
            return resumen
    raise HTTPException(status_code=404, detail="Nota no encontrada")

@app.patch("/notas/{identificador}", response_model=Nota, tags=["Notas"])
def actualizar_nota(identificador: str, patch: NotaPatch):
    """Marca una nota como procesada y opcionalmente cambia su categoría."""
    notas = leer_json(NOTAS_FILE)
    for i, n in enumerate(notas):
        if n["identificador"] == identificador:
            if n.get("procesada", False):
                raise HTTPException(status_code=400, detail="La nota ya está procesada y no puede modificarse")
            if patch.tipo is not None:
                if patch.tipo not in CATEGORIAS:
                    raise HTTPException(status_code=422, detail=f"Categoría inválida: {patch.tipo}")
                notas[i]["metadato"]["tipo"] = patch.tipo
            if patch.prioridad is not None:
                if patch.prioridad not in PRIORIDADES:
                    raise HTTPException(status_code=422, detail=f"Prioridad inválida: {patch.prioridad}")
                notas[i]["metadato"]["prioridad"] = patch.prioridad
            if patch.procesada is not None:
                notas[i]["procesada"] = patch.procesada
            guardar_json(NOTAS_FILE, notas)
            return notas[i]
    raise HTTPException(status_code=404, detail="Nota no encontrada")

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

@app.get("/prioridades", tags=["Utilidades"])
def obtener_prioridades():
    return {"prioridades": PRIORIDADES}

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

def extract_pdf_text(content: bytes, max_chars: int = 2000) -> str:
    """Extrae texto de un PDF usando pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        full_text = " ".join(text_parts).strip()
        # Limitar para no exceder tokens de la IA
        return full_text[:max_chars] if len(full_text) > max_chars else full_text
    except Exception as e:
        return ""

@app.post("/notas/upload", response_model=Nota, tags=["Notas"], status_code=201)
async def crear_nota_con_archivo(
    usuario_id: str = Form(...),
    descripcion: str = Form(default=""),
    autor: Optional[str] = Form(default=None),
    prioridad: Optional[str] = Form(default=None),
    archivo: UploadFile = File(...),
):
    """Crea una nota adjuntando un archivo de audio (mp3, wav, ogg…) o PDF."""
    if not any(u["identificador"] == usuario_id for u in leer_json(USUARIOS_FILE)):
        raise HTTPException(status_code=404, detail="No se puede crear la nota: el usuario no existe")

    content_type = archivo.content_type or ""
    # Normalizar tipos de audio que algunos navegadores envían diferente
    filename_lower = (archivo.filename or "").lower()
    if content_type == "application/octet-stream":
        if filename_lower.endswith(".mp3"):  content_type = "audio/mpeg"
        elif filename_lower.endswith(".wav"): content_type = "audio/wav"
        elif filename_lower.endswith(".ogg"): content_type = "audio/ogg"
        elif filename_lower.endswith(".m4a"): content_type = "audio/m4a"
        elif filename_lower.endswith(".webm"): content_type = "audio/webm"
        elif filename_lower.endswith(".pdf"):  content_type = "application/pdf"

    is_audio = content_type in ALLOWED_AUDIO_TYPES
    is_pdf   = content_type in ALLOWED_PDF_TYPES

    if not is_audio and not is_pdf:
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de archivo no soportado ({content_type}). Solo se aceptan audios y PDFs."
        )

    file_content = await archivo.read()

    # Guardar archivo en disco
    ext = os.path.splitext(archivo.filename or "")[1] or (".pdf" if is_pdf else ".mp3")
    file_id   = str(uuid4())
    file_name = f"{file_id}{ext}"
    file_path = os.path.join(UPLOADS_DIR, file_name)
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Determinar descripción y clasificación
    if is_audio:
        desc_final = descripcion or archivo.filename or "Nota de voz"
        clasificacion = {"tipo": "audios", "confianza": 1.0, "motivo": "Archivo de audio adjunto"}
    else:
        # PDF: extraer texto y clasificar con IA
        pdf_text = extract_pdf_text(file_content)
        texto_clasificar = descripcion or pdf_text or archivo.filename or "Documento PDF"
        desc_final = descripcion or archivo.filename or "Documento PDF"
        if pdf_text:
            # Clasificar usando el texto extraído del PDF
            clasificacion = await classify_note(pdf_text[:1000])
        else:
            clasificacion = await classify_note(texto_clasificar)

    metadato = {
        "tipo":         clasificacion["tipo"],
        "autor":        autor,
        "prioridad":    prioridad,
        "ia_confianza": clasificacion["confianza"],
        "ia_motivo":    clasificacion["motivo"],
        "archivo":      file_name,
        "archivo_tipo": content_type,
        "archivo_nombre_original": archivo.filename,
    }

    notas = leer_json(NOTAS_FILE)
    nueva = {
        "identificador": str(uuid4()),
        "usuario_id":    usuario_id,
        "descripcion":   desc_final,
        "fecha":         datetime.now().isoformat(),
        "metadato":      metadato,
        "procesada":     False,
    }
    notas.append(nueva)
    guardar_json(NOTAS_FILE, notas)
    return nueva

@app.get("/uploads/{filename}", tags=["Archivos"])
async def servir_archivo(filename: str):
    """Sirve un archivo subido (audio o PDF)."""
    from fastapi.responses import FileResponse
    file_path = os.path.join(UPLOADS_DIR, filename)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    # Seguridad: evitar path traversal
    abs_path    = os.path.abspath(file_path)
    abs_uploads = os.path.abspath(UPLOADS_DIR)
    if not abs_path.startswith(abs_uploads):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return FileResponse(abs_path)


    return {
        "status":    "ok",
        "docs":      "/docs",
        "modelo":    GEMINI_MODEL,
        "ia_activa": bool(GEMINI_API_KEY),
        "endpoints": ["/usuarios", "/notas", "/estadisticas", "/clasificar", "/categorias"]
    }
