document.addEventListener('DOMContentLoaded', function () {

const API_BASE = "https://notify-o1c2.onrender.com";
const $ = (sel) => document.querySelector(sel);

const CATEGORY_ICONS = {
  youtube:"▶", audios:"🎙", recordatorios:"🔔", codigo:"</>",
  personal:"👤", trabajo:"💼", estudios:"📚", salud:"❤", compra:"🛒",
  tareas:"✓", ideas:"💡", lectura:"📖", peliculas_series:"🎬",
  eventos:"📅", contactos:"👥", recetas:"🍳", musica:"🎵", metas:"🎯",
  tecnologia:"⚙", inspiraciones:"✨", links:"🔗", mapas_mentales:"🗺",
  flashcards:"🃏", proyectos:"📐", reflexiones:"🪞", viajes:"✈️", otras:"•",
};

const CATEGORY_COLORS = {
  youtube:"rgba(255,0,0,.18)", audios:"rgba(168,85,247,.18)",
  recordatorios:"rgba(251,191,36,.18)", codigo:"rgba(34,211,238,.18)",
  personal:"rgba(99,102,241,.18)", trabajo:"rgba(59,130,246,.18)",
  estudios:"rgba(16,185,129,.18)", salud:"rgba(239,68,68,.18)",
  compra:"rgba(245,158,11,.18)", tareas:"rgba(107,114,128,.18)",
  ideas:"rgba(234,179,8,.18)", lectura:"rgba(14,165,233,.18)",
  peliculas_series:"rgba(217,70,239,.18)", eventos:"rgba(20,184,166,.18)",
  contactos:"rgba(168,162,158,.18)", recetas:"rgba(234,88,12,.18)",
  musica:"rgba(236,72,153,.18)", metas:"rgba(120, 135, 125, 0.18)",
  tecnologia:"rgba(6,182,212,.18)", inspiraciones:"rgba(251,146,60,.18)",
  links:"rgba(99,202,183,.18)", mapas_mentales:"rgba(139,92,246,.18)",
  flashcards:"rgba(249,115,22,.18)", proyectos:"rgba(20,184,166,.18)",
  reflexiones:"rgba(180,180,220,.18)", viajes:"rgba(56,189,248,.18)", otras:"rgba(148,163,184,.18)",
};

const PRIORITY_ORDER = { high:0, medium:1, low:2, "":3 };
const PRIORITY_ICONS = { high:"🔴", medium:"🟡", low:"🟢" };

/* ---- elementos ---- */
const pageAuth        = $("#pageAuth");
const pageApp         = $("#pageApp");
const tabLogin        = $("#tabLogin");
const tabRegistro     = $("#tabRegistro");
const panelLogin      = $("#panelLogin");
const panelRegistro   = $("#panelRegistro");
const btnLogin        = $("#btnLogin");
const btnCrearUsuario = $("#btnCrearUsuario");
const msgLogin        = $("#msgLogin");
const msgRegistro     = $("#msgRegistro");
const serverStatus    = $("#serverStatus");
const form            = $("#formNota");
const msg             = $("#msg");
const usuarioActivoBadge = $("#usuarioActivoBadge");
const btnLogout       = $("#btnLogout");

let cacheNotas          = [];
let usuarioActivo       = null;
let archivoSeleccionado = null;

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
    serverStatus.textContent = "✗ Sin conexión.";
    serverStatus.style.color = "rgba(224,92,115,.9)";
  }
}

function irAAuth() { pageApp.style.display="none"; pageAuth.style.display=""; }
function irAApp()  {
  pageAuth.style.display="none"; pageApp.style.display="";
  usuarioActivoBadge.textContent = usuarioActivo?.nombre ?? "";
  cargarNotas();
}

function guardarSesion(u) { usuarioActivo=u; localStorage.setItem("notify_session", JSON.stringify(u)); }
function cargarSesion()   { try { const s=localStorage.getItem("notify_session"); return s?JSON.parse(s):null; } catch { return null; } }
function cerrarSesion()   { usuarioActivo=null; localStorage.removeItem("notify_session"); irAAuth(); }

