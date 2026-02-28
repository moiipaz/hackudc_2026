INSTALLING


uvicorn main:app --reload

---

## Ejecución local (actualizada para nuevos colaboradores)

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPO>
cd hackudc_2026
```

### 2. Crear y activar entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Sabrás que el entorno está activo cuando veas `(.venv)` al inicio del prompt.

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Variables de entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-2.0-flash
```

| Variable | Obligatoria | Descripción |
|---|---|---|
| `OPENAI_API_KEY` | Sí (para clasificación IA) | Clave de API de OpenAI. Sin ella el backend funciona, pero la clasificación automática devuelve `"otras"` con confianza `0.0`. |
| `GEMINI_MODEL` | No | Modelo a usar en la API. Por defecto: `gemini-2.0-flash`. |

> El archivo `.env` se carga automáticamente gracias a `python-dotenv` en `main.py`.

### 5. Arrancar el backend

```bash
uvicorn main:app --reload
```

El servidor quedará escuchando en **http://127.0.0.1:8000**.

### 6. Arrancar el frontend estático

Abre `index.html` directamente en el navegador, o usa cualquier servidor estático. Por ejemplo con Python:

```bash
python -m http.server 5500
```

Luego accede a **http://localhost:5500**.

> **Importante:** Para desarrollo local, cambia `API_BASE` en `app.js` de la URL de producción a tu servidor local:
> ```js
> const API_BASE = "http://127.0.0.1:8000";
> ```

---

### Comprobaciones rápidas de salud

| Comprobación | Cómo verificar | Respuesta esperada |
|---|---|---|
| Backend activo | `GET http://127.0.0.1:8000/` | JSON con `"status": "ok"` y lista de endpoints |
| Documentación interactiva | Abrir `http://127.0.0.1:8000/docs` en el navegador | Swagger UI de FastAPI |
| Frontend → Backend | Abrir el frontend en el navegador; el indicador de conexión debe mostrar **"✓ Servidor listo"** | Estado verde en la interfaz |

Prueba rápida desde terminal:

```bash
curl http://127.0.0.1:8000/
```

Respuesta esperada:
```json
{
  "status": "ok",
  "docs": "/docs",
  "modelo": "gemini-2.0-flash",
  "ia_activa": true,
  "endpoints": ["/usuarios", "/notas", "/estadisticas", "/clasificar", "/categorias"]
}
```

---

### Troubleshooting

| Problema | Causa probable | Solución |
|---|---|---|
| `'uvicorn' no se reconoce como nombre de un cmdlet` | El entorno virtual no está activado o uvicorn no está instalado | Activa el entorno (`.venv\Scripts\Activate`) y ejecuta `pip install -r requirements.txt` |
| `ERROR: [Errno 10048] address already in use` | El puerto 8000 ya está ocupado | Usa otro puerto: `uvicorn main:app --reload --port 8001` |
| La clasificación devuelve siempre `"otras"` con confianza `0.0` | Falta `OPENAI_API_KEY` en el archivo `.env` | Crea o revisa el archivo `.env` con una clave válida |
| El frontend muestra "✗ Sin conexión" | `API_BASE` en `app.js` apunta a la URL de producción en lugar de `localhost` | Cambia `API_BASE` a `"http://127.0.0.1:8000"` en `app.js` |
| Error de CORS al hacer peticiones desde el frontend | El navegador bloquea peticiones cross-origin | Verifica que el backend esté corriendo y que `API_BASE` coincida con el origen del servidor. El middleware CORS en `main.py` ya permite todos los orígenes (`"*"`) |

---

> **Última verificación de comandos:** 28 de febrero de 2026
