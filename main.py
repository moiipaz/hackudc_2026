from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import json
import os
import bcrypt
import httpx
import io
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="API de Notas Personales",
    description="Sistema para gestionar usuarios y sus notas privadas",
    version="5.0.0"
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

os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/webm", "audio/m4a", "audio/x-m4a"}
ALLOWED_PDF_TYPES   = {"application/pdf"}
ALLOWED_TEXT_TYPES  = {"text/plain"}

CATEGORIAS = [
    "youtube", "audios", "recordatorios", "codigo", "personal",
    "trabajo", "estudios", "salud", "compra", "tareas", "ideas",
    "lectura", "peliculas_series", "eventos", "contactos", "recetas",
    "musica", "metas", "tecnologia", "inspiraciones",
    "links", "mapas_mentales", "flashcards", "proyectos", "reflexiones",
    "viajes", "otras"
]

PRIORIDADES = ["low", "medium", "high"]

# =====================================================================
# MODELOS
# =====================================================================

class Metadato(BaseModel):
    tipo: str = Field(default="otras")
    tipo_secundario: Optional[str] = Field(None, description="Segunda categoría (ej: audios + trabajo)")
    autor: Optional[str] = None
    prioridad: Optional[str] = Field(None, description="low | medium | high")

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
    password: str = Field(..., min_length=6)

class Usuario(UsuarioBase):
    identificador: str
    fecha_registro: datetime

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class ClasificarRequest(BaseModel):
    texto: str

# =====================================================================
# CONFIGURACIÓN IA
# =====================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("GEMINI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """Eres un clasificador de notas personales.
Dada una descripción, devuelve SOLO un JSON con este formato exacto (sin texto adicional, sin markdown):
{"tipo": "<categoria>", "confianza": <0.0-1.0>, "motivo": "<texto corto>"}

Categorías disponibles (elige SOLO una):
youtube, audios, recordatorios, codigo, personal, trabajo, estudios, salud,
compra, tareas, ideas, lectura, peliculas_series, eventos, contactos,
recetas, musica, metas, tecnologia, inspiraciones,
links, mapas_mentales, flashcards, proyectos, reflexiones, viajes, otras

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
- Inspiración, cita, frase motivacional, reflexión abstracta → inspiraciones
- Gadgets, software, hardware, tech en general → tecnologia
- Libro, artículo, blog, leer, lectura → lectura
- URL o enlace que no sea youtube → links
- Mapa mental, diagrama visual → mapas_mentales
- Tarjeta de estudio, flashcard, pregunta-respuesta → flashcards
- Proyecto en curso, hoja de ruta, planificación → proyectos
- Reflexión personal, introspección, diario → reflexiones
- Viajes, destino, vuelo, hotel, itinerario, turismo, país, ciudad que visitar → viajes
- Recordatorio con urgencia, alarma, no olvidar → recordatorios
- Ámbito profesional, trabajo, empresa, cliente, proyecto laboral → trabajo
- Universidad, clase, apuntes, examen, estudiar → estudios
- Algo personal/íntimo que no encaja en otras → personal
- Nada encaja bien → otras

Devuelve SOLO el JSON válido, sin backticks ni texto extra."""

RESUMEN_PROMPT = """Eres un asistente que genera resúmenes concisos de notas personales.
Dado el contenido de una nota, devuelve SOLO un JSON con este formato exacto:
{"resumen": "<texto del resumen en 2-4 frases>", "puntos_clave": ["<punto 1>", "<punto 2>", "<punto 3>"]}
Reglas:
- El resumen debe ser claro, útil y en español
- Los puntos clave: máximo 4
- Devuelve SOLO el JSON válido, sin backticks ni texto extra"""

# =====================================================================
# FUNCIONES IA
# =====================================================================

async def classify_note(descripcion: str) -> dict:
    if not OPENAI_API_KEY:
        return {"tipo": "otras", "confianza": 0.0, "motivo": "Sin OPENAI_API_KEY"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": OPENAI_MODEL,
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
        return {"tipo": tipo, "confianza": float(result.get("confianza", 0.8)), "motivo": result.get("motivo", "")}
    except Exception as e:
        return {"tipo": "otras", "confianza": 0.0, "motivo": f"Error: {str(e)[:80]}"}


async def transcribe_audio(file_content: bytes, filename: str) -> str:
    """Transcribe audio usando Whisper de OpenAI."""
    if not OPENAI_API_KEY:
        return ""
    try:
        ext = os.path.splitext(filename)[1].lower() or ".mp3"
        mime_map = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
                    ".m4a": "audio/m4a", ".webm": "audio/webm"}
        mime = mime_map.get(ext, "audio/mpeg")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={"file": (filename, file_content, mime)},
                data={"model": "whisper-1", "language": "es", "response_format": "text"},
            )
            response.raise_for_status()
            return response.text.strip()
    except Exception as e:
        return ""


async def scrape_url(url: str) -> str:
    """Obtiene el texto visible de una URL para clasificarlo."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            html = r.text
        # Extracción simple: quitar tags HTML
        import re
        # Obtener title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        # Quitar scripts, styles
        html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", " ", html, flags=re.IGNORECASE | re.DOTALL)
        # Quitar todos los tags
        text = re.sub(r"<[^>]+>", " ", html)
        # Limpiar espacios
        text = re.sub(r"\s+", " ", text).strip()
        combined = f"{title}. {text[:1500]}" if title else text[:1500]
        return combined
    except Exception:
        return ""


