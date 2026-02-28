// Cambia esto si despliegas tu backend en Render/Fly/etc.
const API_BASE = "https://hackudc-2026.onrender.com";

const $ = (sel) => document.querySelector(sel);

const form = $("#formNota");
const msg = $("#msg");
const lista = $("#lista");
const contador = $("#contador");
const buscador = $("#buscador");
const filtroTipo = $("#filtroTipo");

$("#btnRecargar").addEventListener("click", () => cargarNotas());

buscador.addEventListener("input", () => renderUltimas());
filtroTipo.addEventListener("change", () => renderUltimas());

let cacheNotas = [];

function setMsg(text, isError = false){
  msg.textContent = text;
  msg.style.color = isError ? "rgba(251,113,133,.95)" : "rgba(255,255,255,.65)";
}

function toNiceDate(isoOrDate){
  try{
    const d = new Date(isoOrDate);
    return d.toLocaleString();
  }catch{
    return String(isoOrDate);
  }
}

async function apiFetch(path, options = {}){
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });

  if (!res.ok){
    let detail = "";
    try{
      const data = await res.json();
      detail = data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data);
    }catch{
      detail = await res.text();
    }
    throw new Error(`HTTP ${res.status}: ${detail || "Error"}`);
  }

  // DELETE puede devolver json simple; GET/POST devuelven json
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

function normalizaTexto(s){
  return (s ?? "").toString().toLowerCase();
}

function aplicaFiltros(notas){
  const q = normalizaTexto(buscador.value);
  const tipo = filtroTipo.value;

  return notas.filter(n => {
    const hayTipo = !tipo || n?.metadato?.tipo === tipo;

    const hayQuery = !q || [
      n?.descripcion,
      n?.metadato?.autor,
      n?.metadato?.tipo,
      n?.identificador
    ].some(v => normalizaTexto(v).includes(q));

    return hayTipo && hayQuery;
  });
}

function render(notas){
  contador.textContent = String(notas.length);
  lista.innerHTML = "";

  if (notas.length === 0){
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "No hay notas que mostrar.";
    lista.appendChild(empty);
    return;
  }

  for (const n of notas){
    const item = document.createElement("div");
    item.className = "item";

    const top = document.createElement("div");
    top.className = "itemTop";

    const title = document.createElement("div");
    title.className = "itemTitle";

    const desc = document.createElement("div");
    desc.className = "desc";
    desc.textContent = n.descripcion ?? "";

    const meta = document.createElement("div");
    meta.className = "meta";

    const pillTipo = document.createElement("span");
    pillTipo.className = "pill";
    pillTipo.textContent = `tipo: ${n?.metadato?.tipo ?? "-"}`;

    const pillAutor = document.createElement("span");
    pillAutor.className = "pill";
    pillAutor.textContent = `autor: ${n?.metadato?.autor ?? "-"}`;

    const pillPrioridad = document.createElement("span");
    pillPrioridad.className = "pill";
    pillPrioridad.textContent = `prioridad: ${n?.metadato?.prioridad ?? "-"}`;

    const pillFecha = document.createElement("span");
    pillFecha.className = "pill";
    pillFecha.textContent = `fecha: ${toNiceDate(n.fecha)}`;

    meta.append(pillTipo, pillAutor, pillPrioridad, pillFecha);

    title.append(desc, meta);

    const btn = document.createElement("button");
    btn.className = "danger";
    btn.textContent = "Borrar";
    btn.addEventListener("click", async () => {
      if (!confirm("¿Borrar esta nota?")) return;
      try{
        await apiFetch(`/notas/${encodeURIComponent(n.identificador)}`, { method: "DELETE" });
        setMsg("Nota eliminada.");
        await cargarNotas();
      }catch(e){
        setMsg(e.message, true);
      }
    });

    top.append(title, btn);
    item.append(top);
    lista.append(item);
  }
}

function renderUltimas(){
  const filtradas = aplicaFiltros(cacheNotas);
  render(filtradas);
}

async function cargarNotas(){
  try{
    setMsg("Cargando...");
    const notas = await apiFetch("/notas");
    cacheNotas = Array.isArray(notas) ? notas : [];
    setMsg(`Cargadas ${cacheNotas.length} notas.`);
    renderUltimas();
  }catch(e){
    setMsg(e.message, true);
  }
}

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  setMsg("");

  const descripcion = $("#descripcion").value.trim();
  const tipo = $("#tipo").value;
  const autorRaw = $("#autor").value.trim();
  const prioridadRaw = $("#prioridad").value.trim();

  const metadato = {
    tipo,
    ...(autorRaw ? { autor: autorRaw } : {}),
    ...(prioridadRaw !== "" ? { prioridad: Number(prioridadRaw) } : {}),
  };

  const payload = { descripcion, metadato };

  try{
    setMsg("Creando...");
    await apiFetch("/notas", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    $("#descripcion").value = "";
    $("#autor").value = "";
    $("#prioridad").value = "";

    setMsg("Nota creada.");
    await cargarNotas();
  }catch(e){
    setMsg(e.message, true);
  }
});

// Inicio
cargarNotas();
