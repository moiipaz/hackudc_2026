// Cambia esto si despliegas tu backend en Render/Fly/etc.
const API_BASE = "https://hackudc-2026.onrender.com";

const $ = (sel) => document.querySelector(sel);

const form          = $("#formNota");
const msg           = $("#msg");
const lista         = $("#lista");
const contador      = $("#contador");
const buscador      = $("#buscador");
const filtroTipo    = $("#filtroTipo");

// UI usuarios
const usuarioSelect       = $("#usuarioSelect");
const usuarioActivoBadge  = $("#usuarioActivoBadge");
const btnCrearUsuario     = $("#btnCrearUsuario");
const btnCargarUsuarios   = $("#btnCargarUsuarios");
const btnLogin            = $("#btnLogin");
const btnMostrarRegistro  = $("#btnMostrarRegistro");
const btnCancelarRegistro = $("#btnCancelarRegistro");
const panelLogin          = $("#panelLogin");
const panelRegistro       = $("#panelRegistro");
const msgLogin            = $("#msgLogin");

let cacheNotas    = [];
let cacheUsuarios = [];

/* ---- helpers ---- */
function setMsg(text, isError = false) {
  msg.textContent = text;
  msg.style.color = isError ? "rgba(224,92,115,.9)" : "rgba(255,255,255,.45)";
}

function setMsgLogin(text, isError = false) {
  msgLogin.textContent = text;
  msgLogin.style.color = isError ? "rgba(224,92,115,.9)" : "rgba(74,222,128,.8)";
}

function setUsuarioBadge() {
  const id = getUsuarioId();
  const u  = cacheUsuarios.find(x => x.identificador === id);
  usuarioActivoBadge.textContent = u ? u.nombre : "Sin usuario";
}

function getUsuarioId() {
  return usuarioSelect?.value || localStorage.getItem("usuario_id") || "";
}

function setUsuarioId(id) {
  if (usuarioSelect) usuarioSelect.value = id;
  localStorage.setItem("usuario_id", id);
  setUsuarioBadge();
}

function toNiceDate(isoOrDate) {
  try { return new Date(isoOrDate).toLocaleString(); }
  catch { return String(isoOrDate); }
}

async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
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
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

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

/* ---- render notas ---- */
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

    const top   = document.createElement("div");
    top.className = "itemTop";

    const title = document.createElement("div");
    title.className = "itemTitle";

    const desc = document.createElement("div");
    desc.className = "desc";
    desc.textContent = n.descripcion ?? "";

    const meta = document.createElement("div");
    meta.className = "meta";

    const pills = [
      `tipo: ${n?.metadato?.tipo ?? "-"}`,
      `autor: ${n?.metadato?.autor ?? "-"}`,
      `prioridad: ${n?.metadato?.prioridad ?? "-"}`,
      `fecha: ${toNiceDate(n.fecha)}`,
    ];

    for (const t of pills) {
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

function renderUltimas() {
  render(aplicaFiltros(cacheNotas));
}

/* ---- cargar usuarios ---- */
async function cargarUsuarios() {
  try {
    const usuarios = await apiFetch("/usuarios");
    cacheUsuarios = Array.isArray(usuarios) ? usuarios : [];

    usuarioSelect.innerHTML = "";
    if (cacheUsuarios.length === 0) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "No hay usuarios (crea uno)";
      usuarioSelect.appendChild(opt);
      setUsuarioBadge();
      return;
    }

    for (const u of cacheUsuarios) {
      const opt = document.createElement("option");
      opt.value = u.identificador;
      opt.textContent = `${u.nombre} (${u.email})`;
      usuarioSelect.appendChild(opt);
    }

    const saved = localStorage.getItem("usuario_id");
    const existe = saved && cacheUsuarios.some(u => u.identificador === saved);
    setUsuarioId(existe ? saved : cacheUsuarios[0].identificador);
  } catch(e) { setMsg(e.message, true); }
}

/* ---- cargar notas ---- */
async function cargarNotas() {
  try {
    const usuario_id = getUsuarioId();
    if (!usuario_id) {
      cacheNotas = [];
      setMsg("Crea/selecciona un usuario para ver notas.", true);
      renderUltimas();
      return;
    }
    setMsg("Cargando...");
    const notas = await apiFetch(`/usuarios/${encodeURIComponent(usuario_id)}/notas`);
    cacheNotas = Array.isArray(notas) ? notas : [];
    setMsg(`Cargadas ${cacheNotas.length} nota${cacheNotas.length !== 1 ? "s" : ""}.`);
    renderUltimas();
  } catch(e) { setMsg(e.message, true); }
}

