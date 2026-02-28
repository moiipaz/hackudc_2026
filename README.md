# API de Notas Personales

Sistema para gestionar usuarios y sus notas privadas con clasificación automática por IA.

---

## Ejecución local

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

### 4. Configurar el archivo `.env`

Para que la clasificación automática de notas funcione, necesitas crear un archivo `.env` en la raíz del proyecto con tu clave de API de OpenAI:

```env
OPENAI_API_KEY = tu-api-key
```

> **Sin este archivo el backend arranca igualmente**, pero todas las notas se clasificarán como `"otras"` con confianza `0.0`.
>
> El archivo `.env` se carga automáticamente gracias a `python-dotenv`. **No subas este archivo a GitHub** — ya está incluido en `.gitignore`.

### 5. Arrancar backend y frontend

Necesitas **dos terminales** abiertas simultáneamente:

**Terminal 1 — Backend (puerto 8000):**
```bash
uvicorn main:app --reload
```

**Terminal 2 — Frontend (puerto 5500):**
```bash
python -m http.server 5500
```

### 6. Abrir la aplicación

Abre **http://localhost:5500** en el navegador.

---

### Comprobaciones rápidas

| Comprobación | Cómo verificar | Respuesta esperada |
|---|---|---|
| Backend activo | `GET http://127.0.0.1:8000/` | JSON con `"status": "ok"` |
| Documentación interactiva | Abrir `http://127.0.0.1:8000/docs` | Swagger UI de FastAPI |
| Frontend conectado | Abrir `http://localhost:5500` | Indicador **"✓ Servidor listo"** en verde |

---

### Troubleshooting

| Problema | Solución |
|---|---|
| `'uvicorn' no se reconoce` | Activa el entorno virtual y ejecuta `pip install -r requirements.txt` |
| `address already in use` | Usa otro puerto: `uvicorn main:app --reload --port 8001` |
| Clasificación devuelve siempre `"otras"` | Revisa que el archivo `.env` tenga una `OPENAI_API_KEY` válida |
| Frontend muestra "✗ Sin conexión" | Comprueba que el backend esté corriendo en el puerto 8000 |

---

> **Última verificación de comandos:** 28 de febrero de 2026