async function apiFetch(path, options={}) {
  let res;
  try {
    res = await fetch(API_BASE+path, {
      headers: {"Content-Type":"application/json", ...(options.headers||{})},
      ...options
    });
  } catch(e) { throw new Error("NETWORK: "+e.message); }
  if (!res.ok) {
    let detail="";
    try { const d=await res.json(); detail=d?.detail?JSON.stringify(d.detail):JSON.stringify(d); }
    catch { detail=await res.text(); }
    throw new Error("HTTP "+res.status+": "+(detail||"Error"));
  }
  const ct=res.headers.get("content-type")||"";
  return ct.includes("application/json")?res.json():res.text();
}

function setMsg(text,isError) {
  msg.textContent=text;
  msg.style.color=isError?"rgba(224,92,115,.9)":"rgba(255,255,255,.45)";
}
function setMsgAuth(el,text,isError) {
  el.textContent=text;
  el.style.color=isError?"rgba(224,92,115,.9)":"rgba(74,222,128,.85)";
}
function errorMsg(e) {
  if (e.message.includes("401")) return "Contraseña incorrecta.";
  if (e.message.includes("404")) return "Usuario no encontrado.";
  if (e.message.includes("400")) return "Ya existe una cuenta con ese email.";
  if (e.message.includes("NETWORK")) return "Sin conexión con el servidor.";
  return e.message;
}

/* --- TABS AUTH --- */
tabLogin.addEventListener("click", () => {
  tabLogin.classList.add("active"); tabRegistro.classList.remove("active");
  panelLogin.style.display=""; panelRegistro.style.display="none";
  setMsgAuth(msgLogin,"");
});
tabRegistro.addEventListener("click", () => {
  tabRegistro.classList.add("active"); tabLogin.classList.remove("active");
  panelRegistro.style.display=""; panelLogin.style.display="none";
  setMsgAuth(msgRegistro,"");
});

/* --- LOGIN --- */
async function doLogin() {
  const email=$("#lEmail").value.trim(), password=$("#lPassword").value;
  if (!email||!password) { setMsgAuth(msgLogin,"Introduce email y contraseña.",true); return; }
  setMsgAuth(msgLogin,"Iniciando sesión...");
  try {
    const u=await apiFetch("/usuarios/login",{method:"POST",body:JSON.stringify({email,password})});
    guardarSesion({identificador:u.identificador,nombre:u.nombre,email:u.email});
    $("#lEmail").value=""; $("#lPassword").value="";
    irAApp();
  } catch(e) { setMsgAuth(msgLogin,errorMsg(e),true); }
}
btnLogin.addEventListener("click", doLogin);
$("#lEmail").addEventListener("keydown",    e=>{ if(e.key==="Enter") doLogin(); });
$("#lPassword").addEventListener("keydown", e=>{ if(e.key==="Enter") doLogin(); });

/* --- REGISTRO --- */
async function doRegistro() {
  const nombre=$("#uNombre").value.trim(), email=$("#uEmail").value.trim(), password=$("#uPassword").value;
  if (!nombre||!email||!password) { setMsgAuth(msgRegistro,"Rellena todos los campos.",true); return; }
  if (password.length<6) { setMsgAuth(msgRegistro,"La contraseña debe tener al menos 6 caracteres.",true); return; }
  setMsgAuth(msgRegistro,"Creando cuenta...");
  try {
    const u=await apiFetch("/usuarios",{method:"POST",body:JSON.stringify({nombre,email,password})});
    guardarSesion({identificador:u.identificador,nombre:u.nombre,email:u.email});
    $("#uNombre").value=""; $("#uEmail").value=""; $("#uPassword").value="";
    irAApp();
  } catch(e) { setMsgAuth(msgRegistro,errorMsg(e),true); }
}
btnCrearUsuario.addEventListener("click", doRegistro);
$("#uPassword").addEventListener("keydown", e=>{ if(e.key==="Enter") doRegistro(); });
btnLogout.addEventListener("click", cerrarSesion);

/* ================================================================
   FILTROS
   ================================================================ */
function normalizaTexto(s) { return (s??"").toString().toLowerCase(); }

/** Una nota coincide con el filtro de tipo si tipo principal O secundario == filtro */
function matchTipo(nota, tipo) {
  if (!tipo) return true;
  const t1 = nota?.metadato?.tipo ?? "";
  const t2 = nota?.metadato?.tipo_secundario ?? "";
  return tipo === t1 || tipo === t2;
}

function sortByPriority(notas) {
  return [...notas].sort((a,b)=>{
    const pa=PRIORITY_ORDER[a?.metadato?.prioridad??""]??3;
    const pb=PRIORITY_ORDER[b?.metadato?.prioridad??""]??3;
    return pa-pb;
  });
}

