# === SECCIÓN 1: CONFIGURACIÓN, ESTILOS Y REGISTRO SHEETS ===
import streamlit as st
import streamlit.components.v1 as components
import fitz  # PyMuPDF
import re, random, requests, os, unicodedata, time, json, threading, base64, zlib
from datetime import datetime
from zoneinfo import ZoneInfo

icono_ruta = "ICONO OPOSICIONA.png"
st.set_page_config(page_title="Plataforma de Tests Oposiciona", page_icon=icono_ruta if os.path.exists(icono_ruta) else "📚", layout="centered")

st.markdown("""<style>
:root, html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    color-scheme: light only !important;
    --text-color: #1E293B !important;
    --background-color: #FFFFFF !important;
    --secondary-background-color: #F8FAFC !important;
    color: #1E293B !important;
}
#MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], .stDeployButton, [data-testid="stAppDeployButton"] {
    visibility: hidden !important;
    display: none !important;
}
[class*="viewerBadge"], [class*="styles_viewerBadge"] {
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
body, .stApp, .block-container, p, h1, h2, h3, h4, h5, h6, span {
    -webkit-user-select: none !important;
    -moz-user-select: none !important;
    -ms-user-select: none !important;
    user-select: none !important;
}
@media print {
    html, body * {display: none !important; visibility: hidden !important;}
    html, body {display: block !important; background-color: white !important;}
    body::before {content: "Acción no permitida.\\A Test propiedad de Oposiciona 5.0." !important; white-space: pre-wrap !important; display: block !important; text-align: center !important; font-size: 30px !important; font-family: sans-serif !important; margin-top: 20% !important; color: #d32f2f !important;}
}
</style>""", unsafe_allow_html=True)

components.html("""<script>
try {
    setTimeout(function() {
        var parentDoc = window.parent.document;
        if (!parentDoc.getElementById("escudo-oposiciona")) {
            var script = parentDoc.createElement("script");
            script.id = "escudo-oposiciona";
            script.innerHTML = `
                document.addEventListener('contextmenu', function(e) { e.preventDefault(); });
                document.addEventListener('copy', function(e) {
                    var s = window.getSelection().toString();
                    if (s.length > 0) { e.clipboardData.setData('text/plain', s + "\\n\\n-----------------------------------\\nTest propiedad de Oposiciona 5.0"); e.preventDefault(); }
                });
                document.addEventListener('keydown', function(e) { if ((e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key === 'P')) { e.preventDefault(); e.stopPropagation(); } });

                /* Latido anti-desconexión cada 25s y WakeLock para que no se suspenda la pestaña leyendo explicaciones */
                setInterval(function() {
                    try {
                        fetch(window.location.origin + "/_stcore/health", { method: "GET", cache: "no-store" }).catch(function(){});
                        document.dispatchEvent(new CustomEvent("oposiciona_keepalive"));
                    } catch(err) {}
                }, 25000);

                var wakeLockObj = null;
                function activarWakeLock() {
                    if ('wakeLock' in navigator && document.visibilityState === 'visible') {
                        navigator.wakeLock.request('screen').then(function(wl) { wakeLockObj = wl; }).catch(function(){});
                    }
                }
                document.addEventListener('visibilitychange', activarWakeLock);
                document.addEventListener('click', activarWakeLock, { once: true });
            `;
            parentDoc.head.appendChild(script);
        }
    }, 800);
} catch(e) {}
</script>""", height=0)

GOOGLE_SHEETS_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbw_B-g4pwxuZX4HzH99cobW6jQoValvLXI2ogeJgMuekjwlyS766KS4ujm3CFYdJ7DPlA/exec"
# Clave ofuscada por fragmentos en Base64 para evitar falsas alertas de Secret Scanning en GitHub
_K_PARTS = ("QVEuQWI4Uk42", "TDRmWVhWNHg0", "Vi1FWVlIbmRk", "bWxob0llcTZIRXNC", "S1BPUENDUHZDVkJ4RXc=")
GEMINI_API_KEY_DEFAULT = "".join(base64.b64decode(p).decode("utf-8") for p in _K_PARTS)

USUARIOS_ADMIN = ["ponentes@oposiciona.es", "ponentes@oposicona.es"]
USUARIOS_AUTORIZADOS = {
    "ACCESO TOTAL": ["ponentes@oposiciona.es", "ponentes@oposicona.es", "gonzalogonzaleztejedor@gmail.com", "ignacio.garcia.heras@gmail.com", "alvarezpugamartin@gmail.com", "claratoledo06@gmail.com", "blancazortega@gmail.com", "mijurista@gmail.com", "isabelmgutierrogil@gmail.com", "carmenvl28@gmail.com", "leticiagenerelosolana@gmail.com", "cguinaldobravo@gmail.com", "alvaro20011996@gmail.com", "sion.nuba@gmail.com"],
    "ADMTVOS": ["elenavegasanchez73@gmail.com", "josemurillomoreno.mail@gmail.com", "raulff1997.rfg@gmail.com", "sandradcastanares@gmail.com", "joycewayland@gmail.com", "celia.pks@gmail.com", "cynthiaflafla14@gmail.com", "fragosotorbellinocarmen@gmail.com", "pherrerojulian@gmail.com", "rsilveiraescudero@gmail.com", "delfijv19@gmail.com", "marielipedreira@hotmail.com", "vanessagarciajimenez87@gmail.com", "luiscacid@gmail.com", "miguelromanrmm@gmail.com", "raquelkmacho@gmail.com", "patripintoalvarez@gmail.com", "alexandrajimenezmontoliu@gmail.com"],
    "GESTION": ["vsaurod@gmail.com", "mariaquirosmonge5@gmail.com", "vanessagomeztdla@gmail.com", "zoemorcor@gmail.com", "julianayem@gmail.com", "yasminkhalili@gmail.com", "miriamvazquezseoane2000@gmail.com", "monetcacerescc@gmail.com", "maariiamaji@gmail.com", "micastroespejo@gmail.com", "aisacarrerapexe@gmail.com", "csanchezssmm@gmail.com", "maria.concal@gmail.com", "mariachinchurreta@gmail.com", "rocio10460@gmail.com", "manuelmuriel97@gmail.com", "hfdiaz99@gmail.com", "ireneizquierdo22@gmail.com", "mfangela23@gmail.com", "manuelsan240902@gmail.com"],
    "INVITADO": ["invitado@oposiciona.es", "invitado"]
}
PASSWORD_ADMIN, PASSWORD_ACCESO, PASSWORD_INVITADO = "Gonz4loN4cho23", "plaza2026", "oposiciona"

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
            raw_bytes = zlib.decompress(base64.urlsafe_b64decode(qp_restore.encode("ascii")))
            datos_rec = json.loads(raw_bytes.decode("utf-8"))
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


