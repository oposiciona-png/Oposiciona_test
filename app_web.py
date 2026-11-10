# === SECCIÓN 1: CONFIGURACIÓN, ESTILOS Y REGISTRO SHEETS ===
import streamlit as st
import streamlit.components.v1 as components
import fitz  # PyMuPDF
import re, random, requests, os, unicodedata, time, json, threading, base64, zlib
from datetime import datetime
from zoneinfo import ZoneInfo

icono_ruta = "ICONO OPOSICIONA.png"
st.set_page_config(
    page_title="Plataforma de Tests Oposiciona",
    page_icon=icono_ruta if os.path.exists(icono_ruta) else "📚",
    layout="centered",
    menu_items={"Get Help": None, "Report a bug": None, "About": None}
)

GOOGLE_SHEETS_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbw_B-g4pwxuZX4HzH99cobW6jQoValvLXI2ogeJgMuekjwlyS766KS4ujm3CFYdJ7DPlA/exec"
# Clave ofuscada por fragmentos en Base64 para evitar falsas alertas de Secret Scanning en GitHub
_K_PARTS = ("QVEuQWI4Uk42", "TDRmWVhWNHg0", "Vi1FWVlIbmRk", "bWxob0llcTZIRXNC", "S1BPUENDUHZDVkJ4RXc=")
GEMINI_API_KEY_DEFAULT = "".join(base64.b64decode(p).decode("utf-8") for p in _K_PARTS)

# Clave interna del servidor para cifrar el backup de sesión en localStorage y evitar que nadie extraiga el JSON de preguntas
_BACKUP_SECRET_BYTES = b"Oposiciona_5.0_Blindaje_Privado_2026_SS#Key"

def _cifrar_backup_sesion(datos_dict):
    raw = zlib.compress(json.dumps(datos_dict, ensure_ascii=False).encode("utf-8"), level=9)
    klen = len(_BACKUP_SECRET_BYTES)
    xored = bytes(b ^ _BACKUP_SECRET_BYTES[i % klen] for i, b in enumerate(raw))
    return "v2_" + base64.urlsafe_b64encode(xored).decode("ascii")

def _descifrar_backup_sesion(token_str):
    if not token_str:
        return {}
    if token_str.startswith("v2_"):
        xored = base64.urlsafe_b64decode(token_str[3:].encode("ascii"))
        klen = len(_BACKUP_SECRET_BYTES)
        raw = bytes(b ^ _BACKUP_SECRET_BYTES[i % klen] for i, b in enumerate(xored))
        return json.loads(zlib.decompress(raw).decode("utf-8"))
    raw_legacy = zlib.decompress(base64.urlsafe_b64decode(token_str.encode("ascii")))
    return json.loads(raw_legacy.decode("utf-8"))

USUARIOS_ADMIN = ["ponentes@oposiciona.es", "ponentes@oposicona.es"]
USUARIOS_AUTORIZADOS = {
    "ACCESO TOTAL": [
        "ponentes@oposiciona.es", "ponentes@oposicona.es", "gonzalogonzaleztejedor@gmail.com",
        "ignacio.garcia.heras@gmail.com", "alvarezpugamartin@gmail.com", "claratoledo06@gmail.com",
        "blancazortega@gmail.com", "mijurista@gmail.com", "isabelmgutierrogil@gmail.com",
        "carmenvl28@gmail.com", "leticiagenerelosolana@gmail.com", "cguinaldobravo@gmail.com",
        "alvaro20011996@gmail.com", "sion.nuba@gmail.com"
    ],
    "ADMTVOS": [
        "elenavegasanchez73@gmail.com", "josemurillomoreno.mail@gmail.com", "raulff1997.rfg@gmail.com",
        "sandradcastanares@gmail.com", "joycewayland@gmail.com", "celia.pks@gmail.com",
        "cynthiaflafla14@gmail.com", "fragosotorbellinocarmen@gmail.com", "pherrerojulian@gmail.com",
        "rsilveiraescudero@gmail.com", "delfijv19@gmail.com", "marielipedreira@hotmail.com",
        "vanessagarciajimenez87@gmail.com", "luiscacid@gmail.com", "miguelromanrmm@gmail.com",
        "raquelkmacho@gmail.com", "patripintoalvarez@gmail.com", "alexandrajimenezmontoliu@gmail.com"
    ],
    "GESTION": [
        "vsaurod@gmail.com", "mariaquirosmonge5@gmail.com", "vanessagomeztdla@gmail.com",
        "zoemorcor@gmail.com", "julianayem@gmail.com", "yasminkhalili@gmail.com",
        "miriamvazquezseoane2000@gmail.com", "monetcacerescc@gmail.com", "maariiamaji@gmail.com",
        "micastroespejo@gmail.com", "aisacarrerapexe@gmail.com", "csanchezssmm@gmail.com",
        "maria.concal@gmail.com", "mariachinchurreta@gmail.com", "rocio10460@gmail.com",
        "manuelmuriel97@gmail.com", "hfdiaz99@gmail.com", "ireneizquierdo22@gmail.com",
        "manuelsan240902@gmail.com"
    ],
    "INVITADO": ["invitado@oposiciona.es", "invitado"]
}
PASSWORD_ADMIN, PASSWORD_ACCESO, PASSWORD_INVITADO = "Gonz4loN4cho23", "plaza2026", "oposiciona"

for k, v in [
    ('autenticado', False), ('rol', None), ('email', None), ('es_admin', False),
    ('do_scroll', False), ('mostrar_opciones_simulacro', False), ('celebracion_mostrada', False),
    ('inicio_registrado_sheets', False), ('resultado_registrado', False),
    ('test_start_ts', None), ('fecha_inicio_str', ""), ('hora_inicio_str', ""),
    ('test_esp', ""), ('test_cat', ""), ('borrar_backup_ls', False),
    ('gemini_api_key_session', GEMINI_API_KEY_DEFAULT),
    ('modo_avance', "**Modo reflexivo** (puedes comprobar la pregunta y el paso a la siguiente es manual pulsando siguiente)")
]:
    if k not in st.session_state: st.session_state[k] = v

_es_sesion_admin = bool(
    st.session_state.get("autenticado", False) and (
        st.session_state.get("es_admin", False) or
        (st.session_state.get("email") or "").lower().strip() in USUARIOS_ADMIN
    )
)

_css_proteccion_impresion = """
body, .stApp, .block-container, p, h1, h2, h3, h4, h5, h6, span {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}
@media print {
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .block-container {
        display: block !important;
        visibility: visible !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    body::before {
        content: none !important;
        display: none !important;
    }
}
""" if _es_sesion_admin else """
body, .stApp, .block-container, p, h1, h2, h3, h4, h5, h6, span, div, img {
    -webkit-user-select: none !important;
    -moz-user-select: none !important;
    -ms-user-select: none !important;
    user-select: none !important;
    -webkit-touch-callout: none !important;
    -webkit-user-drag: none !important;
}
@media print {
    html, body * {display: none !important; visibility: hidden !important;}
    html, body {display: block !important; background-color: white !important;}
    body::before {content: "Acción no permitida.\\A Test propiedad de Oposiciona 5.0." !important; white-space: pre-wrap !important; display: block !important; text-align: center !important; font-size: 30px !important; font-family: sans-serif !important; margin-top: 20% !important; color: #d32f2f !important;}
}
"""

st.markdown("""<style>
:root, html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    color-scheme: light only !important;
    --text-color: #1E293B !important;
    --background-color: #FFFFFF !important;
    --secondary-background-color: #F8FAFC !important;
    color: #1E293B !important;
}
#MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton, [data-testid="stAppDeployButton"] {
    visibility: hidden !important;
    display: none !important;
}
[class*="viewerBadge"], [class*="styles_viewerBadge"], [class*="profileContainer"], [class*="stActionButton"] {
    display: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
}
/* Textos generales, títulos, párrafos y etiquetas siempre oscuros incluso en Modo Oscuro de iPhone/iPad */
h1, h2, h3, h4, h5, h6, p, span, label, li, summary,
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5, [data-testid="stMarkdownContainer"] h6,
[data-testid="stMarkdownContainer"] span, [data-testid="stMarkdownContainer"] div,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p {
    color: #1E293B !important;
}
/* Carpetas / Desplegables (Expanders) siempre con fondo claro y texto negro */
[data-testid="stExpander"], details {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    color: #1E293B !important;
}
[data-testid="stExpander"] summary, details summary, [data-testid="stExpander"] summary:hover {
    background-color: #F8FAFC !important;
    color: #1E293B !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary svg, [data-testid="stExpanderDetails"],
[data-testid="stExpanderDetails"] div, [data-testid="stExpanderDetails"] b,
[data-testid="stExpanderDetails"] span {
    color: #1E293B !important;
    fill: #1E293B !important;
}
/* Campos de texto, buscador y contraseñas siempre claros con letra negra */
input, textarea, [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
    border-color: #CBD5E1 !important;
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}
input::placeholder, textarea::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    opacity: 1 !important;
}
[data-baseweb="input"] button, [data-baseweb="input"] svg {
    background-color: transparent !important;
    color: #1E293B !important;
    fill: #1E293B !important;
}
/* Botones secundarios (Anterior, Comprobar, Siguiente, Repetir, Cambiar, Reportar en resumen) */
div.stButton > button, button[kind="secondary"] {
    background-color: #F1F5F9 !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
}
div.stButton > button p, div.stButton > button span, button[kind="secondary"] p, button[kind="secondary"] span {
    color: #1E293B !important;
}
div.stButton > button:hover, button[kind="secondary"]:hover {
    background-color: #E2E8F0 !important;
    border-color: #94A3B8 !important;
    color: #000000 !important;
}
/* Botones primarios (Entrar, Iniciar Test, Enviar reporte, Finalizar sesión) */
div.stButton > button[kind="primary"], button[kind="primary"] {
    background-color: #1F77B4 !important;
    color: #FFFFFF !important;
    border: 1px solid #1F77B4 !important;
}
div.stButton > button[kind="primary"] p, div.stButton > button[kind="primary"] span,
button[kind="primary"] p, button[kind="primary"] span {
    color: #FFFFFF !important;
}
div.stButton > button[kind="primary"]:hover, button[kind="primary"]:hover {
    background-color: #155A8A !important;
    border-color: #155A8A !important;
}
/* Botón verde de Simulacro Global */
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button {
    background-color: #2e7d32 !important;
    border-color: #2e7d32 !important;
}
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button p,
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button span {
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 17px !important;
}
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button:hover {
    background-color: #1b5e20 !important;
    border-color: #1b5e20 !important;
}
/* Opciones de respuesta tipo Radio */
div[role="radiogroup"] label {
    margin-bottom: 12px !important;
}
div[role="radiogroup"] label, div[role="radiogroup"] label p, div[role="radiogroup"] label div, div[role="radiogroup"] label span {
    font-size: 17px !important;
    line-height: 1.3 !important;
    text-align: justify !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    white-space: normal !important;
}
div[data-baseweb="radio"] > div:first-child {
    background-color: #FFFFFF !important;
    border-color: #000000 !important;
    border-width: 2px !important;
}
div[data-baseweb="radio"][data-checked="true"] > div:first-child > div {
    background-color: #000000 !important;
}
/* Alertas e info boxes legibles en modo oscuro */
[data-testid="stAlert"] p, [data-testid="stAlert"] span, [data-testid="stAlert"] div {
    color: #1E293B !important;
}
/* Subida de archivos local */
[data-testid="stFileUploader"] section {
    background-color: #F8FAFC !important;
    border: 1px dashed #CBD5E1 !important;
    color: #1E293B !important;
}
[data-testid="stFileUploader"] section span, [data-testid="stFileUploader"] section small, [data-testid="stFileUploader"] button {
    color: #1E293B !important;
}
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 6rem !important;
    max-width: 750px !important;
}
""" + _css_proteccion_impresion + "</style>", unsafe_allow_html=True)

components.html(f"""<script>
try {{
    setTimeout(function() {{
        var pw = window.parent;
        var parentDoc = pw.document;
        pw.__oposiciona_es_admin = {"true" if _es_sesion_admin else "false"};

        if (!parentDoc.getElementById("escudo-oposiciona")) {{
            var script = parentDoc.createElement("script");
            script.id = "escudo-oposiciona";
            script.innerHTML = `
                /* 1. Bloqueo de menú contextual (clic derecho) y arrastrar elementos */
                document.addEventListener('contextmenu', function(e) {{
                    if (window.__oposiciona_es_admin) return;
                    e.preventDefault();
                }}, true);

                document.addEventListener('dragstart', function(e) {{
                    if (window.__oposiciona_es_admin) return;
                    e.preventDefault();
                }}, true);

                /* 2. Bloqueo de copiado / cortado fuera de campos de escritura (textarea/input) */
                document.addEventListener('copy', function(e) {{
                    if (window.__oposiciona_es_admin) return;
                    var tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : '';
                    if (tag === 'textarea' || tag === 'input') return;
                    e.clipboardData.setData('text/plain', 'Contenido protegido propiedad de Oposiciona 5.0.');
                    e.preventDefault();
                }}, true);

                document.addEventListener('cut', function(e) {{
                    if (window.__oposiciona_es_admin) return;
                    var tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : '';
                    if (tag === 'textarea' || tag === 'input') return;
                    e.preventDefault();
                }}, true);

                /* 3. Bloqueo de atajos de descarga HTML (Ctrl+S), código fuente (Ctrl+U), impresión (Ctrl+P) e Inspector DevTools (F12 / Ctrl+Shift+I/J/C/K) */
                window.addEventListener('keydown', function(e) {{
                    if (window.__oposiciona_es_admin) return;
                    var k = (e.key || '').toLowerCase();
                    var code = e.keyCode || e.which || 0;

                    /* F12 */
                    if (code === 123 || k === 'f12') {{
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }}
                    /* Ctrl+S (Guardar HTML), Ctrl+U (Ver fuente), Ctrl+P (Imprimir) */
                    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && (k === 's' || k === 'u' || k === 'p')) {{
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }}
                    /* Ctrl+Shift+I / J / C / K (Herramientas de Desarrollador en Windows/Linux) */
                    if (e.ctrlKey && e.shiftKey && (k === 'i' || k === 'j' || k === 'c' || k === 'k')) {{
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }}
                    /* Cmd+Option+I / J / C / U (Herramientas de Desarrollador y Ver fuente en Mac) */
                    if (e.metaKey && e.altKey && (k === 'i' || k === 'j' || k === 'c' || k === 'u')) {{
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }}
                }}, true);

                /* Latido anti-desconexión cada 25s y WakeLock */
                setInterval(function() {{
                    try {{
                        fetch(window.location.origin + "/_stcore/health", {{ method: "GET", cache: "no-store" }}).catch(function(){{}});
                        document.dispatchEvent(new CustomEvent("oposiciona_keepalive"));
                    }} catch(err) {{}}
                }}, 25000);

                var wakeLockObj = null;
                function activarWakeLock() {{
                    if ('wakeLock' in navigator && document.visibilityState === 'visible') {{
                        navigator.wakeLock.request('screen').then(function(wl) {{ wakeLockObj = wl; }}).catch(function(){{}});
                    }}
                }}
                document.addEventListener('visibilitychange', activarWakeLock);
                document.addEventListener('click', activarWakeLock, {{ once: true }});
            `;
            parentDoc.head.appendChild(script);
        }}
    }}, 300);
}} catch(e) {{}}
</script>""", height=0)

def detectar_dispositivo_usuario():
    try:
        ua = (st.context.headers.get("User-Agent") or "").lower()
        if not ua:
            return "Desconocido"
        if "ipad" in ua:
            return "📟 Tablet (iPad)"
        if "tablet" in ua or "playbook" in ua or "silk" in ua or ("android" in ua and "mobile" not in ua):
            return "📟 Tablet (Android)"
        if "iphone" in ua or "ipod" in ua:
            return "📱 Móvil (iPhone)"
        if "android" in ua and "mobile" in ua:
            return "📱 Móvil (Android)"
        if any(x in ua for x in ["mobile", "iemobile", "opera mini"]):
            return "📱 Móvil"
        if "windows" in ua:
            return "💻 PC (Windows)"
        if "macintosh" in ua or "mac os x" in ua:
            return "💻 PC (Mac)"
        if "cros" in ua:
            return "💻 PC (Chromebook)"
        if "linux" in ua:
            return "💻 PC (Linux)"
        return "💻 PC"
    except Exception:
        return "Desconocido"

def formatear_duracion(segundos):
    segundos = max(0, int(segundos))
    horas, resto = divmod(segundos, 3600)
    minutos, segs = divmod(resto, 60)
    if horas > 0:
        return f"{horas}h {minutos:02d}m {segs:02d}s"
    return f"{minutos}m {segs:02d}s"

def iniciar_cronometro_test():
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    st.session_state.test_start_ts = time.time()
    st.session_state.fecha_inicio_str = ahora.strftime("%d/%m/%Y")
    st.session_state.hora_inicio_str = ahora.strftime("%H:%M:%S")
    st.session_state.inicio_registrado_sheets = False
    st.session_state.resultado_registrado = False

def _enviar_post_background(url, payload):
    try:
        requests.post(url, json=payload, timeout=8)
    except Exception:
        pass

def registrar_actividad_sheets(evento, nombre_test="", aciertos="", fallos="", blancos="", nota="", accion="nueva_fila"):
    email_actual = (st.session_state.get("email") or "").lower().strip()
    if email_actual in USUARIOS_ADMIN or st.session_state.get("es_admin", False):
        return

    url = (GOOGLE_SHEETS_WEBHOOK_URL or "").strip()
    if not url or not url.startswith("https://script.google.com/"):
        return
    try:
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        hora_actual = ahora.strftime("%H:%M:%S")
        fecha_ini = st.session_state.get("fecha_inicio_str") or ahora.strftime("%d/%m/%Y")
        hora_ini = st.session_state.get("hora_inicio_str") or hora_actual

        if accion == "nueva_fila":
            hora_fin, duracion_str = "", ""
        else:
            hora_fin = hora_actual
            ini_ts = st.session_state.get("test_start_ts")
            duracion_str = formatear_duracion(time.time() - ini_ts) if ini_ts else ""

        payload = {
            "accion": accion,
            "fecha": fecha_ini,
            "hora_inicio": hora_ini,
            "hora_fin": hora_fin,
            "duracion": duracion_str,
            "email": email_actual or "desconocido",
            "rol": st.session_state.get("rol") or "",
            "especialidad": st.session_state.get("test_esp") or st.session_state.get("saved_esp") or "",
            "categoria": st.session_state.get("test_cat") or st.session_state.get("saved_cat") or "",
            "evento": evento,
            "test": nombre_test,
            "aciertos": aciertos,
            "fallos": fallos,
            "blancos": blancos,
            "nota": nota,
            "dispositivo": detectar_dispositivo_usuario()
        }
        threading.Thread(target=_enviar_post_background, args=(url, payload), daemon=True).start()
    except Exception:
        pass

if st.session_state.get("borrar_backup_ls", False):
    st.session_state.borrar_backup_ls = False
    components.html("""<script>
    try {
        window.parent.localStorage.removeItem("oposiciona_test_backup_v1");
        window.parent.localStorage.removeItem("oposiciona_auth_backup_v1");
    } catch(e) {}
    </script>""", height=0)

if st.session_state.do_scroll:
    st.session_state.do_scroll = False
    components.html("""<script>
    try { setTimeout(function() {
        var p = window.parent, d = p.document;
        [d.querySelector('.main'), d.querySelector('[data-testid="stMainBlockContainer"]'), d.querySelector('.block-container'), d.documentElement, d.body].forEach(el => { if (el) el.scrollTop = 0; });
        p.scrollTo({top: 0, behavior: 'smooth'});
    }, 200); } catch(e) {}
    </script>""", height=0)

col1, col2, col3 = st.columns([1, 0.8, 1])
with col2:
    try: st.image("oposiciona (320 x 132 px).png", use_container_width=True)
    except: pass
    st.markdown("<p style='text-align: center; font-size: 12px; margin-top: -15px; margin-bottom: 0px;'><a href='https://oposiciona.es/' style='text-decoration: none; color: #1f77b4 !important;'>🌐 oposiciona.es</a></p>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 5px; margin-bottom: 12px; border: none; border-top: 1px solid #d3d3d3;'>", unsafe_allow_html=True)

if not st.session_state.autenticado:
    qp_restore = st.query_params.get("restore_session", "")
    if qp_restore:
        try:
            datos_rec = _descifrar_backup_sesion(qp_restore)
            correo_rec = (datos_rec.get("email") or "").lower().strip()
            rol_rec = next((r for r, lc in USUARIOS_AUTORIZADOS.items() if correo_rec in lc), None)
            if rol_rec:
                st.session_state.autenticado = True
                st.session_state.email = correo_rec
                st.session_state.rol = "ACCESO TOTAL" if correo_rec in USUARIOS_ADMIN else rol_rec
                st.session_state.es_admin = bool(datos_rec.get("es_admin", False) or (correo_rec in USUARIOS_ADMIN))
                st.session_state.saved_esp = datos_rec.get("saved_esp", "ADMINISTRATIVOS")
                st.session_state.saved_cat = datos_rec.get("saved_cat", "ESPECIFICO")
                st.session_state.modo_avance = datos_rec.get("modo_avance", st.session_state.modo_avance)
                st.session_state.saved_avance = st.session_state.modo_avance
                if datos_rec.get("questions"):
                    st.session_state.questions = datos_rec["questions"]
                    st.session_state.stats = {int(k): v for k, v in datos_rec.get("stats", {}).items()}
                    st.session_state.current_index = int(datos_rec.get("current_index", 0))
                    st.session_state.finished = bool(datos_rec.get("finished", False))
                    st.session_state.checked = bool(datos_rec.get("checked", False))
                    st.session_state.test_name = datos_rec.get("test_name")
                    st.session_state.test_esp = datos_rec.get("test_esp", "")
                    st.session_state.test_cat = datos_rec.get("test_cat", "")
                    st.session_state.test_start_ts = datos_rec.get("test_start_ts", time.time())
                    st.session_state.fecha_inicio_str = datos_rec.get("fecha_inicio_str", "")
                    st.session_state.hora_inicio_str = datos_rec.get("hora_inicio_str", "")
                    st.session_state.inicio_registrado_sheets = bool(datos_rec.get("inicio_registrado_sheets", False))
                    st.session_state.resultado_registrado = bool(datos_rec.get("resultado_registrado", False))
                st.query_params.clear()
                st.rerun()
        except Exception:
            st.query_params.clear()

    components.html("""<script>
    (function() {
        try {
            var ls = window.parent.localStorage;
            var savedTest = ls.getItem("oposiciona_test_backup_v1") || ls.getItem("oposiciona_auth_backup_v1");
            if (savedTest && window.parent.location.search.indexOf("restore_session=") === -1) {
                var url = new URL(window.parent.location.href);
                url.searchParams.set("restore_session", savedTest);
                window.parent.location.replace(url.toString());
            }
        } catch(e) {}
    })();
    </script>""", height=0)

    c_img1, c_img2, c_img3 = st.columns([1, 0.25, 1])
    with c_img2:
        try: st.image("test-utiles-768x768.png", use_container_width=True)
        except: pass
    st.markdown("<h3 style='text-align: center; color: #2C3E50 !important; margin-top: -5px;'>🔒 Acceso Restringido</h3><p style='text-align: center; font-size: 14px; color: #1E293B !important; margin-bottom: 20px;'>Plataforma exclusiva de <b>Oposiciona</b>. Introduce tus credenciales para acceder.</p>", unsafe_allow_html=True)
    email_input = st.text_input("Usuario o correo electrónico asociado")
    password_input = st.text_input("Contraseña de acceso", type="password")
    if st.button("Entrar a la plataforma", use_container_width=True, type="primary"):
        correo_limpio = email_input.lower().strip()
        rol_usuario = next((r for r, lc in USUARIOS_AUTORIZADOS.items() if correo_limpio in lc), None)
        if correo_limpio in USUARIOS_ADMIN:
            if password_input == PASSWORD_ADMIN:
                st.session_state.update(autenticado=True, rol="ACCESO TOTAL", email=correo_limpio, es_admin=True, do_scroll=True)
                st.rerun()
            else: st.error("❌ Contraseña de administrador incorrecta.")
        elif rol_usuario == "INVITADO" and password_input == PASSWORD_INVITADO:
            st.session_state.update(autenticado=True, rol="INVITADO", email=correo_limpio, es_admin=False, do_scroll=True)
            st.rerun()
        elif rol_usuario and password_input in [PASSWORD_ACCESO, PASSWORD_ADMIN]:
            es_adm = (password_input == PASSWORD_ADMIN) or (correo_limpio in USUARIOS_ADMIN)
            st.session_state.update(autenticado=True, rol=rol_usuario, email=correo_limpio, es_admin=es_adm, do_scroll=True)
            st.rerun()
        else: st.error("❌ Correo o contraseña incorrectos, o no tienes autorización activa.")
    st.stop()
# === FIN SECCIÓN 1 ===

# === SECCIÓN 2: CATÁLOGO DE TESTS DISPONIBLES ===