function aplicaFiltrosPendientes(notas) {
  const q    = normalizaTexto($("#buscador").value);
  const tipo = $("#filtroTipo").value;
  const prio = $("#filtroPrioridad").value;
  return sortByPriority(notas.filter(n=>{
    if (n?.procesada) return false;
    const hayTipo  = matchTipo(n, tipo);
    const hayPrio  = !prio || n?.metadato?.prioridad===prio;
    const hayQuery = !q || [n?.descripcion, n?.metadato?.autor, n?.metadato?.tipo, n?.metadato?.tipo_secundario]
      .some(v=>normalizaTexto(v).includes(q));
    return hayTipo && hayPrio && hayQuery;
  }));
}

function aplicaFiltrosProcesadas(notas) {
  const q    = normalizaTexto($("#buscadorProcesadas").value);
  const tipo = $("#filtroTipoProcesadas").value;
  const prio = $("#filtroPrioridadProcesadas").value;
  return sortByPriority(notas.filter(n=>{
    if (!n?.procesada) return false;
    const hayTipo  = matchTipo(n, tipo);
    const hayPrio  = !prio || n?.metadato?.prioridad===prio;
    const hayQuery = !q || [n?.descripcion, n?.metadato?.autor, n?.metadato?.tipo, n?.metadato?.tipo_secundario]
      .some(v=>normalizaTexto(v).includes(q));
    return hayTipo && hayPrio && hayQuery;
  }));
}