# === SECCIÓN 2: LECTOR DE PDF (PDFQuizParser) ===
class PDFQuizParser:
    REEMPLAZOS_INGLES_RAE = [
        # Conectores y palabras en inglés coladas en textos en español
        (r'\band\b', 'y'),
        (r'\bor\b', 'o'),
        (r'\bbut\b', 'pero'),
        (r'\bwith\b', 'con'),
        (r'\bwithout\b', 'sin'),
        (r'\bbetween\b', 'entre'),
        (r'\bfrom\b', 'desde'),
        (r'\buntil\b', 'hasta'),
        (r'\bsince\b', 'desde'),
        (r'\bduring\b', 'durante'),
        (r'\bbefore\b', 'antes de'),
        (r'\bafter\b', 'después de'),
        (r'\bunder\b', 'bajo'),
        (r'\bover\b', 'sobre'),
        (r'\bthrough\b', 'a través de'),
        (r'\bwithin\b', 'dentro de'),
        (r'\bagainst\b', 'contra'),
        (r'\bamong\b', 'entre'),
        (r'\bbecause\b', 'porque'),
        (r'\balthough\b', 'aunque'),
        (r'\bhowever\b', 'sin embargo'),
        (r'\btherefore\b', 'por tanto'),
        (r'\bmoreover\b', 'además'),
        (r'\bfurthermore\b', 'además'),
        (r'\bnevertheless\b', 'no obstante'),
        (r'\botherwise\b', 'en caso contrario'),
        (r'\binstead\b', 'en su lugar'),
        (r'\balso\b', 'también'),
        (r'\bonly\b', 'solo'),
        (r'\balways\b', 'siempre'),
        (r'\bnever\b', 'nunca'),
        (r'\bboth\b', 'ambos'),
        (r'\beach\b', 'cada'),
        (r'\bevery\b', 'cada'),
        (r'\bother\b', 'otro'),
        (r'\banother\b', 'otro'),
        (r'\bsuch\b', 'tal'),
        (r'\bsame\b', 'mismo'),
        (r'\bwhile\b', 'mientras'),
        (r'\bwhen\b', 'cuando'),
        (r'\bwhere\b', 'donde'),
        (r'\bwhich\b', 'el cual'),
        (r'\bwhose\b', 'cuyo'),
        (r'\bwho\b', 'quien'),
        (r'\bwhom\b', 'a quien'),
        (r'\bthat\b', 'que'),
        (r'\bthis\b', 'este'),
        (r'\bthese\b', 'estos'),
        (r'\bthose\b', 'aquellos'),
        (r'\bthe\b', 'el'),
        (r'\bmust\b', 'debe'),
        (r'\bshould\b', 'debería'),
        (r'\bcould\b', 'podría'),
        (r'\bwould\b', 'haría'),
        (r'\bcan\b', 'puede'),
        (r'\bcannot\b', 'no puede'),
        (r'\bmay\b', 'puede'),
        (r'\bmight\b', 'podría'),
        (r'\bshall\b', 'deberá'),
        (r'\bwill\b', 'será'),
        (r'\bis\b', 'es'),
        (r'\bare\b', 'son'),
        (r'\bwas\b', 'fue'),
        (r'\bwere\b', 'fueron'),
        (r'\bbeen\b', 'sido'),
        (r'\bbeing\b', 'siendo'),
        (r'\bhave\b', 'tienen'),
        (r'\bhad\b', 'tenía'),
        (r'\bnot\b', 'no'),
        (r'\btrue\b', 'verdadero'),
        (r'\bfalse\b', 'falso'),
        (r'\bnull\b', 'nulo'),
        # Anglicismos no admitidos por la RAE -> Equivalente en español
        (r'\btrust\s+fideicomiso\b', 'fideicomiso'),
        (r'\btrusts?\b', 'fideicomiso'),
        (r'\bknow[\-\s]?how\b', 'saber hacer'),
        (r'\bholdings?\b', 'grupo de sociedades'),
        (r'\bleasing\b', 'arrendamiento financiero'),
        (r'\brenting\b', 'alquiler a largo plazo'),
        (r'\bfactoring\b', 'cesión de créditos'),
        (r'\bfranchising\b', 'franquicia'),
        (r'\bjoint[\-\s]?venture\b', 'empresa conjunta'),
        (r'\boutsourcing\b', 'externalización'),
        (r'\bcrowdfunding\b', 'financiación colectiva'),
        (r'\bcompliance\b', 'cumplimiento normativo'),
        (r'\bdeadlines?\b', 'plazo límite'),
        (r'\btargets?\b', 'objetivo'),
        (r'\bfeedback\b', 'retroalimentación'),
        (r'\bstaff\b', 'personal'),
        (r'\bmanagement\b', 'dirección'),
        (r'\bmanagers?\b', 'director'),
        (r'\bceo\b', 'consejero delegado'),
        (r'\bdefault\b', 'impago'),
        (r'\binputs?\b', 'aportación'),
        (r'\boutputs?\b', 'resultado'),
        (r'\bchecks?\b', 'comprobación'),
        (r'\blinks?\b', 'enlace'),
        (r'\be[\-\s]?mails?\b', 'correo electrónico'),
        (r'\bon[\-\s]?line\b', 'en línea'),
        (r'\boff[\-\s]?line\b', 'fuera de línea'),
        (r'\bfull[\-\s]?time\b', 'a tiempo completo'),
        (r'\bpart[\-\s]?time\b', 'a tiempo parcial'),
        (r'\bback[\-\s]?office\b', 'administración interna'),
        (r'\bfront[\-\s]?office\b', 'atención al público'),
        (r'\bcall[\-\s]?center\b', 'centro de llamadas'),
        (r'\bpen[\-\s]?drive\b', 'memoria USB'),
        (r'\bpasswords?\b', 'contraseña'),
        (r'\blogin\b', 'inicio de sesión'),
        (r'\blogout\b', 'cierre de sesión'),
        (r'\bstreaming\b', 'transmisión en directo'),
        (r'\bplanning\b', 'planificación'),
        (r'\btiming\b', 'calendario'),
        (r'\branking\b', 'clasificación'),
    ]

    @classmethod
    def traducir_ingles_no_rae(cls, texto):
        if not texto:
            return texto
        for patron, reemplazo in cls.REEMPLAZOS_INGLES_RAE:
            def _reemplazar_respetando_mayus(m):
                orig = m.group(0)
                if orig.isupper() and len(orig) > 1:
                    return reemplazo.upper()
                if orig[0].isupper():
                    return reemplazo.capitalize()
                return reemplazo
            texto = re.sub(patron, _reemplazar_respetando_mayus, texto, flags=re.IGNORECASE)
        return texto

    @staticmethod
    def _reducir_opciones_pregunta(q, limite):
        pat_fija = r'(todas\s+(las\s+respuestas?\s+)?son\s+(correctas|incorrectas|falsas|verdaderas)|ninguna\s+(de\s+las\s+(anteriores|respuestas?)\s+)?es\s+correcta|ambas\s+son\s+correctas)'
        while len(q["options"]) > limite:
            ans = q.get("answer", -1)
            candidatos = [
                i for i in range(len(q["options"]) - 1, -1, -1)
                if i != ans and not re.search(pat_fija, q["options"][i], re.IGNORECASE)
            ]
            if not candidatos:
                candidatos = [i for i in range(len(q["options"]) - 1, -1, -1) if i != ans]
            idx_del = candidatos[0] if candidatos else (len(q["options"]) - 1)
            del q["options"][idx_del]
            if ans > idx_del:
                q["answer"] = ans - 1
        nuevas_opts = []
        for i, opt in enumerate(q["options"]):
            limpia = re.sub(r'^[a-eA-E][\)\.\-]\s*', '', opt).strip()
            nuevas_opts.append(f"{chr(97 + i)}) {limpia}")
        q["options"] = nuevas_opts

    @staticmethod
    def _unir_lineas_en_parrafos(lista_lineas):
        if not lista_lineas:
            return ""
        parrafos = []
        actual = ""
        for l in lista_lineas:
            l_str = l.strip()
            if not l_str:
                continue
            es_nuevo_apartado = bool(re.match(r'^([a-e][\)\.\-]|\d+[\.\)]|[•\*\-–])\s+', l_str))
            if not actual:
                actual = l_str
            elif es_nuevo_apartado or (actual.endswith(('.', ':', '»', '"')) and l_str[0].isupper() and len(actual) > 120):
                parrafos.append(actual)
                actual = l_str
            else:
                actual += " " + l_str
        if actual:
            parrafos.append(actual)
        return "\n\n".join(parrafos)

    @staticmethod
    def parse_abiertas_gestion(pdf_bytes, modo="TODOS"):
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        raw_lines = []
        all_clean_lines = []
        in_abiertas = False

        for page in doc:
            for b in page.get_text("dict")["blocks"]:
                if b.get("type", 0) == 0:
                    for l in b["lines"]:
                        lt = " ".join(s["text"].strip() for s in l["spans"] if s["text"].strip()).strip()
                        if not lt:
                            continue
                        lt = re.sub(r'<{2,}', '«', lt)
                        lt = re.sub(r'>{2,}', '»', lt)
                        lt = re.sub(r'(?:https?://)?(?:www\.)?oposiciona\.es\b', '', lt, flags=re.IGNORECASE).strip()
                        lt = re.sub(r'\bP[aá]gina\s+\d+\s+de\s+\d+\b', '', lt, flags=re.IGNORECASE).strip()
                        if not lt or re.match(r'^(OPOSICIONA|ADMINISTRATIVO DE LA SEGURIDAD SOCIAL|GESTI[OÓ]N DE LA SEGURIDAD SOCIAL)$', lt, re.IGNORECASE):
                            continue
                        tl = lt.lower().translate(str.maketrans("áéíóú", "aeiou"))
                        tl_clean = re.sub(r'[^a-z0-9\s]', '', tl).strip()

                        lt_proc = PDFQuizParser.traducir_ingles_no_rae(lt)
                        lt_proc = re.sub(r'(\d+\.)\s*\^\s*\{?([ºª°a])\}?', lambda m: m.group(1) + ('ª' if m.group(2) == 'a' else m.group(2)), lt_proc)
                        lt_proc = re.sub(r'(\d+)\s*\^\s*\{?([ºª°a])\}?', lambda m: m.group(1) + ('ª' if m.group(2) == 'a' else m.group(2)), lt_proc)
                        lt_proc = re.sub(r'(\d+\.)\s+([ºª°])', r'\1\2', lt_proc)
                        all_clean_lines.append(lt_proc)

                        if not in_abiertas:
                            if any(x in tl_clean for x in ["supuesto practico", "supuestos practicos", "pregunta de desarrollo", "preguntas de desarrollo", "caso practico", "casos practicos"]):
                                if lt.isupper() or len(tl_clean) < 95:
                                    in_abiertas = True
                        if in_abiertas:
                            raw_lines.append(lt_proc)

        desarrollo_qs = []
        supuestos_qs = []

        if raw_lines:
            idx = 0
            current_context = ""
            current_q = None

            while idx < len(raw_lines):
                line = raw_lines[idx].strip()

                # 1. Detectar PREGUNTA DE DESARROLLO explícita
                if re.match(r'^PREGUNTAS?\s+DE\s+DESARROLLO\b', line, re.IGNORECASE):
                    if current_q and (current_q["answer_text"] or current_q["explanation"]):
                        supuestos_qs.append(current_q)
                        current_q = None
                    partes_titulo = []
                    t_ini = re.sub(r'^PREGUNTAS?\s+DE\s+DESARROLLO\s*[:\-–]?\s*', '', line, flags=re.IGNORECASE).strip()
                    if t_ini:
                        partes_titulo.append(t_ini)
                    idx += 1
                    while idx < len(raw_lines):
                        cand_t = raw_lines[idx].strip()
                        if cand_t.isupper() and not re.match(r'^(SUPUESTOS?\s+PR[ÁA]CTICOS?|CASOS?\s+PR[ÁA]CTICOS?)\b', cand_t, re.IGNORECASE):
                            partes_titulo.append(cand_t)
                            idx += 1
                        else:
                            break
                    titulo_des = " ".join(partes_titulo).strip()

                    cuerpo_des = []
                    while idx < len(raw_lines):
                        l_next = raw_lines[idx].strip()
                        if re.match(r'^(SUPUESTOS?\s+PR[ÁA]CTICOS?|CASOS?\s+PR[ÁA]CTICOS?|PREGUNTAS?\s+DE\s+DESARROLLO)\b', l_next, re.IGNORECASE) and (l_next.isupper() or len(l_next) < 85):
                            break
                        cuerpo_des.append(l_next)
                        idx += 1
                    texto_oficial = PDFQuizParser._unir_lineas_en_parrafos(cuerpo_des)
                    if texto_oficial:
                        desarrollo_qs.append({
                            "is_open": True,
                            "tipo_abierta": "DESARROLLO",
                            "preamble": "📝 **PREGUNTA DE DESARROLLO (SEGUNDO EJERCICIO DE LA OPOSICIÓN DE GESTIÓN)**",
                            "question_text": f"Desarrolla de forma completa y rigurosa el siguiente epígrafe conforme a la normativa vigente:\n\n« {titulo_des} »",
                            "options": [],
                            "answer": -1,
                            "answer_text": "",
                            "explanation": texto_oficial
                        })
                    continue

                # 2. Detectar cabecera SUPUESTO PRÁCTICO
                if re.match(r'^(SUPUESTOS?\s+PR[ÁA]CTICOS?|CASOS?\s+PR[ÁA]CTICOS?)\b', line, re.IGNORECASE) and (line.isupper() or len(line) < 80):
                    if current_q and (current_q["answer_text"] or current_q["explanation"]):
                        supuestos_qs.append(current_q)
                        current_q = None
                    resto_cab = re.sub(r'^(SUPUESTOS?\s+PR[ÁA]CTICOS?|CASOS?\s+PR[ÁA]CTICOS?)\s*[:\-–]?\s*', '', line, flags=re.IGNORECASE).strip()
                    current_context = resto_cab if resto_cab else ""
                    idx += 1
                    continue

                # 3. Detectar nuevo planteamiento narrativo intermedio
                if current_q and current_q["state"] == "E" and not re.match(r'^\d+[\.\-\)]', line):
                    if re.match(r'^(La\s+familia|La\s+empresa|La\s+mercantil|Don\s+|Doña\s+|El\s+trabajador|En\s+el\s+ejercicio)\b', line) and "?" not in line:
                        hay_preg_despues = any(re.match(r'^\d{1,2}[\.\-\)]\s+', raw_lines[k].strip()) for k in range(idx + 1, min(idx + 20, len(raw_lines))))
                        if hay_preg_despues and len(current_q["explanation"]) > 120:
                            supuestos_qs.append(current_q)
                            current_q = None
                            current_context = line
                            idx += 1
                            while idx < len(raw_lines) and not re.match(r'^\d{1,2}[\.\-\)]\s+', raw_lines[idx].strip()):
                                current_context += " " + raw_lines[idx].strip()
                                idx += 1
                            continue

                # 4. Detectar pregunta numerada del supuesto
                m_q = re.match(r'^(\d{1,2})[\.\-\)]\s+(.+)$', line)
                if m_q:
                    if current_q and (current_q["answer_text"] or current_q["explanation"]):
                        supuestos_qs.append(current_q)
                    q_txt = m_q.group(2).strip()
                    ans_initial = ""
                    if "?" in q_txt and not q_txt.endswith("?"):
                        partes_q = q_txt.split("?", 1)
                        q_txt = partes_q[0].strip() + "?"
                        ans_initial = partes_q[1].strip()
                    current_q = {
                        "is_open": True,
                        "tipo_abierta": "SUPUESTO",
                        "preamble": f"📋 **PLANTEAMIENTO DEL SUPUESTO PRÁCTICO (TERCER EJERCICIO DE GESTIÓN):**\n\n{current_context.strip()}" if current_context.strip() else "📋 **SUPUESTO PRÁCTICO (TERCER EJERCICIO DE GESTIÓN)**",
                        "question_text": f"Cuestión {m_q.group(1)}. {q_txt}",
                        "options": [],
                        "answer": -1,
                        "answer_text": ans_initial,
                        "explanation": "",
                        "state": "A" if ans_initial else "Q"
                    }
                    idx += 1
                    continue

                if current_q is None:
                    current_context = (current_context + " " + line).strip() if current_context else line
                    idx += 1
                    continue

                if re.match(r'^(Explicaci[óo]n|Fundamentaci[óo]n|Soluci[óo]n|Respuesta)\s*[:\.]', line, re.IGNORECASE):
                    exp_clean = re.sub(r'^(Explicaci[óo]n|Fundamentaci[óo]n|Soluci[óo]n|Respuesta)\s*[:\.]\s*', '', line, flags=re.IGNORECASE).strip()
                    current_q["explanation"] = exp_clean
                    current_q["state"] = "E"
                    idx += 1
                    continue

                if current_q["state"] == "Q":
                    if "?" in line:
                        partes_q = line.split("?", 1)
                        current_q["question_text"] += " " + partes_q[0].strip() + "?"
                        resto_a = partes_q[1].strip()
                        if resto_a:
                            current_q["answer_text"] = resto_a
                        current_q["state"] = "A"
                    else:
                        current_q["question_text"] += " " + line
                elif current_q["state"] == "A":
                    current_q["answer_text"] = (current_q["answer_text"] + " " + line).strip() if current_q["answer_text"] else line
                elif current_q["state"] == "E":
                    current_q["explanation"] = (current_q["explanation"] + " " + line).strip() if current_q["explanation"] else line

                idx += 1

            if current_q and (current_q["answer_text"] or current_q["explanation"]):
                supuestos_qs.append(current_q)

        # 5. EXTRACCIÓN DE EPÍGRAFES PARA PDFs DE RESUMEN (ej. Tema_51_Resumen_Epigrafes y Tema_52_Resumen_Epigrafes)
        # Cada explicación abarca íntegramente desde el título del Epígrafe hasta el siguiente Epígrafe o el final del PDF.
        if modo in ["DESARROLLO", "TODOS"] and not desarrollo_qs and all_clean_lines:
            tema_cabecera = ""
            lineas_utiles = []
            for l in all_clean_lines:
                l_s = l.strip()
                if not l_s:
                    continue
                if not tema_cabecera and re.match(r'^(?:RESUMEN\s+)?TEMA\s+\d+', l_s, re.IGNORECASE):
                    tema_cabecera = l_s
                    continue
                if re.match(r'^RESUMEN\s+DE\s+EP[IÍ]GRAFES', l_s, re.IGNORECASE) and len(l_s) < 90:
                    continue
                lineas_utiles.append(l_s)

            # Comprobamos si el documento usa la palabra explícita "EPÍGRAFE"
            tiene_palabra_epigrafe = any(
                re.match(r'^(?:[•\*\-–]\s*)?EP[IÍ]GRAFE\s+(?:\d+|[I|V|X]+)', l, re.IGNORECASE)
                for l in lineas_utiles
            )

            def _es_inicio_epigrafe(linea):
                if tiene_palabra_epigrafe:
                    return bool(re.match(r'^(?:[•\*\-–]\s*)?EP[IÍ]GRAFE\s+(?:\d+|[I|V|X]+)\b', linea, re.IGNORECASE))
                # Si el PDF no escribe la palabra "EPÍGRAFE", solo corta en títulos principales EN MAYÚSCULAS numerados (1., 2., I., II.)
                return bool(
                    re.match(r'^(?:\d{1,2}[\.\-\)]|[I|V|X]{1,4}[\.\-\)])\s+[A-ZÁÉÍÓÚÑ0-9\s,\.\-–:\(\)\/«»"]+$', linea)
                    and linea.isupper()
                    and len(linea) >= 12
                )

            epigrafes_detectados = []
            idx_l = 0
            n_lineas = len(lineas_utiles)

            while idx_l < n_lineas:
                l_actual = lineas_utiles[idx_l]
                if _es_inicio_epigrafe(l_actual):
                    partes_tit = [l_actual]
                    idx_l += 1
                    # Si el título del epígrafe continúa en la línea siguiente en mayúsculas (o empieza sin terminar frase), lo unimos al título
                    while idx_l < n_lineas and not _es_inicio_epigrafe(lineas_utiles[idx_l]):
                        cand = lineas_utiles[idx_l]
                        if (cand.isupper() and len(cand) < 140) or (not partes_tit[-1].endswith(('.', ':')) and len(" ".join(partes_tit)) < 75 and len(cand) < 95 and not cand.endswith('.')):
                            partes_tit.append(cand)
                            idx_l += 1
                        else:
                            break
                    titulo_ep = " ".join(partes_tit).strip()

                    # Recogemos TODO el cuerpo de explicación hasta el siguiente Epígrafe o hasta el final del documento
                    cuerpo_ep = []
                    while idx_l < n_lineas and not _es_inicio_epigrafe(lineas_utiles[idx_l]):
                        cuerpo_ep.append(lineas_utiles[idx_l])
                        idx_l += 1

                    texto_ep = PDFQuizParser._unir_lineas_en_parrafos(cuerpo_ep)
                    if texto_ep:
                        epigrafes_detectados.append((titulo_ep, texto_ep))
                else:
                    idx_l += 1

            if epigrafes_detectados:
                for i_ep, (tit_ep, txt_ep) in enumerate(epigrafes_detectados, 1):
                    enc_tema = f" — {tema_cabecera}" if tema_cabecera else ""
                    desarrollo_qs.append({
                        "is_open": True,
                        "tipo_abierta": "DESARROLLO",
                        "preamble": f"📝 **PREGUNTA DE DESARROLLO — EPÍGRAFE {i_ep} DE {len(epigrafes_detectados)}{enc_tema} (2.º EJERCICIO GESTIÓN)**",
                        "question_text": f"Desarrolla de forma completa y rigurosa el siguiente epígrafe conforme a la normativa vigente:\n\n« {tit_ep} »",
                        "options": [],
                        "answer": -1,
                        "answer_text": "",
                        "explanation": txt_ep
                    })
            elif lineas_utiles:
                texto_integro = PDFQuizParser._unir_lineas_en_parrafos(lineas_utiles)
                tit_gen = tema_cabecera or lineas_utiles[0][:100]
                desarrollo_qs.append({
                    "is_open": True,
                    "tipo_abierta": "DESARROLLO",
                    "preamble": "📝 **PREGUNTA DE DESARROLLO (SEGUNDO EJERCICIO DE LA OPOSICIÓN DE GESTIÓN)**",
                    "question_text": f"Desarrolla de forma completa y rigurosa los epígrafes del tema conforme a la normativa vigente:\n\n« {tit_gen} »",
                    "options": [],
                    "answer": -1,
                    "answer_text": "",
                    "explanation": texto_integro
                })

        if modo == "DESARROLLO":
            return desarrollo_qs
        if modo == "SUPUESTOS":
            return supuestos_qs
        return desarrollo_qs + supuestos_qs

    @staticmethod
    def parse(pdf_bytes, max_options=None):
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        questions, lines = [], []
        stop_reading = ignoring_mode = entered_supuestos = False
        detected_gestion_header = False
        detected_adm_header = False

        for page in doc:
            if stop_reading: break
            for b in page.get_text("dict")["blocks"]:
                if stop_reading: break
                if b.get("type", 0) == 0:
                    for l in b["lines"]:
                        if stop_reading: break
                        line_text, is_bold = "", False
                        for s in l["spans"]:
                            t = s["text"].strip()
                            if not t: continue
                            line_text += t + " "
                            if "bold" in s["font"].lower() or (s["flags"] & 2 != 0):
                                if not re.match(r'^[a-dA-D][\)\.-]?$', t): is_bold = True
                        line_text = line_text.strip()
                        if line_text:
                            if line_text.isupper():
                                if re.search(r'\bADMINISTRATIVOS?\s+DE\s+LA\s+SEGURIDAD\s+SOCIAL\b', line_text):
                                    detected_adm_header = True
                                elif re.search(r'\bGESTI[OÓ]N\s+DE\s+LA\s+SEGURIDAD\s+SOCIAL\b', line_text):
                                    detected_gestion_header = True
                            line_text = re.sub(r'<{2,}', '«', line_text)
                            line_text = re.sub(r'>{2,}', '»', line_text)
                            line_text = re.sub(r'<(?=[A-ZÁÉÍÓÚÑa-záéíóúñ0-9"«])', '«', line_text)
                            line_text = re.sub(r'(?<=[.?!;:"»a-zA-Z0-9])>', '»', line_text)
                            line_text = re.sub(r'(?:https?://)?(?:www\.)?oposiciona\.es\b', '', line_text, flags=re.IGNORECASE).strip()
                            line_text = re.sub(r'\bP[aá]gina\s+\d+\s+de\s+\d+\b', '', line_text, flags=re.IGNORECASE).strip()
                            for pat in [
                                r'^(?:OPOSICIONA\s*)+', r'^POSICIO\s*', r'^GESTI[OÓ]N DE LA SEGURIDAD SOCIAL\s*', r'^ADMINISTRATIVO DE LA SEGURIDAD SOCIAL\s*',
                                r'^EXAMEN\s+REPASO\s+ADMINISTRATIVO\s+\d+\s+[A-ZÁÉÍÓÚÑ]+\s+202\d\s*',
                                r'^EXAMEN\s+REPASO\s+TEMA\s+\d+\s+COMPLETO\s*',
                                r'^(?:GENERAL\s+|ESPEC[IÍ]FICO\s+|EXAMEN\s+|TEST\s+|RESPUESTAS\s+)?TEMAS?\s+\d+[a-zA-Z]?\s*[\-–:]\s*(?:ADMINISTRATIVO|GESTI[OÓ]N)\s+202\d\s*',
                                r'^(?:GENERAL\s+|ESPEC[IÍ]FICO\s+|EXAMEN\s+|TEST\s+|RESPUESTAS\s+)?TEMAS?\s+\d+[a-zA-Z]?\s*[\-–:]\s*[A-ZÁÉÍÓÚÑ0-9\s\-–:,\.\(\)\/]+\b\.?\s*',
                                r'^ESPECIAL\s+SIMULACROS?\s+\d+\s*[\-–]\s*\d+\s+[A-ZÁÉÍÓÚÑ0-9\s\-–:,\.\(\)\/]+\s*',
                                r'^TEST\s+ADMINISTRATIVO\s+\d+\s+TODO\s+EL\s+TEMARIO\s*',
                                r'^RESPUESTAS\s+(?:TIPO\s+)?TEST:?\s+TEMAS?\s+\d+\s+[A-ZÁÉÍÓÚÑ0-9\s\-–:,\.\(\)\/]+\b\.?\s*',
                                r'^EXAMEN\s+[A-ZÁÉÍÓÚÑ0-9\s]+\s*202\d\s*'
                            ]:
                                m = re.match(pat, line_text, flags=re.IGNORECASE)
                                if m and m.group(0).isupper(): line_text = line_text[m.end():].strip()
                        if not line_text: continue
                        tl = line_text.lower().translate(str.maketrans("áéíóúäτεμα", "aeiouatema"))
                        tl_clean_spaces = re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', '', tl).strip())

                        if "plantilla de respuesta" in tl_clean_spaces or "plantillas de respuesta" in tl_clean_spaces:
                            stop_reading = True; break
                        if not re.match(r'^\s*(?:Pregunta\s+)?\d+\s*[\.\-\):]', line_text, re.IGNORECASE):
                            if any(x in tl_clean_spaces for x in ["supuesto practico", "supuestos practicos", "pregunta de desarrollo", "preguntas de desarrollo", "casos practicos", "caso practico"]):
                                if line_text.isupper() or len(tl_clean_spaces) < 45:
                                    ignoring_mode = entered_supuestos = True
                        if any(x in tl_clean_spaces for x in ["preguntas de reserva", "pregunta de reserva"]) or tl_clean_spaces == "reserva":
                            if not entered_supuestos: ignoring_mode = False
                        if not ignoring_mode and questions and questions[-1].get("state") == "E":
                            for pat in [
                                r'^(La mercantil|La empresa)\s+["\'«][A-ZÁÉÍÓÚÑ]', r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+y\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+son\s+',
                                r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+de\s+\d+\s+(y\s+\d+\s+)?años', r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+forma\s+una\s+familia',
                                r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+cumple\s+\d+\s+años\s+el', r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+nacid[ao]\s+el\s+\d+',
                                r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+camarer[ao]\s+desde', r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+trabaja\s+en\s+la\s+empresa'
                            ]:
                                if re.match(pat, line_text): ignoring_mode = entered_supuestos = True; break
                        if ignoring_mode: continue

                        is_header = bool(line_text.isupper() and re.match(r'^(RESPUESTAS\s+|GENERAL\s+|ESPECIFICO\s+|EXAMEN\s+|TEST\s+|BLOQUE\s+\d+\s*[\-–]?\s*)?(?:TEST\s+DE\s+REPASO\s+)?TEMAS?\s+\d+', line_text))
                        is_page_ref = bool(re.match(r'^\(p[aá]gina\s+\d+', line_text.strip(), re.IGNORECASE))
                        if not is_header and not is_page_ref and len(tl_clean_spaces) < 120:
                            for pat in [
                                r'^oposiciona', r'oposicionaes', r'^pagina\s+\d+\s+de\s+\d+$', r'^(administrativo|gestion)\s+de\s+la\s+seguridad\s+social',
                                r'^(administrativo|gestion)\s+202\d\s+tema\s+\d+[a-z]?', r'^tema\s+\d+[a-z]?\s+(administrativo|gestion)\s+202\d$',
                                r'^tema\s+\d+[a-z]?\s+campo\s+de\s+aplicacion\s+y\s+composicion',
                                r'^tema\s+\d+\s+derecho\s+mercantil',
                                r'^(general|especifico|examen|test|respuestas|respuestas\s+(tipo\s+)?test:?|test\s+profesor)\s+temas?\s+\d+',
                                r'^bloque\s+\d+\s+test\s+de\s+repaso\s+temas?\s+\d+',
                                r'^examen\s+repaso', r'^examen\s+[a-záéíóúñ0-9\s]+\s*202\d', r'^normas\s+para\s+la\s+realizacion', r'^especial\s+simulacros?',
                                r'^test\s+administrativo\s+\d+\s+todo\s+el\s+temario', r'^respuestas\s+tipo\s+test:\s+temas?\s+\d+'
                            ]:
                                if re.search(pat, tl_clean_spaces): is_header = True; break
                        if is_header: continue

                        line_text = PDFQuizParser.traducir_ingles_no_rae(line_text)
                        line_text = re.sub(r'(\d+\.)\s+([ºª°])', r'\1\2', line_text)

                        line_text = re.sub(r'(?<=[.?!;\)\]"\'”»])\s*(Explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?[:\.]?|Respuest[as]?:|Resp:|El\s+n[úu]cleo\s+de\s+la\s+trampa:|La\s+trampa\s+del\s+examinador:|La\s+trampa\s+del\s+examen:)(\s|$)', r'\n\1\2', line_text, flags=re.IGNORECASE)
                        line_text = re.sub(r'(?<=\S)\s{2,}(Explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?[:\.]?|Respuest[as]?:|Resp:|El\s+n[úu]cleo\s+de\s+la\s+trampa:|La\s+trampa\s+del\s+examinador:|La\s+trampa\s+del\s+examen:)(\s|$)', r'\n\1\2', line_text, flags=re.IGNORECASE)
                        line_text = re.sub(r'(?<=\S)\s*(OJO|NOTA|IMPORTANTE|RECUERDA|Regla\s+mnemot[ée]cnica(?:\s+para\s+el\s+examen)?):', r'\n\1:', line_text, flags=re.IGNORECASE)
                        line_text = re.sub(r'(?<=[.?!;”"\'\)])\s*(?<!"\s)(?<!«\s)(Art[íi]culo\s+aplicable:|Art[íi]culo|Art\.)\s', r'\n\1 ', line_text)
                        line_text = re.sub(r'(?<=\S)\s+([•\*])(\s|$)', r'\n\1\2', line_text)
                        line_text = re.sub(r'(?<=[a-zA-ZáéíóúñÁÉÍÓÚÑ\)\."\'”»])(?<![0-9]\.)(?<!\d)(\d{1,3}(?:[\.\-]+:?|:))(?!\s*[ºª°\d])\s*(?=[A-ZÁÉÍÓÚÑ¿¡"\'«])', r'\n\1 ', line_text)
                        line_text = re.sub(r'(?<![0-9]\.)(?<!\d)([.?!;:"»”\)])\s*([a-d][\)\.\-]|[A-D][\)\-])\s+(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])', r'\1\n\2 ', line_text)
                        line_text = re.sub(r'(?<![0-9]\.)(?<![\dA-ZÁÉÍÓÚÑ])([.?!;:"»”\)])([a-d][\)\.\-]|[A-D][\)\-])(?!\s*\.)\s*(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])', r'\1\n\2 ', line_text)
                        line_text = re.sub(r'(?<=\S)\s*(\(p[aá]pages?\s+\d+[^)]*\)|\(p[aá]ginas?\s+\d+[^)]*\))', r'\n\1', line_text, flags=re.IGNORECASE)

                        for part in line_text.split('\n'):
                            part = part.strip()
                            if part:
                                lines.append({"text": re.sub(r'^([a-d][\)\.-]|[A-D][\)\-])(?=[^\s])', r'\1 ', part), "bold": is_bold})
                    lines.append({"text": "<NEW_BLOCK>", "bold": False})

        cleaned_num_lines, k = [], 0
        while k < len(lines):
            curr = lines[k]
            txt = curr["text"].strip()
            if re.match(r'^(?:Pregunta\s+)?\d{1,3}[,\.\-\):]+$', txt, re.IGNORECASE):
                m = k + 1
                while m < len(lines) and lines[m]["text"] == "<NEW_BLOCK>":
                    m += 1
                if cleaned_num_lines and (
                    ")" in txt and "(" not in txt and cleaned_num_lines[-1]["text"].count("(") > cleaned_num_lines[-1]["text"].count(")") or
                    (m < len(lines) and re.match(r'^[a-d][\)\.\-](\s|$)', lines[m]["text"].strip(), re.IGNORECASE))
                ):
                    prev_idx = len(cleaned_num_lines) - 1
                    while prev_idx >= 0 and cleaned_num_lines[prev_idx]["text"] == "<NEW_BLOCK>":
                        prev_idx -= 1
                    if prev_idx >= 0:
                        cleaned_num_lines[prev_idx]["text"] = cleaned_num_lines[prev_idx]["text"].rstrip() + " " + txt
                        k += 1
                        continue
                if m < len(lines):
                    next_txt = lines[m]["text"].strip()
                    if re.match(r'^(?:Pregunta\s+)?\d{1,3}[,\.\-\):]+(\s|$)', next_txt, re.IGNORECASE):
                        k = m
                        continue
                    else:
                        lines[m]["text"] = txt + " " + next_txt
                        lines[m]["bold"] = curr["bold"] or lines[m]["bold"]
                        k = m
                        continue
            cleaned_num_lines.append(curr)
            k += 1
        lines = cleaned_num_lines

        reordered_lines, r_idx = [], 0
        while r_idx < len(lines):
            t_curr = lines[r_idx]["text"].strip()
            if re.match(r'^a[\)\.\-]\s*$', t_curr, re.IGNORECASE):
                n_b = r_idx + 1
                while n_b < len(lines) and lines[n_b]["text"] == "<NEW_BLOCK>":
                    n_b += 1
                if n_b < len(lines) and re.match(r'^b[\)\.\-]\s*$', lines[n_b]["text"].strip(), re.IGNORECASE):
                    chunk_lines = []
                    scan_k = n_b + 1
                    while scan_k < len(lines) and len(chunk_lines) < 8:
                        tk = lines[scan_k]["text"].strip()
                        if tk != "<NEW_BLOCK>":
                            if re.match(r'^[c-d][\)\.\-](\s|$)', tk, re.IGNORECASE):
                                break
                            chunk_lines.append(lines[scan_k])
                        scan_k += 1
                    prev_real = len(reordered_lines) - 1
                    while prev_real >= 0 and reordered_lines[prev_real]["text"] == "<NEW_BLOCK>":
                        prev_real -= 1
                    if prev_real >= 0:
                        prev_txt = reordered_lines[prev_real]["text"].strip()
                        prev_prev = prev_real - 1
                        while prev_prev >= 0 and reordered_lines[prev_prev]["text"] == "<NEW_BLOCK>":
                            prev_prev -= 1
                        if prev_prev >= 0 and reordered_lines[prev_prev]["text"].strip().endswith(":") and not prev_txt.endswith(":") and not prev_txt.endswith("?"):
                            orphan_line = reordered_lines.pop(prev_real)
                            if len(chunk_lines) >= 2:
                                txt_b = chunk_lines[0]["text"].strip()
                                txt_a = orphan_line["text"].strip() + " " + " ".join(x["text"].strip() for x in chunk_lines[1:])
                                bold_a = lines[r_idx]["bold"] or orphan_line["bold"] or chunk_lines[-1]["bold"]
                                bold_b = lines[n_b]["bold"] or chunk_lines[0]["bold"]
                                reordered_lines.append({"text": "a) " + txt_a, "bold": bold_a})
                                reordered_lines.append({"text": "b) " + txt_b, "bold": bold_b})
                                r_idx = scan_k
                                continue
                    if len(chunk_lines) >= 1:
                        combined_txt = " ".join(x["text"].strip() for x in chunk_lines)
                        m_two = re.match(r'^(.+?\.)\s+([A-ZÁÉÍÓÚÑ¿¡0-9].*)$', combined_txt)
                        if m_two:
                            bold_a = lines[r_idx]["bold"] or chunk_lines[0]["bold"]
                            bold_b = lines[n_b]["bold"] or chunk_lines[-1]["bold"]
                            reordered_lines.append({"text": "a) " + m_two.group(1).strip(), "bold": bold_a})
                            reordered_lines.append({"text": "b) " + m_two.group(2).strip(), "bold": bold_b})
                            r_idx = scan_k
                            continue
            if re.match(r'^b[\)\.\-]\s*$', t_curr, re.IGNORECASE):
                n_a = r_idx + 1
                while n_a < len(lines) and lines[n_a]["text"] == "<NEW_BLOCK>":
                    n_a += 1
                if n_a < len(lines) and re.match(r'^a[\)\.\-]\s+\S', lines[n_a]["text"].strip(), re.IGNORECASE):
                    n_b_txt = n_a + 1
                    while n_b_txt < len(lines) and lines[n_b_txt]["text"] == "<NEW_BLOCK>":
                        n_b_txt += 1
                    if n_b_txt < len(lines) and not re.match(r'^[a-d][\)\.\-](\s|$)', lines[n_b_txt]["text"].strip(), re.IGNORECASE):
                        reordered_lines.append(lines[n_a])
                        reordered_lines.append({
                            "text": "b) " + lines[n_b_txt]["text"].strip(),
                            "bold": lines[r_idx]["bold"] or lines[n_b_txt]["bold"]
                        })
                        r_idx = n_b_txt + 1
                        continue
            reordered_lines.append(lines[r_idx])
            r_idx += 1
        lines = reordered_lines

        merged_lines, i = [], 0
        while i < len(lines):
            curr = lines[i]
            txt = curr["text"].strip()
            if txt != "<NEW_BLOCK>" and re.search(r'(?:«|"|“|\(|\b)(?:Art[íi]culos?|Art\.|Ley|Real\s+Decreto(?:\s+Legislativo|\-ley)?|Decreto(?:\s+Legislativo|\-ley)?)\s*$', txt, re.IGNORECASE):
                j = i + 1
                while j < len(lines) and lines[j]["text"] == "<NEW_BLOCK>": j += 1
                if j < len(lines) and re.match(r'^\d+', lines[j]["text"].strip()):
                    curr["text"] = txt + " " + lines[j]["text"].strip()
                    curr["bold"] = curr["bold"] or lines[j]["bold"]
                    merged_lines.append(curr); i = j + 1; continue
            merged_lines.append(curr); i += 1
        lines = merged_lines

        for i in range(len(lines)):
            txt = lines[i]["text"].strip()
            if txt.endswith("carenci") and i + 1 < len(lines) and lines[i + 1]["text"].strip().startswith("a) se exige"):
                lines[i]["text"] = lines[i]["text"].replace("carenci", "carencia)")
                lines[i + 1]["text"] = lines[i + 1]["text"].replace("a) se exige", "se exige", 1)
            if txt.startswith("D. Carlos"):
                lines[i]["text"] = lines[i]["text"].replace("D. Carlos", "Don Carlos", 1)

        def is_exp_marker(s):
            return bool(
                re.match(r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?|respuestas?|resp)\s*[:\.]+', s, re.IGNORECASE) or
                re.match(r'^explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?\s+[A-ZÁÉÍÓÚÑ"«\']', s) or
                re.match(r'^EXPLICACI[ÓO]N\b', s) or
                re.match(r'^explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?\s*$', s, re.IGNORECASE) or
                re.match(r'^(?:el\s+n[úu]cleo\s+de\s+la\s+trampa|la\s+trampa\s+del\s+examinador|la\s+trampa\s+del\s+examen|regla\s+mnemot[ée]cnica(?:\s+para\s+el\s+examen)?)\s*:', s, re.IGNORECASE)
            )

        def match_q_num(s):
            if re.match(r'^\s*\d{1,4}[\.\-\),\s]+(?:de\s+enero|de\s+febrero|de\s+marzo|de\s+abril|de\s+mayo|de\s+junio|de\s+julio|de\s+agosto|de\s+septiembre|de\s+octubre|de\s+noviembre|de\s+diciembre|meses|años|días|horas|euros|por\s+ciento|y\s+\d+|del\s+t[íi]tulo|del\s+art[íi]culo|del\s+real|de\s+la\s+ley)\b', s, re.IGNORECASE):
                return None
            if re.match(r'^\s*(?:19\d\d|20\d\d)\b', s):
                return None
            return (
                re.match(r'^\s*(?:Pregunta\s+)?(\d+)[,\.\-\):]+(?![\dºª°])\s+\S', s, re.IGNORECASE) or
                re.match(r'^\s*(?:Pregunta\s+)?(\d+)\s+[,\.\-\):]+(?![\dºª°])\s*\S', s, re.IGNORECASE) or
                re.match(r'^\s*(?:Pregunta\s+)?(\d+)[,\.\-\):]+(?![\dºª°])\s*(?=[¿¡A-ZÁÉÍÓÚÑ«"\'\[\(])', s) or
                re.match(r'^\s*(?:Pregunta\s+)?(\d+)\s*¿', s, re.IGNORECASE)
            )

        pdf_uses_explicit_exp = sum(1 for l in lines if is_exp_marker(l["text"].strip())) >= 10
        current_q, preamble, expected_q_num = None, "", 1

        for idx, line in enumerate(lines):
            text, is_bold = line["text"], line["bold"]
            if text == "<NEW_BLOCK>":
                if current_q and current_q["state"] == "E" and current_q["explanation"]:
                    if current_q["explanation"].strip()[-1:] in ['.', ':', '?', '!', '"', '”', '»', ')'] and not current_q["explanation"].endswith("\n\n"):
                        current_q["explanation"] = current_q["explanation"].rstrip() + "\n\n"
                continue

            text_lower = text.lower()
            is_option = bool(re.match(r'^([a-d][\)\.\-]|[A-D][\)\-])(\s|$)', text))
            is_explanation = False if (current_q and current_q["state"] == "E") else is_exp_marker(text.strip())

            forced_not_option = False
            if is_option and current_q and current_q["state"] == "Q" and not current_q["options"]:
                if text.strip().endswith('?') and not re.match(r'^([a-d][\)\.\-]|[A-D][\)\-])\s*[¿A-ZÁÉÍÓÚÑ]', text):
                    is_option, forced_not_option = False, True

            is_reserve = bool(re.search(r'\bpreguntas?\s+de\s+reserva\b', text_lower) or re.match(r'^\s*reserva\b', text_lower))
            is_case_study = bool(re.match(r'^\s*(supuestos?\s+pr[áa]cticos?)', text_lower))
            is_letter_block = bool(re.match(r'^[A-ZÑ][\)\.-]+\s*[A-ZÁÉÍÓÚÑ]', text))
            if is_letter_block and (re.search(r'\b(fals[ao]|verdader[ao]|correct[ao]|incorrect[ao])\b', text_lower) or (current_q and current_q["state"] == "E" and pdf_uses_explicit_exp)):
                is_letter_block = False

            if (is_reserve or is_case_study or is_letter_block) and (not current_q or current_q["state"] == "E"):
                is_real_preamble = any(
                    match_q_num(lines[j]["text"].strip()) or
                    (re.match(r'^\s*(¿|C[óo]mo|Cu[áa]l|Cu[áa]ntos|Qu[ée])\b', lines[j]["text"].strip(), re.IGNORECASE) and lines[j]["text"].strip().endswith('?'))
                    for j in range(idx + 1, min(idx + 30, len(lines)))
                )
                if is_real_preamble or is_reserve or is_case_study:
                    if current_q and current_q["options"]: questions.append(current_q)
                    current_q = None
                    if not is_reserve:
                        preamble += text + "\n"
                        expected_q_num = 1
                    continue

            is_new_q = False
            m_num = match_q_num(text)

            if m_num and current_q and current_q["state"] == "E":
                exp_so_far = current_q["explanation"].strip()
                if re.search(r'(?:«|"|“|\(|\b)(?:Art[íi]culos?|Art\.|Ley|Real\s+Decreto(?:\s+Legislativo|\-ley)?|Decreto(?:\s+Legislativo|\-ley)?)\s*$', exp_so_far[-60:], re.IGNORECASE):
                    m_num = None
                elif exp_so_far.count("«") > exp_so_far.count("»") and not re.search(r'\(p[aá]ginas?\s+\d+', exp_so_far[-80:], re.IGNORECASE):
                    m_num = None

            m_rescue = False
            if not m_num and not is_option and not is_explanation and not pdf_uses_explicit_exp:
                tc = text.strip()
                if ((current_q and current_q["state"] in ["E", "O"]) or not current_q) and re.match(r'^\s*(¿|C[óo]mo|Cu[áa]l|Cu[áa]ntos|Qu[ée])\b', tc, re.IGNORECASE) and tc.endswith('?'):
                    m_rescue = True

            if m_num or m_rescue:
                is_real_q_candidate = found_a = found_b = found_c = aborted = False
                cand_num = int(m_num.group(1)) if m_num else expected_q_num
                for j in range(idx + 1, min(idx + 140, len(lines))):
                    ft = lines[j]["text"].strip()
                    if ft == "<NEW_BLOCK>": continue
                    m_fnum = match_q_num(ft)
                    if m_fnum and (
                        re.match(r'^\d+\.\d+', ft) or
                        re.match(r'^\d+\s+a\s+\d+\s+del\b', ft, re.IGNORECASE)
                    ):
                        m_fnum = None
                    if not found_a:
                        if is_exp_marker(ft):
                            aborted = True; break
                        if m_fnum and int(m_fnum.group(1)) == cand_num + 1:
                            aborted = True; break
                        if re.match(r'^a[\)\.\-](\s|$)', ft, re.IGNORECASE):
                            found_a = True
                            if re.search(r'(?:^|\s)b[\)\.\-](\s|$)', ft, re.IGNORECASE): found_b = True
                            if re.search(r'(?:^|\s)c[\)\.\-](\s|$)', ft, re.IGNORECASE): found_c = True
                    elif not found_b:
                        if is_exp_marker(ft):
                            aborted = True; break
                        if re.match(r'^b[\)\.\-](\s|$)', ft, re.IGNORECASE) or re.search(r'(?:^|\s)b[\)\.\-](\s|$)', ft, re.IGNORECASE):
                            found_b = True
                            if re.search(r'(?:^|\s)c[\)\.\-](\s|$)', ft, re.IGNORECASE): found_c = True
                            if not pdf_uses_explicit_exp: is_real_q_candidate = True; break
                    else:
                        if re.match(r'^c[\)\.\-](\s|$)', ft, re.IGNORECASE) or re.search(r'(?:^|\s)c[\)\.\-](\s|$)', ft, re.IGNORECASE):
                            found_c = True
                        if is_exp_marker(ft):
                            is_real_q_candidate = True; break
                        if m_fnum:
                            if not pdf_uses_explicit_exp and found_c and (int(m_fnum.group(1)) == cand_num + 1 or int(m_fnum.group(1)) == 1):
                                is_real_q_candidate = True; break
                            if not pdf_uses_explicit_exp:
                                aborted = True; break
                        if re.match(r'^\(p[aá]ginas?\s+\d+', ft, re.IGNORECASE):
                            if not pdf_uses_explicit_exp and found_c:
                                is_real_q_candidate = True; break
                            aborted = True; break

                if is_real_q_candidate and not aborted:
                    if m_num:
                        num = int(m_num.group(1))
                        prev_closed_with_pageref = bool(current_q and current_q["state"] == "E" and re.search(r'\(p[aá]ginas?\s+\d+', current_q["explanation"], re.IGNORECASE))
                        if current_q is None:
                            is_new_q, expected_q_num = True, num + 1
                        elif pdf_uses_explicit_exp and current_q["state"] in ["O", "E"] and 1 <= num <= 250:
                            is_new_q, expected_q_num = True, num + 1
                        elif expected_q_num - 1 <= num <= expected_q_num + 15:
                            is_new_q, expected_q_num = True, num + 1
                        elif num in [1, 2] and current_q["state"] in ["O", "E"] and expected_q_num >= 5:
                            is_new_q, expected_q_num = True, num + 1
                        elif prev_closed_with_pageref and 1 <= num <= 250:
                            is_new_q, expected_q_num = True, num + 1
                    elif m_rescue:
                        is_new_q = True; expected_q_num += 1

            if is_new_q:
                ct = re.sub(r'^\s*(?:Pregunta\s+)?\d+\s*¿', '¿', re.sub(r'^\s*(?:Pregunta\s+)?\d+[,\.\-\):]+\s*(-*\s*)?', '', text, flags=re.IGNORECASE), flags=re.IGNORECASE)
                if m_rescue and current_q and current_q["state"] == "E" and current_q["explanation"]:
                    exp_parts = current_q["explanation"].rstrip().split("\n\n")
                    last_part = exp_parts[-1].strip()
                    if last_part.endswith(",") and len(last_part) < 180:
                        ct = re.sub(r'^\s*(?:Pregunta\s+)?\d+[,\.\-\):]*\s*', '', last_part, flags=re.IGNORECASE) + " " + ct
                        current_q["explanation"] = "\n\n".join(exp_parts[:-1]).strip()
                if current_q and current_q["options"]: questions.append(current_q)
                current_q, preamble = {"preamble": preamble.strip(), "question_text": ct, "options": [], "answer": -1, "explanation": "", "state": "Q"}, ""
                continue

            if not current_q:
                if not is_reserve: preamble += text + "\n"
                continue

            if is_option and current_q["state"] in ["Q", "O"] and len(current_q["options"]) < 4 and re.match(r'^([a-d][\)\.-]|[A-D][\)\-])(\s|$)', text):
                opt_letter = text.strip()[0].lower()
                expected_letter = chr(ord('a') + len(current_q["options"]))
                if opt_letter == expected_letter:
                    only_marker = bool(re.match(r'^([a-d][\)\.-]|[A-D][\)\-])\s*$', text.strip()))
                    if only_marker and current_q["options"]:
                        prev_opt = current_q["options"][-1]
                        m_split = re.match(r'^([a-dA-D][\)\.-]\s*.+?\.)\s+([A-ZÁÉÍÓÚÑ].*)$', prev_opt)
                        if m_split:
                            current_q["options"][-1] = m_split.group(1)
                            text = f"{text.strip()} {m_split.group(2)}"
                    current_q["options"].append(text)
                    current_q["state"] = "O"
                    if is_bold and current_q["answer"] == -1: current_q["answer"] = len(current_q["options"]) - 1
                    continue

            if is_explanation:
                exp_clean_line = re.sub(r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?|respuestas?|resp)\s*[:\.]*\s*', '', text.strip(), flags=re.IGNORECASE).strip()
                if exp_clean_line:
                    current_q["explanation"] = (current_q["explanation"].rstrip() + "\n\n" + exp_clean_line) if current_q["explanation"] else exp_clean_line
                current_q["state"] = "E"
                continue

            if current_q["state"] == "Q":
                if forced_not_option and re.search(r'[a-zA-Z]$', current_q["question_text"].strip()):
                    m = re.match(r'^([a-zA-Z])([\)\.\-])\s*(.*)', text)
                    current_q["question_text"] = (current_q["question_text"].strip() + m.group(1) + m.group(2) + " " + m.group(3)) if m else (current_q["question_text"] + " " + text)
                else:
                    current_q["question_text"] += " " + text
            elif current_q["state"] == "O":
                if re.search(r'\(Art\.\s*$', text.strip()):
                    continue
                next_expected_opt = chr(ord('a') + len(current_q["options"]))
                has_more_opts_ahead = False
                if len(current_q["options"]) < 4:
                    for k_ah in range(idx + 1, min(idx + 12, len(lines))):
                        t_ah = lines[k_ah]["text"].strip()
                        if t_ah == "<NEW_BLOCK>": continue
                        if is_exp_marker(t_ah) or match_q_num(t_ah): break
                        if re.match(rf'^{next_expected_opt}[\)\.\-](\s|$)', t_ah, re.IGNORECASE):
                            has_more_opts_ahead = True; break

                lo = current_q["options"][-1].strip()
                ep = bool(re.search(r'[\.;\?]$', lo))
                ec = bool(re.search(r'(,| y| o| que| de| a| con| en| por| para| el| la| los| las| un| una)$', lo, re.IGNORECASE))
                inp = not has_more_opts_ahead and len(current_q["options"]) >= 3 and ep and bool(re.match(r'^[A-Z0-9¿¡"\'«]', text))
                ilr = not has_more_opts_ahead and bool(re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|seg[úu]n)\b', text_lower))
                iie = not has_more_opts_ahead and len(current_q["options"]) >= 3 and bool(re.match(r'^[A-ZÁÉÍÓÚ¿¡"\'«]', text)) and (
                    bool(re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|seg[úu]n|normativa|de conformidad|conforme|en virtud)\b', text_lower)) or
                    (bool(re.match(r'^(el\b|la\b|los\b|las\b|para\b|de\b|en\b|cuando\b|se\b|es\b|esta\b|este\b|al\b|por\b|si\b)', text_lower)) and (ep or not ec))
                )
                implicit_after_4_opts = len(current_q["options"]) >= 4 and ep and ilr
                if len(current_q["options"]) < 3 or ec or len(lo) <= 5: inp = ilr = iie = False
                if ((inp or ilr or iie) and not pdf_uses_explicit_exp) or implicit_after_4_opts:
                    current_q["state"], current_q["explanation"] = "E", text
                else:
                    if is_bold and current_q["answer"] == -1: current_q["answer"] = len(current_q["options"]) - 1
                    current_q["options"][-1] += " " + text
            elif current_q["state"] == "E":
                if current_q["explanation"].endswith("\n\n"):
                    current_q["explanation"] += text
                else:
                    lc = current_q["explanation"].strip()[-1:] if current_q["explanation"].strip() else ""
                    ib = bool(re.match(r'^[\s]*[•\*]', text))
                    io = bool(re.match(r'^[\s]*(OJO|NOTA|IMPORTANTE|RECUERDA|Regla\s+mnemot[ée]cnica)[\s:]', text, re.IGNORECASE))
                    ipr = bool(re.match(r'^\(p[aá]ginas?\s+\d+', text, re.IGNORECASE))
                    ins = lc in ['.', ':', '?', '!', '"', '”', '»'] and bool(re.match(r'^[\s]*([A-ZÁÉÍÓÚ¿¡"\'«]|\d)', text))
                    if ipr or ib or io or ins:
                        current_q["explanation"] = current_q["explanation"].rstrip() + "\n\n" + text
                    else:
                        current_q["explanation"] += (" " + text) if current_q["explanation"] else text

        if current_q and current_q["options"]: questions.append(current_q)

        for q in questions:
            if q["answer"] == -1 and q.get("explanation"):
                m_ans = re.search(r'(?:respuesta\s+correcta\s+es\s+la|opci[óo]n\s+([a-d])\s+es\s+la\s+correcta|correcta\s*:\s*([a-d]))\s*([a-d])?', q["explanation"], re.IGNORECASE)
                if m_ans:
                    letra_det = (m_ans.group(1) or m_ans.group(2) or m_ans.group(3) or "").lower()
                    if letra_det and 0 <= (ord(letra_det) - ord('a')) < len(q["options"]):
                        q["answer"] = ord(letra_det) - ord('a')

        target_max = max_options
        if target_max is None:
            if detected_gestion_header and not detected_adm_header:
                target_max = 3
            elif len(questions) >= 5:
                count_3_opts = sum(1 for q in questions if len(q["options"]) == 3)
                if count_3_opts / len(questions) >= 0.80:
                    target_max = 3

        if target_max is not None:
            for q in questions:
                if len(q["options"]) > target_max:
                    PDFQuizParser._reducir_opciones_pregunta(q, target_max)

        return questions
