const API_BASE = "https://hackudc-2026.onrender.com";

const $ = (sel) => document.querySelector(sel);

let cacheNotas = [];
let usuarioActivo = null; // { identificador, nombre, email }

// =========================
// 📌 UTILIDADES
// =========================

function setMsg(id, text, isError = false) {
  const el = $(id);
  if (!el) return;
  el.textContent = text;
  el.style.color = isError ? "rgba(251,113,133,.95)" : "rgba(255,255,255,.65)";
}

function toNiceDate(isoOrDate) {
  try { return new Date(isoOrDate).toLocaleString(); } catch { return String(isoOrDate); }
}

async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (!res.ok) {
    let detail = "";
    try { const d = await res.json(); detail = d?.detail ? JSON.stringify(d.detail) : JSON.stringify(d); }
    catch { detail = await res.text(); }
    throw new Error(`HTTP ${res.status}: ${detail || "Error"}`);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

// =========================
// 📌 AUTH - TABS
// =========================

function showTab(tab) {
  $(`#formLogin`).style.display = tab === "login" ? "block" : "none";
  $(`#formRegister`).style.display = tab === "register" ? "block" : "none";
  $("#tabLogin").classList.toggle("active", tab === "login");
  $("#tabRegister").classList.toggle("active", tab === "register");
}

// =========================
// 📌 AUTH - LOGIN
// =========================

async function handleLogin() {
  const email = $("#loginEmail").value.trim();
  const password = $("#loginPassword").value.trim();

  if (!email || !password) {
    setMsg("#loginMsg", "Rellena email y contraseña.", true);
    return;
  }

  try {
    setMsg("#loginMsg", "Entrando...");
    const data = await apiFetch("/usuarios/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });

    usuarioActivo = {
      identificador: data.identificador,
      nombre: data.nombre,
      email: data.email
    };
    localStorage.setItem("usuario", JSON.stringify(usuarioActivo));

    mostrarPantallaMain();
    await cargarNotas();
  } catch (e) {
    setMsg("#loginMsg", e.message, true);
  }
}

// =========================
// 📌 AUTH - REGISTRO
// =========================

async function handleRegister() {
  const nombre = $("#regNombre").value.trim();
  const email = $("#regEmail").value.trim();
  const password = $("#regPassword").value.trim();

  if (!nombre || !email || !password) {
    setMsg("#registerMsg", "Rellena todos los campos.", true);
    return;
  }
  if (password.length < 6) {
    setMsg("#registerMsg", "La contraseña debe tener al menos 6 caracteres.", true);
    return;
  }

  try {
    setMsg("#registerMsg", "Creando cuenta...");
    await apiFetch("/usuarios", {
      method: "POST",
      body: JSON.stringify({ nombre, email, password })
    });
    setMsg("#registerMsg", "¡Cuenta creada! Inicia sesión.");
    showTab("login");
    $("#loginEmail").value = email;
  } catch (e) {
    setMsg("#registerMsg", e.message, true);
  }
}

// =========================
// 📌 AUTH - LOGOUT
// =========================

function handleLogout() {
  usuarioActivo = null;
  localStorage.removeItem("usuario");
  $("#mainScreen").style.display = "none";
  $("#authScreen").style.display = "flex";
  setMsg("#loginMsg", "");
}

// =========================
// 📌 PANTALLAS
// =========================

function mostrarPantallaMain() {
  $("#authScreen").style.display = "none";
  $("#mainScreen").style.display = "block";
  $("#usuarioActivoBadge").textContent = usuarioActivo?.nombre || "Usuario";
}

// =========================
// 📌 NOTAS
// =========================

function normalizaTexto(s) {
  return (s ?? "").toString().toLowerCase();
}

function aplicaFiltros(notas) {
  const q = normalizaTexto($("#buscador").value);
  const tipo = $("#filtroTipo").value;
  return notas.filter(n => {
    const hayTipo = !tipo || n?.metadato?.tipo === tipo;
    const hayQuery = !q || [n?.descripcion, n?.metadato?.autor, n?.metadato?.tipo, n?.identificador]
      .some(v => normalizaTexto(v).includes(q));
    return hayTipo && hayQuery;
  });
}

function render(notas) {
  const contador = $("#contador");
  const lista = $("#lista");
  contador.textContent = String(notas.length);
  lista.innerHTML = "";

  if (notas.length === 0) {
    const empty = document.createElement("div");
    empty.className = "muted";
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

    for (const [label, val] of [
      ["tipo", n?.metadato?.tipo],
      ["autor", n?.metadato?.autor],
      ["prioridad", n?.metadato?.prioridad],
      ["fecha", toNiceDate(n.fecha)]
    ]) {
      const pill = document.createElement("span");
      pill.className = "pill";
      pill.textContent = `${label}: ${val ?? "-"}`;
      meta.appendChild(pill);
    }

    title.append(desc, meta);

    const btn = document.createElement("button");
    btn.className = "danger";
    btn.textContent = "Borrar";
    btn.addEventListener("click", async () => {
      if (!confirm("¿Borrar esta nota?")) return;
      try {
        await apiFetch(`/notas/${encodeURIComponent(n.identificador)}`, { method: "DELETE" });
        setMsg("#msg", "Nota eliminada.");
        await cargarNotas();
      } catch (e) {
        setMsg("#msg", e.message, true);
      }
    });

    top.append(title, btn);
    item.append(top);
    lista.append(item);
  }
}

function renderUltimas() {
  render(aplicaFiltros(cacheNotas));
}

async function cargarNotas() {
  if (!usuarioActivo) return;
  try {
    setMsg("#msg", "Cargando...");
    const notas = await apiFetch(`/usuarios/${encodeURIComponent(usuarioActivo.identificador)}/notas`);
    cacheNotas = Array.isArray(notas) ? notas : [];
    setMsg("#msg", `${cacheNotas.length} notas cargadas.`);
    renderUltimas();
  } catch (e) {
    setMsg("#msg", e.message, true);
  }
}

// =========================
// 📌 EVENTOS
// =========================

$("#btnRecargar").addEventListener("click", () => cargarNotas());
$("#buscador").addEventListener("input", () => renderUltimas());
$("#filtroTipo").addEventListener("change", () => renderUltimas());

$("#formNota").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  if (!usuarioActivo) return;

  const descripcion = $("#descripcion").value.trim();
  const tipo = $("#tipo").value;
  const autorRaw = $("#autor").value.trim();
  const prioridadRaw = $("#prioridad").value.trim();

  const metadato = {
    tipo,
    ...(autorRaw ? { autor: autorRaw } : {}),
    ...(prioridadRaw !== "" ? { prioridad: Number(prioridadRaw) } : {}),
  };

  try {
    setMsg("#msg", "Creando...");
    await apiFetch("/notas", {
      method: "POST",
      body: JSON.stringify({ usuario_id: usuarioActivo.identificador, descripcion, metadato })
    });
    $("#descripcion").value = "";
    $("#autor").value = "";
    $("#prioridad").value = "";
    setMsg("#msg", "Nota creada.");
    await cargarNotas();
  } catch (e) {
    setMsg("#msg", e.message, true);
  }
});

// =========================
// 📌 INICIO
// =========================

(function init() {
  const saved = localStorage.getItem("usuario");
  if (saved) {
    try {
      usuarioActivo = JSON.parse(saved);
      mostrarPantallaMain();
      cargarNotas();
    } catch {
      localStorage.removeItem("usuario");
    }
  }
})();
