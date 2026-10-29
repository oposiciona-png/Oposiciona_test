# === SECCIÓN 1: CONFIGURACIÓN, ESTILOS Y REGISTRO SHEETS ===
import streamlit as st
import streamlit.components.v1 as components
import fitz  # PyMuPDF
import re, random, requests, os, unicodedata, time, json, threading
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
            `;
            parentDoc.head.appendChild(script);
        }
    }, 1000);
} catch(e) {}
</script>""", height=0)

GOOGLE_SHEETS_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbw_B-g4pwxuZX4HzH99cobW6jQoValvLXI2ogeJgMuekjwlyS766KS4ujm3CFYdJ7DPlA/exec"

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
    ('test_esp', ""), ('test_cat', ""),
    ('modo_avance', "**Modo reflexivo** (puedes comprobar la pregunta y el paso a la siguiente es manual pulsando siguiente)")
]:
    if k not in st.session_state: st.session_state[k] = v

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
    def parse(pdf_bytes):
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        questions, lines = [], []
        stop_reading = ignoring_mode = entered_supuestos = False

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
                                if not re.match(r'^[a-eA-E][\)\.-]?$', t): is_bold = True
                        line_text = line_text.strip()
                        if line_text:
                            line_text = re.sub(r'<{2,}', '«', line_text)
                            line_text = re.sub(r'>{2,}', '»', line_text)
                            line_text = re.sub(r'<(?=[A-ZÁÉÍÓÚÑa-záéíóúñ0-9"«])', '«', line_text)
                            line_text = re.sub(r'(?<=[.?!;:"»a-zA-Z0-9])>', '»', line_text)
                            line_text = re.sub(r'(?:https?://)?(?:www\.)?oposiciona\.es\b', '', line_text, flags=re.IGNORECASE).strip()
                            line_text = re.sub(r'\bP[aá]gina\s+\d+\s+de\s+\d+\b', '', line_text, flags=re.IGNORECASE).strip()
                            for pat in [
                                r'^OPOSICIONA\s*', r'^GESTI[OÓ]N DE LA SEGURIDAD SOCIAL\s*', r'^ADMINISTRATIVO DE LA SEGURIDAD SOCIAL\s*',
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
                                r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+cumple\s+\d+\s+años\s+el', r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\_nacid[ao]\s+el\s+\d+',
                                r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\_camarer[ao]\s+desde', r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\_trabaja\s+en\s+la\s+empresa'
                            ]:
                                if re.match(pat, line_text): ignoring_mode = entered_supuestos = True; break
                        if ignoring_mode: continue

                        is_header = bool(line_text.isupper() and re.match(r'^(RESPUESTAS\s+|GENERAL\s+|ESPECIFICO\s+|EXAMEN\s+|TEST\s+)?TEMAS?\s+\d+', line_text))
                        is_page_ref = bool(re.match(r'^\(p[aá]gina\s+\d+', line_text.strip(), re.IGNORECASE))
                        if not is_header and not is_page_ref and len(tl_clean_spaces) < 120:
                            for pat in [
                                r'^oposiciona$', r'oposicionaes', r'^pagina\s+\d+\s+de\s+\d+$', r'^(administrativo|gestion)\s+de\s+la\s+seguridad\s+social',
                                r'^(administrativo|gestion)\s+202\d\s+tema\s+\d+[a-z]?', r'^tema\s+\d+[a-z]?\s+(administrativo|gestion)\s+202\d$',
                                r'^tema\s+\d+[a-z]?\s+campo\s+de\s+aplicacion\s+y\s+composicion',
                                r'^(general|especifico|examen|test|respuestas|respuestas\s+(tipo\s+)?test:?|test\s+profesor)\s+temas?\s+\d+',
                                r'^examen\s+repaso', r'^examen\s+[a-záéíóúñ0-9\s]+\s*202\d', r'^normas\s+para\s+la\s+realizacion', r'^especial\s+simulacros?',
                                r'^test\s+administrativo\s+\d+\s+todo\s+el\s+temario', r'^respuestas\s+tipo\s+test:\s+temas?\s+\d+'
                            ]:
                                if re.search(pat, tl_clean_spaces): is_header = True; break
                        if is_header: continue

                        line_text = PDFQuizParser.traducir_ingles_no_rae(line_text)
                        # Unir superíndices ordinales separados por PyMuPDF (ej. "1. ª" -> "1.ª")
                        line_text = re.sub(r'(\d+\.)\s+([ºª°])', r'\1\2', line_text)

                        line_text = re.sub(r'(?<=[.?!;\)\]"\'”»])\s*(Explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s*\([^)]*\))?:|Respuest[as]?:|Resp:|El\s+n[úu]cleo\s+de\s+la\s+trampa:|La\s+trampa\s+del\s+examinador:|La\s+trampa\s+del\s+examen:)(\s|$)', r'\n\1\2', line_text, flags=re.IGNORECASE)
                        line_text = re.sub(r'(?<=\S)\s{2,}(Explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s*\([^)]*\))?:|Respuest[as]?:|Resp:|El\s+n[úu]cleo\s+de\s+la\s+trampa:|La\s+trampa\s+del\s+examinador:|La\s+trampa\s+del\s+examen:)(\s|$)', r'\n\1\2', line_text, flags=re.IGNORECASE)
                        line_text = re.sub(r'(?<=\S)\s*(OJO|NOTA|IMPORTANTE|RECUERDA|Regla\s+mnemot[ée]cnica(?:\s+para\s+el\s+examen)?):', r'\n\1:', line_text, flags=re.IGNORECASE)
                        line_text = re.sub(r'(?<=[.?!;”"\'\)])\s*(?<!"\s)(?<!«\s)(Art[íi]culo\s+aplicable:|Art[íi]culo|Art\.)\s', r'\n\1 ', line_text)
                        line_text = re.sub(r'(?<=\S)\s+([•\*])(\s|$)', r'\n\1\2', line_text)
                        line_text = re.sub(r'(?<=[a-zA-ZáéíóúñÁÉÍÓÚÑ\)\."\'”»])(?<![0-9]\.)(?<!\d)(\d{1,3}(?:[\.\-]+:?|:))(?!\s*[ºª°\d])\s*(?=[A-ZÁÉÍÓÚÑ¿¡"\'«])', r'\n\1 ', line_text)
                        line_text = re.sub(r'(?<![0-9]\.)(?<!\d)([.?!;:"»”\)])\s*([a-e][\)\.\-]|[A-E][\)\-])\s+(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])', r'\1\n\2 ', line_text)
                        line_text = re.sub(r'(?<![0-9]\.)(?<![\dA-ZÁÉÍÓÚÑ])([.?!;:"»”\)])([a-e][\)\.\-]|[A-E][\)\-])(?!\s*\.)\s*(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])', r'\1\n\2 ', line_text)
                        line_text = re.sub(r'(?<=[a-zA-ZáéíóúñÁÉÍÓÚÑ])\s+([a-e][\)\.\-]|[A-E][\)\-])\s*(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])(?!\s*[A-Z]\.)', r'\n\1 ', line_text)
                        line_text = re.sub(r'(?<=\S)\s*(\(p[aá]gina\s+\d+[^)]*\))', r'\n\1', line_text, flags=re.IGNORECASE)

                        for part in line_text.split('\n'):
                            part = part.strip()
                            if part:
                                lines.append({"text": re.sub(r'^([a-f][\)\.-]|[A-F][\)\-])(?=[^\s])', r'\1 ', part), "bold": is_bold})
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
                    (m < len(lines) and re.match(r'^[a-e][\)\.\-](\s|$)', lines[m]["text"].strip(), re.IGNORECASE))
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

        # Reparar opciones desordenadas o agrupadas sin texto:
        # Caso 1: "a)" solitario seguido de "b)" solitario y luego varias líneas de texto hasta "c)" (ej. Pregunta 14 de Tema 73)
        # Caso 2: "b)" solitario justo antes de "a) ..." (ej. Pregunta 38 de Tema 10)
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
                            if re.match(r'^[c-e][\)\.\-](\s|$)', tk, re.IGNORECASE):
                                break
                            chunk_lines.append(lines[scan_k])
                        scan_k += 1
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
                    if n_b_txt < len(lines) and not re.match(r'^[a-e][\)\.\-](\s|$)', lines[n_b_txt]["text"].strip(), re.IGNORECASE):
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
                re.match(r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s*\([^)]*\))?|respuestas?|resp)\s*:', s, re.IGNORECASE) or
                re.match(r'^explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s*\([^)]*\))?\s*$', s, re.IGNORECASE) or
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
                re.match(r'^\s*(?:Pregunta\s+)?(\d+)[,\.\-\):]+(?![\dºª°])\s*(?=[¿¡A-ZÁÉÍÓÚÑ«"\'])', s) or
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
            is_option = bool(re.match(r'^([a-z][\)\.\-]|[A-Z][\)\-])(\s|$)', text))
            is_explanation = False if (current_q and current_q["state"] == "E") else is_exp_marker(text.strip())

            forced_not_option = False
            if is_option and current_q and current_q["state"] == "Q" and not current_q["options"]:
                if text.strip().endswith('?') and not re.match(r'^([a-z][\)\.\-]|[A-Z][\)\-])\s*[¿A-ZÁÉÍÓÚÑ]', text):
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
                if re.search(r'(?:«|"|“|\(|\b)(?:Art[íi]culos?|Art\.|Ley|Real\s+Decreto(?:\s+Legislativo|\-ley)?|Decreto(?:\s+Legislativo|\-ley)?)\s*$', current_q["explanation"].strip()[-60:], re.IGNORECASE):
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
                            if found_c and (int(m_fnum.group(1)) == cand_num + 1 or int(m_fnum.group(1)) == 1):
                                is_real_q_candidate = True; break
                            if not pdf_uses_explicit_exp:
                                aborted = True; break
                        if re.match(r'^\(p[aá]gina\s+\d+', ft, re.IGNORECASE):
                            if found_c:
                                is_real_q_candidate = True; break
                            aborted = True; break

                if is_real_q_candidate and not aborted:
                    if m_num:
                        num = int(m_num.group(1))
                        prev_closed_with_pageref = bool(current_q and current_q["state"] == "E" and re.search(r'\(p[aá]gina\s+\d+', current_q["explanation"], re.IGNORECASE))
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

            if is_option and current_q["state"] in ["Q", "O"] and re.match(r'^([a-e][\)\.-]|[A-E][\)\-])(\s|$)', text):
                only_marker = bool(re.match(r'^([a-e][\)\.-]|[A-E][\)\-])\s*$', text.strip()))
                if only_marker and current_q["options"]:
                    prev_opt = current_q["options"][-1]
                    m_split = re.match(r'^([a-eA-E][\)\.-]\s*.+?\.)\s+([A-ZÁÉÍÓÚÑ].*)$', prev_opt)
                    if m_split:
                        current_q["options"][-1] = m_split.group(1)
                        text = f"{text.strip()} {m_split.group(2)}"
                current_q["options"].append(text)
                current_q["state"] = "O"
                if is_bold and current_q["answer"] == -1: current_q["answer"] = len(current_q["options"]) - 1
                continue

            if is_explanation:
                exp_clean_line = re.sub(r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s*\([^)]*\))?|respuestas?|resp)\s*:?\s*', '', text.strip(), flags=re.IGNORECASE).strip()
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
                lo = current_q["options"][-1].strip()
                ep = bool(re.search(r'[\.;\?]$', lo))
                ec = bool(re.search(r'(,| y| o| que| de| a| con| en| por| para| el| la| los| las| un| una)$', lo, re.IGNORECASE))
                inp = len(current_q["options"]) >= 2 and ep and bool(re.match(r'^[A-Z0-9¿¡"\'«]', text))
                ilr = bool(re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|seg[úu]n)\b', text_lower))
                iie = len(current_q["options"]) >= 3 and bool(re.match(r'^[A-ZÁÉÍÓÚ¿¡"\'«]', text)) and (
                    bool(re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|seg[úu]n|normativa|de conformidad|conforme|en virtud)\b', text_lower)) or
                    (bool(re.match(r'^(el\b|la\b|los\b|las\b|para\b|de\b|en\b|cuando\b|se\b|es\b|esta\b|este\b|al\b|por\b|si\b)', text_lower)) and (ep or not ec))
                )
                implicit_after_4_opts = len(current_q["options"]) >= 4 and ep and ilr
                if len(current_q["options"]) < 2 or ec or len(lo) <= 5: inp = ilr = iie = False
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
                    ipr = bool(re.match(r'^\(p[aá]gina\s+\d+', text, re.IGNORECASE))
                    ins = lc in ['.', ':', '?', '!', '"', '”', '»'] and bool(re.match(r'^[\s]*([A-ZÁÉÍÓÚ¿¡"\'«]|\d)', text))
                    if ipr or ib or io or ins:
                        current_q["explanation"] = current_q["explanation"].rstrip() + "\n\n" + text
                    else:
                        current_q["explanation"] += (" " + text) if current_q["explanation"] else text

        if current_q and current_q["options"]: questions.append(current_q)
        return questions
# === FIN SECCIÓN 2 ===

# === SECCIÓN 3: CATÁLOGO DE TESTS ===
_D = "https://drive.google.com/uc?export=download&id="

NUEVOS_HOY = [
    "✨ NOVEDADES RDL 31_2026 adm",
    "✨NOVEDADES RDL_31_2026 gestion",
]

TESTS_DISPONIBLES_COMPLETO = {
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
    },
    "GESTION": {
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
    },
}

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
def usuario_es_admin():
    correo_act = (st.session_state.get('email') or "").lower().strip()
    return bool(st.session_state.get('es_admin', False) or correo_act in USUARIOS_ADMIN)

def usuario_puede_reportar():
    return st.session_state.get('rol') != 'INVITADO'

def obtener_tests_segun_rol():
    return TESTS_DISPONIBLES_INVITADO if st.session_state.get('rol') == 'INVITADO' else TESTS_DISPONIBLES_COMPLETO

def descargar_pdf_fresco(url):
    sep = "&" if "?" in url else "?"
    url_nocache = f"{url}{sep}_cb={int(time.time() * 1000)}"
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    return requests.get(url_nocache, headers=headers)

def render_cuadro_reporte_error(q, num_pregunta, ubicacion_key):
    if not usuario_puede_reportar():
        return

    nombre_pdf = st.session_state.get('test_name') or "Test sin nombre"
    usuario_rep = st.session_state.get('email') or "Alumno Oposiciona"
    preamble_txt = re.sub(r'\*\*|\🏷️', '', q.get('preamble', '')).strip()
    pregunta_txt = q.get('question_text', '').strip()
    lista_opciones = q.get('options', [])
    idx_correcta = q.get('answer', -1)
    correcta_txt = lista_opciones[idx_correcta] if (0 <= idx_correcta < len(lista_opciones)) else "⚠️ No detectada automáticamente en el PDF"
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
                "01_🚨_QUE_REPORTA_EL_ALUMNO": f"« {motivo.strip()} »",
                "02_👤_ALUMNO_Y_TEST": f"Alumno: {usuario_rep}   |   Test: {nombre_pdf} (Pregunta Nº {num_pregunta})" + (f"   |   {preamble_txt}" if preamble_txt else ""),
                "03_❓_ENUNCIADO_DE_LA_PREGUNTA": pregunta_txt,
            }

            for i_opt, texto_opt in enumerate(lista_opciones):
                letra_mayus = chr(65 + i_opt)
                num_campo = 4 + i_opt
                if i_opt == idx_correcta:
                    payload[f"{num_campo:02d}_✅_OPCION_{letra_mayus}_(MARCADA_CORRECTA)"] = f"✅ [CORRECTA] ➡️ {texto_opt}"
                else:
                    payload[f"{num_campo:02d}_⚪_OPCION_{letra_mayus}"] = f"⚪ {texto_opt}"

            payload["09_🎯_RESPUESTA_QUE_DA_POR_BUENA_EL_SISTEMA"] = correcta_txt
            payload["10_💡_EXPLICACION_EXTRAIDA_DEL_PDF"] = exp_limpia
            payload["_template"] = "box"
            payload["_captcha"] = "false"

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
                        if (msg.toLowerCase().indexOf("activate") !== -1 || msg.toLowerCase().indexOf("confirm") !== -1) {{
                            box.innerHTML = "🔔 <b>Activación única necesaria:</b> Revisa el correo (y carpeta SPAM) de <b>info@oposiciona.es</b> y pulsa <b>'Activate Form'</b>.";
                        }} else {{
                            box.innerHTML = "ℹ️ Respuesta del servidor: " + (msg || JSON.stringify(res));
                        }}
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
    m = re.match(r'^TEMAS?\s*[\.\-]?\s*(\d+(?:\s*(?:a|y)\s*\d+)?)', nombre_test, re.IGNORECASE)
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
    with st.spinner(f"Extrayendo '{nombre_test}' de forma segura..."):
        try:
            r = descargar_pdf_fresco(url_descarga)
            if r.status_code == 200:
                raw_qs = PDFQuizParser.parse(r.content)
                if not raw_qs: st.error("No se encontraron preguntas válidas en este PDF.")
                else: procesar_preguntas(raw_qs)
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

def extraer_preguntas_aleatorias_de_lista(pdfs_candidatos, cantidad_deseada, barra_progreso):
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
                qs = PDFQuizParser.parse(r.content)
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
                qs = PDFQuizParser.parse(r.content)
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
    if ambito_seleccionado == "TODO":
        c_gen = int(round(total_deseadas * 0.60))
        c_esp = total_deseadas - c_gen
        p_gen = [("GENERAL", tn, u) for tn, u in diccionario_tests[especialidad].get("GENERAL", {}).items() if u is not None]
        p_esp = [("ESPECIFICO", tn, u) for tn, u in diccionario_tests[especialidad].get("ESPECIFICO", {}).items() if u is not None]
        examen = extraer_preguntas_aleatorias_de_lista(p_gen, c_gen, barra) + extraer_preguntas_aleatorias_de_lista(p_esp, c_esp, barra)
    else:
        co = "GENERAL" if ambito_seleccionado == "GENERAL" else "ESPECIFICO"
        p_cat = [(co, tn, u) for tn, u in diccionario_tests[especialidad].get(co, {}).items() if u is not None]
        examen = extraer_preguntas_aleatorias_de_lista(p_cat, total_deseadas, barra)
    barra.empty()
    random.shuffle(examen)
    return examen

if 'questions' not in st.session_state:
    st.session_state.update(questions=[], current_index=0, stats={}, finished=False, checked=False, test_name=None)

def save_answer(selected):
    stat = st.session_state.stats[st.session_state.current_index]
    if selected and selected != stat['selected']:
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

def procesar_preguntas(raw_qs):
    patrones_fijos = [
        r'todas\s+son\s+(correctas|incorrectas|falsas|verdaderas)',
        r'todas\s+las\s+respuestas?\s+son\s+(correctas|incorrectas|falsas|verdaderas)',
        r'ninguna\s+es\s+correcta',
        r'ninguna\s+de\s+las\s+(anteriores|respuestas?)\s+es\s+correcta',
        r'las\s+opciones?\s+[a-d]\s*y\s*[a-d]\s+son\s+correctas'
    ]
    for q in raw_qs:
        cleaned_options, tiene_fija = [], False
        for opt in q["options"]:
            to = re.sub(r'^[a-zA-Z][\)\.-]\s*', '', opt).strip()
            cleaned_options.append(to)
            if any(re.search(p, to.lower()) for p in patrones_fijos): tiene_fija = True
        corr = cleaned_options[q["answer"]] if 0 <= q["answer"] < len(cleaned_options) else None
        if not tiene_fija: random.shuffle(cleaned_options)
        if corr: q["answer"] = cleaned_options.index(corr)
        q["options"] = [f"{chr(97+i)}) {o}" for i, o in enumerate(cleaned_options)]
    random.shuffle(raw_qs)
    st.session_state.update(
        questions=raw_qs,
        stats={i: {'attempts': 0, 'selected': None} for i in range(len(raw_qs))},
        mostrar_opciones_simulacro=False,
        celebracion_mostrada=False,
        do_scroll=True
    )
    iniciar_cronometro_test()
    st.rerun()

def action_repetir_test():
    st.session_state.update(
        current_index=0,
        stats={i: {'attempts': 0, 'selected': None} for i in range(len(st.session_state.questions))},
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
    st.session_state.do_scroll = True
# === FIN SECCIÓN 4 ===


# === SECCIÓN 5: INTERFAZ Y RESULTADOS ===
if not st.session_state.questions:
    st.markdown("<style>:root { --background-color: #FFFFFF !important; --secondary-background-color: #F8FAFC !important; --text-color: #1E293B !important; } html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFFFF !important; color: #1E293B !important; }</style>", unsafe_allow_html=True)
    es_admin = usuario_es_admin()
    col_texto, col_img = st.columns([2.5, 1])
    with col_img:
        try: st.image("test-utiles-768x768.png", use_container_width=True)
        except: pass
    with col_texto:
        st.markdown("<h3 style='color:#2C3E50 !important; margin-top: -10px; margin-bottom: 10px;'>📚 Comienza a practicar</h3>", unsafe_allow_html=True)
        rol = st.session_state.rol
        TESTS_DISPONIBLES = obtener_tests_segun_rol()
        st.markdown("<h4 style='color:#1E293B !important; margin-bottom:6px;'>1. Especialidad</h4>", unsafe_allow_html=True)
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

        st.markdown("<h4 style='color:#1E293B !important; margin-bottom:6px;'>2. Categoría</h4>", unsafe_allow_html=True)
        l_cat = list(TESTS_DISPONIBLES[especialidad].keys())
        i_cat = l_cat.index(st.session_state.saved_cat) if st.session_state.get("saved_cat") in l_cat else 0
        categoria = st.radio("Selecciona el tipo de test:", l_cat, index=i_cat, horizontal=True, key="radio_categoria", label_visibility="collapsed", on_change=cambio_categoria_o_especialidad)
        st.session_state.saved_cat = categoria

    st.markdown("<h4 style='color:#1E293B !important; margin-bottom:6px;'>3. Modo de avance</h4>", unsafe_allow_html=True)
    op_av = [
        "**Modo reflexivo** (puedes comprobar la pregunta y el paso a la siguiente es manual pulsando siguiente)",
        "**Modo metralleta** (pasa a la pregunta siguiente al pulsar una opción)"
    ]
    i_av = op_av.index(st.session_state.saved_avance) if st.session_state.get("saved_avance") in op_av else 0
    modo_avance = st.radio("Modo de avance:", op_av, index=i_av, label_visibility="collapsed")
    st.session_state.saved_avance = st.session_state.modo_avance = modo_avance

    st.markdown("<h4 style='color:#1E293B !important; margin-bottom:6px;'>4. Selección de Test</h4>", unsafe_allow_html=True)
    tests_reales = {k: v for k, v in TESTS_DISPONIBLES[especialidad][categoria].items() if v is not None}

    if rol == "INVITADO":
        if not tests_reales: st.warning("⚠️ CATEGORÍA NO DISPONIBLE PARA USUARIOS INVITADOS")
        else: st.info("ℹ️ ÚNICO TEST DE DEMOSTRACIÓN DISPONIBLE PARA USUARIO INVITADO")

    if tests_reales:
        mostrar_filtro = (categoria != "EXAMENES") and any("repaso" in n.lower() for n in tests_reales)
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
            st.caption(f"🔎 Búsqueda en **Todos los tests de {categoria}**: encontrados **{len(tests_filtrados)}** de **{len(tests_reales)}**" if hay_busq else f"Mostrando **{len(tests_filtrados)}** de **{len(tests_reales)}** tests disponibles en {categoria}")

        if not tests_filtrados:
            st.warning("No hay ningún test que coincida con esa búsqueda.")
        else:
            grupos = {}
            for n, u in tests_filtrados.items():
                grupos.setdefault(obtener_grupo_tema(n, categoria), []).append((n, u))
            exp_todo = (categoria == "EXAMENES") or (len(grupos) <= 3) or hay_busq
            for ig, (ng, lt) in enumerate(grupos.items()):
                with st.expander(f"{ng}  —  ({len(lt)} {'test' if len(lt)==1 else 'tests'})", expanded=exp_todo):
                    for it, (tn, tu) in enumerate(lt):
                        es_r = ("repaso" in tn.lower()) and (categoria != "EXAMENES")
                        ic = "🔄" if es_r else ("🏆" if categoria == "EXAMENES" else "📘")
                        et = "<span style='background:#fff3cd; color:#856404 !important; padding:2px 6px; border-radius:4px; font-size:11px; margin-left:6px;'>REPASO</span>" if es_r else ""
                        cn, cb = st.columns([3.2, 1])
                        with cn: st.markdown(f"<div style='padding-top:6px; font-size:15px; color:#1E293B !important;'>{ic} <b style='color:#1E293B !important;'>{tn}</b> {et}</div>", unsafe_allow_html=True)
                        with cb:
                            if st.button("🚀 Iniciar", key=f"btn_grp_{especialidad}_{categoria}_{ig}_{it}", use_container_width=True, type="primary"):
                                cargar_test_desde_url(tn, tu, especialidad, categoria)

    total_deseadas = 95 if especialidad == "GESTION" else 75
    with st.container():
        st.markdown('<div class="cargar-test-container"></div><div style="background-color: #fff3cd; border: 2px dashed #ffc107; border-radius: 8px; padding: 15px 15px 5px 15px; text-align: center; margin: 15px 0 10px 0;"><h4 style="color: #856404 !important; margin-top: 0; margin-bottom: 5px;">🔥 SIMULACRO GLOBAL EXPERTO 🔥</h4><p style="color: #856404 !important; font-size: 14px; margin-bottom: 10px;">Genera un examen aleatorio cruzando preguntas de los distintos temas disponibles en esta especialidad.</p></div>', unsafe_allow_html=True)
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
        with st.expander("Opcional: Subir un test PDF manualmente desde tu dispositivo"):
            uf = st.file_uploader("", type="pdf")
            if uf is not None:
                st.session_state.update(modo_avance=modo_avance, test_name=uf.name, test_esp=especialidad, test_cat="ARCHIVO LOCAL")
                with st.spinner("Procesando documento local..."):
                    rqs = PDFQuizParser.parse(uf.read())
                    if not rqs: st.error("No se encontraron preguntas válidas en este PDF.")
                    else: procesar_preguntas(rqs)

    if es_admin:
        with st.expander("📊 Herramienta Admin: Generar tablas con Nº exacto de preguntas"):
            st.info("Esta herramienta es visible únicamente para el administrador.")
            if st.button("Contar preguntas de todos los PDFs y crear tablas", use_container_width=True, type="primary"):
                nuevos_hoy = []
                tot_pdfs = sum(1 for ec in TESTS_DISPONIBLES_COMPLETO.values() for ct in ec.values() for u in ct.values() if u is not None)
                bp, proc, txt_copiar = st.progress(0, text="Analizando PDFs..."), 0, ""
                for esp, cats in TESTS_DISPONIBLES_COMPLETO.items():
                    st.markdown(f"### 📋 Catálogo de Tests: {esp}")
                    t_md = "| Categoría | Nombre del Test | Nº de Preguntas |\n| :--- | :--- | :---: |\n"
                    for cat, tests in cats.items():
                        for nom, url in tests.items():
                            if url is None: continue
                            proc += 1
                            bp.progress(proc / tot_pdfs, text=f"Analizando ({proc}/{tot_pdfs}): {nom}...")
                            try:
                                r = descargar_pdf_fresco(url)
                                nq = len(PDFQuizParser.parse(r.content)) if r.status_code == 200 else "Error"
                            except Exception: nq = "-"
                            t_md += f"| **{cat}** | **{nom} (🆕 Nuevo hoy)** | **{nq} preguntas** |\n" if nom in nuevos_hoy else f"| {cat} | {nom} | {nq} preguntas |\n"
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

    st.markdown(f"<p style='color: #64748B !important; font-size: 14px; margin-top: -10px; margin-bottom: 5px;'>Pregunta {idx + 1} de {len(st.session_state.questions)}</p>", unsafe_allow_html=True)
    if q['preamble']: st.write(q['preamble'])
    st.markdown(f"<p style='font-size: 19px; font-weight: 600; color: #2C3E50 !important; margin-bottom: 15px; line-height: 1.3; text-align: justify;'>{q['question_text']}</p>", unsafe_allow_html=True)

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
        if q['answer'] != -1:
            co = q['options'][q['answer']]
            if sel_opt == co: st.success("✅ ¡CORRECTO!")
            elif not sel_opt: st.warning(f"⚪ EN BLANCO. La correcta era: {co}")
            else: st.error(f"❌ INCORRECTO. La respuesta correcta era: {co}")
        else:
            st.warning("⚪ EN BLANCO. La correcta no se detectó automáticamente en el PDF.") if not sel_opt else st.info("⚠️ Tu respuesta ha sido guardada. (La opción correcta no estaba remarcada en el PDF original, revisa la explicación).")
        et = re.sub(r'(?i)^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s*\([^)]*\))?:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip()).strip() or "No hay explicación disponible."
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

    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        if q['answer'] != -1:
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

    nota_referencia = (aciertos / preg_eval) * 10 if preg_eval > 0 else 0.0

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
        if aciertos > 0:
            max_intento = max(aciertos_por_intento.keys())
            tope_mostrar = 1 if max_intento == 1 else max(3, max_intento)
            desglose_str = ", ".join([f"{aciertos_por_intento.get(k, 0)}-{k}" for k in range(1, tope_mostrar + 1)])
            aciertos_sheets_str = f"{aciertos} ({desglose_str})"
        else:
            aciertos_sheets_str = "0"

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
        st.markdown("<div style='background: linear-gradient(90deg, #e8f5e9, #c8e6c9, #e8f5e9); border: 2px solid #2e7d32; border-radius: 10px; padding: 12px; text-align: center; margin-bottom: 15px;'><h3 style='color: #1b5e20 !important; margin: 0; font-size: 22px;'>🎉 ¡ENHORABUENA, HAS APROBADO EL TEST! 🎉</h3><p style='color: #2e7d32 !important; margin: 4px 0 0 0; font-size: 14px; font-weight: 600;'>¡Sigue así, estás cada vez más cerca de tu plaza!</p></div>", unsafe_allow_html=True)
        cr1, cr2, cr3 = st.columns([1, 0.4, 1])
        with cr2:
            try: st.image("test-utiles-768x768.png", use_container_width=True)
            except: pass
    else:
        cr1, cr2, cr3 = st.columns([1, 1.5, 1])
        with cr2:
            try: st.image("llorona.jpeg", use_container_width=True)
            except: pass

    st.markdown("<h3 style='text-align: center; color: #2C3E50 !important; margin-top: -10px;'>📊 RESULTADOS FINALES</h3>", unsafe_allow_html=True)
    if st.session_state.get('test_name'):
        st.markdown(f"<h5 style='text-align: center; color: #1f77b4 !important; margin-top: -10px; margin-bottom: 15px;'>📄 {st.session_state.test_name}</h5>", unsafe_allow_html=True)

    st.markdown(
        f"<h4 style='text-align: center; font-size: 16px; color: #334155 !important; margin-bottom: 10px;'>"
        f"✅ Acertadas: <b style='color:#000000 !important;'>{aciertos}</b> &nbsp;|&nbsp; ❌ Falladas: <b style='color:#000000 !important;'>{fallos}</b> &nbsp;|&nbsp; ⚪ En blanco: <b style='color:#000000 !important;'>{blancos}</b>"
        f"</h4>"
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

    c1_t, c2_t, c3_t = st.columns(3)
    c1_t.button("🔄 Repetir Test", key="btn_rep_top", on_click=action_repetir_test, use_container_width=True)
    c2_t.button("📁 Cambiar de Test", key="btn_sub_top", on_click=action_subir_otro, use_container_width=True)
    c3_t.button("🚪 Finalizar Sesión", key="btn_out_top", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
    st.markdown("<hr style='margin-top: 15px; margin-bottom: 15px; border: none; border-top: 1px solid #d3d3d3;'>", unsafe_allow_html=True)

    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        co = q['options'][q['answer']] if q['answer'] != -1 else "No detectada (revisa la explicación)"
        col = "#15803d" if stat['final_status'] == "✅ Correcta" else "#dc2626" if stat['final_status'] == "❌ Incorrecta" else "#d97706"
        et = re.sub(r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s*\([^)]*\))?:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip(), flags=re.IGNORECASE).strip() or "No hay explicación disponible."
        eh = "".join([f"<div style='margin-top: 3px; line-height: 1.3; color: #0c5460 !important;'>{p.strip()}</div>" for p in et.split('\n') if p.strip()])
        ph = f"<div style='text-align: justify; line-height: 1.3; margin-bottom: 4px; font-size: 14px; color: #334155 !important;'>{q['preamble']}</div>" if q.get('preamble') else ""
        st.markdown(
            f"<div style='margin-bottom: 5px;'>"
            f"<div style='color: {col} !important; font-size: 17px; font-weight: 700; margin-bottom: 4px;'>Pregunta {i+1} | {stat['final_status']} | Intentos: {stat['attempts']}</div>"
            f"{ph}"
            f"<div style='font-size:15px; color:#000000 !important; text-align: justify; line-height: 1.3; margin-bottom: 2px;'><b style='color:#000000 !important;'>Pregunta:</b> {q['question_text']}</div>"
            f"<div style='font-size:15px; color:#000000 !important; text-align: justify; line-height: 1.3; margin-bottom: 2px;'><b style='color:#000000 !important;'>Tu respuesta:</b> {stat['selected'] if stat['selected'] else 'Ninguna'}</div>"
            f"<div style='font-size:15px; color:#000000 !important; text-align: justify; line-height: 1.3; margin-bottom: 6px;'><b style='color:#000000 !important;'>Respuesta correcta:</b> {co}</div>"
            f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 10px; border-radius: 4px; margin-bottom: 6px;'><div style='font-size: 14px; font-weight: 600; margin-bottom: 2px; color: #0c5460 !important;'>Explicación:</div><div style='font-size: 14px; color: #0c5460 !important; text-align: justify;'>{eh}</div></div>"
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
    c1_b.button("🔄 Repetir Test", key="btn_rep_bot", on_click=action_repetir_test, use_container_width=True)
    c2_b.button("📁 Cambiar de Test", key="btn_sub_bot", on_click=action_subir_otro, use_container_width=True)
    c3_b.button("🚪 Finalizar Sesión", key="btn_out_bot", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
# === FIN SECCIÓN 5 ===
# --- FIN DEL ARCHIVO ---