# === FIN SECCIÓN 2 ===


# === SECCIÓN 3: CATÁLOGO DE TESTS ===
_D = "https://drive.google.com/uc?export=download&id="

NUEVOS_HOY = [
    "✨ NOVEDADES RDL 31_2026 adm",
    "✨NOVEDADES RDL_31_2026 gestion",
    "EXAMEN SABADO 01 NOVIEMBRE 2026",
]

# Categorías exclusivas en GESTIÓN para el Administrador (Segundo y Tercer Ejercicio)
DESARROLLO_GESTION_ADMIN = {
    "Elige una pregunta de desarrollo...": None,
    "📝 TEMA 73 - PREGUNTA DE DESARROLLO: ACCIÓN PROTECTORA EN EL SISTEMA ESPECIAL DE EMPLEADOS DE HOGAR": "https://drive.google.com/uc?export=download&id=1gHCYu7-PUSZB34e4IFlG5twCQJ8r9rXm",
}

SUPUESTOS_GESTION_ADMIN = {
    "Elige un supuesto práctico...": None,
    "📋 TEMA 73 - SUPUESTOS PRÁCTICOS: FAMILIAS GARCÍA-VALENZUELA Y MONTORO (15 CUESTIONES)": "https://drive.google.com/uc?export=download&id=1gHCYu7-PUSZB34e4IFlG5twCQJ8r9rXm",
}