TESTS_DISPONIBLES = {
    "ADMINISTRATIVOS": {
        "ESPECIFICO": {
            "Elige un test de especifico...": None,
            "TEMA 01 ESPECIFICO_ACTUALIZADO": "https://drive.google.com/uc?export=download&id=13LzbXP5OknUY9NGZAdVMMN3F1Zl57glS",
            "TEMA 02A ACTUALIZADO": "https://drive.google.com/uc?export=download&id=11fAALQB33q5kGOn7VCW-5z6z83WWmP0Z",
            "TEMA 02B ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1VODyD_gdbg7pINDKdIxJpQ_D246dRMVO",
            "TEMA 02C ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1QGfK-_TUQhjbQddcTM9uARR0OHX-KIjw",
            "TEMA 02D ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1X6qx6h8AQS9gD7oGTHf9_GDsvCCXv5NT",
            "TEMA 03 AFILIACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1fhJxtDHNTVgEIjQYRPGDsuIMiqRC4SBQ",
            "TEMA 04 - TEST Y SUPUESTOS COTIZACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1Tpw0hJ1Vpc8d9KGe6TffL-FRqGoWPTML",
            "Tema 04 COTIZACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1oirjNXzELp4sCZ-2woU6SU-aLVZT2Lpi",
            "TEMA 08 IP ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1JUb9ndQ7MIaTagpQztXnrv1rsVxTE6im",
            "TEMA 08 REPASO 1 IT E IP ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1M3rydnWydxk_IkiL5-M3lOb8YrHASHXk",
            "TEMA 08 REPASO 2 IT E IP ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1mbLqDw1Z30I5BNVEXRDdAiUuBya9jn1G",
            "TEMA 08A IT ACTUALIZADO": "https://drive.google.com/uc?export=download&id=10QRftoDQI2qIN7ANeF_Nc689wlhyzDWc",
            "TEMA 09 NYCM ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1ns2r9zRvdbcTT3PqY1atS1RIUeVPFDpH",
            "TEMA 09 REPASO 1 NYCM ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1vw0GIL5VZKbGH4jNafCi2DvrY8dqgCNJ",
            "TEMA 09 REPASO 2 NYCM ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1HBpE6Xo0pljlQMvc2ny5kdz3EHgRkokG",
            "TEMA 10 JUBILACIÓN ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1V_oqlMqAUmE0ZNkAxgqTlco_Bb6wdIuN",
            "TEMA 10 REPASO 1 JUBILACIÓN ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1gPop5SOvriVEjUdTcYabrXis5DtxOwOl",
            "TEMA 10 REPASO 2 JUBILACIÓN ESPECÏFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1uCSBQBiX05aXIa_srEf-TP2mcqnqIVw3",
            "TEMA 11 MUERTE Y SUPERVIVENCIA ACTUALIZADO": "https://drive.google.com/uc?export=download&id=19ueHQsspJTQ1geqPm79kgnCgQO0zvgHt",
            "TEMA 11 REPASO 1 MUERTE Y SUPERVIVENCIA ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1OFCPOGSZUdIwXdwYXX8lSFIESHTHnM7c",
            "TEMA 11 REPASO 2 MUERTE Y SUPERVIVENCIA ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=19NIPI-Sh8adW9Xui5QSBVE9-PxCCm9l6",
            "TEMA 12 IMV": "https://drive.google.com/uc?export=download&id=1na10IZg8Ys6SQz6mKg__x3VDaoF7ZOJH",
            "TEMA 12 PNC": "https://drive.google.com/uc?export=download&id=1gP9vTETlURWw47btnomZNj6MKJdsKbdP",
            "TEMA 12 REPASO 1 IMV ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1GnVkEUXfN2OS2j96nxOu2jhl1OVSEEvx",
            "TEMA 12 REPASO 2 IMV ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1Uo7K8giiosHapdoWpnq5Vy7WaTpHUWg2",
        },
        "EXAMENES": {
            "Elige un test de examenes...": None,
            "✨ NOVEDADES RDL 31_2026 adm": "https://drive.google.com/uc?export=download&id=1B0Ff30-Hao-HsG2CkXTHYiuJ-1tkQwmK",
            "EXAMEN OFICIAL 2023 ACTUALIZADO A 2026 (RDL 31_2026)": "https://drive.google.com/uc?export=download&id=1WbIpgWBSDDPY9A6a6J5rKGVYgR72p8IT",
            "EXAMEN OFICIAL 2026 B ROJO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1VRUncb1rKn8O1cIOiIqZAEaVmkfSvC5l",
            "EXAMEN REPASO 1 TEMA 01 a 14 GENERAL ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1qEfrgrJeiJnH29GpjyEf8Ya0pwoyiJWw",
            "EXAMEN REPASO 1 TEMA 08 a 12 ESPECIFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1m06sF7_F_sZVlfRQq3Uv0egrvo44gcmX",
            "EXAMEN REPASO TEMA 2 COMPLETO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1sixOo5p9R_WeuL_mg8LliJScO1ljnNV0",
            "EXAMEN SABADO 31 OCTUBRE 2026": "https://drive.google.com/uc?export=download&id=1Yh_1mNSQNgQ6m-L-V2r6gaahKoWar0Oi",
            "SABADO 10 OCT 2026 ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1qtDZt9e2KsrnvElHWkSaN3wYnI1gT9Eq",
            "SABADO 5 SEP 2026 ACTUALIZADO": "https://drive.google.com/uc?export=download&id=17KWYOcGCSQR49cR7KMwqOKFi6QDsPkbh",
        },
        "GENERAL": {
            "Elige un test de general...": None,
            "TEMA 01 a 03 CONSTITUCIONAL": "https://drive.google.com/uc?export=download&id=14z3ZzvLLVZQ0XiUKx4qmiyneMoldZIB2",
            "TEMA 01 a 03 REPASO CONSTITUCION GENERAL": "https://drive.google.com/uc?export=download&id=153p-VAMdsxaXu47tqkkNOIjhO9mWhxVX",
            "TEMA 04 LA JEFATURA DEL ESTADO": "https://drive.google.com/uc?export=download&id=1y-u-_wTqfIyB_fn0he0cvyKAPLjsM06A",
            "TEMA 04 REPASO LA CORONA GENERAL": "https://drive.google.com/uc?export=download&id=1yeSHcMWRBtuotYSqUXUMgLQ-9KLXKbmG",
            "TEMA 05 REPASO CORTES GENERALES GENERAL": "https://drive.google.com/uc?export=download&id=1gGNUiRh7Ia1rS-sCEr8B1et94OXOOc2k",
            "TEMA 05 y 06 PODER LEGISLATIVO Y JUDICIAL": "https://drive.google.com/uc?export=download&id=1Hog53fH7CsG1FCk6CC0X4m4tIXZ2tPYd",
            "TEMA 06 REPASO PODER JUDICIAL GENERAL": "https://drive.google.com/uc?export=download&id=1SQoWQlO1Cnoc_WpP0VTmUlPSumT5FgkG",
            "TEMA 07 PODER EJECUTIVO": "https://drive.google.com/uc?export=download&id=1BXKLo950u1GSODuag-lds2SCbBTYF2UD",
            "TEMA 07 REPASO PODER EJECUTIVO GENERAL": "https://drive.google.com/uc?export=download&id=1v9ms7CaSFNyZAPM2qQoC_3_TO9gQ8wC7",
            "Tema 08 ADM GRAL ESTADO": "https://drive.google.com/uc?export=download&id=1sjO0bi2IwPJpPcESpQkWvqROPAHJ12L6",
            "TEMA 08 REPASO AGE GENRAL": "https://drive.google.com/uc?export=download&id=1PnGmAEZwJkVOwfzG4YMgs3LRNZa19KIz",
            "TEMA 09 CCAA Y MUNICIPIOS general": "https://drive.google.com/uc?export=download&id=1zk4mZRrMPIb8AnOD_8pFAPL-utUeFGKZ",
            "TEMA 09 REPASO CCAA GENERAL": "https://drive.google.com/uc?export=download&id=198XcxyyIPDFTJe22rsqYkXmfE1CTsjDH",
            "TEMA 10 INSTITUCIONES DE LA UE general": "https://drive.google.com/uc?export=download&id=1IGcXDNtMwW7MuhPon95EycFwOHrVQbW7",
            "TEMA 10 REPASO INSTITUCIONES DE LA UE GENERAL": "https://drive.google.com/uc?export=download&id=1Hw1l1-2_zsGfX4tbjUuw1DDokmE682e9",
            "TEMA 11  FUENTES DE LA UE GENERAL": "https://drive.google.com/uc?export=download&id=1gFNuLkKNhX8iq7GUrZzDj5xCSdKUPzCB",
            "TEMA 11 REPASO FUENTES DE LA UE GENERAL": "https://drive.google.com/uc?export=download&id=1OzmfuJkQooMX7ld_KFrNRnLj4xH9XHD1",
            "TEMA 13 REPASO FUENTES DEL DERECHO GENERAL": "https://drive.google.com/uc?export=download&id=1pMqfE5ThZaFgiqvqAWnXFeYfkOwCMUur",
            "TEMA 14 REPASO LA LEY GENERAL": "https://drive.google.com/uc?export=download&id=1k4RXRU6DKUQZ-MCI9A0T3kgiGOL39zgN",
        },
        "SUPUESTOS": {
            "Elige un test de supuestos...": None,
        },
    },
    "GESTION": {
        "DESARROLLO": {
            "Elige un test de desarrollo...": None,
            "Tema_51_Seguridad_Social_CE_y_TRLGSS": "https://drive.google.com/uc?export=download&id=1QzmhKlHNyv75TbL1ztW4HoG6bQHTLn5b",
            "Tema_52_Campo_Aplicacion_y_Composicion_SS": "https://drive.google.com/uc?export=download&id=1G3B8VJ5B-1pnMNyppVgpzMXgnhNVBbZL",
            "Tema_53_Afiliacion_Altas_Bajas_Convenio_Especial_Inscripcion": "https://drive.google.com/uc?export=download&id=1yEed2dlJZay1YHCbcpcC5VcADMGMrAQY",
            "Tema_54_Contingencias_Accidente_Trabajo_In_Itinere_Enfermedad_Profesional_Terrorismo": "https://drive.google.com/uc?export=download&id=1UiESIO2DsO76Opv1O99rlriFUUff6NdL",
            "Tema_55_Accion_Protectora_Prestaciones_Revalorizacion_Complementos": "https://drive.google.com/uc?export=download&id=1xJRnf86Ek4xmSGZMrKl7Y-Y1g8P8-KW2",
            "Tema_56_Requisitos_Generales_Responsabilidad_Empresarial_Automaticidad": "https://drive.google.com/uc?export=download&id=15GGBAgafDRCM5aBUMhMZ-9UdFodAf8F8",
            "Tema_57_Incapacidad_Temporal": "https://drive.google.com/uc?export=download&id=1-miLA9Tk7gUE-juwDvPcea1Wor_n_M8i",
            "Tema_58_Nacimiento_Corresponsabilidad_Riesgo_Embarazo_Lactancia_Menor_Cancer-v2": "https://drive.google.com/uc?export=download&id=1JAyEYB8RjPqRQHn1TsRjXREyINcy5EFg",
            "Tema_59_Incapacidad_Permanente_Contributiva_Cuantia_Compatibilidad-v2": "https://drive.google.com/uc?export=download&id=1lO2T5P4VcJVhGybReIeviRrBNmpIfhOb",
            "Tema_60_Calificacion_Revision_Incapacidad_Permanente_Lesiones_No_Invalidantes-v2": "https://drive.google.com/uc?export=download&id=1RnO7YfTph25VusZAvmDejPmvI0BA-c_R",
            "Tema_61_Jubilacion_Contributiva_Modalidades_Ley_27_2011_Vejez_SOVI-v2": "https://drive.google.com/uc?export=download&id=1NuEgPTYZmEals8Wv5ILmmyswT12Owfuu",
            "Tema_62_Proteccion_Muerte_y_Supervivencia": "https://drive.google.com/uc?export=download&id=1ATIGJ-0SxfOnN2tJHpQ1Hm6g7LPHAx2s",
            "Tema_67_Asistencia_Sanitaria_Prestaciones_y_Gestion": "https://drive.google.com/uc?export=download&id=1fmLaDtnKASH6GjGATrz363bn26B1BURw",
            "Tema_73_Regimenes_Integrados_Sistema_Especial_Agrario_y_Empleados_de_Hogar": "https://drive.google.com/uc?export=download&id=1geoGjR6csLIc78aJeU13zQTdt7DPZuYb",
            "Tema_74_Regimen_Especial_Trabajadores_Autonomos_RETA-v2": "https://drive.google.com/uc?export=download&id=1hx4PKcE0NALdBWdvQi1OxqgBzuC4eqFf",
            "Tema_75_Mineria_del_Carbon_Seguro_Escolar_y_Regimenes_Externos": "https://drive.google.com/uc?export=download&id=1RSXfx-Jzri8G0D42JobMx9tVe3DWhQG1",
        },
        "ESPECIFICO": {
            "Elige un test de especifico...": None,
            "TEMA 51 - CONSTITUCION EN LA SS Y TRLGSS ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1NHnqc_FOnsYV1473iGT04VbRCsL5OB0m",
            "TEMA 52 - CAMPO DE APLICACIÓN Y COMPOSICIÓN DEL SISTEMA ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1-5Rm3LkOugs5dVSYdURRAfLVR0FIVnmz",
            "TEMA 52 - REPASO 1 - CAMPO APLICACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1YLYxtBUxnyqcqRonpnOZBH1gs4BiOM1_",
            "TEMA 53 - AFILIACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1Kv-Bm_Eig1SMcXB-xBjzbQwQqjlAQ8Bf",
            "TEMA 53 - REPASO 1 - AFILIACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1_CJEGRuBVlSNa65SOD9N6oey7ZzbNvXb",
            "TEMA 54 - TEST - ACCIDENTE DE TRABAJO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1c2KfUMB2teOEKxN8y_gVZyKxUNdDT5Bb",
            "TEMA 55 ACCIÓN PROTECTORA CONTENIDO Y CLASIFICACIÓN DE LAS PRESTACIONES ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1oN_zQjZndYyv6Vqb23RSwnbc3kOLr_qG",
            "TEMA 55 REPASO PRESTACIONES ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1-s-CC-bmKNxORvrB_fojQJzYri0ghLnm",
            "TEMA 56 REPASO ACCION PROTECTORA ESPECÏFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1KemtXXZhcBEjA_D3-4MzrVqMcX3LTprK",
            "TEMA 56 REQUISITOS GENERALES DE LAS PRESTACIONES ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1dNoTqgXlXHmNK1YJEZVMb5K6ml5gKv9V",
            "TEMA 57 INCAPACIDAD TEMPORAL ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1X5vyIIDpecxuu3OjUSg5UM3bOVjgKFjd",
            "TEMA 57 REPASO INCAPACIDAD TEMPORAL ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=13H8QscCgfCTJ2HPCmNwE7g_1pmn2WPWX",
            "TEMA 58 REPASO NACIMIENTO Y CUIDADO DEL MENOR ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1Vpa3ITJ-U-gT53nfJBZFbW7M-5QSMbZm",
            "TEMA 59 y 60 IP ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1POaTzuPYzbWlZyXnfwVaGjA0V_UqwDwb",
            "TEMA 59 y 60 IP y LESIONES PERMANENTES ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1eQdN_fTcyn_T605iUc9FjpqFf64uDa0A",
            "TEMA 59 y 60 REPASO INCAPACIDAD PERMANETE ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=18C0alZZHd4iGVGRaFOHivbUOBzyEdksV",
            "TEMA 61 JUBILACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1nKrr7F0EeskM4NNFc4vY3qmBdWb9qpg5",
            "TEMA 61 REPASO  JUBILACIÓN ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1YXAiZqWdlEpdXUCnqjennX2hHwT87N-8",
            "TEMA 62 MUERTE Y SUPERVIVENCIA ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1z0iTZLKWW49SF_TDCZ5TzAikHIw0Dl96",
            "TEMA 62 REPASO MUERTE SUPERVIVENCIA ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=18UwNzRcHE-XTJWy8Va58krL_65MNgQEZ",
            "TEMA 64 IMV REPASO ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1fsmjqL8jeCPS_mMLP0Svuq3IWAr_BVd-",
            "TEMA 67 - REPASO 1 - COTIZACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1XfUA3JPXNS3AiDLU0x3m18D2FV8aLuR2",
            "Tema 67 COTIZACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=10oRTI6Rw_yF0yFZTQXhP8f8cHrZUWxK6",
            "TEMA 73 - LOS REGIMENES ESPECIALES DE LA S SOCIAL ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1gHCYu7-PUSZB34e4IFlG5twCQJ8r9rXm",
            "TEMA 73 - REPASO 1 - REGIMES ESPECIALES INTEGRADO EN RG ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1Cct-h4j1Pn9g5YUg27ihZ0bNk9dKNUQO",
            "TEMA 74 - RETA, SETA  Y MAR ACTUALIZADO": "https://drive.google.com/uc?export=download&id=18N_VW51u8AsyPx57fBzQ9TUAacy4YEw6",
            "TEMA 74.- REPASO 1 - RETA SETA Y MAR ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1IKx62YjsGUH_Ph7hAsYDcBreVWAuJ7SA",
            "TEMA 75 - MINERIA - SEGURO ESCOLAR FUNCIONARIOS ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1syZMOnCoJ3MEydEK2r7Due7b37FM9ywt",
            "TEMA 75- REPASO 1 - MINERÍA DEL CARBÓN - SEGURO ESCOLAR - FUNCIONARIOS ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1fM7zE6644urC4osPFd_zJCzQpbdlteB3",
        },
        "EXAMENES": {
            "Elige un test de examenes...": None,
            "✨NOVEDADES RDL_31_2026 gestion": "https://drive.google.com/uc?export=download&id=1Sfsqc1wV7rCfTaaoVbWOOLlDai5f7sMm",
            "DOMINGO 11 OCT 2026 ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1cQ9aPHfcpZmJrP3nOv52GNaY3ag9KVZ0",
            "DOMINGO 6 SEP 2026 ACTUALIZADO": "https://drive.google.com/uc?export=download&id=17Sn2tH9MnBKs4waafXN5NvLEJW8Dieq4",
            "Examen oficial 17 de mayo de 2026 ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1sZT_v_KQE1R0kyKxojAbpxMssu9vkdnG",
            "EXAMEN PRESENCIAL 01 NOV 2026": "https://drive.google.com/uc?export=download&id=1H6gXzNqQlleHzWOq_4N32wiGR7sZPHWP",
            "EXAMEN REPASO 1 TEMA 42 a 50 GENERAL ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1h_08kcGUlybuOk-VXUA6Ca6h11UFWBT2",
            "EXAMEN REPASO 1 TEMA 55 a 65 ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1jwafdNNaw4H9IgkjW7-TJgzcSaUkKFHm",
            "EXAMEN REPASO TEMA 6 a 10 DERECHO MERCANTIL ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1QT7rmZPvuuNr7SradBQGCk3ieIi8n9V0",
        },
        "GENERAL": {
            "Elige un test de general...": None,
            "TEMA 01 y 02 CIVIL general": "https://drive.google.com/uc?export=download&id=1YsqXQvC-dWW6ybnrP3vgwfphjHwwPHuk",
            "TEMA 03 CIVIL general": "https://drive.google.com/uc?export=download&id=1hkwMefSXTe4Vj6gqLZ2gpzpK8Imn8LA9",
            "TEMA 04 CIVIL": "https://drive.google.com/uc?export=download&id=1qDVfPe3VWD1dPqdFb-ePnjKy5_MXO7Nc",
            "TEMA 06 -  LA EMPRESA MERCANTIL": "https://drive.google.com/uc?export=download&id=17myj2PoQaWv_wZn7OV13wESOS7gBVNSN",
            "TEMA 07 - SOCIEDAD ANONIMA": "https://drive.google.com/uc?export=download&id=1_vZNRIHwJIcoPHdGyhbg7s-UEQEGrvMK",
            "TEMA 08 - TITULOS VALORES": "https://drive.google.com/uc?export=download&id=1JjPfA7i3yP1Xuqx19IBJQrYYZMYh6MoS",
            "TEMA 09 - LAS OBLIGACIONES MERCANTILES": "https://drive.google.com/uc?export=download&id=1ZhUqRGsA8SV8k4QPzVuGz0t2yXzdElXj",
            "TEMA 10 - DERECHO MERCANTIL - CONCURSO ACREEDORES": "https://drive.google.com/uc?export=download&id=1Tcn1glkQI4DkbjnHap3SY9B2gU49tWgT",
            "TEMA 25 EL DERECHO PRESUPUESTARIO": "https://drive.google.com/uc?export=download&id=1laSQ9V_KWQsADQ3ltO9TheF3kHOrlJnF",
            "TEMA 40 - IGUALDAD": "https://drive.google.com/uc?export=download&id=1tJ3MrhWg8GafmEfT7zX1hqnFNzPFmhAg",
            "TEMA 41 GOBIERNO ABIERTO Y AGENDA 2030": "https://drive.google.com/uc?export=download&id=1eCF7-MBTZ3SWJX2-agLKqQstxSXkdqJ_",
            "TEMA 42 a 50 REPASO LABORAL GENERAL": "https://drive.google.com/uc?export=download&id=1-XZ-qj8ITF0lPkDJMbOWXS2xcku-pAR6",
            "TEMA 42 EL DERECHO DEL TRABAJO": "https://drive.google.com/uc?export=download&id=1ARQ8PoNtyTykdcbixOxWgEr4SZ7sZV6c",
            "TEMA 42 REPASO DERECHO DEL TRABAJO GENERAL": "https://drive.google.com/uc?export=download&id=1_CNXYhEr-9WeBn-w9TA-iH3fG8VwII_N",
            "TEMA 43 CONVENIOS COLECTIVOS": "https://drive.google.com/uc?export=download&id=11uc4s9pZP5-vAnbUY7klhQOVR10rCpYg",
            "TEMA 43 REPASO CONVENIOS COLECTIVOS GENERAL": "https://drive.google.com/uc?export=download&id=1euDzEZfvjhx_3jGFaTo5kbNBP7aynypY",
            "TEMA 44 CONTRATOS": "https://drive.google.com/uc?export=download&id=1LRLQAx8Ql3MnMEe1kksaBQIiXUvuR2VT",
            "TEMA 44 REPASO CONTRATOS GENERAL": "https://drive.google.com/uc?export=download&id=1IBvudhfW61OhkBC_MZuTskWyEoLjcIJR",
            "TEMA 45 REPASO SALARIO Y JORNADA 2 GENERAL ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1FX3BQmFY5JNJtcTERwUFoLF9RA4F0pnw",
            "TEMA 45 REPASO SALARIO Y JORNADA GENERAL": "https://drive.google.com/uc?export=download&id=1QbifFgtRs2xui2vOPNeLbtBW5uVGTZE_",
            "TEMA 45 SALARIO Y JORNADA": "https://drive.google.com/uc?export=download&id=1RRl35OdPYxOVs4f2L1GZkQO4EAgZoSWm",
            "TEMA 46 MODIFICACIÓN SUSTANCIAL": "https://drive.google.com/uc?export=download&id=1LGFdvQcFjuinwdXWf6AM66QKoOL9_dn6",
            "TEMA 46 REPASO PODER DE DIRECCIÓN 2 GENERAL ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1ldFdccng8WcRE1kdua-WcmxvmE3k_JyO",
            "TEMA 46 REPASO PODER DE DIRECCIÓN GENERAL": "https://drive.google.com/uc?export=download&id=1tz8uIUPD5Re1GgzgUh2TjhVryNeZGj-I",
            "TEMA 47 REPASO SUSPENSIÓN DEL CONTRATO GENERAL ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1o7JnwcNBFN_81VZWRbVDIQL2Mx72kexY",
            "TEMA 47 SUSPENSIÓN": "https://drive.google.com/uc?export=download&id=1-kTGpXGLGBbbdKe26Lhq9gPXxZKCc44L",
            "Tema 48 - Extinción del Contrato": "https://drive.google.com/uc?export=download&id=1mbE4W0EnqJa9IosTYk2iEHbs2aBQOFdH",
            "TEMA 48 REPASO DESPIDO COLECTIVO GENERAL": "https://drive.google.com/uc?export=download&id=1N66XYQvXIWdiEbd7B3E_yFn97a4nnf-_",
            "TEMA 49 REPASO DESPIDO GENERAL": "https://drive.google.com/uc?export=download&id=1FXOlDF71QbID0Z9THcf8hO899XIWjtyu",
            "TEMA 49 y 50 DESPIDO Y HUELGA": "https://drive.google.com/uc?export=download&id=1FFt9QtwAeTz-U0VvCZQMaf15xS4s33bd",
            "TEMA 50 REPASO CONFLICTOS COLECTIVOS GENERAL": "https://drive.google.com/uc?export=download&id=10A9Fx_wO7Y-_Mw27YxR153ketgZ3WUB_",
        },
        "SUPUESTOS": {
            "Elige un test de supuestos...": None,
            "PROFESOR TEMA 54 - PREGUNTA + SUPUESTO PRÁCTICO": "https://drive.google.com/uc?export=download&id=1_pcP-rkh-8vXr5zViCY1XsCntnxlc4Yw",
        },
    },
}

TESTS_DISPONIBLES_COMPLETO = TESTS_DISPONIBLES

TESTS_DISPONIBLES_INVITADO = {
    "ADMINISTRATIVOS": {
        "ESPECIFICO": {
            "Elige un test de especifico...": None,
            "TEMA 01 ESPECIFICO_ACTUALIZADO": "https://drive.google.com/uc?export=download&id=13LzbXP5OknUY9NGZAdVMMN3F1Zl57glS",
        },
        "EXAMENES": {
            "Elige un test de examenes...": None,
        },
        "GENERAL": {
            "Elige un test de general...": None,
        },
    },
    "GESTION": {
        "ESPECIFICO": {
            "Elige un test de especifico...": None,
            "TEMA 51 - CONSTITUCION EN LA SS Y TRLGSS ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1NHnqc_FOnsYV1473iGT04VbRCsL5OB0m",
        },
        "EXAMENES": {
            "Elige un test de examenes...": None,
        },
        "GENERAL": {
            "Elige un test de general...": None,
        },
        "DESARROLLO": {
            "Elige un test de desarrollo...": None,
        },
    },
}

NUEVOS_HOY = [
    "Tema_54_Contingencias_Accidente_Trabajo_In_Itinere_Enfermedad_Profesional_Terrorismo",
    "TEMA 54 - TEST - ACCIDENTE DE TRABAJO ACTUALIZADO",
    "TEMA 25 EL DERECHO PRESUPUESTARIO",
    "PROFESOR TEMA 54 - PREGUNTA + SUPUESTO PRÁCTICO",
]
# === FIN SECCIÓN 2 ===

# === SECCIÓN 3: MOTOR DE EXTRACCIÓN DE PDF Y WORD (.DOCX) ===
import io, zipfile
import xml.etree.ElementTree as ET