/* ---- toggle paneles ---- */
btnMostrarRegistro.addEventListener("click", () => {
  panelRegistro.style.display = "block";
  panelLogin.style.display    = "none";
});

btnCancelarRegistro.addEventListener("click", () => {
  panelRegistro.style.display = "none";
  panelLogin.style.display    = "block";
});

/* ---- LOGIN ---- */
btnLogin.addEventListener("click", async () => {
  const email    = $("#lEmail").value.trim();
  const password = $("#lPassword").value;

  if (!email || !password) {
    setMsgLogin("Introduce email y contraseña.", true);
    return;
  }

  try {
    setMsgLogin("Iniciando sesión...", false);
    const u = await apiFetch("/usuarios/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    await cargarUsuarios();
    if (u?.identificador) setUsuarioId(u.identificador);

    setMsgLogin(`¡Bienvenido, ${u.nombre}!`);
    $("#lEmail").value    = "";
    $("#lPassword").value = "";
    await cargarNotas();
  } catch(e) {
    const msg401 = e.message.includes("401");
    const msg404 = e.message.includes("404");
    setMsgLogin(msg401 ? "Contraseña incorrecta." : msg404 ? "Usuario no encontrado." : e.message, true);
  }
});

/* ---- CREAR USUARIO ---- */
btnCrearUsuario.addEventListener("click", async () => {
  const nombre   = $("#uNombre").value.trim();
  const email    = $("#uEmail").value.trim();
  const password = $("#uPassword").value;

  if (!nombre || !email || !password) {
    setMsg("Falta nombre, email o contraseña.", true);
    return;
  }
  if (password.length < 6) {
    setMsg("La contraseña debe tener al menos 6 caracteres.", true);
    return;
  }

  try {
    setMsg("Creando cuenta...");
    const u = await apiFetch("/usuarios", {
      method: "POST",
      body: JSON.stringify({ nombre, email, password }),
    });

    await cargarUsuarios();
    if (u?.identificador) setUsuarioId(u.identificador);

    $("#uNombre").value   = "";
    $("#uEmail").value    = "";
    $("#uPassword").value = "";

    // volver al panel de login
    panelRegistro.style.display = "none";
    panelLogin.style.display    = "block";

    setMsgLogin(`Cuenta creada. ¡Bienvenido, ${u.nombre}!`);
    await cargarNotas();
  } catch(e) { setMsg(e.message, true); }
});

/* ---- recargar usuarios ---- */
btnCargarUsuarios.addEventListener("click", async () => {
  await cargarUsuarios();
  await cargarNotas();
});

/* ---- cambio de usuario activo ---- */
usuarioSelect.addEventListener("change", async () => {
  setUsuarioId(usuarioSelect.value);
  await cargarNotas();
});

/* ---- recargar notas ---- */
$("#btnRecargar").addEventListener("click", () => cargarNotas());

/* ---- filtros ---- */
buscador.addEventListener("input", () => renderUltimas());
filtroTipo.addEventListener("change", () => renderUltimas());

/* ---- submit nota ---- */
form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  setMsg("");

  const usuario_id = getUsuarioId();
  if (!usuario_id) {
    setMsg("Selecciona o crea un usuario antes de crear una nota.", true);
    return;
  }

  const descripcion   = $("#descripcion").value.trim();
  const tipo          = $("#tipo").value;
  const autorRaw      = $("#autor").value.trim();
  const prioridadRaw  = $("#prioridad").value.trim();

  const metadato = {
    tipo,
    ...(autorRaw      ? { autor:    autorRaw }               : {}),
    ...(prioridadRaw  ? { prioridad: Number(prioridadRaw) }  : {}),
  };

  try {
    setMsg("Creando nota...");
    await apiFetch("/notas", {
      method: "POST",
      body: JSON.stringify({ usuario_id, descripcion, metadato }),
    });
    $("#descripcion").value = "";
    $("#autor").value       = "";
    $("#prioridad").value   = "";
    setMsg("Nota creada.");
    await cargarNotas();
  } catch(e) { setMsg(e.message, true); }
});

/* ---- init ---- */
(async function init() {
  await cargarUsuarios();
  setUsuarioBadge();
  await cargarNotas();
})();