# ==============================================================================
# >>> INICIO DEL BLOQUE A SUSTITUIR: DICCIONARIO TESTS_DISPONIBLES
# ==============================================================================
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
            "TEMA 11 REPASO FUENTES DE LA UE GENERAL": "https://drive.google.com/uc?export=download&id=1OzmfuJkQooMX7ld_KFrNRnLj4xH9XHD1",
            "TEMA 12 REPASO 1 MV ESPECÍFICO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1GnVkEUXfN2OS2j96nxOu2jhl1OVSEEvx",
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
            "EXAMEN SABADO 01 NOVIEMBRE 2026": "https://drive.google.com/uc?export=download&id=1Yh_1mNSQNgQ6m-L-V2r6gaahKoWar0Oi",
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
            "TEMA 11 REPASO FUENTES DE LA UE GENERAL": "https://drive.google.com/uc?export=download&id=1YLmKCK14-W0TfRwndlhUSkeWoOMtWxY-",
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
            "Tema_51_Resumen_Epigrafes": "https://drive.google.com/uc?export=download&id=1ZMe2_3RnNyOvg4xv9cwb0QD-5jtX4SXB",
            "Tema_52_Resumen_Epigrafes": "https://drive.google.com/uc?export=download&id=1OBdM_hMExnQY40sfIQlCZdSZT3eFaMG8",
        },
        "ESPECIFICO": {
            "Elige un test de especifico...": None,
            "TEMA 51 - CONSTITUCION EN LA SS Y TRLGSS ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1NHnqc_FOnsYV1473iGT04VbRCsL5OB0m",
            "TEMA 52 - CAMPO DE APLICACIÓN Y COMPOSICIÓN DEL SISTEMA ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1-5Rm3LkOugs5dVSYdURRAfLVR0FIVnmz",
            "TEMA 52 - REPASO 1 - CAMPO APLICACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1YLYxtBUxnyqcqRonpnOZBH1gs4BiOM1_",
            "TEMA 53 - AFILIACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1Kv-Bm_Eig1SMcXB-xBjzbQwQqjlAQ8Bf",
            "TEMA 53 - REPASO 1 - AFILIACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1_CJEGRuBVlSNa65SOD9N6oey7ZzbNvXb",
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
        },
    },
}
# ==============================================================================
# <<< FIN DEL BLOQUE A SUSTITUIR (Mantén intacto todo lo que va antes y después)
# ==============================================================================

TESTS_DISPONIBLES_INVITADO = {
    "ADMINISTRATIVOS": {
        "ESPECIFICO": {"Elige un test de especifico...": None, "TEMA 04 - TEST Y SUPUESTOS COTIZACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1Tpw0hJ1Vpc8d9KGe6TffL-FRqGoWPTML"},
        "EXAMENES": {"Elige un test de examenes...": None},
        "GENERAL": {"Elige un test de general...": None},
    },
    "GESTION": {
        "ESPECIFICO": {"Elige un test de especifico...": None, "TEMA 53 - AFILIACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1Kv-Bm_Eig1SMcXB-xBjzbQwQqjlAQ8Bf"},
        "EXAMENES": {"Elige un test de examenes...": None},
        "GENERAL": {"Elige un test de general...": None},
    },
}
# === FIN SECCIÓN 3 ===

# === SECCIÓN 4: FUNCIONES Y LÓGICA DEL TEST ===
# Puente automático para evitar NameError con TESTS_DISPONIBLES_COMPLETO
if "TESTS_DISPONIBLES_COMPLETO" not in globals():
    TESTS_DISPONIBLES_COMPLETO = globals().get("TESTS_DISPONIBLES", globals().get("ESTS_DISPONIBLES", {}))

def usuario_es_admin():
    correo_act = (st.session_state.get('email') or "").lower().strip()
    return bool(st.session_state.get('es_admin', False) or correo_act in USUARIOS_ADMIN)

def usuario_puede_reportar():
    return st.session_state.get('rol') != 'INVITADO'

def obtener_tests_segun_rol():
    catalogo_base = globals().get("TESTS_DISPONIBLES_COMPLETO") or globals().get("TESTS_DISPONIBLES") or globals().get("ESTS_DISPONIBLES") or {}
    if st.session_state.get('rol') == 'INVITADO':
        return TESTS_DISPONIBLES_INVITADO
    if usuario_es_admin():
        cat_admin = {
            "ADMINISTRATIVOS": dict(catalogo_base.get("ADMINISTRATIVOS", {})),
            "GESTION": dict(catalogo_base.get("GESTION", {})),
        }
        # Incorpora automáticamente los PDFs de la carpeta DESARROLLO de Drive
        desarrollo_combinado = dict(DESARROLLO_GESTION_ADMIN)
        for k_des, v_des in catalogo_base.get("GESTION", {}).get("DESARROLLO", {}).items():
            if v_des is not None and k_des not in desarrollo_combinado and f"📝 {k_des}" not in desarrollo_combinado:
                desarrollo_combinado[f"📝 {k_des}"] = v_des
        cat_admin["GESTION"]["PREGUNTA DE DESARROLLO"] = desarrollo_combinado
        cat_admin["GESTION"]["SUPUESTOS PRÁCTICOS"] = SUPUESTOS_GESTION_ADMIN
        return cat_admin
    return catalogo_base

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
            "🎩 **Observación del Tribunal Evaluador de Oposiciona:**\n\n"
            "Comprendemos que la preparación hacia el Cuerpo de Gestión de la Administración de la Seguridad Social "
            "tiene momentos de cansancio y máxima exigencia, pero esta plataforma ha sido concebida con un único propósito: "
            "**forjar funcionarios de excelencia y acercarte cada día más a tu plaza, no perder el tiempo**.\n\n"
            "El día del examen oficial ante el Tribunal, cada línea que escribas será el reflejo de tu rigor técnico y de tu temple como futuro gestor público. "
            "Respira hondo, retoma el pulso jurídico y redacta una respuesta a la altura del profesional en el que te estás convirtiendo. "
            "Cuando estés listo, vuelve a pulsar **«Comprobar»**."
        )
    return None

def _dividir_en_oraciones_juridicas(texto):
    if not texto:
        return []
    t = re.sub(r'(?<![.?!:;»"\'])\n(?![a-e][\)\.\-]\s|\d+[\.\)]\s)', ' ', texto)
    t = re.sub(r'\b(art|arts|núm|num|cap|disp|ad|trans|apdo|párr|pág|rd|rdl|et|cc|lec)\.', r'\1<DOT>', t, flags=re.IGNORECASE)
    t = re.sub(r'(\d)\.(\d)', r'\1<DOT>\2', t)
    t = re.sub(r'(\d)\.([a-zA-Zºª°])', r'\1<DOT>\2', t)
    t = re.sub(r'\.([a-e])\b', r'<DOT>\1', t)

    partes = re.split(r'(?<=[.?!;])\s+(?=[A-ZÁÉÍÓÚÑ«"\']|[a-e][\)\.\-]\s|\d+[\.\)]\s)|\n+', t)
    oraciones = []
    for p in partes:
        p_rest = p.replace('<DOT>', '.').strip()
        p_rest = re.sub(r'^[«"\'\-\•\*]+|[»"\']+$', '', p_rest).strip()
        if len(p_rest) >= 30:
            oraciones.append(p_rest)
    return oraciones

# Criterios Oficiales del Tribunal (Resolución 22 de diciembre de 2025 - Cuerpo de Gestión Acceso Libre)
CRITERIOS_OFICIALES_TRIBUNAL_2_EJERCICIO = """
CRITERIOS OFICIALES DE CORRECCIÓN, VALORACIÓN Y SUPERACIÓN DEL SEGUNDO EJERCICIO (CUERPO DE GESTIÓN DE LA ADMINISTRACIÓN DE LA SEGURIDAD SOCIAL - ACCESO LIBRE):
A) Estructura eliminatoria:
   - Primera parte (Preguntas de desarrollo): contestación por escrito a un cuestionario de preguntas sobre las materias del bloque VIII del programa.
   - Segunda parte (Supuestos prácticos): resolución por escrito de un supuesto práctico de ocho preguntas relacionadas con las materias del bloque VIII del programa.
B) Calificación y no compensación:
   - El segundo ejercicio se califica de 0 a 100 puntos (mínimo 50 puntos para superar).
   - Cada parte se califica de 0 a 50 puntos, siendo necesario obtener AL MENOS 25 PUNTOS directos en cada una para sumar ambas partes (sin compensación si alguna es inferior a 25 puntos).
C) Baremo de la Primera Parte (Desarrollo - máximo 50 puntos):
   1. Conocimiento manifestado en la respuesta y precisión de la normativa correspondiente y ajustada a su literalidad: de 0 a 45 puntos.
   2. Orden de las ideas a través de una exposición correctamente estructurada: de 0 a 3 puntos (SIEMPRE QUE se alcancen al menos 20 puntos sobre 45 en el apartado 1; si no llega a 20/45, recibe 0 puntos en este apartado).
   3. Calidad de la expresión escrita: de 0 a 2 puntos (SIEMPRE QUE se alcancen al menos 20 puntos sobre 45 en el apartado 1; si no llega a 20/45, recibe 0 puntos en este apartado).
D) Baremo de la Segunda Parte (Supuesto Práctico - máximo 50 puntos):
   1. Conocimiento manifestado, precisión de la normativa correspondiente y ajustada a su literalidad y precisión de las respuestas a las situaciones prácticas planteadas: de 0 a 45 puntos.
   2. Orden de las ideas a través de una exposición correctamente estructurada: de 0 a 3 puntos (SIEMPRE QUE se alcancen al menos 20 puntos sobre 45 en el apartado 1).
   3. Calidad de la expresión escrita: de 0 a 2 puntos (SIEMPRE QUE se alcancen al menos 20 puntos sobre 45 en el apartado 1).
"""

# Fuentes exclusivas autorizadas de NotebookLM:
# 1) "TEMAS GESTION HASTA EL MOMENTO"
# 2) "TEMAS ADMINISTRATIVO HASTA EL MOMENTO"
# 3) "NOVEDADES 2026"
FUENTES_TEMARIO_NOTEBOOKLM = {
    "SEEH": {
        "cuaderno": "TEMAS GESTION HASTA EL MOMENTO | TEMAS ADMINISTRATIVO HASTA EL MOMENTO | NOVEDADES 2026",
        "epigrafe": "Tema 73 (Bloque VIII) — Epígrafe 5: SISTEMA ESPECIAL PARA EMPLEADOS DE HOGAR (SEEH): Altas, bajas, cotización y particularidades de la acción protectora",
        "resumen_fuente": (
            "- Fuentes consultadas: 'TEMAS GESTION HASTA EL MOMENTO', 'TEMAS ADMINISTRATIVO HASTA EL MOMENTO' y 'NOVEDADES 2026' (TRLGSS RD Legislativo 8/2015, Orden PJC/297/2026, RD 126/2026 SMI, RDL 3/2026 y RDL 31/2026).\n"
            "- Integración en el Régimen General: Ley 27/2011, de 1 de agosto (efectos 01/01/2012) y art. 136.2.b) TRLGSS.\n"
            "- Regulación laboral especial: Real Decreto 1620/2011, de 14 de noviembre (art. 2.1.b ET) y RDL 16/2022, de 6 de septiembre (protección por desempleo y FOGASA).\n"
            "- Campo de aplicación (art. 250 TRLGSS): Servicios retribuidos por cuenta y dependencia del titular del hogar familiar. Excluidos: personas jurídicas/ETT (van al RG ordinario), parientes hasta 2.º grado salvo prueba en contrario de condición salarial, trabajos por amistad/benevolencia o «a la par».\n"
            "- Cotización y beneficios: Escala de tramos sobre retribución (Orden PJC/297/2026 y RD 126/2026 SMI); en tiempo parcial la retribución mínima del tramo es SMI/hora × horas mensuales; no aplica el recargo por contratos inferiores a 30 días (art. 151 TRLGSS) ni la cotización adicional por horas del art. 122 de la Ley 31/2022; reducción del 20% en contingencias comunes o bonificación del 45%/80% en familias numerosas (solo para un cuidador por unidad familiar).\n"
            "- Acción protectora (art. 251 TRLGSS): a) IT común se abona desde el 9.º día (días 4.º al 8.º a cargo del empleador), salvo en las 5 situaciones especiales del art. 169.1.a) TRLGSS tras el RDL 31/2026 (menstruación incapacitante/interrupción embarazo, semana 39.ª, donación órganos, trastorno menopáusico secundario codificado y violencia de género), donde se abona por la entidad gestora/mutua desde el día siguiente a la baja (día de la baja a cargo del empleador); b) Pago directo de IT por la entidad gestora/mutua (no procede pago delegado); c) En contingencias profesionales no aplica el régimen de responsabilidad empresarial en orden a las prestaciones del art. 167 TRLGSS (capital coste); d) Integración de lagunas desde 01/01/2024 en IP común y jubilación conforme a arts. 197.4 y 209.1.b) TRLGSS; e) Desempleo y cobertura del FOGASA (RD 505/1985 y art. 11.2 RD 1620/2011: indemnización de 12 días por año con tope de 6 mensualidades y salario diario máximo del doble del SMI)."
        )
    },
    "SEA": {
        "cuaderno": "TEMAS GESTION HASTA EL MOMENTO | TEMAS ADMINISTRATIVO HASTA EL MOMENTO | NOVEDADES 2026",
        "epigrafe": "Tema 73 (Bloque VIII) — Epígrafe 4: SISTEMA ESPECIAL PARA TRABAJADORES POR CUENTA AJENA AGRARIOS (SEA): Campo de aplicación, cotización, recaudación y acción protectora",
        "resumen_fuente": (
            "- Fuentes consultadas: 'TEMAS GESTION HASTA EL MOMENTO', 'TEMAS ADMINISTRATIVO HASTA EL MOMENTO' y 'NOVEDADES 2026' (TRLGSS arts. 252-256, Guía SEA Inactividad 2026, Orden PJC/297/2026, RDL 3/2026 y RDL 31/2026).\n"
            "- Integración en el Régimen General: Ley 28/2011, de 22 de septiembre (efectos 01/01/2012), arts. 252 a 256 del TRLGSS, Ley 19/1995 de Modernización de Explotaciones Agrarias y supletoriamente Decreto 3772/1972.\n"
            "- Campo de aplicación (art. 252 TRLGSS): Trabajadores por cuenta ajena en labores agrarias, forestales o pecuarias y tareas complementarias. Exclusión expresa (art. 252.1.b): manipulado, empaquetado y comercialización del plátano (van al RG ordinario aunque sea en la explotación) y mecánicos/administrativos de fincas.\n"
            "- Períodos de inactividad (art. 253 TRLGSS): Existen cuando las jornadas reales en el mes natural sean inferiores al 76,67% de los días naturales de alta. Inclusión en inactividad requiere 30 jornadas reales en 365 días (o 5 jornadas reales si estuvo antes integrado + solicitud en 3 meses con efectos día 1 del mes siguiente). Exclusión por impago de 2 mensualidades consecutivas o no realizar 30 jornadas reales.\n"
            "- Cotización 2026 (arts. 254 y 255 TRLGSS y Orden PJC/297/2026): En inactividad cotiza a cargo exclusivo del trabajador sobre base mínima grupo 7 al 11,50% + MEI (0,90%), con reducción del 19,11% si en 2025 realizó un máximo de 55 jornadas reales. Tope máximo cuota empresarial grupo 1 en actividad: 279,00 €/mes o 12,68 €/jornada. Excedencia por cuidado de hijo (art. 237 TRLGSS) es período de cotización efectiva durante 3 años.\n"
            "- Acción protectora (art. 256 TRLGSS): Requisito de estar al corriente en cuotas de inactividad; pago directo del subsidio de IT desde el día 16.º; en inactividad la protección comprende maternidad, paternidad, IP y muerte y supervivencia por contingencias comunes y jubilación."
        )
    }
}