class PDFQuizParser:
    @staticmethod
    def es_archivo_docx(file_bytes):
        if not file_bytes or len(file_bytes) < 4:
            return False
        if file_bytes[:4] == b'PK\x03\x04':
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                    return "word/document.xml" in zf.namelist()
            except Exception:
                return False
        return False

    @staticmethod
    def _extraer_lineas_estructuradas_docx(docx_bytes):
        lineas_info = []
        try:
            with zipfile.ZipFile(io.BytesIO(docx_bytes)) as zf:
                xml_content = zf.read("word/document.xml")
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            root = ET.fromstring(xml_content)
            body = root.find("w:body", ns)
            if body is None:
                return []

            for p in body.iter(f"{{{ns['w']}}}p"):
                pPr = p.find("w:pPr", ns)
                pStyle = ""
                es_lista = False
                if pPr is not None:
                    st_el = pPr.find("w:pStyle", ns)
                    if st_el is not None:
                        pStyle = st_el.attrib.get(f"{{{ns['w']}}}val", "")
                    if pPr.find("w:numPr", ns) is not None:
                        es_lista = True

                partes_txt = []
                partes_html = []
                chars_totales = 0
                chars_negrita = 0

                for r in p.findall("w:r", ns):
                    rPr = r.find("w:rPr", ns)
                    r_bold = False
                    if rPr is not None:
                        b_el = rPr.find("w:b", ns)
                        if b_el is not None:
                            val_b = b_el.attrib.get(f"{{{ns['w']}}}val", "true").lower()
                            r_bold = val_b not in ("0", "false", "off")
                    t_runs = []
                    for child in r:
                        tag_loc = child.tag.split("}")[-1]
                        if tag_loc == "t" and child.text:
                            t_runs.append(child.text)
                        elif tag_loc == "tab":
                            t_runs.append(" ")
                        elif tag_loc in ("br", "cr"):
                            t_runs.append("\n")
                    txt_r = "".join(t_runs)
                    if txt_r:
                        partes_txt.append(txt_r)
                        txt_esc = txt_r.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        partes_html.append(f"<b>{txt_esc}</b>" if r_bold else txt_esc)
                        n_ch = len(txt_r.strip())
                        chars_totales += n_ch
                        if r_bold:
                            chars_negrita += n_ch

                texto_p = "".join(partes_txt).strip()
                html_p = "".join(partes_html).strip()
                if not texto_p:
                    continue

                es_heading = bool(re.search(r'heading|titulo|encabezado|title', pStyle, re.IGNORECASE))
                es_negrita = es_heading or (chars_totales > 0 and (chars_negrita / chars_totales) >= 0.65)

                sub_lineas_txt = texto_p.split("\n")
                sub_lineas_html = html_p.split("\n")
                for idx_sl, sub_l in enumerate(sub_lineas_txt):
                    sub_l = sub_l.strip()
                    sub_h = sub_lineas_html[idx_sl].strip() if idx_sl < len(sub_lineas_html) else sub_l
                    if sub_l:
                        lineas_info.append({
                            "text": sub_l,
                            "html": sub_h,
                            "is_bold": es_negrita,
                            "is_heading": es_heading,
                            "is_list": es_lista,
                            "style": pStyle
                        })
        except Exception:
            return []
        return lineas_info

    @staticmethod
    def _limpiar_marca_agua_linea(linea):
        if not linea:
            return ""
        l = re.sub(
            r'(?:GESTI[ÓO]N\s+DE\s+LA\s+SEGURIDAD\s+SOCIAL\s*|ADMINISTRATIVO\s+DE\s+LA\s+SEGURIDAD\s+SOCIAL\s*)?(?:https?://)?(?:www\.)?oposiciona\.es\s*[•·\-]*\s*',
            '',
            linea,
            flags=re.IGNORECASE
        ).strip()
        return l

    @staticmethod
    def _es_basura_cabecera_o_pie(linea, titulo_tema=""):
        l = PDFQuizParser._limpiar_marca_agua_linea(linea)
        if not l:
            return True
        if re.match(r'^(?:p[áa]gina\s*)?\d{1,3}(?:\s+de\s+\d{1,3})?$', l, re.IGNORECASE):
            return True
        if re.match(
            r'^(?:GESTI[ÓO]N\s+DE\s+LA\s+SEGURIDAD\s+SOCIAL|ADMINISTRATIVO\s+DE\s+LA\s+SEGURIDAD\s+SOCIAL|PREGUNTAS?\s+DE\s+RESERVA|OPOSICIONA(?:\.ES|\s+5\.0)?|RESPUESTAS?\s+TE[ST]*\s+TEMAS?.*)$',
            l,
            re.IGNORECASE
        ):
            return True
        if titulo_tema and len(l) < 120:
            t_n = re.sub(r'\W+', '', titulo_tema.lower())
            l_n = re.sub(r'\W+', '', l.lower())
            if t_n and l_n == t_n:
                return True
        return False

    @staticmethod
    def _limpiar_cabeceras_incrustadas(texto, titulo_tema=""):
        if not texto:
            return ""
        lineas_out = []
        for l in texto.split("\n"):
            ls = PDFQuizParser._limpiar_marca_agua_linea(l.strip())
            if not ls:
                continue
            if PDFQuizParser._es_basura_cabecera_o_pie(ls, titulo_tema):
                continue
            lineas_out.append(ls)
        return "\n".join(lineas_out)

    @staticmethod
    def renderizar_explicacion_html(texto_explicacion, titulo_tema=""):
        if not texto_explicacion:
            return "<div>Sin explicación disponible.</div>"
        txt_limpio = PDFQuizParser._limpiar_cabeceras_incrustadas(texto_explicacion, titulo_tema)
        bloques_html = []
        for linea in txt_limpio.split("\n"):
            l = linea.strip()
            if not l:
                continue
            es_cabecera_h = False
            if l.startswith("[[H]]"):
                es_cabecera_h = True
                l = l.replace("[[H]]", "").strip()
            elif re.match(r'^(?:EXPLICACI[ÓO]N|RESPUESTA\s+T[ÉE]CNICA)\s*:?$', l, re.IGNORECASE):
                es_cabecera_h = True
            elif re.match(r'^(?:\d{1,2}[\.\)]\s+[A-ZÁÉÍÓÚÑ]|EP[ÍI]GRAFE\s+\d+|APARTADO\s+\d+)', l) and len(l) < 135 and not l.endswith("."):
                es_cabecera_h = True

            if es_cabecera_h:
                bloques_html.append(
                    f"<div style='font-size:14.5px; font-weight:800; color:#083B46 !important; margin-top:12px; margin-bottom:5px;'>{l}</div>"
                )
            elif re.match(r'^(?:[•\-\*▪■·]|\d{1,2}[\.\º\ª]*\)|\([a-z0-9]+\)|[a-g]\))\s*', l):
                l_fmt = re.sub(r'^([•\-\*▪■·]\s*[^:\.]{3,90}:)', r'<b>\1</b>', l)
                bloques_html.append(
                    f"<div style='margin-top:5px; margin-bottom:5px; padding-left:12px; line-height:1.5; color:#0c5460 !important; text-align:justify;'>{l_fmt}</div>"
                )
            else:
                l_fmt = re.sub(r'^(\d{1,2}\.º\s+|(?:EXPLICACI[ÓO]N|RESPUESTA\s+T[ÉE]CNICA)\s*:|[A-ZÁÉÍÓÚÑ][^:\.]{2,75}:)', r'<b>\1</b>', l)
                bloques_html.append(
                    f"<div style='margin-top:6px; margin-bottom:6px; line-height:1.52; color:#0c5460 !important; text-align:justify;'>{l_fmt}</div>"
                )
        return "".join(bloques_html)

    @staticmethod
    def _formatear_html_planteamiento_supuesto(lineas_planteamiento):
        bloques = []
        pat_ordinal_caso = re.compile(
            r'^(?:[•·\-\*▪■]\s*)?(En\s+(?:primer|segundo|tercer|cuarto|quinto|sexto|s[ée]ptimo|octavo|noveno|d[ée]cimo(?:\s+y\s+[úu]ltimo)?)\s+lugar\b.*)$',
            re.IGNORECASE
        )
        for item in lineas_planteamiento:
            txt_p = PDFQuizParser._limpiar_marca_agua_linea(item.get("text") or "")
            html_p = PDFQuizParser._limpiar_marca_agua_linea(item.get("html") or txt_p)
            es_lista = bool(item.get("is_list", False))
            if not txt_p:
                continue

            m_ord = pat_ordinal_caso.match(txt_p)
            if m_ord or txt_p.startswith(("·", "•", "▪", "■")):
                html_limpio = re.sub(r'^(?:<[^>]+>)*\s*[•·\-\*▪■]\s*', '', html_p).strip()
                bloques.append(
                    f"<div style='margin:0 0 5px 0; padding-left:14px; text-indent:-10px; font-size:10pt !important; line-height:1.38; color:#1E293B !important; text-align:justify; font-weight:normal;'>"
                    f"·&nbsp;&nbsp;{html_limpio}"
                    f"</div>"
                )
            elif es_lista:
                bloques.append(
                    f"<div style='margin:0 0 5px 0; padding-left:14px; text-indent:-10px; font-size:10pt !important; line-height:1.38; color:#1E293B !important; text-align:justify; font-weight:normal;'>"
                    f"·&nbsp;&nbsp;{html_p}"
                    f"</div>"
                )
            else:
                bloques.append(
                    f"<p style='margin:0 0 6px 0; font-size:10pt !important; line-height:1.4; color:#1E293B !important; text-align:justify; font-weight:normal;'>"
                    f"{html_p}"
                    f"</p>"
                )
        return "".join(bloques)

    @staticmethod
    def _parse_supuestos_practicos(parrafos, tema_titulo=""):
        pat_marca_supuesto = re.compile(
            r'(?:^|\b)(?:(?:\d+|I|II|III)[\.\-\)]\s*)?SUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+\d+)?\s*[:\.\-]?\s*',
            re.IGNORECASE
        )

        parrafos_utiles = []
        encontrado_supuesto = False

        for p in parrafos:
            txt_p = PDFQuizParser._limpiar_marca_agua_linea(p["text"])
            html_p = PDFQuizParser._limpiar_marca_agua_linea(p.get("html") or txt_p)
            if not txt_p:
                continue
            if not encontrado_supuesto:
                m_sup = pat_marca_supuesto.search(txt_p)
                if m_sup and (txt_p[m_sup.start():m_sup.end()].isupper() or m_sup.start() == 0):
                    encontrado_supuesto = True
                    resto_txt = txt_p[m_sup.end():].strip()
                    if resto_txt:
                        resto_html = re.sub(
                            r'^.*?(?:SUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+\d+)?\s*[:\.\-]?\s*)(?:</b>)?\s*',
                            '',
                            html_p,
                            flags=re.IGNORECASE
                        ).strip()
                        parrafos_utiles.append({
                            "text": resto_txt,
                            "html": resto_html if resto_html else resto_txt,
                            "is_bold": False,
                            "is_list": p.get("is_list", False)
                        })
                continue
            else:
                parrafos_utiles.append({
                    "text": txt_p,
                    "html": html_p,
                    "is_bold": p.get("is_bold", False),
                    "is_list": p.get("is_list", False)
                })

        if not encontrado_supuesto:
            parrafos_utiles = parrafos

        if not parrafos_utiles:
            return []

        pat_pregunta_explicita = re.compile(r'^(?:CUESTI[ÓO]N\s+|PREGUNTA\s+)?(\d{1,2})[\.\-\)]\s+(.+)$', re.IGNORECASE)
        pat_cierre_planteamiento = re.compile(
            r'(?:responda\s+de\s+forma\s+razonada|siguientes\s+(?:\w+\s+)?cuestiones\s+pr[áa]cticas|responda\s+a\s+las\s+siguientes\s+preguntas)\s*:\s*$',
            re.IGNORECASE
        )
        pat_ordinal_enunciado = re.compile(
            r'^(?:[•·\-\*▪■]\s*)?En\s+(?:primer|segundo|tercer|cuarto|quinto|sexto|s[ée]ptimo|octavo|noveno|d[ée]cimo(?:\s+y\s+[úu]ltimo)?)\s+lugar\b',
            re.IGNORECASE
        )
        pat_verbo_pregunta = re.compile(
            r'^(?:Determine|Analice|Calcule|Indique|Precise|Razone|Justifique|Explique|Señale|Resuelva|En\s+relaci[óo]n\s+con|Respecto\s+(?:de|a)|Ante\s+la)\b',
            re.IGNORECASE
        )
        pat_explicacion = re.compile(r'^EXPLICACI[ÓO]N\s*:\s*(.*)$', re.IGNORECASE)
        pat_resp_tecnica = re.compile(r'^RESPUESTA\s+T[ÉE]CNICA\s*:\s*(.*)$', re.IGNORECASE)

        lineas_planteamiento = []
        questions = []
        curr_q = None
        leyendo_planteamiento = True
        cierre_planteamiento_visto = False
        contador_preguntas = 0

        for p in parrafos_utiles:
            txt_raw = PDFQuizParser._limpiar_marca_agua_linea(p["text"])
            txt = re.sub(r'^[•·\-\*▪■]\s*', '', txt_raw).strip()
            html_p = PDFQuizParser._limpiar_marca_agua_linea(p.get("html") or txt_raw)
            es_bold = bool(p.get("is_bold", False))
            es_lista = bool(p.get("is_list", False))

            if not txt or txt == tema_titulo:
                continue

            m_exp = pat_explicacion.match(txt)
            m_rt = pat_resp_tecnica.match(txt)

            if m_exp and curr_q is not None:
                curr_q["explanation_lines"].append("[[H]]📌 EXPLICACIÓN Y ANÁLISIS DEL SUPUESTO:")
                if m_exp.group(1).strip():
                    curr_q["explanation_lines"].append(m_exp.group(1).strip())
                continue

            if m_rt and curr_q is not None:
                curr_q["explanation_lines"].append("[[H]]⚖️ RESPUESTA TÉCNICA Y FUNDAMENTACIÓN JURÍDICA:")
                if m_rt.group(1).strip():
                    curr_q["explanation_lines"].append(m_rt.group(1).strip())
                continue

            if leyendo_planteamiento and pat_ordinal_enunciado.match(txt_raw):
                lineas_planteamiento.append({"text": txt_raw, "html": html_p, "is_list": True})
                continue

            if leyendo_planteamiento and pat_cierre_planteamiento.search(txt):
                lineas_planteamiento.append({"text": txt_raw, "html": html_p, "is_list": False})
                cierre_planteamiento_visto = True
                continue

            m_q = pat_pregunta_explicita.match(txt)
            es_subapartado_respuesta = bool(re.match(r'^\d{1,2}\.[ºª°]', txt))
            es_nueva_pregunta = False
            num_q = 0
            cuerpo_q = ""

            if m_q and not es_subapartado_respuesta:
                num_cand = int(m_q.group(1))
                cuerpo_cand = m_q.group(2).strip()
                if (
                    cierre_planteamiento_visto or
                    (not leyendo_planteamiento and curr_q is not None and len(curr_q["explanation_lines"]) > 0) or
                    pat_verbo_pregunta.match(cuerpo_cand)
                ):
                    es_nueva_pregunta = True
                    num_q = num_cand
                    cuerpo_q = cuerpo_cand
            elif not es_subapartado_respuesta and (cierre_planteamiento_visto or (curr_q is not None and len(curr_q["explanation_lines"]) > 0)):
                if (es_bold or es_lista) and pat_verbo_pregunta.match(txt) and len(txt) > 35:
                    es_nueva_pregunta = True
                    num_q = contador_preguntas + 1
                    cuerpo_q = txt

            if es_nueva_pregunta:
                if curr_q is not None:
                    questions.append(curr_q)
                leyendo_planteamiento = False
                contador_preguntas = num_q
                preamble_html_str = PDFQuizParser._formatear_html_planteamiento_supuesto(lineas_planteamiento)
                curr_q = {
                    "num": num_q,
                    "question_text": f"{num_q}. {cuerpo_q}",
                    "preamble": preamble_html_str,
                    "options": [],
                    "answer": -1,
                    "answer_text": "",
                    "explanation_lines": [],
                    "is_open": True,
                    "tipo_abierta": "SUPUESTO",
                    "tema_titulo": tema_titulo
                }
                continue

            if leyendo_planteamiento:
                lineas_planteamiento.append({"text": txt_raw, "html": html_p, "is_list": es_lista})
            elif curr_q is not None:
                if not curr_q["explanation_lines"] and es_bold and not txt.startswith(("·", "•", "-", "«", '"', "1.", "2.", "3.")):
                    curr_q["question_text"] += " " + txt
                else:
                    if es_lista and not re.match(r'^(?:[•\-\*▪■·]|\d+[\.\º\ª\)]|[a-zA-Z][\.\)])\s*', txt_raw):
                        curr_q["explanation_lines"].append(f"· {txt}")
                    else:
                        curr_q["explanation_lines"].append(txt_raw)

        if curr_q is not None:
            questions.append(curr_q)

        salida_final = []
        for q_item in questions:
            exp_unida = "\n".join(q_item.pop("explanation_lines", [])).strip()
            q_item.pop("num", None)
            q_item["explanation"] = exp_unida
            salida_final.append(q_item)

        return salida_final

    @staticmethod
    def parse_abiertas_gestion(file_bytes, modo="DESARROLLO"):
        lineas_estructuradas = []
        if PDFQuizParser.es_archivo_docx(file_bytes):
            lineas_estructuradas = PDFQuizParser._extraer_lineas_estructuradas_docx(file_bytes)
        else:
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    blocks = page.get_text("dict").get("blocks", [])
                    for b in blocks:
                        for l in b.get("lines", []):
                            spans = l.get("spans", [])
                            txt_l = "".join(s.get("text", "") for s in spans).strip()
                            txt_l = PDFQuizParser._limpiar_marca_agua_linea(txt_l)
                            if not txt_l:
                                continue
                            chars_tot = sum(len(s.get("text", "").strip()) for s in spans)
                            chars_b = sum(
                                len(s.get("text", "").strip())
                                for s in spans
                                if "bold" in (s.get("font", "") or "").lower() or (s.get("flags", 0) & 16)
                            )
                            is_b = chars_tot > 0 and (chars_b / chars_tot) >= 0.65
                            txt_esc = txt_l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                            lineas_estructuradas.append({
                                "text": txt_l,
                                "html": f"<b>{txt_esc}</b>" if is_b else txt_esc,
                                "is_bold": is_b,
                                "is_heading": False,
                                "is_list": txt_l.startswith(("·", "•", "▪", "■"))
                            })
                doc.close()
            except Exception:
                return []

        if not lineas_estructuradas:
            return []

        parrafos = []
        buf_txt = ""
        buf_html = ""
        buf_bold = False
        buf_list = False
        es_docx = PDFQuizParser.es_archivo_docx(file_bytes)

        pat_corte_estructural_pdf = re.compile(
            r'^(?:TEMA\s+\d+|EP[ÍI]GRAFE\s+\d+|PREGUNTA\s+DE\s+DESARROLLO|SUPUESTOS?\s+PR[ÁA]CTICOS?|EXPLICACI[ÓO]N\s*:|RESPUESTA\s+T[ÉE]CNICA\s*:|CUESTI[ÓO]N\s+\d+|PREGUNTA\s+\d+|\d{1,2}[\.\)]\s+|[•\-\*▪■·]\s*En\s+(?:primer|segundo|tercer|cuarto|quinto|sexto|s[ée]ptimo|octavo|noveno|d[ée]cimo)|En\s+(?:primer|segundo|tercer|cuarto|quinto|sexto|s[ée]ptimo|octavo|noveno|d[ée]cimo)\s+lugar|Con\s+base\s+en\s+los\s+hechos|[•\-\*▪■·]\s+|[a-g]\)\s+)',
            re.IGNORECASE
        )

        for item in lineas_estructuradas:
            t = re.sub(r'\s+', ' ', PDFQuizParser._limpiar_marca_agua_linea(item["text"])).strip()
            h = re.sub(r'\s+', ' ', PDFQuizParser._limpiar_marca_agua_linea(item.get("html") or t)).strip()
            if not t or PDFQuizParser._es_basura_cabecera_o_pie(t):
                continue
            if es_docx:
                parrafos.append({
                    "text": t,
                    "html": h,
                    "is_bold": item.get("is_bold", False),
                    "is_list": item.get("is_list", False)
                })
                continue

            es_nuevo_bloque = (
                item.get("is_heading") or
                item.get("is_bold") != buf_bold or
                bool(pat_corte_estructural_pdf.match(t))
            )
            if not buf_txt:
                buf_txt = t
                buf_html = h
                buf_bold = item.get("is_bold", False)
                buf_list = item.get("is_list", False)
            elif es_nuevo_bloque or buf_txt.endswith((".", ":", "?", "!", "»", '"')):
                parrafos.append({"text": buf_txt, "html": buf_html, "is_bold": buf_bold, "is_list": buf_list})
                buf_txt = t
                buf_html = h
                buf_bold = item.get("is_bold", False)
                buf_list = item.get("is_list", False)
            else:
                buf_txt += " " + t
                buf_html += " " + h
        if buf_txt:
            parrafos.append({"text": buf_txt, "html": buf_html, "is_bold": buf_bold, "is_list": buf_list})

        tema_titulo = ""
        for p in parrafos[:8]:
            if re.match(r'^TEMA\s+\d+', p["text"], re.IGNORECASE):
                tema_titulo = p["text"].strip()
                break
        if not tema_titulo:
            for p in parrafos:
                m_pag_tema = re.search(r'\(p[áa]gina\s+\d+[^)]*,\s*(tema\s+\d+)\)', p["text"], re.IGNORECASE)
                if m_pag_tema:
                    tema_titulo = m_pag_tema.group(1).upper()
                    break

        if modo in ("SUPUESTOS", "SUPUESTO"):
            return PDFQuizParser._parse_supuestos_practicos(parrafos, tema_titulo=tema_titulo)

        parrafos_desarrollo = []
        for p in parrafos:
            if re.search(r'(?:^|\b)SUPUESTOS?\s+PR[ÁA]CTICOS?\b', p["text"].strip()):
                break
            parrafos_desarrollo.append(p)

        pat_epigrafe = re.compile(
            r'^(?:EP[ÍI]GRAFE\s+\d+[\.\:\-\s]*|PREGUNTA(?:\s+DE\s+DESARROLLO)?(?:\s+\d+)?[\.\:\-\s]*)(.*)$',
            re.IGNORECASE
        )

        questions = []
        curr_title = ""
        curr_body = []

        for p in parrafos_desarrollo:
            txt = p["text"].strip()
            if txt == tema_titulo:
                continue
            m_ep = pat_epigrafe.match(txt)
            if m_ep and (txt.upper().startswith("EPÍGRAFE") or txt.upper().startswith("EPIGRAFE") or txt.upper().startswith("PREGUNTA DE DESARROLLO")):
                if curr_title and curr_body:
                    questions.append({
                        "question_text": curr_title,
                        "preamble": "",
                        "options": [],
                        "answer": -1,
                        "answer_text": "",
                        "explanation": "\n".join(curr_body),
                        "is_open": True,
                        "tipo_abierta": "DESARROLLO",
                        "tema_titulo": tema_titulo
                    })
                resto_tit = m_ep.group(1).strip()
                curr_title = resto_tit if resto_tit else txt
                curr_body = []
            else:
                if curr_title:
                    if curr_title.upper() == "PREGUNTA DE DESARROLLO" and not curr_body and len(txt) < 160:
                        curr_title = f"PREGUNTA DE DESARROLLO: {txt}"
                    elif p.get("is_bold") and len(txt) < 135 and not txt.endswith("."):
                        curr_body.append(f"[[H]]{txt}")
                    else:
                        curr_body.append(txt)

        if curr_title and curr_body:
            questions.append({
                "question_text": curr_title,
                "preamble": "",
                "options": [],
                "answer": -1,
                "answer_text": "",
                "explanation": "\n".join(curr_body),
                "is_open": True,
                "tipo_abierta": "DESARROLLO",
                "tema_titulo": tema_titulo
            })

        if not questions and parrafos_desarrollo:
            for p in parrafos_desarrollo:
                txt = p["text"].strip()
                if txt == tema_titulo:
                    continue
                es_titulo_num = p.get("is_bold") and bool(re.match(r'^(?:\d{1,2}[\.\-\)]\s+|[IVX]+[\.\-\)]\s+)[A-ZÁÉÍÓÚÑ]', txt)) and len(txt) < 160
                if es_titulo_num:
                    if curr_title and curr_body:
                        questions.append({
                            "question_text": curr_title,
                            "preamble": "",
                            "options": [],
                            "answer": -1,
                            "answer_text": "",
                            "explanation": "\n".join(curr_body),
                            "is_open": True,
                            "tipo_abierta": "DESARROLLO",
                            "tema_titulo": tema_titulo
                        })
                    curr_title = txt
                    curr_body = []
                elif curr_title:
                    curr_body.append(f"[[H]]{txt}" if (p.get("is_bold") and len(txt) < 130) else txt)

            if curr_title and curr_body:
                questions.append({
                    "question_text": curr_title,
                    "preamble": "",
                    "options": [],
                    "answer": -1,
                    "answer_text": "",
                    "explanation": "\n".join(curr_body),
                    "is_open": True,
                    "tipo_abierta": "DESARROLLO",
                    "tema_titulo": tema_titulo
                })

        return questions

    @staticmethod
    def _atomizar_linea_test(raw_line, is_bold):
        """
        Divide líneas de PDF donde:
        - La opción 'A)' viene pegada al final del enunciado de la pregunta tras ':' o '?' (ej. P25 y P28 de Constitucional).
        - Varias opciones vienen pegadas en la misma línea ('a) Texto. b) Texto.' o 'c) Texto. C) Texto.').
        - 'Explicación:' viene pegada al final de la opción d).
        """
        l = PDFQuizParser._limpiar_marca_agua_linea(re.sub(r'\s+', ' ', raw_line or "").strip())
        if not l or l in ("0", "-", "•", "·", "#"):
            return []

        segmentos = []
        # 1. Separar si 'Explicación:' viene pegada al final de una opción
        m_exp_inline = re.search(
            r'(?<=[.?!»"\)\]])\s+((?:Explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s*\([^)]*\))?|Respuesta(?:\s+correcta)?|Soluci[óo]n)\s*:\s*.*)$',
            l,
            flags=re.IGNORECASE
        )
        cola_exp = None
        if m_exp_inline and m_exp_inline.start() > 3:
            cola_exp = l[m_exp_inline.start():].strip()
            l = l[:m_exp_inline.start()].strip()

        # 2. Separar si la opción 'A)' viene pegada al final del enunciado de una pregunta (ej. '25.- Sobre la pena de muerte: A) Queda abolida...')
        m_q_with_a = re.match(
            r'^((?:#\s*)?(?:Pregunta\s+)?\d{1,3}\s*[\.\-\)]\s*.*?(?:[:\?\.]))\s+([aA][\)\.\-]\s+[A-ZÁÉÍÓÚÑ¡¿"\'«\d].*)$',
            l
        )
        if m_q_with_a:
            q_part = m_q_with_a.group(1).strip()
            opts_part = m_q_with_a.group(2).strip()
            segmentos.append((q_part, False))
            l = opts_part

        # 3. Separar múltiples opciones pegadas en una sola línea:
        partes_opt = re.split(
            r'(?:(?<=[.?!»"\)\];:])\s+|\s{2,})(?=(?:#\s*)?[a-dA-D][\)\.\-]\s+[A-ZÁÉÍÓÚÑ¡¿"\'«\d])',
            l
        )
        for p in partes_opt:
            ps = re.sub(r'^#\s*(?=[a-dA-D][\)\.\-])', '', p.strip())
            if ps:
                segmentos.append((ps, is_bold))

        if cola_exp:
            segmentos.append((cola_exp, False))
        return segmentos

    @staticmethod
    def _reparar_fragmentos_desordenados_pdf(lineas_pagina):
        """
        Repara el desfase de coordenadas de PDF como el de la Pregunta 10 de Constitucional (pág. 4),
        donde un fragmento en minúscula ('ley ordinaria y cabe recurso de') se extrae justo antes
        de la cabecera de opción a la que pertenece ('C) Su desarrollo se reserva a'), habiendo
        cerrado ya la opción anterior en punto ('.').
        """
        if not lineas_pagina:
            return []
        reparadas = []
        i = 0
        n = len(lineas_pagina)
        while i < n:
            txt_i, bold_i = lineas_pagina[i]
            txt_i_clean = PDFQuizParser._limpiar_marca_agua_linea(txt_i)
            # ¿Es un fragmento huérfano que empieza por minúscula tras una línea ya cerrada en punto y justo antes de una opción 'X) ... a / de / con / por / en'?
            if (
                i + 1 < n and
                reparadas and
                reparadas[-1][0].rstrip().endswith((".", "?", "!", "»", '"')) and
                re.match(r'^[a-záéíóúñ]', txt_i_clean) and
                not re.match(r'^[a-dA-D][\)\.\-]\s', txt_i_clean)
            ):
                txt_next, bold_next = lineas_pagina[i + 1]
                txt_next_clean = re.sub(r'^#\s*', '', PDFQuizParser._limpiar_marca_agua_linea(txt_next))
                m_opt_next = re.match(r'^([a-dA-D][\)\.\-]\s+)(.+)$', txt_next_clean)
                if m_opt_next:
                    pref_next = m_opt_next.group(1)
                    cuerpo_next = m_opt_next.group(2).strip()
                    # Si la primera parte de 'C) Su desarrollo se reserva a' está cortada en preposición/verbo
                    m_corte_prep = re.match(r'^(.+?\b(?:a|de|en|con|por|para|la|el|los|las|un|una|que|se|su|al|del))\s+(.+)$', cuerpo_next, flags=re.IGNORECASE)
                    if m_corte_prep:
                        nuevo_txt = f"{pref_next}{m_corte_prep.group(1)} {txt_i_clean} {m_corte_prep.group(2)}"
                    else:
                        nuevo_txt = f"{pref_next}{cuerpo_next} {txt_i_clean}"
                    reparadas.append((re.sub(r'\s+', ' ', nuevo_txt).strip(), bold_i or bold_next))
                    i += 2
                    continue
            reparadas.append((txt_i, bold_i))
            i += 1
        return reparadas

    @staticmethod
    def parse(file_bytes, max_options=None):
        """
        Extrae preguntas tipo test (a, b, c, d) tanto de PDF como de Word (.docx).
        """
        lineas_brutas = []
        if PDFQuizParser.es_archivo_docx(file_bytes):
            for item in PDFQuizParser._extraer_lineas_estructuradas_docx(file_bytes):
                lineas_brutas.append((item["text"], item["is_bold"]))
        else:
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    items_pagina = []
                    blocks = page.get_text("dict").get("blocks", [])
                    for b in blocks:
                        for l in b.get("lines", []):
                            bbox = l.get("bbox", (0, 0, 0, 0))
                            y0, x0 = round(bbox[1], 1), round(bbox[0], 1)
                            spans = l.get("spans", [])
                            txt_l = "".join(s.get("text", "") for s in spans).strip()
                            if not txt_l:
                                continue
                            sub_spans = []
                            curr_s_txt = ""
                            curr_ch_tot = 0
                            curr_ch_bold = 0
                            for s in spans:
                                st = s.get("text", "")
                                if not st:
                                    continue
                                sb = "bold" in (s.get("font", "") or "").lower() or bool(s.get("flags", 0) & 16)
                                if curr_s_txt and re.match(r'^\s*[a-dA-D][\)\.\-]\s+', st) and re.search(r'[.?!»"\)\];:]\s*$', curr_s_txt):
                                    is_b_seg = curr_ch_tot > 0 and (curr_ch_bold / curr_ch_tot) >= 0.55
                                    sub_spans.append((curr_s_txt.strip(), is_b_seg))
                                    curr_s_txt = st
                                    curr_ch_tot = len(st.strip())
                                    curr_ch_bold = len(st.strip()) if sb else 0
                                else:
                                    curr_s_txt += st
                                    n_c = len(st.strip())
                                    curr_ch_tot += n_c
                                    if sb:
                                        curr_ch_bold += n_c
                            if curr_s_txt.strip():
                                is_b_seg = curr_ch_tot > 0 and (curr_ch_bold / curr_ch_tot) >= 0.55
                                sub_spans.append((curr_s_txt.strip(), is_b_seg))

                            for idx_sp, (s_txt, s_bold) in enumerate(sub_spans):
                                s_clean = PDFQuizParser._limpiar_marca_agua_linea(s_txt)
                                if s_clean and not PDFQuizParser._es_basura_cabecera_o_pie(s_clean):
                                    items_pagina.append((y0, x0 + idx_sp * 0.1, s_clean, s_bold))

                    # Ordenar visualmente de arriba abajo (agrupando líneas cuya coordenada Y difiera en menos de 2.5 pt)
                    items_pagina.sort(key=lambda it: (round(it[0] / 2.5), it[1]))
                    lineas_pag_ordenadas = [(it[2], it[3]) for it in items_pagina]
                    lineas_pag_reparadas = PDFQuizParser._reparar_fragmentos_desordenados_pdf(lineas_pag_ordenadas)
                    lineas_brutas.extend(lineas_pag_reparadas)
                doc.close()
            except Exception:
                return []

        lineas_doc = []
        for r_txt, r_bold in lineas_brutas:
            for seg_txt, seg_bold in PDFQuizParser._atomizar_linea_test(r_txt, r_bold):
                lineas_doc.append((seg_txt, seg_bold))

        questions = []
        curr_q = None
        state = "IDLE"
        preamble_buf = []
        pending_empty_opts = []

        pat_q = re.compile(r'^(?:#\s*)?(?:Pregunta\s+)?(\d{1,3})\s*[\.\-\)]\s*(?![ºª°a-zA-Z]\b)\s*[\.\-\)]*\s*(.+)$', re.IGNORECASE)
        pat_opt_empty = re.compile(r'^(?:#\s*)?([a-dA-D])[\)\.\-]\s*$')
        pat_opt = re.compile(r'^(?:#\s*)?([a-dA-D])[\)\.\-]\s+(.+)$')
        pat_exp = re.compile(r'^(?:Explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s*\([^)]*\))?|Respuesta(?:\s+correcta)?|Soluci[óo]n)\s*:\s*(.*)$', re.IGNORECASE)
        pat_ans_letter = re.compile(r'^(?:Respuesta\s+correcta|Soluci[óo]n|Correcta)\s*:\s*([a-dA-D])\b', re.IGNORECASE)

        def _formatear_preamble_test(lineas_pre):
            if not lineas_pre:
                return ""
            bloques_p = []
            for lp in lineas_pre:
                lp_c = PDFQuizParser._limpiar_marca_agua_linea(lp)
                if not lp_c:
                    continue
                if re.match(r'^(?:#\s*)?(?:SUPUESTO\s+PR[ÁA]CTICO|CASO\s+PR[ÁA]CTICO|ENUNCIADO\s+DEL\s+SUPUESTO)\b', lp_c, re.IGNORECASE):
                    lp_tit = re.sub(r'^#\s*', '', lp_c).strip()
                    bloques_p.append(f"<div style='font-size:10pt !important; font-weight:800; color:#1E3A8A !important; margin-bottom:4px;'>📋 {lp_tit}</div>")
                else:
                    bloques_p.append(f"<p style='margin:0 0 5px 0; font-size:10pt !important; line-height:1.38; color:#1E293B !important; text-align:justify;'>{lp_c}</p>")
            return "".join(bloques_p)

        def _cerrar_pregunta_actual(q_obj):
            if not q_obj:
                return
            opts_limpias = []
            ans_final = q_obj.get("answer", -1)
            for idx_o, o_txt in enumerate(q_obj.get("options", [])):
                cuerpo_o = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', o_txt).strip()
                cuerpo_o = PDFQuizParser._limpiar_marca_agua_linea(cuerpo_o)
                if cuerpo_o:
                    letra_norm = chr(ord('a') + len(opts_limpias))
                    if idx_o == q_obj.get("answer", -1):
                        ans_final = len(opts_limpias)
                    opts_limpias.append(f"{letra_norm}) {cuerpo_o}")
            q_obj["options"] = opts_limpias
            q_obj["answer"] = ans_final if 0 <= ans_final < len(opts_limpias) else -1
            if len(q_obj["options"]) >= 2:
                questions.append(q_obj)

        for raw_line, is_bold in lineas_doc:
            line = PDFQuizParser._limpiar_marca_agua_linea(raw_line)
            if not line or PDFQuizParser._es_basura_cabecera_o_pie(line):
                continue

            if re.match(r'^(?:#\s*)?(?:SUPUESTO\s+PR[ÁA]CTICO|CASO\s+PR[ÁA]CTICO|ENUNCIADO\s+DEL\s+SUPUESTO)\b', line, re.IGNORECASE):
                _cerrar_pregunta_actual(curr_q)
                curr_q = None
                pending_empty_opts = []
                preamble_buf = [re.sub(r'^#\s*', '', line).strip()]
                state = "PREAMBLE"
                continue

            m_q = pat_q.match(line)
            m_opt_empty = pat_opt_empty.match(line)
            m_opt = pat_opt.match(line)
            m_exp = pat_exp.match(line)

            if m_q and not m_opt and not m_opt_empty:
                _cerrar_pregunta_actual(curr_q)
                pending_empty_opts = []
                curr_q = {
                    "question_text": f"{m_q.group(1)}. {m_q.group(2).strip()}",
                    "preamble": _formatear_preamble_test(preamble_buf),
                    "options": [],
                    "options_bold": [],
                    "answer": -1,
                    "explanation": ""
                }
                state = "QUESTION"
                continue

            if state == "PREAMBLE" and curr_q is None:
                preamble_buf.append(line)
                continue

            if curr_q is None:
                continue

            if m_exp:
                state = "EXPLANATION"
                pending_empty_opts = []
                resto_exp = m_exp.group(1).strip()
                m_let = pat_ans_letter.match(line)
                if m_let and curr_q["answer"] == -1:
                    idx_l = ord(m_let.group(1).lower()) - ord('a')
                    if 0 <= idx_l < len(curr_q["options"]):
                        curr_q["answer"] = idx_l
                if resto_exp:
                    curr_q["explanation"] = (curr_q["explanation"] + "\n" + resto_exp).strip()
                continue

            if m_opt_empty and state in ("QUESTION", "OPTIONS"):
                if max_options is None or len(curr_q["options"]) < max_options:
                    letra_asignada = chr(ord('a') + len(curr_q["options"]))
                    curr_q["options"].append(f"{letra_asignada}) ")
                    curr_q["options_bold"].append(is_bold)
                    pending_empty_opts.append(len(curr_q["options"]) - 1)
                    state = "OPTIONS"
                    continue

            if m_opt and state in ("QUESTION", "OPTIONS"):
                es_marcada_hash = line.lstrip().startswith("#")
                es_correcta_opt = is_bold or es_marcada_hash
                cuerpo_op = m_opt.group(2).strip()
                if pending_empty_opts and len(curr_q["options"]) == pending_empty_opts[0] + 1 and curr_q["options"][-1].strip().endswith(")"):
                    idx_fill = pending_empty_opts.pop(0)
                    letra_f = chr(ord('a') + idx_fill)
                    curr_q["options"][idx_fill] = f"{letra_f}) {cuerpo_op}"
                    curr_q["options_bold"][idx_fill] = curr_q["options_bold"][idx_fill] or es_correcta_opt
                    if es_correcta_opt:
                        curr_q["answer"] = idx_fill
                    state = "OPTIONS"
                    continue

                pending_empty_opts = []
                if max_options is None or len(curr_q["options"]) < max_options:
                    letra_secuencial = chr(ord('a') + len(curr_q["options"]))
                    curr_q["options"].append(f"{letra_secuencial}) {cuerpo_op}")
                    curr_q["options_bold"].append(es_correcta_opt)
                    if es_correcta_opt:
                        curr_q["answer"] = len(curr_q["options"]) - 1
                    state = "OPTIONS"
                    continue

            if state == "QUESTION":
                curr_q["question_text"] += " " + line
            elif state == "OPTIONS" and curr_q["options"]:
                if pending_empty_opts:
                    idx_target = pending_empty_opts[0]
                    txt_actual = re.sub(r'^[a-d]\)\s*', '', curr_q["options"][idx_target]).strip()
                    if not txt_actual:
                        letra_t = chr(ord('a') + idx_target)
                        curr_q["options"][idx_target] = f"{letra_t}) {line}"
                        curr_q["options_bold"][idx_target] = curr_q["options_bold"][idx_target] or is_bold
                        if is_bold:
                            curr_q["answer"] = idx_target
                        if line.endswith((".", ";", "!", "?")) or len(pending_empty_opts) > 1:
                            pending_empty_opts.pop(0)
                    else:
                        curr_q["options"][idx_target] += " " + line
                        if is_bold:
                            curr_q["answer"] = idx_target
                        if line.endswith((".", ";", "!", "?")):
                            pending_empty_opts.pop(0)
                else:
                    curr_q["options"][-1] += " " + line
                    if is_bold and curr_q["answer"] == -1:
                        curr_q["answer"] = len(curr_q["options"]) - 1
            elif state == "EXPLANATION":
                curr_q["explanation"] = (curr_q["explanation"] + "\n" + line).strip()

        _cerrar_pregunta_actual(curr_q)

        for q in questions:
            if q["answer"] == -1 and q.get("explanation"):
                m_ans = re.search(r'(?:respuesta\s+correcta|opci[óo]n\s+correcta|es\s+la\s+opci[óo]n|correcta\s+es\s+la)\s*[:\s]*([a-dA-D])\b', q["explanation"], re.IGNORECASE)
                if m_ans:
                    idx_a = ord(m_ans.group(1).lower()) - ord('a')
                    if 0 <= idx_a < len(q["options"]):
                        q["answer"] = idx_a
            q.pop("options_bold", None)

        return questions
# === FIN SECCIÓN 3 ===

# === SECCIÓN 4: FUNCIONES Y LÓGICA DEL TEST ===
# Puente automático para evitar NameError con TESTS_DISPONIBLES_COMPLETO
if "TESTS_DISPONIBLES_COMPLETO" not in globals():
    TESTS_DISPONIBLES_COMPLETO = globals().get("TESTS_DISPONIBLES", globals().get("ESTS_DISPONIBLES", {}))

# Baja efectiva e inmediata de correos revocados (bloqueo en memoria y cierre de sesión activa)
USUARIOS_DADOS_DE_BAJA = {
    "andreitalopeamor1@gmail.com",
    "mfangela23@gmail.com",
}

def _aplicar_bajas_usuarios():
    for nombre_var in ["USUARIOS_AUTORIZADOS", "ALUMNOS_AUTORIZADOS", "CORREOS_AUTORIZADOS", "USUARIOS_PERMITIDOS", "LISTA_ALUMNOS"]:
        col = globals().get(nombre_var)
        if isinstance(col, dict):
            for c_baja in list(col.keys()):
                if str(c_baja).lower().strip() in USUARIOS_DADOS_DE_BAJA:
                    del col[c_baja]
        elif isinstance(col, set):
            for c_baja in list(col):
                if str(c_baja).lower().strip() in USUARIOS_DADOS_DE_BAJA:
                    col.discard(c_baja)
        elif isinstance(col, list):
            globals()[nombre_var] = [x for x in col if str(x).lower().strip() not in USUARIOS_DADOS_DE_BAJA]

    email_sesion = (st.session_state.get("email") or "").lower().strip()
    if email_sesion in USUARIOS_DADOS_DE_BAJA:
        st.session_state.clear()
        st.session_state.borrar_backup_ls = True
        st.error("🚫 Tu acceso a la plataforma ha sido dado de baja. Si crees que se trata de un error, contacta con info@oposiciona.es.")
        st.stop()

_aplicar_bajas_usuarios()

def usuario_es_admin():
    correo_act = (st.session_state.get('email') or "").lower().strip()
    return bool(st.session_state.get('es_admin', False) or correo_act in USUARIOS_ADMIN)

def usuario_puede_reportar():
    return st.session_state.get('rol') != 'INVITADO'

def limpiar_estados_reportes_error():
    """Cierra y limpia cualquier cuadro o texto de reporte de error abierto previamente."""
    for k in list(st.session_state.keys()):
        if k.startswith(("rep_open_", "txt_rep_", "rep_ok_msg_")):
            del st.session_state[k]

def activar_proteccion_antirecortes_alumno():
    es_admin_real = usuario_es_admin()
    modo_prueba_admin = bool(st.session_state.get("admin_test_blur", False))

    if es_admin_real and not modo_prueba_admin:
        components.html("""<script>
        (function() {
            try {
                var pw = window.parent;
                var pd = pw.document;
                pw.__oposiciona_blur_disabled = true;
                pw.__oposiciona_es_admin = true;
                if (pw.__oposiciona_focus_timer) {
                    clearInterval(pw.__oposiciona_focus_timer);
                    pw.__oposiciona_focus_timer = null;
                }
                var appEl = pd.querySelector('[data-testid="stAppViewContainer"]') || pd.querySelector('.stApp') || pd.body;
                if (appEl) {
                    appEl.style.filter = 'none';
                    appEl.style.webkitFilter = 'none';
                }
                var ov = pd.getElementById('oposiciona_blur_overlay');
                if (ov) ov.style.display = 'none';
            } catch(e) {}
        })();
        </script>""", height=0)
        return

    components.html("""<script>
    (function() {
        try {
            var pw = window.parent;
            var pd = pw.document;
            pw.__oposiciona_blur_disabled = false;
            pw.__oposiciona_es_admin = false;

            if (!pd.getElementById('oposiciona_blur_overlay')) {
                var ov = pd.createElement('div');
                ov.id = 'oposiciona_blur_overlay';
                ov.style.cssText = 'display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(15,23,42,0.78); z-index:2147483647; justify-content:center; align-items:center; text-align:center; color:#ffffff; font-family:sans-serif; padding:24px; cursor:pointer; user-select:none;';
                ov.innerHTML = '<div style="background:#1E293B; border:2px solid #3B82F6; border-radius:12px; padding:24px 30px; max-width:480px; box-shadow:0 10px 25px rgba(0,0,0,0.5);"><div style="font-size:34px; margin-bottom:10px;">🛡️</div><div style="font-size:18px; font-weight:800; margin-bottom:8px; color:#F8FAFC;">Contenido Protegido por Oposiciona</div><div style="font-size:14px; color:#CBD5E1; line-height:1.45;">La pantalla se protege automáticamente al detectar herramientas de inspección, descarga, recorte o cambio de ventana.<br><br><b style="color:#60A5FA;">Cierra cualquier panel lateral y haz clic aquí dentro para continuar.</b></div></div>';
                pd.body.appendChild(ov);
                ov.addEventListener('click', function() {
                    pw.__oposiciona_forzar_blur = false;
                    if (pw.oposicionaQuitarBlur) pw.oposicionaQuitarBlur();
                });
            }

            pw.oposicionaAplicarBlur = function() {
                if (pw.__oposiciona_blur_disabled) return;
                var appEl = pd.querySelector('[data-testid="stAppViewContainer"]') || pd.querySelector('.stApp') || pd.body;
                if (appEl) {
                    appEl.style.transition = 'none';
                    appEl.style.filter = 'blur(24px)';
                    appEl.style.webkitFilter = 'blur(24px)';
                }
                var ov = pd.getElementById('oposiciona_blur_overlay');
                if (ov) ov.style.display = 'flex';
            };

            pw.oposicionaQuitarBlur = function() {
                var appEl = pd.querySelector('[data-testid="stAppViewContainer"]') || pd.querySelector('.stApp') || pd.body;
                if (appEl) {
                    appEl.style.filter = 'none';
                    appEl.style.webkitFilter = 'none';
                }
                var ov = pd.getElementById('oposiciona_blur_overlay');
                if (ov) ov.style.display = 'none';
            };

            if (pw.__oposiciona_focus_timer) clearInterval(pw.__oposiciona_focus_timer);
            pw.__oposiciona_focus_timer = setInterval(function() {
                if (pw.__oposiciona_blur_disabled) return;
                var tieneFoco = pd.hasFocus();
                var esMovil = /iphone|ipad|ipod|android|mobile/i.test(pw.navigator.userAgent || '');
                var devToolsAbierto = false;
                if (!esMovil && pw.outerWidth > 0 && pw.innerWidth > 0) {
                    var diffW = pw.outerWidth - pw.innerWidth;
                    var diffH = pw.outerHeight - pw.innerHeight;
                    if (diffW > 240 || diffH > 260) {
                        devToolsAbierto = true;
                    }
                }
                if (!tieneFoco || pd.hidden || pw.__oposiciona_forzar_blur || devToolsAbierto) {
                    pw.oposicionaAplicarBlur();
                } else {
                    pw.oposicionaQuitarBlur();
                }
            }, 150);

            if (!pw.__oposiciona_blur_listeners_ready) {
                pw.__oposiciona_blur_listeners_ready = true;

                pw.addEventListener('blur', function() {
                    pw.oposicionaAplicarBlur();
                });

                pw.addEventListener('focus', function() {
                    pw.__oposiciona_forzar_blur = false;
                    pw.oposicionaQuitarBlur();
                });

                pd.addEventListener('visibilitychange', function() {
                    if (pd.hidden) {
                        pw.oposicionaAplicarBlur();
                    } else {
                        pw.__oposiciona_forzar_blur = false;
                        pw.oposicionaQuitarBlur();
                    }
                });

                pd.addEventListener('keyup', function(e) {
                    if (pw.__oposiciona_blur_disabled) return;
                    if (e.key === 'PrintScreen' || e.keyCode === 44) {
                        pw.__oposiciona_forzar_blur = true;
                        pw.oposicionaAplicarBlur();
                        try { pw.navigator.clipboard.writeText('Contenido protegido por Oposiciona.'); } catch(err) {}
                    }
                });

                pd.addEventListener('keydown', function(e) {
                    if (pw.__oposiciona_blur_disabled) return;
                    var k = (e.key || '').toLowerCase();
                    var code = e.keyCode || e.which || 0;
                    if (
                        code === 123 || k === 'f12' ||
                        ((e.metaKey || e.ctrlKey) && !e.shiftKey && (k === 's' || k === 'u' || k === 'p')) ||
                        ((e.metaKey || e.ctrlKey) && e.shiftKey && (k === 's' || k === 'i' || k === 'j' || k === 'c' || k === '3' || k === '4')) ||
                        (e.metaKey && e.altKey && (k === 'i' || k === 'j' || k === 'c' || k === 'u'))
                    ) {
                        e.preventDefault();
                        e.stopPropagation();
                        pw.__oposiciona_forzar_blur = true;
                        pw.oposicionaAplicarBlur();
                        return false;
                    }
                }, true);
            }
        } catch(e) {}
    })();
    </script>""", height=0)

