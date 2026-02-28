document.addEventListener('DOMContentLoaded', function () {

const API_BASE = "https://hackudc-2026.onrender.com";
const $ = (sel) => document.querySelector(sel);

// Iconos por categoría
const CATEGORY_ICONS = {
  youtube:         "▶",
  audios:          "🎙",
  recordatorios:   "🔔",
  codigo:          "</>",
  personal:        "👤",
  trabajo:         "💼",
  estudios:        "📚",
  salud:           "❤",
  compra:          "🛒",
  tareas:          "✓",
  ideas:           "💡",
  lectura:         "📖",
  peliculas_series:"🎬",
  eventos:         "📅",
  contactos:       "👥",
  recetas:         "🍳",
  musica:          "🎵",
  metas:           "🎯",
  tecnologia:      "⚙",
  inspiraciones:   "✨",
  otras:           "•",
};

// Colores por categoría
const CATEGORY_COLORS = {
  youtube:         "rgba(255,0,0,.18)",
  audios:          "rgba(168,85,247,.18)",
  recordatorios:   "rgba(251,191,36,.18)",
  codigo:          "rgba(34,211,238,.18)",
  personal:        "rgba(99,102,241,.18)",
  trabajo:         "rgba(59,130,246,.18)",
  estudios:        "rgba(16,185,129,.18)",
  salud:           "rgba(239,68,68,.18)",
  compra:          "rgba(245,158,11,.18)",
  tareas:          "rgba(107,114,128,.18)",
  ideas:           "rgba(234,179,8,.18)",
  lectura:         "rgba(14,165,233,.18)",
  peliculas_series:"rgba(217,70,239,.18)",
  eventos:         "rgba(20,184,166,.18)",
  contactos:       "rgba(168,162,158,.18)",
  recetas:         "rgba(234,88,12,.18)",
  musica:          "rgba(236,72,153,.18)",
  metas:           "rgba(34,197,94,.18)",
  tecnologia:      "rgba(6,182,212,.18)",
  inspiraciones:   "rgba(251,146,60,.18)",
  otras:           "rgba(148,163,184,.18)",
};

/* ---- elementos ---- */
const pageAuth   = $("#pageAuth");
const pageApp    = $("#pageApp");
const tabLogin        = $("#tabLogin");
const tabRegistro     = $("#tabRegistro");
const panelLogin      = $("#panelLogin");
const panelRegistro   = $("#panelRegistro");
const btnLogin        = $("#btnLogin");
const btnCrearUsuario = $("#btnCrearUsuario");
const msgLogin        = $("#msgLogin");
const msgRegistro     = $("#msgRegistro");
const serverStatus    = $("#serverStatus");
const form               = $("#formNota");
const msg                = $("#msg");
const lista              = $("#lista");
const contador           = $("#contador");
const buscador           = $("#buscador");
const filtroTipo         = $("#filtroTipo");
const usuarioActivoBadge = $("#usuarioActivoBadge");
const btnLogout          = $("#btnLogout");

let cacheNotas    = [];
let usuarioActivo = null;

/* --- WAKE UP --- */
async function wakeUpServer() {
  try {
    serverStatus.textContent = "⏳ Conectando con el servidor...";
    serverStatus.style.color = "rgba(255,180,0,.85)";
    const res = await fetch(API_BASE + "/", { signal: AbortSignal.timeout(35000) });
    if (res.ok) {
      serverStatus.textContent = "✓ Servidor listo";
      serverStatus.style.color = "rgba(74,222,128,.85)";
      setTimeout(() => { serverStatus.textContent = ""; }, 3000);
    }
  } catch(e) {
    serverStatus.textContent = "✗ Sin conexión. Espera unos segundos y recarga.";
    serverStatus.style.color = "rgba(224,92,115,.9)";
  }
}

/* --- NAVEGACIÓN --- */
function irAAuth() {
  pageApp.style.display  = "none";
  pageAuth.style.display = "";
}
function irAApp() {
  pageAuth.style.display = "none";
  pageApp.style.display  = "";
  usuarioActivoBadge.textContent = usuarioActivo?.nombre ?? "";
  cargarNotas();
}

/* --- SESIÓN --- */
function guardarSesion(u) {
  usuarioActivo = u;
  localStorage.setItem("notify_session", JSON.stringify(u));
}
function cargarSesion() {
  try { const s = localStorage.getItem("notify_session"); return s ? JSON.parse(s) : null; }
  catch { return null; }
}
function cerrarSesion() {
  usuarioActivo = null;
  localStorage.removeItem("notify_session");
  irAAuth();
}

/* --- API --- */
async function apiFetch(path, options = {}) {
  let res;
  try {
    res = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options
    });
  } catch(e) {
    throw new Error("NETWORK: " + e.message);
  }
  if (!res.ok) {
    let detail = "";
    try { const d = await res.json(); detail = d?.detail ? JSON.stringify(d.detail) : JSON.stringify(d); }
    catch { detail = await res.text(); }
    throw new Error("HTTP " + res.status + ": " + (detail || "Error"));
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

/* --- MENSAJES --- */
function setMsg(text, isError) {
  msg.textContent = text;
  msg.style.color = isError ? "rgba(224,92,115,.9)" : "rgba(255,255,255,.45)";
}
function setMsgAuth(el, text, isError) {
  el.textContent = text;
  el.style.color = isError ? "rgba(224,92,115,.9)" : "rgba(74,222,128,.85)";
}
function errorMsg(e) {
  if (e.message.includes("401")) return "Contraseña incorrecta.";
  if (e.message.includes("404")) return "Usuario no encontrado.";
  if (e.message.includes("400")) return "Ya existe una cuenta con ese email.";
  if (e.message.includes("NETWORK")) return "Sin conexión con el servidor. Espera unos segundos y reintenta.";
  return e.message;
}

/* --- TABS --- */
tabLogin.addEventListener("click", () => {
  tabLogin.classList.add("active"); tabRegistro.classList.remove("active");
  panelLogin.style.display = ""; panelRegistro.style.display = "none";
  setMsgAuth(msgLogin, "");
});
tabRegistro.addEventListener("click", () => {
  tabRegistro.classList.add("active"); tabLogin.classList.remove("active");
  panelRegistro.style.display = ""; panelLogin.style.display = "none";
  setMsgAuth(msgRegistro, "");
});

/* --- LOGIN --- */
async function doLogin() {
  const email    = $("#lEmail").value.trim();
  const password = $("#lPassword").value;
  if (!email || !password) { setMsgAuth(msgLogin, "Introduce email y contraseña.", true); return; }
  setMsgAuth(msgLogin, "Iniciando sesión...");
  try {
    const u = await apiFetch("/usuarios/login", { method: "POST", body: JSON.stringify({ email, password }) });
    guardarSesion({ identificador: u.identificador, nombre: u.nombre, email: u.email });
    $("#lEmail").value = ""; $("#lPassword").value = "";
    irAApp();
  } catch(e) { setMsgAuth(msgLogin, errorMsg(e), true); }
}
btnLogin.addEventListener("click", doLogin);
$("#lEmail").addEventListener("keydown",    e => { if (e.key === "Enter") doLogin(); });
$("#lPassword").addEventListener("keydown", e => { if (e.key === "Enter") doLogin(); });

/* --- REGISTRO --- */
async function doRegistro() {
  const nombre   = $("#uNombre").value.trim();
  const email    = $("#uEmail").value.trim();
  const password = $("#uPassword").value;
  if (!nombre || !email || !password) { setMsgAuth(msgRegistro, "Rellena todos los campos.", true); return; }
  if (password.length < 6) { setMsgAuth(msgRegistro, "La contraseña debe tener al menos 6 caracteres.", true); return; }
  setMsgAuth(msgRegistro, "Creando cuenta...");
  try {
    const u = await apiFetch("/usuarios", { method: "POST", body: JSON.stringify({ nombre, email, password }) });
    guardarSesion({ identificador: u.identificador, nombre: u.nombre, email: u.email });
    $("#uNombre").value = ""; $("#uEmail").value = ""; $("#uPassword").value = "";
    irAApp();
  } catch(e) { setMsgAuth(msgRegistro, errorMsg(e), true); }
}
btnCrearUsuario.addEventListener("click", doRegistro);
$("#uPassword").addEventListener("keydown", e => { if (e.key === "Enter") doRegistro(); });

/* --- LOGOUT --- */
btnLogout.addEventListener("click", cerrarSesion);

/* --- NOTAS --- */
function normalizaTexto(s) { return (s ?? "").toString().toLowerCase(); }

function aplicaFiltros(notas) {
  const q    = normalizaTexto(buscador.value);
  const tipo = filtroTipo.value;
  return notas.filter(n => {
    const hayTipo  = !tipo || n?.metadato?.tipo === tipo;
    const hayQuery = !q || [n?.descripcion, n?.metadato?.autor, n?.metadato?.tipo, n?.identificador]
      .some(v => normalizaTexto(v).includes(q));
    return hayTipo && hayQuery;
  });
}

function toNiceDate(d) {
  try { return new Date(d).toLocaleString(); }
  catch { return String(d); }
}

function render(notas) {
  contador.textContent = String(notas.length);
  lista.innerHTML = "";

  if (notas.length === 0) {
    const e = document.createElement("div");
    e.style.cssText = "color:rgba(255,255,255,.3);font-size:13px;padding:12px 0;";
    e.textContent = "No hay notas que mostrar.";
    lista.appendChild(e);
    return;
  }

  for (const n of notas) {
    const tipo  = n?.metadato?.tipo ?? "otras";
    const icon  = CATEGORY_ICONS[tipo]  ?? "•";
    const color = CATEGORY_COLORS[tipo] ?? "rgba(148,163,184,.18)";

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

    // Badge de categoría (destacado)
    const badgeTipo = document.createElement("span");
    badgeTipo.className = "pill pill-tipo";
    badgeTipo.style.background   = color;
    badgeTipo.style.borderColor  = color.replace(".18", ".45");
    badgeTipo.style.color        = "rgba(255,255,255,.9)";
    badgeTipo.textContent        = icon + " " + tipo;
    meta.appendChild(badgeTipo);

    // Resto de pills
    const extraPills = [
      n?.metadato?.autor     ? "autor: " + n.metadato.autor           : null,
      n?.metadato?.prioridad ? "prioridad: " + n.metadato.prioridad   : null,
      "fecha: " + toNiceDate(n.fecha),
    ].filter(Boolean);

    for (const t of extraPills) {
      const p = document.createElement("span");
      p.className = "pill";
      p.textContent = t;
      meta.appendChild(p);
    }

    // Motivo IA (si existe y confianza < 0.9, mostrar sutil)
    if (n?.metadato?.ia_motivo && n?.metadato?.ia_confianza < 0.9) {
      const motivo = document.createElement("span");
      motivo.className = "pill pill-ia";
      motivo.textContent = "IA: " + n.metadato.ia_motivo;
      meta.appendChild(motivo);
    }

    title.append(desc, meta);

    const btn = document.createElement("button");
    btn.className = "danger";
    btn.textContent = "Borrar";
    btn.addEventListener("click", async () => {
      if (!confirm("¿Borrar esta nota?")) return;
      try {
        await apiFetch("/notas/" + encodeURIComponent(n.identificador), { method: "DELETE" });
        setMsg("Nota eliminada.");
        await cargarNotas();
      } catch(e) { setMsg(e.message, true); }
    });

    top.append(title, btn);
    item.append(top);
    lista.append(item);
  }
}

function renderFiltradas() { render(aplicaFiltros(cacheNotas)); }

async function cargarNotas() {
  if (!usuarioActivo?.identificador) return;
  setMsg("Cargando...");
  try {
    const notas = await apiFetch("/usuarios/" + encodeURIComponent(usuarioActivo.identificador) + "/notas");
    cacheNotas = Array.isArray(notas) ? notas : [];
    setMsg(cacheNotas.length + " nota" + (cacheNotas.length !== 1 ? "s" : "") + ".");
    renderFiltradas();
  } catch(e) { setMsg(errorMsg(e), true); }
}

buscador.addEventListener("input",    renderFiltradas);
filtroTipo.addEventListener("change", renderFiltradas);
$("#btnRecargar").addEventListener("click", cargarNotas);

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  if (!usuarioActivo?.identificador) return;

  const descripcion  = $("#descripcion").value.trim();
  const autorRaw     = $("#autor").value.trim();
  const prioridadRaw = $("#prioridad").value.trim();

  if (!descripcion) { setMsg("Escribe una descripción.", true); return; }

  const metadato = {
    tipo: "otras",   // el backend lo sobreescribirá con la clasificación IA
    ...(autorRaw     ? { autor: autorRaw }                : {}),
    ...(prioridadRaw ? { prioridad: Number(prioridadRaw) } : {}),
  };

  setMsg("⏳ Clasificando con IA y guardando...");
  try {
    await apiFetch("/notas", {
      method: "POST",
      body: JSON.stringify({ usuario_id: usuarioActivo.identificador, descripcion, metadato }),
    });
    $("#descripcion").value = "";
    $("#autor").value       = "";
    $("#prioridad").value   = "";
    setMsg("✓ Nota creada y clasificada.");
    await cargarNotas();
  } catch(e) { setMsg(errorMsg(e), true); }
});

/* --- INIT --- */
(function () {
  const sesion = cargarSesion();
  if (sesion?.identificador) {
    usuarioActivo = sesion;
    irAApp();
  } else {
    irAAuth();
    wakeUpServer();
  }
})();

}); // fin DOMContentLoaded