async def generate_summary(descripcion: str, tipo: str) -> dict:
    if not OPENAI_API_KEY:
        return {"resumen": "No disponible: falta OPENAI_API_KEY.", "puntos_clave": []}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": OPENAI_MODEL,
                    "temperature": 0.3,
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": RESUMEN_PROMPT},
                        {"role": "user", "content": f"Categoría: {tipo}\n\nContenido:\n{descripcion}"},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
        result = json.loads(data["choices"][0]["message"]["content"].strip())
        return {"resumen": result.get("resumen", "Sin resumen."), "puntos_clave": result.get("puntos_clave", [])}
    except Exception as e:
        return {"resumen": f"Error: {str(e)[:80]}", "puntos_clave": []}

# =====================================================================
# HELPERS JSON
# =====================================================================

def leer_json(filepath: str) -> list:
    if not os.path.exists(filepath):
        with open(filepath, "w") as f: json.dump([], f)
        return []
    with open(filepath, "r") as f:
        content = f.read().strip()
        if not content: return []
        try: return json.loads(content)
        except json.JSONDecodeError: return []

def guardar_json(filepath: str, data: list) -> None:
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4, default=str)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def extract_pdf_text(content: bytes, max_chars: int = 2000) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        text = " ".join(p.extract_text() or "" for p in reader.pages).strip()
        return text[:max_chars]
    except Exception:
        return ""

def nota_matches_filtro(nota: dict, tipo_filtro: str) -> bool:
    """Comprueba si una nota pertenece a una categoría (tipo principal O secundario)."""
    if not tipo_filtro:
        return True
    tipo_principal  = nota.get("metadato", {}).get("tipo", "")
    tipo_secundario = nota.get("metadato", {}).get("tipo_secundario", "")
    return tipo_filtro in (tipo_principal, tipo_secundario)

# =====================================================================
# ENDPOINTS - USUARIOS
# =====================================================================

@app.get("/usuarios", response_model=List[Usuario], tags=["Usuarios"])
def obtener_usuarios():
    return [{k: v for k, v in u.items() if k != "password_hash"} for u in leer_json(USUARIOS_FILE)]

