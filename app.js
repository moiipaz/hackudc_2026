const API_BASE = "https://hackudc-2026.onrender.com";
const $ = (sel) => document.querySelector(sel);

<<<<<<< HEAD
/* ---- elementos ---- */
const pageAuth   = $("#pageAuth");
const pageApp    = $("#pageApp");

// auth
const tabLogin        = $("#tabLogin");
const tabRegistro     = $("#tabRegistro");
const panelLogin      = $("#panelLogin");
const panelRegistro   = $("#panelRegistro");
const btnLogin        = $("#btnLogin");
const btnCrearUsuario = $("#btnCrearUsuario");
const msgLogin        = $("#msgLogin");
const msgRegistro     = $("#msgRegistro");

// app
const form               = $("#formNota");
const msg                = $("#msg");
const lista              = $("#lista");
const contador           = $("#contador");
const buscador           = $("#buscador");
const filtroTipo         = $("#filtroTipo");
const usuarioActivoBadge = $("#usuarioActivoBadge");
const btnLogout          = $("#btnLogout");

let cacheNotas   = [];
let usuarioActivo = null;  // { identificador, nombre, email }

/* ============================================================
   NAVEGACIÓN
   ============================================================ */
function irAAuth() {
  pageApp.style.display  = "none";
  pageAuth.style.display = "";
  // reset animación
  pageAuth.style.animation = "none";
  requestAnimationFrame(() => { pageAuth.style.animation = ""; });
}

function irAApp() {
  pageAuth.style.display = "none";
  pageApp.style.display  = "";
  pageApp.style.animation = "none";
  requestAnimationFrame(() => { pageApp.style.animation = ""; });
  usuarioActivoBadge.textContent = usuarioActivo?.nombre ?? "Sin usuario";
  cargarNotas();
}

/* ============================================================
   SESIÓN
   ============================================================ */
function guardarSesion(u) {
  usuarioActivo = u;
  localStorage.setItem("session", JSON.stringify(u));
}

function cargarSesion() {
  try {
    const s = localStorage.getItem("session");
    return s ? JSON.parse(s) : null;
  } catch { return null; }
}

function cerrarSesion() {
  usuarioActivo = null;
  localStorage.removeItem("session");
  irAAuth();
}

=======
/* ============================================================
   WAKE-UP DEL SERVIDOR (Render duerme tras 15min sin uso)
   ============================================================ */
async function wakeUpServer() {
  const indicator = $("#serverStatus");
  if (!indicator) return;
  try {
    indicator.textContent = "⏳ Conectando con el servidor...";
    indicator.style.color = "rgba(255,180,0,.85)";
    const res = await fetch(`${API_BASE}/`, { signal: AbortSignal.timeout(30000) });
    if (res.ok) {
      indicator.textContent = "✓ Servidor listo";
      indicator.style.color = "rgba(74,222,128,.85)";
      setTimeout(() => { indicator.textContent = ""; }, 3000);
    }
  } catch(e) {
    indicator.textContent = "✗ Sin conexión con el servidor. Espera unos segundos y recarga.";
    indicator.style.color = "rgba(224,92,115,.9)";
  }
}

/* ---- elementos ---- */
const pageAuth   = $("#pageAuth");
const pageApp    = $("#pageApp");

// auth
const tabLogin        = $("#tabLogin");
const tabRegistro     = $("#tabRegistro");
const panelLogin      = $("#panelLogin");
const panelRegistro   = $("#panelRegistro");
const btnLogin        = $("#btnLogin");
const btnCrearUsuario = $("#btnCrearUsuario");
const msgLogin        = $("#msgLogin");
const msgRegistro     = $("#msgRegistro");

// app
const form               = $("#formNota");
const msg                = $("#msg");
const lista              = $("#lista");
const contador           = $("#contador");
const buscador           = $("#buscador");
const filtroTipo         = $("#filtroTipo");
const usuarioActivoBadge = $("#usuarioActivoBadge");
const btnLogout          = $("#btnLogout");

let cacheNotas   = [];
let usuarioActivo = null;  // { identificador, nombre, email }

/* ============================================================
   NAVEGACIÓN
   ============================================================ */
function irAAuth() {
  pageApp.style.display  = "none";
  pageAuth.style.display = "";
  // reset animación
  pageAuth.style.animation = "none";
  requestAnimationFrame(() => { pageAuth.style.animation = ""; });
}

function irAApp() {
  pageAuth.style.display = "none";
  pageApp.style.display  = "";
  pageApp.style.animation = "none";
  requestAnimationFrame(() => { pageApp.style.animation = ""; });
  usuarioActivoBadge.textContent = usuarioActivo?.nombre ?? "Sin usuario";
  cargarNotas();
}