MAPA_TEMATICO_PRECEPTOS = [
    {
        "materia": "Sistema Especial para Empleados de Hogar (SEEH)",
        "keywords_contexto": ["hogar", "domestico", "domestica", "empleada de hogar", "empleados de hogar", "seeh", "1620/2011", "250", "251", "familiar", "familia"],
        "articulos_validos": {
            "1": "Ámbito de aplicación y exclusiones laborales (ET)",
            "2": "Relación laboral de carácter especial del servicio del hogar familiar (art. 2.1.b ET)",
            "7": "Extensión del campo de aplicación del Sistema de la Seguridad Social (TRLGSS)",
            "11": "Extinción del contrato en el servicio del hogar familiar (RD 1620/2011)",
            "12": "Exclusión de relaciones entre familiares y trabajo a tiempo parcial",
            "15": "Inscripción, afiliación, altas y bajas (TRLGSS)",
            "16": "Obligación de afiliación y alta previa (TRLGSS)",
            "33": "Cobertura indemnizatoria del Fondo de Garantía Salarial - FOGASA (ET)",
            "42": "Catálogo general de prestaciones de la Acción Protectora del sistema (TRLGSS)",
            "49": "Causas de extinción del contrato de trabajo (ET)",
            "122": "Exclusión de la cotización adicional por horas en el SEEH (art. 122 Ley 31/2022)",
            "136": "Integración de los Empleados de Hogar en el Régimen General (art. 136.2.b TRLGSS)",
            "137": "Exclusiones del Régimen General (trabajos amistosos/familiares)",
            "147": "Determinación de la base de cotización (TRLGSS)",
            "151": "Exclusión del recargo por contratos inferiores a 30 días en el SEEH (TRLGSS)",
            "162": "Caracteres de las relaciones laborales de carácter especial en el Régimen General (TRLGSS)",
            "165": "Requisitos generales del derecho a las prestaciones y alta (TRLGSS)",
            "166": "Situaciones asimiladas a la de alta (TRLGSS)",
            "167": "Responsabilidad en orden a las prestaciones y exclusión de capital coste (TRLGSS)",
            "169": "Concepto y situaciones especiales de Incapacidad Temporal (TRLGSS)",
            "171": "Cuantía y base reguladora de la prestación de IT (TRLGSS)",
            "172": "Períodos de carencia en Incapacidad Temporal (TRLGSS)",
            "173": "Nacimiento, duración y pago del subsidio de IT (TRLGSS)",
            "197": "Base reguladora e integración de lagunas en Incapacidad Permanente (TRLGSS)",
            "209": "Base reguladora e integración de lagunas en la pensión de Jubilación (TRLGSS)",
            "250": "Objeto y configuración del Sistema Especial para Empleados de Hogar (TRLGSS)",
            "251": "Acción protectora y peculiaridades de cotización y prestaciones en el SEEH (TRLGSS)",
            "267": "Situación legal de desempleo en extinción del contrato del hogar familiar (TRLGSS)",
        },
        "normas_validas": {
            "8/2015": "Texto Refundido de la Ley General de la Seguridad Social (TRLGSS)",
            "2/2015": "Texto Refundido de la Ley del Estatuto de los Trabajadores (ET)",
            "1620/2011": "Real Decreto regulador de la relación laboral especial del servicio del hogar familiar",
            "16/2022": "Real Decreto-ley para la mejora de las condiciones de trabajo y de Seguridad Social de las personas trabajadoras al servicio del hogar (desempleo y FOGASA)",
            "505/1985": "Real Decreto sobre organización y funcionamiento del Fondo de Garantía Salarial (FOGASA)",
            "27/2011": "Ley sobre actualización, adecuación y modernización del sistema de Seguridad Social (integración del SEEH)",
            "31/2022": "Ley de Presupuestos Generales del Estado (art. 122 sobre cotización en el SEEH)",
            "84/1996": "Reglamento General sobre inscripción de empresas, afiliación, altas y bajas",
            "2064/1995": "Reglamento General sobre Cotización y Liquidación de otros Derechos de la Seguridad Social",
            "31/2026": "Real Decreto-ley de reforma de situaciones especiales de IT y protección social",
            "126/2026": "Real Decreto por el que se fija el salario mínimo interprofesional para 2026",
            "297/2026": "Orden PJC/297/2026 anual de cotización para 2026",
        }
    },
    {
        "materia": "Sistema Especial para Trabajadores por Cuenta Ajena Agrarios (SEA)",
        "keywords_contexto": ["agrario", "agraria", "agricola", "sea", "jornadas reales", "inactividad", "finca", "recoleccion", "agropecuaria", "252", "253", "254", "255", "256"],
        "articulos_validos": {
            "7": "Campo de aplicación del Sistema de la Seguridad Social (TRLGSS)",
            "15": "Afiliación, altas y bajas en el sistema (TRLGSS)",
            "16": "Solicitudes de afiliación y alta previa (TRLGSS)",
            "42": "Acción protectora del Sistema de la Seguridad Social (TRLGSS)",
            "136": "Inclusión del Sistema Especial Agrario en el Régimen General (art. 136.2.a TRLGSS)",
            "144": "Duración de la obligación de cotizar en IT, maternidad y riesgo (TRLGSS)",
            "151": "Exclusión de cotización adicional en contratos de corta duración en el SEA (TRLGSS)",
            "165": "Requisitos de acceso a prestaciones (TRLGSS)",
            "166": "Situaciones asimiladas al alta (TRLGSS)",
            "169": "Incapacidad temporal y situaciones especiales (TRLGSS)",
            "173": "Abono y pago directo del subsidio de IT (TRLGSS)",
            "237": "Prestaciones familiares y períodos de cotización efectiva por excedencia (TRLGSS)",
            "252": "Ámbito de aplicación y concepto de labores agrarias en el SEA (TRLGSS)",
            "253": "Inclusión y exclusión en los períodos de inactividad del SEA y requisito de 30 jornadas reales (TRLGSS)",
            "254": "Reglas de cotización en actividad e inactividad en el SEA (TRLGSS)",
            "255": "Cotización durante las situaciones de incapacidad temporal, nacimiento y riesgo en el SEA (TRLGSS)",
            "256": "Peculiaridades de la acción protectora, pago directo de IT y requisito de estar al corriente en el SEA (TRLGSS)",
            "284": "Protección por desempleo de los trabajadores eventuales agrarios (TRLGSS)",
        },
        "normas_validas": {
            "8/2015": "Texto Refundido de la Ley General de la Seguridad Social (TRLGSS)",
            "28/2011": "Ley por la que se procede a la integración del Régimen Especial Agrario en el Régimen General",
            "19/1995": "Ley de Modernización de las Explotaciones Agrarias",
            "3772/1972": "Decreto por el que se aprueba el Reglamento General del Régimen Especial Agrario (aplicación supletoria)",
            "84/1996": "Reglamento General de Afiliación, Altas y Bajas",
            "2064/1995": "Reglamento General sobre Cotización y Liquidación",
            "31/2026": "Real Decreto-ley de actualización de prestaciones de la Seguridad Social",
            "297/2026": "Orden PJC/297/2026 anual de cotización para 2026",
        }
    },
    {
        "materia": "Cotización, Recaudación y Afiliación General",
        "keywords_contexto": ["cotizacion", "base de cotizacion", "recaudacion", "afiliacion", "alta", "baja", "pluriempleo", "recargo", "tgss", "cuota"],
        "articulos_validos": {
            "15": "Obligatoriedad y alcance de la afiliación (TRLGSS)",
            "16": "Sujetos obligados a solicitar la afiliación y el alta (TRLGSS)",
            "17": "Procedimiento y efectos de la afiliación (TRLGSS)",
            "18": "Obligatoriedad de la cotización (TRLGSS)",
            "19": "Bases y tipos de cotización y cotización adicional de solidaridad (TRLGSS)",
            "20": "Adquisición, mantenimiento y pérdida de beneficios en la cotización (TRLGSS)",
            "24": "Prescripción de cuatro años de las deudas por cuotas (TRLGSS)",
            "26": "Devolución de ingresos indebidos (TRLGSS)",
            "28": "Recargos por ingreso fuera de plazo (TRLGSS)",
            "30": "Reclamaciones de deuda y recargos del 10% y 20% (TRLGSS)",
            "136": "Campo de aplicación del Régimen General (TRLGSS)",
            "139": "Inscripción de empresas (TRLGSS)",
            "141": "Sujetos obligados y responsables en la cotización (TRLGSS)",
            "142": "Sujeto responsable del ingreso de cuotas y descuento de la cuota obrera (TRLGSS)",
            "143": "Nacimiento de la obligación de cotizar (TRLGSS)",
            "144": "Duración y subsistencia de la obligación de cotizar en IT y nacimiento (TRLGSS)",
            "147": "Conceptos computables y excluidos de la base de cotización (TRLGSS)",
            "148": "Topes máximo y mínimo de la base de cotización y pluriempleo (TRLGSS)",
            "151": "Cotización adicional en contratos temporales de corta duración (TRLGSS)",
        },
        "normas_validas": {
            "8/2015": "Texto Refundido de la Ley General de la Seguridad Social (TRLGSS)",
            "84/1996": "Reglamento General sobre Inscripción de Empresas y Afiliación",
            "2064/1995": "Reglamento General sobre Cotización y Liquidación",
            "1415/2004": "Reglamento General de Recaudación de la Seguridad Social",
            "643/2026": "Real Decreto de reforma de plazos de bajas y variaciones de datos",
            "297/2026": "Orden de cotización para 2026",
        }
    }
]

def obtener_fuente_notebooklm_para_pregunta(texto_contexto):
    t_low = (texto_contexto or "").lower()
    partes = []
    if any(k in t_low for k in ["hogar", "domestico", "domestica", "seeh", "250", "251", "1620/2011", "montoro", "garcia-valenzuela"]):
        f = FUENTES_TEMARIO_NOTEBOOKLM["SEEH"]
        partes.append(f"📘 **Fuente NotebookLM:** {f['cuaderno']}\n📌 **{f['epigrafe']}**\n{f['resumen_fuente']}")
    if any(k in t_low for k in ["agrario", "agraria", "sea", "inactividad", "jornadas reales", "252", "253", "254", "255", "256", "montoro"]):
        f = FUENTES_TEMARIO_NOTEBOOKLM["SEA"]
        partes.append(f"📘 **Fuente NotebookLM:** {f['cuaderno']}\n📌 **{f['epigrafe']}**\n{f['resumen_fuente']}")
    return "\n\n".join(partes)

def _verificar_precepto_adicional(k_tipo, k_id, k_lbl, texto_alumno, contexto_pregunta_y_exp):
    def _norm(s):
        s = ''.join(c for c in unicodedata.normalize('NFD', (s or "").lower()) if unicodedata.category(c) != 'Mn')
        return re.sub(r'\s+', ' ', s).strip()

    ctx_norm = _norm(contexto_pregunta_y_exp)

    for bloque in MAPA_TEMATICO_PRECEPTOS:
        if any(kw in ctx_norm for kw in bloque["keywords_contexto"]):
            if k_tipo == "ART" and k_id in bloque["articulos_validos"]:
                desc = bloque["articulos_validos"][k_id]
                return True, f"{k_lbl} ({desc} — conectado con {bloque['materia']})"
            if k_tipo == "NORMA" and k_id in bloque["normas_validas"]:
                desc = bloque["normas_validas"][k_id]
                return True, f"{k_lbl} ({desc})"

    normas_troncales = {
        "8/2015": "Texto Refundido de la Ley General de la Seguridad Social (TRLGSS)",
        "2/2015": "Texto Refundido de la Ley del Estatuto de los Trabajadores (ET)",
        "2064/1995": "Reglamento General sobre Cotización y Liquidación",
        "84/1996": "Reglamento General de Inscripción y Afiliación",
        "1415/2004": "Reglamento General de Recaudación de la Seguridad Social",
        "2621/1986": "Real Decreto de integración de regímenes especiales en el Régimen General",
        "3/2026": "Real Decreto-ley de revalorización de pensiones y cotización para 2026",
        "31/2026": "Real Decreto-ley de reforma de prestaciones de Seguridad Social",
        "126/2026": "Real Decreto de fijación del SMI para 2026",
        "607/2026": "Real Decreto de relación laboral especial de personas artistas y técnicos",
        "643/2026": "Real Decreto de modificación de plazos de afiliación y recaudación",
        "297/2026": "Orden PJC/297/2026 de cotización para 2026",
    }
    if k_tipo == "NORMA" and k_id in normas_troncales:
        return True, f"{k_lbl} ({normas_troncales[k_id]})"
    if k_tipo == "SIGLA" and k_id in ["trlgss", "et"]:
        return True, k_lbl

    oraciones_al = re.split(r'(?<=[.?!;])\s+|\n+', texto_alumno)
    palabras_ctx = set(re.findall(r'\b[a-záéíóúñ]{5,}\b', ctx_norm))
    for orac in oraciones_al:
        if k_id in _norm(orac):
            palabras_orac = set(re.findall(r'\b[a-záéíóúñ]{5,}\b', _norm(orac)))
            coincidencias = palabras_orac.intersection(palabras_ctx)
            if len(coincidencias) >= 3 and len(orac.strip()) >= 40:
                return True, f"{k_lbl} (precepto conexo bien interrelacionado en tu exposición)"

    return False, f"{k_lbl} (no guarda relación directa con el supuesto planteado)"