@app.post("/usuarios/login", tags=["Usuarios"])
def login_usuario(datos: UsuarioLogin):
    for u in leer_json(USUARIOS_FILE):
        if u["email"] == datos.email:
            if verify_password(datos.password, u["password_hash"]):
                return {"mensaje": "Login correcto", "identificador": u["identificador"],
                        "nombre": u["nombre"], "email": u["email"]}
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.post("/usuarios", response_model=Usuario, tags=["Usuarios"], status_code=201)
def crear_usuario(usuario: UsuarioCreate):
    usuarios = leer_json(USUARIOS_FILE)
    if any(u["email"] == usuario.email for u in usuarios):
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")
    nuevo = {
        "identificador": str(uuid4()), "nombre": usuario.nombre,
        "email": usuario.email, "password_hash": hash_password(usuario.password),
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
            guardar_json(NOTAS_FILE, [n for n in leer_json(NOTAS_FILE) if n["usuario_id"] != identificador])
            return {"mensaje": "Usuario y sus notas eliminados"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.get("/usuarios/{usuario_id}/notas", tags=["Notas"])
def obtener_notas_de_usuario(usuario_id: str):
    if not any(u["identificador"] == usuario_id for u in leer_json(USUARIOS_FILE)):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return [n for n in leer_json(NOTAS_FILE) if n["usuario_id"] == usuario_id]

# =====================================================================
# ENDPOINTS - NOTAS
# =====================================================================

@app.get("/notas", tags=["Notas"])
def obtener_notas():
    return leer_json(NOTAS_FILE)

@app.get("/notas/{identificador}", tags=["Notas"])
def obtener_nota(identificador: str):
    for nota in leer_json(NOTAS_FILE):
        if nota["identificador"] == identificador:
            return nota
    raise HTTPException(status_code=404, detail="Nota no encontrada")

@app.post("/notas", tags=["Notas"], status_code=201)
async def crear_nota(nota: NotaCreate):
    """Crea una nota de texto. Si la descripción contiene una URL, la clasifica también como 'links'."""
    if not any(u["identificador"] == nota.usuario_id for u in leer_json(USUARIOS_FILE)):
        raise HTTPException(status_code=404, detail="Usuario no existe")

    descripcion = nota.descripcion
    meta_base   = nota.metadato.model_dump() if nota.metadato else {}

    # Detectar si es un link
    import re
    url_match = re.search(r"https?://\S+", descripcion)
    tipo_secundario = None

    if url_match:
        url = url_match.group(0)
        # Scraping del contenido de la URL
        url_text = await scrape_url(url)
        texto_clasificar = url_text or descripcion
        clasificacion = await classify_note(texto_clasificar)
        tipo_principal = "links"
        # Si la IA dice que es youtube, el principal es youtube (no links)
        if clasificacion["tipo"] == "youtube":
            tipo_principal  = "youtube"
            tipo_secundario = None
        else:
            tipo_secundario = clasificacion["tipo"] if clasificacion["tipo"] != "links" else None
    else:
        clasificacion   = await classify_note(descripcion)
        tipo_principal  = clasificacion["tipo"]
        tipo_secundario = None

    metadato = {
        "tipo":            tipo_principal,
        "tipo_secundario": tipo_secundario,
        "autor":           meta_base.get("autor"),
        "prioridad":       meta_base.get("prioridad"),
        "ia_confianza":    clasificacion["confianza"],
        "ia_motivo":       clasificacion["motivo"],
    }

    notas = leer_json(NOTAS_FILE)
    nueva = {
        "identificador": str(uuid4()), "usuario_id": nota.usuario_id,
        "descripcion": descripcion, "fecha": datetime.now().isoformat(),
        "metadato": metadato, "procesada": False,
    }
    notas.append(nueva)
    guardar_json(NOTAS_FILE, notas)
    return nueva


@app.post("/notas/upload", tags=["Notas"], status_code=201)
async def crear_nota_con_archivo(
    usuario_id:  str = Form(...),
    descripcion: str = Form(default=""),
    autor:       Optional[str] = Form(default=None),
    prioridad:   Optional[str] = Form(default=None),
    archivo:     UploadFile = File(...),
):
    """Crea una nota con archivo adjunto: audio (MP3/WAV/…), PDF o TXT."""
    if not any(u["identificador"] == usuario_id for u in leer_json(USUARIOS_FILE)):
        raise HTTPException(status_code=404, detail="Usuario no existe")

    content_type  = archivo.content_type or ""
    filename_lower = (archivo.filename or "").lower()

    # Normalizar content_type por extensión
    if content_type in ("application/octet-stream", ""):
        ext_map = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
                   ".m4a": "audio/m4a", ".webm": "audio/webm",
                   ".pdf": "application/pdf", ".txt": "text/plain"}
        for ext, mime in ext_map.items():
            if filename_lower.endswith(ext):
                content_type = mime; break

    is_audio = content_type in ALLOWED_AUDIO_TYPES
    is_pdf   = content_type in ALLOWED_PDF_TYPES
    is_txt   = content_type in ALLOWED_TEXT_TYPES or filename_lower.endswith(".txt")

    if not (is_audio or is_pdf or is_txt):
        raise HTTPException(status_code=415,
            detail=f"Tipo no soportado ({content_type}). Solo audio, PDF o TXT.")

    file_content = await archivo.read()

    # Guardar archivo en disco
    ext       = os.path.splitext(archivo.filename or "")[1] or (".mp3" if is_audio else ".pdf" if is_pdf else ".txt")
    file_id   = str(uuid4())
    file_name = f"{file_id}{ext}"
    file_path = os.path.join(UPLOADS_DIR, file_name)
    with open(file_path, "wb") as f:
        f.write(file_content)

    tipo_secundario = None
    transcripcion   = ""

    if is_audio:
        # Transcribir con Whisper
        transcripcion = await transcribe_audio(file_content, archivo.filename or "audio.mp3")
        texto_ia      = transcripcion or descripcion or archivo.filename or "Audio"
        clasificacion = await classify_note(texto_ia)

        tipo_principal  = "audios"
        tipo_secundario = clasificacion["tipo"] if clasificacion["tipo"] != "audios" else None

        # La descripción incluye la transcripción si existe
        desc_final = descripcion or "Nota de voz"
        if transcripcion:
            desc_final = f"{desc_final}\n\n📝 Transcripción:\n{transcripcion}" if descripcion else f"📝 Transcripción:\n{transcripcion}"

    elif is_txt:
        texto = file_content.decode("utf-8", errors="replace")[:3000]
        texto_clasificar = descripcion or texto
        clasificacion    = await classify_note(texto_clasificar)
        tipo_principal   = clasificacion["tipo"]
        desc_final       = descripcion or texto[:500] or archivo.filename or "Archivo de texto"

    else:  # PDF
        pdf_text      = extract_pdf_text(file_content)
        texto_clasif  = descripcion or pdf_text or archivo.filename or "PDF"
        clasificacion = await classify_note(texto_clasif[:1000])
        tipo_principal = clasificacion["tipo"]
        desc_final     = descripcion or archivo.filename or "Documento PDF"

    metadato = {
        "tipo":            tipo_principal,
        "tipo_secundario": tipo_secundario,
        "autor":           autor,
        "prioridad":       prioridad,
        "ia_confianza":    clasificacion["confianza"],
        "ia_motivo":       clasificacion["motivo"],
        "archivo":         file_name,
        "archivo_tipo":    content_type,
        "archivo_nombre_original": archivo.filename,
        **({"transcripcion": transcripcion} if transcripcion else {}),
    }

    notas = leer_json(NOTAS_FILE)
    nueva = {
        "identificador": str(uuid4()), "usuario_id": usuario_id,
        "descripcion": desc_final, "fecha": datetime.now().isoformat(),
        "metadato": metadato, "procesada": False,
    }
    notas.append(nueva)
    guardar_json(NOTAS_FILE, notas)
    return nueva


@app.patch("/notas/{identificador}", tags=["Notas"])
def actualizar_nota(identificador: str, patch: NotaPatch):
    notas = leer_json(NOTAS_FILE)
    for i, n in enumerate(notas):
        if n["identificador"] == identificador:
            if n.get("procesada", False):
                raise HTTPException(status_code=400, detail="La nota ya está procesada")
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
            return {"mensaje": "Nota eliminada"}
    raise HTTPException(status_code=404, detail="Nota no encontrada")


@app.get("/notas/{identificador}/resumen", tags=["Notas"])
async def obtener_resumen_nota(identificador: str):
    for nota in leer_json(NOTAS_FILE):
        if nota["identificador"] == identificador:
            if not nota.get("procesada", False):
                raise HTTPException(status_code=400, detail="Solo se pueden resumir notas procesadas")
            return await generate_summary(nota.get("descripcion", ""), nota.get("metadato", {}).get("tipo", "otras"))
    raise HTTPException(status_code=404, detail="Nota no encontrada")


@app.get("/uploads/{filename}", tags=["Archivos"])
async def servir_archivo(filename: str):
    file_path = os.path.join(UPLOADS_DIR, filename)
    abs_path  = os.path.abspath(file_path)
    if not abs_path.startswith(os.path.abspath(UPLOADS_DIR)):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(abs_path)

# =====================================================================
# ENDPOINTS - UTILIDADES
# =====================================================================

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
            "con_notas": len(set(n["usuario_id"] for n in notas)),
            "sin_notas": len(usuarios) - len(set(n["usuario_id"] for n in notas)),
        }
    }

@app.get("/")
def root():
    return {
        "status":    "ok",
        "docs":      "/docs",
        "version":   "5.0.0",
        "modelo":    OPENAI_MODEL,
        "ia_activa": bool(OPENAI_API_KEY),
        "endpoints": ["/usuarios", "/notas", "/notas/upload", "/estadisticas", "/clasificar", "/categorias"]
    }
