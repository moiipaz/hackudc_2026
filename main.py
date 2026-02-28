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

DB_FILE = "notas.json"


# =========================
# 📌 MODELOS
# =========================

class Metadato(BaseModel):
    tipo: str = Field(..., example="personal")
    autor: str | None = None
    prioridad: int | None = None


class Nota(BaseModel):
    identificador: str
    descripcion: str
    fecha: datetime
    metadato: Metadato


class NotaCreate(BaseModel):
    descripcion: str
    metadato: Metadato


# =========================
# 📌 FUNCIONES AUXILIARES
# =========================

def leer_notas():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)

    with open(DB_FILE, "r") as f:
        return json.load(f)


def guardar_notas(notas):
    with open(DB_FILE, "w") as f:
        json.dump(notas, f, indent=4, default=str)


# =========================
# 📌 ENDPOINTS
# =========================

@app.get("/notas", response_model=List[Nota])
def obtener_notas():
    return leer_notas()


@app.get("/notas/{identificador}", response_model=Nota)
def obtener_nota(identificador: str):
    notas = leer_notas()
    for nota in notas:
        if nota["identificador"] == identificador:
            return nota
    raise HTTPException(status_code=404, detail="Nota no encontrada")


@app.post("/notas", response_model=Nota)
def crear_nota(nota: NotaCreate):
    notas = leer_notas()

    nueva_nota = Nota(
        identificador=str(uuid4()),
        descripcion=nota.descripcion,
        fecha=datetime.now(),
        metadato=nota.metadato
    )

    notas.append(nueva_nota.model_dump())
    guardar_notas(notas)

    return nueva_nota


@app.delete("/notas/{identificador}")
def eliminar_nota(identificador: str):
    notas = leer_notas()

    for nota in notas:
        if nota["identificador"] == identificador:
            notas.remove(nota)
            guardar_notas(notas)
            return {"mensaje": "Nota eliminada"}

    raise HTTPException(status_code=404, detail="Nota no encontrada")