/* ============================================================
   SESIÓN
   ============================================================ */
function guardarSesion(u) {
  usuarioActivo = u;
  localStorage.setItem("session", JSON.stringify(u));
}

function cargarSesion() {
  try {
    const s = localStorage.getItem("session");
    return s ? JSON.parse(s) : null;
  } catch { return null; }
}

function cerrarSesion() {
  usuarioActivo = null;
  localStorage.removeItem("session");
  irAAuth();
}

>>>>>>> c3c576badfd93ec830bfd2e07579756508b3af08
/* ============================================================
   API
   ============================================================ */
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      detail = data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data);
    } catch { detail = await res.text(); }
    throw new Error(`HTTP ${res.status}: ${detail || "Error"}`);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

/* ============================================================
   MENSAJES
   ============================================================ */
function setMsg(text, isError = false) {
  msg.textContent = text;
  msg.style.color = isError ? "rgba(224,92,115,.9)" : "rgba(255,255,255,.45)";
}

function setMsgAuth(el, text, isError = false) {
  el.textContent = text;
  el.style.color = isError ? "rgba(224,92,115,.9)" : "rgba(74,222,128,.85)";
}

/* ============================================================
   TABS AUTH
   ============================================================ */
tabLogin.addEventListener("click", () => {
  tabLogin.classList.add("active");
  tabRegistro.classList.remove("active");
  panelLogin.style.display    = "";
  panelRegistro.style.display = "none";
  setMsgAuth(msgLogin, "");
});

tabRegistro.addEventListener("click", () => {
  tabRegistro.classList.add("active");
  tabLogin.classList.remove("active");
  panelRegistro.style.display = "";
  panelLogin.style.display    = "none";
  setMsgAuth(msgRegistro, "");
});

/* ============================================================
   LOGIN
   ============================================================ */