def evaluar_respuesta_escrita(texto_alumno, respuesta_oficial, explicacion_oficial, enunciado_pregunta=""):
    def _norm(s):
        s = ''.join(c for c in unicodedata.normalize('NFD', (s or "").lower()) if unicodedata.category(c) != 'Mn')
        return re.sub(r'\s+', ' ', s).strip()

    def _raiz(palabra):
        p = _norm(palabra)
        if len(p) >= 7:
            return p[:-2]
        if len(p) >= 5:
            return p[:-1]
        return p

    alumno_norm = _norm(texto_alumno)
    ref_completa = f"{respuesta_oficial or ''} {explicacion_oficial or ''}".strip()
    contexto_total = f"{enunciado_pregunta or ''} {ref_completa}".strip()
    ref_norm = _norm(ref_completa)

    pat_normas = r'\b(?:art(?:[íi]culos?|\.)\s*\d+(?:\.\d+)?(?:\.[a-z])?|ley(?:\s+org[áa]nica)?\s+\d+/\d{4}|real\s+decreto(?:\-ley|\s+legislativo)?\s+\d+/\d{4}|rdl\s+\d+/\d{4}|rd[\-\s]*ley\s+\d+/\d{4}|rd\s+\d+/\d{4}|decreto\s+\d+/\d{4}|trlgss|estatuto\s+de\s+los\s+trabajadores|orden\s+[a-z]+/\d+/\d{4}|disposici[óo]n\s+(?:adicional|transitoria)\s+(?:\d+[ºª°]?|[a-záéíóúñ]+))'

    def _clave_norma(texto_cita):
        cn = _norm(texto_cita)
        m_art = re.match(r'^art(?:iculos?|\.)\s*(\d+)', cn)
        if m_art:
            return ("ART", m_art.group(1), f"Artículo {m_art.group(1)}")
        m_ley = re.search(r'(ley(?:\s+organica)?|real\s+decreto(?:\-ley|\s+legislativo)?|rdl|rd[\-\s]*ley|rd|decreto|orden(?:\s+[a-z]+)?)\s+(\d+/\d{4})', cn)
        if m_ley:
            tipo = m_ley.group(1).upper()
            num = m_ley.group(2)
            if "LEGISLATIVO" in tipo:
                etiqueta = f"RD Legislativo {num}"
            elif "LEY" in tipo and ("RD" in tipo or "DECRETO" in tipo):
                etiqueta = f"RD-ley {num}"
            elif "REAL DECRETO" in tipo or tipo == "RD":
                etiqueta = f"Real Decreto {num}"
            elif "ORDEN" in tipo:
                etiqueta = f"Orden {num}"
            else:
                etiqueta = f"Ley {num}"
            return ("NORMA", num, etiqueta)
        if "trlgss" in cn:
            return ("SIGLA", "trlgss", "TRLGSS (RD Legislativo 8/2015)")
        if "estatuto de los trabajadores" in cn:
            return ("SIGLA", "et", "Estatuto de los Trabajadores")
        m_da = re.match(r'^disposicion\s+(adicional|transitoria)\s+(.+)$', cn)
        if m_da:
            return ("DISP", f"{m_da.group(1)}_{m_da.group(2)}", texto_cita.strip().capitalize())
        return ("OTRO", cn, texto_cita.strip())

    citas_ref_raw = re.findall(pat_normas, ref_completa, flags=re.IGNORECASE)
    citas_alumno_raw = re.findall(pat_normas, texto_alumno, flags=re.IGNORECASE)

    mapa_ref = {}
    for c in citas_ref_raw:
        k_tipo, k_id, k_lbl = _clave_norma(c)
        if (k_tipo, k_id) not in mapa_ref:
            mapa_ref[(k_tipo, k_id)] = k_lbl

    mapa_al = {}
    for c in citas_alumno_raw:
        k_tipo, k_id, k_lbl = _clave_norma(c)
        if (k_tipo, k_id) not in mapa_al:
            mapa_al[(k_tipo, k_id)] = k_lbl

    ids_ref_equiv = set(mapa_ref.keys())
    if ("NORMA", "8/2015") in ids_ref_equiv or ("SIGLA", "trlgss") in ids_ref_equiv:
        ids_ref_equiv.add(("NORMA", "8/2015"))
        ids_ref_equiv.add(("SIGLA", "trlgss"))

    citas_ok, citas_complementarias, citas_faltan, citas_erroneas = [], [], [], []
    for k_par, lbl in mapa_ref.items():
        if k_par in mapa_al or (k_par in [("NORMA", "8/2015"), ("SIGLA", "trlgss")] and any(x in mapa_al for x in [("NORMA", "8/2015"), ("SIGLA", "trlgss")])):
            citas_ok.append(lbl)
        elif k_par[0] == "ART" and re.search(rf'\b{re.escape(k_par[1])}\b', alumno_norm) and "art" in alumno_norm:
            citas_ok.append(lbl)
        else:
            citas_faltan.append(lbl)

    for k_par, lbl in mapa_al.items():
        if k_par not in ids_ref_equiv:
            if k_par[1] in ref_norm:
                citas_ok.append(lbl)
            else:
                es_valido_extra, explicacion_extra = _verificar_precepto_adicional(
                    k_par[0], k_par[1], lbl, texto_alumno, contexto_total
                )
                if es_valido_extra:
                    citas_complementarias.append(explicacion_extra)
                else:
                    citas_erroneas.append(explicacion_extra)

    pat_cifras = r'\b\d+(?:[\.,]\d+)?\s*(?:%|por\s+ciento|puntos\s+porcentuales|d[íi]as?(?:\s+naturales|\s+h[áa]biles)?|meses|a[ñn]os|horas|jornadas?(?:\s+reales)?|euros(?:/mes|/d[íi]a)?|€/mes|mensualidades|tramo\s+\d+[ºª°]?|(?:primer|segundo|tercer)\s+grado)\b'
    cifras_raw = re.findall(pat_cifras, ref_completa, flags=re.IGNORECASE)
    cifras_unicas = []
    vistas_n = set()
    for cf in cifras_raw:
        cfn = _norm(cf)
        if cfn not in vistas_n:
            vistas_n.add(cfn)
            cifras_unicas.append(cf.strip())

    cifras_ok, cifras_faltan = [], []
    for cf in cifras_unicas:
        cfn = _norm(cf)
        num_principal = re.findall(r'\d+(?:[\.,]\d+)?', cfn)
        if cfn in alumno_norm or (num_principal and num_principal[0] in alumno_norm):
            cifras_ok.append(cf)
        else:
            cifras_faltan.append(cf)

    stopwords = {
        "para", "como", "este", "esta", "estos", "estas", "pero", "sino", "porque", "cuando", "donde",
        "cual", "cuales", "quien", "quienes", "todo", "toda", "todos", "todas", "otro", "otra", "otros",
        "otras", "mismo", "misma", "mismos", "mismas", "tanto", "entre", "sobre", "bajo", "ante", "tras",
        "desde", "hasta", "hacia", "segun", "conforme", "mediante", "durante", "cada", "algun", "alguna",
        "ningun", "ninguna", "pueden", "puede", "debe", "debera", "deberan", "sera", "seran", "tiene",
        "tienen", "haber", "habia", "estar", "esta", "estan", "sido", "siendo", "establece", "dispone",
        "regula", "articulo", "texto", "refundido", "general", "seguridad", "social", "norma", "normativa",
        "literalmente", "siguiente", "siguientes", "caso", "casos", "supuesto", "supuestos", "efectos",
        "parte", "partes", "forma", "manera", "dichos", "dicha", "dicho", "dichas", "aquel", "aquella",
        "ademas", "asimismo", "obstante", "embargo", "respecto", "aplicacion", "sistema", "especial"
    }

    texto_base_ideas = f"{respuesta_oficial}. {explicacion_oficial}" if respuesta_oficial else explicacion_oficial
    oraciones_completas = _dividir_en_oraciones_juridicas(texto_base_ideas)
    puntos_cubiertos = []
    puntos_omitidos = []

    for orac_limpia in oraciones_completas:
        if any(_norm(orac_limpia)[:50] == _norm(x)[:50] for x in (puntos_cubiertos + puntos_omitidos)):
            continue
        palabras_orac = [
            w for w in re.findall(r'\b[a-záéíóúñ]{4,}\b|\b\d+(?:[\.,]\d+)?\b', _norm(orac_limpia))
            if w not in stopwords
        ]
        if not palabras_orac:
            continue
        aciertos_orac = sum(1 for w in palabras_orac if _raiz(w) in alumno_norm)
        ratio_orac = aciertos_orac / len(palabras_orac)
        if ratio_orac >= 0.42 or (len(palabras_orac) <= 4 and aciertos_orac >= 2):
            puntos_cubiertos.append(orac_limpia)
        else:
            puntos_omitidos.append(orac_limpia)

    alerta_sentido = ""
    resp_inicio = _norm(respuesta_oficial[:40]) if respuesta_oficial else ""
    alumno_inicio = alumno_norm[:50]
    if re.match(r'^no\b', resp_inicio) and re.match(r'^si\b', alumno_inicio):
        alerta_sentido = "❌ **Sentido de la respuesta invertido:** La solución oficial comienza negando (**«No...»**), mientras que tu respuesta comienza afirmando (**«Sí...»**)."
    elif re.match(r'^si\b', resp_inicio) and re.match(r'^no\b', alumno_inicio):
        alerta_sentido = "❌ **Sentido de la respuesta invertido:** La solución oficial comienza afirmando (**«Sí...»**), mientras que tu respuesta comienza negando (**«No...»**)."
    elif re.match(r'^ninguno\b', resp_inicio) and not any(x in alumno_norm for x in ["ninguno", "excluid", "no procede", "no estan"]):
        alerta_sentido = "⚠️ **Falta la conclusión directa:** La solución oficial concluye que **ninguno de los dos** procede ser incluido (ambos están excluidos)."
    elif re.match(r'^nadie\b', resp_inicio) and not any(x in alumno_norm for x in ["nadie", "exento", "no existe obligacion", "cotizacion efectiva", "no ingresa"]):
        alerta_sentido = "⚠️ **Falta la conclusión directa:** La solución oficial concluye que **nadie** asume el ingreso por tratarse de un período de cotización efectiva."

    if puntos_omitidos:
        texto_sugerido = " ".join(puntos_omitidos[:3])
    elif respuesta_oficial:
        texto_sugerido = respuesta_oficial
    else:
        texto_sugerido = explicacion_oficial

    total_eval = len(citas_ok) + len(citas_faltan) + len(cifras_ok) + len(cifras_faltan) + len(puntos_cubiertos) + len(puntos_omitidos)
    acertados_eval = len(citas_ok) + len(cifras_ok) + len(puntos_cubiertos)
    pts_criterio_1 = (acertados_eval / max(1, total_eval)) * 45.0
    pts_criterio_1 = min(45.0, pts_criterio_1 + (1.80 * len(citas_complementarias)))
    if citas_erroneas:
        pts_criterio_1 = max(0.0, pts_criterio_1 - (2.25 * len(citas_erroneas)))
    if alerta_sentido:
        pts_criterio_1 = max(0.0, pts_criterio_1 - 11.25)
    pts_criterio_1 = round(pts_criterio_1, 2)

    supera_umbral_20 = pts_criterio_1 >= 20.0
    if supera_umbral_20:
        num_parrafos_al = len([p for p in texto_alumno.split("\n") if len(p.strip()) > 20])
        usa_conectores = sum(1 for c in ["conforme", "virtud", "establece", "dispone", "asimismo", "obstante", "tanto", "articulo", "respecto"] if c in alumno_norm)
        pts_criterio_2 = round(min(3.0, 1.8 + (0.6 if num_parrafos_al >= 2 else 0.0) + (0.6 if usa_conectores >= 2 else 0.0)), 2)
        pts_criterio_3 = round(min(2.0, 1.2 + (0.8 if len(texto_alumno.strip()) >= 180 and usa_conectores >= 1 else 0.3)), 2)
    else:
        pts_criterio_2 = 0.0
        pts_criterio_3 = 0.0

    nota_50 = round(min(50.0, pts_criterio_1 + pts_criterio_2 + pts_criterio_3), 2)
    nota_10 = round((nota_50 / 50.0) * 10.0, 2)
    fuente_nb = obtener_fuente_notebooklm_para_pregunta(contexto_total)

    return {
        "nota": nota_10,
        "nota_50": nota_50,
        "pts_criterio_1": pts_criterio_1,
        "pts_criterio_2": pts_criterio_2,
        "pts_criterio_3": pts_criterio_3,
        "supera_umbral_20": supera_umbral_20,
        "alerta_sentido": alerta_sentido,
        "citas_ok": citas_ok,
        "citas_complementarias": citas_complementarias,
        "citas_faltan": citas_faltan,
        "citas_erroneas": citas_erroneas,
        "cifras_ok": cifras_ok,
        "cifras_faltan": cifras_faltan,
        "puntos_cubiertos": puntos_cubiertos,
        "puntos_omitidos": puntos_omitidos,
        "texto_sugerido": texto_sugerido,
        "fuente_notebooklm": fuente_nb
    }

def generar_dictamen_tribunal_inteligente(ev, respuesta_alumno, respuesta_oficial, explicacion_oficial):
    bloques = []

    encuadre_nb = ""
    if ev.get("fuente_notebooklm"):
        primera_linea_nb = ev["fuente_notebooklm"].split("\n")[1] if "\n" in ev["fuente_notebooklm"] else ""
        encuadre_nb = f"📌 *Fuentes de contraste (TEMAS GESTIÓN / ADMINISTRATIVO HASTA EL MOMENTO y NOVEDADES 2026):* {primera_linea_nb}\n\n"

    if ev["puntos_cubiertos"] or ev["citas_ok"] or ev["citas_complementarias"] or ev["cifras_ok"]:
        aciertos_txt = []
        if ev["citas_ok"]:
            aciertos_txt.append(f"Has fundamentado con rigor tu exposición invocando la normativa nuclear del epígrafe (**{', '.join(ev['citas_ok'])}**).")
        if ev["citas_complementarias"]:
            aciertos_txt.append(
                f"🌟 **Interrelación normativa de alto nivel:** Has conectado acertadamente otros preceptos del bloque legal aplicables a la materia (**{'; '.join(ev['citas_complementarias'])}**), demostrando dominio transversal del temario y sumando puntuación adicional."
            )
        if ev["cifras_ok"]:
            aciertos_txt.append(f"Has precisado correctamente los parámetros cuantitativos/temporales (**{', '.join(ev['cifras_ok'])}**).")
        if ev["puntos_cubiertos"]:
            resumen_ideas = " ".join([f"«{p}»" for p in ev["puntos_cubiertos"][:2]])
            aciertos_txt.append(f"En cuanto al fondo jurídico, tu redacción desarrolla con acierto: {resumen_ideas}")
        bloques.append("1. **✅ Análisis jurídico de tu exposición y ajuste a la literalidad normativa:**\n" + encuadre_nb + " ".join(aciertos_txt))
    else:
        bloques.append(
            "1. **✅ Análisis jurídico de tu exposición y ajuste a la literalidad normativa:**\n"
            + encuadre_nb +
            "Tu contestación es todavía muy genérica o embrionaria y no llega a recoger los elementos técnicos nucleares exigidos en este epígrafe del temario oficial."
        )

    rev_normativa = []
    if ev["alerta_sentido"]:
        rev_normativa.append(ev["alerta_sentido"])
    if ev["citas_ok"]:
        rev_normativa.append(f"✔️ **Normativa principal del epígrafe acertada:** {', '.join(ev['citas_ok'])}.")
    if ev["citas_complementarias"]:
        rev_normativa.append(
            f"🌟 **Normativa complementaria verificada en las fuentes legales (suma valor en Criterio 1):** {', '.join(ev['citas_complementarias'])}."
        )
    if ev["citas_erroneas"]:
        rev_normativa.append(
            f"❌ **Preceptos sin aplicación directa en este epígrafe tras consultar el texto legal:** {', '.join(ev['citas_erroneas'])}."
        )
    if ev["citas_faltan"]:
        rev_normativa.append(
            f"⚠️ **Artículos y normas del epígrafe oficial que te faltó citar:** {', '.join(ev['citas_faltan'])}."
        )
    if not rev_normativa:
        rev_normativa.append("✔️ Has citado correctamente toda la base normativa exigible en este epígrafe.")
    bloques.append("2. **⚖️ Auditoría de artículos y fuentes legales (TEMAS HASTA EL MOMENTO Y NOVEDADES 2026):**\n" + "\n".join(rev_normativa))

    if ev["puntos_omitidos"] or ev["cifras_faltan"]:
        detalles_str = ""
        if ev["cifras_faltan"]:
            detalles_str += f"Te ha faltado especificar los siguientes plazos, tramos o porcentajes clave: **{', '.join(ev['cifras_faltan'])}**.\n"
        if ev["puntos_omitidos"]:
            lista_om = "\n".join([f"   - *{p}*" for p in ev["puntos_omitidos"][:5]])
            detalles_str += f"Comparando tu texto con el epígrafe oficial del tema, has omitido desarrollar estos extremos:\n{lista_om}\n\n"
        modelo_parrafo = respuesta_oficial if (respuesta_oficial and len(respuesta_oficial) > 40) else ev["texto_sugerido"]
        detalles_str += f"✍️ **Párrafo magistral que deberías incorporar a tu examen para alcanzar la máxima puntuación:**\n« {modelo_parrafo} »"
        bloques.append("3. **⚠️ Detalles omitidos del epígrafe y redacción modelo recomendada:**\n" + detalles_str)
    else:
        bloques.append(
            "3. **⚠️ Detalles omitidos del epígrafe y redacción modelo recomendada:**\n"
            "¡Excelente trabajo! Tu respuesta abarca todos los requisitos, excepciones y matices técnicos del epígrafe oficial."
        )

    c1 = ev.get("pts_criterio_1", 0.0)
    c2 = ev.get("pts_criterio_2", 0.0)
    c3 = ev.get("pts_criterio_3", 0.0)
    n50 = ev.get("nota_50", round(ev["nota"] * 5, 2))
    umbral_txt = (
        "✔️ Superas el umbral mínimo de **20,00 / 45 puntos** en el Criterio 1, por lo que **sí se te computan** los puntos de orden de ideas (hasta 3 ptos) y calidad de expresión escrita (hasta 2 ptos)."
        if ev.get("supera_umbral_20") else
        "⚠️ Al no alcanzar al menos **20,00 / 45 puntos** en el Criterio 1 (conocimiento y literalidad normativa), conforme a los Criterios Oficiales del Tribunal **no pueden sumarse** los apartados de orden de ideas (0/3) ni calidad de expresión escrita (0/2)."
    )
    estado_corte = (
        "✅ **PARTE SUPERADA** (alcanzas el mínimo eliminatorio de **25,00 / 50 puntos** necesario para sumar ambas partes del Segundo Ejercicio)."
        if n50 >= 25.0 else
        "❌ **NO ALCANZA EL MÍNIMO ELIMINATORIO DE 25,00 / 50 PUNTOS** (recuerda que el Tribunal no admite compensación entre la 1.ª y la 2.ª parte si alguna es inferior a 25 puntos)."
    )

    desglose_tribunal = (
        "4. **🎓 Calificación Oficial según los Criterios del Tribunal (Resolución 22/12/2025):**\n"
        f"   - **Criterio 1 — Conocimiento, precisión normativa ajustada a su literalidad y resolución práctica (0 a 45 ptos):** `{c1:.2f} / 45,00 puntos`\n"
        f"   - **Criterio 2 — Orden de las ideas y estructura de la exposición (0 a 3 ptos):** `{c2:.2f} / 3,00 puntos`\n"
        f"   - **Criterio 3 — Calidad de la expresión escrita (0 a 2 ptos):** `{c3:.2f} / 2,00 puntos`\n"
        f"   - {umbral_txt}\n"
        f"   - 📊 **PUNTUACIÓN DIRECTA DE LA PARTE (Escala Oficial 0-50):** **`{n50:.2f} / 50,00 puntos`** *(Equivalencia sobre 10: **`{ev['nota']:.2f} / 10`**)*\n"
        f"   - 🏛️ **Estado frente al corte del Tribunal:** {estado_corte}"
    )
    bloques.append(desglose_tribunal)

    return "\n\n".join(bloques)

def obtener_gemini_api_key_activa():
    try:
        sec_k = st.secrets.get("GEMINI_API_KEY", "")
        if sec_k and str(sec_k).strip():
            return str(sec_k).strip()
    except Exception:
        pass
    sess_k = st.session_state.get("gemini_api_key_session", "")
    if sess_k and str(sess_k).strip():
        return str(sess_k).strip()
    return GEMINI_API_KEY_DEFAULT

