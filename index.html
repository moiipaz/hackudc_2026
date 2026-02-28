<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Notify</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="./style.css" />
</head>
<body>
  <div class="noise"></div>

  <!-- =============================================
       PÁGINA AUTH
       ============================================= -->
  <div id="pageAuth" class="page page-auth">
    <div class="auth-wrap">

      <div class="auth-brand">
        <h1>Notify<span class="dot">.</span></h1>
        <p class="muted">Tu espacio privado para gestionar ideas.</p>
      </div>

      <div class="auth-tabs">
        <button type="button" class="auth-tab active" id="tabLogin">Iniciar sesión</button>
        <button type="button" class="auth-tab" id="tabRegistro">Crear cuenta</button>
      </div>

      <div id="panelLogin" class="auth-panel">
        <label class="field">
          <span>Email</span>
          <input id="lEmail" type="email" placeholder="ana@email.com" autocomplete="email" />
        </label>
        <label class="field">
          <span>Contraseña</span>
          <input id="lPassword" type="password" placeholder="••••••••" autocomplete="current-password" />
        </label>
        <button type="button" id="btnLogin" class="btn-primary btn-full">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
          Iniciar sesión
        </button>
        <p id="msgLogin" class="msg" aria-live="polite"></p>
      </div>

      <div id="panelRegistro" class="auth-panel" style="display:none;">
        <label class="field">
          <span>Nombre</span>
          <input id="uNombre" type="text" placeholder="Ana García" autocomplete="name" />
        </label>
        <label class="field">
          <span>Email</span>
          <input id="uEmail" type="email" placeholder="ana@email.com" autocomplete="email" />
        </label>
        <label class="field">
          <span>Contraseña <em class="hint">mín. 6 caracteres</em></span>
          <input id="uPassword" type="password" placeholder="••••••••" autocomplete="new-password" />
        </label>
        <button type="button" id="btnCrearUsuario" class="btn-primary btn-full">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg>
          Crear cuenta
        </button>
        <p id="msgRegistro" class="msg" aria-live="polite"></p>
      </div>

      <p id="serverStatus" class="msg" style="text-align:center;margin-top:14px;min-height:18px;font-size:12px;"></p>
    </div>
  </div>

  <!-- =============================================
       PÁGINA APP
       ============================================= -->
  <div id="pageApp" class="page" style="display:none;">

    <header class="container">
      <div class="header-inner">
        <div>
          <h1>Notify<span class="dot">.</span></h1>
          <p class="muted">Tu espacio privado para gestionar ideas.</p>
        </div>
        <div class="header-right">
          <div class="header-badge" id="usuarioActivoBadge">Sin usuario</div>
          <button type="button" id="btnLogout" class="btn-ghost btn-sm">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            Salir
          </button>
        </div>
      </div>
    </header>

    <main class="container">
      <div class="grid">
        <section class="card">
          <div class="card-label">NUEVA NOTA</div>
          <form id="formNota" class="form">
            <label class="field">
              <span>Descripción</span>
              <textarea id="descripcion" placeholder="Escribe la nota..." required></textarea>
            </label>
            <div class="row">
              <label class="field">
                <span>Tipo</span>
                <select id="tipo" required>
                  <option value="personal">personal</option>
                  <option value="trabajo">trabajo</option>
                  <option value="estudio">estudio</option>
                </select>
              </label>
              <label class="field">
                <span>Prioridad <em class="hint">opcional</em></span>
                <input id="prioridad" type="number" min="1" max="5" step="1" placeholder="1 – 5" />
              </label>
            </div>
            <label class="field">
              <span>Autor <em class="hint">opcional</em></span>
              <input id="autor" type="text" placeholder="Tu nombre" />
            </label>
            <div class="btn-row">
              <button type="submit" class="btn-primary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Crear nota
              </button>
              <button type="button" id="btnRecargar" class="btn-ghost">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
                Recargar
              </button>
            </div>
            <p id="msg" class="msg" aria-live="polite"></p>
          </form>
        </section>

        <section class="card">
          <div class="card-header">
            <div class="card-label" style="margin-bottom:0;">MIS NOTAS</div>
            <div class="counter-badge" id="contador">0</div>
          </div>
          <div class="toolbar">
            <div class="search-wrap">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input id="buscador" type="search" placeholder="Buscar por texto, autor o tipo..." />
            </div>
            <select id="filtroTipo" class="filter-select">
              <option value="">Todos</option>
              <option value="personal">personal</option>
              <option value="trabajo">trabajo</option>
              <option value="estudio">estudio</option>
            </select>
          </div>
          <div id="lista" class="lista"></div>
        </section>
      </div>
    </main>

    <footer class="container footer">
      <span class="muted mono">Notify — Backend: FastAPI</span>
    </footer>

  </div>

  <script src="./app.js"></script>
</body>
</html>