btnLogin.addEventListener("click", async () => {
  const email    = $("#lEmail").value.trim();
  const password = $("#lPassword").value;

  if (!email || !password) {
    setMsgAuth(msgLogin, "Introduce email y contraseña.", true);
    return;
  }

  setMsgAuth(msgLogin, "Iniciando sesión...");
  try {
    const u = await apiFetch("/usuarios/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    guardarSesion({ identificador: u.identificador, nombre: u.nombre, email: u.email });
    $("#lEmail").value    = "";
    $("#lPassword").value = "";
    irAApp();
  } catch(e) {
<<<<<<< HEAD
    if      (e.message.includes("401")) setMsgAuth(msgLogin, "Contraseña incorrecta.", true);
    else if (e.message.includes("404")) setMsgAuth(msgLogin, "Usuario no encontrado.", true);
=======
    if      (e.message.includes("401"))    setMsgAuth(msgLogin, "Contraseña incorrecta.", true);
    else if (e.message.includes("404"))    setMsgAuth(msgLogin, "Usuario no encontrado.", true);
    else if (e.message.includes("Failed") || e.message.includes("NetworkError") || e.message.includes("fetch"))
                                           setMsgAuth(msgLogin, "Sin conexión con el servidor. El servidor puede estar arrancando, espera 30s y reintenta.", true);
>>>>>>> c3c576badfd93ec830bfd2e07579756508b3af08
    else    setMsgAuth(msgLogin, e.message, true);
  }
});

// Login con Enter
["lEmail", "lPassword"].forEach(id => {
  $(` #${id}`);
  document.getElementById(id)?.addEventListener("keydown", e => {
    if (e.key === "Enter") btnLogin.click();
  });
});

/* ============================================================
   REGISTRO
   ============================================================ */
btnCrearUsuario.addEventListener("click", async () => {
  const nombre   = $("#uNombre").value.trim();
  const email    = $("#uEmail").value.trim();
  const password = $("#uPassword").value;

  if (!nombre || !email || !password) {
    setMsgAuth(msgRegistro, "Rellena todos los campos.", true);
    return;
  }
  if (password.length < 6) {
    setMsgAuth(msgRegistro, "La contraseña debe tener al menos 6 caracteres.", true);
    return;
  }

  setMsgAuth(msgRegistro, "Creando cuenta...");
  try {
    const u = await apiFetch("/usuarios", {
      method: "POST",
      body: JSON.stringify({ nombre, email, password }),
    });
    guardarSesion({ identificador: u.identificador, nombre: u.nombre, email: u.email });
    $("#uNombre").value   = "";
    $("#uEmail").value    = "";
    $("#uPassword").value = "";
    irAApp();
  } catch(e) {
<<<<<<< HEAD
    if (e.message.includes("400")) setMsgAuth(msgRegistro, "Ya existe una cuenta con ese email.", true);
=======
    if      (e.message.includes("400"))    setMsgAuth(msgRegistro, "Ya existe una cuenta con ese email.", true);
    else if (e.message.includes("Failed") || e.message.includes("NetworkError") || e.message.includes("fetch"))
                                           setMsgAuth(msgRegistro, "Sin conexión con el servidor. El servidor puede estar arrancando, espera 30s y reintenta.", true);
>>>>>>> c3c576badfd93ec830bfd2e07579756508b3af08
    else setMsgAuth(msgRegistro, e.message, true);
  }
});

// Registro con Enter en último campo
document.getElementById("uPassword")?.addEventListener("keydown", e => {
  if (e.key === "Enter") btnCrearUsuario.click();
});

/* ============================================================
   LOGOUT
   ============================================================ */
btnLogout.addEventListener("click", () => cerrarSesion());

/* ============================================================
   NOTAS
   ============================================================ */
function normalizaTexto(s) {
  return (s ?? "").toString().toLowerCase();
}

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

function toNiceDate(isoOrDate) {
  try { return new Date(isoOrDate).toLocaleString(); }
  catch { return String(isoOrDate); }
}

function render(notas) {
  contador.textContent = String(notas.length);
  lista.innerHTML = "";

  if (notas.length === 0) {
    const empty = document.createElement("div");
    empty.style.cssText = "color:rgba(255,255,255,.3);font-size:13px;padding:12px 0;";
    empty.textContent = "No hay notas que mostrar.";
    lista.appendChild(empty);
    return;
  }

  for (const n of notas) {
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

    for (const t of [
      `tipo: ${n?.metadato?.tipo ?? "-"}`,
      `autor: ${n?.metadato?.autor ?? "-"}`,
      `prioridad: ${n?.metadato?.prioridad ?? "-"}`,
      `fecha: ${toNiceDate(n.fecha)}`,
    ]) {
      const p = document.createElement("span");
      p.className = "pill";
      p.textContent = t;
      meta.appendChild(p);
    }

    title.append(desc, meta);

    const btn = document.createElement("button");
    btn.className = "danger";
    btn.textContent = "Borrar";
    btn.addEventListener("click", async () => {
      if (!confirm("¿Borrar esta nota?")) return;
      try {
        await apiFetch(`/notas/${encodeURIComponent(n.identificador)}`, { method: "DELETE" });
        setMsg("Nota eliminada.");
        await cargarNotas();
      } catch(e) { setMsg(e.message, true); }
    });

    top.append(title, btn);
    item.append(top);
    lista.append(item);
  }
}

function renderFiltradas() {
  render(aplicaFiltros(cacheNotas));
}

async function cargarNotas() {
  if (!usuarioActivo?.identificador) return;
  setMsg("Cargando...");
  try {
    const notas = await apiFetch(`/usuarios/${encodeURIComponent(usuarioActivo.identificador)}/notas`);
    cacheNotas = Array.isArray(notas) ? notas : [];
    setMsg(`${cacheNotas.length} nota${cacheNotas.length !== 1 ? "s" : ""}.`);
    renderFiltradas();
  } catch(e) { setMsg(e.message, true); }
}

buscador.addEventListener("input",   () => renderFiltradas());
filtroTipo.addEventListener("change", () => renderFiltradas());
$("#btnRecargar").addEventListener("click", () => cargarNotas());

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  if (!usuarioActivo?.identificador) return;

  const descripcion  = $("#descripcion").value.trim();
  const tipo         = $("#tipo").value;
  const autorRaw     = $("#autor").value.trim();
  const prioridadRaw = $("#prioridad").value.trim();

  const metadato = {
    tipo,
    ...(autorRaw     ? { autor:    autorRaw }              : {}),
    ...(prioridadRaw ? { prioridad: Number(prioridadRaw) } : {}),
  };

  setMsg("Creando nota...");
  try {
    await apiFetch("/notas", {
      method: "POST",
      body: JSON.stringify({ usuario_id: usuarioActivo.identificador, descripcion, metadato }),
    });
    $("#descripcion").value = "";
    $("#autor").value       = "";
    $("#prioridad").value   = "";
    setMsg("Nota creada.");
    await cargarNotas();
  } catch(e) { setMsg(e.message, true); }
});

/* ============================================================
   INIT
   ============================================================ */
(function init() {
  const sesion = cargarSesion();
  if (sesion?.identificador) {
    usuarioActivo = sesion;
    irAApp();
  } else {
    irAAuth();
<<<<<<< HEAD
  }
})();
=======
    wakeUpServer();
  }
})();
>>>>>>> c3c576badfd93ec830bfd2e07579756508b3af08