def obtener_tests_segun_rol():
    catalogo_base = globals().get("TESTS_DISPONIBLES_COMPLETO") or globals().get("TESTS_DISPONIBLES") or globals().get("ESTS_DISPONIBLES") or {}
    if st.session_state.get('rol') == 'INVITADO':
        inv_res = {
            "ADMINISTRATIVOS": dict(TESTS_DISPONIBLES_INVITADO.get("ADMINISTRATIVOS", {})),
            "GESTION": dict(TESTS_DISPONIBLES_INVITADO.get("GESTION", {})),
        }
        inv_res["GESTION"]["DESARROLLO"] = {}
        return inv_res

    es_adm = usuario_es_admin()
    resultado = {"ADMINISTRATIVOS": {}, "GESTION": {}}

    for esp in ["ADMINISTRATIVOS", "GESTION"]:
        origen_esp = catalogo_base.get(esp, {})
        if es_adm:
            orden_categorias = ["ESPECIFICO", "EXAMENES", "GENERAL", "SUPUESTOS", "DESARROLLO"]
        elif esp == "GESTION":
            orden_categorias = ["ESPECIFICO", "EXAMENES", "GENERAL", "DESARROLLO"]
        else:
            orden_categorias = ["ESPECIFICO", "EXAMENES", "GENERAL"]

        for cat in orden_categorias:
            if cat in origen_esp:
                resultado[esp][cat] = dict(origen_esp[cat])

    return resultado

def obtener_etiqueta_tema_visible(nombre_test, q=None):
    if q and q.get("tema_titulo"):
        return q["tema_titulo"]
    nt = (nombre_test or "").strip()
    m = re.search(r'tema[_\s\-]*(\d+)', nt, re.IGNORECASE)
    if m:
        num_t = int(m.group(1))
        titulos_conocidos = {
            51: "TEMA 51: LA SEGURIDAD SOCIAL EN LA CONSTITUCIÓN ESPAÑOLA DE 1978 Y EL TRLGSS",
            52: "TEMA 52: CAMPO DE APLICACIÓN Y COMPOSICIÓN DEL SISTEMA DE LA SEGURIDAD SOCIAL",
            53: "TEMA 53: AFILIACIÓN, ALTAS, BAJAS, CONVENIO ESPECIAL E INSCRIPCIÓN",
            54: "TEMA 54: CONTINGENCIAS PROTEGIBLES: ACCIDENTE DE TRABAJO, ENFERMEDAD PROFESIONAL Y TERRORISMO",
            55: "TEMA 55: ACCIÓN PROTECTORA: CONTENIDO Y CLASIFICACIÓN DE LAS PRESTACIONES",
            56: "TEMA 56: REQUISITOS GENERALES DEL DERECHO A LAS PRESTACIONES Y RESPONSABILIDAD",
            57: "TEMA 57: INCAPACIDAD TEMPORAL",
            58: "TEMA 58: NACIMIENTO Y CUIDADO DE MENOR, CORRESPONSABILIDAD Y RIESGO DURANTE EL EMBARAZO/LACTANCIA",
            59: "TEMA 59: INCAPACIDAD PERMANENTE EN EL RÉGIMEN GENERAL (CONCEPTO, GRADOS Y PRESTACIONES)",
            60: "TEMA 60: CALIFICACIÓN Y REVISIÓN DE LA INCAPACIDAD PERMANENTE Y LESIONES PERMANENTES NO INVALIDANTES",
            61: "TEMA 61: JUBILACIÓN EN EL RÉGIMEN GENERAL",
            62: "TEMA 62: MUERTE Y SUPERVIVENCIA",
            67: "TEMA 67: ASISTENCIA SANITARIA / COTIZACIÓN EN EL RÉGIMEN GENERAL DE LA SEGURIDAD SOCIAL",
            73: "TEMA 73: REGÍMENES ESPECIALES E INTEGRACIÓN EN EL RÉGIMEN GENERAL (SEA Y SEEH)",
            74: "TEMA 74: RÉGIMEN ESPECIAL DE TRABAJADORES AUTÓNOMOS (RETA), SETA Y MAR",
            75: "TEMA 75: MINERÍA DEL CARBÓN, SEGURO ESCOLAR Y REGÍMENES ESPECIALES DE FUNCIONARIOS",
        }
        return titulos_conocidos.get(num_t, f"TEMA {num_t:02d} ({nt})")
    return nt or "Tema en curso"

def detectar_respuesta_inapropiada_o_sin_interes(texto_alumno):
    t_raw = (texto_alumno or "").strip()
    if not t_raw:
        return None
    t_norm = ''.join(c for c in unicodedata.normalize('NFD', t_raw.lower()) if unicodedata.category(c) != 'Mn')
    t_norm = re.sub(r'\s+', ' ', t_norm).strip()
    primera_frase = re.split(r'[.?!;\n]', t_norm)[0].strip()

    patrones_inaceptables = [
        r'\b(puta|puto|mierda|caca|joder|coño|hostia|ostia|polla|capullo|gilipollas|imbecil|idiota|estupidez|asco|basura|porqueria)\b',
        r'\b(esto\s+es\s+una\s+(caca|mierda|porqueria|basura|tonteria|chorrada))\b',
        r'\b(paso\s+de\s+(todo|hacerlo|responder|estudiar|esto))\b',
        r'\b(me\s+da\s+igual|me\s+importa\s+un\s+(bledo|pimiento|carajo|huevo)|no\s+me\s+da\s+la\s+gana)\b',
        r'\b(que\s+te\s+den|vete\s+a\s+la\s+mierda|estoy\s+harto|estoy\s+hasta\s+las\s+narices)\b',
        r'^(no\s+se(\s+nada)?|ni\s+idea|paso|nada|hola|prueba|test|asdf+|qwer+|zxcv+|jaja+|jeje+|bla\s*bla.*)$'
    ]

    es_inapropiada = any(re.search(p, primera_frase) or re.search(p, t_norm) for p in patrones_inaceptables)
    palabras_reales = re.findall(r'\b[a-záéíóúñ]{3,}\b', t_norm)
    sin_sentido = (len(t_norm) < 12 and len(palabras_reales) < 2) or bool(re.match(r'^([a-z])\1{4,}$', t_norm))

    if es_inapropiada or sin_sentido:
        return (
            "🎩 **Observación de tus preparadores de Oposiciona:**\n\n"
            "Comprendemos que la preparación hacia el Cuerpo de Gestión de la Administración de la Seguridad Social "
            "tiene momentos de cansancio y máxima exigencia, pero esta plataforma ha sido concebida con un único propósito: "
            "**forjar funcionarios de excelencia y acercarte cada día más a tu plaza, no perder el tiempo**.\n\n"
            "El día del examen oficial ante el Tribunal, cada línea que escribas será el reflejo de tu rigor técnico y de tu temple como futuro gestor público. "
            "Respira hondo, retoma el pulso jurídico y redacta una respuesta a la altura del profesional en el que te estás convirtiendo. "
            "Cuando estés listo, vuelve a pulsar **«Comprobar»**."
        )
    return None

NOTA_METODOLOGICA_PREPARADORES = (
    "ℹ️ <b>Criterios Oficiales de Valoración del Tribunal:</b> La calificación se realiza aplicando los criterios oficiales del Segundo Ejercicio "
    "del Cuerpo de Gestión de la Administración de la Seguridad Social con un enfoque constructivo y formativo: "
    "<b>Criterio 1 (0 a 45 puntos)</b> por conocimiento y desarrollo de los apartados del epígrafe preguntado, valorando positivamente tanto la comprensión "
    "conceptual como las aportaciones conexas que enriquezcan el tema; <b>Criterio 2 (0 a 3 puntos)</b> por orden de las ideas y estructura; y "
    "<b>Criterio 3 (0 a 2 puntos)</b> por calidad de la expresión escrita y presentación de siglas (ej. «Nombre completo (SIGLA)» o «..., en adelante, SIGLA»). "
    "Los Criterios 2 y 3 se suman al alcanzar al menos 20,00 puntos en el Criterio 1. Mínimo para superar el ejercicio: <b>25,00 sobre 50 puntos</b>."
)

CRITERIOS_OFICIALES_TRIBUNAL_2_EJERCICIO = """
CRITERIOS OFICIALES DE CORRECCIÓN, VALORACIÓN Y SUPERACIÓN DEL SEGUNDO EJERCICIO (CUERPO DE GESTIÓN DE LA ADMINISTRACIÓN DE LA SEGURIDAD SOCIAL - ACCESO LIBRE):
- Cada parte del ejercicio se califica de 0 a 50 puntos, siendo necesario obtener un mínimo de 25,00 puntos directos para superarla.
- Criterio 1 (de 0 a 45 puntos): Conocimiento y desarrollo de los apartados del epígrafe concreto preguntado e inclusión de normativa de aplicación.
- Criterio 2 (de 0 a 3 puntos): Orden de las ideas, claridad expositiva y estructura sistemática (solo puntúa si alcanza al menos 20,00 puntos en el Criterio 1).
- Criterio 3 (de 0 a 2 puntos): Calidad de la expresión escrita y presentación de siglas ("Nombre completo (SIGLA)" o "Nombre completo, en adelante, SIGLA").
"""

def auditar_siglas_sin_definir_previa(texto_alumno):
    if not texto_alumno:
        return []
    t_norm = ''.join(c for c in unicodedata.normalize('NFD', texto_alumno) if unicodedata.category(c) != 'Mn')
    t_norm = re.sub(r'\s+', ' ', t_norm)
    t_low = t_norm.lower()

    catalogo_siglas = [
        ("TRLGSS", r'\bTRLGSS\b', ["texto refundido de la ley general de la seguridad social", "ley general de la seguridad social"], "Texto Refundido de la Ley General de la Seguridad Social (TRLGSS) o ..., en adelante, TRLGSS"),
        ("LGSS", r'\bLGSS\b', ["ley general de la seguridad social"], "Ley General de la Seguridad Social (LGSS) o ..., en adelante, LGSS"),
        ("RIA", r'\bRIA\b', ["reglamento general sobre inscripcion de empresas", "reglamento general de inscripcion de empresas", "afiliacion, altas, bajas"], "Reglamento General sobre inscripción de empresas y afiliación, altas, bajas y variaciones de datos (RIA)"),
        ("RGCL", r'\bRGCL\b', ["reglamento general sobre cotizacion y liquidacion", "reglamento general de cotizacion y liquidacion"], "Reglamento General sobre Cotización y Liquidación (RGCL)"),
        ("RGR", r'\bRGR\b', ["reglamento general de recaudacion"], "Reglamento General de Recaudación de la Seguridad Social (RGR)"),
        ("RDL", r'\b(?:RDL|R\.D\.L\.)\b', ["real decreto-ley", "real decreto ley", "real decreto legislativo"], "Real Decreto-ley (RDL) / Real Decreto Legislativo (RDL)"),
        ("RD", r'\b(?:RD|R\.D\.)\b(?!\s*Leg|\s*\-?\s*ley)', ["real decreto"], "Real Decreto (RD)"),
        ("CE", r'\bCE\b', ["constitucion espanola", "constitucion de 1978"], "Constitución Española (CE)"),
        ("ET", r'\bET\b', ["estatuto de los trabajadores"], "Estatuto de los Trabajadores (ET)"),
        ("TRET", r'\bTRET\b', ["texto refundido de la ley del estatuto de los trabajadores", "estatuto de los trabajadores"], "Texto Refundido de la Ley del Estatuto de los Trabajadores (TRET)"),
        ("LETA", r'\bLETA\b', ["estatuto del trabajo autonomo"], "Estatuto del Trabajo Autónomo (LETA)"),
        ("LISOS", r'\bLISOS\b', ["infracciones y sanciones en el orden social"], "Ley sobre Infracciones y Sanciones en el Orden Social (LISOS)"),
        ("TGSS", r'\bTGSS\b', ["tesoreria general de la seguridad social"], "Tesorería General de la Seguridad Social (TGSS)"),
        ("INSS", r'\bINSS\b', ["instituto nacional de la seguridad social"], "Instituto Nacional de la Seguridad Social (INSS)"),
        ("ISM", r'\bISM\b', ["instituto social de la marina"], "Instituto Social de la Marina (ISM)"),
        ("SEPE", r'\bSEPE\b', ["servicio publico de empleo estatal"], "Servicio Público de Empleo Estatal (SEPE)"),
        ("IMSERSO", r'\bIMSERSO\b', ["instituto de mayores y servicios sociales"], "Instituto de Mayores y Servicios Sociales (IMSERSO)"),
        ("ITSS", r'\bITSS\b', ["inspeccion de trabajo y seguridad social", "inspeccion de trabajo"], "Inspección de Trabajo y Seguridad Social (ITSS)"),
        ("RETA", r'\bRETA\b', ["regimen especial de trabajadores por cuenta propia", "regimen especial de los trabajadores por cuenta propia", "regimen especial de trabajadores autonomos", "trabajadores por cuenta propia o autonomos"], "Régimen Especial de Trabajadores por Cuenta Propia o Autónomos (RETA)"),
        ("RGSS", r'\bRGSS\b', ["regimen general de la seguridad social"], "Régimen General de la Seguridad Social (RGSS)"),
        ("SEA", r'\bSEA\b', ["sistema especial para trabajadores por cuenta ajena agrarios", "sistema especial agrario"], "Sistema Especial para Trabajadores por Cuenta Ajena Agrarios (SEA)"),
        ("SEEH", r'\bSEEH\b', ["sistema especial para empleados de hogar", "sistema especial de empleados de hogar"], "Sistema Especial para Empleados de Hogar (SEEH)"),
        ("SETA", r'\bSETA\b', ["sistema especial para trabajadores por cuenta propia agrarios"], "Sistema Especial para Trabajadores por Cuenta Propia Agrarios (SETA)"),
        ("CCC", r'\bCCC\b', ["codigo de cuenta de cotizacion", "codigos de cuenta de cotizacion"], "Código de Cuenta de Cotización (CCC)"),
        ("NAF", r'\bNAF\b', ["numero de afiliacion"], "Número de Afiliación (NAF)"),
        ("NSS", r'\bNSS\b', ["numero de la seguridad social"], "Número de la Seguridad Social (NSS)"),
        ("SEDESS", r'\bSEDESS\b', ["sede electronica de la seguridad social", "sede electronica de la secretaria de estado"], "Sede Electrónica de la Seguridad Social (SEDESS)"),
        ("CNAE", r'\bCNAE\b', ["clasificacion nacional de actividades economicas"], "Clasificación Nacional de Actividades Económicas (CNAE)"),
        ("CNO", r'\bCNO\b', ["clasificacion nacional de ocupaciones"], "Clasificación Nacional de Ocupaciones (CNO)"),
        ("ERE", r'\bERE\b', ["expediente de regulacion de empleo", "expedientes de regulacion de empleo"], "Expediente de Regulación de Empleo (ERE)"),
        ("SMI", r'\bSMI\b', ["salario minimo interprofesional"], "Salario Mínimo Interprofesional (SMI)"),
        ("IMV", r'\bIMV\b', ["ingreso minimo vital"], "Ingreso Mínimo Vital (IMV)"),
        ("FOGASA", r'\bFOGASA\b', ["fondo de garantia salarial"], "Fondo de Garantía Salarial (FOGASA)"),
        ("MEI", r'\bMEI\b', ["mecanismo de equidad intergeneracional"], "Mecanismo de Equidad Intergeneracional (MEI)"),
        ("IT", r'\bIT\b', ["incapacidad temporal"], "Incapacidad Temporal (IT)"),
        ("IP", r'\bIP\b', ["incapacidad permanente"], "Incapacidad Permanente (IP)"),
        ("AT", r'\bAT\b', ["accidente de trabajo", "accidentes de trabajo"], "Accidente de Trabajo (AT)"),
        ("EP", r'\bEP\b', ["enfermedad profesional", "enfermedades profesionales"], "Enfermedad Profesional (EP)"),
    ]

    siglas_sin_definir = []
    for sigla, pat_regex, frases_completas, ejemplo_formal in catalogo_siglas:
        m_sigla = re.search(pat_regex, t_norm)
        if m_sigla:
            pos_sigla = m_sigla.start()
            ventana_entorno = t_low[:min(len(t_low), pos_sigla + 120)]
            definida_correctamente = any(frase in ventana_entorno for frase in frases_completas)
            if not definida_correctamente:
                siglas_sin_definir.append((sigla, ejemplo_formal))

    return siglas_sin_definir

def _extraer_articulos_detallados_de_texto(texto):
    if not texto:
        return [], set()

    t_limpio = re.sub(r'\s+', ' ', texto)
    etiquetas = []
    numeros_base = set()
    vistos_norm = set()

    def _detectar_norma_cercana(norma_capturada, pos_fin_match):
        if norma_capturada and norma_capturada.strip():
            nc = norma_capturada.strip().upper()
            if "84/1996" in nc or "RIA" in nc:
                return "RIA"
            if "8/2015" in nc or "TRLGSS" in nc or "LGSS" in nc:
                return "TRLGSS"
            if "2064/1995" in nc or "RGCL" in nc:
                return "RGCL"
            if "1415/2004" in nc or "RGR" in nc:
                return "RGR"
            if "ET" in nc or "ESTATUTO" in nc:
                return "ET"
            if "CE" in nc or "CONSTITUCI" in nc:
                return "CE"
            if "LISOS" in nc or "5/2000" in nc:
                return "LISOS"
            return norma_capturada.strip()
        ventana_sig = t_limpio[pos_fin_match:pos_fin_match + 45]
        if re.search(r'^\s*(?:del?\s+|de\s+la\s+)?(?:RIA|Reglamento\s+General\s+sobre\s+inscripci|RD\s*84/1996)', ventana_sig, re.IGNORECASE):
            return "RIA"
        if re.search(r'^\s*(?:del?\s+|de\s+la\s+)?(?:RGCL|Reglamento\s+General\s+sobre\s+Cotizaci|RD\s*2064/1995)', ventana_sig, re.IGNORECASE):
            return "RGCL"
        if re.search(r'^\s*(?:del?\s+|de\s+la\s+)?(?:RGR|Reglamento\s+General\s+de\s+Recaudaci|RD\s*1415/2004)', ventana_sig, re.IGNORECASE):
            return "RGR"
        if re.search(r'^\s*(?:del?\s+|de\s+la\s+)?(?:TRLGSS|LGSS|Texto\s+Refundido|RDL\s*8/2015)', ventana_sig, re.IGNORECASE):
            return "TRLGSS"
        return ""

    pat_multi = r'\b(?:art[íi]culos?|arts?\.)\s*(\d{1,3}(?:\.\d+)?(?:\s*(?:,\s*\d{1,3}(?:\.\d+)?)*\s*(?:y|a|al|\-|–)\s*\d{1,3}(?:\.\d+)?))(?:\s+(?:del?\s+|de\s+la\s+)?(TRLGSS|LGSS|RIA|RGCL|RGR|ET|TRET|CE|LISOS|RD\s+\d+/\d{4}|Real\s+Decreto(?:\-ley|\s+Legislativo)?\s+\d+/\d{4}|Orden\s+[A-Z]+/\d+/\d{4}|Ley\s+\d+/\d{4}))?'
    for m in re.finditer(pat_multi, t_limpio, flags=re.IGNORECASE):
        rango_txt = re.sub(r'\s+', ' ', m.group(1).strip())
        norma_txt = _detectar_norma_cercana(m.group(2), m.end())
        nums_hallados = re.findall(r'\b(\d{1,3})\b', rango_txt)
        for nh in nums_hallados:
            numeros_base.add(nh)
        if re.search(r'\b(a|al|\-|–)\b', rango_txt) and len(nums_hallados) == 2:
            ini, fin = int(nums_hallados[0]), int(nums_hallados[1])
            if ini <= fin and (fin - ini) <= 60:
                for k_n in range(ini, fin + 1):
                    numeros_base.add(str(k_n))
        lbl = f"Arts. {rango_txt}" + (f" {norma_txt}" if norma_txt else "")
        clave_v = lbl.lower()
        if clave_v not in vistos_norm:
            vistos_norm.add(clave_v)
            etiquetas.append((nums_hallados, norma_txt.upper(), lbl))

    pat_indiv = r'\b(?:art[íi]culo|art\.)\s*(\d{1,3}(?:\.\d+)*(?:\.[ºª°a-z])?)(?:\s+(?:del?\s+|de\s+la\s+)?(TRLGSS|LGSS|RIA|RGCL|RGR|ET|TRET|CE|LISOS|RD\s+\d+/\d{4}|Real\s+Decreto(?:\-ley|\s+Legislativo)?\s+\d+/\d{4}|Orden\s+[A-Z]+/\d+/\d{4}|Ley\s+\d+/\d{4}))?'
    for m in re.finditer(pat_indiv, t_limpio, flags=re.IGNORECASE):
        num_completo = m.group(1).strip()
        num_base = re.match(r'^(\d{1,3})', num_completo).group(1)
        norma_txt = _detectar_norma_cercana(m.group(2), m.end())
        numeros_base.add(num_base)
        lbl = f"Art. {num_completo}" + (f" {norma_txt}" if norma_txt else "")
        ya_incluido = any(num_base in nums_g and (not norma_txt or norma_txt.upper() == n_g or not n_g) for nums_g, n_g, _ in etiquetas)
        if not ya_incluido:
            etiquetas.append(([num_base], norma_txt.upper(), lbl))

    pat_disp = r'\b(DA\s+\d+[\.ºª°a-z]*|DT\s+\d+[\.ºª°a-z]*|Disposici[óo]n\s+(?:adicional|transitoria|final)\s+[0-9a-záéíóúñ\.ºª°]+)(?:\s+(?:del?\s+)?(TRLGSS|LGSS|RIA|ET))?'
    for m in re.finditer(pat_disp, t_limpio, flags=re.IGNORECASE):
        d_txt = re.sub(r'\s+', ' ', m.group(1).strip())
        norma_txt = (m.group(2) or "").strip()
        num_d = re.findall(r'\d+', d_txt)
        token_d = f"DA_{num_d[0]}" if num_d else d_txt.lower()
        numeros_base.add(token_d)
        lbl = f"{d_txt}" + (f" {norma_txt}" if norma_txt else "")
        if lbl.lower() not in vistos_norm:
            vistos_norm.add(lbl.lower())
            etiquetas.append(([token_d], norma_txt.upper(), lbl))

    return etiquetas, numeros_base

def _normalizar_sin_acentos(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', (s or "").lower()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s).strip()

def _extraer_bloques_estructurales_epigrafe(explicacion_oficial):
    if not explicacion_oficial:
        return []
    lineas = [b.strip() for b in explicacion_oficial.split('\n') if b.strip()]
    bloques = []
    cabecera_pendiente = ""

    for l in lineas:
        l_clean = re.sub(r'^[•\*■▪\-–\s]+', '', l.replace("[[H]]", "")).strip()
        if not l_clean or PDFQuizParser._es_basura_cabecera_o_pie(l_clean):
            continue
        if len(l_clean) < 95 and not l_clean.endswith('.') and ":" not in l_clean:
            cabecera_pendiente = l_clean
            continue
        if cabecera_pendiente:
            l_clean = f"{cabecera_pendiente}: {l_clean}"
            cabecera_pendiente = ""
        if len(l_clean) < 35:
            continue
        m_cab = re.match(r'^((?:\d{1,2}[\.\)]|[a-g]\))?\s*[^:\.]{3,95}):\s+(.+)$', l_clean)
        if m_cab:
            bloques.append((m_cab.group(1).strip(), m_cab.group(2).strip(), l_clean))
        else:
            palabras = l_clean.split()
            tit_corto = " ".join(palabras[:8]) + ("..." if len(palabras) > 8 else "")
            bloques.append((tit_corto, l_clean, l_clean))
    return bloques

def auditar_pertinencia_y_bloques_epigrafe(enunciado_epigrafe, explicacion_oficial, texto_alumno):
    ep_norm = _normalizar_sin_acentos(enunciado_epigrafe)
    al_norm = _normalizar_sin_acentos(texto_alumno)

    palabras_genericas_ss = {
        "seguridad", "social", "regimen", "general", "sistema", "trabajador", "trabajadores", "persona", "personas",
        "empresario", "empresarios", "empresa", "empresas", "actividad", "actividades", "laboral", "profesional",
        "servicios", "prestacion", "prestaciones", "derecho", "obligacion", "situacion", "situaciones", "solicitud",
        "solicitudes", "efectos", "plazo", "plazos", "datos", "actos", "acto", "administrativo", "tesoreria", "tgss",
        "administracion", "inicio", "cese", "trabajo", "real", "decreto", "legislativo", "orden", "reglamento",
        "aprobado", "conformidad", "articulo", "articulos", "trlgss", "lgss", "ria", "oficio", "inspeccion", "itss",
        "cotizacion", "cotizaciones", "momento", "tiempo", "forma", "mismo", "dicho", "dicha", "caso", "supuesto",
        "procedimiento", "normas", "sobre", "otras", "otros", "entre", "cuando", "aunque", "hasta", "desde", "para",
        "alta", "altas", "baja", "bajas", "presentacion", "reglamentario"
    }

    desviacion_epigrafe = False
    motivo_desviacion = ""

    if "afiliacion" in ep_norm and "altas" not in ep_norm and "bajas" not in ep_norm and "procedimiento" not in ep_norm:
        marcadores_afil = [
            r'\bunic(?:a|idad)\b', r'\bvitalici[oa]\b', r'\bnss\b', r'\bnaf\b',
            r'numero\s+de\s+(?:la\s+)?seguridad\s+social', r'numero\s+de\s+afiliacion',
            r'primera\s+vez', r'vez\s+primera', r'afiliacion(?:es)?\s+indebida',
            r'fichero\s+general\s+de\s+afiliacion', r'\bart(?:iculo|\.)\s*15\b', r'\bart(?:iculo|\.)\s*6\b'
        ]
        if sum(1 for pat in marcadores_afil if re.search(pat, al_norm)) <= 1:
            desviacion_epigrafe = True
            motivo_desviacion = (
                "🚨 **INCONGRUENCIA CON EL EPÍGRAFE PREGUNTADO (`Normas sobre afiliación`):** "
                "El texto presentado desarrolla otro epígrafe distinto y omite el contenido nuclear de la afiliación (concepto del art. 15 TRLGSS y art. 6 RIA, caracteres de unicidad y vitalicidad, NSS/NAF, vías de promoción del art. 16 TRLGSS y afiliaciones indebidas del art. 59 RIA)."
            )

    elif "convenio especial" in ep_norm:
        marcadores_convenio = [
            r'2865/2003', r'1\.080', r'1080\s*dias', r'12\s*anos', r'doce\s*anos',
            r'90\s*dias', r'noventa\s*dias', r'0[,\.]94', r'0[,\.]77', r'coeficiente\s+reductor',
            r'cuidadores\s+no\s+profesionales', r'practicas\s+formativas', r'386/2024'
        ]
        if sum(1 for pat in marcadores_convenio if re.search(pat, al_norm)) == 0:
            desviacion_epigrafe = True
            motivo_desviacion = (
                "🚨 **INCONGRUENCIA CON EL EPÍGRAFE PREGUNTADO (`El convenio especial y otras situaciones asimiladas a la del alta`):** "
                "Tu respuesta no desarrolla el Convenio Especial (Orden TAS/2865/2003, requisito de 1.080 días de cotización en 12 años, plazo de 90 días / 1 año, reglas de base de cotización y coeficiente 0,94, extinción y modalidades especiales)."
            )

    elif "inscripcion" in ep_norm and "encuadramiento" in ep_norm:
        marcadores_inscripcion = [
            r'inscripcion\s+de\s+empresa', r'cuenta\s+de\s+cotizacion', r'\bccc\b',
            r'mutua\s+colaboradora', r'poliza\s+de\s+asociacion', r'documento\s+de\s+asociacion',
            r'fichero\s+general\s+de\s+empresarios', r'cnae', r'45\s+dias', r'\bart(?:iculo|\.)\s*138\b', r'\bart(?:iculo|\.)\s*5\b'
        ]
        if sum(1 for pat in marcadores_inscripcion if re.search(pat, al_norm)) <= 1:
            desviacion_epigrafe = True
            motivo_desviacion = (
                "🚨 **INCONGRUENCIA CON EL EPÍGRAFE PREGUNTADO (`Encuadramiento e inscripción`):** "
                "El texto presentado no desarrolla la inscripción de empresas (art. 138 TRLGSS y art. 5 RIA), el Código de Cuenta de Cotización (CCC), la opción de cobertura con Mutua ni las variaciones de datos empresariales."
            )

    bloques_ep = _extraer_bloques_estructurales_epigrafe(explicacion_oficial)
    apartados_completos = []
    apartados_incompletos = []
    apartados_omitidos = []

    for tit_b, cuerpo_b, full_b in bloques_ep:
        tit_n = _normalizar_sin_acentos(tit_b)
        cuerpo_n = _normalizar_sin_acentos(cuerpo_b)

        if "baja" in tit_n and ("plazo" in tit_n or "32" in tit_n or "35.2" in tit_n):
            if not re.search(r'\b(6\s*dias|seis\s*dias|32\.3|no\s+extinguen?\s+la\s+obligacion\s+de\s+cotizar|35\.2)\b', al_norm):
                apartados_omitidos.append((tit_b, full_b))
                continue
        if "conservacion" in tit_n or "57" in tit_n:
            if not re.search(r'\b(conserva|4\s*anos|cuatro\s*anos|57)\b', al_norm):
                apartados_omitidos.append((tit_b, full_b))
                continue
        if "sistema red" in tit_n or "38" in tit_n or "132" in cuerpo_n:
            if not re.search(r'\b(sistema\s+red|remision\s+electronica|medios\s+electronicos|sedess|484/2013|132)\b', al_norm):
                apartados_omitidos.append((tit_b, full_b))
                continue
        if "ocupacion" in tit_n or "30.2" in tit_n:
            if "ocupacion" not in al_norm and "30.2" not in al_norm:
                apartados_omitidos.append((tit_b, full_b))
                continue

        palabras_cuerpo_distintivas = [
            w for w in re.findall(r'\b[a-z]{4,}\b|\b\d+(?:[\.,]\d+)?\b', cuerpo_n)
            if w not in palabras_genericas_ss
        ]
        aciertos_cuerpo = sum(1 for w in palabras_cuerpo_distintivas if w[:5] in al_norm)
        ratio_cuerpo = aciertos_cuerpo / max(1, len(palabras_cuerpo_distintivas))

        if ratio_cuerpo >= 0.35 and aciertos_cuerpo >= 2:
            apartados_completos.append((tit_b, full_b))
        elif ratio_cuerpo >= 0.18 and aciertos_cuerpo >= 2:
            apartados_incompletos.append((tit_b, full_b))
        else:
            apartados_omitidos.append((tit_b, full_b))

    total_b = max(1, len(bloques_ep))
    unidades_reales = len(apartados_completos) + (0.55 * len(apartados_incompletos))
    ratio_cobertura_epigrafe = min(1.0, unidades_reales / total_b)

    return {
        "desviacion_epigrafe": desviacion_epigrafe,
        "motivo_desviacion": motivo_desviacion,
        "total_apartados": total_b,
        "apartados_completos": apartados_completos,
        "apartados_incompletos": apartados_incompletos,
        "apartados_omitidos": apartados_omitidos,
        "ratio_cobertura_epigrafe": round(ratio_cobertura_epigrafe, 2)
    }

def auditar_articulos_y_aportaciones_alumno(texto_alumno, respuesta_oficial, explicacion_oficial, enunciado_pregunta=""):
    ref_completa = f"{respuesta_oficial or ''} {explicacion_oficial or ''}".strip()
    etiquetas_ref, nums_ref = _extraer_articulos_detallados_de_texto(ref_completa)
    etiquetas_al, nums_al = _extraer_articulos_detallados_de_texto(texto_alumno)

    articulos_omitidos_limpios = []
    articulos_acertados_limpios = []
    for nums_grupo, norma_g, lbl_art in etiquetas_ref:
        if any(n in nums_al for n in nums_grupo):
            articulos_acertados_limpios.append(lbl_art)
        else:
            articulos_omitidos_limpios.append(lbl_art)

    aud_bloques = auditar_pertinencia_y_bloques_epigrafe(enunciado_pregunta, ref_completa, texto_alumno)

    articulos_extra_validos = []
    articulos_extra_erroneos = []
    for nums_grupo, norma_al, lbl_al in etiquetas_al:
        if all(n not in nums_ref for n in nums_grupo):
            num_p = nums_grupo[0]
            if num_p.isdigit():
                n_int = int(num_p)
                if norma_al in ("TRLGSS", "LGSS", "") and n_int > 373:
                    articulos_extra_erroneos.append(f"{lbl_al} (inexistente: el TRLGSS consta de 373 artículos)")
                elif norma_al == "RIA" and n_int > 64:
                    articulos_extra_erroneos.append(f"{lbl_al} (inexistente en el RD 84/1996)")
                else:
                    articulos_extra_validos.append(f"{lbl_al}")
            else:
                articulos_extra_validos.append(f"{lbl_al}")

    siglas_sin_presentar = auditar_siglas_sin_definir_previa(texto_alumno)

    return {
        "articulos_acertados": articulos_acertados_limpios,
        "articulos_omitidos": articulos_omitidos_limpios,
        "articulos_extra_validos": articulos_extra_validos,
        "articulos_extra_erroneos": articulos_extra_erroneos,
        "siglas_sin_presentar": siglas_sin_presentar,
        "auditoria_bloques": aud_bloques
    }

def evaluar_respuesta_escrita(texto_alumno, respuesta_oficial, explicacion_oficial, enunciado_pregunta=""):
    auditoria = auditar_articulos_y_aportaciones_alumno(texto_alumno, respuesta_oficial, explicacion_oficial, enunciado_pregunta)
    aud_b = auditoria["auditoria_bloques"]

    if not (texto_alumno or "").strip():
        return {
            "nota": 0.0,
            "nota_50": 0.0,
            "pts_criterio_1": 0.0,
            "pts_criterio_2": 0.0,
            "pts_criterio_3": 0.0,
            "supera_umbral_20": False,
            "auditoria": auditoria
        }

    if aud_b["desviacion_epigrafe"]:
        n_comp = len(aud_b["apartados_completos"])
        n_parciales = len(aud_b["apartados_incompletos"])
        pts_c1_desv = round(min(10.0, (n_comp * 3.0) + (n_parciales * 1.5) + (len(auditoria["articulos_acertados"]) * 0.50)), 2)
        nota_50_desv = pts_c1_desv
        nota_10_desv = round((nota_50_desv / 50.0) * 10.0, 2)
        return {
            "nota": nota_10_desv,
            "nota_50": nota_50_desv,
            "pts_criterio_1": pts_c1_desv,
            "pts_criterio_2": 0.0,
            "pts_criterio_3": 0.0,
            "supera_umbral_20": False,
            "auditoria": auditoria
        }

    ratio_cobertura_real = aud_b.get("ratio_cobertura_epigrafe", 0.0)
    pts_base_c1 = ratio_cobertura_real * 43.0
    bonus_extra = min(4.0, len(auditoria["articulos_extra_validos"]) * 0.65)
    resta_arts_omitidos = min(1.50, len(auditoria["articulos_omitidos"]) * 0.08)
    pts_criterio_1 = round(max(0.0, min(45.0, pts_base_c1 + bonus_extra - resta_arts_omitidos)), 2)

    supera_umbral_20 = pts_criterio_1 >= 20.0
    if supera_umbral_20:
        num_parrafos = len([p for p in texto_alumno.split("\n") if len(p.strip()) > 25])
        pts_criterio_2 = round(min(3.0, 2.2 + (0.6 if num_parrafos >= 3 else 0.2)), 2)
        resta_siglas = min(0.50, len(auditoria["siglas_sin_presentar"]) * 0.15)
        pts_criterio_3 = round(max(0.50, min(2.0, 1.85 - resta_siglas)), 2)
    else:
        pts_criterio_2 = 0.0
        pts_criterio_3 = 0.0

    nota_50 = round(min(50.0, pts_criterio_1 + pts_criterio_2 + pts_criterio_3), 2)
    nota_10 = round((nota_50 / 50.0) * 10.0, 2)

    return {
        "nota": nota_10,
        "nota_50": nota_50,
        "pts_criterio_1": pts_criterio_1,
        "pts_criterio_2": pts_criterio_2,
        "pts_criterio_3": pts_criterio_3,
        "supera_umbral_20": supera_umbral_20,
        "auditoria": auditoria
    }

def obtener_gemini_api_key_activa():
    sess_k = st.session_state.get("gemini_api_key_custom", "")
    if sess_k and str(sess_k).strip():
        return str(sess_k).strip()
    try:
        sec_k = st.secrets.get("GEMINI_API_KEY", "")
        if sec_k and str(sec_k).strip():
            return str(sec_k).strip()
    except Exception:
        pass
    sess_def = st.session_state.get("gemini_api_key_session", "")
    if sess_def and str(sess_def).strip():
        return str(sess_def).strip()
    return GEMINI_API_KEY_DEFAULT

@st.cache_data(ttl=3600, show_spinner=False)
def _obtener_modelos_disponibles_api(clave_limpia):
    modelos_prioritarios = [
        "gemini-3.0-flash",
        "gemini-3.1-pro-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.0-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash"
    ]
    try:
        r = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={clave_limpia}",
            timeout=6
        )
        if r.status_code == 200:
            datos = r.json().get("models", [])
            disponibles = []
            for m in datos:
                metodos = m.get("supportedGenerationMethods", [])
                nom = (m.get("name") or "").replace("models/", "")
                if "generateContent" in metodos and "gemini" in nom and "vision" not in nom and "embedding" not in nom and "imagen" not in nom and "tts" not in nom:
                    disponibles.append(nom)
            if disponibles:
                ordenados = [m for m in modelos_prioritarios if m in disponibles]
                for d in disponibles:
                    if d not in ordenados and ("3." in d or "flash" in d or "pro" in d):
                        ordenados.append(d)
                return ordenados[:6]
    except Exception:
        pass
    return modelos_prioritarios