function toNiceDate(d) { try { return new Date(d).toLocaleString(); } catch { return String(d); } }
function escapeHtml(str) {
  return String(str??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

/* ================================================================
   CREAR ITEM NOTA
   ================================================================ */
function crearItemNota(n, isProcesada) {
  const tipo  = n?.metadato?.tipo ?? "otras";
  const tipo2 = n?.metadato?.tipo_secundario ?? null;
  const icon  = CATEGORY_ICONS[tipo]  ?? "•";
  const color = CATEGORY_COLORS[tipo] ?? "rgba(148,163,184,.18)";

  const item = document.createElement("div");
  item.className = "item"+(isProcesada?" item-procesada":"");

  const top = document.createElement("div");
  top.className = "itemTop";

  const title = document.createElement("div");
  title.className = "itemTitle";

  const desc = document.createElement("div");
  desc.className = "desc";
  desc.textContent = n.descripcion ?? "";

  const meta = document.createElement("div");
  meta.className = "meta";

  // Badge categoría principal
  const badgeTipo = document.createElement("span");
  badgeTipo.className = "pill pill-tipo";
  badgeTipo.style.background  = color;
  badgeTipo.style.borderColor = color.replace(".18",".45");
  badgeTipo.style.color       = "rgba(255,255,255,.9)";
  badgeTipo.textContent       = icon+" "+tipo;
  meta.appendChild(badgeTipo);

  // Badge categoría secundaria (doble categoría: audios+X, links+X)
  if (tipo2 && tipo2 !== tipo) {
    const icon2  = CATEGORY_ICONS[tipo2] ?? "•";
    const color2 = CATEGORY_COLORS[tipo2] ?? "rgba(148,163,184,.18)";
    const badge2 = document.createElement("span");
    badge2.className = "pill pill-tipo";
    badge2.style.background  = color2;
    badge2.style.borderColor = color2.replace(".18",".45");
    badge2.style.color       = "rgba(255,255,255,.9)";
    badge2.textContent       = icon2+" "+tipo2;
    meta.appendChild(badge2);
  }

  // Prioridad
  if (n?.metadato?.prioridad) {
    const prio = n.metadato.prioridad;
    const prioBadge = document.createElement("span");
    prioBadge.className = "pill pill-prio pill-prio-"+prio;
    prioBadge.textContent = (PRIORITY_ICONS[prio]??"")+" "+prio;
    meta.appendChild(prioBadge);
  }

  const extraPills = [
    n?.metadato?.autor ? "autor: "+n.metadato.autor : null,
    "fecha: "+toNiceDate(n.fecha),
  ].filter(Boolean);
  for (const t of extraPills) {
    const p=document.createElement("span"); p.className="pill"; p.textContent=t; meta.appendChild(p);
  }

  if (n?.metadato?.ia_motivo && !isProcesada) {
    const motivo=document.createElement("span"); motivo.className="pill pill-ia";
    motivo.textContent="IA: "+n.metadato.ia_motivo; meta.appendChild(motivo);
  }
  if (isProcesada) {
    const lock=document.createElement("span"); lock.className="pill pill-lock";
    lock.textContent="🔒 procesada"; meta.appendChild(lock);
  }

  title.append(desc,meta);

  // Botones
  const btnWrap=document.createElement("div"); btnWrap.className="btn-actions";

  if (!isProcesada) {
    const btnProcesar=document.createElement("button"); btnProcesar.className="btn-procesar";
    btnProcesar.innerHTML=`<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg> Procesar`;
    btnProcesar.addEventListener("click",()=>abrirModalProcesar(n));
    btnWrap.appendChild(btnProcesar);
  }

  const btnBorrar=document.createElement("button"); btnBorrar.className="danger";
  btnBorrar.textContent="Borrar";
  btnBorrar.addEventListener("click",async()=>{
    if (!confirm("¿Borrar esta nota?")) return;
    try {
      await apiFetch("/notas/"+encodeURIComponent(n.identificador),{method:"DELETE"});
      setMsg("Nota eliminada."); await cargarNotas();
    } catch(e) { setMsg(e.message,true); }
  });
  btnWrap.appendChild(btnBorrar);
  top.append(title,btnWrap);
  item.append(top);

  // Reproductor de audio / enlace PDF / indicador TXT
  const archivo      = n?.metadato?.archivo;
  const archivoTipoN = n?.metadato?.archivo_tipo||"";
  if (archivo) {
    const esAudio = archivoTipoN.startsWith("audio/") || /\.(mp3|wav|ogg|m4a|webm)$/i.test(archivo);
    const esPDF   = archivoTipoN==="application/pdf" || /\.pdf$/i.test(archivo);
    const esTxt   = archivoTipoN==="text/plain" || /\.txt$/i.test(archivo);
    if (esAudio) {
      const player=document.createElement("audio");
      player.controls=true; player.className="audio-player";
      player.src=API_BASE+"/uploads/"+encodeURIComponent(archivo);
      item.append(player);
    } else if (esPDF) {
      const pdfLink=document.createElement("a");
      pdfLink.href=API_BASE+"/uploads/"+encodeURIComponent(archivo);
      pdfLink.target="_blank"; pdfLink.rel="noopener noreferrer";
      pdfLink.className="pdf-link";
      pdfLink.innerHTML=`<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> Abrir PDF`;
      item.append(pdfLink);
    } else if (esTxt) {
      const txtLink=document.createElement("a");
      txtLink.href=API_BASE+"/uploads/"+encodeURIComponent(archivo);
      txtLink.target="_blank"; txtLink.rel="noopener noreferrer";
      txtLink.className="pdf-link";
      txtLink.innerHTML=`📄 Ver archivo TXT`;
      item.append(txtLink);
    }
  }

  // Botón resumen (solo procesadas)
  if (isProcesada) {
    const resumenWrap=document.createElement("div"); resumenWrap.className="resumen-wrap";
    const btnResumen=document.createElement("button"); btnResumen.className="btn-resumen";
    btnResumen.innerHTML=`<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Ver resumen`;
    btnResumen.dataset.open="false";
    const resumenBody=document.createElement("div"); resumenBody.className="resumen-body"; resumenBody.style.display="none";

    btnResumen.addEventListener("click",async()=>{
      const isOpen=btnResumen.dataset.open==="true";
      if (isOpen) {
        resumenBody.style.display="none"; btnResumen.dataset.open="false";
        btnResumen.innerHTML=`<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Ver resumen`;
        return;
      }
      if (!resumenBody.dataset.loaded) {
        resumenBody.style.display="block"; btnResumen.dataset.open="true";
        btnResumen.innerHTML=`... Ocultar resumen`;
        resumenBody.innerHTML=`<div class="resumen-loading"><span class="resumen-spinner"></span> Generando resumen con IA...</div>`;
        try {
          const data=await apiFetch("/notas/"+encodeURIComponent(n.identificador)+"/resumen");
          resumenBody.dataset.loaded="true";
          let html=`<p class="resumen-text">${escapeHtml(data.resumen)}</p>`;
          if (data.puntos_clave&&data.puntos_clave.length>0) {
            html+=`<div class="resumen-puntos-label">Puntos clave</div><ul class="resumen-puntos">`;
            for (const p of data.puntos_clave) html+=`<li>${escapeHtml(p)}</li>`;
            html+=`</ul>`;
          }
          resumenBody.innerHTML=html;
        } catch(e) { resumenBody.innerHTML=`<p class="resumen-error">${escapeHtml(e.message)}</p>`; }
      } else {
        resumenBody.style.display="block"; btnResumen.dataset.open="true";
        btnResumen.innerHTML=`... Ocultar resumen`;
      }
    });
    resumenWrap.append(btnResumen,resumenBody);
    item.append(resumenWrap);
  }

  return item;
}

/* ================================================================
   RENDER
   ================================================================ */
function renderNotas() {
  const pendientes=aplicaFiltrosPendientes(cacheNotas);
  const procesadas=aplicaFiltrosProcesadas(cacheNotas);
  const listaPend=$("#listaPendientes");
  const listaPro=$("#listaProcesadas");
  $("#contadorPendientes").textContent=String(pendientes.length);
  $("#contadorProcesadas").textContent=String(procesadas.length);
  listaPend.innerHTML=""; listaPro.innerHTML="";

  if (pendientes.length===0) {
    const e=document.createElement("div");
    e.style.cssText="color:rgba(255,255,255,.3);font-size:13px;padding:12px 0;";
    e.textContent="No hay notas pendientes."; listaPend.appendChild(e);
  } else { for (const n of pendientes) listaPend.append(crearItemNota(n,false)); }

  if (procesadas.length===0) {
    const e=document.createElement("div");
    e.style.cssText="color:rgba(255,255,255,.3);font-size:13px;padding:12px 0;";
    e.textContent="Aún no hay notas procesadas."; listaPro.appendChild(e);
  } else { for (const n of procesadas) listaPro.append(crearItemNota(n,true)); }
}

async function cargarNotas() {
  if (!usuarioActivo?.identificador) return;
  const msgEl=$("#msg"); msgEl.textContent="Cargando..."; msgEl.style.color="rgba(255,255,255,.45)";
  try {
    const notas=await apiFetch("/usuarios/"+encodeURIComponent(usuarioActivo.identificador)+"/notas");
    cacheNotas=Array.isArray(notas)?notas:[];
    const nPend=cacheNotas.filter(n=>!n.procesada).length;
    const nProc=cacheNotas.filter(n=> n.procesada).length;
    setMsg(nPend+" pendiente"+(nPend!==1?"s":"")+" · "+nProc+" procesada"+(nProc!==1?"s":"")+".");
    renderNotas();
  } catch(e) { setMsg(errorMsg(e),true); }
}

["#buscador","#filtroTipo","#filtroPrioridad",
 "#buscadorProcesadas","#filtroTipoProcesadas","#filtroPrioridadProcesadas"]
  .forEach(sel => {
    const el=$(sel);
    if (el) el.addEventListener(sel.includes("busca")?"input":"change", renderNotas);
  });
$("#btnRecargar").addEventListener("click", cargarNotas);

/* ================================================================
   MODAL PROCESAR
   ================================================================ */
let notaEnModal=null;

function abrirModalProcesar(n) {
  notaEnModal=n;
  $("#modalDescripcion").textContent=n.descripcion??"";
  $("#modalIaMotivo").textContent=n?.metadato?.ia_motivo
    ?"IA: "+n.metadato.ia_motivo+" (confianza "+Math.round((n.metadato.ia_confianza??0)*100)+"%)"
    :"Sin motivo IA";
  $("#modalCategoria").value=n?.metadato?.tipo??"otras";
  $("#modalPrioridad").value=n?.metadato?.prioridad??"";
  $("#modalMsg").textContent="";
  $("#modalProcesar").style.display="flex";
}

function cerrarModal() { $("#modalProcesar").style.display="none"; notaEnModal=null; }
$("#modalCerrar").addEventListener("click", cerrarModal);
$("#modalProcesar").addEventListener("click", e=>{ if (e.target===e.currentTarget) cerrarModal(); });
$("#btnAceptarIA").addEventListener("click",()=>{
  if (notaEnModal) {
    $("#modalCategoria").value=notaEnModal?.metadato?.tipo??"otras";
    $("#modalPrioridad").value=notaEnModal?.metadato?.prioridad??"";
  }
});
$("#btnConfirmarProcesar").addEventListener("click",async()=>{
  if (!notaEnModal) return;
  const msgEl=$("#modalMsg");
  msgEl.textContent="Procesando..."; msgEl.style.color="rgba(255,255,255,.45)";
  try {
    await apiFetch("/notas/"+encodeURIComponent(notaEnModal.identificador),{
      method:"PATCH",
      body:JSON.stringify({procesada:true, tipo:$("#modalCategoria").value, prioridad:$("#modalPrioridad").value||null}),
    });
    cerrarModal(); setMsg("✓ Nota procesada y bloqueada."); await cargarNotas();
  } catch(e) { msgEl.textContent=e.message; msgEl.style.color="rgba(224,92,115,.9)"; }
});

/* ================================================================
   CREAR NOTA
   ================================================================ */
form.addEventListener("submit", async(e)=>{
  e.preventDefault();
  if (!usuarioActivo?.identificador) { setMsg("Inicia sesión primero.",true); return; }

  const descripcion=$("#descripcion").value.trim();
  if (!descripcion && !archivoSeleccionado) { setMsg("Escribe una descripción o adjunta un archivo.",true); return; }

  const prioridad=$("#prioridad").value||null;
  const autor=$("#autor").value.trim()||null;

  if (archivoSeleccionado) {
    setMsg("⏳ Subiendo y procesando archivo...");
    const fd=new FormData();
    fd.append("usuario_id", usuarioActivo.identificador);
    fd.append("descripcion", descripcion);
    if (autor) fd.append("autor", autor);
    if (prioridad) fd.append("prioridad", prioridad);
    fd.append("archivo", archivoSeleccionado);
    try {
      const res=await fetch(API_BASE+"/notas/upload",{method:"POST",body:fd});
      if (!res.ok) { const d=await res.json().catch(()=>({})); throw new Error(d?.detail||"Error al subir archivo"); }
      $("#descripcion").value=""; $("#prioridad").value=""; $("#autor").value="";
      quitarArchivo(); setMsg("✓ Archivo procesado y nota creada."); await cargarNotas();
    } catch(e) { setMsg(errorMsg(e),true); }
  } else {
    setMsg("⏳ Clasificando con IA...");
    try {
      await apiFetch("/notas",{method:"POST",body:JSON.stringify({
        usuario_id:usuarioActivo.identificador, descripcion,
        metadato:{tipo:"otras",autor,prioridad},
      })});
      $("#descripcion").value=""; $("#prioridad").value=""; $("#autor").value="";
      setMsg("✓ Nota creada y clasificada."); await cargarNotas();
    } catch(e) { setMsg(errorMsg(e),true); }
  }
});

/* ================================================================
   ADJUNTAR ARCHIVO
   ================================================================ */
const inputArchivo     = $("#inputArchivo");
const archivoPreview   = $("#archivoPreview");
const archivoNombre    = $("#archivoNombre");
const archivoTipoEl    = $("#archivoTipo");
const archivoIcono     = $("#archivoIcono");
const btnQuitarArchivo = $("#btnQuitarArchivo");

function mostrarPreviewArchivo(file) {
  archivoSeleccionado=file;
  archivoNombre.textContent=file.name;
  const esAudio=file.type.startsWith("audio/")||/\.(mp3|wav|ogg|m4a|webm)$/i.test(file.name);
  const esPDF=file.type==="application/pdf"||/\.pdf$/i.test(file.name);
  const esTxt=file.type==="text/plain"||/\.txt$/i.test(file.name);
  archivoIcono.textContent=esAudio?"🎙":esPDF?"📄":esTxt?"📝":"📎";
  archivoTipoEl.textContent=esAudio?"audio":esPDF?"pdf":esTxt?"txt":file.type;
  archivoPreview.style.display="flex";
}
function quitarArchivo() {
  archivoSeleccionado=null; inputArchivo.value="";
  archivoPreview.style.display="none";
}

$("#btnAdjuntar").addEventListener("click",()=>inputArchivo.click());
inputArchivo.addEventListener("change",()=>{ if(inputArchivo.files[0]) mostrarPreviewArchivo(inputArchivo.files[0]); });
btnQuitarArchivo.addEventListener("click", quitarArchivo);

/* ================================================================
   INIT
   ================================================================ */
(function(){
  const sesion=cargarSesion();
  if (sesion?.identificador) { usuarioActivo=sesion; irAApp(); }
  else { irAAuth(); wakeUpServer(); }
})();

}); // fin DOMContentLoaded