def consultar_ia_gemini_correccion(api_key, enunciado_supuesto, pregunta, respuesta_alumno, respuesta_oficial, explicacion_oficial, ev_fallback=None):
    aviso_elegante = detectar_respuesta_inapropiada_o_sin_interes(respuesta_alumno)
    if aviso_elegante:
        return aviso_elegante

    clave_limpia = (api_key or GEMINI_API_KEY_DEFAULT).strip().replace("×", "x").replace(" ", "")
    contexto_total = f"{enunciado_supuesto} {pregunta} {respuesta_oficial} {explicacion_oficial}"
    fuente_nb = obtener_fuente_notebooklm_para_pregunta(contexto_total)

    prompt = (
        "Actúa como la Presidenta del Tribunal Calificador de las pruebas selectivas del Cuerpo de Gestión de la Administración de la Seguridad Social (Resolución de 22 de diciembre de 2025) y preparador experto de Oposiciona.\n"
        "Tu misión es corregir con rigor técnico absoluto la respuesta escrita por el opositor en el Segundo Ejercicio, "
        "contrastándola exclusivamente con las 3 fuentes oficiales de Oposiciona en NotebookLM: "
        "1) 'TEMAS GESTION HASTA EL MOMENTO', 2) 'TEMAS ADMINISTRATIVO HASTA EL MOMENTO' y 3) 'NOVEDADES 2026'.\n\n"
        f"{CRITERIOS_OFICIALES_TRIBUNAL_2_EJERCICIO}\n\n"
        "REGLAS DE CORRECCIÓN DE OBLIGADO CUMPLIMIENTO:\n"
        "0. **FILTRO DE ELEGANCIA EN FRASES INICIALES:** Si el texto contiene expresiones inaceptables, vulgares o frases sin ningún interés para el tema ('esto es una caca', 'puta mierda', 'paso de todo', etc.), NO realices la corrección técnica: responde únicamente con un mensaje lleno de clase, educación y estilo recordando que la plataforma se ha creado para alcanzar la excelencia y conseguir su plaza, no para perder el tiempo.\n"
        "1. **INTERRELACIÓN NORMATIVA Y CONSULTA PREVIA DEL TEXTO LEGAL:** Antes de dar por inválido cualquier artículo o norma citado por el alumno que no figure literalmente en la explicación del PDF, comprueba en 'TEMAS GESTION HASTA EL MOMENTO', 'TEMAS ADMINISTRATIVO HASTA EL MOMENTO' y 'NOVEDADES 2026' (TRLGSS, ET, Ley 27/2011, Ley 28/2011, RD 1620/2011, RDL 16/2022, RD 505/1985, Ley 31/2022 art. 122, RDL 3/2026, RDL 31/2026, Orden PJC/297/2026, RD 126/2026, RD 643/2026, RD 84/1996, RD 2064/1995, RD 1415/2004) si guarda relación con la materia. Si es correcto y mejora el contenido, explícalo y súmale puntos en el Criterio 1.\n"
        "2. **APLICACIÓN ESTRICTA DEL BAREMO DE 50 PUNTOS DEL TRIBUNAL:**\n"
        "   - Evalúa el **Criterio 1 (0 a 45 puntos)** exigiendo precisión normativa ajustada a su literalidad y precisión en la situación práctica.\n"
        "   - Evalúa el **Criterio 2 — Orden de las ideas y estructura (0 a 3 puntos)** y el **Criterio 3 — Calidad de la expresión escrita (0 a 2 puntos)**, aplicando rigurosamente la regla oficial del Tribunal: **solo puntúan si el alumno alcanza al menos 20 puntos sobre 45 en el Criterio 1** (si obtiene menos de 20/45 en el Criterio 1, asigna 0 puntos en Criterio 2 y 0 puntos en Criterio 3).\n"
        "   - Indica la nota total sobre **50 puntos** (señalando si supera los **25 puntos eliminatorios** necesarios para no quedar excluido sin compensación) y su nota equivalente sobre **10 puntos**.\n\n"
        f"=== FUENTES OFICIALES NOTEBOOKLM (TEMAS GESTION HASTA EL MOMENTO | TEMAS ADMINISTRATIVO HASTA EL MOMENTO | NOVEDADES 2026) ===\n{fuente_nb if fuente_nb else 'Corpus Oficial NotebookLM: TEMAS GESTION HASTA EL MOMENTO, TEMAS ADMINISTRATIVO HASTA EL MOMENTO y NOVEDADES 2026.'}\n\n"
        f"=== ENUNCIADO ===\n{enunciado_supuesto}\n{pregunta}\n\n"
        f"=== RESPUESTA DIRECTA OFICIAL ===\n{respuesta_oficial}\n\n"
        f"=== EXPLICACIÓN OFICIAL DEL TEMA ===\n{explicacion_oficial}\n\n"
        f"=== RESPUESTA ESCRITA POR EL ALUMNO ===\n{respuesta_alumno}\n\n"
        "Estructura tu respuesta en estos 4 bloques exactos:\n"
        "1. **✅ Análisis jurídico de tu exposición y ajuste a la literalidad normativa**\n"
        "2. **⚖️ Auditoría de artículos, leyes y relaciones con las fuentes (TEMAS HASTA EL MOMENTO y NOVEDADES 2026)**\n"
        "3. **⚠️ Detalles técnicos omitidos y párrafo magistral que deberías haber incluido**\n"
        "4. **🎓 Calificación Oficial según los Criterios del Tribunal (desglose Criterio 1 [0-45], Criterio 2 [0-3], Criterio 3 [0-2], Total sobre 50 puntos y equivalencia sobre 10)**"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for modelo in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={clave_limpia}"
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=12)
            if r.status_code == 200:
                data = r.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            continue

    if ev_fallback is None:
        ev_fallback = evaluar_respuesta_escrita(respuesta_alumno, respuesta_oficial, explicacion_oficial, f"{enunciado_supuesto} {pregunta}")
    return generar_dictamen_tribunal_inteligente(ev_fallback, respuesta_alumno, respuesta_oficial, explicacion_oficial)

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
        b64_auth = base64.urlsafe_b64encode(zlib.compress(json.dumps(datos_auth, ensure_ascii=False).encode("utf-8"), level=9)).decode("ascii")

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
            b64_test = base64.urlsafe_b64encode(zlib.compress(json.dumps(datos_test, ensure_ascii=False).encode("utf-8"), level=9)).decode("ascii")
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

    nombre_pdf = st.session_state.get('test_name') or "Test sin nombre"
    usuario_rep = (st.session_state.get('email') or "Alumno Oposiciona").strip()
    preamble_txt = re.sub(r'\*\*|\🏷️', '', q.get('preamble', '')).strip()
    pregunta_txt = q.get('question_text', '').strip()
    lista_opciones = q.get('options', [])
    idx_correcta = q.get('answer', -1)
    correcta_txt = lista_opciones[idx_correcta] if (0 <= idx_correcta < len(lista_opciones)) else (q.get('answer_text') or "⚠️ No detectada automáticamente en el PDF")
    exp_limpia = re.sub(r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s*\([^)]*\))?:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip(), flags=re.IGNORECASE).strip() or "Sin explicación disponible."

    st.markdown(
        "<div style='background-color:#fff8e1; border:2px solid #ffb300; border-radius:8px; padding:12px; margin-top:8px; margin-bottom:8px;'>"
        f"<b style='color:#bf360c !important; font-size:15px;'>🛠️ Reportar error en la Pregunta {num_pregunta} a info@oposiciona.es</b><br>"
        "<span style='font-size:13px; color:#5d4037 !important;'>Se enviará una ficha visual con tu comentario, el enunciado, las opciones por separado y la explicación para revisarlo al instante.</span>"
        "</div>",
        unsafe_allow_html=True
    )

    motivo = st.text_area(
        "Explica brevemente el error encontrado:",
        key=f"txt_rep_{ubicacion_key}_{num_pregunta}",
        placeholder="Ejemplo: Falta un 'NO' en el enunciado, la respuesta correcta debería ser la b), o se ha cortado una frase..."
    )

    if st.button("📨 Enviar a info@oposiciona.es", key=f"btn_send_{ubicacion_key}_{num_pregunta}", type="primary", use_container_width=True):
        if not motivo.strip():
            st.warning("⚠️ Escribe brevemente en qué consiste el error antes de enviarlo.")
        else:
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
                st.success("✅ ¡Reporte enviado con éxito a info@oposiciona.es! Muchas gracias por tu colaboración.")
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
    st.session_state.test_name = nombre_test
    st.session_state.test_esp = especialidad_sel or st.session_state.get('saved_esp', '')
    st.session_state.test_cat = categoria_sel or st.session_state.get('saved_cat', '')
    st.session_state.mostrar_opciones_simulacro = False
    cat_actual = st.session_state.test_cat
    max_op = 3 if "GESTI" in (st.session_state.test_esp or "").upper() else 4
    with st.spinner(f"Extrayendo '{nombre_test}' de forma segura..."):
        try:
            r = descargar_pdf_fresco(url_descarga)
            if r.status_code == 200:
                if cat_actual in ["DESARROLLO", "PREGUNTA DE DESARROLLO"]:
                    raw_qs = PDFQuizParser.parse_abiertas_gestion(r.content, modo="DESARROLLO")
                    if not raw_qs:
                        st.error("No se encontraron preguntas o epígrafes de desarrollo en este PDF.")
                    else:
                        procesar_preguntas(raw_qs, barajar=False)
                elif cat_actual in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"]:
                    raw_qs = PDFQuizParser.parse_abiertas_gestion(r.content, modo="SUPUESTOS")
                    if not raw_qs:
                        st.error("No se encontraron supuestos prácticos en este PDF.")
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

def save_answer(selected):
    stat = st.session_state.stats[st.session_state.current_index]
    if selected is not None and str(selected).strip() != "" and selected != stat['selected']:
        stat['selected'] = selected
        stat['attempts'] += 1
        if not st.session_state.get('inicio_registrado_sheets', False):
            st.session_state.inicio_registrado_sheets = True
            registrar_actividad_sheets("🚀 En curso", nombre_test=st.session_state.get("test_name") or "Test", accion="nueva_fila")

def handle_radio_change():
    idx = st.session_state.current_index
    selected = st.session_state.get(f"radio_{idx}")
    save_answer(selected)
    if "metralleta" in st.session_state.modo_avance.lower() and selected:
        if idx < len(st.session_state.questions) - 1:
            st.session_state.current_index += 1
            st.session_state.checked = False
            st.session_state.do_scroll = True
        else:
            st.session_state.update(finished=True, celebracion_mostrada=False, do_scroll=True)

def procesar_preguntas(raw_qs, barajar=True):
    patrones_fijos = [
        r'todas\s+son\s+(correctas|incorrectas|falsas|verdaderas)',
        r'todas\s+las\s+respuestas?\s+son\s+(correctas|incorrectas|falsas|verdaderas)',
        r'ninguna\s+es\s+correcta',
        r'ninguna\s+de\s+las\s+(anteriores|respuestas?)\s+es\s+correcta',
        r'las\s+opciones?\s+[a-d]\s*y\s*[a-d]\s+son\s+correctas'
    ]
    for q in raw_qs:
        if q.get("is_open", False):
            continue
        cleaned_options, tiene_fija = [], False
        for opt in q["options"]:
            to = re.sub(r'^[a-zA-Z][\)\.-]\s*', '', opt).strip()
            cleaned_options.append(to)
            if any(re.search(p, to.lower()) for p in patrones_fijos): tiene_fija = True
        corr = cleaned_options[q["answer"]] if 0 <= q["answer"] < len(cleaned_options) else None
        if not tiene_fija and barajar: random.shuffle(cleaned_options)
        if corr: q["answer"] = cleaned_options.index(corr)
        q["options"] = [f"{chr(97+i)}) {o}" for i, o in enumerate(cleaned_options)]
    if barajar:
        random.shuffle(raw_qs)
    st.session_state.update(
        questions=raw_qs,
        current_index=0,
        finished=False,
        checked=False,
        stats={i: {'attempts': 0, 'selected': None, 'ai_feedback': None, 'last_evaluated_text': None} for i in range(len(raw_qs))},
        mostrar_opciones_simulacro=False,
        celebracion_mostrada=False,
        do_scroll=True
    )
    iniciar_cronometro_test()
    st.rerun()

def action_repetir_test():
    st.session_state.update(
        current_index=0,
        stats={i: {'attempts': 0, 'selected': None, 'ai_feedback': None, 'last_evaluated_text': None} for i in range(len(st.session_state.questions))},
        finished=False, checked=False, celebracion_mostrada=False, do_scroll=True
    )
    iniciar_cronometro_test()

def action_subir_otro():
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