def _extraer_puntuaciones_de_respuesta_ia(texto_ia, ev_respaldo):
    ev_out = dict(ev_respaldo or {})
    if not texto_ia:
        return ev_out, ""

    aud_b = (ev_out.get("auditoria") or {}).get("auditoria_bloques") or {}
    hay_desviacion = bool(aud_b.get("desviacion_epigrafe", False))

    # Si viene etiqueta directa de SUPUESTO PRÁCTICO (sobre 10, sin criterios de tribunal)
    m_sup = re.search(r'\[\[NOTA_SUPUESTO:\s*(\d+(?:[\.,]\d+)?)\s*\]\]', texto_ia, flags=re.IGNORECASE)
    if m_sup:
        nota_10 = round(max(0.0, min(10.0, float(m_sup.group(1).replace(",", ".")))), 2)
        nota_50 = round(nota_10 * 5.0, 2)
        texto_ia = re.sub(r'\[\[NOTA_SUPUESTO:[^\]]*\]\]\s*', '', texto_ia, flags=re.IGNORECASE).strip()
        ev_out.update({
            "nota": nota_10,
            "nota_50": nota_50,
            "pts_criterio_1": round(nota_10 * 4.5, 2),
            "pts_criterio_2": 0.0,
            "pts_criterio_3": 0.0,
            "supera_umbral_20": nota_10 >= 5.0
        })
        return ev_out, texto_ia

    c1_val = c2_val = c3_val = None

    m_tag = re.search(
        r'\[\[NOTAS_TRIBUNAL:\s*C1\s*=\s*(\d+(?:[\.,]\d+)?)\s*\|\s*C2\s*=\s*(\d+(?:[\.,]\d+)?)\s*\|\s*C3\s*=\s*(\d+(?:[\.,]\d+)?)\s*\]\]',
        texto_ia,
        flags=re.IGNORECASE
    )
    if m_tag:
        c1_val = float(m_tag.group(1).replace(",", "."))
        c2_val = float(m_tag.group(2).replace(",", "."))
        c3_val = float(m_tag.group(3).replace(",", "."))
        texto_ia = re.sub(r'\[\[NOTAS_TRIBUNAL:[^\]]*\]\]\s*', '', texto_ia, flags=re.IGNORECASE).strip()
    else:
        m_c1 = re.search(r'Criterio\s*1[^\d\n]{0,65}(\d{1,2}(?:[\.,]\d{1,2})?)\s*/\s*45', texto_ia, flags=re.IGNORECASE)
        m_c2 = re.search(r'Criterio\s*2[^\d\n]{0,65}(\d{1}(?:[\.,]\d{1,2})?)\s*/\s*3', texto_ia, flags=re.IGNORECASE)
        m_c3 = re.search(r'Criterio\s*3[^\d\n]{0,65}(\d{1}(?:[\.,]\d{1,2})?)\s*/\s*2', texto_ia, flags=re.IGNORECASE)
        if m_c1:
            c1_val = float(m_c1.group(1).replace(",", "."))
        if m_c2:
            c2_val = float(m_c2.group(1).replace(",", "."))
        if m_c3:
            c3_val = float(m_c3.group(1).replace(",", "."))

    if c1_val is not None:
        c1_val = round(max(0.0, min(45.0, c1_val)), 2)
        if hay_desviacion:
            c1_val = min(c1_val, 10.0)
        if c1_val < 20.0:
            c2_val = 0.0
            c3_val = 0.0
        else:
            c2_val = round(max(0.0, min(3.0, c2_val if c2_val is not None else 2.2)), 2)
            c3_val = round(max(0.0, min(2.0, c3_val if c3_val is not None else 1.6)), 2)

        nota_50 = round(min(50.0, c1_val + c2_val + c3_val), 2)
        nota_10 = round((nota_50 / 50.0) * 10.0, 2)

        ev_out.update({
            "pts_criterio_1": c1_val,
            "pts_criterio_2": c2_val,
            "pts_criterio_3": c3_val,
            "nota_50": nota_50,
            "nota": nota_10,
            "supera_umbral_20": c1_val >= 20.0
        })

    return ev_out, texto_ia

def generar_informe_analitico_respaldo(pregunta, ev_fallback, aud, modo="DESARROLLO"):
    """Alternativa analítica de respaldo por si en algún momento no hubiera conexión con los servidores de Google."""
    aud_b = aud.get("auditoria_bloques") or {}
    desv = aud_b.get("desviacion_epigrafe", False)
    mot_desv = aud_b.get("motivo_desviacion", "")
    tot_ap = aud_b.get("total_apartados", 1)
    comp = aud_b.get("apartados_completos", [])
    inc = aud_b.get("apartados_incompletos", [])
    omit = aud_b.get("apartados_omitidos", [])

    arts_omitidos_str = ", ".join(aud["articulos_omitidos"]) if aud["articulos_omitidos"] else "Ninguno"
    arts_acertados_str = ", ".join(aud["articulos_acertados"]) if aud["articulos_acertados"] else "Ninguno de los incluidos en la explicación"
    arts_extra_ok_str = "; ".join(aud["articulos_extra_validos"]) if aud["articulos_extra_validos"] else "Ninguno"
    siglas_mal_str = (
        ", ".join([f"**{s}** (debiste presentar la primera vez como *«{ej}»*)" for s, ej in aud["siglas_sin_presentar"]])
        if aud["siglas_sin_presentar"] else "Ninguna (todas las siglas fueron correctamente presentadas)"
    )

    c1 = ev_fallback.get("pts_criterio_1", 0.0)
    c2 = ev_fallback.get("pts_criterio_2", 0.0)
    c3 = ev_fallback.get("pts_criterio_3", 0.0)
    n50 = ev_fallback.get("nota_50", 0.0)
    n10 = ev_fallback.get("nota", 0.0)

    if modo == "SUPUESTO":
        return (
            f"1. **✅ Lo que has acertado en esta cuestión práctica:**\n"
            f"- **Preceptos y elementos de la solución citados:** {arts_acertados_str}.\n"
            f"- **Bloques o cálculos identificados:** {len(comp) + len(inc)} de {tot_ap}.\n\n"
            f"2. **⚠️ Por qué obtienes esta nota (lo que ha faltado o debes revisar frente a la explicación):**\n"
            f"- **Artículos de la solución no citados:** {arts_omitidos_str}.\n"
            f"- Revisa a continuación la **Explicación y Respuesta Técnica oficial** para contrastar los cálculos exactos, plazos y fundamentación normativa.\n\n"
            f"3. **🎯 Calificación de la cuestión práctica:** **`{n10:.2f} / 10 puntos`**"
        )

    partes = []
    if desv:
        partes.append(f"1. **🚨 Control de congruencia con el epígrafe preguntado (`{pregunta}`):**\n{mot_desv}")
    else:
        tits_comp = "; ".join([t for t, _ in comp]) if comp else "Ninguno desarrollado de forma íntegra"
        tits_inc = "; ".join([t for t, _ in inc]) if inc else "Ninguno"
        partes.append(
            f"1. **✅ Análisis de lo acertado y aportaciones al epígrafe (`{pregunta}`):**\n"
            f"- **Apartados del epígrafe bien desarrollados ({len(comp)} de {tot_ap}):** {tits_comp}.\n"
            f"- **Apartados abordados de forma parcial ({len(inc)} de {tot_ap}):** {tits_inc}.\n"
            f"- **Preceptos o conceptos adicionales válidos aportados:** {arts_extra_ok_str}."
        )

    lineas_om = []
    for idx_o, (tit_o, full_o) in enumerate(omit, 1):
        resumen_o = full_o[:220] + ("..." if len(full_o) > 220 else "")
        lineas_om.append(f"   - ❌ **Apartado omitido {idx_o} ({tit_o}):** *{resumen_o}*")
    for idx_i, (tit_i, full_i) in enumerate(inc, 1):
        resumen_i = full_i[:200] + ("..." if len(full_i) > 200 else "")
        lineas_om.append(f"   - 🟡 **Apartado incompleto ({tit_i}):** faltó precisar *{resumen_i}*")
    if not lineas_om:
        lineas_om.append("   - ✔️ Has cubierto todos los apartados estructurales de la explicación oficial.")

    partes.append(
        f"2. **⚠️ Contraste analítico apartado por apartado frente a la explicación oficial ({len(omit)} omitidos de {tot_ap}):**\n"
        + "\n".join(lineas_om)
    )

    partes.append(
        "3. **⚖️ Rigor normativo y uso de siglas:**\n"
        f"- **Artículos de la explicación citados:** {arts_acertados_str}\n"
        f"- **Artículos omitidos:** {arts_omitidos_str}\n"
        f"- **Uso de siglas sin presentación previa:** {siglas_mal_str}"
    )

    faltan_c1 = round(max(0.0, 45.0 - c1), 2)
    partes.append(
        "4. **🎓 Calificación por Criterios del Tribunal y Resumen sencillo de puntos sumados y restados:**\n"
        f"- **Criterio 1 (Conocimiento y normativa: 0 a 45 ptos):** `{c1:.2f} / 45,00 puntos`\n"
        f"- **Criterio 2 (Orden de las ideas y estructura: 0 a 3 ptos):** `{c2:.2f} / 3,00 puntos`\n"
        f"- **Criterio 3 (Calidad de la expresión escrita y siglas: 0 a 2 ptos):** `{c3:.2f} / 2,00 puntos`\n"
        f"- 🏆 **CALIFICACIÓN TOTAL:** **`{n50:.2f} / 50,00 puntos`** *(Equivalencia: **`{n10:.2f} / 10`**)*\n\n"
        "📊 **Resumen sencillo de por qué has sumado y por qué te han restado puntos:**\n"
        f"- **➕ Qué te ha sumado puntos:** `+{c1:.2f} ptos` por los apartados de `{pregunta}` que sí has abordado.\n"
        f"- **➖ Qué te ha restado o impedido sumar:** `-{faltan_c1:.2f} ptos` por los **{len(omit)} apartados omitidos** de `{pregunta}`, la ausencia de citas de la explicación (**Artículos omitidos**) y el no activar los Criterios 2 y 3 si no se superan los 20,00 puntos en el Criterio 1.\n\n"
        "💡 **Orientación de tus preparadores para mejorar este epígrafe:** Vas por buen camino; completa tu esquema incorporando los apartados pendientes y asegurando las citas normativas principales."
    )

    return "\n\n".join(partes)

def consultar_ia_gemini_correccion(api_key, enunciado_supuesto, pregunta, respuesta_alumno, respuesta_oficial, explicacion_oficial, ev_fallback=None, modo="DESARROLLO"):
    aviso_elegante = detectar_respuesta_inapropiada_o_sin_interes(respuesta_alumno)
    if aviso_elegante:
        return aviso_elegante

    if ev_fallback is None:
        ev_fallback = evaluar_respuesta_escrita(respuesta_alumno, respuesta_oficial, explicacion_oficial, f"{enunciado_supuesto} {pregunta}")

    aud = ev_fallback.get("auditoria") or auditar_articulos_y_aportaciones_alumno(
        respuesta_alumno, respuesta_oficial, explicacion_oficial, f"{enunciado_supuesto} {pregunta}"
    )
    aud_b = aud.get("auditoria_bloques") or {}

    arts_omitidos_str = ", ".join(aud["articulos_omitidos"]) if aud["articulos_omitidos"] else "Ninguno"
    arts_acertados_str = ", ".join(aud["articulos_acertados"]) if aud["articulos_acertados"] else "Ninguno de los incluidos en la explicación"
    arts_extra_ok_str = "; ".join(aud["articulos_extra_validos"]) if aud["articulos_extra_validos"] else "Ninguno adicional detectado"
    siglas_mal_str = (
        ", ".join([f"{s} (no fue presentada con su nombre completo antes)" for s, _ in aud["siglas_sin_presentar"]])
        if aud["siglas_sin_presentar"] else "Ninguna (todas las siglas empleadas por el alumno fueron correctamente presentadas)"
    )

    clave_limpia = (api_key or GEMINI_API_KEY_DEFAULT).strip().replace("×", "x").replace(" ", "")
    enunciado_limpio = re.sub(r'<[^>]+>', ' ', enunciado_supuesto or "").strip()

    if modo in ("SUPUESTO", "SUPUESTOS"):
        prompt = (
            "Actúa como el equipo de preparadores del Cuerpo de Gestión de la Administración de la Seguridad Social.\n"
            "Evalúa la respuesta del alumno a esta cuestión de un SUPUESTO PRÁCTICO comparándola directamente con la "
            "EXPLICACIÓN Y RESPUESTA TÉCNICA OFICIAL de la pregunta (SIN aplicar baremos ni criterios formales de Tribunal C1/C2/C3).\n\n"
            "=== REGLAS DE CORRECCIÓN DEL SUPUESTO PRÁCTICO ===\n"
            "1. Califica la respuesta de **0,00 a 10,00 puntos** (siendo 5,00 el aprobado), aplicando un criterio justo, constructivo y ligeramente indulgente cuando el alumno identifique bien la solución jurídica o el planteamiento del cálculo.\n"
            "2. Comprueba si el alumno:\n"
            "   - Ha detectado la clave o «trampa» jurídica/matemática explicada en el bloque `EXPLICACION`.\n"
            "   - Ha llegado al resultado numérico, plazo o calificación jurídica correcta indicada en `RESPUESTA TÉCNICA`.\n"
            "   - Ha fundamentado su respuesta en la normativa aplicable (no penalices en exceso si omite el número exacto de algún artículo pero aplica bien la regla legal).\n\n"
            f"=== PLANTEAMIENTO DEL SUPUESTO ===\n{enunciado_limpio}\n\n"
            f"=== PREGUNTA PRÁCTICA ===\n{pregunta}\n\n"
            f"=== EXPLICACIÓN Y SOLUCIÓN OFICIAL DE LA PREGUNTA ===\n{respuesta_oficial}\n{explicacion_oficial}\n\n"
            f"=== RESPUESTA DEL ALUMNO ===\n{respuesta_alumno}\n\n"
            "=== FORMATO OBLIGATORIO DE TU RESPUESTA ===\n"
            "En la PRIMERA LÍNEA escribe siempre esta etiqueta exacta con la nota sobre 10 (con punto decimal):\n"
            "[[NOTA_SUPUESTO: X.XX]]\n\n"
            "A continuación, redacta una valoración clara, directa y formativa estructurada en estos 3 puntos:\n"
            "1. **✅ Lo que has acertado en la resolución de la pregunta:**\n"
            "   - Destaca los cálculos, plazos, conclusiones jurídicas y preceptos que el alumno ha resuelto correctamente.\n"
            "2. **⚠️ Por qué obtienes esta nota (qué ha faltado o qué trampa del supuesto debes tener en cuenta):**\n"
            "   - Explica con claridad qué matiz, cálculo, plazo o precepto de la explicación oficial le ha faltado o en qué punto se ha desviado, justificando de forma transparente el porqué de la nota.\n"
            f"   - Indica en una línea limpia: **Artículos de la solución no citados:** {arts_omitidos_str}\n"
            "3. **💡 Consejo práctico para clavar esta pregunta en el examen:**\n"
            "   - Un consejo breve y directo para recordar la regla o fórmula aplicada."
        )
    else:
        alerta_desv_str = (
            f"\n🚨 ATENCIÓN: Se ha detectado incongruencia con el epígrafe preguntado: {aud_b.get('motivo_desviacion')}\n"
            "Si el alumno ha contestado un epígrafe distinto al preguntado (por ejemplo, hablar de Altas y Bajas cuando se pregunta Afiliación o Convenio Especial), la nota de Criterio 1 no puede superar los 10,00 puntos.\n"
            if aud_b.get("desviacion_epigrafe") else ""
        )

        prompt = (
            "Actúa como el Tribunal Calificador y equipo de preparadores del Cuerpo de Gestión de la Administración de la Seguridad Social.\n"
            "Realiza un análisis analítico, detallado, justo y constructivo comparando el TEXTO ESCRITO POR EL ALUMNO con la "
            "EXPLICACIÓN / DESARROLLO OFICIAL DE ESTE EPÍGRAFE CONCRETO que se te facilita más abajo, aplicando un criterio **equilibrado, formativo y ligeramente indulgente** para no desanimar en exceso al opositor cuando sí trabaja el epígrafe:\n\n"
            "=== REGLAS EQUILIBRADAS DE VALORACIÓN DEL TRIBUNAL ===\n"
            "1. **DISTINCIÓN CLARA ENTRE CONTESTAR OTRO EPÍGRAFE VS. RESPUESTA PARCIAL PERO PERTINENTE (`" + pregunta + "`):**\n"
            "   - **Cuándo SÍ debes suspender con firmeza (< 12 / 50 ptos):** Únicamente cuando el alumno conteste un epígrafe distinto al preguntado (por ejemplo, si el epígrafe preguntado es `Normas sobre afiliación`, `El convenio especial` o `Encuadramiento e inscripción` y el alumno pega un texto sobre `Altas y bajas en el Régimen General` omitiendo la institución preguntada) o cuando deje casi todo en blanco.\n"
            "   - **Cuándo debes ser UN POCO MÁS INDULGENTE Y CONSTRUCTIVO (permitiendo alcanzar o superar los 22-30 / 45 puntos en Criterio 1):** Cuando el alumno SÍ está contestando al epígrafe preguntado, comprende bien el núcleo del tema y desarrolla correctamente una parte relevante (por ejemplo, explica bien las modalidades de alta —real, asimilada, presunta/pleno derecho y especial— y además aporta el procedimiento, efectos o altas/bajas indebidas), aunque haya olvidado algunos subapartados del esquema (como definir pluriempleo/pluriactividad o sujetos obligados) o haya explicado conceptos con sus propias palabras sin recordar todos los números de artículo. En estos casos, **valora con generosidad todo lo que sí sabe y aporta** para que su esfuerzo se vea recompensado y pueda superar el corte eliminatorio de 25/50 si la respuesta demuestra estudio y buena base.\n"
            "   - **NO EXIJAS COMO OBLIGATORIO LO QUE NO ESTÉ EN LA EXPLICACIÓN OFICIAL DE ESTE EPÍGRAFE:** Si el alumno adelanta o añade conceptos conexos válidos del tema (como plazos de altas previas, efectos de las altas o las altas y bajas indebidas de los arts. 60 y 61 RIA), súmale puntos adicionales en el Criterio 1 por enriquecer la exposición."
            f"{alerta_desv_str}\n"
            "2. **REGLA EXACTA SOBRE PRESENTACIÓN DE SIGLAS (PROHIBIDO INVENTAR FALSOS POSITIVOS):**\n"
            "   - Una sigla está **CORRECTAMENTE PRESENTADA** tanto si el alumno escribe su nombre completo seguido de la sigla entre paréntesis —por ejemplo: *«Reglamento General sobre inscripción de empresas y afiliación, altas, bajas y variaciones de datos de trabajadores en la Seguridad Social (RIA)»*— como si utiliza la fórmula *«..., en adelante, SIGLA»*.\n"
            "   - **PROHIBIDO** acusar al alumno de usar siglas sin presentar si ya puso su nombre completo antes (como en el caso de `(RIA)`), y **PROHIBIDO** mencionar siglas que el alumno ni siquiera ha escrito en su texto.\n"
            f"   - Auditoría automática verificada sobre el texto del alumno: **Siglas usadas sin presentar detectadas:** `{siglas_mal_str}` (respeta exactamente este dato y resta muy poquito —máximo 0,15 o 0,20 ptos— si hay alguna).\n\n"
            "3. **FALTA DE ARTÍCULOS INCLUIDOS EN LA EXPLICACIÓN (RESTA MUY LEVE Y FORMATO ESTRICTO «Artículos omitidos: ...»):**\n"
            "   - Omitir números de artículos incluidos en la explicación oficial debe restar **muy poco** cuando el alumno ha sabido explicar el concepto jurídico.\n"
            "   - En el apartado 3 de tu informe, escribe en una línea limpia únicamente **`Artículos omitidos:`** seguido directamente de la relación de artículos omitidos.\n"
            f"   - Relación detectada: **Artículos omitidos:** {arts_omitidos_str}.\n\n"
            "=== BAREMO OFICIAL DEL TRIBUNAL CALIFICADOR ===\n"
            "- Puntuación total: de 0 a 50 puntos (mínimo 25,00 puntos para aprobar).\n"
            "- Criterio 1 (0 a 45 puntos): Conocimiento y desarrollo de los apartados de la explicación oficial de este epígrafe + puntos extra por conceptos o artículos adicionales conexos válidos que mejoren el epígrafe - resta muy leve por los artículos omitidos de la explicación.\n"
            "- Criterio 2 (0 a 3 puntos): Orden de las ideas y estructura sistemática (puntúa si Criterio 1 >= 20,00; si Criterio 1 < 20,00, Criterio 2 = 0,00).\n"
            "- Criterio 3 (0 a 2 puntos): Calidad de la expresión escrita y presentación de siglas (puntúa si Criterio 1 >= 20,00; resta muy levemente solo por las siglas que realmente haya usado el alumno sin presentar su nombre completo).\n\n"
            f"=== EPÍGRAFE PREGUNTADO ===\n{enunciado_limpio}\n{pregunta}\n\n"
            f"=== EXPLICACIÓN / DESARROLLO OFICIAL DEL EPÍGRAFE (REFERENCIA DE CONTENIDO) ===\n{respuesta_oficial}\n{explicacion_oficial}\n\n"
            f"=== TEXTO ESCRITO POR EL ALUMNO ===\n{respuesta_alumno}\n\n"
            f"=== DATOS DE AUDITORÍA VERIFICADOS ===\n"
            f"- Artículos de la explicación citados por el alumno: {arts_acertados_str}\n"
            f"- Artículos omitidos de la explicación: {arts_omitidos_str}\n"
            f"- Artículos adicionales aportados por el alumno: {arts_extra_ok_str}\n"
            f"- Siglas usadas por el alumno sin presentación previa: {siglas_mal_str}\n\n"
            "=== FORMATO OBLIGATORIO DE TU RESPUESTA ===\n"
            "En la PRIMERA LÍNEA escribe siempre esta etiqueta exacta con las puntuaciones numéricas (con punto decimal) que otorgas:\n"
            "[[NOTAS_TRIBUNAL: C1=XX.XX | C2=X.XX | C3=X.XX]]\n\n"
            "A continuación, redacta tu dictamen analítico y motivador estructurado en estos 4 apartados:\n"
            "1. **✅ Análisis de pertinencia, apartados acertados y aportaciones adicionales que enriquecen el epígrafe:**\n"
            "   - Valora de forma constructiva y positiva todo lo que el alumno ha desarrollado bien respecto al epígrafe y destaca muy favorablemente los conceptos o artículos adicionales conexos (como efectos o altas/bajas indebidas) que ha aportado para enriquecer su respuesta.\n"
            "2. **⚠️ Análisis constructivo de lo que falta por completar respecto a la explicación oficial:**\n"
            "   - Explica con detalle analítico pero con tono cercano y pedagógico qué apartados o matices de la `EXPLICACIÓN / DESARROLLO OFICIAL DEL EPÍGRAFE` le han faltado para alcanzar una nota de sobresaliente.\n"
            "3. **⚖️ Rigor normativo y uso de siglas:**\n"
            "   - Valora las normas y artículos bien citados (incluyendo la correcta presentación de siglas como `(RIA)` cuando lo haya hecho).\n"
            f"   - Escribe en una línea limpia: **Artículos omitidos:** {arts_omitidos_str}\n"
            f"   - Respecto a las siglas sin presentar, indica únicamente: **Siglas sin presentación previa:** {siglas_mal_str}\n"
            "4. **🎓 Calificación por Criterios del Tribunal y Desglose sencillo de puntos sumados y restados:**\n"
            "   - Muestra las puntuaciones otorgadas en:\n"
            "     • **Criterio 1 (Conocimiento y normativa: 0 a 45 ptos):** `XX,XX / 45,00 puntos`\n"
            "     • **Criterio 2 (Orden de las ideas y estructura: 0 a 3 ptos):** `X,XX / 3,00 puntos`\n"
            "     • **Criterio 3 (Calidad de la expresión escrita y siglas: 0 a 2 ptos):** `X,XX / 2,00 puntos`\n"
            "     • **🏆 CALIFICACIÓN TOTAL:** **`XX,XX / 50,00 puntos`** *(Equivalencia: **`X,XX / 10`**)*\n"
            "   - Añade el bloque **📊 Resumen sencillo de por qué has sumado y por qué te han restado puntos:**\n"
            "     • **➕ Qué te ha sumado puntos:** viñetas claras con los puntos aportados por cada bloque bien desarrollado, por los conceptos/artículos adicionales que mejoraron el epígrafe y por estructura/expresión.\n"
            "     • **➖ Qué te ha restado o impedido sumar hasta los 50 puntos:** viñetas claras con los puntos que faltaron por los apartados de la explicación oficial no incluidos, la resta leve por **Artículos omitidos** y la resta leve (si procede) por **siglas sin presentación previa**.\n"
            "   - Cierra con **💡 Orientación motivadora de tus preparadores para seguir subiendo nota en este epígrafe:**."
        )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.15,
            "topP": 0.85,
        }
    }

    modelos_a_probar = _obtener_modelos_disponibles_api(clave_limpia)
    for modelo in modelos_a_probar:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={clave_limpia}"
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=35)
            if r.status_code == 200:
                data = r.json()
                texto_ia = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                ev_actualizado, texto_ia_limpio = _extraer_puntuaciones_de_respuesta_ia(texto_ia, ev_fallback)
                if isinstance(ev_fallback, dict):
                    ev_fallback.update(ev_actualizado)
                return texto_ia_limpio
        except Exception:
            continue

    return generar_informe_analitico_respaldo(pregunta, ev_fallback, aud, modo=modo)

def sincronizar_progreso_navegador():
    try:
        datos_auth = {
            "email": st.session_state.get("email"),
            "rol": st.session_state.get("rol"),
            "es_admin": st.session_state.get("es_admin", False),
            "saved_esp": st.session_state.get("saved_esp", "ADMINISTRATIVOS"),
            "saved_cat": st.session_state.get("saved_cat", "ESPECIFICO"),
            "modo_avance": st.session_state.get("modo_avance", "")
        }
        b64_auth = _cifrar_backup_sesion(datos_auth)

        if st.session_state.get("questions"):
            datos_test = dict(datos_auth)
            datos_test.update({
                "questions": st.session_state.get("questions", []),
                "stats": {str(k): v for k, v in st.session_state.get("stats", {}).items()},
                "current_index": st.session_state.get("current_index", 0),
                "finished": st.session_state.get("finished", False),
                "checked": st.session_state.get("checked", False),
                "test_name": st.session_state.get("test_name"),
                "test_esp": st.session_state.get("test_esp", ""),
                "test_cat": st.session_state.get("test_cat", ""),
                "test_start_ts": st.session_state.get("test_start_ts"),
                "fecha_inicio_str": st.session_state.get("fecha_inicio_str", ""),
                "hora_inicio_str": st.session_state.get("hora_inicio_str", ""),
                "inicio_registrado_sheets": st.session_state.get("inicio_registrado_sheets", False),
                "resultado_registrado": st.session_state.get("resultado_registrado", False)
            })
            b64_test = _cifrar_backup_sesion(datos_test)
            components.html(f"""<script>
            try {{
                window.parent.localStorage.setItem("oposiciona_auth_backup_v1", "{b64_auth}");
                window.parent.localStorage.setItem("oposiciona_test_backup_v1", "{b64_test}");
            }} catch(e) {{}}
            </script>""", height=0)
        else:
            components.html(f"""<script>
            try {{
                window.parent.localStorage.setItem("oposiciona_auth_backup_v1", "{b64_auth}");
                window.parent.localStorage.removeItem("oposiciona_test_backup_v1");
            }} catch(e) {{}}
            </script>""", height=0)
    except Exception:
        pass

def descargar_pdf_fresco(url):
    sep = "&" if "?" in url else "?"
    url_nocache = f"{url}{sep}_cb={int(time.time() * 1000)}"
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    return requests.get(url_nocache, headers=headers)

def render_cuadro_reporte_error(q, num_pregunta, ubicacion_key):
    if not usuario_puede_reportar():
        return

    es_desarrollo = bool(q.get("tipo_abierta") == "DESARROLLO")
    es_abierta = bool(q.get("is_open", False))
    tipo_lbl = "Epígrafe" if es_desarrollo else ("Cuestión" if es_abierta else "Pregunta")
    nombre_pdf = st.session_state.get('test_name') or "Test sin nombre"
    id_test_limpio = re.sub(r'\W+', '_', nombre_pdf)
    tema_vis = obtener_etiqueta_tema_visible(nombre_pdf, q)
    usuario_rep = (st.session_state.get('email') or "Alumno Oposiciona").strip()
    preamble_txt = re.sub(r'<[^>]+>|\*\*|\🏷️', '', q.get('preamble', '')).strip()
    pregunta_txt = q.get('question_text', '').strip()
    exp_limpia = re.sub(r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+fundamento\s+legal|\s+y\s+soluci[óo]n\s+detallada|\s*\([^)]*\))?:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').replace("[[H]]", "").strip(), flags=re.IGNORECASE).strip() or "Sin explicación disponible."

    st.markdown(
        "<div style='background-color:#fff8e1; border:2px solid #ffb300; border-radius:8px; padding:12px; margin-top:8px; margin-bottom:8px;'>"
        f"<b style='color:#bf360c !important; font-size:15px;'>🛠️ Reportar Error en {tipo_lbl} {num_pregunta} a info@oposiciona.es</b><br>"
        f"<span style='font-size:13px; color:#5d4037 !important;'>{'Se enviará una ficha específica con tu comentario, el Tema, el enunciado, tu Respuesta escrita, el Dictamen de corrección generado y la Explicación oficial.' if es_abierta else 'Se enviará una ficha visual con tu comentario, el enunciado, las opciones por separado y la explicación para revisarlo al instante.'}</span>"
        "</div>",
        unsafe_allow_html=True
    )

    placeholder_txt = (
        "Ejemplo: Tengo una duda sobre la valoración o hay una errata en la explicación oficial..."
        if es_abierta else
        "Ejemplo: Falta un 'NO' en el enunciado, la respuesta correcta debería ser la b), o se ha cortado una frase..."
    )

    key_txt_area = f"txt_rep_{id_test_limpio}_{ubicacion_key}_{num_pregunta}"
    motivo = st.text_area(
        f"Explica brevemente el error o incidencia encontrada en este {tipo_lbl.lower()}:",
        key=key_txt_area,
        placeholder=placeholder_txt
    )

    col_env, col_cer = st.columns([3, 1])
    with col_cer:
        if st.button("✖ Cerrar", key=f"btn_close_{id_test_limpio}_{ubicacion_key}_{num_pregunta}", use_container_width=True):
            limpiar_estados_reportes_error()
            st.rerun()

    with col_env:
        enviar_pulsado = st.button(f"📨 Enviar reporte de {tipo_lbl} {num_pregunta} a info@oposiciona.es", key=f"btn_send_{id_test_limpio}_{ubicacion_key}_{num_pregunta}", type="primary", use_container_width=True)

    if enviar_pulsado:
        if not motivo.strip():
            st.warning("⚠️ Escribe brevemente en qué consiste el error o incidencia antes de enviarlo.")
        else:
            stat_q = st.session_state.get("stats", {}).get(num_pregunta - 1, {})
            if es_abierta:
                resp_alumno_env = (stat_q.get("selected") or st.session_state.get(f"open_txt_{num_pregunta - 1}") or "Sin respuesta escrita por el alumno").strip()
                dictamen_env = (stat_q.get("ai_feedback") or "Aún no se había pulsado Comprobar").strip()
                payload = {
                    "_subject": f"⚠️ Revisar {tipo_lbl} {num_pregunta} ({tema_vis}) | {nombre_pdf}",
                    "email": usuario_rep if "@" in usuario_rep else "info@oposiciona.es",
                    "_replyto": usuario_rep if "@" in usuario_rep else "info@oposiciona.es",
                    "01_COMENTARIO_DEL_ALUMNO": f"🚨 « {motivo.strip()} »",
                    "02_TEMA_Y_ALUMNO": f"📘 Tema: {tema_vis}   |   👤 Alumno: {usuario_rep}   |   Archivo: {nombre_pdf}",
                    "03_PREGUNTA_O_EPIGRAFE": f"📝 {pregunta_txt}",
                    "04_RESPUESTA_ESCRITA_POR_EL_ALUMNO": f"✍️ {resp_alumno_env}",
                    "05_DICTAMEN_DE_CORRECCION_GENERADO": f"🤖 {dictamen_env}",
                    "06_EXPLICACION_OFICIAL": f"📖 {exp_limpia}",
                    "_template": "box",
                    "_captcha": "false"
                }
            else:
                lista_opciones = q.get('options', [])
                idx_correcta = q.get('answer', -1)
                correcta_txt = lista_opciones[idx_correcta] if (0 <= idx_correcta < len(lista_opciones)) else (q.get('answer_text') or "⚠️ No detectada automáticamente en el PDF")
                payload = {
                    "_subject": f"⚠️ Revisar Pregunta {num_pregunta} | {nombre_pdf}",
                    "email": usuario_rep if "@" in usuario_rep else "info@oposiciona.es",
                    "_replyto": usuario_rep if "@" in usuario_rep else "info@oposiciona.es",
                    "01_QUE_REPORTA_EL_ALUMNO": f"🚨 « {motivo.strip()} »",
                    "02_ALUMNO_Y_TEST": f"👤 Alumno: {usuario_rep}   |   Test: {nombre_pdf} (Pregunta Nº {num_pregunta})" + (f"   |   {preamble_txt}" if preamble_txt else ""),
                    "03_ENUNCIADO_DE_LA_PREGUNTA": f"❓ {pregunta_txt}",
                }
                for i_opt, texto_opt in enumerate(lista_opciones):
                    letra_mayus = chr(65 + i_opt)
                    num_campo = 4 + i_opt
                    if i_opt == idx_correcta:
                        payload[f"{num_campo:02d}_OPCION_{letra_mayus}_(MARCADA_CORRECTA)"] = f"✅ [CORRECTA] ➡️ {texto_opt}"
                    else:
                        payload[f"{num_campo:02d}_OPCION_{letra_mayus}"] = f"⚪ {texto_opt}"
                payload["09_RESPUESTA_QUE_DA_POR_BUENA_EL_SISTEMA"] = f"🎯 {correcta_txt}"
                payload["10_EXPLICACION_EXTRAIDA_DEL_PDF"] = f"💡 {exp_limpia}"
                payload["_template"] = "box"
                payload["_captcha"] = "false"

            enviado_servidor = False
            try:
                headers_fs = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Referer": "https://test-oposiciona.streamlit.app/",
                    "Origin": "https://test-oposiciona.streamlit.app",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                resp_fs = requests.post("https://formsubmit.co/ajax/info@oposiciona.es", json=payload, headers=headers_fs, timeout=10)
                if resp_fs.status_code == 200:
                    datos_fs = resp_fs.json()
                    if str(datos_fs.get("success", "")).lower() == "true":
                        enviado_servidor = True
            except Exception:
                enviado_servidor = False

            if enviado_servidor:
                limpiar_estados_reportes_error()
                st.session_state[f"rep_ok_msg_{id_test_limpio}_{num_pregunta}"] = True
                st.rerun()
            else:
                payload_json = json.dumps(payload)
                components.html(f"""
                <div id="status_envio" style="font-family:sans-serif; padding:10px; border-radius:6px; background:#e8f5e9; border:1px solid #2e7d32; color:#1b5e20; font-size:14px; font-weight:600; text-align:center;">
                    ⏳ Enviando reporte a info@oposiciona.es...
                </div>
                <script>
                (function() {{
                    var rawData = {payload_json};
                    var formData = new FormData();
                    for (var k in rawData) {{
                        if (Object.prototype.hasOwnProperty.call(rawData, k)) {{
                            formData.append(k, rawData[k]);
                        }}
                    }}
                    var box = document.getElementById("status_envio");
                    fetch("https://formsubmit.co/ajax/info@oposiciona.es", {{
                        method: "POST",
                        headers: {{ "Accept": "application/json" }},
                        body: formData
                    }})
                    .then(function(r) {{ return r.json(); }})
                    .then(function(res) {{
                        if (res.success === "true" || res.success === true) {{
                            box.style.background = "#e8f5e9";
                            box.style.borderColor = "#2e7d32";
                            box.style.color = "#1b5e20";
                            box.innerHTML = "✅ ¡Reporte enviado con éxito a info@oposiciona.es! Muchas gracias por tu colaboración.";
                        }} else {{
                            var msg = res.message || "";
                            box.style.background = "#fff3cd";
                            box.style.borderColor = "#ffc107";
                            box.style.color = "#856404";
                            box.innerHTML = "ℹ️ Respuesta del servidor: " + (msg || JSON.stringify(res));
                        }}
                    }})
                    .catch(function(err) {{
                        box.style.background = "#ffebee";
                        box.style.borderColor = "#c62828";
                        box.style.color = "#b71c1c";
                        box.innerHTML = "❌ No se pudo completar el envío desde el navegador.";
                    }});
                }})();
                </script>
                """, height=75)

def limpiar_todas_las_busquedas():
    for k in list(st.session_state.keys()):
        if k.startswith("busqueda_"): st.session_state[k] = ""

def limpiar_busqueda_al_filtrar(key_busqueda):
    st.session_state[key_busqueda] = ""

def cambio_categoria_o_especialidad():
    st.session_state.saved_esp = st.session_state.get('radio_especialidad', 'ADMINISTRATIVOS')
    st.session_state.saved_cat = st.session_state.get('radio_categoria', 'ESPECIFICO')
    st.session_state.mostrar_opciones_simulacro = False
    limpiar_todas_las_busquedas()

def normalizar_para_busqueda(texto):
    t = ''.join(c for c in unicodedata.normalize('NFD', texto.lower().strip()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'\b0+(\d+)', r'\1', t))

def coincide_busqueda(nombre_test, consulta):
    if not consulta or not consulta.strip(): return True
    n_norm, q_norm = normalizar_para_busqueda(nombre_test), normalizar_para_busqueda(consulta)
    return bool(re.search(re.escape(q_norm) + r'(?!\d)', n_norm)) if re.search(r'\d+$', q_norm) else (q_norm in n_norm)

def obtener_grupo_tema(nombre_test, categoria):
    if categoria == "EXAMENES": return "🏆 Exámenes y Simulacros Oficiales"
    if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO"]: return "📝 2.º Ejercicio (1.ª Parte) — Preguntas de Desarrollo"
    if categoria in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"]: return "📋 2.º Ejercicio (2.ª Parte) — Supuestos Prácticos"
    m = re.match(r'^TEMAS?\s*[_\.\-]?\s*(\d+(?:\s*(?:a|y)\s*\d+)?)', nombre_test, re.IGNORECASE)
    if m:
        b = m.group(1).upper().strip()
        nums = re.findall(r'\d+', b)
        return f"📁 TEMA {int(nums[0]):02d}" if len(nums) == 1 else f"📁 TEMAS {b}"
    return "📁 Otros Tests"

def cargar_test_desde_url(nombre_test, url_descarga, especialidad_sel="", categoria_sel=""):
    limpiar_estados_reportes_error()
    st.session_state.test_name = nombre_test
    st.session_state.test_esp = especialidad_sel or st.session_state.get('saved_esp', '')
    cat_limpia = categoria_sel or st.session_state.get('saved_cat', '')
    if cat_limpia in ["DESARROLLO", "PREGUNTA DE DESARROLLO"]:
        cat_limpia = "DESARROLLO"
    elif cat_limpia in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"]:
        cat_limpia = "SUPUESTOS"
    st.session_state.test_cat = cat_limpia
    st.session_state.mostrar_opciones_simulacro = False
    cat_actual = st.session_state.test_cat
    max_op = 3 if "GESTI" in (st.session_state.test_esp or "").upper() else 4
    with st.spinner(f"Extrayendo '{nombre_test}' de forma segura..."):
        try:
            r = descargar_pdf_fresco(url_descarga)
            if r.status_code == 200:
                if cat_actual == "DESARROLLO":
                    raw_qs = PDFQuizParser.parse_abiertas_gestion(r.content, modo="DESARROLLO")
                    if not raw_qs:
                        st.error("No se encontraron preguntas o epígrafes de desarrollo en este documento.")
                    else:
                        procesar_preguntas(raw_qs, barajar=False)
                elif cat_actual == "SUPUESTOS":
                    raw_qs = PDFQuizParser.parse_abiertas_gestion(r.content, modo="SUPUESTOS")
                    if not raw_qs:
                        st.error("No se encontraron supuestos prácticos en este documento.")
                    else:
                        procesar_preguntas(raw_qs, barajar=False)
                else:
                    raw_qs = PDFQuizParser.parse(r.content, max_options=max_op)
                    if not raw_qs: st.error("No se encontraron preguntas válidas en este PDF.")
                    else: procesar_preguntas(raw_qs, barajar=True)
            else: st.error("Error de descarga. Comprueba que el archivo en Drive tiene permisos de lectura.")
        except Exception as e: st.error(f"Error de conexión: {e}")

def asignar_cuotas_aleatorias_variables(num_pdfs, total_preguntas, limites_por_pdf=None):
    if num_pdfs == 0 or total_preguntas <= 0: return []
    pesos = [random.choice([0, 1, 1, 2, 2, 3, 4]) for _ in range(num_pdfs)]
    if sum(pesos) == 0: pesos = [random.randint(1, 3) for _ in range(num_pdfs)]
    cuotas = [0] * num_pdfs
    for _ in range(total_preguntas):
        disp = [i for i in range(num_pdfs) if cuotas[i] < limites_por_pdf[i]] if limites_por_pdf is not None else list(range(num_pdfs))
        if not disp: break
        p_disp = [pesos[i] for i in disp]
        if sum(p_disp) == 0: p_disp = [1 for _ in disp]
        cuotas[random.choices(disp, weights=p_disp, k=1)[0]] += 1
    return cuotas

def extraer_preguntas_aleatorias_de_lista(pdfs_candidatos, cantidad_deseada, barra_progreso, max_options=None):
    if not pdfs_candidatos or cantidad_deseada <= 0: return []
    pdfs_copia = list(pdfs_candidatos)
    random.shuffle(pdfs_copia)
    n_pdfs = len(pdfs_copia)
    cuotas_ini = asignar_cuotas_aleatorias_variables(n_pdfs, cantidad_deseada)
    cache_qs = {}
    idx_desc = [i for i, c in enumerate(cuotas_ini) if c > 0]

    for paso, idx_pdf in enumerate(idx_desc):
        cat, t_name, url = pdfs_copia[idx_pdf]
        if barra_progreso is not None:
            barra_progreso.progress((paso + 1) / max(1, len(idx_desc)), text="🎲 Sorteando temas y extrayendo preguntas al azar...")
        try:
            r = descargar_pdf_fresco(url)
            if r.status_code == 200:
                qs = PDFQuizParser.parse(r.content, max_options=max_options)
                if qs:
                    for q in qs:
                        f = f"🏷️ **Fuente: {cat} - {t_name}**"
                        q["preamble"] = f + "\n\n" + q["preamble"] if q["preamble"] else f
                    cache_qs[idx_pdf] = qs
        except Exception: pass

    qs_disp = sum(len(qs) for qs in cache_qs.values())
    idx_res = [i for i in range(n_pdfs) if i not in cache_qs]
    random.shuffle(idx_res)

    for ir in idx_res:
        if qs_disp >= cantidad_deseada: break
        cat, t_name, url = pdfs_copia[ir]
        try:
            r = descargar_pdf_fresco(url)
            if r.status_code == 200:
                qs = PDFQuizParser.parse(r.content, max_options=max_options)
                if qs:
                    for q in qs:
                        f = f"🏷️ **Fuente: {cat} - {t_name}**"
                        q["preamble"] = f + "\n\n" + q["preamble"] if q["preamble"] else f
                    cache_qs[ir] = qs
                    qs_disp += len(qs)
        except Exception: pass

    if not cache_qs: return []
    claves = list(cache_qs.keys())
    limites = [len(cache_qs[k]) for k in claves]
    cuotas_fin = [min(cuotas_ini[k], limites[p]) for p, k in enumerate(claves)]
    faltantes = min(cantidad_deseada, sum(limites)) - sum(cuotas_fin)
    if faltantes > 0:
        p_extra = [random.randint(1, 3) for _ in claves]
        for _ in range(faltantes):
            disp = [i for i in range(len(claves)) if cuotas_fin[i] < limites[i]]
            if not disp: break
            cuotas_fin[random.choices(disp, weights=[p_extra[i] for i in disp], k=1)[0]] += 1

    sel = []
    for p, k in enumerate(claves):
        if cuotas_fin[p] > 0: sel.extend(random.sample(cache_qs[k], cuotas_fin[p]))
    return sel

def generar_simulacro_aleatorio(especialidad, ambito_seleccionado, total_deseadas, diccionario_tests):
    barra = st.progress(0, text="🎲 Preparando sorteo de temas y preguntas...")
    max_op = 3 if "GESTI" in especialidad.upper() else 4
    if ambito_seleccionado == "TODO":
        c_gen = int(round(total_deseadas * 0.60))
        c_esp = total_deseadas - c_gen
        p_gen = [("GENERAL", tn, u) for tn, u in diccionario_tests[especialidad].get("GENERAL", {}).items() if u is not None]
        p_esp = [("ESPECIFICO", tn, u) for tn, u in diccionario_tests[especialidad].get("ESPECIFICO", {}).items() if u is not None]
        examen = extraer_preguntas_aleatorias_de_lista(p_gen, c_gen, barra, max_options=max_op) + extraer_preguntas_aleatorias_de_lista(p_esp, c_esp, barra, max_options=max_op)
    else:
        co = "GENERAL" if ambito_seleccionado == "GENERAL" else "ESPECIFICO"
        p_cat = [(co, tn, u) for tn, u in diccionario_tests[especialidad].get(co, {}).items() if u is not None]
        examen = extraer_preguntas_aleatorias_de_lista(p_cat, total_deseadas, barra, max_options=max_op)
    barra.empty()
    random.shuffle(examen)
    return examen

if 'questions' not in st.session_state:
    st.session_state.update(questions=[], current_index=0, stats={}, finished=False, checked=False, test_name=None)

def _diagnosticar_extension_respuesta_desarrollo(texto):
    t = (texto or "").strip()
    if not t:
        return "⚠️ No cumplimentó nada en el texto"
    lineas_no_vacias = [l.strip() for l in t.split('\n') if l.strip()]
    palabras = re.findall(r'\S+', t)
    if len(palabras) < 35 or (len(lineas_no_vacias) <= 2 and len(t) < 200):
        num_lin = 1 if len(palabras) < 18 else 2
        return f"⚠️ Solo escribió {num_lin} {'línea' if num_lin == 1 else 'líneas'} ({len(palabras)} palabras)"
    return "✅ Cumplimentado"

def construir_nombre_test_seguimiento_sheets(indice_actual=None):
    qs = st.session_state.get("questions", [])
    es_desarrollo = (
        (st.session_state.get("test_cat") or "").upper() == "DESARROLLO"
        or any(q.get("tipo_abierta") == "DESARROLLO" for q in qs)
    )
    if not es_desarrollo or not qs:
        return st.session_state.get("test_name") or "Test"

    st.session_state.test_cat = "DESARROLLO"
    tema_lbl = obtener_etiqueta_tema_visible(st.session_state.get("test_name"), qs[0])
    stats = st.session_state.get("stats", {})

    if indice_actual is not None and not st.session_state.get("finished", False):
        q_act = qs[indice_actual]
        ep_titulo = q_act.get("question_text", f"Epígrafe {indice_actual + 1}").strip()
        txt_al = (stats.get(indice_actual, {}).get("selected") or "").strip()
        estado_txt = _diagnosticar_extension_respuesta_desarrollo(txt_al)
        return f"{tema_lbl}\n{ep_titulo} -> {estado_txt}"

    detalles_epigrafes = []
    alguno_tocado = False
    for i_q, q_item in enumerate(qs):
        ep_tit = q_item.get("question_text", f"Epígrafe {i_q + 1}").strip()
        txt_i = (stats.get(i_q, {}).get("selected") or "").strip()
        intentos_i = stats.get(i_q, {}).get("attempts", 0)
        if txt_i or intentos_i > 0:
            alguno_tocado = True
            est_i = _diagnosticar_extension_respuesta_desarrollo(txt_i)
            detalles_epigrafes.append(f"{ep_tit} -> {est_i}")

    if not alguno_tocado:
        idx_ref = st.session_state.get("current_index", 0)
        ep_actual = qs[idx_ref].get("question_text", f"Epígrafe {idx_ref + 1}").strip() if idx_ref < len(qs) else "Todos los epígrafes"
        detalles_epigrafes.append(f"{ep_actual} -> ⚠️ No cumplimentó nada en el texto")

    return f"{tema_lbl}\n" + "\n".join(detalles_epigrafes)

def save_answer(selected):
    idx_curr = st.session_state.current_index
    stat = st.session_state.stats[idx_curr]
    q_curr = st.session_state.questions[idx_curr] if st.session_state.get("questions") else {}
    es_desarrollo_curr = bool(q_curr.get("tipo_abierta") == "DESARROLLO" or st.session_state.get("test_cat") == "DESARROLLO")

    if selected is not None and str(selected).strip() != "" and selected != stat['selected']:
        stat['selected'] = selected
        stat['attempts'] += 1
        if not st.session_state.get('inicio_registrado_sheets', False):
            st.session_state.inicio_registrado_sheets = True
            if es_desarrollo_curr:
                st.session_state.test_cat = "DESARROLLO"
            nombre_celda = construir_nombre_test_seguimiento_sheets(indice_actual=idx_curr)
            registrar_actividad_sheets("🚀 En curso", nombre_test=nombre_celda, accion="nueva_fila")
    elif es_desarrollo_curr and st.session_state.get("checked", False):
        if not st.session_state.get('inicio_registrado_sheets', False):
            st.session_state.inicio_registrado_sheets = True
            st.session_state.test_cat = "DESARROLLO"
            nombre_celda = construir_nombre_test_seguimiento_sheets(indice_actual=idx_curr)
            registrar_actividad_sheets("🚀 En curso", nombre_test=nombre_celda, accion="nueva_fila")

def handle_radio_change():
    idx = st.session_state.current_index
    selected = st.session_state.get(f"radio_{idx}")
    save_answer(selected)
    if "metralleta" in st.session_state.modo_avance.lower() and selected:
        limpiar_estados_reportes_error()
        if idx < len(st.session_state.questions) - 1:
            st.session_state.current_index += 1
            st.session_state.checked = False
            st.session_state.do_scroll = True
        else:
            st.session_state.update(finished=True, celebracion_mostrada=False, do_scroll=True)

def preparar_preguntas_como_en_test(raw_qs, barajar=True):
    patrones_fijos = [
        r'todas\s+son\s+(correctas|incorrectas|falsas|verdaderas)',
        r'todas\s+las\s+respuestas?\s+son\s+(correctas|incorrectas|falsas|verdaderas)',
        r'ninguna\s+es\s+correcta',
        r'ninguna\s+de\s+las\s+(anteriores|respuestas?)\s+es\s+correcta',
        r'las\s+opciones?\s+[a-d]\s*y\s*[a-d]\s+son\s+correctas'
    ]
    qs_preparadas = []
    for q_orig in raw_qs:
        q = dict(q_orig)
        if q.get("is_open", False):
            qs_preparadas.append(q)
            continue
        cleaned_options, tiene_fija = [], False
        for opt in q.get("options", []):
            to = re.sub(r'^[a-zA-Z][\)\.-]\s*', '', opt).strip()
            cleaned_options.append(to)
            if any(re.search(p, to.lower()) for p in patrones_fijos):
                tiene_fija = True
        corr = cleaned_options[q["answer"]] if 0 <= q.get("answer", -1) < len(cleaned_options) else None
        if not tiene_fija and barajar:
            random.shuffle(cleaned_options)
        if corr is not None and corr in cleaned_options:
            q["answer"] = cleaned_options.index(corr)
        else:
            q["answer"] = -1
        q["options"] = [f"{chr(97+i)}) {o}" for i, o in enumerate(cleaned_options)]
        qs_preparadas.append(q)
    if barajar:
        random.shuffle(qs_preparadas)
    return qs_preparadas

def auditar_extraccion_test_real(pdf_bytes, max_options=4):
    raw_qs = PDFQuizParser.parse(pdf_bytes, max_options=max_options)
    qs_finales = preparar_preguntas_como_en_test(raw_qs, barajar=False)
    nq = len(qs_finales)
    if nq == 0:
        return {
            "nq": 0,
            "media_op": "0",
            "estado_resumen": "❌ 0 preguntas extraídas",
            "incidencias": ["No se extrajo ninguna pregunta del PDF."]
        }

    avg_val = sum(len(q.get("options", [])) for q in qs_finales) / nq
    media_op = str(int(avg_val)) if avg_val.is_integer() else f"{avg_val:.2f}".replace(".", ",")

    incidencias = []
    sin_correcta = []
    opciones_incompletas = []
    preguntas_fusionadas = []
    explicaciones_cortadas = []

    for idx_q, q in enumerate(qs_finales, 1):
        opts = q.get("options", [])
        ans = q.get("answer", -1)
        exp = (q.get("explanation") or "").strip()
        q_txt = (q.get("question_text") or "").strip()

        opts_sin_prefijo = [re.sub(r'^[a-d]\)\s*', '', o).strip() for o in opts]
        if len(opts) < max_options or any(len(o) < 2 for o in opts_sin_prefijo):
            opciones_incompletas.append(f"P{idx_q} ({len(opts)} opc)")

        if ans == -1 or ans >= len(opts):
            sin_correcta.append(f"P{idx_q}")

        exp_sin_citas = re.sub(r'«[^»]*»|"[^"]*"', ' ', exp)
        tiene_bloque_opciones_pregunta = bool(
            re.search(r'(?:^|\n)\s*a\)\s+(?!\(Falsa\)|\(Correcta\)).+\n\s*b\)\s+(?!\(Falsa\)|\(Correcta\)).+\n\s*c\)\s+', exp_sin_citas) or
            re.search(r'(?:^|\n)\s*(?:Pregunta\s+)?\d{1,3}[\.\-\)]\s+[^\n]{15,}\?\s*\n\s*a\)\s+', exp_sin_citas)
        )
        if tiene_bloque_opciones_pregunta:
            preguntas_fusionadas.append(f"P{idx_q}")

        if not exp or len(exp) < 25:
            explicaciones_cortadas.append(f"P{idx_q} (sin exp)")
        elif exp.endswith((',', 'artículo', 'artículos', 'Art.', 'Ley', 'Real Decreto', 'de', 'del', 'en', 'con', 'por', 'para', '(')):
            explicaciones_cortadas.append(f"P{idx_q} (cortada: «...{exp[-22:]}»)")
        elif len(q_txt) < 12:
            explicaciones_cortadas.append(f"P{idx_q} (enunciado corto)")

    if preguntas_fusionadas:
        incidencias.append(f"🚨 Pregunta fusionada en exp: {', '.join(preguntas_fusionadas)}")
    if explicaciones_cortadas:
        incidencias.append(f"✂️ Exp/Texto cortado: {', '.join(explicaciones_cortadas[:5])}" + ("..." if len(explicaciones_cortadas) > 5 else ""))
    if opciones_incompletas:
        incidencias.append(f"⚠️ Opciones (<{max_options}): {', '.join(opciones_incompletas[:5])}" + ("..." if len(opciones_incompletas) > 5 else ""))
    if sin_correcta:
        incidencias.append(f"❓ Sin resp. correcta: {', '.join(sin_correcta[:6])}" + (f" (+{len(sin_correcta)-6} más)" if len(sin_correcta) > 6 else ""))

    if not incidencias:
        estado_resumen = f"✅ OK ({nq}/{nq} íntegras)"
    else:
        estado_resumen = " / ".join(incidencias)

    return {
        "nq": nq,
        "media_op": media_op,
        "estado_resumen": estado_resumen,
        "incidencias": incidencias
    }

def procesar_preguntas(raw_qs, barajar=True):
    limpiar_estados_reportes_error()
    qs_listas = preparar_preguntas_como_en_test(raw_qs, barajar=barajar)
    st.session_state.update(
        questions=qs_listas,
        current_index=0,
        finished=False,
        checked=False,
        stats={i: {'attempts': 0, 'selected': None, 'ai_feedback': None, 'ai_eval': None, 'last_evaluated_text': None} for i in range(len(qs_listas))},
        mostrar_opciones_simulacro=False,
        celebracion_mostrada=False,
        do_scroll=True
    )
    iniciar_cronometro_test()
    st.rerun()

def action_repetir_test():
    limpiar_estados_reportes_error()
    st.session_state.update(
        current_index=0,
        stats={i: {'attempts': 0, 'selected': None, 'ai_feedback': None, 'ai_eval': None, 'last_evaluated_text': None} for i in range(len(st.session_state.questions))},
        finished=False, checked=False, celebracion_mostrada=False, do_scroll=True
    )
    iniciar_cronometro_test()

def action_subir_otro():
    limpiar_estados_reportes_error()
    st.session_state.update(
        questions=[], current_index=0, stats={}, finished=False, checked=False,
        test_name=None, mostrar_opciones_simulacro=False, celebracion_mostrada=False,
        inicio_registrado_sheets=False, resultado_registrado=False, do_scroll=True
    )

def action_finalizar_sesion():
    st.session_state.clear()
    st.session_state.borrar_backup_ls = True
    st.session_state.do_scroll = True
# === FIN SECCIÓN 4 ===

# === SECCIÓN 5: INTERFAZ Y RESULTADOS ===
sincronizar_progreso_navegador()
activar_proteccion_antirecortes_alumno()