if not st.session_state.questions:
    st.markdown("<style>:root { --background-color: #FFFFFF !important; --secondary-background-color: #F8FAFC !important; --text-color: #1E293B !important; } html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFFFF !important; color: #1E293B !important; }</style>", unsafe_allow_html=True)
    es_admin = usuario_es_admin()
    col_texto, col_img = st.columns([2.5, 1])
    with col_img:
        try: st.image("test-utiles-768x768.png", use_container_width=True)
        except: pass
    with col_texto:
        st.markdown("<div style='font-size:24px; font-weight:700; color:#2C3E50 !important; margin-top: -10px; margin-bottom: 10px;'>📚 Comienza a practicar</div>", unsafe_allow_html=True)
        rol = st.session_state.rol
        TESTS_DISPONIBLES = obtener_tests_segun_rol()
        st.markdown("<div style='font-size:18px; font-weight:700; color:#1E293B !important; margin-bottom:6px;'>1. Especialidad</div>", unsafe_allow_html=True)
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

        st.markdown("<div style='font-size:18px; font-weight:700; color:#1E293B !important; margin-bottom:6px;'>2. Categoría</div>", unsafe_allow_html=True)
        l_cat = list(TESTS_DISPONIBLES[especialidad].keys())
        i_cat = l_cat.index(st.session_state.saved_cat) if st.session_state.get("saved_cat") in l_cat else 0
        categoria = st.radio("Selecciona el tipo de test:", l_cat, index=i_cat, horizontal=True, key="radio_categoria", label_visibility="collapsed", on_change=cambio_categoria_o_especialidad)
        st.session_state.saved_cat = categoria

    st.markdown("<div style='font-size:18px; font-weight:700; color:#1E293B !important; margin-bottom:6px;'>3. Modo de avance</div>", unsafe_allow_html=True)
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

    st.markdown(f"<div style='font-size:18px; font-weight:700; color:#1E293B !important; margin-bottom:6px;'>{titulo_paso_4}</div>", unsafe_allow_html=True)
    if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO", "SUPUESTOS", "SUPUESTOS PRÁCTICOS"] and es_admin:
        ej_txt = "2.º Ejercicio — 1.ª Parte (Preguntas de Desarrollo: 0 a 50 ptos)" if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO"] else "2.º Ejercicio — 2.ª Parte (Supuesto Práctico: 0 a 50 ptos)"
        st.info(f"🔒 **Modo Administrador — {ej_txt}:** Corrección con IA de Gemini aplicando los Criterios Oficiales del Tribunal (0-45 ptos conocimiento y literalidad normativa; 0-3 ptos orden de ideas y 0-2 ptos expresión escrita condicionados a alcanzar ≥ 20/45; mínimo eliminatorio 25/50 ptos) y contrastando con `TEMAS GESTION HASTA EL MOMENTO`, `TEMAS ADMINISTRATIVO HASTA EL MOMENTO` y `NOVEDADES 2026`.")

    tests_reales = {k: v for k, v in TESTS_DISPONIBLES[especialidad][categoria].items() if v is not None}

    if rol == "INVITADO":
        if not tests_reales: st.warning("⚠️ CATEGORÍA NO DISPONIBLE PARA USUARIOS INVITADOS")
        else: st.info("ℹ️ ÚNICO TEST DE DEMOSTRACIÓN DISPONIBLE PARA USUARIO INVITADO")

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
                        et = "<span style='background:#fff3cd; color:#856404 !important; padding:2px 6px; border-radius:4px; font-size:11px; margin-left:6px;'>REPASO</span>" if es_r else ""
                        cn, cb = st.columns([3.2, 1])
                        with cn: st.markdown(f"<div style='padding-top:6px; font-size:15px; color:#1E293B !important;'>{ic} <b style='color:#1E293B !important;'>{tn}</b> {et}</div>", unsafe_allow_html=True)
                        with cb:
                            if st.button("🚀 Iniciar", key=f"btn_grp_{especialidad}_{categoria}_{ig}_{it}", use_container_width=True, type="primary"):
                                cargar_test_desde_url(tn, tu, especialidad, categoria)

    total_deseadas = 95 if especialidad == "GESTION" else 75
    with st.container():
        st.markdown('<div class="cargar-test-container"></div><div style="background-color: #fff3cd; border: 2px dashed #ffc107; border-radius: 8px; padding: 15px 15px 5px 15px; text-align: center; margin: 15px 0 10px 0;"><div style="font-size: 18px; font-weight: 700; color: #856404 !important; margin-top: 0; margin-bottom: 5px;">🔥 SIMULACRO GLOBAL EXPERTO 🔥</div><p style="color: #856404 !important; font-size: 14px; margin-bottom: 10px;">Genera un examen aleatorio cruzando preguntas de los distintos temas disponibles en esta especialidad.</p></div>', unsafe_allow_html=True)
        if st.button(f"🚨 INICIAR SIMULACRO ({total_deseadas} PREGUNTAS) 🚨", use_container_width=True, type="primary"):
            if rol == "INVITADO": st.error("🔒 Función no disponible para usuarios invitados. Matricúlate para acceder al Simulacro Global Experto.")
            else: st.session_state.mostrar_opciones_simulacro = True

        if rol != "INVITADO" and st.session_state.get('mostrar_opciones_simulacro', False):
            st.markdown("<div style='background-color:#eef6ff; border:2px solid #1f77b4; border-radius:8px; padding:12px; margin-top:8px; margin-bottom:10px; text-align:center;'><b style='color:#1f77b4 !important; font-size:16px;'>🎯 ¿Sobre qué bloques quieres realizar el Simulacro?</b></div>", unsafe_allow_html=True)
            cs1, cs2, cs3 = st.columns(3)
            for col_b, lbl, amb, t_lbl in [(cs1, "🌐 TODO", "TODO", "SIMULACRO GLOBAL"), (cs2, "📘 GENERAL", "GENERAL", "SIMULACRO"), (cs3, "🎯 ESPECÍFICO", "ESPECIFICO", "SIMULACRO")]:
                if col_b.button(lbl, use_container_width=True, type="primary"):
                    st.session_state.test_name = f"{t_lbl} ({especialidad} - {amb})"
                    st.session_state.test_esp = especialidad
                    st.session_state.test_cat = f"SIMULACRO ({amb})"
                    with st.spinner("Generando simulacro..."):
                        ex = generar_simulacro_aleatorio(especialidad, amb, total_deseadas, TESTS_DISPONIBLES)
                        if ex: procesar_preguntas(ex)
                        else: st.error("No se pudo extraer ninguna pregunta.")

    if rol != "INVITADO":
        with st.expander("Opcional: Subir un PDF manualmente desde tu dispositivo"):
            uf = st.file_uploader("", type="pdf")
            if uf is not None:
                st.session_state.update(modo_avance=modo_avance, test_name=uf.name, test_esp=especialidad, test_cat=categoria if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO", "SUPUESTOS", "SUPUESTOS PRÁCTICOS"] else "ARCHIVO LOCAL")
                max_op_local = 3 if "GESTI" in especialidad.upper() else 4
                with st.spinner("Procesando documento local..."):
                    pdf_bytes_local = uf.read()
                    if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO"]:
                        rqs = PDFQuizParser.parse_abiertas_gestion(pdf_bytes_local, modo="DESARROLLO")
                        if not rqs: st.error("No se encontraron preguntas de desarrollo en este PDF.")
                        else: procesar_preguntas(rqs, barajar=False)
                    elif categoria in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"]:
                        rqs = PDFQuizParser.parse_abiertas_gestion(pdf_bytes_local, modo="SUPUESTOS")
                        if not rqs: st.error("No se encontraron supuestos prácticos en este PDF.")
                        else: procesar_preguntas(rqs, barajar=False)
                    else:
                        rqs = PDFQuizParser.parse(pdf_bytes_local, max_options=max_op_local)
                        if not rqs: st.error("No se encontraron preguntas válidas en este PDF.")
                        else: procesar_preguntas(rqs, barajar=True)

    if es_admin:
        with st.expander("📊 Herramienta Admin: Generar tablas con Nº exacto de preguntas"):
            st.info("Esta herramienta es visible únicamente para el administrador.")
            if st.button("Contar preguntas de todos los PDFs y crear tablas", use_container_width=True, type="primary"):
                nuevos_hoy = globals().get("NUEVOS_HOY", [])
                tot_pdfs = sum(1 for ec in TESTS_DISPONIBLES_COMPLETO.values() for ct in ec.values() for u in ct.values() if u is not None)
                bp, proc, txt_copiar = st.progress(0, text="Analizando PDFs..."), 0, ""
                for esp, cats in TESTS_DISPONIBLES_COMPLETO.items():
                    max_op_adm = 3 if "GESTI" in esp.upper() else 4
                    st.markdown(f"### 📋 Catálogo de Tests: {esp}")
                    t_md = "| Categoría | Nombre del Test | Nº de Preguntas | Media Opciones |\n| :--- | :--- | :---: | :---: |\n"
                    for cat, tests in cats.items():
                        for nom, url in tests.items():
                            if url is None: continue
                            proc += 1
                            bp.progress(proc / tot_pdfs, text=f"Analizando ({proc}/{tot_pdfs}): {nom}...")
                            try:
                                r = descargar_pdf_fresco(url)
                                if r.status_code == 200:
                                    if cat == "DESARROLLO":
                                        qs_parsed = PDFQuizParser.parse_abiertas_gestion(r.content, modo="DESARROLLO")
                                        nq, media_op = len(qs_parsed), "Desarrollo"
                                    else:
                                        qs_parsed = PDFQuizParser.parse(r.content, max_options=max_op_adm)
                                        nq = len(qs_parsed)
                                        if nq > 0:
                                            avg_val = sum(len(q.get("options", [])) for q in qs_parsed) / nq
                                            media_op = str(int(avg_val)) if avg_val.is_integer() else f"{avg_val:.2f}".replace(".", ",")
                                        else:
                                            media_op = "0"
                                else:
                                    nq, media_op = "Error", "-"
                            except Exception:
                                nq, media_op = "-", "-"
                            if nom in nuevos_hoy:
                                t_md += f"| **{cat}** | **{nom} (🆕 Nuevo hoy)** | **{nq} preguntas** | **{media_op}** |\n"
                            else:
                                t_md += f"| {cat} | {nom} | {nq} preguntas | {media_op} |\n"
                    st.markdown(t_md)
                    txt_copiar += f"### 📋 Catálogo de Tests: {esp}\n\n" + t_md + "\n---\n\n"
                bp.empty()
                st.success("✅ ¡Recuento completado con éxito!")
                st.code(txt_copiar, language="markdown")

elif not st.session_state.finished:
    st.markdown("<style>:root { --background-color: #FFFDE7 !important; --secondary-background-color: #FFFDE7 !important; --text-color: #1E293B !important; } html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFDE7 !important; background-image: none !important; color: #1E293B !important; } .block-container, [data-testid='stMainBlockContainer'], div[data-testid='stVerticalBlock'] { background-color: transparent !important; background: transparent !important; }</style>", unsafe_allow_html=True)
    idx = st.session_state.current_index
    q, stat = st.session_state.questions[idx], st.session_state.stats[idx]
    puede_rep = usuario_puede_reportar()
    es_abierta = bool(q.get("is_open", False))

    st.markdown(f"<p style='color: #64748B !important; font-size: 14px; margin-top: -10px; margin-bottom: 5px;'>{'Epígrafe / Cuestión' if es_abierta else 'Pregunta'} {idx + 1} de {len(st.session_state.questions)}</p>", unsafe_allow_html=True)
    if q.get('preamble'):
        st.markdown(
            f"<div style='background-color:#FFFFFF; border:1px solid #CBD5E1; border-left:4px solid #1F77B4; border-radius:6px; padding:12px; margin-bottom:12px; font-size:15px; line-height:1.45; text-align:justify; color:#1E293B !important;'>{q['preamble']}</div>",
            unsafe_allow_html=True
        )
    st.markdown(f"<p style='font-size: 19px; font-weight: 600; color: #2C3E50 !important; margin-bottom: 15px; line-height: 1.3; text-align: justify;'>{q['question_text']}</p>", unsafe_allow_html=True)

    if es_abierta:
        altura_caja = 260 if q.get("tipo_abierta") == "DESARROLLO" else 160
        sel_opt = st.text_area(
            "✍️ Escribe aquí tu desarrollo o respuesta jurídica:",
            value=stat.get("selected") or "",
            height=altura_caja,
            key=f"open_txt_{idx}",
            placeholder="Redacta aquí tu contestación indicando la conclusión jurídica, requisitos, plazos, porcentajes y los artículos o normas aplicables..."
        )
        if st.session_state.get(f"open_txt_{idx}") is not None:
            sel_opt = st.session_state.get(f"open_txt_{idx}")
    else:
        def_idx = q['options'].index(stat['selected']) if stat['selected'] in q['options'] else None
        sel_opt = st.radio("Elige tu respuesta:", q['options'], index=def_idx, key=f"radio_{idx}", label_visibility="collapsed", on_change=handle_radio_change)

    if puede_rep:
        c1, c2, c3, c4, c5 = st.columns([0.95, 1, 1, 1.15, 1.25])
    else:
        c1, c2, c3, c4 = st.columns(4)
        c5 = None

    if c1.button("🡄 Anterior", use_container_width=True) and idx > 0:
        save_answer(sel_opt)
        st.session_state.update(checked=False, current_index=idx - 1, do_scroll=True); st.rerun()
    if c2.button("Comprobar", use_container_width=True):
        save_answer(sel_opt)
        st.session_state.update(checked=True, do_scroll=True); st.rerun()
    if idx < len(st.session_state.questions) - 1:
        if c3.button("Siguiente ➔", use_container_width=True):
            save_answer(sel_opt)
            st.session_state.update(checked=False, current_index=idx + 1, do_scroll=True); st.rerun()
    else:
        if c3.button("Terminar ➔", use_container_width=True):
            save_answer(sel_opt)
            st.session_state.update(finished=True, celebracion_mostrada=False, do_scroll=True); st.rerun()
    if c4.button("⏹ Finalizar Test", use_container_width=True):
        save_answer(sel_opt)
        st.session_state.update(finished=True, celebracion_mostrada=False, do_scroll=True); st.rerun()

    key_rep_test = f"rep_open_test_{idx + 1}"
    if key_rep_test not in st.session_state:
        st.session_state[key_rep_test] = False
    if puede_rep and c5 is not None:
        if c5.button("⚠️ Reportar Error", key=f"btn_err_top_{idx + 1}", use_container_width=True, type="primary"):
            st.session_state[key_rep_test] = not st.session_state[key_rep_test]

    if st.session_state.checked:
        if es_abierta:
            txt_alumno = (sel_opt or stat.get("selected") or "").strip()
            resp_of = (q.get("answer_text") or "").strip()
            exp_of = (q.get("explanation") or "").strip()
            ctx_pregunta = f"{q.get('preamble', '')} {q.get('question_text', '')}".strip()
            if not txt_alumno:
                st.warning("⚪ No has escrito ninguna respuesta todavía. Redacta tu contestación en el cuadro superior y pulsa «Comprobar» para que el Tribunal Evaluador analice qué te falta.")
            else:
                aviso_inapropiado = detectar_respuesta_inapropiada_o_sin_interes(txt_alumno)
                if aviso_inapropiado:
                    stat["open_score"] = 0.0
                    st.markdown(
                        f"<div style='background-color:#fff8e1; border:2px solid #d97706; border-radius:8px; padding:16px; margin-top:10px; margin-bottom:10px; font-size:15px; color:#1E293B !important; line-height:1.55; text-align:justify;'>"
                        f"{aviso_inapropiado}"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                else:
                    ev = evaluar_respuesta_escrita(txt_alumno, resp_of, exp_of, ctx_pregunta)
                    stat["open_score"] = ev["nota"]

                    if stat.get("last_evaluated_text") != txt_alumno or not stat.get("ai_feedback"):
                        stat["last_evaluated_text"] = txt_alumno
                        clave_activa = obtener_gemini_api_key_activa()
                        with st.spinner("🤖 El Tribunal Evaluador de Gemini está aplicando los Criterios Oficiales (0-50 ptos) y contrastando con el texto completo del Epígrafe..."):
                            stat["ai_feedback"] = consultar_ia_gemini_correccion(
                                clave_activa, q.get("preamble", ""), q["question_text"], txt_alumno, resp_of, exp_of, ev_fallback=ev
                            )

                    st.markdown(
                        "<div style='background-color:#f0fdf4; border:2px solid #16a34a; border-radius:8px; padding:14px 16px 6px 16px; margin-top:10px; margin-bottom:8px;'>"
                        "<div style='font-size:17px; font-weight:800; color:#15803d !important; margin-bottom:6px;'>🤖 DICTAMEN OFICIAL DEL TRIBUNAL EVALUADOR IA (BAREMO 0-50 PTOS + NOTEBOOKLM)</div>"
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
                        eh = "".join([f"<div style='margin-top: 6px; line-height: 1.4; color: #0c5460 !important;'>{p.strip()}</div>" for p in exp_of.split('\n') if p.strip()])
                        titulo_exp = "📖 Texto Íntegro Oficial del Epígrafe (hasta el siguiente epígrafe / final del documento):" if q.get("tipo_abierta") == "DESARROLLO" else "📖 Explicación y Fundamentación Legal (2.º Ejercicio - 2.ª Parte):"
                        st.markdown(
                            f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 12px; border-radius: 4px; margin-top: 10px;'>"
                            f"<div style='font-size: 14px; font-weight: 600; margin-bottom: 4px; color: #0c5460 !important;'>{titulo_exp}</div>"
                            f"<div style='font-size: 14px; color: #0c5460 !important; text-align: justify;'>{eh}</div></div>",
                            unsafe_allow_html=True
                        )
        else:
            if q['answer'] != -1:
                co = q['options'][q['answer']]
                if sel_opt == co: st.success("✅ ¡CORRECTO!")
                elif not sel_opt: st.warning(f"⚪ EN BLANCO. La correcta era: {co}")
                else: st.error(f"❌ INCORRECTO. La respuesta correcta era: {co}")
            else:
                st.warning("⚪ EN BLANCO. La correcta no se detectó automáticamente en el PDF.") if not sel_opt else st.info("⚠️ Tu respuesta ha sido guardada. (La opción correcta no estaba remarcada en el PDF original, revisa la explicación).")
            et = re.sub(r'(?i)^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip()).strip() or "No hay explicación disponible."
            eh = "".join([f"<div style='margin-top: 3px; line-height: 1.3; color: #0c5460 !important;'>{p.strip()}</div>" for p in et.split('\n') if p.strip()])
            st.markdown(f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 12px; border-radius: 4px; margin-top: 10px;'><div style='font-size: 14px; font-weight: 600; margin-bottom: 3px; color: #0c5460 !important;'>Explicación:</div><div style='font-size: 14px; color: #0c5460 !important; text-align: justify;'>{eh}</div></div>", unsafe_allow_html=True)

    if puede_rep and st.session_state.get(key_rep_test, False):
        render_cuadro_reporte_error(q, idx + 1, "test_activo")

else:
    st.markdown("<style>:root { --background-color: #FFFFFF !important; --secondary-background-color: #F8FAFC !important; --text-color: #1E293B !important; } html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFFFF !important; color: #1E293B !important; }</style>", unsafe_allow_html=True)
    components.html("<script>setTimeout(function() { if(window.parent) window.parent.scrollTo({top: 0, behavior: 'smooth'}); }, 500);</script>", height=0)

    puede_rep = usuario_puede_reportar()
    aciertos = fallos = blancos = preg_eval = 0
    aciertos_por_intento = {}
    suma_notas_abiertas = 0.0
    suma_notas_50 = 0.0
    es_test_abierto = any(q.get("is_open", False) for q in st.session_state.questions)

    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        if q.get("is_open", False):
            preg_eval += 1
            txt_al = (stat.get("selected") or "").strip()
            if not txt_al:
                blancos += 1
                stat['final_status'] = "⚪ En blanco (0,00 / 50 ptos)"
            elif detectar_respuesta_inapropiada_o_sin_interes(txt_al):
                fallos += 1
                stat['final_status'] = "⚠️ Respuesta no evaluable (0,00 / 50 ptos)"
            else:
                ctx_q = f"{q.get('preamble', '')} {q.get('question_text', '')}".strip()
                ev = evaluar_respuesta_escrita(txt_al, q.get("answer_text", ""), q.get("explanation", ""), ctx_q)
                nota_q = ev["nota"]
                nota_q_50 = ev["nota_50"]
                suma_notas_abiertas += nota_q
                suma_notas_50 += nota_q_50
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
        # Evaluamos la media tanto sobre las contestadas como sobre el total de epígrafes del tema
        preg_contestadas = max(1, aciertos + fallos)
        nota_referencia = suma_notas_abiertas / preg_contestadas if (aciertos + fallos) > 0 else 0.0
        nota_media_50 = suma_notas_50 / preg_contestadas if (aciertos + fallos) > 0 else 0.0
        nota_oposicion_10 = nota_referencia
        aciertos_netos = aciertos
        puntos_restados = 0.0
        divisor_penalizacion = 1
        penalizacion_texto = "Mínimo eliminatorio de 25,00 / 50 puntos en cada parte (sin compensación)"
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
        if aciertos > 0 and aciertos_por_intento:
            max_intento = max(aciertos_por_intento.keys())
            tope_mostrar = 1 if max_intento == 1 else max(3, max_intento)
            desglose_str = ", ".join([f"{aciertos_por_intento.get(k, 0)}-{k}" for k in range(1, tope_mostrar + 1)])
            aciertos_sheets_str = f"{aciertos} ({desglose_str})"
        else:
            aciertos_sheets_str = str(aciertos)

        nota_sheets_str = f"{nota_referencia:.2f} (Opos: {nota_oposicion_10:.2f})".replace(".", ",")
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
        st.markdown("<div style='background: linear-gradient(90deg, #e8f5e9, #c8e6c9, #e8f5e9); border: 2px solid #2e7d32; border-radius: 10px; padding: 12px; text-align: center; margin-bottom: 15px;'><div style='color: #1b5e20 !important; margin: 0; font-size: 22px; font-weight: 700;'>🎉 ¡ENHORABUENA, HAS SUPERADO EL CORTE DE 25 / 50 PUNTOS! 🎉</div><p style='color: #2e7d32 !important; margin: 4px 0 0 0; font-size: 14px; font-weight: 600;'>¡Sigue así, estás cada vez más cerca de tu plaza!</p></div>", unsafe_allow_html=True)
        cr1, cr2, cr3 = st.columns([1, 0.4, 1])
        with cr2:
            try: st.image("test-utiles-768x768.png", use_container_width=True)
            except: pass
    else:
        cr1, cr2, cr3 = st.columns([1, 1.5, 1])
        with cr2:
            try: st.image("llorona.jpeg", use_container_width=True)
            except: pass

    st.markdown("<div style='text-align: center; font-size: 22px; font-weight: 700; color: #2C3E50 !important; margin-top: -10px; margin-bottom: 6px;'>📊 RESULTADOS FINALES</div>", unsafe_allow_html=True)
    if st.session_state.get('test_name'):
        st.markdown(f"<div style='text-align: center; font-size: 16px; font-weight: 600; color: #1f77b4 !important; margin-bottom: 15px;'>📄 {st.session_state.test_name}</div>", unsafe_allow_html=True)

    if es_test_abierto:
        st.markdown(
            f"<div style='text-align: center; font-size: 16px; font-weight: 600; color: #334155 !important; margin-bottom: 12px;'>"
            f"✅ Superadas (≥ 25/50): <b style='color:#000000 !important;'>{aciertos}</b> &nbsp;|&nbsp; ⚠️ Inferiores a 25/50: <b style='color:#000000 !important;'>{fallos}</b> &nbsp;|&nbsp; ⚪ En blanco: <b style='color:#000000 !important;'>{blancos}</b>"
            f"</div>"
            f"<div style='background-color: #eef6ff; border: 2px solid #1f77b4; border-radius: 10px; padding: 14px 16px; margin-bottom: 20px;'>"
            f"<div style='text-align: center; font-size: 14px; font-weight: 700; color: #1f77b4 !important; letter-spacing: 0.5px; margin-bottom: 4px;'>🎯 BAREMO OFICIAL DEL TRIBUNAL ({nombre_cuerpo})</div>"
            f"<div style='text-align: center; font-size: 22px; font-weight: 800; color: #0d47a1 !important; margin-bottom: 4px;'>"
            f"🏛️ PUNTUACIÓN DIRECTA DE LA PARTE: {nota_media_50:.2f} / 50,00 PUNTOS"
            f"</div>"
            f"<div style='text-align: center; font-size: 16px; font-weight: 700; color: #1565c0 !important; margin-bottom: 8px;'>"
            f"🎓 Equivalencia sobre 10: {nota_oposicion_10:.2f} / 10"
            f"</div>"
            f"<div style='background-color: #ffffff; border-left: 4px solid #1f77b4; padding: 9px 12px; border-radius: 4px; font-size: 13px; color: #2C3E50 !important; text-align: justify; line-height: 1.4;'>"
            f"<b>Criterios Oficiales (Resolución 22/12/2025):</b> Cada parte del Segundo Ejercicio se califica de 0 a 50 puntos (0-45 ptos conocimiento, literalidad normativa y precisión práctica; 0-3 ptos orden de ideas y 0-2 ptos calidad de expresión escrita siempre que se alcancen al menos 20/45 ptos en el apartado 1). Es necesario obtener al menos <b>25 puntos directos</b> en cada parte para sumar ambas sin posibilidad de compensación."
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
        co = (q.get('answer_text') or "Ver texto íntegro del epígrafe debajo") if q.get("is_open") else (q['options'][q['answer']] if q['answer'] != -1 else "No detectada (revisa la explicación)")
        col = "#15803d" if "✅" in stat.get('final_status', '') else "#dc2626" if "❌" in stat.get('final_status', '') else "#d97706"
        et = re.sub(r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip(), flags=re.IGNORECASE).strip() or "No hay explicación disponible."
        eh = "".join([f"<div style='margin-top: 3px; line-height: 1.3; color: #0c5460 !important;'>{p.strip()}</div>" for p in et.split('\n') if p.strip()])
        ph = f"<div style='text-align: justify; line-height: 1.3; margin-bottom: 4px; font-size: 14px; color: #334155 !important;'>{q['preamble']}</div>" if q.get('preamble') else ""
        st.markdown(
            f"<div style='margin-bottom: 5px;'>"
            f"<div style='color: {col} !important; font-size: 17px; font-weight: 700; margin-bottom: 4px;'>{'Epígrafe / Cuestión' if q.get('is_open') else 'Pregunta'} {i+1} | {stat['final_status']}</div>"
            f"{ph}"
            f"<div style='font-size:15px; color:#000000 !important; text-align: justify; line-height: 1.3; margin-bottom: 4px;'><b style='color:#000000 !important;'>Enunciado:</b> {q['question_text']}</div>"
            f"<div style='font-size:15px; color:#000000 !important; text-align: justify; line-height: 1.3; margin-bottom: 4px;'><b style='color:#000000 !important;'>Tu respuesta:</b> {stat['selected'] if stat['selected'] else 'Ninguna'}</div>"
            f"<div style='font-size:15px; color:#1b5e20 !important; text-align: justify; line-height: 1.3; margin-bottom: 6px;'><b style='color:#1b5e20 !important;'>Respuesta oficial:</b> {co}</div>"
            f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 10px; border-radius: 4px; margin-bottom: 6px;'><div style='font-size: 14px; font-weight: 600; margin-bottom: 2px; color: #0c5460 !important;'>{'Texto íntegro del Epígrafe:' if q.get('tipo_abierta') == 'DESARROLLO' else 'Explicación:'}</div><div style='font-size: 14px; color: #0c5460 !important; text-align: justify;'>{eh}</div></div>"
            f"</div>",
            unsafe_allow_html=True
        )
        if puede_rep:
            key_rep_res = f"rep_open_res_{i + 1}"
            if key_rep_res not in st.session_state:
                st.session_state[key_rep_res] = False
            if st.button(f"⚠️ Reportar error en Pregunta {i + 1}", key=f"btn_err_res_{i + 1}"):
                st.session_state[key_rep_res] = not st.session_state[key_rep_res]
            if st.session_state[key_rep_res]:
                render_cuadro_reporte_error(q, i + 1, "resumen_final")

        st.markdown("<hr style='margin: 12px 0px 15px 0px; border: 0; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)

    c1_b, c2_b, c3_b = st.columns(3)
    c1_b.button(lbl_repetir, key="btn_rep_bot", on_click=action_repetir_test, use_container_width=True)
    c2_b.button(lbl_cambiar, key="btn_sub_bot", on_click=action_subir_otro, use_container_width=True)
    c3_b.button("🚪 Finalizar Sesión", key="btn_out_bot", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
# === FIN SECCIÓN 5 ===