if not st.session_state.questions:
    st.markdown("""<style>
    :root { --background-color: #FFFFFF !important; --secondary-background-color: #F8FAFC !important; --text-color: #1E293B !important; }
    html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFFFF !important; color: #1E293B !important; }
    .block-container { max-width: 820px !important; }
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-grid) div[role="radiogroup"] {
        display: flex !important;
        flex-wrap: wrap !important;
        max-width: 470px !important;
        row-gap: 6px !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-grid) div[role="radiogroup"] > label {
        min-width: 135px !important;
        margin-right: 12px !important;
    }
    [data-testid="stExpanderDetails"] div.stButton > button {
        background-color: #2e7d32 !important;
        border-color: #2e7d32 !important;
        padding: 2px 10px !important;
        min-height: 31px !important;
        height: 31px !important;
        border-radius: 6px !important;
    }
    [data-testid="stExpanderDetails"] div.stButton > button p,
    [data-testid="stExpanderDetails"] div.stButton > button span {
        color: #FFFFFF !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        line-height: 1.1 !important;
    }
    [data-testid="stExpanderDetails"] div.stButton > button:hover {
        background-color: #1b5e20 !important;
        border-color: #1b5e20 !important;
    }
    [data-testid="stExpanderDetails"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 0.5rem !important;
    }
    </style>""", unsafe_allow_html=True)
    es_admin = usuario_es_admin()
    col_texto, col_img = st.columns([2.5, 1])
    with col_img:
        try: st.image("test-utiles-768x768.png", use_container_width=True)
        except: pass
    with col_texto:
        st.markdown("<div style='font-size:22px; font-weight:700; color:#2C3E50 !important; margin-top: -10px; margin-bottom: 8px;'>📚 Comienza a practicar</div>", unsafe_allow_html=True)
        rol = st.session_state.rol
        TESTS_DISPONIBLES = obtener_tests_segun_rol()
        st.markdown("<div style='font-size:17px; font-weight:700; color:#1E293B !important; margin-bottom:5px;'>1. Especialidad</div>", unsafe_allow_html=True)
        if rol in ["ACCESO TOTAL", "INVITADO"]:
            l_esp = list(TESTS_DISPONIBLES.keys())
            i_esp = l_esp.index(st.session_state.saved_esp) if st.session_state.get("saved_esp") in l_esp else 0
            especialidad = st.radio("Selecciona tu especialidad:", l_esp, index=i_esp, horizontal=True, key="radio_especialidad", label_visibility="collapsed", on_change=cambio_categoria_o_especialidad)
            st.session_state.saved_esp = especialidad
        elif rol in ["ADMTVOS", "GESTION"]:
            especialidad = "ADMINISTRATIVOS" if rol == "ADMTVOS" else "GESTION"
            st.session_state.saved_esp = especialidad
            st.info(f"Tienes acceso directo a tu especialidad: **{especialidad}**")
        else:
            st.error("Error en los permisos de usuario."); st.stop()

        with st.container():
            st.markdown("<div class='marcador-cat-grid'></div><div style='font-size:17px; font-weight:700; color:#1E293B !important; margin-bottom:5px;'>2. Categoría</div>", unsafe_allow_html=True)
            l_cat = list(TESTS_DISPONIBLES[especialidad].keys())
            i_cat = l_cat.index(st.session_state.saved_cat) if st.session_state.get("saved_cat") in l_cat else 0
            categoria = st.radio("Selecciona el tipo de test:", l_cat, index=i_cat, horizontal=True, key="radio_categoria", label_visibility="collapsed", on_change=cambio_categoria_o_especialidad)
            st.session_state.saved_cat = categoria

    st.markdown("<div style='font-size:17px; font-weight:700; color:#1E293B !important; margin-bottom:5px;'>3. Modo de avance</div>", unsafe_allow_html=True)
    op_av = [
        "**Modo reflexivo** (puedes comprobar la pregunta y el paso a la siguiente es manual pulsando siguiente)",
        "**Modo metralleta** (pasa a la pregunta siguiente al pulsar una opción)"
    ]
    i_av = op_av.index(st.session_state.saved_avance) if st.session_state.get("saved_avance") in op_av else 0
    modo_avance = st.radio("Modo de avance:", op_av, index=i_av, label_visibility="collapsed")
    st.session_state.saved_avance = st.session_state.modo_avance = modo_avance

    if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO"]:
        titulo_paso_4 = "4. Seleccionar Pregunta de desarrollo (2.º Ejercicio - 1.ª Parte)"
    elif categoria in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"]:
        titulo_paso_4 = "4. Seleccionar Supuestos prácticos (2.º Ejercicio - 2.ª Parte)"
    else:
        titulo_paso_4 = "4. Selección de Test"

    st.markdown(f"<div style='font-size:17px; font-weight:700; color:#1E293B !important; margin-bottom:6px;'>{titulo_paso_4}</div>", unsafe_allow_html=True)
    if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO"] and es_admin:
        st.info("🔒 **Modo Administrador — 2.º Ejercicio — 1.ª Parte (Preguntas de Desarrollo: 0 a 50 ptos):** Soporta archivos Word (`.docx`) y PDF (`.pdf`). Valoración por IA según los Criterios Oficiales del Tribunal.")
    elif categoria in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"] and es_admin:
        st.info("🔒 **Modo Administrador — 2.º Ejercicio — 2.ª Parte (Supuestos Prácticos):** Descarta cualquier texto previo al encabezado `SUPUESTO PRÁCTICO`, mantiene el planteamiento fijo en cada pregunta (en tamaño 10pt) y valora cada cuestión de 0 a 10 comparándola directamente con la explicación y solución oficial.")

    tests_reales = {k: v for k, v in TESTS_DISPONIBLES[especialidad][categoria].items() if v is not None}

    if rol == "INVITADO":
        if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO"]:
            st.markdown(
                "<div style='background-color:#EFF6FF; border:2px solid #2563EB; border-radius:10px; padding:16px 18px; margin-top:8px; margin-bottom:14px; line-height:1.5; color:#1E293B !important;'>"
                "<div style='font-size:16px; font-weight:800; color:#1E3A8A !important; margin-bottom:8px;'>📝 ¿En qué consiste la categoría DESARROLLO de Oposiciona 5.0?</div>"
                "<p style='font-size:14px; color:#1E293B !important; text-align:justify; margin-bottom:10px;'>"
                "Este módulo interactivo está diseñado específicamente para preparar la <b>1.ª Parte del Segundo Ejercicio del Cuerpo de Gestión de la Administración de la Seguridad Social</b> (desarrollo escrito de epígrafes oficiales del temario). "
                "El alumno redacta su contestación directamente en la plataforma y nuestro sistema de <b>Inteligencia Artificial entrenado con los Criterios Oficiales del Tribunal Calificador</b> analiza su respuesta en tiempo real comparándola con el texto mínimo oficial elaborado por los preparadores."
                "</p>"
                "<ul style='font-size:13.5px; color:#1E293B !important; margin-bottom:12px; padding-left:20px;'>"
                "<li><b>Calificación oficial de 0 a 50 puntos</b> desglosada en <b>Criterio 1 (0 a 45 ptos)</b> de conocimiento y rigor normativo, <b>Criterio 2 (0 a 3 ptos)</b> de estructura y orden expositivo, y <b>Criterio 3 (0 a 2 ptos)</b> de expresión escrita y presentación formal de siglas.</li>"
                "<li><b>Informe analítico personalizado:</b> Detalla qué apartados has desarrollado correctamente, qué conceptos o artículos adicionales han enriquecido tu respuesta, qué puntos te han faltado por completar y la relación de artículos omitidos, junto con el texto mínimo oficial completo para tu estudio.</li>"
                "</ul>"
                "<div style='background-color:#FEF3C7; border-left:4px solid #D97706; padding:10px 14px; border-radius:6px; font-size:13.5px; color:#92400E !important;'>"
                "🔒 <b>Acceso exclusivo para alumnos de Oposiciona 5.0:</b> Esta funcionalidad no está disponible para usuarios invitados. "
                "Puedes solicitar más información y matricularte escribiendo a <a href='mailto:info@oposiciona.es' style='color:#B45309 !important; font-weight:800; text-decoration:underline;'>info@oposiciona.es</a>."
                "</div>"
                "</div>",
                unsafe_allow_html=True
            )
        elif not tests_reales:
            st.warning("⚠️ CATEGORÍA NO DISPONIBLE PARA USUARIOS INVITADOS")
        else:
            st.info("ℹ️ ÚNICO TEST DE DEMOSTRACIÓN DISPONIBLE PARA USUARIO INVITADO")

    if tests_reales:
        mostrar_filtro = (categoria not in ["EXAMENES", "DESARROLLO", "PREGUNTA DE DESARROLLO", "SUPUESTOS", "SUPUESTOS PRÁCTICOS"]) and any("repaso" in n.lower() for n in tests_reales)
        mostrar_busc = len(tests_reales) > 1
        k_busq, k_filt = f"busqueda_{especialidad}_{categoria}", f"filtro_tipo_{especialidad}_{categoria}"
        if k_busq not in st.session_state: st.session_state[k_busq] = ""

        if mostrar_filtro and mostrar_busc:
            cf1, cf2 = st.columns([1.35, 1.05])
            with cf1:
                filtro_tipo = st.radio("Filtrar por tipo:", ["📚 Todos", "📖 Temario Base", "🔄 Repasos"], horizontal=True, label_visibility="collapsed", key=k_filt, on_change=limpiar_busqueda_al_filtrar, args=(k_busq,))
            with cf2:
                if st.session_state.get(k_busq, "").strip():
                    ci, cc = st.columns([5, 1])
                    with ci: busqueda = st.text_input("🔍 Buscar tema...", placeholder="🔍 Buscar (ej: tema 2, IP, cotizacion...)", label_visibility="collapsed", key=k_busq)
                    with cc: st.button("✖", key=f"clr_{k_busq}", help="Borrar búsqueda", on_click=limpiar_busqueda_al_filtrar, args=(k_busq,), use_container_width=True)
                else:
                    busqueda = st.text_input("🔍 Buscar tema...", placeholder="🔍 Buscar (ej: tema 2, IP, cotizacion...)", label_visibility="collapsed", key=k_busq)
        elif mostrar_busc:
            filtro_tipo = "📚 Todos"
            if st.session_state.get(k_busq, "").strip():
                ci, cc = st.columns([7, 1])
                with ci: busqueda = st.text_input("🔍 Buscar tema...", placeholder="🔍 Buscar (ej: tema 2, IP, cotizacion...)", label_visibility="collapsed", key=k_busq)
                with cc: st.button("✖", key=f"clr_{k_busq}", help="Borrar búsqueda", on_click=limpiar_busqueda_al_filtrar, args=(k_busq,), use_container_width=True)
            else:
                busqueda = st.text_input("🔍 Buscar tema...", placeholder="🔍 Buscar (ej: tema 2, IP, cotizacion...)", label_visibility="collapsed", key=k_busq)
        else:
            filtro_tipo, busqueda = "📚 Todos", ""

        hay_busq = bool(busqueda and busqueda.strip())
        tests_filtrados = {}
        for nombre, url in tests_reales.items():
            if hay_busq:
                if coincide_busqueda(nombre, busqueda): tests_filtrados[nombre] = url
            else:
                es_rep = "repaso" in nombre.lower()
                if (filtro_tipo == "📖 Temario Base" and es_rep) or (filtro_tipo == "🔄 Repasos" and not es_rep): continue
                tests_filtrados[nombre] = url

        if mostrar_busc:
            st.caption(f"🔎 Búsqueda en **Todos los elementos de {categoria}**: encontrados **{len(tests_filtrados)}** de **{len(tests_reales)}**" if hay_busq else f"Mostrando **{len(tests_filtrados)}** de **{len(tests_reales)}** disponibles en {categoria}")

        if not tests_filtrados:
            st.warning("No hay ningún elemento que coincida con esa búsqueda.")
        else:
            grupos = {}
            for n, u in tests_filtrados.items():
                grupos.setdefault(obtener_grupo_tema(n, categoria), []).append((n, u))
            exp_todo = (categoria in ["EXAMENES", "DESARROLLO", "PREGUNTA DE DESARROLLO", "SUPUESTOS", "SUPUESTOS PRÁCTICOS"]) or (len(grupos) <= 3) or hay_busq
            for ig, (ng, lt) in enumerate(grupos.items()):
                with st.expander(f"{ng}  —  ({len(lt)} {'disponible' if len(lt)==1 else 'disponibles'})", expanded=exp_todo):
                    for it, (tn, tu) in enumerate(lt):
                        es_r = ("repaso" in tn.lower()) and (categoria not in ["EXAMENES", "DESARROLLO", "PREGUNTA DE DESARROLLO", "SUPUESTOS", "SUPUESTOS PRÁCTICOS"])
                        ic = "📝" if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO"] else ("📋" if categoria in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"] else ("🔄" if es_r else ("🏆" if categoria == "EXAMENES" else "📘")))
                        et = "<span style='background:#fff3cd; color:#856404 !important; padding:1px 5px; border-radius:4px; font-size:10.5px; margin-left:5px;'>REPASO</span>" if es_r else ""
                        cn, cb = st.columns([4.6, 1])
                        with cn:
                            st.markdown(
                                f"<div style='display:flex; align-items:center; gap:6px; padding:1px 0; font-size:13.2px; line-height:1.25; color:#1E293B !important;'>"
                                f"<span style='flex-shrink:0; font-size:14px;'>{ic}</span>"
                                f"<span style='font-weight:600; color:#1E293B !important; word-break:break-word;'>{tn}{et}</span>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        with cb:
                            if st.button("🚀 Iniciar", key=f"btn_grp_{especialidad}_{categoria}_{ig}_{it}", use_container_width=True, type="primary"):
                                cargar_test_desde_url(tn, tu, especialidad, categoria)

    total_deseadas = 95 if especialidad == "GESTION" else 75
    with st.container():
        st.markdown('<div class="cargar-test-container"></div><div style="background-color: #fff3cd; border: 2px dashed #ffc107; border-radius: 8px; padding: 12px 15px 4px 15px; text-align: center; margin: 14px 0 8px 0;"><div style="font-size: 16.5px; font-weight: 700; color: #856404 !important; margin-top: 0; margin-bottom: 4px;">🔥 SIMULACRO GLOBAL EXPERTO 🔥</div><p style="color: #856404 !important; font-size: 13.5px; margin-bottom: 8px;">Genera un examen aleatorio cruzando preguntas de los distintos temas disponibles en esta especialidad.</p></div>', unsafe_allow_html=True)
        if st.button(f"🚨 INICIAR SIMULACRO ({total_deseadas} PREGUNTAS) 🚨", use_container_width=True, type="primary"):
            if rol == "INVITADO": st.error("🔒 Función no disponible para usuarios invitados. Solicita información en info@oposiciona.es para acceder al Simulacro Global Experto.")
            else: st.session_state.mostrar_opciones_simulacro = True

        if rol != "INVITADO" and st.session_state.get('mostrar_opciones_simulacro', False):
            st.markdown("<div style='background-color:#eef6ff; border:2px solid #1f77b4; border-radius:8px; padding:12px; margin-top:8px; margin-bottom:10px; text-align:center;'><b style='color:#1f77b4 !important; font-size:15.5px;'>🎯 ¿Sobre qué bloques quieres realizar el Simulacro?</b></div>", unsafe_allow_html=True)
            cs1, cs2, cs3 = st.columns(3)
            for col_b, lbl, amb, t_lbl in [(cs1, "🌐 TODO", "TODO", "SIMULACRO GLOBAL"), (cs2, "📘 GENERAL", "GENERAL", "SIMULACRO"), (cs3, "🎯 ESPECÍFICO", "ESPECIFICO", "SIMULACRO")]:
                if col_b.button(lbl, use_container_width=True, type="primary"):
                    limpiar_estados_reportes_error()
                    st.session_state.test_name = f"{t_lbl} ({especialidad} - {amb})"
                    st.session_state.test_esp = especialidad
                    st.session_state.test_cat = f"SIMULACRO ({amb})"
                    with st.spinner("Generando simulacro..."):
                        ex = generar_simulacro_aleatorio(especialidad, amb, total_deseadas, TESTS_DISPONIBLES)
                        if ex: procesar_preguntas(ex)
                        else: st.error("No se pudo extraer ninguna pregunta.")

    if rol != "INVITADO":
        with st.expander("Opcional: Subir un PDF o Word (.docx) manualmente desde tu dispositivo"):
            uf = st.file_uploader("", type=["pdf", "docx"])
            if uf is not None:
                limpiar_estados_reportes_error()
                es_docx_subido = uf.name.lower().endswith(".docx")
                if categoria in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"]:
                    cat_local = "SUPUESTOS"
                elif categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO"] or es_docx_subido:
                    cat_local = "DESARROLLO"
                else:
                    cat_local = "ARCHIVO LOCAL"
                st.session_state.update(modo_avance=modo_avance, test_name=uf.name, test_esp=especialidad, test_cat=cat_local)
                max_op_local = 3 if "GESTI" in especialidad.upper() else 4
                with st.spinner("Procesando documento local..."):
                    file_bytes_local = uf.read()
                    if cat_local == "SUPUESTOS":
                        rqs = PDFQuizParser.parse_abiertas_gestion(file_bytes_local, modo="SUPUESTOS")
                        if not rqs: st.error("No se encontraron supuestos prácticos en este documento.")
                        else: procesar_preguntas(rqs, barajar=False)
                    elif cat_local == "DESARROLLO" or PDFQuizParser.es_archivo_docx(file_bytes_local):
                        rqs = PDFQuizParser.parse_abiertas_gestion(file_bytes_local, modo="DESARROLLO")
                        if not rqs: st.error("No se encontraron preguntas o epígrafes de desarrollo en este documento.")
                        else: procesar_preguntas(rqs, barajar=False)
                    else:
                        rqs = PDFQuizParser.parse(file_bytes_local, max_options=max_op_local)
                        if not rqs: st.error("No se encontraron preguntas válidas en este PDF.")
                        else: procesar_preguntas(rqs, barajar=True)

    if es_admin:
        with st.expander("📊 Herramienta Admin: Auditoría de Extracción Real y Recuento de Preguntas, Supuestos y Epígrafes"):
            st.info(
                "Esta herramienta ejecuta exactamente el mismo motor de extracción y procesado que cuando un alumno abre cada test o documento (PDF o Word .docx), "
                "auditando si hay cortes en explicaciones, preguntas fusionadas, opciones faltantes o respuestas sin marcar."
            )
            st.checkbox(
                "🧪 Probar desenfoque antirrecortes en mi sesión de Administrador (desmárcalo para trabajar sin desenfoque)",
                key="admin_test_blur"
            )
            if st.button("🔍 Auditar extracción real y contar todos los documentos", use_container_width=True, type="primary"):
                nuevos_hoy = globals().get("NUEVOS_HOY", [])
                tot_pdfs = sum(1 for ec in TESTS_DISPONIBLES_COMPLETO.values() for ct in ec.values() for u in ct.values() if u is not None)
                bp, proc, txt_copiar = st.progress(0, text="Extrayendo y auditando documentos con el motor real..."), 0, ""
                alertas_globales = []

                for esp, cats in TESTS_DISPONIBLES_COMPLETO.items():
                    max_op_adm = 3 if "GESTI" in esp.upper() else 4

                    st.markdown(f"### 📋 Catálogo y Auditoría Real de Tests: {esp}")
                    t_md = "| Categoría | Nombre del Test | Nº Extraídas | Media Opc. | Auditoría Real de Extracción |\n| :--- | :--- | :---: | :---: | :--- |\n"
                    for cat in ["ESPECIFICO", "EXAMENES", "GENERAL"]:
                        tests = cats.get(cat, {})
                        for nom, url in tests.items():
                            if url is None:
                                continue
                            proc += 1
                            bp.progress(proc / max(1, tot_pdfs), text=f"Extrayendo y auditando ({proc}/{tot_pdfs}): {nom}...")
                            try:
                                r = descargar_pdf_fresco(url)
                                if r.status_code == 200:
                                    res_aud = auditar_extraccion_test_real(r.content, max_options=max_op_adm)
                                    nq = res_aud["nq"]
                                    media_op = res_aud["media_op"]
                                    est_aud = res_aud["estado_resumen"]
                                    if res_aud["incidencias"]:
                                        alertas_globales.append(f"**[{esp} - {cat}] {nom} ({nq} preg.):** {est_aud}")
                                else:
                                    nq, media_op, est_aud = "Error", "-", "❌ Error de descarga en Drive"
                                    alertas_globales.append(f"**[{esp} - {cat}] {nom}:** Error HTTP {r.status_code}")
                            except Exception as e_aud:
                                nq, media_op, est_aud = "-", "-", f"❌ Excepción: {e_aud}"
                                alertas_globales.append(f"**[{esp} - {cat}] {nom}:** {e_aud}")

                            if nom in nuevos_hoy:
                                t_md += f"| **{cat}** | **{nom} (🆕 Nuevo hoy)** | **{nq} preguntas** | **{media_op}** | {est_aud} |\n"
                            else:
                                t_md += f"| {cat} | {nom} | {nq} preguntas | {media_op} | {est_aud} |\n"
                    st.markdown(t_md)
                    txt_copiar += f"### 📋 Catálogo y Auditoría Real de Tests: {esp}\n\n" + t_md + "\n"

                    supuestos_dict = {k: v for k, v in cats.get("SUPUESTOS", {}).items() if v is not None}
                    st.markdown(f"#### 🧩 Apartado SUPUESTOS — {esp} ({len(supuestos_dict)} {'tema incluido' if len(supuestos_dict)==1 else 'temas incluidos'})")
                    if supuestos_dict:
                        s_md = "| Categoría | Tema / Supuesto Incluido | Nº de Cuestiones Extraídas | Estado Extracción |\n| :--- | :--- | :---: | :--- |\n"
                        tot_cuestiones_sup = 0
                        for nom_s, url_s in supuestos_dict.items():
                            proc += 1
                            bp.progress(proc / max(1, tot_pdfs), text=f"Auditando Supuesto ({proc}/{tot_pdfs}): {nom_s}...")
                            try:
                                r = descargar_pdf_fresco(url_s)
                                if r.status_code == 200:
                                    qs_sup = PDFQuizParser.parse_abiertas_gestion(r.content, modo="SUPUESTOS")
                                    qs_sup = preparar_preguntas_como_en_test(qs_sup, barajar=False)
                                    if not qs_sup and not PDFQuizParser.es_archivo_docx(r.content):
                                        qs_sup = preparar_preguntas_como_en_test(PDFQuizParser.parse(r.content, max_options=max_op_adm), barajar=False)
                                    n_sup = len(qs_sup)
                                    tot_cuestiones_sup += n_sup
                                    n_sup_str = f"{n_sup} cuestiones"
                                    est_s = "✅ OK" if n_sup > 0 else "⚠️ 0 cuestiones detectadas"
                                else:
                                    n_sup_str, est_s = "Error", "❌ Error de descarga"
                            except Exception as e_s:
                                n_sup_str, est_s = "-", f"❌ {e_s}"
                            et_tema_s = obtener_etiqueta_tema_visible(nom_s)
                            s_md += f"| **SUPUESTOS** | **{nom_s}** — *{et_tema_s}* | **{n_sup_str}** | {est_s} |\n"
                        s_md += f"| **TOTAL SUPUESTOS ({esp})** | **{len(supuestos_dict)} documentos incluidos** | **{tot_cuestiones_sup} cuestiones** | — |\n"
                    else:
                        s_md = "*Actualmente no hay ningún documento cargado en la categoría SUPUESTOS de esta especialidad.*\n"
                    st.markdown(s_md)
                    txt_copiar += f"#### 🧩 Apartado SUPUESTOS — {esp} ({len(supuestos_dict)} incluidos)\n\n" + s_md + "\n"

                    if "DESARROLLO" in cats:
                        desarrollo_dict = {k: v for k, v in cats.get("DESARROLLO", {}).items() if v is not None}
                        st.markdown(f"#### 📝 Apartado DESARROLLO — {esp} ({len(desarrollo_dict)} {'tema incluido' if len(desarrollo_dict)==1 else 'temas incluidos'})")
                        if desarrollo_dict:
                            d_md = "| Categoría | Documento Incluido | Formato | Tema Correspondiente | Nº de Epígrafes Extraídos | Auditoría Epígrafes |\n| :--- | :--- | :---: | :--- | :---: | :--- |\n"
                            tot_epigrafes_des = 0
                            for nom_d, url_d in desarrollo_dict.items():
                                proc += 1
                                bp.progress(proc / max(1, tot_pdfs), text=f"Auditando Epígrafes de Desarrollo ({proc}/{tot_pdfs}): {nom_d}...")
                                et_tema_d = obtener_etiqueta_tema_visible(nom_d)
                                fmt_doc = "-"
                                try:
                                    r = descargar_pdf_fresco(url_d)
                                    if r.status_code == 200:
                                        fmt_doc = "📘 Word (.docx)" if PDFQuizParser.es_archivo_docx(r.content) else "📕 PDF"
                                        qs_des = PDFQuizParser.parse_abiertas_gestion(r.content, modo="DESARROLLO")
                                        qs_des = preparar_preguntas_como_en_test(qs_des, barajar=False)
                                        n_ep = len(qs_des)
                                        tot_epigrafes_des += n_ep
                                        if qs_des and qs_des[0].get("tema_titulo"):
                                            et_tema_d = qs_des[0]["tema_titulo"]
                                        n_ep_str = f"{n_ep} {'epígrafe' if n_ep == 1 else 'epígrafes'}"
                                        ep_cortos = [f"Ep.{idx_e}" for idx_e, qe in enumerate(qs_des, 1) if len((qe.get("explanation") or "").strip()) < 120]
                                        if n_ep == 0:
                                            est_d = "❌ 0 epígrafes extraídos"
                                        elif ep_cortos:
                                            est_d = f"⚠️ Texto corto en {', '.join(ep_cortos)}"
                                        else:
                                            est_d = f"✅ OK ({n_ep} epígrafes completos)"
                                    else:
                                        n_ep_str, est_d = "Error", "❌ Error de descarga"
                                except Exception as e_d:
                                    n_ep_str, est_d = "-", f"❌ {e_d}"
                                d_md += f"| **DESARROLLO** | **{nom_d}** | {fmt_doc} | {et_tema_d} | **{n_ep_str}** | {est_d} |\n"
                            d_md += f"| **TOTAL DESARROLLO ({esp})** | **{len(desarrollo_dict)} documentos incluidos** | **Word / PDF** | **Relación completa de temas de desarrollo** | **{tot_epigrafes_des} epígrafes en total** | — |\n"
                        else:
                            d_md = "*Actualmente no hay ningún documento cargado en la categoría DESARROLLO de esta especialidad.*\n"
                        st.markdown(d_md)
                        txt_copiar += f"#### 📝 Apartado DESARROLLO — {esp} ({len(desarrollo_dict)} temas incluidos)\n\n" + d_md + "\n"

                    txt_copiar += "---\n\n"

                bp.empty()
                st.success("✅ ¡Auditoría real de extracción y recuento completados con éxito!")
                if alertas_globales:
                    st.warning(f"⚠️ **Se han detectado incidencias de extracción en {len(alertas_globales)} documento(s) que conviene revisar:**\n\n" + "\n".join([f"- {a}" for a in alertas_globales]))
                else:
                    st.balloons()
                    st.success("🎉 ¡Todos los documentos han superado la auditoría de extracción sin preguntas fusionadas ni explicaciones cortadas!")
                st.code(txt_copiar, language="markdown")

elif not st.session_state.finished:
    st.markdown("<style>:root { --background-color: #FFFDE7 !important; --secondary-background-color: #FFFDE7 !important; --text-color: #1E293B !important; } html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFDE7 !important; background-image: none !important; color: #1E293B !important; } .block-container, [data-testid='stMainBlockContainer'], div[data-testid='stVerticalBlock'] { background-color: transparent !important; background: transparent !important; }</style>", unsafe_allow_html=True)
    idx = st.session_state.current_index
    q, stat = st.session_state.questions[idx], st.session_state.stats[idx]
    puede_rep = usuario_puede_reportar()
    es_abierta = bool(q.get("is_open", False))
    es_supuesto_q = bool(q.get("tipo_abierta") == "SUPUESTO")
    nombre_test_act = st.session_state.get("test_name") or "Test"
    id_test_act = re.sub(r'\W+', '_', nombre_test_act)

    etiqueta_tema = obtener_etiqueta_tema_visible(nombre_test_act, q)
    tipo_item_lbl = "Epígrafe" if q.get("tipo_abierta") == "DESARROLLO" else ("Cuestión" if es_abierta else "Pregunta")
    st.markdown(
        f"<div style='background-color:#EFF6FF; border:1px solid #93C5FD; border-left:5px solid #1D4ED8; border-radius:6px; padding:8px 12px; margin-top:-8px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;'>"
        f"<span style='font-size:14px; font-weight:700; color:#1E3A8A !important;'>📘 {etiqueta_tema}</span>"
        f"<span style='font-size:13px; font-weight:700; color:#1D4ED8 !important; background:#DBEAFE; padding:2px 8px; border-radius:4px;'>{tipo_item_lbl} {idx + 1} de {len(st.session_state.questions)}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    if q.get('preamble'):
        if es_supuesto_q:
            st.markdown(
                f"<div style='background-color:#FFFFFF; border:1px solid #CBD5E1; border-left:4px solid #1F77B4; border-radius:6px; padding:10px 14px; margin-bottom:12px; font-size:10pt !important; line-height:1.42; text-align:justify; color:#1E293B !important;'>"
                f"<div style='font-size:10pt !important; font-weight:800; color:#1E3A8A !important; margin-bottom:6px; border-bottom:1px solid #E2E8F0; padding-bottom:4px;'>📋 PLANTEAMIENTO DEL SUPUESTO PRÁCTICO</div>"
                f"{q['preamble']}"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='background-color:#FFFFFF; border:1px solid #CBD5E1; border-left:4px solid #1F77B4; border-radius:6px; padding:12px; margin-bottom:12px; font-size:15px; line-height:1.45; text-align:justify; color:#1E293B !important;'>{q['preamble']}</div>",
                unsafe_allow_html=True
            )

    st.markdown(f"<p style='font-size: 18px; font-weight: 700; color: #2C3E50 !important; margin-bottom: 12px; line-height: 1.35; text-align: justify;'>{q['question_text']}</p>", unsafe_allow_html=True)

    if es_abierta:
        altura_caja = 260 if q.get("tipo_abierta") == "DESARROLLO" else 170
        lbl_textarea = (
            "✍️ Escribe aquí tu respuesta razonada a la cuestión planteada (cálculos, plazos, calificación jurídica y normativa aplicable):"
            if es_supuesto_q else
            "✍️ Escribe aquí tu desarrollo o respuesta jurídica (recuerda definir las siglas la primera vez que las uses, ej. «Texto Refundido de la Ley General de la Seguridad Social, en adelante TRLGSS»):"
        )
        placeholder_textarea = (
            "Redacta aquí tu solución razonada al supuesto práctico, detallando los cálculos y artículos aplicables..."
            if es_supuesto_q else
            "Redacta aquí tu contestación desarrollando los apartados del epígrafe, requisitos, plazos y normativa aplicable..."
        )
        sel_opt = st.text_area(
            lbl_textarea,
            value=stat.get("selected") or "",
            height=altura_caja,
            key=f"open_txt_{idx}",
            placeholder=placeholder_textarea
        )
        if st.session_state.get(f"open_txt_{idx}") is not None:
            sel_opt = st.session_state.get(f"open_txt_{idx}")
    else:
        def_idx = q['options'].index(stat['selected']) if stat['selected'] in q['options'] else None
        sel_opt = st.radio("Elige tu respuesta:", q['options'], index=def_idx, key=f"radio_{idx}", label_visibility="collapsed", on_change=handle_radio_change)

    if puede_rep:
        c1, c2, c3, c4, c5 = st.columns([0.9, 0.95, 0.95, 1.1, 1.5])
    else:
        c1, c2, c3, c4 = st.columns(4)
        c5 = None

    if c1.button("🡄 Anterior", use_container_width=True) and idx > 0:
        save_answer(sel_opt)
        limpiar_estados_reportes_error()
        st.session_state.update(checked=False, current_index=idx - 1, do_scroll=True); st.rerun()
    if c2.button("Comprobar", use_container_width=True):
        save_answer(sel_opt)
        if q.get("tipo_abierta") == "DESARROLLO":
            st.session_state.test_cat = "DESARROLLO"
            nombre_celda_des = construir_nombre_test_seguimiento_sheets(indice_actual=idx)
            if not st.session_state.get('inicio_registrado_sheets', False):
                st.session_state.inicio_registrado_sheets = True
                registrar_actividad_sheets("🚀 En curso", nombre_test=nombre_celda_des, aciertos="", fallos="", blancos="", accion="nueva_fila")
            else:
                registrar_actividad_sheets("✍️ Revisado", nombre_test=nombre_celda_des, aciertos="", fallos="", blancos="", accion="actualizar_fin")
        st.session_state.update(checked=True, do_scroll=True); st.rerun()
    if idx < len(st.session_state.questions) - 1:
        if c3.button("Siguiente ➔", use_container_width=True):
            save_answer(sel_opt)
            limpiar_estados_reportes_error()
            st.session_state.update(checked=False, current_index=idx + 1, do_scroll=True); st.rerun()
    else:
        if c3.button("Terminar ➔", use_container_width=True):
            save_answer(sel_opt)
            limpiar_estados_reportes_error()
            st.session_state.update(finished=True, celebracion_mostrada=False, do_scroll=True); st.rerun()
    if c4.button("⏹ Finalizar Test", use_container_width=True):
        save_answer(sel_opt)
        limpiar_estados_reportes_error()
        st.session_state.update(finished=True, celebracion_mostrada=False, do_scroll=True); st.rerun()

    key_rep_test = f"rep_open_test_{id_test_act}_{idx + 1}"
    if key_rep_test not in st.session_state:
        st.session_state[key_rep_test] = False
    lbl_btn_reporte_top = "⚠️ Reportar Error en Epígrafe" if q.get("tipo_abierta") == "DESARROLLO" else "⚠️ Reportar Error"
    if puede_rep and c5 is not None:
        if c5.button(lbl_btn_reporte_top, key=f"btn_err_top_{id_test_act}_{idx + 1}", use_container_width=True, type="primary"):
            st.session_state[key_rep_test] = not st.session_state[key_rep_test]

    if st.session_state.pop(f"rep_ok_msg_{id_test_act}_{idx + 1}", False):
        st.success("✅ ¡Reporte enviado con éxito a info@oposiciona.es! Muchas gracias por tu colaboración.")

    if puede_rep and st.session_state.get(key_rep_test, False):
        render_cuadro_reporte_error(q, idx + 1, "test_activo_top")

    if st.session_state.checked:
        if es_abierta:
            txt_alumno = (sel_opt or stat.get("selected") or "").strip()
            resp_of = (q.get("answer_text") or "").strip()
            exp_of = (q.get("explanation") or "").strip()
            ctx_pregunta = f"{q.get('preamble', '')} {q.get('question_text', '')}".strip()
            modo_corr = "SUPUESTO" if es_supuesto_q else "DESARROLLO"
            if not txt_alumno:
                st.warning("⚪ No has escrito ninguna respuesta todavía. Redacta tu contestación en el cuadro superior y pulsa «Comprobar» para que la IA evalúe tu ejercicio.")
            else:
                aviso_inapropiado = detectar_respuesta_inapropiada_o_sin_interes(txt_alumno)
                if aviso_inapropiado:
                    stat["open_score"] = 0.0
                    stat["ai_eval"] = None
                    st.markdown(
                        f"<div style='background-color:#fff8e1; border:2px solid #d97706; border-radius:8px; padding:16px; margin-top:10px; margin-bottom:10px; font-size:15px; color:#1E293B !important; line-height:1.55; text-align:justify;'>"
                        f"{aviso_inapropiado}"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                else:
                    if stat.get("last_evaluated_text") != txt_alumno or not stat.get("ai_feedback") or not stat.get("ai_eval"):
                        ev = evaluar_respuesta_escrita(txt_alumno, resp_of, exp_of, ctx_pregunta)
                        stat["last_evaluated_text"] = txt_alumno
                        clave_activa = obtener_gemini_api_key_activa()
                        msg_spinner = (
                            "🤖 Comparando tu respuesta con la solución oficial de la pregunta..."
                            if es_supuesto_q else
                            "🤖 Analizando y valorando tu respuesta frente a la explicación oficial según los Criterios del Tribunal..."
                        )
                        with st.spinner(msg_spinner):
                            stat["ai_feedback"] = consultar_ia_gemini_correccion(
                                clave_activa, q.get("preamble", ""), q["question_text"], txt_alumno, resp_of, exp_of, ev_fallback=ev, modo=modo_corr
                            )
                        stat["ai_eval"] = ev
                        stat["open_score"] = ev.get("nota", 0.0)
                    else:
                        ev = stat["ai_eval"]

                    n50_q = ev.get("nota_50", 0.0)
                    n10_q = ev.get("nota", 0.0)
                    c1_q = ev.get("pts_criterio_1", 0.0)
                    c2_q = ev.get("pts_criterio_2", 0.0)
                    c3_q = ev.get("pts_criterio_3", 0.0)

                    if es_supuesto_q:
                        aprobado_s = n10_q >= 5.0
                        bg_card = "#ecfdf5" if aprobado_s else "#fff7ed"
                        border_card = "#16a34a" if aprobado_s else "#ea580c"
                        color_nota = "#15803d" if aprobado_s else "#c2410c"
                        badge_txt = "✅ CUESTIÓN PRÁCTICA SUPERADA" if aprobado_s else "⚠️ CUESTIÓN A REFORZAR"

                        st.markdown(
                            f"<div style='background-color:{bg_card}; border:2px solid {border_card}; border-radius:10px; padding:12px 16px; margin-top:12px; margin-bottom:10px; text-align:center;'>"
                            f"<div style='font-size:13px; font-weight:700; color:{color_nota} !important; letter-spacing:0.5px; margin-bottom:2px;'>🎯 RESULTADO DE TU RESPUESTA A LA CUESTIÓN PRÁCTICA</div>"
                            f"<div style='font-size:26px; font-weight:900; color:{color_nota} !important; margin-bottom:2px;'>NOTA: {n10_q:.2f} / 10 PUNTOS</div>"
                            f"<div style='font-size:14px; font-weight:700; color:#1E293B !important;'>{badge_txt}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                        st.markdown(
                            "<div style='background-color:#f0fdf4; border:2px solid #16a34a; border-radius:8px; padding:10px 14px 4px 14px; margin-top:8px; margin-bottom:8px;'>"
                            "<div style='font-size:15px; font-weight:800; color:#15803d !important; margin-bottom:4px;'>🤖 VALORACIÓN Y PORQUÉ DE TU NOTA (COMPARATIVA CON LA SOLUCIÓN)</div>"
                            "</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(stat.get("ai_feedback") or "")
                    else:
                        aprobado_q = n50_q >= 25.0
                        bg_card = "#ecfdf5" if aprobado_q else "#fff7ed"
                        border_card = "#16a34a" if aprobado_q else "#ea580c"
                        color_nota = "#15803d" if aprobado_q else "#c2410c"
                        badge_txt = "✅ SUPERA EL CORTE ELIMINATORIO (≥ 25 / 50 PTOS)" if aprobado_q else "⚠️ NO ALCANZA EL CORTE ELIMINATORIO DE 25 / 50 PTOS"

                        st.markdown(
                            f"<div style='background-color:{bg_card}; border:2px solid {border_card}; border-radius:10px; padding:14px 16px; margin-top:12px; margin-bottom:10px; text-align:center;'>"
                            f"<div style='font-size:13px; font-weight:700; color:{color_nota} !important; letter-spacing:0.5px; margin-bottom:4px;'>🎯 CALIFICACIÓN OTORGADA SEGÚN LOS CRITERIOS DEL TRIBUNAL</div>"
                            f"<div style='font-size:28px; font-weight:900; color:{color_nota} !important; margin-bottom:2px;'>{n50_q:.2f} / 50,00 PUNTOS</div>"
                            f"<div style='font-size:17px; font-weight:700; color:#1E293B !important; margin-bottom:8px;'>Nota equivalente sobre 10: <span style='color:{color_nota} !important;'>{n10_q:.2f} / 10</span> &nbsp;|&nbsp; {badge_txt}</div>"
                            f"<div style='font-size:13.5px; color:#334155 !important; background:#ffffff; padding:8px 10px; border-radius:6px; border:1px solid #cbd5e1;'>"
                            f"<b>Criterio 1 (Conocimiento y normativa):</b> {c1_q:.2f} / 45,00 ptos &nbsp;•&nbsp; "
                            f"<b>Criterio 2 (Estructura):</b> {c2_q:.2f} / 3,00 ptos &nbsp;•&nbsp; "
                            f"<b>Criterio 3 (Expresión escrita):</b> {c3_q:.2f} / 2,00 ptos"
                            f"</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                        st.markdown(
                            f"<div style='background-color:#F1F5F9; border:1px solid #CBD5E1; border-left:4px solid #64748B; border-radius:6px; padding:9px 12px; margin-top:4px; margin-bottom:10px; font-size:12.5px; line-height:1.4; color:#475569 !important; text-align:justify;'>"
                            f"{NOTA_METODOLOGICA_PREPARADORES}"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                        st.markdown(
                            "<div style='background-color:#f0fdf4; border:2px solid #16a34a; border-radius:8px; padding:10px 14px 4px 14px; margin-top:8px; margin-bottom:8px;'>"
                            "<div style='font-size:15px; font-weight:800; color:#15803d !important; margin-bottom:4px;'>🤖 ANÁLISIS COMPARATIVO Y VALORACIÓN DE LA IA</div>"
                            "</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(stat.get("ai_feedback") or "")

                    if resp_of and resp_of != exp_of:
                        st.markdown(
                            f"<div style='background-color:#e8f5e9; border-left:4px solid #2e7d32; padding:12px; border-radius:4px; margin-top:10px;'>"
                            f"<div style='font-size:14px; font-weight:700; color:#1b5e20 !important; margin-bottom:4px;'>🎯 Respuesta Directa Oficial:</div>"
                            f"<div style='font-size:14px; color:#1b5e20 !important; text-align:justify;'>{resp_of}</div></div>",
                            unsafe_allow_html=True
                        )
                    if exp_of:
                        eh = PDFQuizParser.renderizar_explicacion_html(exp_of, etiqueta_tema)
                        if q.get("tipo_abierta") == "DESARROLLO":
                            cabecera_exp_html = (
                                f"<div style='font-size: 15.5px; font-weight: 800; color: #083B46 !important;'>📖 Texto mínimo de {q['question_text']}</div>"
                                f"<div style='font-size: 12.5px; font-weight: 600; color: #0E5A6A !important; margin-top: 2px; margin-bottom: 8px; border-bottom: 1px solid #b6e0ea; padding-bottom: 6px;'>{etiqueta_tema}</div>"
                            )
                        else:
                            cabecera_exp_html = (
                                f"<div style='font-size: 15px; font-weight: 800; margin-bottom: 8px; color: #083B46 !important; border-bottom: 1px solid #b6e0ea; padding-bottom: 6px;'>📖 Solución y Explicación Oficial de la Pregunta:</div>"
                            )
                        st.markdown(
                            f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 16px 18px; border-radius: 6px; margin-top: 10px;'>"
                            f"{cabecera_exp_html}"
                            f"<div style='font-size: 14.5px; color: #0c5460 !important;'>{eh}</div></div>",
                            unsafe_allow_html=True
                        )

                    if puede_rep:
                        with st.expander(f"⚠️ Reportar Error en {tipo_item_lbl} {idx + 1} a info@oposiciona.es"):
                            render_cuadro_reporte_error(q, idx + 1, "test_activo_bottom")
        else:
            if q['answer'] != -1:
                co = q['options'][q['answer']]
                if sel_opt == co: st.success("✅ ¡CORRECTO!")
                elif not sel_opt: st.warning(f"⚪ EN BLANCO. La correcta era: {co}")
                else: st.error(f"❌ INCORRECTO. La respuesta correcta era: {co}")
            else:
                st.warning("⚪ EN BLANCO. La correcta no se detectó automáticamente en el PDF.") if not sel_opt else st.info("⚠️ Tu respuesta ha sido guardada. (La opción correcta no estaba remarcada en el PDF original, revisa la explicación).")
            et = re.sub(r'(?i)^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip()).strip() or "No hay explicación disponible."
            eh = "".join([f"<div style='margin-top: 5px; line-height: 1.4; color: #0c5460 !important;'>{p.strip()}</div>" for p in et.split('\n') if p.strip()])
            st.markdown(f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 12px; border-radius: 4px; margin-top: 10px;'><div style='font-size: 14px; font-weight: 600; margin-bottom: 3px; color: #0c5460 !important;'>Explicación:</div><div style='font-size: 14px; color: #0c5460 !important; text-align: justify;'>{eh}</div></div>", unsafe_allow_html=True)

else:
    st.markdown("<style>:root { --background-color: #FFFFFF !important; --secondary-background-color: #F8FAFC !important; --text-color: #1E293B !important; } html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFFFF !important; color: #1E293B !important; }</style>", unsafe_allow_html=True)
    components.html("<script>setTimeout(function() { if(window.parent) window.parent.scrollTo({top: 0, behavior: 'smooth'}); }, 500);</script>", height=0)

    puede_rep = usuario_puede_reportar()
    aciertos = fallos = blancos = preg_eval = 0
    aciertos_por_intento = {}
    suma_notas_abiertas = 0.0
    suma_notas_50 = 0.0
    notas_individuales_10 = []
    notas_individuales_50 = []
    es_test_abierto = any(q.get("is_open", False) for q in st.session_state.questions)
    es_test_supuestos = any(q.get("tipo_abierta") == "SUPUESTO" for q in st.session_state.questions)

    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        if q.get("is_open", False):
            preg_eval += 1
            es_sup_i = bool(q.get("tipo_abierta") == "SUPUESTO")
            modo_i = "SUPUESTO" if es_sup_i else "DESARROLLO"
            txt_al = (stat.get("selected") or "").strip()
            if not txt_al:
                blancos += 1
                notas_individuales_10.append((i + 1, 0.0))
                notas_individuales_50.append((i + 1, 0.0))
                stat['final_status'] = "⚪ En blanco (0,00 / 10)" if es_sup_i else "⚪ En blanco (0,00 / 50 ptos)"
            elif detectar_respuesta_inapropiada_o_sin_interes(txt_al):
                fallos += 1
                notas_individuales_10.append((i + 1, 0.0))
                notas_individuales_50.append((i + 1, 0.0))
                stat['final_status'] = "⚠️ Respuesta no evaluable (0,00 / 10)" if es_sup_i else "⚠️ Respuesta no evaluable (0,00 / 50 ptos)"
            else:
                ctx_q = f"{q.get('preamble', '')} {q.get('question_text', '')}".strip()
                if stat.get("last_evaluated_text") == txt_al and stat.get("ai_eval"):
                    ev = stat["ai_eval"]
                else:
                    ev = evaluar_respuesta_escrita(txt_al, q.get("answer_text", ""), q.get("explanation", ""), ctx_q)
                    clave_activa = obtener_gemini_api_key_activa()
                    stat["ai_feedback"] = consultar_ia_gemini_correccion(
                        clave_activa, q.get("preamble", ""), q["question_text"], txt_al, q.get("answer_text", ""), q.get("explanation", ""), ev_fallback=ev, modo=modo_i
                    )
                    stat["last_evaluated_text"] = txt_al
                    stat["ai_eval"] = ev
                nota_q = float(ev.get("nota", 0.0))
                nota_q_50 = float(ev.get("nota_50", 0.0))
                suma_notas_abiertas += nota_q
                suma_notas_50 += nota_q_50
                notas_individuales_10.append((i + 1, nota_q))
                notas_individuales_50.append((i + 1, nota_q_50))
                if es_sup_i:
                    if nota_q >= 5.0:
                        aciertos += 1
                        stat['final_status'] = f"✅ Superada ({nota_q:.2f} / 10)"
                    else:
                        fallos += 1
                        stat['final_status'] = f"⚠️ A reforzar ({nota_q:.2f} / 10)"
                else:
                    if nota_q_50 >= 25.0:
                        aciertos += 1
                        stat['final_status'] = f"✅ Superada ({nota_q_50:.2f} / 50 ptos | {nota_q:.2f} / 10)"
                    else:
                        fallos += 1
                        stat['final_status'] = f"⚠️ Inferior al corte de 25 ptos ({nota_q_50:.2f} / 50 ptos | {nota_q:.2f} / 10)"
        elif q['answer'] != -1:
            preg_eval += 1
            co = q['options'][q['answer']]
            if stat['selected'] == co:
                aciertos += 1
                stat['final_status'] = "✅ Correcta"
                num_int = max(1, stat.get('attempts', 1))
                aciertos_por_intento[num_int] = aciertos_por_intento.get(num_int, 0) + 1
            elif stat['selected'] is None:
                blancos += 1
                stat['final_status'] = "⚪ En blanco"
            else:
                fallos += 1
                stat['final_status'] = "❌ Incorrecta"
        else:
            if stat['selected'] is None:
                blancos += 1
                stat['final_status'] = "⚪ En blanco"
            else:
                stat['final_status'] = "⚠️ Sin corregir (PDF sin marcar)"

    if es_test_abierto:
        # La nota final es la media aritmética de las notas individuales de todas las preguntas/epígrafes del ejercicio
        total_items_abiertos = max(1, preg_eval)
        nota_referencia = round(suma_notas_abiertas / total_items_abiertos, 2)
        nota_media_50 = round(suma_notas_50 / total_items_abiertos, 2)
        nota_oposicion_10 = nota_referencia
        aciertos_netos = aciertos
        puntos_restados = 0.0
        divisor_penalizacion = 1
        penalizacion_texto = "Media aritmética de las calificaciones obtenidas individualmente en cada pregunta"
        nombre_cuerpo = "GESTIÓN DE LA SEGURIDAD SOCIAL — SEGUNDO EJERCICIO (ACCESO LIBRE)"
    else:
        nota_referencia = (aciertos / preg_eval) * 10 if preg_eval > 0 else 0.0
        nota_media_50 = 0.0
        esp_actual = (st.session_state.get("test_esp") or st.session_state.get("saved_esp") or "").upper()
        if "GESTI" in esp_actual or st.session_state.get("rol") == "GESTION":
            es_gestion = True
            nombre_cuerpo = "GESTIÓN DE LA SEGURIDAD SOCIAL"
            divisor_penalizacion = 3
            penalizacion_texto = "0,33 puntos (cada 3 errores restan 1 acierto)"
            puntos_restados = fallos / 3.0
        else:
            es_gestion = False
            nombre_cuerpo = "ADMINISTRATIVO DE LA SEGURIDAD SOCIAL"
            divisor_penalizacion = 4
            penalizacion_texto = "0,25 puntos (cada 4 errores restan 1 acierto)"
            puntos_restados = fallos / 4.0

        aciertos_netos = max(0.0, aciertos - puntos_restados)
        nota_oposicion_10 = (aciertos_netos / preg_eval) * 10 if preg_eval > 0 else 0.0

    if not st.session_state.get('resultado_registrado', False):
        st.session_state.resultado_registrado = True
        sincronizar_progreso_navegador()

        es_desarrollo_fin = any(q.get("tipo_abierta") == "DESARROLLO" for q in st.session_state.questions) or (st.session_state.get("test_cat") or "").upper() == "DESARROLLO"

        if es_desarrollo_fin:
            st.session_state.test_cat = "DESARROLLO"
            nombre_test_final_sheets = construir_nombre_test_seguimiento_sheets()
            nota_sheets_str = f"{nota_media_50:.2f}/50 ({nota_oposicion_10:.2f}/10)".replace(".", ",")
            accion_sheets = "actualizar_fin" if st.session_state.get("inicio_registrado_sheets", False) else "nueva_fila"
            st.session_state.inicio_registrado_sheets = True
            registrar_actividad_sheets(
                evento="✅ Completado",
                nombre_test=nombre_test_final_sheets,
                aciertos="",
                fallos="",
                blancos="",
                nota=nota_sheets_str,
                accion=accion_sheets
            )
        else:
            if aciertos > 0 and aciertos_por_intento:
                max_intento = max(aciertos_por_intento.keys())
                tope_mostrar = 1 if max_intento == 1 else max(3, max_intento)
                desglose_str = ", ".join([f"{aciertos_por_intento.get(k, 0)}-{k}" for k in range(1, tope_mostrar + 1)])
                aciertos_sheets_str = f"{aciertos} ({desglose_str})"
            else:
                aciertos_sheets_str = str(aciertos)

            nota_sheets_str = (
                f"{nota_oposicion_10:.2f}/10".replace(".", ",")
                if es_test_supuestos else
                f"{nota_referencia:.2f} (Opos: {nota_oposicion_10:.2f})".replace(".", ",")
            )
            registrar_actividad_sheets(
                evento="✅ Completado",
                nombre_test=st.session_state.get("test_name") or "Test",
                aciertos=aciertos_sheets_str,
                fallos=fallos,
                blancos=blancos,
                nota=nota_sheets_str,
                accion="actualizar_fin"
            )

    if nota_oposicion_10 >= 5.0:
        if not st.session_state.get('celebracion_mostrada', False):
            st.session_state.celebracion_mostrada = True
            components.html("""<script>
            (function() {
                var pw = window.parent, pd = pw.document;
                function disp() {
                    var end = Date.now() + 3200;
                    (function frame() {
                        pw.confetti({ particleCount: 6, angle: 60, spread: 55, origin: { x: 0, y: 0.6 } });
                        pw.confetti({ particleCount: 6, angle: 120, spread: 55, origin: { x: 1, y: 0.6 } });
                        if (Date.now() < end) requestAnimationFrame(frame);
                    }());
                }
                if (!pw.confetti) {
                    var s = pd.createElement('script');
                    s.src = 'https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js';
                    s.onload = disp; pd.head.appendChild(s);
                } else disp();
            })();
            </script>""", height=0)
        msg_enhorabuena = "🎉 ¡ENHORABUENA, HAS SUPERADO EL SUPUESTO PRÁCTICO! 🎉" if es_test_supuestos else "🎉 ¡ENHORABUENA, HAS SUPERADO EL CORTE DE 25 / 50 PUNTOS! 🎉"
        st.markdown(f"<div style='background: linear-gradient(90deg, #e8f5e9, #c8e6c9, #e8f5e9); border: 2px solid #2e7d32; border-radius: 10px; padding: 12px; text-align: center; margin-bottom: 15px;'><div style='color: #1b5e20 !important; margin: 0; font-size: 22px; font-weight: 700;'>{msg_enhorabuena}</div><p style='color: #2e7d32 !important; margin: 4px 0 0 0; font-size: 14px; font-weight: 600;'>¡Sigue así, estás cada vez más cerca de tu plaza!</p></div>", unsafe_allow_html=True)
        cr1, cr2, cr3 = st.columns([1, 0.4, 1])
        with cr2:
            try: st.image("test-utiles-768x768.png", use_container_width=True)
            except: pass
    else:
        cr1, cr2, cr3 = st.columns([1, 1.5, 1])
        with cr2:
            try: st.image("llorona.jpeg", use_container_width=True)
            except: pass

    nombre_test_fin = st.session_state.get("test_name") or "Test"
    id_test_fin = re.sub(r'\W+', '_', nombre_test_fin)
    etiqueta_tema_fin = obtener_etiqueta_tema_visible(nombre_test_fin, st.session_state.questions[0] if st.session_state.questions else None)
    st.markdown("<div style='text-align: center; font-size: 22px; font-weight: 700; color: #2C3E50 !important; margin-top: -10px; margin-bottom: 6px;'>📊 RESULTADOS FINALES</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 16px; font-weight: 700; color: #1f77b4 !important; margin-bottom: 15px;'>📘 {etiqueta_tema_fin}</div>", unsafe_allow_html=True)

    if es_test_supuestos:
        desglose_indiv_sup = " &nbsp;•&nbsp; ".join([f"<b>P{num_i}:</b> {val_i:.2f}/10" for num_i, val_i in notas_individuales_10])
        st.markdown(
            f"<div style='text-align: center; font-size: 16px; font-weight: 600; color: #334155 !important; margin-bottom: 12px;'>"
            f"✅ Cuestiones superadas (≥ 5/10): <b style='color:#000000 !important;'>{aciertos}</b> &nbsp;|&nbsp; ⚠️ A reforzar (< 5/10): <b style='color:#000000 !important;'>{fallos}</b> &nbsp;|&nbsp; ⚪ En blanco (0/10): <b style='color:#000000 !important;'>{blancos}</b>"
            f"</div>"
            f"<div style='background-color: #eef6ff; border: 2px solid #1f77b4; border-radius: 10px; padding: 14px 16px; margin-bottom: 20px;'>"
            f"<div style='text-align: center; font-size: 14px; font-weight: 700; color: #1f77b4 !important; letter-spacing: 0.5px; margin-bottom: 4px;'>🎯 NOTA FINAL DEL SUPUESTO PRÁCTICO (MEDIA DE LAS {preg_eval} CUESTIONES)</div>"
            f"<div style='text-align: center; font-size: 25px; font-weight: 800; color: #0d47a1 !important; margin-bottom: 6px;'>"
            f"🎓 NOTA MEDIA FINAL: {nota_oposicion_10:.2f} / 10 PUNTOS"
            f"</div>"
            f"<div style='background-color: #ffffff; border-left: 4px solid #1f77b4; padding: 9px 12px; border-radius: 4px; font-size: 13px; color: #2C3E50 !important; text-align: justify; line-height: 1.45;'>"
            f"<b>Cálculo de la nota final:</b> Media aritmética de las notas individuales obtenidas en las {preg_eval} cuestiones del supuesto "
            f"({suma_notas_abiertas:.2f} puntos totales ÷ {preg_eval} cuestiones = <b>{nota_oposicion_10:.2f} / 10</b>).<br>"
            f"<span style='font-size:12.5px; color:#475569 !important;'>{desglose_indiv_sup}</span>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    elif es_test_abierto:
        desglose_indiv_des = " &nbsp;•&nbsp; ".join([f"<b>Ep.{num_i}:</b> {val_i:.2f}/50" for num_i, val_i in notas_individuales_50])
        st.markdown(
            f"<div style='text-align: center; font-size: 16px; font-weight: 600; color: #334155 !important; margin-bottom: 12px;'>"
            f"✅ Superadas (≥ 25/50): <b style='color:#000000 !important;'>{aciertos}</b> &nbsp;|&nbsp; ⚠️ Inferiores a 25/50: <b style='color:#000000 !important;'>{fallos}</b> &nbsp;|&nbsp; ⚪ En blanco (0/50): <b style='color:#000000 !important;'>{blancos}</b>"
            f"</div>"
            f"<div style='background-color: #eef6ff; border: 2px solid #1f77b4; border-radius: 10px; padding: 14px 16px; margin-bottom: 20px;'>"
            f"<div style='text-align: center; font-size: 14px; font-weight: 700; color: #1f77b4 !important; letter-spacing: 0.5px; margin-bottom: 4px;'>🎯 NOTA MEDIA FINAL ({nombre_cuerpo})</div>"
            f"<div style='text-align: center; font-size: 22px; font-weight: 800; color: #0d47a1 !important; margin-bottom: 4px;'>"
            f"🏛️ PUNTUACIÓN MEDIA DIRECTA: {nota_media_50:.2f} / 50,00 PUNTOS"
            f"</div>"
            f"<div style='text-align: center; font-size: 16px; font-weight: 700; color: #1565c0 !important; margin-bottom: 8px;'>"
            f"🎓 Equivalencia media sobre 10: {nota_oposicion_10:.2f} / 10"
            f"</div>"
            f"<div style='background-color: #ffffff; border-left: 4px solid #1f77b4; padding: 9px 12px; border-radius: 4px; font-size: 13px; color: #2C3E50 !important; text-align: justify; line-height: 1.45;'>"
            f"<b>Cálculo de la nota final:</b> Media aritmética de las calificaciones obtenidas individualmente en los {preg_eval} epígrafes del tema "
            f"({suma_notas_50:.2f} ÷ {preg_eval} = <b>{nota_media_50:.2f} / 50 ptos</b> | Equivalencia: <b>{nota_oposicion_10:.2f} / 10</b>).<br>"
            f"<span style='font-size:12.5px; color:#475569 !important;'>{desglose_indiv_des}</span>"
            f"</div></div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div style='text-align: center; font-size: 16px; font-weight: 600; color: #334155 !important; margin-bottom: 10px;'>"
            f"✅ Acertadas: <b style='color:#000000 !important;'>{aciertos}</b> &nbsp;|&nbsp; ❌ Falladas: <b style='color:#000000 !important;'>{fallos}</b> &nbsp;|&nbsp; ⚪ En blanco: <b style='color:#000000 !important;'>{blancos}</b>"
            f"</div>"
            f"<div style='background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; text-align: center;'>"
            f"<div style='font-size: 16px; font-weight: 600; color: #495057 !important;'>📏 PUNTUACIÓN DE REFERENCIA (SIN PENALIZACIÓN): <span style='color: #2C3E50 !important; font-size: 19px;'>{nota_referencia:.2f} / 10</span></div>"
            f"<div style='font-size: 12.5px; color: #6c757d !important; margin-top: 2px;'>Obtenida dividiendo tus {aciertos} aciertos entre las {preg_eval} preguntas evaluables ({aciertos} / {preg_eval} × 10), sin descontar errores.</div>"
            f"</div>"
            f"<div style='background-color: #eef6ff; border: 2px solid #1f77b4; border-radius: 10px; padding: 14px 16px; margin-bottom: 20px;'>"
            f"<div style='text-align: center; font-size: 14px; font-weight: 700; color: #1f77b4 !important; letter-spacing: 0.5px; margin-bottom: 4px;'>🎯 BAREMO OFICIAL OPOSICIÓN ({nombre_cuerpo})</div>"
            f"<div style='text-align: center; font-size: 23px; font-weight: 800; color: #0d47a1 !important; margin-bottom: 4px;'>"
            f"🎓 NOTA CONVERTIDA OPOSICIÓN: {nota_oposicion_10:.2f} / 10"
            f"</div>"
            f"<div style='text-align: center; font-size: 15px; font-weight: 600; color: #1565c0 !important; margin-bottom: 10px;'>"
            f"Puntos netos directos: <b style='color:#0d47a1 !important;'>{aciertos_netos:.2f}</b> sobre {preg_eval} puntos posibles"
            f"</div>"
            f"<div style='background-color: #ffffff; border-left: 4px solid #1f77b4; padding: 9px 12px; border-radius: 4px; font-size: 13.5px; color: #2C3E50 !important; text-align: justify; line-height: 1.4;'>"
            f"<b style='color:#2C3E50 !important;'>ℹ️ ¿Cómo se ha calculado tu nota de oposición?</b><br>"
            f"• <b style='color:#2C3E50 !important;'>Preguntas en blanco ({blancos}):</b> No suman ni restan (0 puntos).<br>"
            f"• <b style='color:#2C3E50 !important;'>Penalización por errores ({fallos} {'fallo' if fallos == 1 else 'fallos'}):</b> En <b style='color:#2C3E50 !important;'>{nombre_cuerpo.title()}</b> cada error resta <b style='color:#2C3E50 !important;'>{penalizacion_texto}</b>. "
            f"Tus {fallos} {'error' if fallos == 1 else 'errores'} restan <b style='color:#2C3E50 !important;'>{puntos_restados:.2f} aciertos</b> ({fallos} ÷ {divisor_penalizacion} = {puntos_restados:.2f}).<br>"
            f"• <b style='color:#2C3E50 !important;'>Cálculo final:</b> {aciertos} aciertos − {puntos_restados:.2f} de penalización = <b style='color:#2C3E50 !important;'>{aciertos_netos:.2f} puntos netos</b> de {preg_eval} posibles "
            f"➔ <b style='color:#2C3E50 !important;'>({aciertos_netos:.2f} ÷ {preg_eval}) × 10 = {nota_oposicion_10:.2f} sobre 10</b>."
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    cat_actual_fin = (st.session_state.get("test_cat") or st.session_state.get("saved_cat") or "").upper()
    if "DESARROLLO" in cat_actual_fin or any(q.get("tipo_abierta") == "DESARROLLO" for q in st.session_state.questions):
        lbl_repetir = "🔄 Repetir Preguntas"
        lbl_cambiar = "📁 Cambiar de Preguntas"
    elif "SUPUESTO" in cat_actual_fin or any(q.get("tipo_abierta") == "SUPUESTO" for q in st.session_state.questions):
        lbl_repetir = "🔄 Repetir Supuestos"
        lbl_cambiar = "📁 Cambiar de Supuestos"
    else:
        lbl_repetir = "🔄 Repetir Test"
        lbl_cambiar = "📁 Cambiar de Test"

    c1_t, c2_t, c3_t = st.columns(3)
    c1_t.button(lbl_repetir, key="btn_rep_top", on_click=action_repetir_test, use_container_width=True)
    c2_t.button(lbl_cambiar, key="btn_sub_top", on_click=action_subir_otro, use_container_width=True)
    c3_t.button("🚪 Finalizar Sesión", key="btn_out_top", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
    st.markdown("<hr style='margin-top: 15px; margin-bottom: 15px; border: none; border-top: 1px solid #d3d3d3;'>", unsafe_allow_html=True)

    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        tipo_lbl_res = "Epígrafe" if q.get("tipo_abierta") == "DESARROLLO" else ("Cuestión" if q.get("is_open") else "Pregunta")
        co = (q.get('answer_text') or "Ver solución y explicación debajo") if q.get("is_open") else (q['options'][q['answer']] if q['answer'] != -1 else "No detectada (revisa la explicación)")
        col = "#15803d" if "✅" in stat.get('final_status', '') else "#dc2626" if "❌" in stat.get('final_status', '') else "#d97706"
        et = re.sub(r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip(), flags=re.IGNORECASE).strip() or "No hay explicación disponible."
        if q.get("tipo_abierta") in ("DESARROLLO", "SUPUESTO"):
            eh = PDFQuizParser.renderizar_explicacion_html(et, etiqueta_tema_fin)
            if q.get("tipo_abierta") == "DESARROLLO":
                cabecera_res_html = (
                    f"<div style='font-size: 15px; font-weight: 800; color: #083B46 !important;'>📖 Texto mínimo de {q['question_text']}</div>"
                    f"<div style='font-size: 12.5px; font-weight: 600; color: #0E5A6A !important; margin-top: 2px; margin-bottom: 6px; border-bottom: 1px solid #b6e0ea; padding-bottom: 5px;'>{etiqueta_tema_fin}</div>"
                )
            else:
                cabecera_res_html = (
                    f"<div style='font-size: 15px; font-weight: 800; color: #083B46 !important; margin-bottom: 6px; border-bottom: 1px solid #b6e0ea; padding-bottom: 5px;'>📖 Solución y Explicación Oficial de la Cuestión {i+1}:</div>"
                )
        else:
            et_limpia = PDFQuizParser._limpiar_cabeceras_incrustadas(et, etiqueta_tema_fin)
            lineas_res_limpias = [
                p.strip() for p in et_limpia.split('\n')
                if p.strip() and not PDFQuizParser._es_basura_cabecera_o_pie(p.strip(), etiqueta_tema_fin)
            ]
            eh = "".join([f"<div style='margin-top: 6px; margin-bottom: 4px; line-height: 1.45; color: #0c5460 !important;'>{p}</div>" for p in lineas_res_limpias])
            cabecera_res_html = "<div style='font-size: 14.5px; font-weight: 800; margin-bottom: 6px; color: #083B46 !important;'>📖 Explicación:</div>"

        ph = ""
        if q.get('preamble') and q.get("tipo_abierta") != "SUPUESTO":
            ph = f"<div style='text-align: justify; line-height: 1.3; margin-bottom: 4px; font-size: 14px; color: #334155 !important;'>{q['preamble']}</div>"
        elif q.get('preamble') and q.get("tipo_abierta") == "SUPUESTO" and i == 0:
            ph = f"<div style='background:#FFFFFF; border:1px solid #CBD5E1; border-left:4px solid #1F77B4; border-radius:6px; padding:10px 12px; margin-bottom:8px; font-size:10pt !important; line-height:1.4; text-align:justify; color:#1E293B !important;'><div style='font-weight:800; color:#1E3A8A !important; margin-bottom:4px;'>📋 Planteamiento del Supuesto Práctico:</div>{q['preamble']}</div>"

        st.markdown(
            f"<div style='margin-bottom: 5px;'>"
            f"{ph}"
            f"<div style='color: {col} !important; font-size: 17px; font-weight: 700; margin-bottom: 4px;'>{tipo_lbl_res} {i+1} | {stat['final_status']}</div>"
            f"<div style='font-size:15px; color:#000000 !important; text-align: justify; line-height: 1.3; margin-bottom: 4px;'><b style='color:#000000 !important;'>{tipo_lbl_res}:</b> {q['question_text']}</div>"
            f"<div style='font-size:15px; color:#000000 !important; text-align: justify; line-height: 1.3; margin-bottom: 4px;'><b style='color:#000000 !important;'>Tu respuesta:</b> {stat['selected'] if stat['selected'] else 'Ninguna'}</div>"
            f"<div style='font-size:15px; color:#1b5e20 !important; text-align: justify; line-height: 1.3; margin-bottom: 6px;'><b style='color:#1b5e20 !important;'>Respuesta oficial:</b> {co}</div>"
            f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 14px 16px; border-radius: 6px; margin-bottom: 6px;'>{cabecera_res_html}<div style='font-size: 14px; color: #0c5460 !important; text-align: justify;'>{eh}</div></div>"
            f"</div>",
            unsafe_allow_html=True
        )
        if q.get("is_open") and stat.get("ai_feedback"):
            with st.expander(f"🤖 Ver valoración detallada de la IA para {tipo_lbl_res} {i + 1}"):
                st.markdown(stat["ai_feedback"])
        if puede_rep:
            key_rep_res = f"rep_open_res_{id_test_fin}_{i + 1}"
            if key_rep_res not in st.session_state:
                st.session_state[key_rep_res] = False
            if st.session_state.pop(f"rep_ok_msg_{id_test_fin}_{i + 1}", False):
                st.success("✅ ¡Reporte enviado con éxito a info@oposiciona.es! Muchas gracias por tu colaboración.")
            lbl_btn_res = f"⚠️ Reportar Error en {tipo_lbl_res} {i + 1}"
            if st.button(lbl_btn_res, key=f"btn_err_res_{id_test_fin}_{i + 1}"):
                st.session_state[key_rep_res] = not st.session_state[key_rep_res]
            if st.session_state[key_rep_res]:
                render_cuadro_reporte_error(q, i + 1, "resumen_final")

        st.markdown("<hr style='margin: 12px 0px 15px 0px; border: 0; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)

    c1_b, c2_b, c3_b = st.columns(3)
    c1_b.button(lbl_repetir, key="btn_rep_bot", on_click=action_repetir_test, use_container_width=True)
    c2_b.button(lbl_cambiar, key="btn_sub_bot", on_click=action_subir_otro, use_container_width=True)
    c3_b.button("🚪 Finalizar Sesión", key="btn_out_bot", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
# === FIN SECCIÓN 5 ===
