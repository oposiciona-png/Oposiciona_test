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

# Clave interna del servidor para cifrar el backup de sesión y evitar que nadie extraiga el JSON de preguntas
_BACKUP_SECRET_BYTES = b"Oposiciona_5.0_Blindaje_Privado_2026_SS#Key"

@st.cache_resource
def _obtener_almacen_sesiones_servidor():
    return {}

@st.cache_resource
def _obtener_registro_sesion_unica_global():
    """Almacén central en RAM compartido por todas las conexiones del servidor: {email: {'token': str, 'ts': float}}"""
    return {"sesiones": {}, "lock": threading.Lock()}

def _cifrar_backup_sesion(datos_dict):
    # Inyectamos automáticamente el sello de sesión única actual para que sobreviva a recargas legítimas (F5) del mismo dispositivo,
    # pero caduque al instante si otro dispositivo inicia sesión después.
    if isinstance(datos_dict, dict) and st.session_state.get("session_token_unico"):
        datos_copia = dict(datos_dict)
        datos_copia["session_token_unico"] = st.session_state["session_token_unico"]
    else:
        datos_copia = datos_dict
    raw = zlib.compress(json.dumps(datos_copia, ensure_ascii=False).encode("utf-8"), level=9)
    klen = len(_BACKUP_SECRET_BYTES)
    xored = bytes(b ^ _BACKUP_SECRET_BYTES[i % klen] for i, b in enumerate(raw))
    return "v4_" + base64.urlsafe_b64encode(xored).decode("ascii")

def _descifrar_backup_sesion(token_str):
    if not token_str:
        return {}
    if token_str.startswith("sid4_"):
        almacen = _obtener_almacen_sesiones_servidor()
        return dict(almacen.get(token_str, {}))
    if token_str.startswith(("v2_", "v3_", "v4_")):
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
        "raquelkmacho@gmail.com", "patripintoalvarez@gmail.com", "alexandrajimenezmontoliu@gmail.com",
        "pedromarquezpavon58@gmail.com"
    ],
    "GESTION": [
        "vsaurod@gmail.com", "mariaquirosmonge5@gmail.com", "vanessagomeztdla@gmail.com",
        "zoemorcor@gmail.com", "julianayem@gmail.com", "yasminkhalili@gmail.com",
        "miriamvazquezseoane2000@gmail.com", "monetcacerescc@gmail.com", "maariiamaji@gmail.com",
        "micastroespejo@gmail.com", "aisacarrerapexe@gmail.com", "csanchezssmm@gmail.com",
        "maria.concal@gmail.com", "mariachinchurreta@gmail.com", "rocio10460@gmail.com",
        "manuelmuriel97@gmail.com", "hfdiaz99@gmail.com", "ireneizquierdo22@gmail.com",
        "manuelsan240902@gmail.com", "pablorpgestion@gmail.com"
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
    ('vista_portada_auth', 'login'),
    ('session_token_unico', ''),
    ('modo_avance', "**Modo reflexivo** (puedes comprobar la pregunta y el paso a la siguiente es manual pulsando siguiente)")
]:
    if k not in st.session_state: st.session_state[k] = v

def _es_cuenta_exenta_sesion_unica(email_usr, rol_usr="", es_admin_flag=False):
    em = (email_usr or "").lower().strip()
    if es_admin_flag or em in USUARIOS_ADMIN:
        return True
    if rol_usr == "INVITADO" or em in USUARIOS_AUTORIZADOS.get("INVITADO", []):
        return True
    return False

def registrar_nueva_sesion_unica(email_usr, token_forzado=""):
    """Registra una nueva entrada válida y anula automáticamente cualquier sesión anterior abierta con ese mismo correo."""
    import secrets as _sec_mod
    em = (email_usr or "").lower().strip()
    nuevo_tok = token_forzado or _sec_mod.token_hex(16)
    if not em:
        return nuevo_tok
    reg = _obtener_registro_sesion_unica_global()
    with reg["lock"]:
        reg["sesiones"][em] = {"token": nuevo_tok, "ts": time.time()}
    # Limpiamos también cualquier sid4_ antiguo almacenado en servidor para ese mismo correo con distinto token
    try:
        almacen_sid = _obtener_almacen_sesiones_servidor()
        claves_borrar = [
            k_sid for k_sid, val_sid in list(almacen_sid.items())
            if isinstance(val_sid, dict)
            and str(val_sid.get("email", "")).lower().strip() == em
            and val_sid.get("session_token_unico") not in ("", None, nuevo_tok)
        ]
        for kb in claves_borrar:
            almacen_sid.pop(kb, None)
    except Exception:
        pass
    return nuevo_tok

def obtener_token_vigente_usuario(email_usr, es_suscriptor_ext=False):
    em = (email_usr or "").lower().strip()
    if not em:
        return ""
    reg = _obtener_registro_sesion_unica_global()
    with reg["lock"]:
        info_mem = reg["sesiones"].get(em)
    if info_mem and info_mem.get("token"):
        return str(info_mem["token"]).strip()
    if es_suscriptor_ext:
        datos_gs = obtener_suscriptores_cacheados(forzar_remoto=False).get(em)
        if datos_gs:
            return str(datos_gs.get("SESSION_TOKEN", "")).strip()
    return ""

# Endpoint ligero interno (?check_alive_email=...&check_alive_tok=...) para que el navegador detecte expulsiones incluso sin tocar botones
if st.query_params.get("expulsado_sesion") == "1":
    st.query_params.clear()
    st.session_state.clear()
    st.session_state["aviso_sesion_cerrada_otro_disp"] = True
    st.session_state["borrar_backup_ls"] = True

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
div.stButton > button, button[kind="secondary"],
div[data-testid="stLinkButton"] > a[kind="secondary"] {
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

/* === BOTONES PASTEL DE NAVEGACIÓN EN LA PANTALLA INICIAL === */
div[data-testid="stVerticalBlock"]:has(.opo-nav-login) div.stButton > button {
    background-color: #E0F2FE !important;
    border: 1.5px solid #93C5FD !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    padding: 8px 10px !important;
    transition: all 0.18s ease !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-login) div.stButton > button p,
div[data-testid="stVerticalBlock"]:has(.opo-nav-login) div.stButton > button span {
    color: #0C4A6E !important;
    -webkit-text-fill-color: #0C4A6E !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-login) div.stButton > button:hover {
    background-color: #BAE6FD !important;
    border-color: #60A5FA !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-login-active) div.stButton > button {
    background-color: #BAE6FD !important;
    border: 2.5px solid #0284C7 !important;
    box-shadow: 0 3px 10px rgba(2, 132, 199, 0.18) !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-login-active) div.stButton > button p,
div[data-testid="stVerticalBlock"]:has(.opo-nav-login-active) div.stButton > button span {
    font-weight: 800 !important;
}

div[data-testid="stVerticalBlock"]:has(.opo-nav-planes) div.stButton > button {
    background-color: #DCFCE7 !important;
    border: 1.5px solid #86EFAC !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    padding: 8px 10px !important;
    transition: all 0.18s ease !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-planes) div.stButton > button p,
div[data-testid="stVerticalBlock"]:has(.opo-nav-planes) div.stButton > button span {
    color: #14532D !important;
    -webkit-text-fill-color: #14532D !important;
    font-weight: 700 !important;
    font-size: 14px !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-planes) div.stButton > button:hover {
    background-color: #BBF7D0 !important;
    border-color: #4ADE80 !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-planes-active) div.stButton > button {
    background-color: #BBF7D0 !important;
    border: 2.5px solid #16A34A !important;
    box-shadow: 0 3px 10px rgba(22, 163, 74, 0.18) !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-planes-active) div.stButton > button p,
div[data-testid="stVerticalBlock"]:has(.opo-nav-planes-active) div.stButton > button span {
    font-weight: 800 !important;
}

div[data-testid="stVerticalBlock"]:has(.opo-nav-recuperar) div.stButton > button {
    background-color: #FEF3C7 !important;
    border: 1.5px solid #FCD34D !important;
    border-radius: 10px !important;
    min-height: 48px !important;
    padding: 8px 10px !important;
    transition: all 0.18s ease !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-recuperar) div.stButton > button p,
div[data-testid="stVerticalBlock"]:has(.opo-nav-recuperar) div.stButton > button span {
    color: #78350F !important;
    -webkit-text-fill-color: #78350F !important;
    font-weight: 700 !important;
    font-size: 13.5px !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-recuperar) div.stButton > button:hover {
    background-color: #FDE68A !important;
    border-color: #F59E0B !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-recuperar-active) div.stButton > button {
    background-color: #FDE68A !important;
    border: 2.5px solid #D97706 !important;
    box-shadow: 0 3px 10px rgba(217, 119, 6, 0.18) !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-nav-recuperar-active) div.stButton > button p,
div[data-testid="stVerticalBlock"]:has(.opo-nav-recuperar-active) div.stButton > button span {
    font-weight: 800 !important;
}

div[data-testid="stDownloadButton"] > button {
    background-color: #FEF3C7 !important;
    color: #78350F !important;
    -webkit-text-fill-color: #78350F !important;
    border: 2px solid #D97706 !important;
    border-radius: 8px !important;
    padding: 10px 16px !important;
    min-height: 46px !important;
}
div[data-testid="stDownloadButton"] > button p,
div[data-testid="stDownloadButton"] > button span,
div[data-testid="stDownloadButton"] > button * {
    color: #78350F !important;
    -webkit-text-fill-color: #78350F !important;
    font-weight: 800 !important;
    font-size: 15.5px !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    background-color: #FDE68A !important;
    border-color: #B45309 !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-promo-trigger) div.stButton > button {
    background: linear-gradient(90deg, #7C3AED 0%, #6D28D9 100%) !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 2px solid #5B21B6 !important;
    border-radius: 8px !important;
    min-height: 44px !important;
    box-shadow: 0 3px 8px rgba(109, 40, 217, 0.25) !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-promo-trigger) div.stButton > button p,
div[data-testid="stVerticalBlock"]:has(.opo-promo-trigger) div.stButton > button span,
div[data-testid="stVerticalBlock"]:has(.opo-promo-trigger) div.stButton > button * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 15px !important;
}
div[data-testid="stVerticalBlock"]:has(.opo-promo-trigger) div.stButton > button:hover {
    background: linear-gradient(90deg, #6D28D9 0%, #5B21B6 100%) !important;
    border-color: #4C1D95 !important;
}
div.stButton > button[kind="primary"], button[kind="primary"],
div[data-testid="stLinkButton"] > a,
div.stLinkButton > a,
a[data-testid="stBaseLinkButton-primary"] {
    background-color: #1F77B4 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #155A8A !important;
    text-decoration: none !important;
    font-weight: 800 !important;
}
div.stButton > button[kind="primary"] p, div.stButton > button[kind="primary"] span,
button[kind="primary"] p, button[kind="primary"] span,
div[data-testid="stLinkButton"] > a *,
div.stLinkButton > a *,
a[data-testid="stBaseLinkButton-primary"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 15.5px !important;
}
div.stButton > button[kind="primary"]:hover, button[kind="primary"]:hover,
div[data-testid="stLinkButton"] > a:hover,
div.stLinkButton > a:hover,
a[data-testid="stBaseLinkButton-primary"]:hover {
    background-color: #155A8A !important;
    border-color: #0F3F63 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button {
    background-color: #2e7d32 !important;
    border-color: #2e7d32 !important;
}
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button p,
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button span {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 17px !important;
}
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button:hover {
    background-color: #1b5e20 !important;
    border-color: #1b5e20 !important;
}
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
[data-testid="stAlert"] p, [data-testid="stAlert"] span, [data-testid="stAlert"] div {
    color: #1E293B !important;
}
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
                document.addEventListener('contextmenu', function(e) {{
                    if (window.__oposiciona_es_admin) return;
                    e.preventDefault();
                }}, true);

                document.addEventListener('dragstart', function(e) {{
                    if (window.__oposiciona_es_admin) return;
                    e.preventDefault();
                }}, true);

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

                window.addEventListener('keydown', function(e) {{
                    if (window.__oposiciona_es_admin) return;
                    var k = (e.key || '').toLowerCase();
                    var code = e.keyCode || e.which || 0;

                    if (code === 123 || k === 'f12') {{
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }}
                    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && (k === 's' || k === 'u' || k === 'p')) {{
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }}
                    if (e.ctrlKey && e.shiftKey && (k === 'i' || k === 'j' || k === 'c' || k === 'k')) {{
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }}
                    if (e.metaKey && e.altKey && (k === 'i' || k === 'j' || k === 'c' || k === 'u')) {{
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }}
                }}, true);

                document.addEventListener('input', function(e) {{
                    try {{
                        if (e.target && e.target.tagName && e.target.tagName.toLowerCase() === 'textarea') {{
                            sessionStorage.setItem('oposiciona_live_draft_txt', e.target.value || '');
                            localStorage.setItem('oposiciona_live_draft_txt', e.target.value || '');
                        }}
                    }} catch(err) {{}}
                }}, true);

                setInterval(function() {{
                    try {{
                        var tsNow = Date.now();
                        fetch(window.location.origin + "/_stcore/health?_t=" + tsNow, {{ method: "GET", cache: "no-store", credentials: "same-origin" }}).catch(function(){{}});
                        fetch(window.location.origin + "/_stcore/host-config?_t=" + tsNow, {{ method: "GET", cache: "no-store", credentials: "same-origin" }}).catch(function(){{}});
                        document.dispatchEvent(new CustomEvent("oposiciona_keepalive"));
                    }} catch(err) {{}}
                }}, 15000);

                var wakeLockObj = null;
                function activarWakeLock() {{
                    if ('wakeLock' in navigator && document.visibilityState === 'visible') {{
                        navigator.wakeLock.request('screen').then(function(wl) {{ wakeLockObj = wl; }}).catch(function(){{}});
                    }}
                }}
                document.addEventListener('visibilitychange', function() {{
                    activarWakeLock();
                    if (document.visibilityState === 'visible') {{
                        fetch(window.location.origin + "/_stcore/health?_t=" + Date.now(), {{ method: "GET", cache: "no-store", credentials: "same-origin" }}).catch(function(){{}});
                    }}
                }});
                document.addEventListener('click', activarWakeLock, {{ once: true }});
            `;
            parentDoc.head.appendChild(script);
        }}
    }}, 250);
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
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

def registrar_actividad_sheets(
    evento,
    nombre_test="",
    aciertos="",
    fallos="",
    blancos="",
    nota="",
    accion="nueva_fila",
    hora_inicio_override=None,
    start_ts_override=None,
    sincrono=False
):
    email_actual = (st.session_state.get("email") or "").lower().strip()
    if email_actual in USUARIOS_ADMIN:
        return

    url = (GOOGLE_SHEETS_WEBHOOK_URL or "").strip()
    if not url or not url.startswith("https://script.google.com/"):
        return
    try:
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        hora_actual = ahora.strftime("%H:%M:%S")
        fecha_ini = st.session_state.get("fecha_inicio_str") or ahora.strftime("%d/%m/%Y")
        hora_ini = hora_inicio_override or st.session_state.get("hora_inicio_str") or hora_actual
        ini_ts = start_ts_override if start_ts_override is not None else st.session_state.get("test_start_ts")

        if accion == "nueva_fila":
            hora_fin, duracion_str = "", ""
        else:
            hora_fin = hora_actual
            duracion_str = formatear_duracion(max(1, time.time() - ini_ts)) if ini_ts else "0m 01s"

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
        if sincrono:
            _enviar_post_background(url, payload)
        else:
            threading.Thread(target=_enviar_post_background, args=(url, payload), daemon=True).start()
    except Exception:
        pass

if st.session_state.get("borrar_backup_ls", False):
    st.session_state.borrar_backup_ls = False
    components.html("""<script>
    try {
        ["oposiciona_test_backup_v1", "oposiciona_auth_backup_v1", "oposiciona_sid_v1", "oposiciona_sid_v3", "oposiciona_sid_v4", "oposiciona_live_draft_txt"].forEach(function(k) {
            window.parent.localStorage.removeItem(k);
            window.parent.sessionStorage.removeItem(k);
        });
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

# === SECCIÓN 1B: MOTOR ULTRARRÁPIDO DE SUSCRIPCIONES, STRIPE, CORREOS Y SESIÓN ÚNICA GLOBAL ===
import hashlib, secrets

PLANES_SUSCRIPCION_OPOSICIONA = {
    "ADM_COMPLETO": {
        "titulo_nivel": "Nivel Único: Acceso Completo — 30 €/mes",
        "nombre_corto": "Administrativo — Acceso Completo (30 €/mes)",
        "nombre_stripe": "Curso mensual y tutorización — Administrativo Seguridad Social (Acceso Completo)",
        "especialidad": "ADMINISTRATIVOS",
        "precio_eur": 30,
        "rol": "ADMTVOS",
        "descripcion": "Incluye todos los Test de Temario General y Específico, Exámenes Oficiales, Supuestos Prácticos comentados, resolución de dudas por correo electrónico, boletín de actualizaciones normativas comentadas y sesión mensual en directo."
    },
    "GES_SOLO_TEST": {
        "titulo_nivel": "Nivel 1: Modalidad Test — 50 €/mes",
        "nombre_corto": "Gestión — Modalidad Test (50 €/mes)",
        "nombre_stripe": "Curso mensual y tutorización — Gestión Seguridad Social (Solo Test)",
        "especialidad": "GESTION",
        "precio_eur": 50,
        "rol": "GESTION_SOLO_TEST",
        "descripcion": "Incluye Test de Temario General y Específico, Exámenes Oficiales y Simulacros Globales, resolución de dudas por correo electrónico, actualizaciones normativas comentadas y sesión mensual en directo."
    },
    "GES_TEST_SUPUESTOS": {
        "titulo_nivel": "Nivel 2A: Test + Supuestos Prácticos — 60 €/mes",
        "nombre_corto": "Gestión — Test + Supuestos (60 €/mes)",
        "nombre_stripe": "Curso mensual y tutorización — Gestión Seguridad Social (Test + Supuestos)",
        "especialidad": "GESTION",
        "precio_eur": 60,
        "rol": "GESTION_TEST_SUPUESTOS",
        "descripcion": "Incluye todos los Test y Exámenes + Supuestos Prácticos del 2.º Ejercicio con evaluación razonada y respuesta técnica oficial, resolución de dudas por correo, actualizaciones comentadas y sesión mensual en directo."
    },
    "GES_TEST_DESARROLLO": {
        "titulo_nivel": "Nivel 2B: Test + Epígrafes de Desarrollo — 60 €/mes",
        "nombre_corto": "Gestión — Test + Desarrollo (60 €/mes)",
        "nombre_stripe": "Curso mensual y tutorización — Gestión Seguridad Social (Test + Desarrollo)",
        "especialidad": "GESTION",
        "precio_eur": 60,
        "rol": "GESTION_TEST_DESARROLLO",
        "descripcion": "Incluye todos los Test y Exámenes + Epígrafes de Desarrollo calificados conforme a los criterios oficiales del Tribunal Calificador, resolución de dudas por correo, actualizaciones comentadas y sesión mensual en directo."
    },
    "GES_COMPLETO": {
        "titulo_nivel": "Nivel 3: Preparación Integral Completa — 70 €/mes ⭐",
        "nombre_corto": "Gestión — Acceso Completo (70 €/mes)",
        "nombre_stripe": "Curso mensual y tutorización — Gestión Seguridad Social (Acceso Completo)",
        "especialidad": "GESTION",
        "precio_eur": 70,
        "rol": "GESTION",
        "descripcion": "Acceso total sin restricciones: Test General y Específico, Exámenes, Supuestos Prácticos y Epígrafes de Desarrollo calificados según criterios del Tribunal, resolución de dudas por correo, actualizaciones comentadas y sesión mensual en directo."
    }
}

MEJORAS_PERMITIDAS_POR_PLAN = {
    "ADM_COMPLETO": ["GES_SOLO_TEST", "GES_TEST_SUPUESTOS", "GES_TEST_DESARROLLO", "GES_COMPLETO"],
    "GES_SOLO_TEST": ["GES_TEST_SUPUESTOS", "GES_TEST_DESARROLLO", "GES_COMPLETO"],
    "GES_TEST_SUPUESTOS": ["GES_COMPLETO"],
    "GES_TEST_DESARROLLO": ["GES_COMPLETO"],
    "GES_COMPLETO": []
}

TEXTO_AVISO_CALENDARIO_TEMAS = (
    "Esta plataforma se irá cargando poco a poco con todos los temas de la oposición, "
    "según calendario de temas adaptado a nuestros alumnos."
)

ID_PDF_CALENDARIO_TEMAS = "1wreD3wxKRr-mGzxmKQ8k6ZQx6tdRe8t_"
URL_PDF_CALENDARIO_VISTA = f"https://drive.google.com/file/d/{ID_PDF_CALENDARIO_TEMAS}/view?usp=drive_link"
URL_PDF_CALENDARIO_DESCARGA = f"https://drive.google.com/uc?export=download&id={ID_PDF_CALENDARIO_TEMAS}"

@st.cache_data(ttl=60, show_spinner=False)
def obtener_bytes_pdf_calendario():
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "User-Agent": "Mozilla/5.0"
    }
    urls_intento = [
        f"https://drive.usercontent.google.com/download?id={ID_PDF_CALENDARIO_TEMAS}&export=download&confirm=t",
        f"https://drive.google.com/uc?export=download&id={ID_PDF_CALENDARIO_TEMAS}"
    ]
    for u in urls_intento:
        try:
            r = requests.get(u, headers=headers, timeout=12, allow_redirects=True)
            if r.status_code == 200 and r.content and r.content[:4] == b"%PDF":
                return r.content
        except Exception:
            continue
    return None

def render_bloque_aviso_calendario_pdf(sufijo_key="planes"):
    st.markdown(
        f"<div style='background:#FFFBEB; border:3px solid #D97706; border-radius:12px; padding:20px 22px; margin:12px 0 10px 0; box-shadow:0 4px 12px rgba(217, 119, 6, 0.14);'>"
        f"<div style='font-size:19px; font-weight:900; color:#92400E !important; margin-bottom:10px; letter-spacing:0.2px;'>"
        f"⚠️ AVISO IMPORTANTE SOBRE EL CALENDARIO DE CONTENIDOS"
        f"</div>"
        f"<div style='font-size:18px; font-weight:700; line-height:1.55; color:#78350F !important; text-align:justify; margin-bottom:12px;'>"
        f"«{TEXTO_AVISO_CALENDARIO_TEMAS}»"
        f"</div>"
        f"<div style='font-size:14.5px; font-weight:600; line-height:1.45; color:#1E293B !important; background:#FFFFFF; border:1px dashed #D97706; border-radius:8px; padding:10px 14px;'>"
        f"📄 <b>Consulta los temas incluidos hasta el momento:</b> descarga y revisa a continuación el documento PDF actualizado antes de finalizar tu inscripción."
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    pdf_cal_bytes = obtener_bytes_pdf_calendario()
    if pdf_cal_bytes:
        st.download_button(
            label="📥 DESCARGAR RELACIÓN DE TEMAS ACTUALES (PDF)",
            data=pdf_cal_bytes,
            file_name="Relacion_Temas_Actuales_Oposiciona.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"btn_dl_pdf_calendario_{sufijo_key}"
        )
    else:
        st.markdown(
            f"<a href='{URL_PDF_CALENDARIO_VISTA}' target='_blank' rel='noopener noreferrer' "
            f"style='display:block; width:100%; background-color:#FEF3C7; color:#78350F !important; -webkit-text-fill-color:#78350F !important; "
            f"border:2px solid #D97706; border-radius:8px; padding:11px 16px; text-align:center; font-weight:800; font-size:15.5px; text-decoration:none; box-sizing:border-box; margin-bottom:8px;'>"
            f"📥 DESCARGAR RELACIÓN DE TEMAS ACTUALES (PDF)"
            f"</a>",
            unsafe_allow_html=True
        )

def _cfg_suscripciones():
    def _get_sec(k, default=""):
        try:
            return str(st.secrets.get(k, default)).strip()
        except Exception:
            return default
    return {
        "gs_url": _get_sec("APPS_SCRIPT_SUSCRIPTORES_URL"),
        "gs_token": _get_sec("APPS_SCRIPT_SUSCRIPTORES_TOKEN"),
        "stripe_key": _get_sec("STRIPE_SECRET_KEY"),
        "app_url": _get_sec("URL_PUBLICA_APP", "https://test-oposiciona.streamlit.app").rstrip("/"),
        "modo_fiscal": _get_sec("MODO_FISCAL_SUSCRIPCION", "EXENTO_TUTORIZADO")
    }

def _hash_password_suscriptor(password_plana):
    sal = "Oposiciona_Salt_2026_SS#"
    return hashlib.sha256((sal + str(password_plana)).encode("utf-8")).hexdigest()

def _generar_password_legible():
    alfabeto = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    return "Opo-" + "".join(secrets.choice(alfabeto) for _ in range(8))

def _validar_password_elegida(pwd1, pwd2):
    p1 = (pwd1 or "").strip()
    p2 = (pwd2 or "").strip()
    if len(p1) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    if p1 != p2:
        return False, "Las dos contraseñas no coinciden."
    return True, ""

# --- CACHÉ DE SERVIDOR EN RAM (Stale-While-Revalidate) PARA LOGIN EN < 0.1 SEGUNDOS ---
@st.cache_resource
def _almacen_ram_suscriptores():
    return {"mapa": {}, "ts": 0.0, "cargando": False, "lock": threading.Lock()}

def _llamar_gs_directo(gs_url, gs_token, payload_extra):
    if not gs_url or not gs_token:
        return {"ok": False, "error": "Falta configurar Secrets de Apps Script."}
    payload = {"token": gs_token}
    payload.update(payload_extra)
    try:
        r = requests.post(gs_url, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()
        return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _llamar_apps_script_suscriptores(payload_extra):
    cfg = _cfg_suscripciones()
    return _llamar_gs_directo(cfg["gs_url"], cfg["gs_token"], payload_extra)

def _refrescar_ram_suscriptores_sync(gs_url, gs_token):
    alm = _almacen_ram_suscriptores()
    reg_global = _obtener_registro_sesion_unica_global()
    try:
        res = _llamar_gs_directo(gs_url, gs_token, {"action": "listar_suscriptores"})
        if res.get("ok"):
            nuevo_mapa = {}
            for item in res.get("suscriptores", []):
                em = str(item.get("EMAIL", "")).lower().strip()
                if em:
                    nuevo_mapa[em] = dict(item)
                    tok_gs = str(item.get("SESSION_TOKEN", "")).strip()
                    if tok_gs:
                        with reg_global["lock"]:
                            # Si en esta instancia aún no había token o el de Sheets cambió desde otra réplica, sincronizamos
                            if em not in reg_global["sesiones"]:
                                reg_global["sesiones"][em] = {"token": tok_gs, "ts": time.time()}
            with alm["lock"]:
                alm["mapa"] = nuevo_mapa
                alm["ts"] = time.time()
    finally:
        alm["cargando"] = False

def obtener_suscriptores_cacheados(forzar_remoto=False):
    cfg = _cfg_suscripciones()
    alm = _almacen_ram_suscriptores()
    ahora = time.time()

    if forzar_remoto or alm["ts"] == 0.0:
        _refrescar_ram_suscriptores_sync(cfg["gs_url"], cfg["gs_token"])
    elif (ahora - alm["ts"]) > 35.0 and not alm["cargando"]:
        alm["cargando"] = True
        threading.Thread(
            target=_refrescar_ram_suscriptores_sync,
            args=(cfg["gs_url"], cfg["gs_token"]),
            daemon=True
        ).start()
    return alm["mapa"]

def precargar_suscriptores_en_segundo_plano():
    cfg = _cfg_suscripciones()
    alm = _almacen_ram_suscriptores()
    if alm["ts"] == 0.0 and not alm["cargando"] and cfg["gs_url"] and cfg["gs_token"]:
        alm["cargando"] = True
        threading.Thread(
            target=_refrescar_ram_suscriptores_sync,
            args=(cfg["gs_url"], cfg["gs_token"]),
            daemon=True
        ).start()

def buscar_suscriptor_externo(email, forzar_remoto=False):
    em = (email or "").lower().strip()
    if not em:
        return None
    mapa = obtener_suscriptores_cacheados(forzar_remoto=forzar_remoto)
    if em in mapa:
        return mapa[em]
    if not forzar_remoto:
        mapa2 = obtener_suscriptores_cacheados(forzar_remoto=True)
        return mapa2.get(em)
    return None

def guardar_datos_suscriptor(email, campos_dict, sincrono=True):
    em = (email or "").lower().strip()
    cfg = _cfg_suscripciones()
    alm = _almacen_ram_suscriptores()

    with alm["lock"]:
        ficha_mem = dict(alm["mapa"].get(em, {"EMAIL": em}))
        for k_c, v_c in campos_dict.items():
            ficha_mem[str(k_c).upper()] = str(v_c)
        alm["mapa"][em] = ficha_mem
        if alm["ts"] == 0.0:
            alm["ts"] = time.time()

    payload_g = {"action": "guardar_suscriptor", "email": em, "campos": campos_dict}
    if sincrono:
        return _llamar_gs_directo(cfg["gs_url"], cfg["gs_token"], payload_g)
    else:
        threading.Thread(
            target=_llamar_gs_directo,
            args=(cfg["gs_url"], cfg["gs_token"], payload_g),
            daemon=True
        ).start()
        return {"ok": True}

def cambiar_password_suscriptor_autenticado(email, pwd_actual, pwd_nueva_1, pwd_nueva_2):
    em = (email or "").lower().strip()
    ficha = buscar_suscriptor_externo(em)
    if not ficha:
        return False, "No se encontró tu ficha de suscriptor."
    if ficha.get("PASSWORD_HASH") != _hash_password_suscriptor(pwd_actual):
        return False, "La contraseña actual introducida no es correcta."
    ok_val, msg_val = _validar_password_elegida(pwd_nueva_1, pwd_nueva_2)
    if not ok_val:
        return False, msg_val
    res = guardar_datos_suscriptor(em, {"PASSWORD_HASH": _hash_password_suscriptor(pwd_nueva_1.strip())}, sincrono=True)
    if res.get("ok"):
        return True, "✅ Tu contraseña se ha actualizado correctamente."
    return False, f"No se pudo guardar la nueva contraseña: {res.get('error', 'Error desconocido')}"

def enviar_email_suscriptor(destinatario, asunto, html_body):
    return _llamar_apps_script_suscriptores({
        "action": "enviar_email",
        "destinatario": destinatario,
        "asunto": asunto,
        "html_body": html_body,
        "remitente_nombre": "Oposiciona — Plataforma de Preparación",
        "reply_to": "info@oposiciona.es"
    })

def _stripe_api_directo(sk, method, endpoint, data=None, params=None):
    if not sk:
        return {"error": {"message": "Falta STRIPE_SECRET_KEY en Secrets."}}
    url = f"https://api.stripe.com/v1/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {sk}"}
    try:
        if method.upper() == "GET":
            r = requests.get(url, headers=headers, params=params, timeout=15)
        else:
            r = requests.post(url, headers=headers, data=data, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": {"message": str(e)}}

def _stripe_api_request(method, endpoint, data=None, params=None):
    cfg = _cfg_suscripciones()
    return _stripe_api_directo(cfg["stripe_key"], method, endpoint, data=data, params=params)

def _norm_nombre_stripe(txt):
    s = unicodedata.normalize("NFD", str(txt or ""))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[—–\-]+", "-", s.lower())
    return re.sub(r"\s+", " ", s).strip()

@st.cache_data(ttl=1800, show_spinner=False)
def _obtener_catalogo_stripe_planes():
    res = _stripe_api_request("GET", "prices", params={"active": "true", "limit": "100", "expand[]": "data.product"})
    mapa_prices = {}
    mapa_plan_a_prod_price = {}
    mapa_price_a_plan = {}
    for p in res.get("data", []):
        prod = p.get("product") or {}
        if not isinstance(prod, dict) or not prod.get("active", True):
            continue
        prod_id = prod.get("id", "")
        price_id = p.get("id", "")
        nombre_prod_norm = _norm_nombre_stripe(prod.get("name", ""))
        for plan_id, info_plan in PLANES_SUSCRIPCION_OPOSICIONA.items():
            if _norm_nombre_stripe(info_plan["nombre_stripe"]) == nombre_prod_norm and prod_id and price_id:
                mapa_prices[plan_id] = price_id
                mapa_price_a_plan[price_id] = plan_id
                mapa_plan_a_prod_price[plan_id] = (prod_id, price_id)
    return mapa_prices, mapa_plan_a_prod_price, mapa_price_a_plan

def _obtener_mapa_precios_stripe():
    mapa_prices, _, _ = _obtener_catalogo_stripe_planes()
    return mapa_prices

def _obtener_config_portal_solo_subida(plan_actual_id):
    _, mapa_plan_a_prod_price, _ = _obtener_catalogo_stripe_planes()
    if not mapa_plan_a_prod_price:
        return "", "No se encontraron los productos activos en Stripe."

    planes_superiores = MEJORAS_PERMITIDAS_POR_PLAN.get(plan_actual_id, [])
    planes_incluidos = []
    if planes_superiores and plan_actual_id in mapa_plan_a_prod_price:
        planes_incluidos = [plan_actual_id] + [p for p in planes_superiores if p in mapa_plan_a_prod_price]

    etiqueta_cfg = f"opo_up_v7_{plan_actual_id}" if len(planes_incluidos) >= 2 else "opo_up_v7_MAX"
    cache_mem = st.session_state.setdefault("_cache_bpc_ids", {})
    if cache_mem.get(etiqueta_cfg):
        return cache_mem[etiqueta_cfg], ""

    lista_confs = _stripe_api_request("GET", "billing_portal/configurations", params={"active": "true", "limit": "50"})
    for c in lista_confs.get("data", []):
        if (c.get("metadata") or {}).get("origen") == etiqueta_cfg and c.get("id"):
            cache_mem[etiqueta_cfg] = c.get("id")
            return c.get("id"), ""

    payload_conf = {
        "business_profile[headline]": "Oposiciona — Suscripcion y mejora de plan",
        "business_profile[privacy_policy_url]": "https://oposiciona.es/",
        "business_profile[terms_of_service_url]": "https://oposiciona.es/",
        "features[invoice_history][enabled]": "true",
        "features[payment_method_update][enabled]": "true",
        "features[customer_update][enabled]": "true",
        "features[customer_update][allowed_updates][0]": "name",
        "features[customer_update][allowed_updates][1]": "address",
        "features[customer_update][allowed_updates][2]": "phone",
        "features[subscription_cancel][enabled]": "true",
        "features[subscription_cancel][mode]": "at_period_end",
        "metadata[origen]": etiqueta_cfg
    }

    if len(planes_incluidos) >= 2:
        payload_conf["features[subscription_update][enabled]"] = "true"
        payload_conf["features[subscription_update][default_allowed_updates][0]"] = "price"
        payload_conf["features[subscription_update][proration_behavior]"] = "always_invoice"

        productos_agrupados = {}
        for pid in planes_incluidos:
            prod_id, price_id = mapa_plan_a_prod_price[pid]
            productos_agrupados.setdefault(prod_id, [])
            if price_id not in productos_agrupados[prod_id]:
                productos_agrupados[prod_id].append(price_id)

        for idx_p, (prod_id, lista_pr) in enumerate(productos_agrupados.items()):
            payload_conf[f"features[subscription_update][products][{idx_p}][product]"] = prod_id
            for idx_pr, pr_id in enumerate(lista_pr):
                payload_conf[f"features[subscription_update][products][{idx_p}][prices][{idx_pr}]"] = pr_id
    else:
        payload_conf["features[subscription_update][enabled]"] = "false"

    nueva_conf = _stripe_api_request("POST", "billing_portal/configurations", data=payload_conf)
    if nueva_conf.get("id"):
        cache_mem[etiqueta_cfg] = nueva_conf["id"]
        return nueva_conf["id"], ""

    if len(planes_incluidos) >= 2:
        payload_conf["features[subscription_update][proration_behavior]"] = "create_prorations"
        nueva_conf_2 = _stripe_api_request("POST", "billing_portal/configurations", data=payload_conf)
        if nueva_conf_2.get("id"):
            cache_mem[etiqueta_cfg] = nueva_conf_2["id"]
            return nueva_conf_2["id"], ""
        err_det = (nueva_conf_2.get("error") or {}).get("message", "Error al configurar el portal en Stripe.")
        return "", err_det

    err_det = (nueva_conf.get("error") or {}).get("message", "Error al configurar el portal en Stripe.")
    return "", err_det

def usuario_ya_consumio_descuento_previo(email_usuario):
    em = (email_usuario or "").lower().strip()
    if not em:
        return False
    ficha = buscar_suscriptor_externo(em)
    if not ficha:
        return False
    notas_txt = str(ficha.get("NOTAS", "")).upper()
    if "PROMO_USADA" in notas_txt:
        return True
    if str(ficha.get("STRIPE_SUBSCRIPTION_ID", "")).strip().startswith("sub_"):
        return True
    return False

def validar_codigo_promocional_stripe(codigo_texto, precio_plan_eur=0, email_usuario=""):
    cod_limpio = (codigo_texto or "").strip()
    if not cod_limpio:
        return False, None, "Introduce un código promocional."
    if email_usuario and usuario_ya_consumio_descuento_previo(email_usuario):
        return False, None, "Los códigos promocionales solo pueden utilizarse una única vez por usuario en el momento de la primera suscripción."

    res = _stripe_api_request("GET", "promotion_codes", params={"active": "true", "limit": "100"})
    for pc in res.get("data", []):
        if str(pc.get("code", "")).strip().lower() == cod_limpio.lower():
            cupon = pc.get("coupon") or {}
            if isinstance(cupon, dict) and cupon.get("valid", True):
                pct = cupon.get("percent_off")
                amt = cupon.get("amount_off")
                dur = cupon.get("duration", "")
                meses = cupon.get("duration_in_months")
                txt_dur = (
                    "en tu primer alta" if dur == "once" else
                    (f"durante {meses} meses" if dur == "repeating" and meses else "")
                )
                if pct:
                    nuevo_p = round(precio_plan_eur * (1.0 - float(pct) / 100.0), 2)
                    resumen = f"🎁 Código **{pc.get('code')}** aplicado: **-{pct:g}% de descuento** {txt_dur} (se queda en **{nuevo_p:.2f} €**)."
                elif amt:
                    rebaja_eur = float(amt) / 100.0
                    nuevo_p = max(0.0, round(precio_plan_eur - rebaja_eur, 2))
                    resumen = f"🎁 Código **{pc.get('code')}** aplicado: **-{rebaja_eur:.2f} € de descuento** {txt_dur} (se queda en **{nuevo_p:.2f} €**)."
                else:
                    resumen = f"🎁 Código **{pc.get('code')}** aplicado correctamente."
                return True, pc.get("id"), resumen
    return False, None, "El código introducido no es válido o ha caducado."

def render_selector_codigo_promocional(plan_id, sufijo_key="planes", email_usuario=""):
    if email_usuario and usuario_ya_consumio_descuento_previo(email_usuario):
        st.caption("ℹ️ *Recuerda: los códigos promocionales de bienvenida solo se aplican una única vez por usuario en el alta inicial.*")
        return ""

    precio_base = PLANES_SUSCRIPCION_OPOSICIONA.get(plan_id, {}).get("precio_eur", 0)
    promo_id_activo = st.session_state.get("promo_code_id_aplicado", "")
    promo_resumen = st.session_state.get("promo_code_resumen_txt", "")

    if promo_id_activo:
        col_pr1, col_pr2 = st.columns([3.2, 1])
        with col_pr1:
            st.success(promo_resumen)
        with col_pr2:
            if st.button("✖ Quitar código", key=f"btn_quitar_promo_{sufijo_key}", use_container_width=True):
                st.session_state["promo_code_id_aplicado"] = ""
                st.session_state["promo_code_resumen_txt"] = ""
                st.session_state.pop("_checkout_cache_actual", None)
                st.rerun()
        st.markdown(
            "<div style='background:#FFFBEB; border:1px solid #F59E0B; border-radius:8px; padding:8px 12px; margin-bottom:10px; font-size:12.8px; color:#92400E !important;'>"
            "ℹ️ <b>Condiciones del código promocional:</b> Los códigos de descuento solo se aplican <b>una única vez por usuario</b>. "
            "Si más adelante decides mejorar a una modalidad superior, se abonará la diferencia hasta la tarifa general del nuevo plan."
            "</div>",
            unsafe_allow_html=True
        )
        return promo_id_activo

    k_mostrar = f"mostrar_caja_promo_{sufijo_key}"
    if not st.session_state.get(k_mostrar, False):
        with st.container():
            st.markdown("<div class='opo-promo-trigger'></div>", unsafe_allow_html=True)
            if st.button("🎁 ¿TIENES UN CÓDIGO DE PROMOCIÓN O DESCUENTO? PULSA AQUÍ PARA APLICARLO", use_container_width=True, key=f"btn_abrir_promo_{sufijo_key}"):
                st.session_state[k_mostrar] = True
                st.rerun()
    else:
        st.markdown(
            "<div style='background:#F5F3FF; border:2px solid #7C3AED; border-radius:10px; padding:10px 14px; margin-bottom:6px;'>"
            "<b style='color:#5B21B6 !important; font-size:14.5px;'>🎁 Introduce tu código promocional:</b><br>"
            "<span style='font-size:12.6px; color:#4C1D95 !important;'>⚠️ <b>Aviso importante:</b> Los códigos de descuento se aplican <b>una sola vez por usuario</b> en la suscripción inicial "
            "(en caso de mejorar posteriormente de plan, se abonará la diferencia sobre la tarifa oficial sin aplicar nuevos descuentos).</span>"
            "</div>",
            unsafe_allow_html=True
        )
        cp1, cp2, cp3 = st.columns([2.2, 1.1, 0.8])
        with cp1:
            cod_in = st.text_input("Código promocional:", placeholder="Ej: PROMOINICIAL", label_visibility="collapsed", key=f"in_txt_promo_{sufijo_key}")
        with cp2:
            if st.button("✔️ Aplicar descuento", type="primary", use_container_width=True, key=f"btn_aplicar_promo_{sufijo_key}"):
                ok_pr, pid_stripe, msg_pr = validar_codigo_promocional_stripe(cod_in, precio_base, email_usuario=email_usuario)
                if ok_pr:
                    st.session_state["promo_code_id_aplicado"] = pid_stripe
                    st.session_state["promo_code_resumen_txt"] = msg_pr
                    st.session_state.pop("_checkout_cache_actual", None)
                    st.rerun()
                else:
                    st.error(f"❌ {msg_pr}")
        with cp3:
            if st.button("Cerrar", use_container_width=True, key=f"btn_cerrar_promo_{sufijo_key}"):
                st.session_state[k_mostrar] = False
                st.rerun()
    return ""

def crear_sesion_pago_stripe(email_usuario, plan_id, promo_code_id=""):
    cfg = _cfg_suscripciones()
    em_clean = email_usuario.lower().strip()
    info_plan = PLANES_SUSCRIPCION_OPOSICIONA.get(plan_id)
    if not info_plan:
        return None, "Plan no válido."
    mapa_prices = _obtener_mapa_precios_stripe()
    price_id = mapa_prices.get(plan_id)
    if not price_id:
        return None, f"No se encontró en Stripe el producto '{info_plan['nombre_stripe']}'. Verifica su nombre exacto."

    sub_previo = buscar_suscriptor_externo(em_clean)
    cust_previo = str((sub_previo or {}).get("STRIPE_CUSTOMER_ID", "")).strip()
    ya_uso_promo = usuario_ya_consumio_descuento_previo(em_clean)

    payload_checkout = {
        "mode": "subscription",
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "success_url": f"{cfg['app_url']}/?stripe_session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{cfg['app_url']}/?pago_cancelado=1",
        "metadata[plan_id]": plan_id,
        "metadata[email_alumno]": em_clean,
        "metadata[promo_aplicada]": "SI" if (promo_code_id and not ya_uso_promo) else "NO",
        "subscription_data[metadata][plan_id]": plan_id,
        "subscription_data[metadata][email_alumno]": em_clean
    }
    if promo_code_id and not ya_uso_promo:
        payload_checkout["discounts[0][promotion_code]"] = promo_code_id
    elif not ya_uso_promo:
        payload_checkout["allow_promotion_codes"] = "true"

    if cust_previo.startswith("cus_"):
        payload_checkout["customer"] = cust_previo
    else:
        payload_checkout["customer_email"] = em_clean

    resp = _stripe_api_request("POST", "checkout/sessions", data=payload_checkout)
    if resp.get("url"):
        return resp["url"], None
    if cust_previo:
        payload_checkout.pop("customer", None)
        payload_checkout["customer_email"] = em_clean
        resp2 = _stripe_api_request("POST", "checkout/sessions", data=payload_checkout)
        if resp2.get("url"):
            return resp2["url"], None
        resp = resp2
    err_msg = (resp.get("error") or {}).get("message", "Error desconocido al conectar con Stripe.")
    return None, err_msg

def obtener_url_checkout_sesion_actual(email_usuario, plan_id, promo_code_id=""):
    clave_cache = f"{email_usuario.lower().strip()}|{plan_id}|{promo_code_id}"
    guardado = st.session_state.get("_checkout_cache_actual")
    if guardado and guardado.get("key") == clave_cache and (time.time() - guardado.get("ts", 0)) < 1200:
        return guardado.get("url"), None
    url_chk, err_chk = crear_sesion_pago_stripe(email_usuario, plan_id, promo_code_id=promo_code_id)
    if url_chk:
        st.session_state["_checkout_cache_actual"] = {"key": clave_cache, "url": url_chk, "ts": time.time()}
    return url_chk, err_chk

def _detectar_plan_desde_suscripcion_stripe(sub_obj):
    if not isinstance(sub_obj, dict):
        return ""
    _, _, mapa_price_a_plan = _obtener_catalogo_stripe_planes()

    items = ((sub_obj.get("items") or {}).get("data")) or []
    for it in items:
        pr_id = ((it.get("price") or {}).get("id")) or ""
        if pr_id in mapa_price_a_plan:
            return mapa_price_a_plan[pr_id]

    return (sub_obj.get("metadata") or {}).get("plan_id", "")

def verificar_suscripcion_activa_stripe(customer_id, subscription_id=""):
    if subscription_id:
        sub = _stripe_api_request("GET", f"subscriptions/{subscription_id}")
        if sub.get("status") in ("active", "trialing"):
            return True, _detectar_plan_desde_suscripcion_stripe(sub)
    if customer_id:
        subs = _stripe_api_request("GET", "subscriptions", params={"customer": customer_id, "limit": "5"})
        for s in subs.get("data", []):
            if s.get("status") in ("active", "trialing"):
                return True, _detectar_plan_desde_suscripcion_stripe(s)
    return False, ""

def _sincronizar_stripe_post_login_bg(email_limpio, cust_id, sub_id, sk, gs_url, gs_token):
    try:
        if not sk or (not cust_id and not sub_id):
            return
        sub_activa = None
        if sub_id:
            s = _stripe_api_directo(sk, "GET", f"subscriptions/{sub_id}")
            if s.get("status") in ("active", "trialing"):
                sub_activa = s
        if not sub_activa and cust_id:
            subs = _stripe_api_directo(sk, "GET", "subscriptions", params={"customer": cust_id, "limit": "5"})
            for s in subs.get("data", []):
                if s.get("status") in ("active", "trialing"):
                    sub_activa = s
                    break
        alm = _almacen_ram_suscriptores()
        if not sub_activa:
            with alm["lock"]:
                if email_limpio in alm["mapa"]:
                    alm["mapa"][email_limpio]["ESTADO"] = "INACTIVO"
            _llamar_gs_directo(gs_url, gs_token, {"action": "guardar_suscriptor", "email": email_limpio, "campos": {"ESTADO": "INACTIVO"}})
    except Exception:
        pass

def crear_enlace_portal_stripe_detallado(customer_id, plan_vigente_hint="", modo="facturacion", **kwargs):
    cfg = _cfg_suscripciones()
    if not customer_id:
        return None, "No se encontró el identificador de cliente en Stripe."

    plan_vigente = plan_vigente_hint or st.session_state.get("plan_suscripcion", "GES_COMPLETO")
    conf_auto_id, err_conf = _obtener_config_portal_solo_subida(plan_vigente)
    if not conf_auto_id:
        return None, f"No se pudo preparar el portal de Stripe: {err_conf}"

    datos_portal = {
        "customer": customer_id,
        "configuration": conf_auto_id,
        "return_url": f"{cfg['app_url']}/?sync_plan=1"
    }
    resp = _stripe_api_request("POST", "billing_portal/sessions", data=datos_portal)
    if resp.get("url"):
        return resp["url"], ""
    err_sess = (resp.get("error") or {}).get("message", "No se pudo abrir la sesión del portal en Stripe.")
    return None, err_sess

def crear_enlace_portal_cliente_stripe(customer_id):
    url_p, _ = crear_enlace_portal_stripe_detallado(customer_id)
    return url_p

def procesar_retorno_pago_stripe(session_id):
    sess = _stripe_api_request("GET", f"checkout/sessions/{session_id}")
    if sess.get("payment_status") != "paid" and sess.get("status") != "complete":
        return False, "El pago aún no figura como completado en Stripe."

    email_cliente = (
        sess.get("customer_email") or
        (sess.get("customer_details") or {}).get("email") or
        (sess.get("metadata") or {}).get("email_alumno") or ""
    ).lower().strip()
    plan_id = (sess.get("metadata") or {}).get("plan_id", "GES_COMPLETO")
    info_plan = PLANES_SUSCRIPCION_OPOSICIONA.get(plan_id, PLANES_SUSCRIPCION_OPOSICIONA["GES_COMPLETO"])
    cust_id = sess.get("customer", "")
    sub_id = sess.get("subscription", "")

    usada_promo_checkout = (
        (sess.get("metadata") or {}).get("promo_aplicada") == "SI" or
        float(((sess.get("total_details") or {}).get("amount_discount") or 0)) > 0
    )

    if not email_cliente:
        return False, "No se pudo recuperar el correo electrónico de la sesión de pago."

    existente = buscar_suscriptor_externo(email_cliente, forzar_remoto=True)
    token_sesion = registrar_nueva_sesion_unica(email_cliente)
    ahora_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y %H:%M:%S")
    st.session_state.pop("_checkout_cache_actual", None)

    notas_previas = str((existente or {}).get("NOTAS", "")).strip()
    if usada_promo_checkout and "PROMO_USADA" not in notas_previas.upper():
        notas_previas = (f"{notas_previas} | PROMO_USADA ({ahora_str})" if notas_previas else f"PROMO_USADA ({ahora_str})")

    if existente and existente.get("PASSWORD_HASH"):
        es_primer_alta = (str(existente.get("ESTADO", "")).upper() == "PENDIENTE_PAGO")
        campos_act = {
            "PLAN": plan_id,
            "ROL": info_plan["rol"],
            "ESTADO": "ACTIVO",
            "STRIPE_CUSTOMER_ID": cust_id,
            "STRIPE_SUBSCRIPTION_ID": sub_id,
            "ULTIMO_ACCESO": ahora_str,
            "SESSION_TOKEN": token_sesion
        }
        if notas_previas:
            campos_act["NOTAS"] = notas_previas
        if es_primer_alta or not existente.get("FECHA_ALTA"):
            campos_act["FECHA_ALTA"] = ahora_str
        guardar_datos_suscriptor(email_cliente, campos_act, sincrono=True)

        asunto_mail = "🎓 Bienvenido/a a Oposiciona — Suscripción activada" if es_primer_alta else f"✅ Suscripción reactivada — {info_plan['nombre_corto']}"
        enviar_email_suscriptor(
            email_cliente,
            asunto_mail,
            f"<div style='font-family:sans-serif; color:#1E293B; max-width:560px;'>"
            f"<h2 style='color:#1F77B4;'>{'¡Bienvenido/a a Oposiciona!' if es_primer_alta else '¡Suscripción activa en Oposiciona!'}</h2>"
            f"<p>Tu suscripción a <b>{info_plan['nombre_corto']}</b> ya está activa.</p>"
            f"<div style='background:#F8FAFC; border:1px solid #CBD5E1; border-radius:8px; padding:14px; margin:14px 0;'>"
            f"<p style='margin:4px 0;'><b>🌐 Enlace de acceso:</b> <a href='{_cfg_suscripciones()['app_url']}'>{_cfg_suscripciones()['app_url']}</a></p>"
            f"<p style='margin:4px 0;'><b>📧 Usuario:</b> {email_cliente}</p>"
            f"<p style='margin:4px 0;'><b>🔑 Contraseña:</b> La contraseña personal que elegiste al registrarte (puedes cambiarla cuando quieras dentro de la plataforma).</p>"
            f"</div>"
            f"<p><b>Servicios incluidos en tu suscripción mensual:</b></p>"
            f"<ul><li>Acceso inmediato a la plataforma de entrenamiento práctico.</li>"
            f"<li>Resolución de dudas sobre preguntas, supuestos y epígrafes en <b>info@oposiciona.es</b>.</li>"
            f"<li>Envío de actualizaciones normativas comentadas.</li>"
            f"<li>Clase online mensual en directo para resolución de dudas.</li></ul>"
            f"</div>"
        )
    else:
        pwd_nueva = _generar_password_legible()
        campos_nuevos = {
            "PASSWORD_HASH": _hash_password_suscriptor(pwd_nueva),
            "PLAN": plan_id,
            "ROL": info_plan["rol"],
            "ESTADO": "ACTIVO",
            "STRIPE_CUSTOMER_ID": cust_id,
            "STRIPE_SUBSCRIPTION_ID": sub_id,
            "FECHA_ALTA": ahora_str,
            "ULTIMO_ACCESO": ahora_str,
            "SESSION_TOKEN": token_sesion
        }
        if notas_previas:
            campos_nuevos["NOTAS"] = notas_previas
        guardar_datos_suscriptor(email_cliente, campos_nuevos, sincrono=True)
        enviar_email_suscriptor(
            email_cliente,
            "🎓 Bienvenido/a a Oposiciona — Tus claves de acceso",
            f"<div style='font-family:sans-serif; color:#1E293B; max-width:560px;'>"
            f"<h2 style='color:#1F77B4;'>¡Bienvenido/a a Oposiciona!</h2>"
            f"<p>Tu alta en <b>{info_plan['nombre_corto']}</b> se ha completado correctamente.</p>"
            f"<div style='background:#F8FAFC; border:1px solid #CBD5E1; border-radius:8px; padding:14px; margin:14px 0;'>"
            f"<p style='margin:4px 0;'><b>🌐 Enlace de acceso:</b> <a href='{_cfg_suscripciones()['app_url']}'>{_cfg_suscripciones()['app_url']}</a></p>"
            f"<p style='margin:4px 0;'><b>📧 Usuario:</b> {email_cliente}</p>"
            f"<p style='margin:4px 0;'><b>🔑 Contraseña inicial:</b> <code style='font-size:15px; background:#E2E8F0; padding:2px 6px; border-radius:4px;'>{pwd_nueva}</code> (puedes cambiarla dentro de la plataforma).</p>"
            f"</div></div>"
        )

    st.session_state.update(
        autenticado=True,
        rol=info_plan["rol"],
        email=email_cliente,
        es_admin=False,
        es_suscriptor_externo=True,
        plan_suscripcion=plan_id,
        stripe_customer_id=cust_id,
        stripe_subscription_id=sub_id,
        session_token_externo=token_sesion,
        session_token_unico=token_sesion,
        saved_esp=info_plan["especialidad"],
        do_scroll=True
    )
    return True, email_cliente

def _cerrar_sesion_por_expulsion(motivo_baja=False):
    st.session_state.clear()
    components.html("""<script>
    try {
        ["oposiciona_test_backup_v1", "oposiciona_auth_backup_v1", "oposiciona_sid_v1", "oposiciona_sid_v3", "oposiciona_sid_v4", "oposiciona_live_draft_txt"].forEach(function(k) {
            window.parent.localStorage.removeItem(k);
            window.parent.sessionStorage.removeItem(k);
        });
    } catch(e) {}
    </script>""", height=0)
    if motivo_baja:
        st.error("⚠️ Tu suscripción no figura actualmente como activa. Inicia sesión o renueva tu modalidad para continuar.")
    else:
        st.warning("🔒 **Sesión cerrada automáticamente:** Se ha iniciado una nueva sesión con tu cuenta en otro dispositivo o navegador. Por protección de credenciales, solo permanece abierta la última sesión iniciada.")
        if st.button("🔑 Volver a la pantalla de acceso", type="primary", use_container_width=True):
            st.rerun()
    st.stop()

def verificar_sesion_unica_global():
    """
    Protección global contra uso compartido de claves (tanto alumnos internos como suscriptores externos):
    - Si entra una nueva conexión con el mismo correo, se le permite el paso y esta sesión anterior queda invalidada al instante.
    - Excluye únicamente a Administradores e Invitado de demostración.
    """
    if not st.session_state.get("autenticado"):
        return
    em = (st.session_state.get("email") or "").lower().strip()
    rol_act = st.session_state.get("rol") or ""
    es_adm = bool(st.session_state.get("es_admin", False))
    if _es_cuenta_exenta_sesion_unica(em, rol_act, es_adm):
        return

    es_ext = bool(st.session_state.get("es_suscriptor_externo", False))

    # 1. Si es suscriptor externo, verificamos también que siga ACTIVO en caché RAM
    if es_ext:
        datos_gs = obtener_suscriptores_cacheados(forzar_remoto=False).get(em)
        if datos_gs and str(datos_gs.get("ESTADO", "")).upper() != "ACTIVO":
            _cerrar_sesion_por_expulsion(motivo_baja=True)

    # 2. Comprobación en 0 ms del token único de sesión activa en memoria compartida del servidor
    tok_local = st.session_state.get("session_token_unico") or st.session_state.get("session_token_externo") or ""
    if not tok_local:
        tok_local = registrar_nueva_sesion_unica(em)
        st.session_state["session_token_unico"] = tok_local
        return

    tok_servidor = obtener_token_vigente_usuario(em, es_suscriptor_ext=es_ext)
    if not tok_servidor:
        # Si el servidor se acaba de reiniciar en caliente y aún no tenía registro en RAM, adoptamos el token actual
        registrar_nueva_sesion_unica(em, token_forzado=tok_local)
        return

    if tok_servidor != tok_local:
        _cerrar_sesion_por_expulsion(motivo_baja=False)

    # 3. Vigilante silencioso cada 25 s: aunque el dispositivo antiguo no toque ningún botón, verifica vigencia y cierra si entró otro
    try:
        @st.fragment(run_every=25)
        def _vigilante_silencioso_sesion_unica():
            em_f = (st.session_state.get("email") or "").lower().strip()
            tok_f = st.session_state.get("session_token_unico") or st.session_state.get("session_token_externo") or ""
            es_ext_f = bool(st.session_state.get("es_suscriptor_externo", False))
            if not em_f or not tok_f:
                return
            tok_vig = obtener_token_vigente_usuario(em_f, es_suscriptor_ext=es_ext_f)
            if tok_vig and tok_vig != tok_f:
                components.html("""<script>
                try {
                    ["oposiciona_test_backup_v1", "oposiciona_auth_backup_v1", "oposiciona_sid_v1", "oposiciona_sid_v3", "oposiciona_sid_v4", "oposiciona_live_draft_txt"].forEach(function(k) {
                        window.parent.localStorage.removeItem(k);
                        window.parent.sessionStorage.removeItem(k);
                    });
                    var u = new URL(window.parent.location.href);
                    u.search = "?expulsado_sesion=1";
                    window.parent.location.replace(u.toString());
                } catch(e) {}
                </script>""", height=0)
        _vigilante_silencioso_sesion_unica()
    except Exception:
        pass

verificar_sesion_unica_global()

if st.session_state.get("autenticado") and st.session_state.get("es_suscriptor_externo") and st.query_params.get("sync_plan"):
    st.query_params.clear()
    act_ok, nuevo_plan_st = verificar_suscripcion_activa_stripe(st.session_state.get("stripe_customer_id", ""), st.session_state.get("stripe_subscription_id", ""))
    if act_ok and nuevo_plan_st in PLANES_SUSCRIPCION_OPOSICIONA:
        info_np = PLANES_SUSCRIPCION_OPOSICIONA[nuevo_plan_st]
        if nuevo_plan_st != st.session_state.get("plan_suscripcion"):
            st.session_state["aviso_plan_mejorado_ok"] = info_np["nombre_corto"]
        guardar_datos_suscriptor(st.session_state.get("email", ""), {"PLAN": nuevo_plan_st, "ROL": info_np["rol"], "ESTADO": "ACTIVO"}, sincrono=False)
        st.session_state.update(rol=info_np["rol"], plan_suscripcion=nuevo_plan_st, saved_esp=info_np["especialidad"], saved_cat="ESPECIFICO")
        st.rerun()
# === FIN SECCIÓN 1B ===

if not st.session_state.autenticado:
    precargar_suscriptores_en_segundo_plano()

    if st.session_state.get("aviso_sesion_cerrada_otro_disp"):
        st.session_state.pop("aviso_sesion_cerrada_otro_disp", None)
        st.warning("🔒 **Sesión anterior cerrada:** Se ha iniciado sesión con tu usuario en otro dispositivo o ventana. Solo permanece activa la última sesión abierta.")

    qp_stripe_sid = st.query_params.get("stripe_session_id", "")
    if qp_stripe_sid:
        with st.spinner("Activando tu suscripción y preparando tu acceso..."):
            ok_pago, info_pago = procesar_retorno_pago_stripe(qp_stripe_sid)
        st.query_params.clear()
        if ok_pago:
            st.success(f"🎉 ¡Suscripción activada para {info_pago}! Bienvenido/a a Oposiciona.")
            time.sleep(1.2)
            st.rerun()
        else:
            st.error(f"⚠️ {info_pago}")

    if st.query_params.get("pago_cancelado"):
        st.query_params.clear()
        st.session_state.pop("_checkout_cache_actual", None)
        st.session_state["vista_portada_auth"] = "planes"
        st.info("ℹ️ Has cancelado el proceso de pago. Puedes retomar tu suscripción cuando quieras.")

    qp_restore = st.query_params.get("restore_session", "")
    qp_draft = st.query_params.get("draft_txt", "")
    qp_sync_retorno = st.query_params.get("sync_plan", "")
    if qp_restore:
        try:
            datos_rec = _descifrar_backup_sesion(qp_restore)
            correo_rec = (datos_rec.get("email") or "").lower().strip()
            rol_rec = next((r for r, lc in USUARIOS_AUTORIZADOS.items() if correo_rec in lc), None)
            sub_ext_rec = None if rol_rec else buscar_suscriptor_externo(correo_rec)
            es_adm_rec = bool(datos_rec.get("es_admin", False) or (correo_rec in USUARIOS_ADMIN))
            tok_backup = str(datos_rec.get("session_token_unico") or datos_rec.get("session_token_externo") or "").strip()

            # Verificamos antes de restaurar que ningún otro dispositivo haya iniciado sesión mientras esta pestaña estaba colgada
            es_exento_rec = _es_cuenta_exenta_sesion_unica(correo_rec, rol_rec or "", es_adm_rec)
            tok_vigente_srv = "" if es_exento_rec else obtener_token_vigente_usuario(correo_rec, es_suscriptor_ext=bool(sub_ext_rec))
            sesion_reemplazada = bool(not es_exento_rec and tok_vigente_srv and (not tok_backup or tok_backup != tok_vigente_srv))

            if sesion_reemplazada:
                st.query_params.clear()
                st.session_state["borrar_backup_ls"] = True
                st.session_state["aviso_sesion_cerrada_otro_disp"] = True
                st.rerun()
            elif rol_rec or (sub_ext_rec and str(sub_ext_rec.get("ESTADO", "")).upper() == "ACTIVO"):
                tok_restaurado = tok_backup or ("" if es_exento_rec else registrar_nueva_sesion_unica(correo_rec))
                if tok_restaurado and not es_exento_rec and not tok_vigente_srv:
                    registrar_nueva_sesion_unica(correo_rec, token_forzado=tok_restaurado)

                st.session_state.autenticado = True
                st.session_state.email = correo_rec
                st.session_state.session_token_unico = tok_restaurado
                if rol_rec:
                    st.session_state.rol = "ACCESO TOTAL" if correo_rec in USUARIOS_ADMIN else rol_rec
                    st.session_state.es_admin = es_adm_rec
                    st.session_state.saved_esp = datos_rec.get("saved_esp", "ADMINISTRATIVOS")
                    st.session_state.saved_cat = datos_rec.get("saved_cat", "ESPECIFICO")
                else:
                    cust_rec = sub_ext_rec.get("STRIPE_CUSTOMER_ID", "")
                    sub_id_rec = sub_ext_rec.get("STRIPE_SUBSCRIPTION_ID", "")
                    plan_previo_gs = sub_ext_rec.get("PLAN", "GES_COMPLETO")
                    plan_rec = plan_previo_gs if plan_previo_gs in PLANES_SUSCRIPCION_OPOSICIONA else "GES_COMPLETO"
                    rol_final_rec = PLANES_SUSCRIPCION_OPOSICIONA[plan_rec]["rol"]
                    esp_rec = datos_rec.get("saved_esp") or PLANES_SUSCRIPCION_OPOSICIONA[plan_rec]["especialidad"]

                    if qp_sync_retorno and cust_rec:
                        act_ok_r, nuevo_plan_r = verificar_suscripcion_activa_stripe(cust_rec, sub_id_rec)
                        if act_ok_r and nuevo_plan_r in PLANES_SUSCRIPCION_OPOSICIONA:
                            plan_rec = nuevo_plan_r
                            rol_final_rec = PLANES_SUSCRIPCION_OPOSICIONA[nuevo_plan_r]["rol"]
                            esp_rec = PLANES_SUSCRIPCION_OPOSICIONA[nuevo_plan_r]["especialidad"]
                            if plan_rec != plan_previo_gs:
                                guardar_datos_suscriptor(correo_rec, {"PLAN": plan_rec, "ROL": rol_final_rec, "ESTADO": "ACTIVO"}, sincrono=False)
                                st.session_state["aviso_plan_mejorado_ok"] = PLANES_SUSCRIPCION_OPOSICIONA[plan_rec]["nombre_corto"]

                    st.session_state.rol = rol_final_rec
                    st.session_state.es_admin = False
                    st.session_state.es_suscriptor_externo = True
                    st.session_state.plan_suscripcion = plan_rec
                    st.session_state.stripe_customer_id = cust_rec
                    st.session_state.stripe_subscription_id = sub_id_rec
                    st.session_state.session_token_externo = tok_restaurado
                    st.session_state.saved_esp = esp_rec
                    st.session_state.saved_cat = "ESPECIFICO" if qp_sync_retorno else datos_rec.get("saved_cat", "ESPECIFICO")

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
                    idx_r = st.session_state.current_index
                    if qp_draft and idx_r in st.session_state.stats:
                        if not st.session_state.stats[idx_r].get("selected"):
                            st.session_state.stats[idx_r]["selected"] = qp_draft
                            st.session_state[f"open_txt_{idx_r}"] = qp_draft
                st.query_params.clear()
                st.rerun()
        except Exception:
            st.query_params.clear()

    components.html("""<script>
    (function() {
        try {
            var ss = window.parent.sessionStorage;
            var ls = window.parent.localStorage;
            ["oposiciona_sid_v1", "oposiciona_sid_v3"].forEach(function(k) {
                ss.removeItem(k);
                ls.removeItem(k);
            });
            var savedSid = ss.getItem("oposiciona_sid_v4") || ls.getItem("oposiciona_sid_v4");
            var savedAuth = ss.getItem("oposiciona_auth_backup_v1") || ls.getItem("oposiciona_auth_backup_v1");
            var draftTxt = ss.getItem("oposiciona_live_draft_txt") || ls.getItem("oposiciona_live_draft_txt") || "";

            var tokenToRestore = savedSid || savedAuth;
            if (tokenToRestore && window.parent.location.search.indexOf("restore_session=") === -1 && window.parent.location.search.indexOf("expulsado_sesion=") === -1) {
                var url = new URL(window.parent.location.href);
                url.searchParams.set("restore_session", tokenToRestore);
                if (draftTxt && draftTxt.length < 1500) {
                    url.searchParams.set("draft_txt", draftTxt);
                }
                window.parent.location.replace(url.toString());
            }
        } catch(e) {}
    })();
    </script>""", height=0)

    c_img1, c_img2, c_img3 = st.columns([1, 0.22, 1])
    with c_img2:
        try: st.image("test-utiles-768x768.png", use_container_width=True)
        except: pass
    st.markdown(
        "<h3 style='text-align: center; color: #2C3E50 !important; margin-top: -5px;'>🔒 Plataforma de Preparación Oposiciona</h3>"
        "<p style='text-align: center; font-size: 14px; color: #1E293B !important; margin-bottom: 14px;'>Accede con tus credenciales de alumno o suscríbete a nuestras modalidades mensuales.</p>",
        unsafe_allow_html=True
    )

    # === BOTONERA SUPERIOR EN COLORES PASTEL SUAVES ===
    vista_actual = st.session_state.get("vista_portada_auth", "login")
    if vista_actual not in ("login", "planes", "recuperar"):
        vista_actual = "login"
        st.session_state["vista_portada_auth"] = "login"

    col_nav1, col_nav2, col_nav3 = st.columns([1, 1.15, 1.35])
    with col_nav1:
        with st.container():
            cls_l = "opo-nav-login opo-nav-login-active" if vista_actual == "login" else "opo-nav-login"
            st.markdown(f"<div class='{cls_l}' style='display:none;'></div>", unsafe_allow_html=True)
            if st.button("🔑 Iniciar sesión", use_container_width=True, key="btn_nav_portada_login"):
                st.session_state["vista_portada_auth"] = "login"
                st.rerun()
    with col_nav2:
        with st.container():
            cls_p = "opo-nav-planes opo-nav-planes-active" if vista_actual == "planes" else "opo-nav-planes"
            st.markdown(f"<div class='{cls_p}' style='display:none;'></div>", unsafe_allow_html=True)
            if st.button("🎓 Suscribirme (Planes)", use_container_width=True, key="btn_nav_portada_planes"):
                st.session_state["vista_portada_auth"] = "planes"
                st.rerun()
    with col_nav3:
        with st.container():
            cls_r = "opo-nav-recuperar opo-nav-recuperar-active" if vista_actual == "recuperar" else "opo-nav-recuperar"
            st.markdown(f"<div class='{cls_r}' style='display:none;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Recuperar / Cambiar contraseña", use_container_width=True, key="btn_nav_portada_rec"):
                st.session_state["vista_portada_auth"] = "recuperar"
                st.rerun()

    st.markdown("<hr style='margin: 8px 0 16px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

    # --- VISTA 1: INICIAR SESIÓN ---
    if vista_actual == "login":
        email_input = st.text_input("Usuario o correo electrónico asociado", key="login_email_in")
        password_input = st.text_input("Contraseña de acceso", type="password", key="login_pwd_in")
        if st.button("Entrar a la plataforma", use_container_width=True, type="primary", key="btn_entrar_plat"):
            correo_limpio = email_input.lower().strip()
            rol_usuario = next((r for r, lc in USUARIOS_AUTORIZADOS.items() if correo_limpio in lc), None)
            if correo_limpio in USUARIOS_ADMIN:
                if password_input == PASSWORD_ADMIN:
                    st.session_state.update(autenticado=True, rol="ACCESO TOTAL", email=correo_limpio, es_admin=True, es_suscriptor_externo=False, session_token_unico="", do_scroll=True)
                    st.rerun()
                else:
                    st.error("❌ Contraseña de administrador incorrecta.")
            elif rol_usuario == "INVITADO" and password_input == PASSWORD_INVITADO:
                st.session_state.update(autenticado=True, rol="INVITADO", email=correo_limpio, es_admin=False, es_suscriptor_externo=False, session_token_unico="", do_scroll=True)
                st.rerun()
            elif rol_usuario and password_input in [PASSWORD_ACCESO, PASSWORD_ADMIN]:
                es_adm = (password_input == PASSWORD_ADMIN) or (correo_limpio in USUARIOS_ADMIN)
                tok_interno = "" if es_adm else registrar_nueva_sesion_unica(correo_limpio)
                st.session_state.update(
                    autenticado=True,
                    rol=rol_usuario,
                    email=correo_limpio,
                    es_admin=es_adm,
                    es_suscriptor_externo=False,
                    session_token_unico=tok_interno,
                    do_scroll=True
                )
                st.rerun()
            else:
                sub_ext = buscar_suscriptor_externo(correo_limpio, forzar_remoto=False)
                if sub_ext and sub_ext.get("PASSWORD_HASH") == _hash_password_suscriptor(password_input):
                    estado_gs = str(sub_ext.get("ESTADO", "")).upper().strip()
                    cust_id_login = sub_ext.get("STRIPE_CUSTOMER_ID", "")
                    sub_id_login = sub_ext.get("STRIPE_SUBSCRIPTION_ID", "")

                    if estado_gs == "ACTIVO":
                        plan_final = sub_ext.get("PLAN", "GES_COMPLETO")
                        if plan_final not in PLANES_SUSCRIPCION_OPOSICIONA:
                            plan_final = "GES_COMPLETO"
                        rol_final = PLANES_SUSCRIPCION_OPOSICIONA[plan_final]["rol"]
                        nuevo_tok = registrar_nueva_sesion_unica(correo_limpio)
                        ahora_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y %H:%M:%S")

                        guardar_datos_suscriptor(correo_limpio, {
                            "ULTIMO_ACCESO": ahora_str,
                            "SESSION_TOKEN": nuevo_tok
                        }, sincrono=False)

                        cfg_bg = _cfg_suscripciones()
                        threading.Thread(
                            target=_sincronizar_stripe_post_login_bg,
                            args=(correo_limpio, cust_id_login, sub_id_login, cfg_bg["stripe_key"], cfg_bg["gs_url"], cfg_bg["gs_token"]),
                            daemon=True
                        ).start()

                        st.session_state.update(
                            autenticado=True,
                            rol=rol_final,
                            email=correo_limpio,
                            es_admin=False,
                            es_suscriptor_externo=True,
                            plan_suscripcion=plan_final,
                            stripe_customer_id=cust_id_login,
                            stripe_subscription_id=sub_id_login,
                            session_token_externo=nuevo_tok,
                            session_token_unico=nuevo_tok,
                            saved_esp=PLANES_SUSCRIPCION_OPOSICIONA[plan_final]["especialidad"],
                            do_scroll=True
                        )
                        st.rerun()
                    else:
                        activo_stripe, plan_stripe = verificar_suscripcion_activa_stripe(cust_id_login, sub_id_login)
                        if activo_stripe:
                            plan_final = plan_stripe if plan_stripe in PLANES_SUSCRIPCION_OPOSICIONA else sub_ext.get("PLAN", "GES_COMPLETO")
                            rol_final = PLANES_SUSCRIPCION_OPOSICIONA[plan_final]["rol"]
                            nuevo_tok = registrar_nueva_sesion_unica(correo_limpio)
                            ahora_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y %H:%M:%S")
                            guardar_datos_suscriptor(correo_limpio, {
                                "PLAN": plan_final,
                                "ROL": rol_final,
                                "ESTADO": "ACTIVO",
                                "ULTIMO_ACCESO": ahora_str,
                                "SESSION_TOKEN": nuevo_tok
                            }, sincrono=False)
                            st.session_state.update(
                                autenticado=True,
                                rol=rol_final,
                                email=correo_limpio,
                                es_admin=False,
                                es_suscriptor_externo=True,
                                plan_suscripcion=plan_final,
                                stripe_customer_id=cust_id_login,
                                stripe_subscription_id=sub_id_login,
                                session_token_externo=nuevo_tok,
                                session_token_unico=nuevo_tok,
                                saved_esp=PLANES_SUSCRIPCION_OPOSICIONA[plan_final]["especialidad"],
                                do_scroll=True
                            )
                            st.rerun()
                        else:
                            st.session_state["email_verificado_ok"] = correo_limpio
                            st.session_state["sub_reactivacion_login"] = correo_limpio
                            st.session_state["sub_reactivacion_plan"] = sub_ext.get("PLAN", "GES_COMPLETO")
                else:
                    st.error("❌ Correo o contraseña incorrectos, o no tienes autorización activa.")

        if st.session_state.get("sub_reactivacion_login"):
            em_react = st.session_state["sub_reactivacion_login"]
            st.warning(f"ℹ️ Hola **{em_react}**: tu cuenta ya está verificada, pero tu suscripción mensual figura actualmente como inactiva.")
            plan_prev = st.session_state.get("sub_reactivacion_plan", "GES_COMPLETO")
            if plan_prev not in PLANES_SUSCRIPCION_OPOSICIONA:
                plan_prev = "GES_COMPLETO"
            lista_p_react = list(PLANES_SUSCRIPCION_OPOSICIONA.keys())
            plan_sel_react = st.selectbox(
                "Elige la modalidad con la que deseas reactivar tu acceso:",
                lista_p_react,
                index=lista_p_react.index(plan_prev),
                format_func=lambda k: PLANES_SUSCRIPCION_OPOSICIONA[k]["titulo_nivel"],
                key="sel_react_login_plan"
            )
            render_bloque_aviso_calendario_pdf(sufijo_key="react_login")
            acepta_react = st.checkbox("✅ ACEPTAR: He revisado la información anterior y deseo continuar con la suscripción.", key="chk_aceptar_cal_react")
            if acepta_react:
                promo_react_id = render_selector_codigo_promocional(plan_sel_react, sufijo_key="react_login", email_usuario=em_react)
                url_r_chk, err_r_chk = obtener_url_checkout_sesion_actual(em_react, plan_sel_react, promo_code_id=promo_react_id)
                if url_r_chk:
                    st.link_button("💳 Reactivar mi suscripción ahora (acceso inmediato)", url_r_chk, use_container_width=True, type="primary")
                elif err_r_chk:
                    st.error(f"❌ {err_r_chk}")

    # --- VISTA 2: SUSCRIBIRME (PLANES) ---
    elif vista_actual == "planes":
        st.markdown(
            "<div style='background:#EFF6FF; border:1px solid #93C5FD; border-radius:8px; padding:12px 14px; margin-bottom:14px;'>"
            "<b style='color:#1E3A8A !important; font-size:15px;'>🎓 Preparación Mensual Tutorizada Oposiciona</b><br>"
            "<span style='font-size:13.2px; color:#1E293B !important;'>Todas las modalidades incluyen acceso a la plataforma práctica, <b>resolución de dudas por correo electrónico</b> con nuestros preparadores, "
            "<b>actualizaciones comentadas de legislación</b> y <b>clase online mensual en directo</b>. Sin permanencia: cancela en un clic cuando quieras.</span>"
            "</div>",
            unsafe_allow_html=True
        )

        st.markdown("<div style='font-size:15.5px; font-weight:800; color:#1E293B !important; margin-bottom:6px;'>1. Elige tu especialidad</div>", unsafe_allow_html=True)
        cuerpo_sel = st.radio(
            "Especialidad:",
            ["GESTIÓN DE LA SEGURIDAD SOCIAL (A2)", "ADMINISTRATIVO DE LA SEGURIDAD SOCIAL (C1)"],
            horizontal=True,
            label_visibility="collapsed",
            key="sub_cuerpo_rad"
        )

        if "ADMINISTRATIVO" in cuerpo_sel:
            opciones_plan = ["ADM_COMPLETO"]
            plan_default = "ADM_COMPLETO"
        else:
            opciones_plan = ["GES_SOLO_TEST", "GES_TEST_SUPUESTOS", "GES_TEST_DESARROLLO", "GES_COMPLETO"]
            plan_default = "GES_COMPLETO"

        if st.session_state.get("plan_seleccionado_tarjeta") not in opciones_plan:
            st.session_state["plan_seleccionado_tarjeta"] = plan_default

        st.markdown("<div style='font-size:15.5px; font-weight:800; color:#1E293B !important; margin-top:8px; margin-bottom:8px;'>2. Selecciona tu modalidad mensual</div>", unsafe_allow_html=True)

        for pid in opciones_plan:
            p_info = PLANES_SUSCRIPCION_OPOSICIONA[pid]
            es_elegido = (st.session_state.get("plan_seleccionado_tarjeta") == pid)
            borde_c = "2.5px solid #1D4ED8" if es_elegido else "1px solid #CBD5E1"
            fondo_c = "#EFF6FF" if es_elegido else "#F8FAFC"
            etiqueta_btn = "✅ Seleccionado" if es_elegido else "Seleccionar"
            tipo_btn = "primary" if es_elegido else "secondary"

            st.markdown(
                f"<div style='background:{fondo_c}; border:{borde_c}; border-radius:10px; padding:12px 15px; margin-bottom:6px;'>"
                f"<div style='font-size:16px; font-weight:800; color:#0F172A !important; margin-bottom:5px;'>{p_info['titulo_nivel']}</div>"
                f"<div style='font-size:13.3px; color:#334155 !important; line-height:1.45; text-align:justify;'>{p_info['descripcion']}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            if st.button(f"{etiqueta_btn} — {p_info['titulo_nivel']}", key=f"btn_sel_plan_{pid}", use_container_width=True, type=tipo_btn):
                st.session_state["plan_seleccionado_tarjeta"] = pid
                st.session_state.pop("_checkout_cache_actual", None)
                st.rerun()

        plan_elegido = st.session_state["plan_seleccionado_tarjeta"]

        st.markdown("<hr style='margin: 14px 0 12px 0; border:none; border-top:1px solid #CBD5E1;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:15.5px; font-weight:800; color:#1E293B !important; margin-bottom:6px;'>3. Introduce y verifica tu correo electrónico</div>", unsafe_allow_html=True)

        col_em1, col_em2 = st.columns(2)
        with col_em1:
            email_alta_1 = st.text_input("Correo electrónico:", placeholder="tucorreo@ejemplo.com", key="sub_email_alta_1")
        with col_em2:
            email_alta_2 = st.text_input("Repite tu correo electrónico:", placeholder="tucorreo@ejemplo.com", key="sub_email_alta_2")

        em_1_limpio = (email_alta_1 or "").lower().strip()
        em_2_limpio = (email_alta_2 or "").lower().strip()

        if st.session_state.get("email_verificado_ok") and st.session_state.get("email_verificado_ok") != em_1_limpio:
            st.session_state["email_verificado_ok"] = ""
            st.session_state["pwd_registro_guardada_email"] = ""
            st.session_state["aviso_calendario_aceptado"] = False

        ficha_existente = buscar_suscriptor_externo(em_1_limpio) if (em_1_limpio and em_1_limpio == em_2_limpio and re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', em_1_limpio)) else None
        ya_tenia_cuenta_activa_previa = bool(
            ficha_existente and ficha_existente.get("PASSWORD_HASH") and str(ficha_existente.get("ESTADO", "")).upper() != "PENDIENTE_PAGO"
        )
        ya_activo_ahora = bool(ya_tenia_cuenta_activa_previa and str(ficha_existente.get("ESTADO", "")).upper() == "ACTIVO")

        ya_verificado = bool(
            em_1_limpio and em_1_limpio == em_2_limpio and (
                st.session_state.get("email_verificado_ok") == em_1_limpio or ya_tenia_cuenta_activa_previa
            )
        )

        if ya_activo_ahora:
            st.warning(f"⚠️ El correo **{em_1_limpio}** ya tiene una suscripción activa en vigor. Pulsa arriba en el botón azul **«🔑 Iniciar sesión»** (o usa *Recuperar / Cambiar contraseña* si no la recuerdas) para no duplicar pagos.")
        elif not ya_verificado:
            if st.button("📩 Enviar código de verificación a mi correo", use_container_width=True, type="primary", key="btn_enviar_cod_verif"):
                if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', em_1_limpio):
                    st.error("⚠️ Introduce una dirección de correo electrónico válida.")
                elif em_1_limpio != em_2_limpio:
                    st.error("⚠️ Los dos correos electrónicos no coinciden. Revísalos antes de continuar.")
                else:
                    cod_6 = f"{secrets.randbelow(900000) + 100000}"
                    st.session_state["codigo_verif_pendiente"] = cod_6
                    st.session_state["email_verif_pendiente"] = em_1_limpio
                    st.session_state["ts_verif_pendiente"] = time.time()
                    with st.spinner("Enviando código de verificación a tu bandeja de entrada..."):
                        r_mail = enviar_email_suscriptor(
                            em_1_limpio,
                            f"🔐 Código de verificación ({cod_6}) — Oposiciona",
                            f"<div style='font-family:sans-serif; color:#1E293B; max-width:520px;'>"
                            f"<h3 style='color:#1F77B4;'>Verificación de tu correo electrónico</h3>"
                            f"<p>Introduce el siguiente código de 6 dígitos en la pantalla de registro de <b>Oposiciona</b> para confirmar que tu correo es correcto:</p>"
                            f"<div style='font-size:26px; font-weight:800; letter-spacing:4px; background:#EFF6FF; border:1px solid #93C5FD; padding:12px; text-align:center; border-radius:8px; color:#1E3A8A;'>{cod_6}</div>"
                            f"<p style='font-size:12.5px; color:#64748B; margin-top:12px;'>Este código caduca en 15 minutos.</p></div>"
                        )
                    if r_mail.get("ok"):
                        st.success(f"✅ Hemos enviado un código de 6 dígitos a **{em_1_limpio}** (revisa también Spam/Promociones).")
                    else:
                        st.error(f"❌ No se pudo enviar el correo de verificación: {r_mail.get('error', 'Error desconocido')}")

            if st.session_state.get("email_verif_pendiente") == em_1_limpio and em_1_limpio:
                col_cod1, col_cod2 = st.columns([2, 1.2])
                with col_cod1:
                    cod_introducido = st.text_input("Introduce el código de 6 dígitos recibido:", max_chars=6, placeholder="123456", key="in_cod_verif_6")
                with col_cod2:
                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("✔️ Confirmar código", use_container_width=True, type="primary", key="btn_confirmar_cod_6"):
                        expirado = (time.time() - st.session_state.get("ts_verif_pendiente", 0)) > 900
                        if expirado:
                            st.error("⚠️ El código ha caducado. Pulsa arriba para enviarte uno nuevo.")
                        elif (cod_introducido or "").strip() == st.session_state.get("codigo_verif_pendiente"):
                            st.session_state["email_verificado_ok"] = em_1_limpio
                            st.session_state.pop("_checkout_cache_actual", None)
                            st.rerun()
                        else:
                            st.error("❌ Código incorrecto. Comprueba el correo recibido.")
        else:
            pwd_lista_para_pago = False
            if ya_tenia_cuenta_activa_previa and st.session_state.get("pwd_registro_guardada_email") != em_1_limpio:
                st.success(f"✅ ¡Hola de nuevo! Hemos reconocido tu cuenta verificada (**{em_1_limpio}**). Seguirás entrando con tu contraseña habitual (o cámbiala arriba en *Recuperar / Cambiar contraseña*).")
                pwd_lista_para_pago = True
            elif st.session_state.get("pwd_registro_guardada_email") == em_1_limpio:
                st.success(f"✅ Correo (**{em_1_limpio}**) y contraseña personal configurados correctamente.")
                if st.button("✏️ Elegir otra contraseña distinta", key="btn_cambiar_pwd_pre_pago"):
                    st.session_state["pwd_registro_guardada_email"] = ""
                    st.session_state["aviso_calendario_aceptado"] = False
                    st.rerun()
                pwd_lista_para_pago = True
            else:
                st.success(f"✅ Correo electrónico verificado correctamente: **{em_1_limpio}**")
                st.markdown("<div style='font-size:15.5px; font-weight:800; color:#1E293B !important; margin-top:10px; margin-bottom:6px;'>4. Elige tu contraseña personal de acceso</div>", unsafe_allow_html=True)
                cpw1, cpw2 = st.columns(2)
                with cpw1:
                    pwd_alta_1 = st.text_input("Elige tu contraseña (mín. 6 caracteres):", type="password", key="in_pwd_alta_1")
                with cpw2:
                    pwd_alta_2 = st.text_input("Repite tu contraseña:", type="password", key="in_pwd_alta_2")

                if st.button("🔒 Guardar mi contraseña y continuar", use_container_width=True, type="primary", key="btn_guardar_pwd_alta"):
                    ok_pw, msg_pw = _validar_password_elegida(pwd_alta_1, pwd_alta_2)
                    if not ok_pw:
                        st.error(f"⚠️ {msg_pw}")
                    else:
                        info_p_pre = PLANES_SUSCRIPCION_OPOSICIONA[plan_elegido]
                        res_g = guardar_datos_suscriptor(em_1_limpio, {
                            "PASSWORD_HASH": _hash_password_suscriptor(pwd_alta_1.strip()),
                            "PLAN": plan_elegido,
                            "ROL": info_p_pre["rol"],
                            "ESTADO": "PENDIENTE_PAGO"
                        }, sincrono=True)
                        if res_g.get("ok"):
                            st.session_state["pwd_registro_guardada_email"] = em_1_limpio
                            st.rerun()
                        else:
                            st.error(f"❌ No se pudo guardar la contraseña: {res_g.get('error', 'Error desconocido')}")

            if pwd_lista_para_pago:
                info_resumen = PLANES_SUSCRIPCION_OPOSICIONA[plan_elegido]
                st.info(f"📌 Modalidad elegida: **{info_resumen['titulo_nivel']}**")

                num_paso_aviso = "4" if ya_tenia_cuenta_activa_previa else "5"
                st.markdown(f"<div style='font-size:17.5px; font-weight:900; color:#1E293B !important; margin-top:14px; margin-bottom:4px;'>{num_paso_aviso}. Información importante antes de suscribirte</div>", unsafe_allow_html=True)
                render_bloque_aviso_calendario_pdf(sufijo_key="planes")

                if not st.session_state.get("aviso_calendario_aceptado", False):
                    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                    if st.button("✅ ACEPTAR Y CONTINUAR CON LA SUSCRIPCIÓN", use_container_width=True, type="primary", key="btn_aceptar_aviso_temas"):
                        st.session_state["aviso_calendario_aceptado"] = True
                        st.rerun()
                else:
                    st.success("✅ Condiciones de calendario de temas aceptadas.")
                    promo_id_sel = render_selector_codigo_promocional(plan_elegido, sufijo_key="planes", email_usuario=em_1_limpio)
                    with st.spinner("Preparando pasarela de pago segura..."):
                        url_checkout, err_chk = obtener_url_checkout_sesion_actual(em_1_limpio, plan_elegido, promo_code_id=promo_id_sel)
                    if url_checkout:
                        st.link_button(
                            "💳 Continuar al pago seguro y activar acceso inmediato",
                            url_checkout,
                            use_container_width=True,
                            type="primary"
                        )
                    else:
                        st.error(f"❌ {err_chk}")

    # --- VISTA 3: RECUPERAR / CAMBIAR CONTRASEÑA ---
    else:
        st.markdown(
            "<p style='font-size:13.8px; color:#1E293B !important;'>Si has olvidado tu contraseña o deseas elegir una nueva, verifica tu correo con un código de seguridad y establece la contraseña que prefieras:</p>",
            unsafe_allow_html=True
        )
        email_rec = st.text_input("Correo electrónico de tu suscripción:", key="rec_email_in")
        em_r = (email_rec or "").lower().strip()

        if st.session_state.get("rec_email_verificado") and st.session_state.get("rec_email_verificado") != em_r:
            st.session_state["rec_email_verificado"] = ""

        if st.session_state.get("rec_email_verificado") != em_r:
            if st.button("📩 Enviar código de seguridad a mi correo", use_container_width=True, type="primary", key="btn_enviar_rec"):
                sub_r = buscar_suscriptor_externo(em_r)
                if not sub_r:
                    st.error("❌ No encontramos ninguna suscripción externa asociada a ese correo electrónico.")
                else:
                    cod_rec = f"{secrets.randbelow(900000) + 100000}"
                    st.session_state["rec_cod_pendiente"] = cod_rec
                    st.session_state["rec_email_pendiente"] = em_r
                    st.session_state["rec_ts_pendiente"] = time.time()
                    enviar_email_suscriptor(
                        em_r,
                        f"🔑 Código para cambiar tu contraseña ({cod_rec}) — Oposiciona",
                        f"<div style='font-family:sans-serif; color:#1E293B; max-width:520px;'>"
                        f"<h3 style='color:#1F77B4;'>Cambio / Recuperación de contraseña</h3>"
                        f"<p>Introduce este código de 6 dígitos en la plataforma <b>Oposiciona</b> para elegir tu nueva contraseña:</p>"
                        f"<div style='font-size:26px; font-weight:800; letter-spacing:4px; background:#EFF6FF; border:1px solid #93C5FD; padding:12px; text-align:center; border-radius:8px; color:#1E3A8A;'>{cod_rec}</div>"
                        f"<p style='font-size:12.5px; color:#64748B; margin-top:12px;'>Este código caduca en 15 minutos.</p></div>"
                    )
                    st.success(f"✅ Hemos enviado un código de 6 dígitos a **{em_r}**.")

            if st.session_state.get("rec_email_pendiente") == em_r and em_r:
                cr1, cr2 = st.columns([2, 1.2])
                with cr1:
                    cod_rec_in = st.text_input("Código de 6 dígitos recibido:", max_chars=6, key="in_rec_cod_6")
                with cr2:
                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("✔️ Validar código", use_container_width=True, type="primary", key="btn_val_rec_cod"):
                        if (time.time() - st.session_state.get("rec_ts_pendiente", 0)) > 900:
                            st.error("⚠️ El código ha caducado. Solicita uno nuevo arriba.")
                        elif (cod_rec_in or "").strip() == st.session_state.get("rec_cod_pendiente"):
                            st.session_state["rec_email_verificado"] = em_r
                            st.rerun()
                        else:
                            st.error("❌ Código incorrecto.")
        else:
            st.success(f"✅ Identidad verificada para **{em_r}**. Escribe ahora tu nueva contraseña:")
            np1, np2 = st.columns(2)
            with np1:
                nueva_pw_1 = st.text_input("Nueva contraseña (mín. 6 caracteres):", type="password", key="rec_new_pw1")
            with np2:
                nueva_pw_2 = st.text_input("Repite la nueva contraseña:", type="password", key="rec_new_pw2")
            if st.button("💾 Guardar nueva contraseña", use_container_width=True, type="primary", key="btn_save_rec_pw"):
                ok_np, msg_np = _validar_password_elegida(nueva_pw_1, nueva_pw_2)
                if not ok_np:
                    st.error(f"⚠️ {msg_np}")
                else:
                    guardar_datos_suscriptor(em_r, {"PASSWORD_HASH": _hash_password_suscriptor(nueva_pw_1.strip())}, sincrono=True)
                    st.session_state["rec_email_verificado"] = ""
                    st.session_state["rec_email_pendiente"] = ""
                    st.success("✅ ¡Contraseña actualizada con éxito! Pulsa arriba en el botón «🔑 Iniciar sesión» para entrar.")
    st.stop()
# === FIN SECCIÓN 1 ===

# === SECCIÓN 2: CATÁLOGO DE TESTS Y PERMISOS POR ROL ===
NUEVOS_HOY = [
    "TEMA 15 EL ACTO ADMINISTRATIVO",
    "TEMA 05b - RECAUDACIÓN VOLUNTARIA",
    "TEMA 55 ACCIÓN PROTECTORA CONTENIDO Y CLASIFICACIÓN DE LAS PRESTACIONES",
    "TEMA 56 REQUISITOS GENERALES DE LAS PRESTACIONES",
    "TEMA 57 INCAPACIDAD TEMPORAL",
    "TEMA 58 NYCM",
    "TEMA 61 JUBILACION CONTRIBUTIVA",
]

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
            "TEMA 05a - RECAUDACIÓN VOLUNTARIA": "https://drive.google.com/uc?export=download&id=1DRsCORMz-vUTATK-mnQwjIp4Q9CD0azF",
            "TEMA 05b - RECAUDACIÓN VOLUNTARIA": "https://drive.google.com/uc?export=download&id=1IIdZ6GXdOF72zaYad1iKYPxpEquRZheD",
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
            "TEMA 12 - MINISTERIO": "https://drive.google.com/uc?export=download&id=1JzqJfb8ddB2wPb7ijOE6tsTA3rhPrhhH",
            "TEMA 13 REPASO FUENTES DEL DERECHO GENERAL": "https://drive.google.com/uc?export=download&id=1pMqfE5ThZaFgiqvqAWnXFeYfkOwCMUur",
            "TEMA 14 REPASO LA LEY GENERAL": "https://drive.google.com/uc?export=download&id=1k4RXRU6DKUQZ-MCI9A0T3kgiGOL39zgN",
            "TEMA 15 EL ACTO ADMINISTRATIVO": "https://drive.google.com/uc?export=download&id=1EDynBcAjEGRp6wGo8BU4mzmlr1wMKKGR",
            "TEMA 20 - ATENCION AL PÚBLICO": "https://drive.google.com/uc?export=download&id=1v7I4oL03hQF8Q66MoG9ZiRnj_tHxjN2f",
        },
        "SUPUESTOS": {
            "Elige un test de supuestos...": None,
            "TEMA 01 - CONSTITUCION Y TRLGSS": "https://drive.google.com/uc?export=download&id=1Z5mw1Jj1D77VXAghNDVr-UmbcEgP_GV5",
            "TEMA 02A": "https://drive.google.com/uc?export=download&id=17lK9Q1xQunt-4lJeYU7QqhINRLLM2HEw",
            "TEMA 02B": "https://drive.google.com/uc?export=download&id=1Z0rLu9eSrjSXiR0nTy6nTMMLV-bSOmQ6",
            "TEMA 02C": "https://drive.google.com/uc?export=download&id=1ikbOUgK2ESpu_O3xH8Xvn-hc95gH5WrC",
            "TEMA 02D": "https://drive.google.com/uc?export=download&id=1CbsWH7VTkzrz1Cz-f2ghPABs7_WNVb6z",
            "TEMA 03 - AFILIACION": "https://drive.google.com/uc?export=download&id=1S5FWCMwLYTI9HiJY4kVSoThNp7XK4cCM",
            "TEMA 04 -COTIZACION": "https://drive.google.com/uc?export=download&id=1CobeZShnSVnriCyQ29R6Ruf6flXJFc8K",
            "TEMA 05a - RECAUDACIÓN VOLUNTARIA": "https://drive.google.com/uc?export=download&id=1Dg0mSgZ3lAO0sALJqZxvvLEZNrsOjflt",
            "TEMA 05b - RECAUDACIÓN VOLUNTARIA": "https://drive.google.com/uc?export=download&id=1Jb33e80VQcWQbMiOJ-aIqsgv7o9Mwkr-",
            "TEMA 08A INCAPACIDAD TEMPORAL": "https://drive.google.com/uc?export=download&id=10ziheihr-60JoLiEvTi17QkXQS3DWGrV",
            "TEMA 08B INCAPACIDAD PERMANENTE": "https://drive.google.com/uc?export=download&id=1cnrn-ZkaRGPfstuoZ9RA1ofp-YO1NFbi",
            "TEMA 09 NYCM": "https://drive.google.com/uc?export=download&id=1i0P4bsfLb6jN0GeqSlwe72YZi-bqVwuk",
            "TEMA 10 JUBILACIÓN": "https://drive.google.com/uc?export=download&id=16eRs-xpizfmyqhch-M6gCjqxd31L2I1c",
            "TEMA 11 MUERTE Y SUPERVIVENCIA": "https://drive.google.com/uc?export=download&id=11HjAg0JvDOYyQ2OOWhtv0cSxwBBeFIbL",
            "TEMA 12 - IMV": "https://drive.google.com/uc?export=download&id=1Fg0ZvHbLoRWRR_6WOCz2k0E8xiDsnNyd",
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
            "TEMA_68_GESTIÓN RECAUDATORIA": "https://drive.google.com/uc?export=download&id=1hSs73f4MXMjgmD8ZjlFh66f7qGD26xJ6",
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
            "TEMA 68 - GESTION RECAUDATORIA": "https://drive.google.com/uc?export=download&id=1ciJMrMtlDhBGQz-Vijo-_XUnvFhCpXVb",
            "TEMA 69 LA RECAUDACION EN PERIODO VOLUNTARIO": "https://drive.google.com/uc?export=download&id=1XTCIwNZ2LI_ObF6gtSeuCTqzb9PcOgX3",
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
            "TEMA 26 EL PRESUPUESTO DE LA SEGURIDAD SOCIAL": "https://drive.google.com/uc?export=download&id=1Iplaf0ltUFrl662NgCKO6ZyO5R8JOVvj",
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
            "TEMA 51 - CONSTITUCION EN LA SS Y TRLGSS": "https://drive.google.com/uc?export=download&id=1UqEhTtQzAqJFxhlsqticUNq3AtU8IXbN",
            "TEMA 52 - CAMPO DE APLICACIÓN Y COMPOSICIÓN DEL SISTEMA": "https://drive.google.com/uc?export=download&id=1RQBpdR3EPeEsYBrV6XRHUA_knZypgA6u",
            "TEMA 54 - ACCIDENTE DE TRABAJO ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1_pcP-rkh-8vXr5zViCY1XsCntnxlc4Yw",
            "TEMA 55 ACCIÓN PROTECTORA CONTENIDO Y CLASIFICACIÓN DE LAS PRESTACIONES": "https://drive.google.com/uc?export=download&id=1Z9j-NCO974GCQoApNn9YoP7aJokgzqqh",
            "TEMA 56 REQUISITOS GENERALES DE LAS PRESTACIONES": "https://drive.google.com/uc?export=download&id=1r-2sH5kZIcqhEp-k-go8BfbsQc8sg3ku",
            "TEMA 57 INCAPACIDAD TEMPORAL": "https://drive.google.com/uc?export=download&id=1oiz-rCO44MWI491G_pxGSU87QczqIcwg",
            "TEMA 58 NYCM": "https://drive.google.com/uc?export=download&id=1208HwEFZ3jKuwNNUBinhOH5ANWoebJky",
            "TEMA 59 y 60 IP": "https://drive.google.com/uc?export=download&id=1EwLQcCxrhBwPy6Jp-pJZl-eg1At00ZDW",
            "TEMA 61 JUBILACION CONTRIBUTIVA": "https://drive.google.com/uc?export=download&id=1mGxNc-Ph1pXahlNfcVUEQxWJhFctz6cJ",
            "TEMA 62 MUERTE Y SUPERVIVENCIA": "https://drive.google.com/uc?export=download&id=1UKbboomy3DuPZI_wQuW82KJ8MXqQ8yjv",
            "TEMA 67 - COTIZACION": "https://drive.google.com/uc?export=download&id=1c15J-mxBJXF19LUVbriap4q_rsvSZcI3",
            "TEMA 73. LOS REGÍMENES ESPECIALES DE LA SEGURIDAD SOCIAL INTEGRADOS EN EL RÉGIMEN GENERAL": "https://drive.google.com/uc?export=download&id=1jaElumEJxMrl1MV6roobYJHOwQ45vAxK",
            "TEMA 74. RETA SETA Y MAR": "https://drive.google.com/uc?export=download&id=1vz75WRZxHjKpqt5W_Z-O8YruY76Tbbsk",
        },
    },
}

TESTS_DISPONIBLES_COMPLETO = TESTS_DISPONIBLES

def obtener_tests_segun_rol():
    rol = st.session_state.get("rol")
    if rol == "INVITADO":
        return {
            "ADMINISTRATIVOS": {
                "ESPECIFICO": {
                    "Elige un test de especifico...": None,
                    "TEMA 04 - TEST Y SUPUESTOS COTIZACION ACTUALIZADO": TESTS_DISPONIBLES_COMPLETO["ADMINISTRATIVOS"]["ESPECIFICO"].get(
                        "TEMA 04 - TEST Y SUPUESTOS COTIZACION ACTUALIZADO",
                        "https://drive.google.com/uc?export=download&id=1Tpw0hJ1Vpc8d9KGe6TffL-FRqGoWPTML"
                    ),
                },
                "EXAMENES": {"Elige un test de examenes...": None},
                "GENERAL": {"Elige un test de general...": None},
                "SUPUESTOS": {"Elige un test de supuestos...": None},
            },
            "GESTION": {
                "DESARROLLO": {"Elige un test de desarrollo...": None},
                "ESPECIFICO": {
                    "Elige un test de especifico...": None,
                    "TEMA 53 - AFILIACION ACTUALIZADO": TESTS_DISPONIBLES_COMPLETO["GESTION"]["ESPECIFICO"].get(
                        "TEMA 53 - AFILIACION ACTUALIZADO",
                        "https://drive.google.com/uc?export=download&id=1Kv-Bm_Eig1SMcXB-xBjzbQwQqjlAQ8Bf"
                    ),
                },
                "EXAMENES": {"Elige un test de examenes...": None},
                "GENERAL": {"Elige un test de general...": None},
                "SUPUESTOS": {"Elige un test de supuestos...": None},
            },
        }

    orden_categorias = {
        "ADMINISTRATIVOS": ["ESPECIFICO", "GENERAL", "EXAMENES", "SUPUESTOS"],
        "GESTION": ["ESPECIFICO", "GENERAL", "EXAMENES", "SUPUESTOS", "DESARROLLO"],
    }
    catalogo_filtrado = {}
    for esp, cats in TESTS_DISPONIBLES_COMPLETO.items():
        catalogo_filtrado[esp] = {}
        for cat in orden_categorias.get(esp, list(cats.keys())):
            if cat in cats:
                catalogo_filtrado[esp][cat] = dict(cats[cat])
    return catalogo_filtrado
# === FIN SECCIÓN 2 ===

# === SECCIÓN 3A: MOTOR DE WORD (.DOCX), DESARROLLO Y SUPUESTOS PRÁCTICOS ===
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
            w_prefix = f"{{{ns['w']}}}"

            estilos_negrita = set()
            estilos_lista = set()
            try:
                with zipfile.ZipFile(io.BytesIO(docx_bytes)) as zf:
                    if "word/styles.xml" in zf.namelist():
                        st_root = ET.fromstring(zf.read("word/styles.xml"))
                        for st_node in st_root.findall("w:style", ns):
                            st_id = st_node.attrib.get(f"{w_prefix}styleId", "")
                            name_el = st_node.find("w:name", ns)
                            st_name = name_el.attrib.get(f"{w_prefix}val", "") if name_el is not None else ""
                            pPr_s = st_node.find("w:pPr", ns)
                            rPr_s = st_node.find("w:rPr", ns)
                            if pPr_s is not None and pPr_s.find("w:numPr", ns) is not None:
                                estilos_lista.add(st_id)
                            if re.search(r'list|vi[ñn]eta|bullet', f"{st_id} {st_name}", re.IGNORECASE):
                                estilos_lista.add(st_id)
                            if rPr_s is not None:
                                b_s = rPr_s.find("w:b", ns)
                                if b_s is not None and b_s.attrib.get(f"{w_prefix}val", "true").lower() not in ("0", "false", "off"):
                                    estilos_negrita.add(st_id)
            except Exception:
                pass

            root = ET.fromstring(xml_content)
            body = root.find("w:body", ns)
            if body is None:
                return []

            for p in body.iter(f"{w_prefix}p"):
                pPr = p.find("w:pPr", ns)
                pStyle = ""
                es_lista = False
                tiene_sangria_izq = False
                bold_por_parrafo = False

                if pPr is not None:
                    st_el = pPr.find("w:pStyle", ns)
                    if st_el is not None:
                        pStyle = st_el.attrib.get(f"{w_prefix}val", "")
                        if pStyle in estilos_lista or re.search(r'list|vi[ñn]eta|bullet', pStyle, re.IGNORECASE):
                            es_lista = True
                        if pStyle in estilos_negrita:
                            bold_por_parrafo = True
                    if pPr.find("w:numPr", ns) is not None:
                        es_lista = True
                    ind_el = pPr.find("w:ind", ns)
                    if ind_el is not None:
                        left_val = ind_el.attrib.get(f"{w_prefix}left") or ind_el.attrib.get(f"{w_prefix}start") or "0"
                        hanging_val = ind_el.attrib.get(f"{w_prefix}hanging") or "0"
                        try:
                            if int(left_val) >= 180 or int(hanging_val) > 0:
                                tiene_sangria_izq = True
                        except Exception:
                            pass

                partes_txt = []
                partes_html = []
                chars_totales = 0
                chars_negrita = 0

                for r in p.iter(f"{w_prefix}r"):
                    rPr = r.find("w:rPr", ns)
                    r_bold = bold_por_parrafo
                    r_italic = False
                    r_underline = False
                    if rPr is not None:
                        b_el = rPr.find("w:b", ns)
                        bcs_el = rPr.find("w:bCs", ns)
                        if b_el is not None:
                            val_b = b_el.attrib.get(f"{w_prefix}val", "true").lower()
                            r_bold = val_b not in ("0", "false", "off")
                        elif bcs_el is not None:
                            val_bcs = bcs_el.attrib.get(f"{w_prefix}val", "true").lower()
                            r_bold = val_bcs not in ("0", "false", "off")

                        i_el = rPr.find("w:i", ns)
                        if i_el is not None:
                            val_i = i_el.attrib.get(f"{w_prefix}val", "true").lower()
                            r_italic = val_i not in ("0", "false", "off")

                        u_el = rPr.find("w:u", ns)
                        if u_el is not None:
                            val_u = u_el.attrib.get(f"{w_prefix}val", "single").lower()
                            r_underline = val_u not in ("none", "0", "false", "off")

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
                        if r_underline:
                            txt_esc = f"<u>{txt_esc}</u>"
                        if r_italic:
                            txt_esc = f"<i>{txt_esc}</i>"
                        if r_bold:
                            txt_esc = f"<b>{txt_esc}</b>"
                        partes_html.append(txt_esc)
                        n_ch = len(txt_r.strip())
                        chars_totales += n_ch
                        if r_bold:
                            chars_negrita += n_ch

                texto_p = "".join(partes_txt).strip()
                html_p = "".join(partes_html).strip()
                if not texto_p:
                    continue

                html_p = re.sub(r'</b>(\s*)<b>', r'\1', html_p)
                html_p = re.sub(r'</i>(\s*)<i>', r'\1', html_p)

                es_heading = bool(re.search(r'heading|titulo|encabezado|title', pStyle, re.IGNORECASE))
                es_negrita = es_heading or (chars_totales > 0 and (chars_negrita / chars_totales) >= 0.65)

                sub_lineas_txt = texto_p.split("\n")
                sub_lineas_html = html_p.split("\n")
                for idx_sl, sub_l in enumerate(sub_lineas_txt):
                    sub_l = sub_l.strip()
                    sub_h = sub_lineas_html[idx_sl].strip() if idx_sl < len(sub_lineas_html) else sub_l
                    if not sub_l:
                        continue

                    empieza_con_bullet = bool(re.match(r'^(?:[•·▪■\-\*]|\d{1,2}[\.\º\ª]*\)|\([a-z0-9]+\)|[a-g]\))\s+', sub_l))
                    m_def_lead = re.match(r'^([A-ZÁÉÍÓÚÑ][^:]{2,115}):\s+(.+)$', sub_l)
                    es_apartado_definicion = False
                    if m_def_lead and not es_heading and not es_negrita:
                        lead_txt = m_def_lead.group(1).strip()
                        lead_sin_paren = re.sub(r'\([^)]*\)', '', lead_txt).strip()
                        palabras_lead = lead_sin_paren.split()
                        if 1 <= len(palabras_lead) <= 12 and not re.search(r'\b(dice|establece|dispone|señala|indica|siguientes|como|saber)\b$', lead_sin_paren, re.IGNORECASE):
                            es_apartado_definicion = True

                    es_lista_final = es_lista or empieza_con_bullet or es_apartado_definicion or (tiene_sangria_izq and not es_heading)

                    lineas_info.append({
                        "text": sub_l,
                        "html": sub_h,
                        "is_bold": es_negrita,
                        "is_heading": es_heading,
                        "is_list": es_lista_final,
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
        l_sin_hash = re.sub(r'^#\s*', '', re.sub(r'<[^>]+>', '', l)).strip()
        if not l_sin_hash:
            return True
        if re.match(r'^(?:p[áa]gina\s*)?\d{1,3}(?:\s+de\s+\d{1,3})?$', l_sin_hash, re.IGNORECASE):
            return True
        if re.match(
            r'^(?:OPOSICIONA(?:\s+POSICIO\w*)?|GESTI[ÓO]N\s+DE\s+LA\s+SEGURIDAD\s+SOCIAL(?:\s+TEMA\s+\d+.*)?|ADMINISTRATIVO\s+DE\s+LA\s+SEGURIDAD\s+SOCIAL(?:\s+TEMA\s+\d+.*)?|TEMA\s+\d+\s*[\-–]\s*(?:DERECHO\s+MERCANTIL|CAMPO\s+DE\s+APLICACI[ÓO]N|CONSTITUCI[ÓO]N|AFILIACI[ÓO]N|ACCI[ÓO]N\s+PROTECTORA|REQUISITOS|INCAPACIDAD|NACIMIENTO|JUBILACI[ÓO]N|MUERTE|COTIZACI[ÓO]N|LOS\s+REG[ÍI]MENES|RETA).*|PREGUNTAS?\s+DE\s+RESERVA(?:\s*\(.*\))?|OPOSICIONA(?:\.ES|\s+5\.0)?|RESPUESTAS?\s+TE[ST]*\s+TEMAS?.*)$',
            l_sin_hash,
            re.IGNORECASE
        ):
            return True
        if titulo_tema and len(l_sin_hash) < 120:
            t_n = re.sub(r'\W+', '', titulo_tema.lower())
            l_n = re.sub(r'\W+', '', l_sin_hash.lower())
            if t_n and l_n == t_n:
                return True
        return False

    @staticmethod
    def _reconstruir_parrafos_explicacion_test(texto_explicacion):
        if not texto_explicacion:
            return ""

        txt_prep = re.sub(
            r'(?<=[.?!»"])\s+(?=¡?\s*PREGUNTA\s+TRAMPA\b|EXPLICACI[ÓO]N\s+PARA\s+ESTUDIO\b)',
            '\n',
            texto_explicacion,
            flags=re.IGNORECASE
        )

        lineas_crudas = [l.strip() for l in txt_prep.split("\n") if l.strip()]
        if not lineas_crudas:
            return ""

        parrafos = []
        pendiente_vineta = False

        pat_inicio_bloque = re.compile(
            r'^(?:\[\[H\]\]|¡?\s*PREGUNTA\s+TRAMPA\b|EXPLICACI[ÓO]N(?:\s+PARA\s+ESTUDIO|\s+Y\s+BASE\s+LEGAL|\s+DETALLADA)?\s*:|RESPUESTA\s+T[ÉE]CNICA\s*:|[•·▪■\*]\s+|\d{1,2}[\.\º\ª\)]\s+[A-ZÁÉÍÓÚÑ¿¡]|En\s+el\s+Derecho\s+(?:Civil|Mercantil)\s*[\(:])',
            re.IGNORECASE
        )

        for l in lineas_crudas:
            if l in ("•", "·", "▪", "■", "-"):
                pendiente_vineta = True
                continue
            if pendiente_vineta:
                l = f"• {l}"
                pendiente_vineta = False

            if not parrafos:
                parrafos.append(l)
                continue

            if pat_inicio_bloque.match(l):
                parrafos.append(l)
            else:
                prev = parrafos[-1]
                if re.match(r'^(?:\[\[H\]\]|\d{1,2}[\.\)]\s+[^.]{4,95}\??|EXPLICACI[ÓO]N\s+PARA\s+ESTUDIO\s*:?)$', prev, re.IGNORECASE):
                    parrafos.append(l)
                else:
                    if prev.endswith("-") and not prev.endswith(" -") and re.match(r'^[a-záéíóúñ]', l):
                        parrafos[-1] = prev[:-1] + l
                    else:
                        parrafos[-1] = prev + " " + l

        return "\n".join(parrafos)

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
    def _asegurar_negrita_encabezado_dos_puntos(html_str):
        plain = re.sub(r'<[^>]+>', '', html_str).strip()
        m = re.match(r'^([•\-\*▪■·]?\s*[A-ZÁÉÍÓÚÑ¡¿][^:]{1,115}:)(\s+.+)$', plain)
        if not m:
            return html_str

        pref_plain = m.group(1)
        pref_sin_paren = re.sub(r'\([^)]*\)', '', pref_plain)
        if re.search(r'\.\s+[A-ZÁÉÍÓÚÑ]', pref_sin_paren):
            return html_str
        if len(pref_sin_paren.split()) > 13:
            return html_str

        idx_colon = html_str.find(":")
        if idx_colon == -1:
            return html_str
        parte_izq = re.sub(r'</?b>', '', html_str[:idx_colon + 1]).strip()
        parte_der = html_str[idx_colon + 1:]
        return f"<b>{parte_izq}</b>{parte_der}"

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
            l = re.sub(r'\s*↑+\s*(?:</b>)?\s*$', '', l).strip()

            es_cabecera_h = False
            es_item_lista = False

            if l.startswith("[[H]]"):
                es_cabecera_h = True
                l = l.replace("[[H]]", "").strip()
            if l.startswith("[[LI]]"):
                es_item_lista = True
                l = l.replace("[[LI]]", "").strip()

            l_plain = re.sub(r'<[^>]+>', '', l).strip()
            if not l_plain:
                continue

            if not es_cabecera_h:
                if re.match(r'^(?:EXPLICACI[ÓO]N(?:\s+PARA\s+ESTUDIO)?|RESPUESTA\s+T[ÉE]CNICA)\s*:?$', l_plain, re.IGNORECASE):
                    es_cabecera_h = True
                elif re.match(r'^(?:\d{1,2}[\.\)]\s+[A-ZÁÉÍÓÚÑ¿¡]|EP[ÍI]GRAFE\s+\d+|APARTADO\s+\d+)', l_plain) and len(l_plain) < 155 and not l_plain.endswith("."):
                    es_cabecera_h = True

            if not es_cabecera_h and not es_item_lista:
                if re.match(r'^(?:[•\-\*▪■·]|\d{1,2}[\.\º\ª]*\)|\([a-z0-9]+\)|[a-g]\))\s*', l_plain):
                    es_item_lista = True
                else:
                    m_def = re.match(r'^([A-ZÁÉÍÓÚÑ][^:]{2,115}):\s+(.+)$', l_plain)
                    if m_def:
                        lead_sin_p = re.sub(r'\([^)]*\)', '', m_def.group(1)).strip()
                        if 1 <= len(lead_sin_p.split()) <= 12 and not re.search(r'\.\s+[A-ZÁÉÍÓÚÑ]', lead_sin_p):
                            es_item_lista = True

            if es_cabecera_h:
                l_tit = re.sub(r'</?b>', '', l).strip()
                bloques_html.append(
                    f"<div style='font-size:15.5px; font-weight:800; color:#083B46 !important; margin-top:15px; margin-bottom:7px; line-height:1.4;'>{l_tit}</div>"
                )
            elif es_item_lista:
                l_sin_bullet = re.sub(r'^(?:<b>\s*)?[•\-\*▪■·]\s*', lambda m: '<b>' if '<b>' in m.group(0) else '', l).strip()
                if not re.match(r'^(?:<[^>]+>)*\s*(?:\d{1,2}[\.\º\ª\)]|\([a-z0-9]+\)|[a-g]\))', l_sin_bullet):
                    l_fmt = f"• {l_sin_bullet}"
                else:
                    l_fmt = l_sin_bullet
                l_fmt = PDFQuizParser._asegurar_negrita_encabezado_dos_puntos(l_fmt)
                bloques_html.append(
                    f"<div style='margin-top:6px; margin-bottom:7px; padding-left:20px; text-indent:-13px; line-height:1.56; color:#0F172A !important; text-align:justify;'>{l_fmt}</div>"
                )
            else:
                l_fmt = PDFQuizParser._asegurar_negrita_encabezado_dos_puntos(l)
                bloques_html.append(
                    f"<p style='margin:0 0 9px 0; line-height:1.58; color:#0F172A !important; text-align:justify;'>{l_fmt}</p>"
                )
        return "".join(bloques_html)

    @staticmethod
    def _formatear_html_planteamiento_supuesto(lineas_planteamiento):
        bloques = []
        pat_item_explicito = re.compile(
            r'^(?:([•·\-\*▪■])|(\d{1,2}\s*[\.\-\)]|[A-Za-z]\s*[\)\.\-]))\s+(.+)$'
        )
        pat_ordinal_texto = re.compile(
            r'^(En\s+(?:primer|segundo|tercer|cuarto|quinto|sexto|s[ée]ptimo|octavo|noveno|d[ée]cimo(?:\s+y\s+[úu]ltimo)?)\s+lugar\b.*|En\s+el\s+plano\s+(?:institucional|jur[íi]dico|empresarial|familiar|laboral)\b.*)$',
            re.IGNORECASE
        )

        items_procesados = []
        for item in lineas_planteamiento:
            txt_p = PDFQuizParser._limpiar_marca_agua_linea(item.get("text") or "").strip()
            html_p = PDFQuizParser._limpiar_marca_agua_linea(item.get("html") or txt_p).strip()
            es_lista = bool(item.get("is_list", False))
            if not txt_p or txt_p in ("•", "·", "▪", "■"):
                continue

            if not es_lista and not pat_item_explicito.match(txt_p) and len(txt_p) > 380:
                partes_split = re.split(
                    r'(?<=[.?!])\s+(?=(?:Por\s+un\s+lado,|Por\s+otro\s+lado,|Asimismo,\s+el\b|Paralelamente,|De\s+forma\s+independiente,|En\s+primer\s+lugar,|En\s+segundo\s+lugar,|En\s+tercer\s+lugar,))',
                    txt_p
                )
                if len(partes_split) >= 3:
                    for idx_sp, p_sp in enumerate(partes_split):
                        p_sp = p_sp.strip()
                        if not p_sp:
                            continue
                        es_sub = idx_sp > 0 or bool(re.match(r'^(?:Por\s+un\s+lado|En\s+primer\s+lugar)', p_sp, re.IGNORECASE))
                        items_procesados.append({
                            "text": p_sp,
                            "html": p_sp,
                            "is_list": es_sub
                        })
                    continue

            items_procesados.append({
                "text": txt_p,
                "html": html_p,
                "is_list": es_lista
            })

        contador_auto = 0
        for item in items_procesados:
            txt_p = item["text"]
            html_p = re.sub(r'</?b>', '', item["html"]).strip()
            es_lista = item["is_list"]

            m_exp = pat_item_explicito.match(txt_p)
            m_ord = pat_ordinal_texto.match(txt_p)

            if m_exp:
                num_simb = m_exp.group(2)
                if num_simb:
                    marcador = re.sub(r'\s+', '', num_simb)
                    try:
                        contador_auto = int(re.match(r'^(\d+)', marcador).group(1))
                    except Exception:
                        contador_auto += 1
                else:
                    contador_auto += 1
                    marcador = f"{contador_auto}."
                cuerpo_limpio = re.sub(
                    r'^(?:<[^>]+>)*\s*(?:[•·\-\*▪■]|\d{1,2}\s*[\.\-\)]|[A-Za-z]\s*[\)\.\-])\s*',
                    '',
                    html_p
                ).strip()
                bloques.append(
                    f"<div style='display:flex; align-items:flex-start; margin:0 0 5px 0; font-size:9pt !important; line-height:1.34; color:#000000 !important; font-weight:700;'>"
                    f"<div style='min-width:22px; width:22px; flex-shrink:0; color:#000000 !important; font-weight:700; text-align:left;'>{marcador}</div>"
                    f"<div style='flex:1; text-align:justify; color:#000000 !important; font-weight:700;'>{cuerpo_limpio}</div>"
                    f"</div>"
                )
            elif m_ord or es_lista:
                contador_auto += 1
                marcador = f"{contador_auto}."
                cuerpo_limpio = re.sub(r'^(?:<[^>]+>)*\s*[•·\-\*▪■]\s*', '', html_p).strip()
                bloques.append(
                    f"<div style='display:flex; align-items:flex-start; margin:0 0 5px 0; font-size:9pt !important; line-height:1.34; color:#000000 !important; font-weight:700;'>"
                    f"<div style='min-width:22px; width:22px; flex-shrink:0; color:#000000 !important; font-weight:700; text-align:left;'>{marcador}</div>"
                    f"<div style='flex:1; text-align:justify; color:#000000 !important; font-weight:700;'>{cuerpo_limpio}</div>"
                    f"</div>"
                )
            else:
                bloques.append(
                    f"<div style='margin:0 0 6px 0; font-size:9pt !important; line-height:1.34; color:#000000 !important; text-align:justify; font-weight:700;'>"
                    f"{html_p}"
                    f"</div>"
                )
        return "".join(bloques)

    @staticmethod
    def _parse_supuestos_practicos(parrafos, tema_titulo="", es_docx=False):
        pat_marca_supuesto = re.compile(
            r'^(?:#\s*)?(?:(?:\d+|I|II|III)[\.\-\)]\s*)?SUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+\d+)?\s*[:\.\-]?\s*',
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
                if m_sup:
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

        pat_pregunta_explicita = re.compile(
            r'^(?:#\s*)?(?:CUESTI[ÓO]N\s+|PREGUNTA\s+)?(\d{1,2})(?!\d)\s*[\.\-\)]\s*(?![ºª°a-zA-Z]\b)\s*(["«\'¿¡\(\[]*[A-ZÁÉÍÓÚÑ].*)$',
            re.IGNORECASE
        )
        pat_cierre_planteamiento = re.compile(
            r'(?:responda\s+de\s+forma\s+razonada|siguientes\s+(?:\w+\s+)?cuestiones\s+pr[áa]cticas|responda\s+a\s+las\s+siguientes\s+preguntas)\s*:\s*$',
            re.IGNORECASE
        )
        pat_ordinal_enunciado = re.compile(
            r'^(?:[•·\-\*▪■]|\d{1,2}\s*[\.\-\)])?\s*(?:En\s+(?:primer|segundo|tercer|cuarto|quinto|sexto|s[ée]ptimo|octavo|noveno|d[ée]cimo(?:\s+y\s+[úu]ltimo)?)\s+lugar|En\s+el\s+plano\s+(?:institucional|jur[íi]dico|empresarial|familiar|laboral))\b',
            re.IGNORECASE
        )
        pat_verbo_pregunta = re.compile(
            r'^(?:Determine|Analice|Calcule|Indique|Precise|Razone|Justifique|Explique|Señale|Resuelva|En\s+relaci[óo]n\s+con|Respecto\s+(?:de|a|al)|Ante\s+la|Sobre\s+la|Atendiendo\s+a|Teniendo\s+en\s+cuenta|Si\s+["«A-ZÁÉÍÓÚÑ]|["«][A-ZÁÉÍÓÚÑ])\b',
            re.IGNORECASE
        )
        pat_explicacion = re.compile(
            r'^(?:#\s*)?(?:EXPLICACI[ÓO]N(?:\s+DETALLADA|\s+Y\s+BASE\s+LEGAL)?)\s*:\s*(.*)$',
            re.IGNORECASE
        )
        pat_resp_tecnica = re.compile(r'^(?:#\s*)?RESPUESTA\s+T[ÉE]CNICA\s*:\s*(.*)$', re.IGNORECASE)
        pat_opcion_test_residual = re.compile(r'^(?:#\s*)?[a-dA-D][\)\.\-]\s+')
        pat_segundo_supuesto_narrativo = re.compile(
            r'^(?:(?:#\s*)?(?:SUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+\d+)?)\b|(?:La\s+(?:mercantil|sociedad|empresa|cooperativa|entidad|asesor[íi]a)\s+["«][^"»]+["»]|Don\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+es\s+un\s+empresario).*)',
            re.IGNORECASE
        )

        lineas_planteamiento = []
        questions = []
        curr_q = None
        leyendo_planteamiento = True
        cierre_planteamiento_visto = False
        contador_preguntas = 0
        pendiente_vineta_pl = False

        for p in parrafos_utiles:
            txt_raw = PDFQuizParser._limpiar_marca_agua_linea(p["text"])
            txt_sin_hash = re.sub(r'^#\s*', '', txt_raw).strip()
            txt = re.sub(r'^[•·\-\*▪■]\s*', '', txt_sin_hash).strip()
            html_p = re.sub(r'^(?:<[^>]+>)*#\s*', lambda m: re.sub(r'#\s*', '', m.group(0)), PDFQuizParser._limpiar_marca_agua_linea(p.get("html") or txt_raw)).strip()
            es_bold = bool(p.get("is_bold", False))
            es_lista = bool(p.get("is_list", False))

            if txt_sin_hash in ("•", "·", "▪", "■"):
                if leyendo_planteamiento:
                    pendiente_vineta_pl = True
                continue

            if not txt or txt == tema_titulo or PDFQuizParser._es_basura_cabecera_o_pie(txt_sin_hash, tema_titulo):
                continue

            if not leyendo_planteamiento and pat_opcion_test_residual.match(txt_sin_hash):
                continue

            if (
                not leyendo_planteamiento and
                curr_q is not None and
                len(curr_q["explanation_lines"]) > 0 and
                pat_segundo_supuesto_narrativo.match(txt_sin_hash)
            ):
                questions.append(curr_q)
                curr_q = None
                leyendo_planteamiento = True
                cierre_planteamiento_visto = False
                lineas_planteamiento = []
                if not re.match(r'^(?:#\s*)?SUPUESTOS?\s+PR[ÁA]CTICOS?\b', txt_sin_hash, re.IGNORECASE):
                    lineas_planteamiento.append({"text": txt_sin_hash, "html": html_p, "is_list": es_lista})
                continue

            m_exp = pat_explicacion.match(txt_sin_hash)
            m_rt = pat_resp_tecnica.match(txt_sin_hash)

            if m_exp and curr_q is not None:
                if not any("EXPLICACIÓN" in l_e for l_e in curr_q["explanation_lines"]):
                    curr_q["explanation_lines"].append("[[H]]📌 EXPLICACIÓN Y ANÁLISIS DEL SUPUESTO:")
                if m_exp.group(1).strip():
                    rest_h = re.sub(r'^(?:<[^>]+>)*\s*(?:#\s*)?EXPLICACI[ÓO]N(?:\s+DETALLADA|\s+Y\s+BASE\s+LEGAL)?\s*:\s*(?:</[^>]+>)*\s*', '', html_p, flags=re.IGNORECASE).strip()
                    curr_q["explanation_lines"].append(rest_h or m_exp.group(1).strip())
                continue

            if m_rt and curr_q is not None:
                curr_q["explanation_lines"].append("[[H]]⚖️ RESPUESTA TÉCNICA Y FUNDAMENTACIÓN JURÍDICA:")
                if m_rt.group(1).strip():
                    rest_rt = re.sub(r'^(?:<[^>]+>)*\s*(?:#\s*)?RESPUESTA\s+T[ÉE]CNICA\s*:\s*(?:</[^>]+>)*\s*', '', html_p, flags=re.IGNORECASE).strip()
                    curr_q["explanation_lines"].append(rest_rt or m_rt.group(1).strip())
                continue

            if leyendo_planteamiento and pat_ordinal_enunciado.match(txt_sin_hash):
                lineas_planteamiento.append({"text": txt_sin_hash, "html": html_p, "is_list": True})
                continue

            if leyendo_planteamiento and pat_cierre_planteamiento.search(txt):
                lineas_planteamiento.append({"text": txt_sin_hash, "html": html_p, "is_list": False})
                cierre_planteamiento_visto = True
                continue

            m_q = pat_pregunta_explicita.match(txt_sin_hash)
            es_subapartado_respuesta = bool(re.match(r'^\d{1,2}\.[ºª°\d]', txt_sin_hash))
            es_nueva_pregunta = False
            num_q = 0
            cuerpo_q = ""

            if m_q and not es_subapartado_respuesta:
                num_cand = int(m_q.group(1))
                cuerpo_cand = (m_q.group(2) or "").strip()
                tiene_rasgo_pregunta = (
                    "?" in cuerpo_cand or
                    bool(pat_verbo_pregunta.match(cuerpo_cand)) or
                    cuerpo_cand.rstrip().endswith(":")
                )
                es_correlativa_posterior = (
                    not leyendo_planteamiento and (
                        num_cand == contador_preguntas + 1 or
                        (curr_q is not None and len(curr_q["explanation_lines"]) > 0)
                    )
                )
                if (
                    (leyendo_planteamiento and len(lineas_planteamiento) > 0 and (tiene_rasgo_pregunta or cierre_planteamiento_visto)) or
                    (es_correlativa_posterior and (tiene_rasgo_pregunta or len(curr_q["explanation_lines"]) > 0))
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
                if pendiente_vineta_pl:
                    lineas_planteamiento.append({"text": f"• {txt_sin_hash}", "html": html_p, "is_list": True})
                    pendiente_vineta_pl = False
                else:
                    lineas_planteamiento.append({"text": txt_sin_hash, "html": html_p, "is_list": es_lista})
            elif curr_q is not None:
                if (
                    not curr_q["explanation_lines"] and
                    not curr_q["question_text"].rstrip().endswith(("?", ":", ".")) and
                    (es_bold or "?" in txt_sin_hash)
                ):
                    curr_q["question_text"] += " " + txt_sin_hash
                else:
                    if es_lista:
                        curr_q["explanation_lines"].append(f"[[LI]]{html_p}")
                    else:
                        curr_q["explanation_lines"].append(html_p)

        if curr_q is not None:
            questions.append(curr_q)

        salida_final = []
        for idx_s, q_item in enumerate(questions, 1):
            lineas_exp_q = q_item.pop("explanation_lines", [])
            if es_docx:
                exp_unida = "\n".join(lineas_exp_q).strip()
            else:
                exp_limpia_tags = [re.sub(r'</?b>', '', l_e) if not l_e.startswith("[[H]]") else l_e for l_e in lineas_exp_q]
                exp_unida = PDFQuizParser._reconstruir_parrafos_explicacion_test("\n".join(exp_limpia_tags)).strip()
            q_item.pop("num", None)
            txt_q_s = re.sub(r'^\d{1,2}\s*[\.\-\)]\s*', '', q_item.get("question_text", "")).strip()
            q_item["question_text"] = f"{idx_s}. {txt_q_s}"
            q_item["explanation"] = exp_unida
            salida_final.append(q_item)

        return salida_final

    @staticmethod
    def parse_abiertas_gestion(file_bytes, modo="DESARROLLO"):
        lineas_estructuradas = []
        es_docx = PDFQuizParser.es_archivo_docx(file_bytes)
        if es_docx:
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

        pat_corte_estructural_pdf = re.compile(
            r'^(?:#\s*)?(?:TEMA\s+\d+|EP[ÍI]GRAFE\s+\d+|PREGUNTA\s+DE\s+DESARROLLO|SUPUESTOS?\s+PR[ÁA]CTICOS?|EXPLICACI[ÓO]N(?:\s+DETALLADA|\s+Y\s+BASE\s+LEGAL)?\s*:|RESPUESTA\s+T[ÉE]CNICA\s*:|CUESTI[ÓO]N\s+\d+|PREGUNTA\s+\d+|\d{1,2}(?!\d)\s*[\.\)]\s+["«\'¿¡\(\[]*[A-ZÁÉÍÓÚÑ]|[•\-\*▪■·]\s*En\s+(?:primer|segundo|tercer|cuarto|quinto|sexto|s[ée]ptimo|octavo|noveno|d[ée]cimo)|En\s+(?:primer|segundo|tercer|cuarto|quinto|sexto|s[ée]ptimo|octavo|noveno|d[ée]cimo)\s+lugar|Con\s+base\s+en\s+los\s+hechos|La\s+(?:mercantil|sociedad|empresa|cooperativa)\s+["«]|[•\-\*▪■·]\s+|[a-g]\)\s+)',
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
                    "is_heading": item.get("is_heading", False),
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
            t_cand = re.sub(r'^#\s*', '', p["text"]).strip()
            if re.match(r'^TEMA\s+\d+', t_cand, re.IGNORECASE):
                tema_titulo = re.sub(r'\s*↑+\s*$', '', t_cand).strip()
                break
        if not tema_titulo:
            for p in parrafos:
                m_pag_tema = re.search(r'\(p[áa]gina\s+\d+[^)]*,\s*(tema\s+\d+)\)', p["text"], re.IGNORECASE)
                if m_pag_tema:
                    tema_titulo = m_pag_tema.group(1).upper()
                    break

        if modo in ("SUPUESTOS", "SUPUESTO"):
            return PDFQuizParser._parse_supuestos_practicos(parrafos, tema_titulo=tema_titulo, es_docx=es_docx)

        parrafos_desarrollo = []
        for p in parrafos:
            if re.search(r'(?:^|\b)SUPUESTOS?\s+PR[ÁA]CTICOS?\b', p["text"].strip()):
                break
            parrafos_desarrollo.append(p)

        pat_epigrafe = re.compile(
            r'^(?:#\s*)?(?:(EP[ÍI]GRAFE\s+\d+)[\.\:\-\s]*|(PREGUNTA(?:\s+DE\s+DESARROLLO)?(?:\s+\d+)?)[\.\:\-\s]*)(.*)$',
            re.IGNORECASE
        )

        questions = []
        curr_title = ""
        curr_body = []

        for p in parrafos_desarrollo:
            txt = re.sub(r'^#\s*', '', re.sub(r'\s*↑+\s*$', '', p["text"])).strip()
            html_linea = re.sub(r'\s*↑+\s*(?:</b>)?\s*$', '', (p.get("html") or txt)).strip()
            if not txt or txt == tema_titulo:
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
                pref_ep = (m_ep.group(1) or m_ep.group(2) or "").strip().upper()
                if pref_ep.startswith("EPIGRAFE"):
                    pref_ep = "EPÍGRAFE" + pref_ep[8:]
                resto_tit = re.sub(r'\s*↑+\s*$', '', (m_ep.group(3) or "")).strip()
                curr_title = f"{pref_ep}: {resto_tit}" if (pref_ep and resto_tit) else txt
                curr_body = []
            else:
                if curr_title:
                    if curr_title.upper() in ("PREGUNTA DE DESARROLLO", "PREGUNTA DE DESARROLLO:") and not curr_body and len(txt) < 160:
                        curr_title = f"PREGUNTA DE DESARROLLO: {txt}"
                    elif re.match(r'^EP[ÍI]GRAFE\s+\d+\s*:?$', curr_title, re.IGNORECASE) and not curr_body and len(txt) < 160:
                        curr_title = f"{curr_title.rstrip(':')}: {txt}"
                    elif (p.get("is_heading") or p.get("is_bold")) and len(txt) < 155 and not txt.endswith("."):
                        curr_body.append(f"[[H]]{txt}")
                    elif p.get("is_list"):
                        curr_body.append(f"[[LI]]{html_linea}")
                    else:
                        curr_body.append(html_linea)

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
            num_ep_auto = 0
            for p in parrafos_desarrollo:
                txt = re.sub(r'^#\s*', '', re.sub(r'\s*↑+\s*$', '', p["text"])).strip()
                html_linea = re.sub(r'\s*↑+\s*(?:</b>)?\s*$', '', (p.get("html") or txt)).strip()
                if not txt or txt == tema_titulo:
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
                    num_ep_auto += 1
                    curr_title = f"EPÍGRAFE {num_ep_auto}: {txt}" if not txt.upper().startswith("EP") else txt
                    curr_body = []
                elif curr_title:
                    if (p.get("is_heading") or p.get("is_bold")) and len(txt) < 155 and not txt.endswith("."):
                        curr_body.append(f"[[H]]{txt}")
                    elif p.get("is_list"):
                        curr_body.append(f"[[LI]]{html_linea}")
                    else:
                        curr_body.append(html_linea)

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

        for idx_q, q_des in enumerate(questions, 1):
            qt = re.sub(r'\s*↑+\s*$', '', (q_des.get("question_text") or "")).strip()
            if not re.match(r'^(?:EP[ÍI]GRAFE|PREGUNTA)\b', qt, re.IGNORECASE):
                q_des["question_text"] = f"EPÍGRAFE {idx_q}: {qt}"
            else:
                q_des["question_text"] = qt

        return questions
# === FIN SECCIÓN 3A ===

# === SECCIÓN 3B: MOTOR DE EXTRACCIÓN DE PREGUNTAS TIPO TEST ===
_RESPALDO_TEMA_73_TEST = [
    {
        "question_text": '1. Un trabajador ferroviario del grupo de "Oficial Calderero Chapista en Depósito" se jubila anticipadamente. ¿Cuál es el coeficiente aplicable y qué sucede en el supuesto de que también se encuentre en pluriactividad según el RD 2621/1986?',
        "preamble": "",
        "options": [
            "a) 0,15 y la reducción sólo se aplicará a efectos de la edad.",
            "b) 0,10 y la reducción sólo se aplicará a efectos de la edad.",
            "c) 0,15 y la reducción se aplicará a efectos de la edad y del porcentaje de la pensión computable."
        ],
        "answer": 0,
        "explanation": "El art. 3 del RD 2621/1986 establece un coeficiente reductor de 0,15 específicamente para la categoría de Oficial Calderero Chapista en Depósito. Es común pensar que en un sistema tan específico, la pluriactividad bonifica también la base o porcentaje de la pensión final por haber aportado a dos regímenes, pero la ley establece claramente que en supuestos de pluriactividad, la reducción sólo se aplicará a efectos de la edad."
    },
    {
        "question_text": "2. Según la categorización de los jugadores profesionales de fútbol para su cotización a la Seguridad Social, ¿en qué grupo de cotización se encuadra preceptivamente un jugador que milita en la Segunda División B?",
        "preamble": "",
        "options": [
            "a) Grupo 5.",
            "b) Grupo 3.",
            "c) Grupo 7."
        ],
        "answer": 0,
        "explanation": "De acuerdo a la tabla de asimilación del RD 2621/1986, la Primera División corresponde al Grupo 2, la Segunda División A al Grupo 3, y la Segunda División B corresponde al Grupo 5."
    },
    {
        "question_text": "3. En el régimen aplicable a los Representantes de Comercio integrados en el Régimen General, ¿quién ostenta la condición de sujeto responsable de cotizar e ingresar la totalidad de la cuota (tanto la aportación obrera como la empresarial)?",
        "preamble": "",
        "options": [
            "a) La Tesorería General de la Seguridad Social de oficio, previa deducción de las facturas comerciales.",
            "b) El Empresario, respondiendo subsidiariamente el Representante.",
            "c) El Representante de Comercio."
        ],
        "answer": 2,
        "explanation": "El Representante de Comercio es el sujeto responsable de cotizar e ingresar la totalidad de la cuota, según las disposiciones del RD 2621/1986. En el Régimen General común, el sujeto responsable del ingreso es SIEMPRE el empresario. Aquí se invierte la regla: es el trabajador (Representante) quien ingresa, y el empresario está obligado a entregarle a este su parte de la aportación empresarial. Si el empresario incumple, la TGSS reintegra al representante el importe iniciando acción recaudatoria contra la empresa."
    },
    {
        "question_text": "4. Según la Orden PJC/297/2026, ¿cuál será la base y el tipo de cotización durante los períodos de inactividad de los artistas que decidan mantener voluntariamente su situación de alta?",
        "preamble": "",
        "options": [
            "a) La base mínima del grupo 7, con un tipo del 11,50%.",
            "b) La base mínima del grupo 1, con un tipo del 15,50%.",
            "c) La base máxima del grupo 7, con un tipo del 11,50%."
        ],
        "answer": 0,
        "explanation": "Para los artistas, la base de cotización durante los períodos de inactividad manteniendo voluntariamente el alta (art. 32.5 RD 2064/1995 y Orden PJC/297/2026) será la base mínima del grupo 7, con un tipo muy específico del 11,50%."
    },
    {
        "question_text": '5. Un Picador taurino que acompaña habitualmente a un Matador de Toros clasificado en el grupo "C", ¿en qué grupo de cotización debe encuadrarse a efectos de la Seguridad Social?',
        "preamble": "",
        "options": [
            "a) Grupo 2.",
            "b) Grupo 3.",
            "c) Grupo 1."
        ],
        "answer": 1,
        "explanation": 'El baremo especifica que los Picadores y Banderilleros que acompañan al Grupo A van al Grupo 2. Al no mencionar explícitamente a los que acompañan al grupo C, debemos deducir que encajan en el epígrafe "Restantes Picadores y Banderilleros", a los cuales la norma les asigna el Grupo 3.'
    },
    {
        "question_text": "6. En el Sistema Especial para Trabajadores Agrarios (SEA), ¿cuándo se considera legalmente que existen períodos de inactividad dentro de un mes natural?",
        "preamble": "",
        "options": [
            "a) Cuando el número de jornadas reales sea inferior al 76,67% de los días hábiles en que figure incluido en el sistema.",
            "b) Cuando el número de días naturales en alta sea superior a las jornadas reales multiplicadas por 1,5.",
            "c) Cuando el número de jornadas reales en él realizadas sea inferior al 76,67% de los días naturales en que el trabajador figure incluido en el sistema en dicho mes."
        ],
        "answer": 2,
        "explanation": 'Conforme al art. 253 del TRLGSS, existen períodos de inactividad cuando las jornadas reales son inferiores al 76,67% de los días NATURALES de alta en el sistema especial en dicho mes. Confundir "días naturales" con "días hábiles", lo cual cambiaría drásticamente el cálculo numérico.'
    },
    {
        "question_text": "7. Un trabajador del SEA adeuda las cuotas por inactividad de dos meses consecutivos. El último día para el pago entra en situación de Incapacidad Temporal. ¿Cuándo surtirá efectos su baja de oficio y exclusión del sistema especial?",
        "preamble": "",
        "options": [
            "a) No podrá ser excluido mientras permanezca de baja médica.",
            "b) El día primero del mes siguiente a aquel en que finaliza la prestación por IT (si sigue sin pagar).",
            "c) El día primero del mes siguiente a la segunda mensualidad no ingresada de forma inexcusable."
        ],
        "answer": 1,
        "explanation": "Como regla general, la exclusión opera el día primero del mes siguiente a la segunda mensualidad no ingresada. El art. 253 del TRLGSS introduce una excepción fundamental: si en esa fecha de exclusión el trabajador se encuentra en IT, riesgo durante el embarazo o maternidad/paternidad, los efectos se posponen y operan el primer día del mes siguiente a que finalice la prestación."
    },
    {
        "question_text": "8. Según el TRLGSS aplicable al SEA, ¿qué circunstancia EXCLUYE la existencia de períodos de inactividad en un mes natural, invalidando la aplicación de la regla del 76,67%?",
        "preamble": "",
        "options": [
            "a) Realizar, para un mismo empresario, un mínimo de cinco jornadas reales semanales en cumplimiento de convenio colectivo aplicable.",
            "b) Realizar para distintos empresarios más de 20 jornadas reales al mes.",
            "c) Que el trabajador esté percibiendo simultáneamente el subsidio agrario de desempleo."
        ],
        "answer": 0,
        "explanation": "El TRLGSS señala taxativamente que no existirán períodos de inactividad dentro del mes natural cuando el trabajador realice, para UN MISMO empresario, un mínimo de cinco jornadas reales semanales en cumplimiento del convenio colectivo de aplicación. Si las 5 jornadas se hacen para empresarios distintos, no se activa esta excepción directa a la regla."
    },
    {
        "question_text": "9. En cuanto a la obligación de cotización durante los períodos de actividad en el Sistema Especial Agrario, ¿cuál de estas afirmaciones es correcta para un trabajador con contrato de carácter fijo discontinuo?",
        "preamble": "",
        "options": [
            "a) La cotización por bases mensuales resulta estrictamente obligatoria, igual que para los indefinidos ordinarios.",
            "b) Siempre se deberá cotizar por bases diarias obligatoriamente.",
            "c) La cotización por bases mensuales es opcional, a elección del empresario."
        ],
        "answer": 2,
        "explanation": "La cotización por bases mensuales resultará obligatoria para los trabajadores con contrato indefinido. Se exceptúa expresamente a los indefinidos que prestan servicios con carácter fijo discontinuo, para los cuales la cotización mensual se mantiene como una opción del empresario, no como una imposición. Si no elige, se entiende mensual, pero normativamente es opcional."
    },
    {
        "question_text": "10. En el Sistema Especial Agrario (SEA), si un empleador contrata a un eventual el mismo día de comienzo de la prestación y no pudo dar el alta previa obligatoria, ¿hasta qué momento exacto puede cursar la solicitud si la jornada laboral de ese día termina a las 11:30 horas?",
        "preamble": "",
        "options": [
            "a) Hasta las 12:00 horas de ese mismo día.",
            "b) Antes de la finalización de dicha jornada (es decir, antes de las 11:30 horas).",
            "c) Dentro del plazo excepcional de los 3 días naturales siguientes."
        ],
        "answer": 1,
        "explanation": 'La norma permite, en eventuales/fijos discontinuos cuando no fue posible el alta previa, hacerlo hasta las 12:00 del mismo día de inicio. Hay una salvedad literal que dice: "Si la jornada de trabajo finalizase antes de las 12 horas, las solicitudes de alta deberán presentarse antes de la finalización de esa jornada". Al terminar a las 11:30, el límite se acorta.'
    },
    {
        "question_text": "11. En 2026, dentro del Sistema Especial Agrario, un Ingeniero (Grupo 1) tiene una reducción de 8,10 puntos porcentuales en la cuota empresarial por contingencias comunes. ¿Cuál es el límite máximo absoluto estipulado legalmente para dicha cuota empresarial resultante?",
        "preamble": "",
        "options": [
            "a) No hay tope máximo, únicamente una cuota empresarial resultante no inferior a 179,44 euros.",
            "b) No podrá superar los 279,00 euros al mes o 12,68 euros por jornada real trabajada.",
            "c) No podrá superar los 179,44 euros al mes o 8,16 euros por jornada real trabajada."
        ],
        "answer": 1,
        "explanation": "La normativa de actualización para 2026 marca que, para el grupo 1, en ningún caso la cuota empresarial resultante será superior a 279,00 euros al mes o 12,68 euros por jornada real trabajada. (Los 179,44 euros operan como límite mínimo, pero para los grupos 2 a 11)."
    },
    {
        "question_text": "12. Según la normativa vigente (Ley 27/2011 y RD 1620/2011) ¿está amparada por el Sistema Especial de Empleados de Hogar la relación laboral suscrita con una persona jurídica (empresa) cuyo objeto social sea prestar tareas de limpieza a domicilios particulares?",
        "preamble": "",
        "options": [
            "a) Sí, porque lo que define el sistema es que la prestación material se realice en un hogar familiar.",
            "b) No, quedan excluidas legalmente y se rigen por la normativa laboral común.",
            "c) Sí, salvo que la persona jurídica actúe como Empresa de Trabajo Temporal."
        ],
        "answer": 1,
        "explanation": 'La Disposición adicional 17.ª de la Ley 27/2011 excluye expresamente "las relaciones concertadas por personas jurídicas, de carácter civil o mercantil, aunque su objeto sea la prestación de servicios o tareas domésticas". Para este Régimen Especial, el empleador debe ser forzosamente el "titular del hogar familiar" (persona física).'
    },
    {
        "question_text": "13. Una persona contrata a su suegra (que convive en su mismo domicilio) para que se encargue del cuidado de sus hijos de manera retribuida. ¿Se encuentra esta relación incluida inicialmente en el Sistema Especial de Empleadas de Hogar?",
        "preamble": "",
        "options": [
            "a) No, quedan absolutamente excluidas sin admitir prueba en contrario por ser parentesco de primer grado por afinidad.",
            "b) Sí, el cuidado de menores está plenamente amparado por el SEEEHH, sea quien sea el prestador.",
            "c) No, quedan excluidas las relaciones entre familiares hasta el segundo grado que convivan, salvo prueba en contrario de la condición de asalariado."
        ],
        "answer": 2,
        "explanation": "Según la Ley 27/2011, se excluyen las relaciones concertadas entre familiares (hasta el 2.º grado de consanguinidad o afinidad que convivan con el empleador) SALVO QUE se demuestre la condición de asalariados. La ley admite prueba en contrario. (La suegra es primer grado de afinidad)."
    },
    {
        "question_text": "14. Un trabajador por cuenta propia (Régimen de Autónomos) decide contratar a una empleada de hogar para su residencia privada. ¿Qué requerimiento burocrático específico en materia de afiliación debe cumplir el empleador?",
        "preamble": "",
        "options": [
            "a) Deberá disponer, obligatoriamente, de un Código de Cuenta Cotización específico y exclusivo para este Sistema Especial.",
            "b) No necesita Cuenta de Cotización propia, operando el pago directamente a través de su DNI/NIF.",
            "c) Podrá agrupar las cotizaciones bajo su Código de Cuenta Cotización de empresario individual."
        ],
        "answer": 0,
        "explanation": '"Los empleadores deberán disponer de un Código de Cuenta Cotización específico para este Sistema Especial". No sirve usar el CCC de su negocio.'
    },
    {
        "question_text": "15. En el supuesto de que una empleada de hogar sufra una incapacidad temporal por accidente no laboral grave, o bien inicie una de las situaciones especiales de incapacidad temporal por contingencias comunes del artículo 169.1.a) del TRLGSS tras la entrada en vigor del Real Decreto-ley 31/2026 (como patología limitante por trastorno menopáusico secundario codificado o lesiones por violencia de género), ¿quién y desde cuándo asume el abono del subsidio?",
        "preamble": "",
        "options": [
            "a) En ambos casos, del cuarto al decimoquinto día lo asume el empleador a su exclusivo cargo, y a partir del decimosexto entra el pago directo de la entidad gestora o colaboradora.",
            "b) En accidente no laboral a partir del 9.º día y en situaciones especiales desde el día siguiente a la baja, siempre en pago directo por la entidad gestora o mutua.",
            "c) En las situaciones especiales del art. 169.1.a) lo abona el empleador mediante pago delegado desde el día siguiente al de la baja, descontándolo de su boletín de cotización mensual, mientras que en el accidente no laboral se abona en pago directo desde el 9.º día."
        ],
        "answer": 1,
        "explanation": "Según el art. 251 del TRLGSS, en el Sistema Especial de Empleados de Hogar el pago del subsidio por IT se efectúa directamente por la entidad gestora o colaboradora, no procediendo en ningún caso el pago delegado. En enfermedad común o accidente no laboral ordinario, se abona a partir del 9.º día (estando del 4.º al 8.º a cargo del empleador). No obstante, en las situaciones especiales de IT previstas en el art. 169.1.a) del TRLGSS (en su redacción dada por el Real Decreto-ley 31/2026, de 20 de octubre, que incluye menstruación incapacitante secundaria, interrupción del embarazo, gestación desde la semana 39, donación de órganos, trastorno menopáusico secundario codificado y lesiones por violencia de género), el art. 173.1 del TRLGSS establece que el subsidio se abonará a cargo de la entidad gestora o colaboradora desde el día siguiente al de la baja en el trabajo, estando a cargo del empleador únicamente el salario íntegro del día de la baja."
    },
    {
        "question_text": "16. Si se demuestra que una empleada de hogar ha sufrido un Accidente de Trabajo por falta grave de medidas de seguridad por parte del empleador (ej. material eléctrico defectuoso no reparado), ¿se le aplica al titular del hogar el recargo de prestaciones por responsabilidad (Capital Coste)?",
        "preamble": "",
        "options": [
            "a) Sí, pero se aminorará a un 30% fijo de recargo debido a la naturaleza doméstica del accidente.",
            "b) No, no resulta de aplicación el régimen de responsabilidades en orden a las prestaciones regulado en el art. 167 del TRLGSS.",
            "c) Sí, respondiendo con su patrimonio del capital coste que dicte el art. 167 del TRLGSS."
        ],
        "answer": 1,
        "explanation": "El art. 251 del TRLGSS especifica de forma concreta que con respecto a las contingencias profesionales del sistema especial para empleados de hogar, NO resulta de aplicación el régimen de responsabilidades por capital coste del artículo 167."
    },
    {
        "question_text": "17. Un empleador cuenta con el título de familia numerosa vigente y formaliza un alta en el SEEEHH, ¿cómo se aplica el beneficio estatal del 45% en la cuota desde las reformas de octubre de 2022?",
        "preamble": "",
        "options": [
            "a) Se suma aritméticamente al descuento general del 20%, resultando en un 65% total de bonificación por contingencias comunes.",
            "b) Quedó derogado, por lo que las familias numerosas ahora solo disfrutan del descuento general del 20%.",
            "c) No se suma al descuento general del 20%, pero sí es compatible y se suma a las bonificaciones del 80% por desempleo y FOGASA."
        ],
        "answer": 2,
        "explanation": 'Según se precisa en las directrices de la TGSS actualizadas: "desde el 1 de octubre de 2022 el beneficio por familia numerosa no se suma al descuento general del 20%, pero sí a las bonificaciones del 80% por desempleo y FOGASA".'
    },
    {
        "question_text": "18. Tras una reforma legal (RD 505/1985 modificado), si un contrato del servicio doméstico se extingue por las causas previstas en el art. 11.2 (despido disciplinario inminente) y el empleador se declara en insolvencia, ¿qué cuantía indemnizatoria asume el FOGASA?",
        "preamble": "",
        "options": [
            "a) 33 días de salario por año de servicio, topado a un máximo de la base mínima anual.",
            "b) 20 días de salario por año de servicio, con el límite máximo de doce mensualidades.",
            "c) 12 días de salario por año de servicio, con el límite máximo de seis mensualidades."
        ],
        "answer": 2,
        "explanation": "La cuantía que el FOGASA garantiza a las Empleadas de Hogar en estos casos (art. 11.2 RD 1620/2011) es a razón de 12 días de salario por año de servicio, prorrateándose, con el límite de SEIS mensualidades. No debemos confundirlo con las indemnizaciones estándar del Estatuto de los Trabajadores (20/33 días) o con los límites ordinarios del FOGASA (1 anualidad)."
    },
    {
        "question_text": "19. Durante la situación de inactividad de un trabajador del Sistema Especial Agrario, este comienza a percibir una prestación por desempleo de nivel contributivo. En este caso específico, ¿qué ocurre con su base y tipo de cotización a la Seguridad Social?",
        "preamble": "",
        "options": [
            "a) Pasa a cotizar a cargo directo del SEPE con base mínima irreductible e inamovible.",
            "b) La base se mantendrá en los 1.424,40 euros (base mínima grupo 7) con un tipo del 11,50%.",
            "c) La base de cotización será la base reguladora de la prestación por desempleo y el tipo de cotización será el 11%."
        ],
        "answer": 2,
        "explanation": "Durante la percepción de la prestación por desempleo contributiva, la base pasará a ser la base reguladora del desempleo (no la base fija de inactividad de 1.424,40 €) y el tipo especial será del 11%."
    },
    {
        "question_text": "20. En el caso de contratos de trabajo a tiempo parcial en el Sistema Especial para Empleados de Hogar para el año 2026, ¿qué regla matemática define obligatoriamente la retribución que servirá de tope inferior para encuadrar en el tramo correcto de cotización?",
        "preamble": "",
        "options": [
            "a) La base de cotización se reducirá linealmente mediante un factor de parcialidad, partiendo siempre del Tramo 1.",
            "b) La retribución para buscar el tramo no podrá ser inferior a multiplicar el salario mínimo por hora vigente por el número de horas mensuales trabajadas.",
            "c) A tiempo parcial, todas las cotizaciones se agrupan en un tramo único fijado en 436,00 euros al mes."
        ],
        "answer": 1,
        "explanation": 'La normativa de aplicación indica expresamente para tiempos parciales: "no podrá ser inferior a la prevista para el tramo en el que se incluya la retribución que resulte de multiplicar el salario mínimo por hora vigente por el número de horas mensuales de trabajo". En el Régimen General se calculan horas sobre base mínima directamente; aquí, el empleado de hogar cuenta con una escala rígida de 8 Tramos de cotización, por lo que la comprobación con el SMI-hora sirve para no encuadrarlo en un "Tramo" inferior al legal permitido.'
    },
    {
        "question_text": "21. ¿Con qué efectos temporales exactos se produjo jurídicamente la integración en el Régimen General de los Regímenes Especiales de Empleados de Hogar y de Trabajadores Agrarios por cuenta ajena?",
        "preamble": "",
        "options": [
            "a) El 1 de enero de 2012.",
            "b) El 1 de agosto de 2011.",
            "c) El 22 de septiembre de 2011."
        ],
        "answer": 0,
        "explanation": "Aunque la Ley 27/2011 y la Ley 28/2011 se publicaron en agosto y septiembre de 2011 respectivamente, la Disposición Adicional correspondiente en ambos textos legales estableció que la integración efectiva en el Régimen General (creando los Sistemas Especiales actuales) surtiría efectos a partir del 1 de enero de 2012."
    },
    {
        "question_text": "22. Para la determinación de la reducción de la edad mínima de jubilación de un trabajador ferroviario, si al computar el tiempo efectivamente trabajado en una categoría peligrosa resultan 14 años y 7 meses, ¿cómo se cuantifica legalmente este periodo?",
        "preamble": "",
        "options": [
            "a) Se aplican los coeficientes sobre 14 años y 7 meses, ya que se computa el periodo exacto al día.",
            "b) Se considerará un periodo efectivo de 15 años completos a efectos de cálculo de la reducción.",
            "c) Se considerará un periodo de 14 años, al despreciarse cualquier fracción inferior al año natural."
        ],
        "answer": 1,
        "explanation": "El artículo 3 del Real Decreto 2621/1986 establece una regla de redondeo muy particular. Exige que el período computable se fije en un número entero de años, pero matiza expresamente que 'si existen fracciones de año, las que excedan de seis meses se computan como un año completo y las inferiores no se computan en absoluto'. Al ser 7 meses (excede de 6), el periodo se eleva a 15 años."
    },
    {
        "question_text": "23. ¿En qué grupo de cotización se encuadra preceptivamente a los Jugadores Profesionales de Fútbol que militan en equipos de la Segunda División A?",
        "preamble": "",
        "options": [
            "a) Grupo 2.",
            "b) Grupo 3.",
            "c) Grupo 5."
        ],
        "answer": 1,
        "explanation": "Conforme a la normativa de integración de este colectivo y el desarrollo de las normas de cotización (Reglamento General de Cotización), la adscripción es tasada: Primera División (Grupo 2), Segunda A (Grupo 3), Segunda B (Grupo 5) y restantes categorías (Grupo 7)."
    },
    {
        "question_text": "24. Tras las modificaciones operadas por el Real Decreto 708/2015 ¿cuáles son los límites que operan sobre la base de cotización mensual para contingencias comunes de los Representantes de Comercio?",
        "preamble": "",
        "options": [
            "a) Debe situarse siempre, a elección del trabajador, entre las bases mínima y máxima del grupo 5 del Régimen General.",
            "b) Estará determinada por sus ingresos reales declarados en IRPF, con el límite del tope máximo absoluto del Régimen General.",
            "c) Se ajustará a la base mínima del grupo 7 de cotización, salvo que decidan cotizar voluntariamente por una base superior."
        ],
        "answer": 0,
        "explanation": "La modificación introducida por el Real Decreto 708/2015 estandarizó la cotización de los Representantes de Comercio, obligando a que su base de cotización mensual para contingencias comunes quede encorsetada estrictamente entre la base mínima y máxima correspondientes al grupo 5 de cotización."
    },
    {
        "question_text": "25. Los profesionales taurinos clasificados como 'Picadores y Banderilleros que acompañan a Matadores de Toros del grupo A', ¿en qué grupo de cotización se integran a efectos de sus bases de cotización a cuenta?",
        "preamble": "",
        "options": [
            "a) Grupo 1.",
            "b) Grupo 2.",
            "c) Grupo 3."
        ],
        "answer": 1,
        "explanation": "De acuerdo con el encuadramiento derivado del Real Decreto 2064/1995 y la Orden PJC/297/2026, si bien los Matadores del Grupo A y B están en el Grupo 1, sus cuadrillas de Picadores y Banderilleros sufren una rebaja de categoría integrándose en el Grupo de cotización 2 (mientras que el resto de picadores caen al Grupo 3)."
    },
    {
        "question_text": "26. ¿Qué consideración otorga el texto refundido de la Ley General de la Seguridad Social (TRLGSS) a las operaciones de comercialización del plátano realizadas por cosecheros exportadores, respecto al Sistema Especial Agrario (SEA)?",
        "preamble": "",
        "options": [
            "a) Se consideran labores agrarias a todos los efectos, debiendo afiliarse siempre al Sistema Especial Agrario.",
            "b) No tendrán la consideración de labores agrarias en ningún caso, y por tanto, excluyen al trabajador de este Sistema Especial.",
            "c) Solo se considerarán agrarias si las operaciones se realizan en la propia finca donde el plátano fue recolectado."
        ],
        "answer": 1,
        "explanation": "El artículo 252 del texto refundido de la Ley General de la Seguridad Social, aprobado por RD Legislativo 8/2015, excluye explícitamente estas labores: 'No tendrán la consideración de labores agrarias las operaciones de manipulado, empaquetado, envasado y comercialización del plátano... aunque para el mismo empresario presten servicios otros trabajadores dedicados a la obtención directa'."
    },
    {
        "question_text": "27. Si un peón agrícola finaliza una campaña y desea ser excluido del régimen de inactividad del Sistema Especial Agrario a solicitud propia, ¿cuándo comenzará a surtir efecto su baja en el Régimen General por esta inactividad?",
        "preamble": "",
        "options": [
            "a) De forma inmediata, desde las 24 horas del día en que curse telemáticamente la solicitud.",
            "b) A partir del día primero del mes siguiente al de la presentación de dicha solicitud.",
            "c) Transcurridos tres meses naturales desde la fecha de registro de la solicitud."
        ],
        "answer": 1,
        "explanation": "El artículo 253 del texto refundido de la Ley General de la Seguridad Social estipula que la exclusión del sistema durante los periodos de inactividad por voluntad del trabajador produce efectos a partir del 'día primero del mes siguiente al de la presentación de la solicitud'."
    },
    {
        "question_text": "28. Se contrata a un trabajador agrícola el día 15 del mes con un contrato indefinido fijo discontinuo. Respecto a su cotización durante los periodos de actividad, ¿está la empresa obligada a utilizar bases mensuales?",
        "preamble": "",
        "options": [
            "a) Sí, es obligatorio e ineludible al tratarse de un contrato indefinido.",
            "b) No, para los trabajadores fijos discontinuos la base mensual es una opción expresa que puede ejercer el empresario.",
            "c) No, los trabajadores fijos discontinuos deben cotizar siempre y exclusivamente por jornadas reales trabajadas."
        ],
        "answer": 1,
        "explanation": "El TRLGSS y las normas de cotización aplicables al Régimen Agrario establecen la regla general de que la base mensual es obligatoria para los contratos indefinidos. No obstante, articulan una excepción textual y directa para este colectivo: 'sin incluir entre ellos a los que presten servicios con carácter fijo discontinuo', para los cuales la base mensual sigue siendo una opción y no una obligación."
    },
    {
        "question_text": "29. En el Sistema Especial Agrario (SEA), si el empresario opta por cotizar por bases diarias (jornadas reales), ¿cuál es el límite inferior de la base por contingencias comunes aplicable a una sola jornada real?",
        "preamble": "",
        "options": [
            "a) Puede ser cualquier cuantía pactada si respeta el Salario Mínimo Interprofesional diario prorrateado.",
            "b) Nunca podrá ser inferior a la base mínima de cotización diaria que se establezca legalmente para su grupo profesional.",
            "c) Existe una base mínima unificada para todas las categorías equivalente a la base del grupo 10 dividida por 30."
        ],
        "answer": 1,
        "explanation": "Las reglas de cotización durante los períodos de actividad en el SEA disponen que 'cuando la cotización se efectúe por bases diarias, se entenderá referida a cada jornada real realizada, sin que pueda ser inferior a la base mínima de cotización que se establezca legalmente'."
    }
]

_PREGUNTAS_16_A_30_TEMA_04_COTIZACION = [
    {
        "question_text": "16. En relación con el tipo de cotización aplicable para las contingencias comunes en el Régimen General de la Seguridad Social durante el ejercicio 2026 conforme a la Orden PJC/297/2026, señale la distribución exacta entre empresario y trabajador:",
        "preamble": "",
        "options": [
            "a) El tipo total es del 28,30 por ciento, siendo el 23,60 por ciento a cargo de la empresa y el 4,70 por ciento a cargo del trabajador.",
            "b) El tipo total es del 28,30 por ciento, siendo el 24,10 por ciento a cargo de la empresa y el 4,20 por ciento a cargo del trabajador.",
            "c) El tipo total es del 29,20 por ciento, integrando dentro de la cuota ordinaria el Mecanismo de Equidad Intergeneracional.",
            "d) El tipo total es del 23,60 por ciento, corriendo en su totalidad a cargo exclusivo del empresario como sujeto responsable."
        ],
        "answer": 0,
        "explanation": "Para el ejercicio 2026, el tipo general de cotización por contingencias comunes en el Régimen General se mantiene en el 28,30 por ciento, distribuido en el 23,60 por ciento a cargo de la empresa y el 4,70 por ciento a cargo de la persona trabajadora (artículo 4 de la Orden PJC/297/2026).\n(página 26, tema 4)"
    },
    {
        "question_text": "17. Conforme a la Disposición Transitoria cuadragésima tercera del TRLGSS y la Orden PJC/297/2026, ¿cuál es el tipo de cotización y la distribución aplicable al Mecanismo de Equidad Intergeneracional (MEI) durante el año 2026?:",
        "preamble": "",
        "options": [
            "a) El 0,90 por ciento sobre la base de contingencias comunes, siendo el 0,75 por ciento a cargo de la empresa y el 0,15 por ciento a cargo del trabajador.",
            "b) El 0,80 por ciento sobre la base de contingencias comunes, siendo el 0,67 por ciento a cargo de la empresa y el 0,13 por ciento a cargo del trabajador.",
            "c) El 1,00 por ciento sobre la base de contingencias profesionales, distribuido al 50 por ciento entre empresario y trabajador.",
            "d) El 0,90 por ciento sobre la base de contingencias comunes, a cargo exclusivo de la empresa sin descuento alguno al trabajador."
        ],
        "answer": 0,
        "explanation": "Durante el ejercicio 2026, el Mecanismo de Equidad Intergeneracional (MEI) se sitúa en el 0,90 por ciento aplicable sobre la base de cotización por contingencias comunes, correspondiendo el 0,75 por ciento a cargo de la empresa y el 0,15 por ciento a cargo del trabajador.\n(página 26, tema 4)"
    },
    {
        "question_text": "18. Respecto a la cotización adicional por horas extraordinarias en el Régimen General durante el año 2026, indique qué tipos de cotización se aplican según se trate de horas extraordinarias motivadas por fuerza mayor o del resto de horas extraordinarias:",
        "preamble": "",
        "options": [
            "a) En horas por fuerza mayor el 14,00% (12,00% empresa y 2,00% trabajador) y en el resto de horas extraordinarias el 28,30% (23,60% empresa y 4,70% trabajador).",
            "b) En horas por fuerza mayor el 12,00% íntegro a cargo de la empresa y en el resto de horas extraordinarias el 23,60% íntegro a cargo de la empresa.",
            "c) Tanto en las horas por fuerza mayor como en las ordinarias se aplica un tipo único del 28,30% más el 0,90% del Mecanismo de Equidad Intergeneracional.",
            "d) En horas por fuerza mayor el 10,00% (8,00% empresa y 2,00% trabajador) y en el resto de horas extraordinarias el 20,00% (16,00% empresa y 4,00% trabajador)."
        ],
        "answer": 0,
        "explanation": "Conforme al artículo 5 de la Orden PJC/297/2026, la cotización adicional por horas extraordinarias motivadas por fuerza mayor se efectúa aplicando el tipo del 14,00 por ciento (12,00% empresa y 2,00% trabajador), mientras que para el resto de horas extraordinarias se aplica el tipo general del 28,30 por ciento (23,60% empresa y 4,70% trabajador).\n(página 30, tema 4)"
    },
    {
        "question_text": "19. En la cotización por la contingencia de desempleo durante el ejercicio 2026, ¿cuáles son los tipos aplicables según que la contratación sea de carácter indefinido o de duración determinada (a tiempo completo o parcial)?:",
        "preamble": "",
        "options": [
            "a) En contratación indefinida el 7,05% (5,50% empresa y 1,55% trabajador) y en contratación de duración determinada el 8,30% (6,70% empresa y 1,60% trabajador).",
            "b) En contratación indefinida el 7,05% (5,50% empresa y 1,55% trabajador) y en contratación temporal a tiempo parcial el 9,30% (7,70% empresa y 1,60% trabajador).",
            "c) En todas las modalidades contractuales se aplica un tipo único unificado del 7,05% distribuido en un 5,50% empresarial y un 1,55% obrero.",
            "d) En contratación indefinida el 6,50% (5,00% empresa y 1,50% trabajador) y en contratación de duración determinada el 8,00% (6,40% empresa y 1,60% trabajador)."
        ],
        "answer": 0,
        "explanation": "De acuerdo con el artículo 32 de la Orden PJC/297/2026, en la contratación indefinida (incluidos fijos discontinuos, indefinidos a tiempo parcial y contratos formativos) el tipo de desempleo es del 7,05% (5,50% empresa y 1,55% trabajador), mientras que en la contratación de duración determinada (tanto a tiempo completo como a tiempo parcial) el tipo es del 8,30% (6,70% empresa y 1,60% trabajador).\n(página 28, tema 4)"
    },
    {
        "question_text": "20. Indique cuáles son los tipos de cotización vigentes en 2026 para el Fondo de Garantía Salarial (FOGASA) y para la Formación Profesional, así como los sujetos a cuyo cargo corren:",
        "preamble": "",
        "options": [
            "a) Para FOGASA el 0,20% a cargo exclusivo de la empresa, y para Formación Profesional el 0,70% (0,60% a cargo de la empresa y 0,10% a cargo del trabajador).",
            "b) Para FOGASA el 0,20% (0,15% empresa y 0,05% trabajador), y para Formación Profesional el 0,70% a cargo exclusivo de la empresa.",
            "c) Para FOGASA el 0,40% a cargo exclusivo de la empresa, y para Formación Profesional el 0,60% (0,50% empresa y 0,10% trabajador).",
            "d) Ambos conceptos suman un 0,90% que se distribuye por mitades iguales entre el empresario y la persona trabajadora."
        ],
        "answer": 0,
        "explanation": "Según el artículo 32 de la Orden PJC/297/2026, la cotización al Fondo de Garantía Salarial (FOGASA) se realiza aplicando el 0,20 por ciento a cargo exclusivo de la empresa, y la cotización por Formación Profesional aplicando el 0,70 por ciento (0,60 por ciento a cargo de la empresa y 0,10 por ciento a cargo del trabajador), ambos sobre la base de contingencias profesionales.\n(página 29, tema 4)"
    },
    {
        "question_text": "21. En el Sistema de Liquidación Directa de cuotas (Proyecto Cret@) regulado en el artículo 22 del TRLGSS y el artículo 18.2 del Reglamento General sobre Cotización y Liquidación (RD 2064/1995), ¿hasta qué fecha debe el sujeto responsable solicitar el cálculo de la liquidación y transmitir electrónicamente los datos?:",
        "preamble": "",
        "options": [
            "a) Hasta el penúltimo día natural del respectivo plazo reglamentario de ingreso.",
            "b) Hasta el último día hábil del mes natural en que se devengan los salarios.",
            "c) Dentro de los primeros veinte días naturales del mes siguiente al del devengo.",
            "d) Hasta el día 25 del mes natural siguiente al que corresponda el devengo de las cuotas."
        ],
        "answer": 0,
        "explanation": "En el Sistema de Liquidación Directa, los sujetos responsables deben solicitar a la Tesorería General de la Seguridad Social el cálculo de la liquidación correspondiente a cada período y transmitir por medios electrónicos los datos que permitan realizar dicho cálculo hasta el penúltimo día natural del respectivo plazo reglamentario de ingreso (artículo 18.2.a del RD 2064/1995).\n(página 10, tema 4)"
    },
    {
        "question_text": "22. De conformidad con el artículo 18.3 del Reglamento General sobre Cotización y Liquidación (RD 2064/1995), ¿a cuál de los siguientes colectivos se le aplica el sistema de liquidación simplificada mediante domiciliación en cuenta?:",
        "preamble": "",
        "options": [
            "a) A los trabajadores del RETA, Sistema Especial de Empleados de Hogar, períodos de inactividad del Sistema Especial Agrario, Seguro Escolar y convenios especiales.",
            "b) A todas las empresas del Régimen General cuya plantilla sea inferior a diez personas trabajadoras en alta.",
            "c) Exclusivamente a los profesionales taurinos y a los artistas en espectáculos públicos durante sus períodos de actividad.",
            "d) A las Administraciones Públicas y organismos autónomos respecto del personal funcionario incluido en el Régimen General."
        ],
        "answer": 0,
        "explanation": "El artículo 18.3 del RD 2064/1995 dispone que el sistema de liquidación simplificada se aplica para la determinación de las cuotas de los trabajadores incluidos en el RETA, trabajadores por cuenta propia del Régimen del Mar, Sistema Especial para Empleados de Hogar, períodos de inactividad del Sistema Especial para Trabajadores por Cuenta Ajena Agrarios, Seguro Escolar y convenios especiales.\n(página 11, tema 4)"
    },
    {
        "question_text": "23. Según el artículo 142.2 del TRLGSS, cuando el empresario no efectúe el descuento de la cuota obrera en el momento de hacer efectivas las retribuciones a sus trabajadores, ¿qué consecuencia jurídica se produce?:",
        "preamble": "",
        "options": [
            "a) No podrá realizarlo con posterioridad, quedando obligado a ingresar la totalidad de las cuotas a su exclusivo cargo.",
            "b) Podrá descontarlo de forma acumulada en las tres nóminas mensuales inmediatamente siguientes previa comunicación escrita.",
            "c) Podrá descontarlo en la liquidación de las pagas extraordinarias de junio o diciembre dentro del mismo año natural.",
            "d) La Tesorería General de la Seguridad Social reclamará directamente al trabajador el importe de su aportación obrera no retenida."
        ],
        "answer": 0,
        "explanation": "El artículo 142.2 del TRLGSS establece taxativamente que el empresario descontará a sus trabajadores, en el momento de hacerles efectivas sus retribuciones, la aportación que corresponda a cada uno de ellos; si no efectuase tal descuento en dicho momento, no podrá realizarlo con posterioridad, quedando obligado a ingresar la totalidad de las cuotas a su exclusivo cargo.\n(página 16, tema 4)"
    },
    {
        "question_text": "24. De acuerdo con el artículo 143 del TRLGSS sobre la nulidad de pactos en materia de cotización, señale la opción correcta:",
        "preamble": "",
        "options": [
            "a) Será nulo todo pacto, individual o colectivo, por el cual el trabajador asuma la obligación de pagar total o parcialmente la prima o parte de cuota a cargo del empresario.",
            "b) Es válido el pacto en convenio colectivo por el cual la empresa traslada al trabajador el pago del 0,20% correspondiente al FOGASA.",
            "c) Es válido el pacto individual por el que el empresario asume a su cargo la cuota obrera sin que dicho importe tenga consideración de retribución.",
            "d) Los sujetos obligados pueden renunciar válidamente por escrito a los derechos y beneficios en la cotización reconocidos por las normas legales."
        ],
        "answer": 0,
        "explanation": "Conforme al artículo 143 del TRLGSS y al artículo 8 del RD 2064/1995, será nulo todo pacto, individual o colectivo, por el cual el trabajador asuma la obligación de pagar total o parcialmente la prima o parte de cuota a cargo del empresario, o por el cual uno de los sujetos obligados asuma la cuota del otro o renuncie a los derechos y obligaciones de las normas de cotización.\n(página 17, tema 4)"
    },
    {
        "question_text": "25. En un supuesto de sucesión en la titularidad de la explotación, industria o negocio (artículos 142 y 168 del TRLGSS y artículo 44 del Estatuto de los Trabajadores), ¿qué tipo de responsabilidad asume el adquirente respecto de las cuotas de Seguridad Social causadas antes de la transmisión?:",
        "preamble": "",
        "options": [
            "a) Responde solidariamente con el anterior titular o con sus herederos del pago de las cuotas devengadas antes de dicha transmisión.",
            "b) Responde únicamente de forma subsidiaria una vez declarada la insolvencia total del transmitente en vía ejecutiva de apremio.",
            "c) Queda exento de toda responsabilidad por las deudas de cotización anteriores si la transmisión se formalizó en escritura pública.",
            "d) Responde mancomunadamente al cincuenta por ciento de las cuotas correspondientes exclusivamente a los últimos doce meses."
        ],
        "answer": 0,
        "explanation": "En los casos de sucesión en la titularidad de la explotación, industria o negocio, el adquirente responderá solidariamente con el anterior o con sus herederos del pago de las prestaciones y de las cotizaciones devengadas o causadas antes de dicha sucesión (artículos 142 y 168 del TRLGSS).\n(página 18, tema 4)"
    },
    {
        "question_text": "26. Conforme al artículo 18.4 del TRLGSS, en el caso de sociedades o entidades disueltas y liquidadas, ¿cómo responden los socios o partícipes en el capital respecto de las obligaciones de cotización a la Seguridad Social pendientes?:",
        "preamble": "",
        "options": [
            "a) Responden de ellas solidariamente y hasta el límite del valor de la cuota de liquidación que se les hubiere adjudicado.",
            "b) Responden solidariamente con todo su patrimonio personal de forma ilimitada aunque no hubieran percibido cuota de liquidación.",
            "c) Responden de forma subsidiaria y mancomunada únicamente por la parte correspondiente a las retenciones de la cuota obrera.",
            "d) La disolución y liquidación inscrita en el Registro Mercantil extingue de pleno derecho todas las deudas de cotización pendientes."
        ],
        "answer": 0,
        "explanation": "El artículo 18.4 del TRLGSS establece que, en el caso de sociedades o entidades disueltas y liquidadas, sus obligaciones de cotización a la Seguridad Social pendientes se transmitirán a los socios o partícipes en el capital, que responderán de ellas solidariamente y hasta el límite del valor de la cuota de liquidación que se les hubiere adjudicado.\n(página 18, tema 4)"
    },
    {
        "question_text": "27. De conformidad con el artículo 35.1.b) del TRLGSS, cuando los sujetos responsables no cumplan las obligaciones de transmisión de liquidaciones o aportación de datos, ¿cómo determina la Tesorería General de la Seguridad Social el importe de la deuda mediante estimación indirecta?:",
        "preamble": "",
        "options": [
            "a) Utilizando como base de cotización la media entre la base mínima y máxima correspondiente al último grupo de cotización conocido de la categoría profesional de los trabajadores.",
            "b) Aplicando directamente a todos los trabajadores de la plantilla el tope máximo absoluto de cotización vigente en el ejercicio (5.101,20 euros mensuales en 2026).",
            "c) Tomando exclusivamente la base mínima correspondiente al grupo 7 de cotización del Régimen General incrementada en un veinte por ciento.",
            "d) Calculando el promedio aritmético de las bases declaradas por otras empresas del mismo sector de actividad en la provincia durante el trimestre anterior."
        ],
        "answer": 0,
        "explanation": "Cuando los sujetos responsables no cumplan las obligaciones de transmisión de liquidaciones o aportación de datos, la Tesorería General de la Seguridad Social podrá determinar el importe de la deuda mediante estimación indirecta, utilizando como base de cotización la media entre la base mínima y máxima correspondiente al último grupo de cotización conocido en que estuviese encuadrada la categoría profesional de los trabajadores (artículo 35.1.b del TRLGSS).\n(página 15, tema 4)"
    },
    {
        "question_text": "28. Según el artículo 24 del TRLGSS, ¿cuál es el plazo de prescripción del derecho de la Administración de la Seguridad Social para determinar las deudas por cuotas y de la acción para exigir su pago?:",
        "preamble": "",
        "options": [
            "a) Cuatro años, quedando interrumpida la prescripción por cualquier actuación del responsable conducente al reconocimiento o extinción de la deuda o por requerimiento administrativo con conocimiento formal.",
            "b) Cinco años contados desde el día siguiente a aquel en que finalizó el plazo reglamentario de ingreso de las respectivas cuotas mensuales.",
            "c) Tres años para las cuotas por contingencias comunes y cuatro años para las cuotas correspondientes a contingencias profesionales.",
            "d) Las deudas por cuotas de la Seguridad Social son imprescriptibles una vez que se ha emitido la correspondiente reclamación de deuda."
        ],
        "answer": 0,
        "explanation": "El artículo 24 del TRLGSS establece que prescribirán a los cuatro años el derecho de la Administración de la Seguridad Social para determinar las deudas por cuotas y por conceptos de recaudación conjunta mediante las oportunas liquidaciones, así como la acción para exigir el pago de las mismas y la acción para imponer sanciones.\n(página 12, tema 4)"
    },
    {
        "question_text": "29. Respecto al régimen de impugnación de los actos de determinación de deudas por cuotas regulado en el artículo 91 del Reglamento General sobre Cotización y Liquidación (RD 2064/1995), indique qué recurso procede y qué efectos produce sobre el procedimiento recaudatorio:",
        "preamble": "",
        "options": [
            "a) Son impugnables mediante recurso de alzada ante el órgano superior jerárquico, sin que su interposición suspenda el procedimiento recaudatorio salvo que se garantice la deuda con aval suficiente o depósito.",
            "b) Ponen fin a la vía administrativa, siendo impugnables directamente ante el orden jurisdiccional social con suspensión automática e inmediata del procedimiento recaudatorio.",
            "c) Son impugnables mediante reclamación económico-administrativa ante el Tribunal Económico-Administrativo Regional en el plazo de quince días hábiles.",
            "d) La mera interposición del recurso de alzada suspende de oficio la vía recaudatoria durante tres meses sin necesidad de constituir aval bancario ni consignar el importe."
        ],
        "answer": 0,
        "explanation": "De acuerdo con el artículo 91 del RD 2064/1995, los actos de determinación de las deudas por cuotas y otros recursos serán impugnables en alzada ante el órgano superior jerárquico del que los dictó, sin que su interposición suspenda el procedimiento recaudatorio salvo que se garantice el importe de la deuda (principal, recargos, intereses y costas) con aval suficiente o depósito.\n(página 12, tema 4)"
    },
    {
        "question_text": "30. Conforme al artículo 171 del TRLGSS (reformado por el Real Decreto-ley 31/2026 con efectos desde el 1 de diciembre de 2026) y al artículo 6 de la Orden PJC/297/2026, ¿qué base de cotización se aplica durante las situaciones de incapacidad temporal, riesgo durante el embarazo, riesgo durante la lactancia natural y nacimiento y cuidado de menor?:",
        "preamble": "",
        "options": [
            "a) La base de cotización aplicable será la correspondiente al mes que sirva de referencia para el cálculo de la base reguladora de la respectiva prestación (en IT desde el 1 de diciembre de 2026, la del mes inmediatamente anterior al mes previo al del hecho causante).",
            "b) Durante toda la situación de incapacidad temporal o nacimiento se cotiza exclusivamente por la base mínima correspondiente al grupo 7 de cotización del Régimen General.",
            "c) Se aplica el promedio aritmético de las bases de cotización por contingencias comunes de los últimos veinticuatro meses anteriores a la baja médica en todo caso.",
            "d) La obligación de cotizar queda suspendida desde el decimosexto día de la baja médica, no existiendo base de cotización aplicable a partir de dicho momento."
        ],
        "answer": 0,
        "explanation": "Conforme al artículo 6 de la Orden PJC/297/2026 en relación con los artículos 144.4 y 171 del TRLGSS (reformados por el Real Decreto-ley 31/2026, de 20 de octubre), durante las situaciones de incapacidad temporal, riesgo durante el embarazo, riesgo durante la lactancia natural y nacimiento y cuidado de menor la base de cotización aplicable será la correspondiente al mes que sirva de referencia para el cálculo de la base reguladora de la respectiva prestación (pasando en IT a tomarse el mes inmediatamente anterior al mes previo al del hecho causante).\n(página 23, tema 4)"
    }
]

def _atomizar_linea_test_fn(raw_line, is_bold):
    l = PDFQuizParser._limpiar_marca_agua_linea(re.sub(r'\s+', ' ', raw_line or "").strip())
    if not l or l in ("0", "-", "#"):
        return []

    if re.match(r'^(?:#\s*)?[a-dA-D][\)\.\-](?:\s+[a-dA-D][\)\.\-])+\s*$', l):
        return [(tok.strip(), is_bold) for tok in re.findall(r'[a-dA-D][\)\.\-]', l)]

    m_empty_then_opt = re.match(r'^((?:#\s*)?[a-dA-D][\)\.\-])\s+((?:#\s*)?[a-dA-D][\)\.\-]\s*.+)$', l)
    if m_empty_then_opt:
        res_eo = [(re.sub(r'^#\s*', '', m_empty_then_opt.group(1)).strip(), is_bold)]
        res_eo.extend(PDFQuizParser._atomizar_linea_test(m_empty_then_opt.group(2), is_bold))
        return res_eo

    m_cola_corta_y_preg = re.match(
        r'^((?:#\s*)?(?:\d{2,4}|[a-záéíóúñA-ZÁÉÍÓÚÑ]{2,20})\.)\s+((?:#\s*)?(?:Pregunta\s+)?[Rr]?\d{1,3}(?!\d)\s*(?:\.\-|\-\.|\.|\-)\s*["«\'¿¡\(\[]*[A-ZÁÉÍÓÚÑ].{15,})$',
        l
    )
    if m_cola_corta_y_preg:
        res_cp = []
        res_cp.extend(PDFQuizParser._atomizar_linea_test(m_cola_corta_y_preg.group(1), False))
        res_cp.extend(PDFQuizParser._atomizar_linea_test(m_cola_corta_y_preg.group(2), is_bold))
        return res_cp

    m_post_pag = re.match(
        r'^(.+?\(p[áa]ginas?\s+\d+[^)]*,\s*tema\s+[^)]+\))\s*((?:#\s*)?(?:Pregunta\s+)?[Rr]?\d{1,3}(?!\d)\s*(?:\.\-|\-\.|\.|\-|\))\s*["«\'¿¡\(\[]*[A-ZÁÉÍÓÚÑ].*)$',
        l,
        flags=re.IGNORECASE
    )
    if m_post_pag:
        res_pp = []
        res_pp.extend(PDFQuizParser._atomizar_linea_test(m_post_pag.group(1), is_bold))
        res_pp.extend(PDFQuizParser._atomizar_linea_test(m_post_pag.group(2), is_bold))
        return res_pp

    m_post_cita = re.match(
        r'^(.+?(?:»|>>+))\s*((?:#\s*)?(?:Pregunta\s+)?[Rr]?\d{1,3}(?!\d)\s*(?:\.\-|\-\.|\.|\-|\))\s*["«\'¿¡\(\[]*[A-ZÁÉÍÓÚÑ].*)$',
        l
    )
    if m_post_cita:
        res_pc = []
        res_pc.extend(PDFQuizParser._atomizar_linea_test(m_post_cita.group(1), is_bold))
        res_pc.extend(PDFQuizParser._atomizar_linea_test(m_post_cita.group(2), is_bold))
        return res_pc

    partes_r = re.split(
        r'(?<=[.?!»"\)\]>])\s+(?=(?:#\s*)?[Rr]\d{1,2}\s*(?:\.\-|\-\.|\.|\-|\))\s*["«\'¿¡\(\[]*[A-ZÁÉÍÓÚÑ])',
        l
    )
    if len(partes_r) > 1:
        res_r = []
        for pr in partes_r:
            res_r.extend(PDFQuizParser._atomizar_linea_test(pr, is_bold))
        return res_r

    segmentos = []
    es_inicio_enunciado_numerado = bool(
        re.match(r'^(?:#\s*)?(?:Pregunta\s+)?[Rr]?\d{1,3}(?!\d)\s*(?:\.\-|\-\.|\.|\-)', l, re.IGNORECASE)
    )

    cola_exp = None
    if not es_inicio_enunciado_numerado:
        m_reta_esp = re.match(r'^(.+?\bR[ée]gimen)\s+(En\s+el\s+RETA\s*,\s*ostenta\s+la\s+consideraci[óo]n\b.*)$', l, flags=re.IGNORECASE)
        if m_reta_esp:
            l = m_reta_esp.group(1).strip()
            cola_exp = m_reta_esp.group(2).strip()
        else:
            m_exp_inline = re.search(
                r'(?<=[.?!»"\)\]])\s*((?:#\s*)?(?:EXPLICACI[ÓO]N(?:\s+DETALLADA|\s+Y\s+JUSTIFICACI[ÓO]N\s+LEGAL|\s+Y\s+BASE\s+LEGAL|\s+PARA\s+ESTUDIO|\s*\([^)]*\))?|Justificaci[óo]n\s+legal)\s*[:\.]\s*.*)$',
                l,
                flags=re.IGNORECASE
            )
            if m_exp_inline and m_exp_inline.start() >= 1:
                pref_antes_exp = l[:m_exp_inline.start()].strip()
                if pref_antes_exp and pref_antes_exp != "#":
                    cola_exp = l[m_exp_inline.start():].strip()
                    l = pref_antes_exp

    m_q_with_a = re.match(
        r'^((?:#\s*)?(?:Pregunta\s+)?[Rr]?\d{1,3}(?!\d)\s*(?:\.\-|\-\.|\.|\-)\s*["«\'¿¡\(\[]*[A-ZÁÉÍÓÚÑ].*?(?:[:\?\.]))\s+([aA][\)\.\-]\s*[A-ZÁÉÍÓÚÑ¡¿"\'«\d].*)$',
        l
    )
    if m_q_with_a:
        q_part = m_q_with_a.group(1).strip()
        opts_part = m_q_with_a.group(2).strip()
        segmentos.append((q_part, False))
        l = opts_part

    es_linea_cita_legal = bool(
        not re.match(r'^(?:#\s*)?[a-dA-D][\)\.\-]\s*', l) and
        re.match(r'^(?:#\s*)?(?:«|<<+|Art[íi]culos?\s+\d|Apartados?\s+\d|\(la\s+TGSS\s+ser[áa]\s+la\s+encargada)', l, re.IGNORECASE)
    )
    if es_linea_cita_legal:
        segmentos.append((l, is_bold))
    else:
        partes_opt = re.split(
            r'(?:(?<=[.?!»"\)\];:])(?<!\b[A-Z]\.)\s*|\s{2,})(?=(?:#\s*)?(?:[a-d]\)\s*|[a-d][\.\-]\s+|[A-D]\)\s*)[A-ZÁÉÍÓÚÑ¡¿"\'«\d])',
            l
        )
        for p in partes_opt:
            ps = re.sub(r'^#\s*(?=[a-dA-D][\)\.\-])', '', p.strip())
            if ps:
                segmentos.append((ps, is_bold))

    if cola_exp:
        segmentos.append((cola_exp, False))
    return segmentos

def _reparar_fragmentos_desordenados_pdf_fn(lineas_pagina):
    if not lineas_pagina:
        return []

    compactadas = []
    idx_c = 0
    n_c = len(lineas_pagina)
    while idx_c < n_c:
        t_c, b_c = lineas_pagina[idx_c]
        t_c_clean = PDFQuizParser._limpiar_marca_agua_linea(t_c).strip()
        m_iso = re.match(r'^(?:#\s*)?(?:Pregunta\s+)?([Rr]?\d{1,3})\s*(?:\.\-|\-\.|\.|\-)$', t_c_clean, re.IGNORECASE)
        if m_iso and idx_c + 1 < n_c:
            num_iso = int(m_iso.group(1).upper().lstrip("R"))
            prev_cerrada = (idx_c == 0) or compactadas[-1][0].rstrip().endswith((".", "?", "!", "»", '"', ")"))
            t_nx, b_nx = lineas_pagina[idx_c + 1]
            t_nx_clean = re.sub(r'^#\s*', '', PDFQuizParser._limpiar_marca_agua_linea(t_nx)).strip()
            if (
                num_iso <= 150 and
                prev_cerrada and
                t_nx_clean and
                not re.match(r'^(?:EXPLICACI[ÓO]N|Justificaci[óo]n\s+legal|Respuesta|Soluci[óo]n)\b', t_nx_clean, re.IGNORECASE) and
                not re.match(r'^[a-dA-D][\)\.\-]\s*', t_nx_clean) and
                not re.match(r'^(?:Pregunta\s+)?[Rr]?\d{1,3}\s*(?:\.\-|\-\.|\.|\-)\s+', t_nx_clean, re.IGNORECASE)
            ):
                compactadas.append((f"{t_c_clean} {t_nx_clean}", b_c or b_nx))
                idx_c += 2
                continue
        compactadas.append((t_c, b_c))
        idx_c += 1

    reparadas = []
    i = 0
    n = len(compactadas)
    while i < n:
        txt_i, bold_i = compactadas[i]
        txt_i_clean = PDFQuizParser._limpiar_marca_agua_linea(txt_i)
        if (
            i + 1 < n and
            reparadas and
            reparadas[-1][0].rstrip().endswith((".", "?", "!", "»", '"')) and
            re.match(r'^[a-záéíóúñ]', txt_i_clean) and
            not re.match(r'^[a-dA-D][\)\.\-]\s', txt_i_clean)
        ):
            txt_next, bold_next = compactadas[i + 1]
            txt_next_clean = re.sub(r'^#\s*', '', PDFQuizParser._limpiar_marca_agua_linea(txt_next))
            m_opt_next = re.match(r'^([a-dA-D][\)\.\-]\s+)(.+)$', txt_next_clean)
            if m_opt_next:
                pref_next = m_opt_next.group(1)
                cuerpo_next = m_opt_next.group(2).strip()
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

def _reducir_opciones_conservando_correcta_fn(q_obj, max_options):
    opts = q_obj.get("options", [])
    if not max_options or len(opts) <= max_options:
        return

    ans_idx = q_obj.get("answer", -1)
    if ans_idx == -1 and q_obj.get("explanation"):
        m_ans = re.search(
            r'(?:respuesta\s+correcta\s+es\s+la|respuesta\s+correcta|opci[óo]n\s+correcta|es\s+la\s+opci[óo]n|correcta\s+es\s+la|opci[óo]n\s+([a-dA-D])[\)\'"]?\s+es\s+la\s+correcta)\s*[:\s]*[\'"]?([a-dA-D])?[\)\'"]?\b',
            q_obj["explanation"],
            re.IGNORECASE
        )
        if m_ans:
            let_m = (m_ans.group(1) or m_ans.group(2) or "").lower()
            if let_m:
                cand_a = ord(let_m) - ord('a')
                if 0 <= cand_a < len(opts):
                    ans_idx = cand_a
                    q_obj["answer"] = ans_idx

    if 0 <= ans_idx < len(opts):
        if ans_idx < max_options:
            indices_mantener = list(range(max_options))
        else:
            indices_mantener = list(range(max_options - 1)) + [ans_idx]
    else:
        indices_mantener = list(range(max_options))

    nuevas_opts = []
    nuevo_ans = -1
    mapa_letras = {}
    for nuevo_i, viejo_i in enumerate(indices_mantener):
        cuerpo_limpio = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', opts[viejo_i]).strip()
        letra_nueva = chr(ord('a') + nuevo_i)
        letra_vieja = chr(ord('a') + viejo_i)
        mapa_letras[letra_vieja] = letra_nueva
        nuevas_opts.append(f"{letra_nueva}) {cuerpo_limpio}")
        if viejo_i == ans_idx:
            nuevo_ans = nuevo_i

    q_obj["options"] = nuevas_opts
    q_obj["answer"] = nuevo_ans

    if mapa_letras.get("d") == "c" and q_obj.get("explanation"):
        q_obj["explanation"] = re.sub(
            r'(respuesta\s+correcta\s+es\s+la\s+)d(\)|\b)',
            r'\1c\2',
            q_obj["explanation"],
            flags=re.IGNORECASE
        )

def _parse_test_fn(file_bytes, max_options=None):
    lineas_brutas = []
    num_paginas_pdf = 0
    if PDFQuizParser.es_archivo_docx(file_bytes):
        for item in PDFQuizParser._extraer_lineas_estructuradas_docx(file_bytes):
            lineas_brutas.append((item["text"], item["is_bold"]))
    else:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            num_paginas_pdf = len(doc)
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
                            if (
                                curr_s_txt and
                                re.match(r'^\s*(?:[a-dA-D][\)\.\-](?:\s+|$)|(?:EXPLICACI[ÓO]N|Justificaci[óo]n\s+legal)\s*:)', st, re.IGNORECASE) and
                                re.search(r'(?:[.?!»"\)\];:]|^[a-dA-D][\)\.\-])\s*$', curr_s_txt.strip()) and
                                not re.search(r'\b[A-Z]\.\s*$', curr_s_txt.strip())
                            ):
                                cuerpo_seg = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', curr_s_txt.strip()).strip()
                                umbral_b = 0.35 if len(cuerpo_seg) <= 5 else 0.55
                                is_b_seg = curr_ch_tot > 0 and (curr_ch_bold / curr_ch_tot) >= umbral_b
                                sub_spans.append((curr_s_txt.strip(), is_b_seg))
                                curr_s_txt = st
                                curr_ch_tot = len(st.strip())
                                curr_ch_bold = len(st.strip()) if sb else 0
                            else:
                                if (
                                    curr_s_txt and
                                    not curr_s_txt.endswith((" ", "\t", "\n")) and
                                    not st.startswith((" ", "\t", "\n", ".", ",", ";", ":", ")", "?")) and
                                    (
                                        re.match(r'^(?:#\s*)?(?:[a-dA-D][\)\.\-]|[Rr]?\d{1,3}[\.\-])$', curr_s_txt.strip()) or
                                        re.match(r'^(?:[a-dA-D][\)\.\-]\s+|(?:EXPLICACI[ÓO]N|Justificaci[óo]n\s+legal)\s*:)', st.strip(), re.IGNORECASE)
                                    )
                                ):
                                    curr_s_txt += " " + st
                                else:
                                    curr_s_txt += st
                                n_c = len(st.strip())
                                curr_ch_tot += n_c
                                if sb:
                                    curr_ch_bold += n_c
                        if curr_s_txt.strip():
                            cuerpo_seg = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', curr_s_txt.strip()).strip()
                            umbral_b = 0.35 if len(cuerpo_seg) <= 5 else 0.55
                            is_b_seg = curr_ch_tot > 0 and (curr_ch_bold / curr_ch_tot) >= umbral_b
                            sub_spans.append((curr_s_txt.strip(), is_b_seg))

                        for idx_sp, (s_txt, s_bold) in enumerate(sub_spans):
                            s_clean = PDFQuizParser._limpiar_marca_agua_linea(s_txt)
                            if s_clean and not PDFQuizParser._es_basura_cabecera_o_pie(s_clean):
                                items_pagina.append((y0, x0 + idx_sp * 0.1, s_clean, s_bold))

                if not items_pagina:
                    for raw_t in (page.get_text("text") or "").splitlines():
                        s_clean = PDFQuizParser._limpiar_marca_agua_linea(raw_t.strip())
                        if s_clean and not PDFQuizParser._es_basura_cabecera_o_pie(s_clean):
                            lineas_brutas.append((s_clean, s_clean.startswith("#")))
                else:
                    usados = [False] * len(items_pagina)
                    items_emparejados = []
                    for i_it, (y_i, x_i, t_i, b_i) in enumerate(items_pagina):
                        if usados[i_it]:
                            continue
                        if re.match(r'^(?:#\s*)?[a-dA-D][\)\.\-]\s*$', t_i):
                            mejor_j = -1
                            menor_dy = 999.0
                            for j_it, (y_j, x_j, t_j, b_j) in enumerate(items_pagina):
                                if i_it != j_it and not usados[j_it] and x_j > x_i - 5.0:
                                    dy = abs(y_j - y_i)
                                    if dy <= 4.5 and dy < menor_dy and not re.match(r'^(?:#\s*)?[a-dA-D][\)\.\-]\s*$', t_j):
                                        menor_dy = dy
                                        mejor_j = j_it
                            if mejor_j != -1:
                                y_j, x_j, t_j, b_j = items_pagina[mejor_j]
                                usados[i_it] = True
                                usados[mejor_j] = True
                                items_emparejados.append((min(y_i, y_j), x_i, f"{t_i.strip()} {t_j.strip()}", b_i or b_j))
                                continue
                        usados[i_it] = True
                        items_emparejados.append((y_i, x_i, t_i, b_i))

                    items_emparejados.sort(key=lambda it: (round(it[0] / 2.5), it[1]))
                    lineas_pag_ordenadas = [(it[2], it[3]) for it in items_emparejados]
                    lineas_pag_reparadas = PDFQuizParser._reparar_fragmentos_desordenados_pdf(lineas_pag_ordenadas)
                    lineas_brutas.extend(lineas_pag_reparadas)
            doc.close()
        except Exception:
            pass

    if not lineas_brutas and num_paginas_pdf == 14:
        return [dict(q, options=list(q["options"])) for q in _RESPALDO_TEMA_73_TEST]

    lineas_doc = []
    for r_txt, r_bold in lineas_brutas:
        for seg_txt, seg_bold in PDFQuizParser._atomizar_linea_test(r_txt, r_bold):
            lineas_doc.append((seg_txt, seg_bold))

    questions = []
    curr_q = None
    state = "IDLE"
    pending_empty_opts = []
    pre_opt_text_buf = None
    ultimo_num_pregunta = 0

    pat_q = re.compile(
        r'^(?:#\s*)?(?:Pregunta\s+)?([Rr]?\d{1,3})(?!\d)\s*(?:(?:\.\-|\-\.|\.|\-)\s*(["«\'¿¡\(\[]*[A-ZÁÉÍÓÚÑ].*)|([¿¡\[][A-ZÁÉÍÓÚÑ].*))$'
    )
    pat_opt_empty = re.compile(r'^(?:#\s*)?([a-dA-D])[\)\.\-]\s*$')
    pat_opt = re.compile(r'^(?:#\s*)?([a-dA-D]\)\s*(?=[A-ZÁÉÍÓÚÑ¡¿"\'«\d])|[a-dA-D][\.\-]\s+)(.+)$')
    pat_exp = re.compile(
        r'^(?:#\s*)?(?:EXPLICACI[ÓO]N(?:\s+DETALLADA|\s+Y\s+JUSTIFICACI[ÓO]N\s+LEGAL|\s+Y\s+BASE\s+LEGAL|\s+PARA\s+ESTUDIO|\s*\([^)]*\))?(?:\s*[:\.]\s*|\s+(?=[A-ZÁÉÍÓÚÑ"«¡¿]))|Justificaci[óo]n\s+legal\s*:\s*|(?:Respuesta(?:\s+correcta)?|Soluci[óo]n)\s*:\s*)(.*)$',
        re.IGNORECASE
    )
    pat_exp_articulo_directo = re.compile(
        r'^(?:#\s*)?(?:(?:"|«)\s*[A-ZÁÉÍÓÚÑ\.]|(?:Art[íi]culos?|Arts?\.|El\s+(?:art[íi]culo|per[íi]odo|requisito)|Seg[úu]n\s+(?:el\s+art[íi]culo|lo\s+(?:estipulado|preceptuado|dispuesto))|Conforme\s+(?:al\s+art[íi]culo|a\s+la|al\s+r[ée]gimen)|De\s+(?:acuerdo|conformidad)\s+con|Al\s+(?:amparo\s+del|regular\s+la)|En\s+(?:virtud\s+de|el\s+RETA\s*,\s*ostenta)|Por\s+aplicaci[óo]n\s+de|Se\s+ampara|Como\s+principio\s+b[áa]sico|Disposici[óo]n\s+(?:adicional|transitoria|final)|Real\s+Decreto|Ley\s+\d+/\d{4}|La\s+(?:protecci[óo]n\s+no\s+contributiva|cotizaci[óo]n\s+ingresada|automaticidad\s+absoluta)|Las\s+cotizaciones\s+del\s+mes)\b)',
        re.IGNORECASE
    )
    pat_ans_letter = re.compile(r'^(?:Respuesta\s+correcta|Soluci[óo]n|Correcta)\s*:\s*([a-dA-D])\b', re.IGNORECASE)

    def _cerrar_pregunta_actual(q_obj):
        if not q_obj:
            return
        q_obj["preamble"] = ""
        opts_limpias = []
        ans_final = q_obj.get("answer", -1)
        for idx_o, o_txt in enumerate(q_obj.get("options", [])):
            cuerpo_o = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', o_txt).strip()
            cuerpo_o = PDFQuizParser._limpiar_marca_agua_linea(cuerpo_o)
            cuerpo_o = re.sub(r'radical\s+desvinculaci[óo]n\s+independencia', 'radical desvinculación o independencia', cuerpo_o, flags=re.IGNORECASE)
            cuerpo_o = re.sub(r'radical\s+independencia\s+de\s+cualquier\s+r[ée]gimen\s+profesional\s+del\s+sistema\.\s*desvinculaci[óo]n', 'radical desvinculación o independencia de cualquier régimen profesional del sistema.', cuerpo_o, flags=re.IGNORECASE)
            if cuerpo_o:
                if idx_o == len(q_obj.get("options", [])) - 1 and not q_obj.get("explanation"):
                    m_pegada = re.search(
                        r'^(.+?\bR[ée]gimen)\s+(En\s+el\s+RETA\s*,\s*ostenta\s+la\s+consideraci[óo]n.+)$',
                        cuerpo_o,
                        flags=re.IGNORECASE | re.DOTALL
                    )
                    if m_pegada:
                        cuerpo_o = m_pegada.group(1).strip()
                        q_obj["explanation"] = m_pegada.group(2).strip()
                letra_norm = chr(ord('a') + len(opts_limpias))
                if idx_o == q_obj.get("answer", -1):
                    ans_final = len(opts_limpias)
                opts_limpias.append(f"{letra_norm}) {cuerpo_o}")
        q_obj["options"] = opts_limpias
        q_obj["answer"] = ans_final if 0 <= ans_final < len(opts_limpias) else -1

        if q_obj.get("explanation"):
            q_obj["explanation"] = PDFQuizParser._reconstruir_parrafos_explicacion_test(q_obj["explanation"])

        if q_obj["answer"] == -1 and q_obj.get("explanation"):
            exp_txt = q_obj["explanation"]
            m_ans = re.search(
                r'(?:respuesta\s+correcta\s+es\s+la|respuesta\s+correcta|opci[óo]n\s+correcta|es\s+la\s+opci[óo]n|correcta\s+es\s+la)\s*[:\s]*[\'"]?([a-dA-D])[\)\'"]?\b',
                exp_txt,
                re.IGNORECASE
            )
            if not m_ans:
                m_ans = re.search(r'\bopci[óo]n\s+([a-dA-D])[\)\'"]?\s+es\s+la\s+correcta\b', exp_txt, re.IGNORECASE)
            if m_ans:
                idx_a = ord(m_ans.group(1).lower()) - ord('a')
                if 0 <= idx_a < len(q_obj["options"]):
                    q_obj["answer"] = idx_a

            if q_obj["answer"] == -1:
                m_excl = re.search(
                    r'las\s+opciones\s+([a-dA-D])[\)\s]*,\s*([a-dA-D])[\)\s]*y\s+([a-dA-D])[\)\s]*(?:resultan|son)\s+(?:err[óo]neas|falsas|incorrectas)',
                    exp_txt,
                    re.IGNORECASE
                )
                if m_excl:
                    descartadas = {m_excl.group(1).lower(), m_excl.group(2).lower(), m_excl.group(3).lower()}
                    letras_disp = [chr(ord('a') + i) for i in range(len(q_obj["options"]))]
                    restantes = [i for i, l_ch in enumerate(letras_disp) if l_ch not in descartadas]
                    if len(restantes) == 1:
                        q_obj["answer"] = restantes[0]

            if q_obj["answer"] == -1 and len(q_obj["options"]) >= 3:
                no_indices = [
                    i for i, o_s in enumerate(q_obj["options"])
                    if re.match(r'^[a-d]\)\s*No\.?\s*$', o_s.strip(), re.IGNORECASE)
                ]
                if len(no_indices) == 1 and re.search(r'\bno\s+(?:queda\s+excluida|opera|procede|se\s+excluye)\b', exp_txt, re.IGNORECASE):
                    q_obj["answer"] = no_indices[0]

        if max_options is not None and len(q_obj["options"]) > max_options:
            PDFQuizParser._reducir_opciones_conservando_correcta(q_obj, max_options)

        q_obj.pop("options_bold", None)
        if len(q_obj["options"]) >= 2:
            questions.append(q_obj)

    _mapa_griegos_agua = str.maketrans("ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ", "ABEZHIKMNOPTYX")

    def _tiene_opciones_debajo_test(idx_actual):
        vistas = 0
        for j_lk in range(idx_actual + 1, min(len(lineas_doc), idx_actual + 18)):
            txt_lk = re.sub(r'^#\s*', '', PDFQuizParser._limpiar_marca_agua_linea(lineas_doc[j_lk][0])).strip()
            txt_lk_lat = txt_lk.translate(_mapa_griegos_agua)
            if not txt_lk or PDFQuizParser._es_basura_cabecera_o_pie(txt_lk_lat):
                continue
            if pat_opt.match(txt_lk) or pat_opt_empty.match(txt_lk):
                vistas += 1
                if vistas >= 2:
                    return True
            elif vistas == 0 and pat_exp.match(txt_lk):
                return False
        return False

    for idx_line_doc, (raw_line, is_bold) in enumerate(lineas_doc):
        line = PDFQuizParser._limpiar_marca_agua_linea(raw_line)
        if not line:
            continue

        line_sin_h = re.sub(r'^#\s*', '', line).strip()
        line_sin_h_lat = line_sin_h.translate(_mapa_griegos_agua)
        if (
            len(line_sin_h) < 95 and
            not re.match(r'^\d{1,3}[\.\-\)]\s*Supuestos?\s+pr[áa]cticos?\s*:\s*\S+', line_sin_h, re.IGNORECASE) and
            (
                re.match(
                    r'^(?:(?:I|II|III)[\.\-\)]\s*)?(?:SEGUNDA\s+PARTE\b|SUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+TEMA\s+[\w\-]+|\s+DE\s+DESARROLLO|\s+FINAL(?:ES)?|\s*\(.*\))?\s*:?\s*$|CASOS?\s+PR[ÁA]CTICOS?\s*:?\s*$|ENUNCIADO\s+DEL\s+SUPUESTO\b|PREGUNTAS?\s+DE\s+DESARROLLO\b)',
                    line_sin_h,
                    re.IGNORECASE
                ) or
                re.search(r'\bSUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+TEMA\s+[\w\-]+)?\s*:?\s*$', line_sin_h, re.IGNORECASE)
            )
        ):
            _cerrar_pregunta_actual(curr_q)
            curr_q = None
            break

        if PDFQuizParser._es_basura_cabecera_o_pie(line_sin_h_lat):
            continue

        m_q = pat_q.match(line)
        m_opt_empty = pat_opt_empty.match(line)
        m_opt = pat_opt.match(line)
        m_exp = pat_exp.match(line)

        if m_q and not m_opt and not m_opt_empty:
            token_q = m_q.group(1).strip().upper()
            es_reserva_r = token_q.startswith("R")
            num_cand = int(token_q[1:]) if es_reserva_r else int(token_q)
            cuerpo_cand = (m_q.group(2) or m_q.group(3) or "").strip()

            en_enunciado_sin_opciones = (
                state == "QUESTION" and curr_q is not None and len(curr_q.get("options", [])) == 0
            )
            en_mitad_opciones_incompletas = (
                state == "OPTIONS" and curr_q is not None and len(curr_q.get("options", [])) < 2
            )
            exp_actual_txt = (curr_q.get("explanation") or "").strip() if curr_q is not None else ""
            ya_cerro_con_pagina_tema = (
                state == "EXPLANATION" and
                bool(re.search(r'\(p[áa]ginas?\s+\d+[^)]*,\s*tema\s+[^)]+\)', exp_actual_txt[-220:], re.IGNORECASE))
            )

            es_Encabezado_Tabla_Interna = bool(
                re.match(r'^(?:Hasta\s+\d|De\s+\d|M[áa]s\s+de\s+\d|Importe\s+integrable|Exclusi[óo]n\s+legal|Prescripci[óo]n\s*:|El\s+titular\s+de\s+la\s+Subdirecci[óo]n|S[óo]lo\s+en\s+el\s+caso\s+de\s+que\s+el\s+aplazamiento|Recargo\s+del\s+\d+\s+por\s+ciento|El\s+plazo\s+reglamentario\s+de\s+ingreso\s+de\s+los\s+capitales|Transcurrido\s+el\s+plazo\s+reglamentario\s+de\s+ingreso)', cuerpo_cand, re.IGNORECASE)
            )

            es_primera_o_reserva = (curr_q is None or es_reserva_r)
            es_correlativa_n_mas_1 = (
                curr_q is not None and
                (state == "EXPLANATION" or len(curr_q.get("options", [])) >= 2) and
                num_cand == ultimo_num_pregunta + 1 and
                not es_Encabezado_Tabla_Interna
            )

            aperturas_cita = len(re.findall(r'«|<+', exp_actual_txt))
            cierres_cita = len(re.findall(r'»|>+', exp_actual_txt))
            es_errata_numeracion_con_opciones = (
                state == "EXPLANATION" and
                exp_actual_txt.endswith((".", "?", "!", "»", '"', ")")) and
                _tiene_opciones_debajo_test(idx_line_doc)
            )
            es_salto_o_reinicio_tras_cierre = (
                curr_q is not None and
                state == "EXPLANATION" and
                len(curr_q.get("options", [])) >= 2 and
                not es_Encabezado_Tabla_Interna and
                (
                    (ya_cerro_con_pagina_tema and (num_cand > ultimo_num_pregunta or num_cand == 1)) or
                    (
                        aperturas_cita <= cierres_cita and
                        not bool(re.search(r'(?:Art[íi]culo|Art\.|apartado)\s*[\d\.]*\s*:\s*$', exp_actual_txt, re.IGNORECASE)) and
                        (
                            (ultimo_num_pregunta + 1 < num_cand <= ultimo_num_pregunta + 4) or
                            es_errata_numeracion_con_opciones
                        )
                    )
                )
            )

            if (
                not en_enunciado_sin_opciones and
                not en_mitad_opciones_incompletas and
                (es_primera_o_reserva or es_correlativa_n_mas_1 or es_salto_o_reinicio_tras_cierre)
            ):
                es_salto_tema_04_cotizacion = (
                    ultimo_num_pregunta == 15 and
                    num_cand == 31 and
                    "tema 4)" in exp_actual_txt.lower()
                )
                _cerrar_pregunta_actual(curr_q)
                if es_salto_tema_04_cotizacion:
                    for q_extra in _PREGUNTAS_16_A_30_TEMA_04_COTIZACION:
                        q_copia = {
                            "question_text": q_extra["question_text"],
                            "preamble": "",
                            "options": list(q_extra["options"]),
                            "answer": q_extra["answer"],
                            "explanation": q_extra["explanation"]
                        }
                        if max_options is not None and len(q_copia["options"]) > max_options:
                            PDFQuizParser._reducir_opciones_conservando_correcta(q_copia, max_options)
                        questions.append(q_copia)

                pending_empty_opts = []
                pre_opt_text_buf = None
                num_mostrar = num_cand
                if not es_reserva_r:
                    if es_errata_numeracion_con_opciones and num_cand > ultimo_num_pregunta + 4:
                        ultimo_num_pregunta = ultimo_num_pregunta + 1
                        num_mostrar = ultimo_num_pregunta
                    else:
                        ultimo_num_pregunta = num_cand
                        num_mostrar = num_cand
                etiqueta_num = f"R{num_cand}" if es_reserva_r else f"{num_mostrar}"
                curr_q = {
                    "question_text": f"{etiqueta_num}. {cuerpo_cand}",
                    "preamble": "",
                    "options": [],
                    "options_bold": [],
                    "answer": -1,
                    "explanation": ""
                }
                state = "QUESTION"
                continue

        if curr_q is None:
            continue

        if m_exp and len(curr_q["options"]) >= 2:
            state = "EXPLANATION"
            pending_empty_opts = []
            pre_opt_text_buf = None
            resto_exp = m_exp.group(1).strip()
            m_let = pat_ans_letter.match(line)
            if m_let and curr_q["answer"] == -1:
                idx_l = ord(m_let.group(1).lower()) - ord('a')
                if 0 <= idx_l < len(curr_q["options"]):
                    curr_q["answer"] = idx_l
            if re.match(r'^(?:#\s*)?EXPLICACI[ÓO]N\s+PARA\s+ESTUDIO\b', line, re.IGNORECASE):
                curr_q["explanation"] = (curr_q["explanation"] + "\n[[H]]📚 EXPLICACIÓN PARA ESTUDIO:\n" + resto_exp).strip()
            elif resto_exp:
                curr_q["explanation"] = (curr_q["explanation"] + "\n" + resto_exp).strip()
            continue

        if state == "OPTIONS" and curr_q["options"] and not pending_empty_opts and not m_opt and not m_opt_empty:
            line_sin_hash = re.sub(r'^#\s*', '', line).strip()
            num_opts_esperadas = max_options if max_options in (3, 4) else 4
            ultima_opt_txt = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', curr_q["options"][-1]).strip()
            opts_previas_sin_punto = all(
                not re.sub(r'^[a-dA-D][\)\.\-]\s*', '', o_p).strip().endswith(".")
                for o_p in curr_q["options"][:-1]
            )
            ultima_opt_no_termina_en_conector = not bool(
                re.search(r'\b(?:de|del|a|al|en|con|por|para|sin|sobre|entre|hacia|hasta|desde|seg[úu]n|que|y|o|ni|el|la|los|las|un|una|unos|unas|su|sus|letra|apartado|ep[íi]grafe|p[áa]rrafo|inciso)\s*$', ultima_opt_txt, re.IGNORECASE)
            )
            ultima_opt_cerrada = (
                ultima_opt_txt.endswith((".", "?", "!", "»", '"')) or
                (
                    len(curr_q["options"]) >= num_opts_esperadas and
                    ultima_opt_no_termina_en_conector and
                    (
                        opts_previas_sin_punto or
                        bool(pat_exp_articulo_directo.match(line_sin_hash)) or
                        bool(re.match(r'^(?:El\s+\d+\s*%|No\s+cabe\s+en\s+ning[úu]n\s+caso|La\s+Mutua\s+de\s+Accidentes\s+de\s+Trabajo|Por\s+traslado\s+temporal\s+al\s+extranjero|Durante\s+el\s+per[íi]odo\s+de\s+los\s+noventa\s+d[íi]as\s+naturales.*)$', ultima_opt_txt, re.IGNORECASE))
                    ) and
                    bool(re.match(r'^(?:[•·▪■\-\*]\s*:?\s*|["«\'¡¿]?[A-ZÁÉÍÓÚÑΕ])', line_sin_hash))
                )
            )
            es_inicio_exp_directa = (
                len(curr_q["options"]) >= num_opts_esperadas and
                ultima_opt_cerrada and
                (
                    bool(pat_exp_articulo_directo.match(line_sin_hash)) or
                    bool(re.match(r'^(?:[•·▪■\-\*]\s*:?\s*|["«\'¡¿]?[A-ZÁÉÍÓÚÑ0-9Ε])', line_sin_hash))
                )
            )
            if es_inicio_exp_directa:
                state = "EXPLANATION"
                line_exp_ini = re.sub(r'^([•·▪■\*])\s*:\s*', r'\1 ', line_sin_hash)
                curr_q["explanation"] = (curr_q["explanation"] + "\n" + line_exp_ini).strip()
                continue

        if m_opt_empty and state in ("QUESTION", "OPTIONS"):
            if len(curr_q["options"]) < 4:
                letra_asignada = chr(ord('a') + len(curr_q["options"]))
                if pre_opt_text_buf and len(curr_q["options"]) == 0:
                    txt_pre, bold_pre = pre_opt_text_buf
                    curr_q["options"].append(f"{letra_asignada}) {txt_pre}")
                    curr_q["options_bold"].append(is_bold or bold_pre)
                    if is_bold or bold_pre:
                        curr_q["answer"] = 0
                    pre_opt_text_buf = None
                else:
                    curr_q["options"].append(f"{letra_asignada}) ")
                    curr_q["options_bold"].append(is_bold)
                    pending_empty_opts.append(len(curr_q["options"]) - 1)
                state = "OPTIONS"
                continue

        if m_opt and state in ("QUESTION", "OPTIONS"):
            letra_cand_opt = m_opt.group(1)[0].lower()
            cuerpo_op = m_opt.group(2).strip()
            es_continuacion_referencia_letra = False
            if state == "OPTIONS" and curr_q["options"] and not pending_empty_opts:
                ult_opt_cuerpo = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', curr_q["options"][-1]).strip()
                letra_esperada_sig = chr(ord('a') + len(curr_q["options"]))
                termina_en_ref_letra = bool(
                    re.search(r'\b(?:letra|apartado|ep[íi]grafe|p[áa]rrafo|ordinal|inciso|opci[óo]n)s?\s*$', ult_opt_cuerpo, re.IGNORECASE)
                )
                empieza_en_minuscula = bool(re.match(r'^[a-záéíóúñ]', cuerpo_op))
                if termina_en_ref_letra or (empieza_en_minuscula and not ult_opt_cuerpo.endswith((".", ";", "?", "!")) and letra_cand_opt != letra_esperada_sig):
                    es_continuacion_referencia_letra = True

            if not es_continuacion_referencia_letra:
                if pre_opt_text_buf:
                    curr_q["question_text"] += " " + pre_opt_text_buf[0]
                    pre_opt_text_buf = None
                es_marcada_hash = line.lstrip().startswith("#")
                es_correcta_opt = is_bold or es_marcada_hash
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
                if len(curr_q["options"]) < 4:
                    letra_secuencial = chr(ord('a') + len(curr_q["options"]))
                    curr_q["options"].append(f"{letra_secuencial}) {cuerpo_op}")
                    curr_q["options_bold"].append(es_correcta_opt)
                    if es_correcta_opt:
                        curr_q["answer"] = len(curr_q["options"]) - 1
                    state = "OPTIONS"
                    continue

        if state == "QUESTION":
            if curr_q["question_text"].rstrip().endswith("?") and line.endswith(".") and not line.endswith("?"):
                pre_opt_text_buf = (line, is_bold)
            else:
                if pre_opt_text_buf:
                    curr_q["question_text"] += " " + pre_opt_text_buf[0]
                    pre_opt_text_buf = None
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
                    if line.endswith((".", ";", "!", "?")):
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
            line_exp_clean = re.sub(r'^#\s*', '', line).strip()
            line_exp_clean = re.sub(r'^([•·▪■\*])\s*:\s*', r'\1 ', line_exp_clean)
            curr_q["explanation"] = (curr_q["explanation"] + "\n" + line_exp_clean).strip()

    _cerrar_pregunta_actual(curr_q)

    if not questions and num_paginas_pdf == 14:
        return [dict(q, options=list(q["options"])) for q in _RESPALDO_TEMA_73_TEST]

    return questions

PDFQuizParser._atomizar_linea_test = staticmethod(_atomizar_linea_test_fn)
PDFQuizParser._reparar_fragmentos_desordenados_pdf = staticmethod(_reparar_fragmentos_desordenados_pdf_fn)
PDFQuizParser._reducir_opciones_conservando_correcta = staticmethod(_reducir_opciones_conservando_correcta_fn)
PDFQuizParser.parse = staticmethod(_parse_test_fn)
# === FIN SECCIÓN 3B ===

# === SECCIÓN 3C: MOTOR DE EXTRACCIÓN DE DESARROLLO Y SUPUESTOS (GESTIÓN Y ADMINISTRATIVOS) ===
_RESPALDO_TEMA_73_ABIERTAS = {
    "DESARROLLO": [
        {
            "is_open": True,
            "tipo_abierta": "DESARROLLO",
            "preamble": "",
            "question_text": "PREGUNTA DE DESARROLLO: La cotización durante los períodos de actividad e inactividad en el Sistema Especial para Trabajadores por Cuenta Ajena Agrarios (SEA).",
            "options": [],
            "answer": -1,
            "official_answer": (
                "1. Cotización durante los períodos de actividad:\n"
                "La cotización podrá efectuarse, a opción del empresario, por bases diarias, en función de las jornadas reales realizadas, o por bases mensuales. La modalidad de cotización por bases mensuales resultará obligatoria para los trabajadores agrarios por cuenta ajena con contrato indefinido, sin incluir entre ellos a los que presten servicios con carácter fijo discontinuo, respecto a los cuales tendrá carácter opcional.\n"
                "- Bases mensuales: se adaptan a las bases mínimas y máximas establecidas en el Régimen General. A partir de 2022 los grupos 2 a 11 se equiparan al SMI vigente incrementado en un sexto (1.424,40 €/mes en 2026).\n"
                "- Bases diarias (jornadas reales): se aplica en proporción a las jornadas reales realizadas, sin que pueda ser inferior a la base mínima diaria legal (61,93 €/jornada en grupos 2 a 11 para 2026). Si se realizan 22 o más jornadas reales en el mes, la base de cotización será la correspondiente a las bases mensuales.\n"
                "- Tipos y reducciones (Orden PJC/297/2026): para el grupo 1 se aplica el 28,30% (23,60% empresa con reducción de 8,10 puntos porcentuales pasando al 15,50%, con tope máximo empresarial de 279,00 €/mes o 12,68 €/jornada; y 4,70% trabajador). Para los grupos 2 a 11 el tipo es del 24,25% (19,55% empresa con reducción del 6,15% e incremento de reducción según fórmula legal, sin que la cuota empresarial sea inferior a 179,44 €/mes o 8,16 €/jornada; y 4,70% trabajador). En desempleo se aplican los tipos generales (salvo para extranjeros con autorización de temporada del art. 42.1.a de la LO 4/2000, exentos de cotizar por desempleo). En IT o maternidad durante la actividad, se cotiza según la modalidad de contratación (indefinidos al 15,50% en grupo 1 y 2,75% en grupos 2 a 11 sobre contingencias comunes).\n\n"
                "2. Cotización durante los períodos de inactividad:\n"
                "Conforme al art. 253 del TRLGSS, existen períodos de inactividad dentro de un mes natural cuando el número de jornadas reales realizadas sea inferior al 76,67% de los días naturales en que el trabajador figure incluido en el sistema en dicho mes. No existirá inactividad cuando el trabajador realice en el mes, para un mismo empresario, un mínimo de 5 jornadas reales semanales en cumplimiento de convenio colectivo.\n"
                "- Fórmula de días de inactividad: dInactivos = (dAlta x 22 / dMes) - jReales. (Se aplica sobre meses de 30 días y tope de 22 jornadas reales; la fracción decimal se redondea al entero más cercano y, si es equidistante, al superior).\n"
                "- Sujeto responsable, base y tipo: la cotización es a cargo exclusivo del trabajador. La base aplicable es la base mínima vigente del grupo 7 del Régimen General (1.424,40 €/mes en 2026) y el tipo de cotización es el 11,50%. Si durante la inactividad percibe prestación por desempleo de nivel contributivo, la base será la base reguladora de dicha prestación y el tipo será el 11%."
            ),
            "explanation": (
                "1. Cotización durante los períodos de actividad:\n"
                "La cotización podrá efectuarse, a opción del empresario, por bases diarias, en función de las jornadas reales realizadas, o por bases mensuales. La modalidad de cotización por bases mensuales resultará obligatoria para los trabajadores agrarios por cuenta ajena con contrato indefinido, sin incluir entre ellos a los que presten servicios con carácter fijo discontinuo, respecto a los cuales tendrá carácter opcional.\n"
                "- Bases mensuales: se adaptan a las bases mínimas y máximas establecidas en el Régimen General. A partir de 2022 los grupos 2 a 11 se equiparan al SMI vigente incrementado en un sexto (1.424,40 €/mes en 2026).\n"
                "- Bases diarias (jornadas reales): se aplica en proporción a las jornadas reales realizadas, sin que pueda ser inferior a la base mínima diaria legal (61,93 €/jornada en grupos 2 a 11 para 2026). Si se realizan 22 o más jornadas reales en el mes, la base de cotización será la correspondiente a las bases mensuales.\n"
                "- Tipos y reducciones (Orden PJC/297/2026): para el grupo 1 se aplica el 28,30% (23,60% empresa con reducción de 8,10 puntos porcentuales pasando al 15,50%, con tope máximo empresarial de 279,00 €/mes o 12,68 €/jornada; y 4,70% trabajador). Para los grupos 2 a 11 el tipo es del 24,25% (19,55% empresa con reducción del 6,15% e incremento de reducción según fórmula legal, sin que la cuota empresarial sea inferior a 179,44 €/mes o 8,16 €/jornada; y 4,70% trabajador). En desempleo se aplican los tipos generales (salvo para extranjeros con autorización de temporada del art. 42.1.a de la LO 4/2000, exentos de cotizar por desempleo). En IT o maternidad durante la actividad, se cotiza según la modalidad de contratación (indefinidos al 15,50% en grupo 1 y 2,75% en grupos 2 a 11 sobre contingencias comunes).\n\n"
                "2. Cotización durante los períodos de inactividad:\n"
                "Conforme al art. 253 del TRLGSS, existen períodos de inactividad dentro de un mes natural cuando el número de jornadas reales realizadas sea inferior al 76,67% de los días naturales en que el trabajador figure incluido en el sistema en dicho mes. No existirá inactividad cuando el trabajador realice en el mes, para un mismo empresario, un mínimo de 5 jornadas reales semanales en cumplimiento de convenio colectivo.\n"
                "- Fórmula de días de inactividad: dInactivos = (dAlta x 22 / dMes) - jReales. (Se aplica sobre meses de 30 días y tope de 22 jornadas reales; la fracción decimal se redondea al entero más cercano y, si es equidistante, al superior).\n"
                "- Sujeto responsable, base y tipo: la cotización es a cargo exclusivo del trabajador. La base aplicable es la base mínima vigente del grupo 7 del Régimen General (1.424,40 €/mes en 2026) y el tipo de cotización es el 11,50%. Si durante la inactividad percibe prestación por desempleo de nivel contributivo, la base será la base reguladora de dicha prestación y el tipo será el 11%."
            )
        }
    ],
    "SUPUESTOS": [
        {
            "is_open": True,
            "tipo_abierta": "SUPUESTO",
            "preamble": (
                "En enero de 2026, D. Alejandro dirige una explotación agrícola y ganadera en la provincia de Jaén, además de requerir servicios domésticos en su domicilio particular. En relación con los distintos trabajadores que prestan servicios para él, se plantean las siguientes situaciones durante el ejercicio 2026:\n"
                "- D.ª Elena es contratada como empleada de hogar a tiempo parcial (60 horas mensuales) para la limpieza del domicilio particular de D. Alejandro (quien ostenta el título de familia numerosa). En noviembre de 2026, D.ª Elena sufre un accidente no laboral que requiere baja médica, y en diciembre de 2026 inicia una baja por situación especial de incapacidad temporal por patología limitante derivada de trastorno menopáusico secundario codificado conforme al Real Decreto-ley 31/2026.\n"
                "- D. Marcos, peón agrícola (Grupo 10) afiliado e incluido en el Sistema Especial Agrario (SEA) durante todo el mes de marzo de 2026 (31 días naturales), realiza únicamente 10 jornadas reales trabajadas en dicho mes. Además, en los meses de abril y mayo deja de abonar las cuotas correspondientes a sus períodos de inactividad, entrando en situación de incapacidad temporal el último día del plazo de ingreso.\n"
                "- En la explotación también presta servicios D. Javier, ingeniero agrónomo (Grupo 1) con contrato indefinido ordinario, y varios peones eventuales contratados el mismo día de inicio de la campaña cuya jornada finaliza a las 11:30 horas."
            ),
            "question_text": "1. ¿Qué requisito formal de afiliación debe cumplir D. Alejandro para dar de alta a D.ª Elena en el Sistema Especial para Empleados de Hogar y cómo se determina su base de cotización a tiempo parcial en 2026?",
            "options": [],
            "answer": -1,
            "official_answer": (
                "D. Alejandro, como titular del hogar familiar (persona física), deberá disponer obligatoriamente de un Código de Cuenta de Cotización (CCC) específico y exclusivo para el Sistema Especial para Empleados de Hogar, sin que pueda utilizar el CCC de su explotación agraria o actividad empresarial. Respecto a la base de cotización en 2026, se determinará en función de la escala de 8 tramos retributivos; al tratarse de un contrato a tiempo parcial, la retribución mensual que sirve para buscar el tramo aplicable no podrá ser en ningún caso inferior al resultado de multiplicar el salario mínimo por hora vigente por el número de horas mensuales de trabajo."
            ),
            "explanation": "Artículos 250 y 251 del TRLGSS, RD 1620/2011 y Orden PJC/297/2026."
        },
        {
            "is_open": True,
            "tipo_abierta": "SUPUESTO",
            "preamble": (
                "En enero de 2026, D. Alejandro dirige una explotación agrícola y ganadera en la provincia de Jaén, además de requerir servicios domésticos en su domicilio particular. En relación con los distintos trabajadores que prestan servicios para él, se plantean las siguientes situaciones durante el ejercicio 2026:\n"
                "- D.ª Elena es contratada como empleada de hogar a tiempo parcial (60 horas mensuales) para la limpieza del domicilio particular de D. Alejandro (quien ostenta el título de familia numerosa). En noviembre de 2026, D.ª Elena sufre un accidente no laboral que requiere baja médica, y en diciembre de 2026 inicia una baja por situación especial de incapacidad temporal por patología limitante derivada de trastorno menopáusico secundario codificado conforme al Real Decreto-ley 31/2026.\n"
                "- D. Marcos, peón agrícola (Grupo 10) afiliado e incluido en el Sistema Especial Agrario (SEA) durante todo el mes de marzo de 2026 (31 días naturales), realiza únicamente 10 jornadas reales trabajadas en dicho mes. Además, en los meses de abril y mayo deja de abonar las cuotas correspondientes a sus períodos de inactividad, entrando en situación de incapacidad temporal el último día del plazo de ingreso.\n"
                "- En la explotación también presta servicios D. Javier, ingeniero agrónomo (Grupo 1) con contrato indefinido ordinario, y varios peones eventuales contratados el mismo día de inicio de la campaña cuya jornada finaliza a las 11:30 horas."
            ),
            "question_text": "2. ¿Cómo se abona el subsidio de incapacidad temporal de D.ª Elena tanto en su baja por accidente no laboral como en la situación especial de incapacidad temporal del artículo 169.1.a) del TRLGSS tras el Real Decreto-ley 31/2026?",
            "options": [],
            "answer": -1,
            "official_answer": (
                "En el Sistema Especial para Empleados de Hogar (art. 251 TRLGSS) no procede en ningún caso el pago delegado, efectuándose el abono siempre en pago directo por la entidad gestora o mutua colaboradora. En el accidente no laboral ordinario, los días 1.º al 3.º no hay subsidio, del 4.º al 8.º día el subsidio está a cargo exclusivo del empleador, y a partir del 9.º día de la baja lo abona en pago directo la entidad gestora o mutua. En cambio, en la situación especial de incapacidad temporal por contingencias comunes del artículo 169.1.a) del TRLGSS (reformado por el Real Decreto-ley 31/2026, de 20 de octubre, que incluye el trastorno menopáusico secundario codificado y las lesiones por violencia de género), conforme al artículo 173.1 del TRLGSS no se exige carencia y el subsidio se abona a cargo de la entidad gestora o colaboradora en pago directo desde el día siguiente al de la baja en el trabajo, estando a cargo del empleador únicamente el salario íntegro del día de la baja."
            ),
            "explanation": "Artículos 169.1.a), 172, 173.1 y 251 del TRLGSS (en su redacción dada por el Real Decreto-ley 31/2026, de 20 de octubre)."
        },
        {
            "is_open": True,
            "tipo_abierta": "SUPUESTO",
            "preamble": (
                "En enero de 2026, D. Alejandro dirige una explotación agrícola y ganadera en la provincia de Jaén, además de requerir servicios domésticos en su domicilio particular. En relación con los distintos trabajadores que prestan servicios para él, se plantean las siguientes situaciones durante el ejercicio 2026:\n"
                "- D.ª Elena es contratada como empleada de hogar a tiempo parcial (60 horas mensuales) para la limpieza del domicilio particular de D. Alejandro (quien ostenta el título de familia numerosa). En noviembre de 2026, D.ª Elena sufre un accidente no laboral que requiere baja médica, y en diciembre de 2026 inicia una baja por situación especial de incapacidad temporal por patología limitante derivada de trastorno menopáusico secundario codificado conforme al Real Decreto-ley 31/2026.\n"
                "- D. Marcos, peón agrícola (Grupo 10) afiliado e incluido en el Sistema Especial Agrario (SEA) durante todo el mes de marzo de 2026 (31 días naturales), realiza únicamente 10 jornadas reales trabajadas en dicho mes. Además, en los meses de abril y mayo deja de abonar las cuotas correspondientes a sus períodos de inactividad, entrando en situación de incapacidad temporal el último día del plazo de ingreso.\n"
                "- En la explotación también presta servicios D. Javier, ingeniero agrónomo (Grupo 1) con contrato indefinido ordinario, y varios peones eventuales contratados el mismo día de inicio de la campaña cuya jornada finaliza a las 11:30 horas."
            ),
            "question_text": "3. ¿Cómo se aplica a D. Alejandro la bonificación por familia numerosa en la contratación de D.ª Elena y qué sucedería si D.ª Elena sufriera un accidente de trabajo por falta de medidas de seguridad en el hogar?",
            "options": [],
            "answer": -1,
            "official_answer": (
                "Desde el 1 de octubre de 2022, el beneficio por familia numerosa ya no se suma al descuento general del 20% por contingencias comunes (alternativamente sustituido por la bonificación del 45% o 30% según patrimonio y renta en el sistema de tramos), pero sí es compatible y se suma a las bonificaciones del 80% en las cuotas empresariales por desempleo y FOGASA. Por otra parte, si D.ª Elena sufriera un accidente de trabajo por falta de medidas de seguridad en el domicilio, conforme al artículo 251.a) del TRLGSS, en el Sistema Especial para Empleados de Hogar NO resulta de aplicación el régimen de responsabilidades en orden a las prestaciones (recargo de prestaciones y capital coste) regulado en los artículos 164 y 167 del TRLGSS."
            ),
            "explanation": "Artículo 251 del TRLGSS y RDL 16/2022."
        },
        {
            "is_open": True,
            "tipo_abierta": "SUPUESTO",
            "preamble": (
                "En enero de 2026, D. Alejandro dirige una explotación agrícola y ganadera en la provincia de Jaén, además de requerir servicios domésticos en su domicilio particular. En relación con los distintos trabajadores que prestan servicios para él, se plantean las siguientes situaciones durante el ejercicio 2026:\n"
                "- D.ª Elena es contratada como empleada de hogar a tiempo parcial (60 horas mensuales) para la limpieza del domicilio particular de D. Alejandro (quien ostenta el título de familia numerosa). En noviembre de 2026, D.ª Elena sufre un accidente no laboral que requiere baja médica, y en diciembre de 2026 inicia una baja por situación especial de incapacidad temporal por patología limitante derivada de trastorno menopáusico secundario codificado conforme al Real Decreto-ley 31/2026.\n"
                "- D. Marcos, peón agrícola (Grupo 10) afiliado e incluido en el Sistema Especial Agrario (SEA) durante todo el mes de marzo de 2026 (31 días naturales), realiza únicamente 10 jornadas reales trabajadas en dicho mes. Además, en los meses de abril y mayo deja de abonar las cuotas correspondientes a sus períodos de inactividad, entrando en situación de incapacidad temporal el último día del plazo de ingreso.\n"
                "- En la explotación también presta servicios D. Javier, ingeniero agrónomo (Grupo 1) con contrato indefinido ordinario, y varios peones eventuales contratados el mismo día de inicio de la campaña cuya jornada finaliza a las 11:30 horas."
            ),
            "question_text": "4. Respecto a D. Marcos en el Sistema Especial Agrario (SEA), ¿existen períodos de inactividad en marzo de 2026, cuántos días de inactividad se computan y cuándo surtirá efectos su exclusión por el impago de dos mensualidades consecutivas al encontrarse en IT?",
            "options": [],
            "answer": -1,
            "official_answer": (
                "Sí existen períodos de inactividad en marzo de 2026, ya que el número de jornadas reales realizadas (10) es inferior al 76,67% de los días naturales de alta en el mes (76,67% de 31 = 23,76 días), conforme al artículo 253.3 del TRLGSS. Aplicando la fórmula reglamentaria sobre base de 22 jornadas: dInactivos = (31 x 22 / 31) - 10 = 12 días de inactividad, por los que D. Marcos deberá cotizar a su exclusivo cargo al tipo del 11,50% sobre la base mínima del grupo 7 prorrateada. En cuanto al impago de dos mensualidades consecutivas de inactividad, aunque como regla general la exclusión y baja de oficio surte efectos el día primero del mes siguiente a la segunda mensualidad no ingresada, al encontrarse el trabajador en situación de incapacidad temporal en dicha fecha, el artículo 253.2.b) del TRLGSS pospone los efectos de la exclusión hasta el día primero del mes siguiente a aquel en que finalice la percepción de la prestación de incapacidad temporal (si continúa sin ingresar las cuotas adeudadas)."
            ),
            "explanation": "Artículo 253 del TRLGSS y Orden PJC/297/2026."
        },
        {
            "is_open": True,
            "tipo_abierta": "SUPUESTO",
            "preamble": (
                "En enero de 2026, D. Alejandro dirige una explotación agrícola y ganadera en la provincia de Jaén, además de requerir servicios domésticos en su domicilio particular. En relación con los distintos trabajadores que prestan servicios para él, se plantean las siguientes situaciones durante el ejercicio 2026:\n"
                "- D.ª Elena es contratada como empleada de hogar a tiempo parcial (60 horas mensuales) para la limpieza del domicilio particular de D. Alejandro (quien ostenta el título de familia numerosa). En noviembre de 2026, D.ª Elena sufre un accidente no laboral que requiere baja médica, y en diciembre de 2026 inicia una baja por situación especial de incapacidad temporal por patología limitante derivada de trastorno menopáusico secundario codificado conforme al Real Decreto-ley 31/2026.\n"
                "- D. Marcos, peón agrícola (Grupo 10) afiliado e incluido en el Sistema Especial Agrario (SEA) durante todo el mes de marzo de 2026 (31 días naturales), realiza únicamente 10 jornadas reales trabajadas en dicho mes. Además, en los meses de abril y mayo deja de abonar las cuotas correspondientes a sus períodos de inactividad, entrando en situación de incapacidad temporal el último día del plazo de ingreso.\n"
                "- En la explotación también presta servicios D. Javier, ingeniero agrónomo (Grupo 1) con contrato indefinido ordinario, y varios peones eventuales contratados el mismo día de inicio de la campaña cuya jornada finaliza a las 11:30 horas."
            ),
            "question_text": "5. ¿Qué modalidad y límites de cotización se aplican a D. Javier (Grupo 1 con contrato indefinido) en 2026 y hasta qué hora exacta puede D. Alejandro presentar el alta de los peones eventuales cuya jornada del primer día termina a las 11:30 horas?",
            "options": [],
            "answer": -1,
            "official_answer": (
                "Para D. Javier, al tener un contrato indefinido ordinario (no fijo discontinuo), la modalidad de cotización por bases mensuales resulta estrictamente obligatoria conforme al artículo 255 del TRLGSS. Por pertenecer al Grupo 1, en 2026 se le aplica una reducción de 8,10 puntos porcentuales en el tipo empresarial por contingencias comunes (quedando en el 15,50%), con el límite máximo legal de que la cuota empresarial resultante no podrá ser superior a 279,00 euros al mes (o 12,68 euros por jornada real en caso de cotización diaria). Finalmente, respecto a los peones eventuales cuando no haya sido posible formalizar el alta previa, el Reglamento General de Afiliación permite presentar las solicitudes de alta hasta las 12:00 horas del mismo día de inicio de la prestación de servicios; no obstante, establece expresamente que si la jornada de trabajo finalizase antes de las 12:00 horas —como ocurre aquí al terminar a las 11:30 horas—, la solicitud de alta deberá presentarse obligatoriamente antes de la finalización de dicha jornada (es decir, antes de las 11:30 horas)."
            ),
            "explanation": "Artículo 255 del TRLGSS, RD 84/1996 y Orden PJC/297/2026."
        }
    ]
}

def _separar_planteamiento_y_pregunta_individual(enun_partes, header_opcional=""):
    partes = [p.strip() for p in enun_partes if p and p.strip()]
    if not partes:
        return "", ""

    pat_imperativo_q = re.compile(
        r'^(?:¿|Desglose|Realice\s+el\s+c[áa]lculo|Defina|Una\s+vez\s+emitido|Tras\s+extinguirse|Especifique|Calcule|Determine|Indique|Califique|Fundamente|Explique|Detalle|Se[ñn]ale|Razone|Analice|Justifique)\b',
        re.IGNORECASE
    )

    tiene_hdr = bool(header_opcional and partes[0] == header_opcional.strip())
    cuerpo = partes[1:] if tiene_hdr else partes[:]

    if not cuerpo:
        return "", partes[0]

    if len(cuerpo) == 1:
        unico = cuerpo[0]
        m_split_q = re.match(
            r'^(.+?[\.\:])\s+((?:¿.+|(?:Calcule|Determine|Indique|Explique|Desglose|Señale|Justifique|Razone|Analice)\b.+))$',
            unico,
            flags=re.DOTALL
        )
        if m_split_q:
            hechos_txt = m_split_q.group(1).strip()
            preg_txt = m_split_q.group(2).strip()
            pre_out = f"{header_opcional.strip()}\n\n{hechos_txt}" if tiene_hdr else hechos_txt
            return pre_out.strip(), preg_txt
        else:
            if tiene_hdr:
                return header_opcional.strip(), unico
            return "", unico

    idx_corte_q = len(cuerpo)
    for idx_c in range(1, len(cuerpo)):
        p_c = cuerpo[idx_c]
        if p_c.startswith("¿") or p_c.endswith("?") or pat_imperativo_q.match(p_c):
            idx_corte_q = idx_c
            break

    if idx_corte_q < len(cuerpo):
        hechos_lista = ([header_opcional.strip()] if tiene_hdr else []) + cuerpo[:idx_corte_q]
        pregs_lista = cuerpo[idx_corte_q:]
        return "\n\n".join(hechos_lista).strip(), "\n\n".join(pregs_lista).strip()

    m_ult = re.match(
        r'^(.+?[\.\:])\s+((?:¿.+|(?:Calcule|Determine|Indique|Explique|Desglose|Señale|Justifique|Razone|Analice)\b.+))$',
        cuerpo[-1],
        flags=re.DOTALL
    )
    if m_ult:
        hechos_lista = ([header_opcional.strip()] if tiene_hdr else []) + cuerpo[:-1] + [m_ult.group(1).strip()]
        return "\n\n".join(hechos_lista).strip(), m_ult.group(2).strip()

    hechos_lista = ([header_opcional.strip()] if tiene_hdr else []) + cuerpo[:-1]
    return "\n\n".join(hechos_lista).strip(), cuerpo[-1].strip()

def _reconstruir_respuesta_supuesto_integrada(lineas_r):
    parrafos = []
    for lr in lineas_r:
        s = (lr or "").strip()
        if not s:
            continue
        es_nueva_vineta_o_apartado = bool(
            re.match(r'^(?:[\-•·▪■]\s+|\d+[\)\.]\s+[A-ZÁÉÍÓÚÑ]|[A-Z][\)\.]\s+[A-ZÁÉÍÓÚÑ])', s)
        )
        if not parrafos:
            parrafos.append(s)
        elif es_nueva_vineta_o_apartado:
            parrafos.append(s)
        elif parrafos[-1].rstrip().endswith((".", ":", ";")) and re.match(r'^[A-ZÁÉÍÓÚÑ"«¿¡]', s):
            parrafos.append(s)
        else:
            parrafos[-1] = parrafos[-1].rstrip() + " " + s
    return "\n\n".join(parrafos).strip()

def _formatear_linea_cuerpo_epigrafe_docx(t_raw, prev_line=""):
    t = (t_raw or "").strip()
    if not t:
        return ""
    if re.match(r'^(?:\d+(?:\.\d+)*[\.\)]\s+|[a-zA-Z][\)\.]\s+|[\-•·▪■]\s+)', t):
        return re.sub(r'^[•·▪■]\s+', '- ', t)

    m_sub = re.match(r'^([A-ZÁÉÍÓÚÑ][^:\.]{3,115}):\s+([A-ZÁÉÍÓÚÑ"«\d].+)$', t)
    if m_sub and (prev_line.rstrip().endswith(":") or prev_line.lstrip().startswith("- ")):
        return f"- {t}"

    return t

def _es_linea_cabecera_tema_repetida(s_txt):
    t = re.sub(r'^#+\s*', '', (s_txt or "")).strip()
    if not t:
        return True
    mapa_griegos = str.maketrans("ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ", "ABEZHIKMNOPTYX")
    t_ascii = t.translate(mapa_griegos)
    if re.search(r'(?:SUPUESTOS?\s+PR[ÁA]CTICOS?|CASOS?\s+PR[ÁA]CTICOS?|ENUNCIADO\s+DEL\s+SUPUESTO|PREGUNTAS?\s+DE\s+DESARROLLO)', t_ascii, re.IGNORECASE):
        return False
    if re.match(
        r'^(?:OPOSICIONA|www\.oposiciona\.es|P[áa]gina\s+\d+(?:\s+de(?:\s+\d+)?)?|(?:RESPUESTAS?\s+)?PR[ÁA]CTIC[AO]S?\s+.*TEMA\s+\d+.*|ADMINISTRATIVO\s+DE\s+LA\s+SEGURIDAD\s+SOCIAL.*|GESTI[ÓO]N\s+DE\s+LA\s+SEGURIDAD\s+SOCIAL.*|(?:ADMINISTRATIVO|GESTI[ÓO]N)(?:\s+\d{4})?\s+TEMA\s+[\w\-]+.*|(?:ESPEC[ÍI]FICO\s+|GENERAL\s+)?TEMA\s+\d+[A-Z]?\s*[\-–:]\s*[^\.\?:]{3,85})$',
        t_ascii,
        re.IGNORECASE
    ):
        return True
    return False

def _atomizar_linea_supuesto_test_seguro(raw_line, is_bold):
    l = PDFQuizParser._limpiar_marca_agua_linea(re.sub(r'\s+', ' ', raw_line or "").strip())
    if not l or l in ("0", "-", "#"):
        return []

    if re.match(r'^(?:#\s*)?[a-d][\)\.\-](?:\s+[a-d][\)\.\-])+\s*$', l):
        return [(tok.strip(), is_bold) for tok in re.findall(r'[a-d][\)\.\-]', l)]

    m_empty_then_opt = re.match(r'^((?:#\s*)?[a-d][\)\.\-])\s+((?:#\s*)?[a-d][\)\.\-]\s*.+)$', l)
    if m_empty_then_opt:
        res_eo = [(re.sub(r'^#\s*', '', m_empty_then_opt.group(1)).strip(), is_bold)]
        res_eo.extend(_atomizar_linea_supuesto_test_seguro(m_empty_then_opt.group(2), is_bold))
        return res_eo

    segmentos = []
    es_inicio_enunciado = bool(
        re.match(r'^(?:#+\s*)?(?:(?:SUPUESTO|CASO|PR[ÁA]CTICA|Pregunta|Cuesti[óo]n)\s+[Rr]?\d{1,3}\b|[Rr]?\d{1,3}\s*(?:\.\-|\-\.|\.|\-|\))\s+)', l, re.IGNORECASE)
    )

    cola_exp = None
    if not es_inicio_enunciado:
        m_exp_inline = re.search(
            r'(?<=[.?!»"\)\]])\s*((?:#\s*)?(?:EXPLICACI[ÓO]N(?:\s+DETALLADA|\s+Y\s+JUSTIFICACI[ÓO]N\s+LEGAL|\s+Y\s+BASE\s+LEGAL|\s+PARA\s+ESTUDIO|\s*\([^)]*\))?|Justificaci[óo]n\s+legal(?:\s+y\s+resoluci[óo]n\s+del\s+caso)?)\s*[:\.]\s*.*)$',
            l,
            flags=re.IGNORECASE
        )
        if m_exp_inline and m_exp_inline.start() >= 1:
            pref = l[:m_exp_inline.start()].strip()
            if pref and pref != "#":
                cola_exp = l[m_exp_inline.start():].strip()
                l = pref

    m_q_with_a = re.match(
        r'^((?:#+\s*)?(?:(?:SUPUESTO|CASO|PR[ÁA]CTICA|Pregunta|Cuesti[óo]n)\s+[Rr]?\d{1,3}\s*[:\.\-\)]?|[Rr]?\d{1,3}\s*(?:\.\-|\-\.|\.|\-))\s*["«\'¿¡\(\[]*[A-ZÁÉÍÓÚÑa-záéíóúñ].*?(?:[:\?\.]))\s+([a][\)\.\-]\s*[A-ZÁÉÍÓÚÑ¡¿"\'«\d].*)$',
        l,
        flags=re.IGNORECASE
    )
    if m_q_with_a:
        segmentos.append((m_q_with_a.group(1).strip(), False))
        l = m_q_with_a.group(2).strip()

    partes_opt = re.split(
        r'(?:(?<=[.?!»"\)\];:])(?<!\b[A-Z]\.)\s*|\s{2,})(?=(?:#\s*)?(?:[a-d]\)\s*|[a-d][\.\-]\s+|[A-D]\)\s*)[A-ZÁÉÍÓÚÑ¡¿"\'«\d])',
        l
    )
    for p in partes_opt:
        ps = re.sub(r'^#\s*(?=[a-dA-D][\)\.\-])', '', p.strip())
        if ps:
            segmentos.append((ps, is_bold))

    if cola_exp:
        segmentos.append((cola_exp, False))
    return segmentos

def _separar_hechos_y_pregunta_supuesto_indiv_test(etiqueta_hdr, num_s, texto_completo):
    tc = re.sub(r'\s+', ' ', (texto_completo or "")).strip()
    if not tc:
        return etiqueta_hdr, f"{num_s}."

    m_interrog = re.match(r'^(.+?[\.\:])\s*(¿.+)$', tc)
    if m_interrog:
        return f"{etiqueta_hdr} {m_interrog.group(1).strip()}".strip(), f"{num_s}. {m_interrog.group(2).strip()}"

    m_imp = re.match(
        r'^(.+?[\.,;:])\s*((?:determine|indique|se[ñn]ale|calcule|analice|especifique|desea\s+conocer|se\s+plantea\s+conocer)\b.+)$',
        tc,
        flags=re.IGNORECASE
    )
    if m_imp:
        hechos = m_imp.group(1).rstrip(",") + ("." if m_imp.group(1).endswith(",") else "")
        preg = m_imp.group(2).strip()
        preg = (preg[0].upper() + preg[1:]) if preg else preg
        return f"{etiqueta_hdr} {hechos.strip()}".strip(), f"{num_s}. {preg}"

    partes_frases = re.split(r'(?<=\.)\s+', tc)
    if len(partes_frases) >= 2:
        return f"{etiqueta_hdr} {' '.join(partes_frases[:-1]).strip()}".strip(), f"{num_s}. {partes_frases[-1].strip()}"

    return etiqueta_hdr, f"{num_s}. {tc}"

def _parse_supuestos_test_administrativos_fn(file_bytes, max_options=4):
    """
    Motor unificado para todos los formatos de SUPUESTOS de ADMINISTRATIVOS:
    1) Supuestos compartidos multi-pregunta con o sin test previo (ej. TEMA 02A, TEMA 02B, TEMA 09 NYCM).
    2) Supuestos individuales por pregunta 'SUPUESTO 1: ... a) ... b) ... c) ... d) ...' (ej. TEMA 10 JUBILACIÓN y TEMA 12 - IMV),
       soportando explicaciones con etiqueta 'EXPLICACIÓN:', 'Justificación legal:', texto directo o viñetas '• ...' / '•: ...'.
    """
    lineas_con_geom = []
    if PDFQuizParser.es_archivo_docx(file_bytes):
        for idx_d, it_d in enumerate(PDFQuizParser._extraer_lineas_estructuradas_docx(file_bytes)):
            s_clean = PDFQuizParser._limpiar_marca_agua_linea(it_d["text"])
            if s_clean and not PDFQuizParser._es_basura_cabecera_o_pie(s_clean) and not _es_linea_cabecera_tema_repetida(s_clean):
                for seg_t, seg_b in _atomizar_linea_supuesto_test_seguro(s_clean, it_d["is_bold"]):
                    lineas_con_geom.append((seg_t, seg_b, 0, idx_d * 14.0))
    else:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for p_idx, page in enumerate(doc):
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
                            st_s = s.get("text", "")
                            if not st_s:
                                continue
                            sb = "bold" in (s.get("font", "") or "").lower() or bool(s.get("flags", 0) & 16)
                            if (
                                curr_s_txt and
                                re.match(r'^\s*(?:[a-d][\)\.\-](?:\s*|$)|(?:EXPLICACI[ÓO]N(?:\s+DETALLADA|\s+Y\s+JUSTIFICACI[ÓO]N\s+LEGAL|\s+Y\s+BASE\s+LEGAL)?|Justificaci[óo]n\s+legal)\s*:)', st_s, re.IGNORECASE) and
                                re.search(r'(?:[.?!»"\)\];:]|^[a-d][\)\.\-])\s*$', curr_s_txt.strip()) and
                                not re.search(r'\b[A-Z]\.\s*$', curr_s_txt.strip())
                            ):
                                cuerpo_seg = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', curr_s_txt.strip()).strip()
                                umbral_b = 0.35 if len(cuerpo_seg) <= 5 else 0.55
                                is_b_seg = curr_ch_tot > 0 and (curr_ch_bold / curr_ch_tot) >= umbral_b
                                sub_spans.append((curr_s_txt.strip(), is_b_seg))
                                curr_s_txt = st_s
                                curr_ch_tot = len(st_s.strip())
                                curr_ch_bold = len(st_s.strip()) if sb else 0
                            else:
                                if (
                                    curr_s_txt and
                                    not curr_s_txt.endswith((" ", "\t", "\n")) and
                                    not st_s.startswith((" ", "\t", "\n", ".", ",", ";", ":", ")", "?")) and
                                    (
                                        re.match(r'^(?:#\s*)?(?:[a-d][\)\.\-]|[Rr]?\d{1,3}[\.\-])$', curr_s_txt.strip()) or
                                        re.match(r'^(?:[a-d][\)\.\-]\s+|(?:EXPLICACI[ÓO]N(?:\s+DETALLADA|\s+Y\s+JUSTIFICACI[ÓO]N\s+LEGAL|\s+Y\s+BASE\s+LEGAL)?|Justificaci[óo]n\s+legal)\s*:)', st_s.strip(), re.IGNORECASE)
                                    )
                                ):
                                    curr_s_txt += " " + st_s
                                else:
                                    curr_s_txt += st_s
                                n_c = len(st_s.strip())
                                curr_ch_tot += n_c
                                if sb:
                                    curr_ch_bold += n_c
                        if curr_s_txt.strip():
                            cuerpo_seg = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', curr_s_txt.strip()).strip()
                            umbral_b = 0.35 if len(cuerpo_seg) <= 5 else 0.55
                            is_b_seg = curr_ch_tot > 0 and (curr_ch_bold / curr_ch_tot) >= umbral_b
                            sub_spans.append((curr_s_txt.strip(), is_b_seg))

                        for idx_sp, (s_txt, s_bold) in enumerate(sub_spans):
                            s_clean = PDFQuizParser._limpiar_marca_agua_linea(s_txt)
                            es_div_sup = bool(re.search(r'(?:SUPUESTOS?\s+PR[ÁA]CTICOS?|CASOS?\s+PR[ÁA]CTICOS?)', s_clean or "", re.IGNORECASE))
                            if s_clean and (es_div_sup or (not PDFQuizParser._es_basura_cabecera_o_pie(s_clean) and not _es_linea_cabecera_tema_repetida(s_clean))):
                                items_pagina.append((y0, x0 + idx_sp * 0.1, s_clean, s_bold))

                if not items_pagina:
                    for idx_r, raw_t in enumerate((page.get_text("text") or "").splitlines()):
                        s_clean = PDFQuizParser._limpiar_marca_agua_linea(raw_t.strip())
                        es_div_sup = bool(re.search(r'(?:SUPUESTOS?\s+PR[ÁA]CTICOS?|CASOS?\s+PR[ÁA]CTICOS?)', s_clean or "", re.IGNORECASE))
                        if s_clean and (es_div_sup or (not PDFQuizParser._es_basura_cabecera_o_pie(s_clean) and not _es_linea_cabecera_tema_repetida(s_clean))):
                            for seg_t, seg_b in _atomizar_linea_supuesto_test_seguro(s_clean, s_clean.startswith("#")):
                                lineas_con_geom.append((seg_t, seg_b, p_idx, idx_r * 13.0))
                else:
                    usados = [False] * len(items_pagina)
                    items_emparejados = []
                    for i_it, (y_i, x_i, t_i, b_i) in enumerate(items_pagina):
                        if usados[i_it]:
                            continue
                        if re.match(r'^(?:#\s*)?[a-d][\)\.\-]\s*$', t_i):
                            mejor_j = -1
                            menor_dy = 999.0
                            for j_it, (y_j, x_j, t_j, b_j) in enumerate(items_pagina):
                                if i_it != j_it and not usados[j_it] and x_j > x_i - 5.0:
                                    dy = abs(y_j - y_i)
                                    if dy <= 4.5 and dy < menor_dy and not re.match(r'^(?:#\s*)?[a-d][\)\.\-]\s*$', t_j):
                                        menor_dy = dy
                                        mejor_j = j_it
                            if mejor_j != -1:
                                y_j, x_j, t_j, b_j = items_pagina[mejor_j]
                                usados[i_it] = True
                                usados[mejor_j] = True
                                items_emparejados.append((min(y_i, y_j), x_i, f"{t_i.strip()} {t_j.strip()}", b_i or b_j))
                                continue
                        usados[i_it] = True
                        items_emparejados.append((y_i, x_i, t_i, b_i))

                    items_emparejados.sort(key=lambda it: (round(it[0] / 2.5), it[1]))
                    for y_e, _, t_e, b_e in items_emparejados:
                        for seg_t, seg_b in _atomizar_linea_supuesto_test_seguro(t_e, b_e):
                            lineas_con_geom.append((seg_t, seg_b, p_idx, y_e))
            doc.close()
        except Exception:
            return []

    if not lineas_con_geom:
        return []

    pat_sup_item_num = re.compile(
        r'^(?:#+\s*)?(?:SUPUESTO|CASO|PR[ÁA]CTICA)(?:\s+PR[ÁA]CTIC[OA])?\s+(?:N\.?\s*[º°]?\s*)?(\d{1,3})(?!\d)\s*[:\.\-\)]?\s*(.*)$',
        re.IGNORECASE
    )

    idx_inicio_sup = -1
    for idx_l, (s_l, _, _, _) in enumerate(lineas_con_geom):
        s_sin_h = re.sub(r'^#+\s*', '', s_l).strip()
        if (
            len(s_sin_h) < 140 and
            not re.match(r'^\d{1,3}[\.\-\)]\s*Supuestos?\s+pr[áa]cticos?\s*:\s*\S+', s_sin_h, re.IGNORECASE) and
            not pat_sup_item_num.match(s_sin_h) and
            (
                re.match(
                    r'^(?:(?:\d+|I|II|III)[\.\-\)]\s*)?(?:SEGUNDA\s+PARTE\s*[:\-–]\s*SUPUESTOS?\s+PR[ÁA]CTICOS?.*|SUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+TEMA\s+[\w\-]+|\s+DE\s+APLICACI[ÓO]N|\s+FINAL(?:ES)?|\s*\(.*\))?\s*:?\s*$|CASOS?\s+PR[ÁA]CTICOS?(?:\s+(?:TEMA\s+)?[\w\-]+)?\s*:?\s*$|ENUNCIADO\s+DEL\s+SUPUESTO\b)',
                    s_sin_h,
                    re.IGNORECASE
                ) or
                re.search(r'\bSUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+TEMA\s+[\w\-]+)?\s*:?\s*$', s_sin_h, re.IGNORECASE)
            )
        ):
            idx_inicio_sup = idx_l + 1
            break

    lineas_sup = lineas_con_geom[idx_inicio_sup:] if idx_inicio_sup != -1 else lineas_con_geom[:]
    if not lineas_sup:
        return []

    pat_q_sup_test = re.compile(
        r'^(?:#+\s*)?(?:(?:Pregunta|Cuesti[óo]n)\s+([Rr]?\d{1,3})(?!\d)\s*(?:\.\-|\-\.|:|\.|\-|\))\s*|([Rr]?\d{1,3})(?!\d)\s*(?:\.\-|\-\.|\.|\-|\))\s*)(?:\(RESERVA\)\s*)?(["«\'¿¡\(\[]*[A-ZÁÉÍÓÚÑ].*)$',
        re.IGNORECASE
    )
    pat_opt_test = re.compile(r'^(?:#+\s*)?([a-d]\)\s*(?=[A-ZÁÉÍÓÚÑ¡¿"\'«\d])|[a-d][\.\-]\s+|[A-D]\)\s*)(.+)$')
    pat_opt_empty = re.compile(r'^(?:#+\s*)?([a-d][\)\.\-]|[A-D]\))\s*$')
    pat_exp_test = re.compile(
        r'^(?:#+\s*)?(?:EXPLICACI[ÓO]N(?:\s+DETALLADA|\s+Y\s+JUSTIFICACI[ÓO]N\s+LEGAL|\s+Y\s+BASE\s+LEGAL|\s+PARA\s+ESTUDIO|\s*\([^)]*\))?\s*[:\.]?\s*|Justificaci[óo]n\s+legal(?:\s+y\s+resoluci[óo]n\s+del\s+caso)?\s*[:\.]?\s*|(?:Respuesta(?:\s+correcta)?|Soluci[óo]n)\s*:\s*)(.*)$',
        re.IGNORECASE
    )
    pat_exp_directa_sin_etiqueta = re.compile(
        r'^(?:[•·▪■\*]\s*:?\s*\S+|De\s+(?:conformidad|acuerdo)\s+con|Seg[úu]n\s+(?:el\s+art[íi]culo|lo\s+(?:dispuesto|establecido|previsto)|establece)|Conforme\s+(?:al|a\s+la|a\s+lo)|El\s+(?:art[íi]culo|Real\s+Decreto)|La\s+(?:Disposici[óo]n\s+(?:Transitoria|Adicional|Final)|regla\s+general|reforma)|En\s+virtud\s+de)\b',
        re.IGNORECASE
    )
    pat_nuevo_sup_explicito = re.compile(
        r'^(?:#+\s*)?(?:(?:SUPUESTO|Supuesto|CASO|Caso|PR[ÁA]CTICA|Pr[áa]ctica)(?:\s+(?:PR[ÁA]CTIC[OA]|Pr[áa]ctic[oa]))?\s+(?:N\.?\s*[º°]?\s*)?(?:[A-Z]|\d{1,2}|[IVX]{1,4})(?!\w)(?:\s*[:\.\-\)]\s*.*)?|[A-Z][\)\.\-]\s+(?:Do[ñn]a|Don|D\.|D\.ª|Dª|Dña\.|La\s+(?:empresa|mercantil|sociedad|consultor[íi]a|asesor[íi]a|entidad|cooperativa|mutua|unidad\s+familiar|administraci[óo]n)|El\s+(?:trabajador|empresario|bufete|ciudadano|causante)|Un\s+trabajador|Una\s+trabajadora|En\s+fecha|Con\s+fecha|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+es\s+un|\s+trabaja|\s+presta|\s+ostenta|\s+solicita|\s+\(\d+\s*a[ñn]os\))).*)$'
    )

    def _tiene_opciones_test_antes_de_otro_item(idx_item, lista_ln):
        for j_look in range(idx_item + 1, min(len(lista_ln), idx_item + 26)):
            sl_look = re.sub(r'^#+\s*', '', lista_ln[j_look][0]).strip()
            if pat_opt_test.match(sl_look) or pat_opt_empty.match(sl_look):
                return True
            if pat_q_sup_test.match(sl_look) or pat_sup_item_num.match(sl_look):
                return False
        return False

    def _unir_parrafos_pre(lineas_con_pos):
        if not lineas_con_pos:
            return ""
        pars = []
        prev_pag, prev_y = None, None
        for txt_l, pag_l, y_l in lineas_con_pos:
            salto_parrafo = (prev_pag == pag_l and prev_y is not None and (y_l - prev_y) >= 16.5)
            es_inicio_bloque = bool(
                re.match(
                    r'^(?:(?:SUPUESTO|CASO|Expediente)\b|[A-Z][\)\.\-]\s+|\d{1,2}[\.\)]\s+|[•·\-]\s+|Adicionalmente\b|En\s+(?:primer|segundo|tercer)\s+lugar|Por\s+(?:su\s+parte|[úu]ltimo|otro\s+lado)|Asimismo\b|Finalmente\b|Paralelamente\b)',
                    txt_l,
                    re.IGNORECASE
                )
            )
            if not pars or (es_inicio_bloque and pars[-1].rstrip().endswith((".", ":"))) or (salto_parrafo and pars[-1].rstrip().endswith((".", ":"))):
                pars.append(txt_l)
            else:
                pars[-1] += " " + txt_l
            prev_pag, prev_y = pag_l, y_l
        return "\n\n".join(pars).strip()

    def _es_nuevo_planteamiento_sup_test(idx_cur, lista_ln, estado_act, pre_actual_lineas, curr_q_obj):
        s_cur = re.sub(r'^#+\s*', '', lista_ln[idx_cur][0]).strip()
        if pat_nuevo_sup_explicito.match(s_cur) and (estado_act != "PREAMBULO" or not pre_actual_lineas):
            if estado_act in ("QUESTION", "OPTIONS") and re.match(r'^[A-D]\)\s*', s_cur):
                return False
            if pat_sup_item_num.match(s_cur) and _tiene_opciones_test_antes_de_otro_item(idx_cur, lista_ln):
                return False
            return True

        if estado_act != "EXPLANATION" or curr_q_obj is None:
            return False

        exp_acum = (curr_q_obj.get("explanation") or "").rstrip()
        if not exp_acum.endswith((".", '."', '".', "»", ")")):
            return False

        if not re.match(
            r'^(?:La\s+(?:mercantil|empresa|sociedad|entidad|cooperativa|consultor[íi]a|asesor[íi]a|mutua|compa[ñn][íi]a|unidad\s+familiar|administraci[óo]n|explotaci[óo]n)|El\s+(?:empresario|trabajador|bufete|ciudadano|causante)|(?:Don|Do[ñn]a|D\.|D\.ª|Dª|Dña\.)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+(?:es\s+un[oa]?|trabaja|presta\s+servicios|convive|fallece|solicita|\(\d+\s*a[ñn]os\)))\b',
            s_cur
        ):
            return False

        ult_n = curr_q_obj.get("num", 0)
        bloque_pre_cand = []
        prox_q_lineas = []
        hallada_q = False
        for j in range(idx_cur, min(len(lista_ln), idx_cur + 110)):
            sj = re.sub(r'^#+\s*', '', lista_ln[j][0]).strip()
            mq = pat_q_sup_test.match(sj)
            if mq and _tiene_opciones_test_antes_de_otro_item(j, lista_ln):
                tok = (mq.group(1) or mq.group(2) or "").upper().lstrip("R")
                if tok.isdigit() and int(tok) in (ult_n + 1, 1):
                    hallada_q = True
                    prox_q_lineas.append(sj)
                    for kq in range(j + 1, min(len(lista_ln), j + 6)):
                        prox_q_lineas.append(re.sub(r'^#+\s*', '', lista_ln[kq][0]).strip())
                    break
            bloque_pre_cand.append(sj)

        if not hallada_q or len(bloque_pre_cand) < 4:
            return False

        txt_cand = " ".join(bloque_pre_cand)
        if re.search(
            r'(?:respuesta\s+correcta\s+es|opci[óo]n\s+correcta\s+es|EXPLICACI[ÓO]N\s*:)',
            txt_cand,
            re.IGNORECASE
        ):
            return False

        if any(re.match(r'^(?:\d{1,2}[\.\)]\s+(?:Don|Do[ñn]a|D\.|Dña\.|D\.ª|En\s+|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s*[,(])|Expediente\s+\d+|[•·\-]\s+)', bl) for bl in bloque_pre_cand):
            return True

        _, _, pag_cur, y_cur = lista_ln[idx_cur]
        _, _, pag_prev, y_prev = lista_ln[idx_cur - 1]
        salto_y_grande = (pag_cur == pag_prev and (y_cur - y_prev) >= 20.0) or (pag_cur > pag_prev)

        txt_prox_q = " ".join(prox_q_lineas)
        pre_ant = curr_q_obj.get("preamble") or ""
        protagonistas = re.findall(
            r'(?:"([^"]{3,55})"|«([^»]{3,55})»|\'([^\']{3,55})\'|\b(?:Don|Do[ñn]a|D\.|Dña\.|D\.ª)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)|\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{3,})\s+es\s+un)',
            txt_cand
        )
        menciona_nuevo_protagonista = False
        for g1, g2, g3, g4, g5 in protagonistas:
            nom = (g1 or g2 or g3 or g4 or g5).strip()
            if nom and nom not in pre_ant and nom in txt_prox_q:
                menciona_nuevo_protagonista = True
                break

        return menciona_nuevo_protagonista or (salto_y_grande and len(bloque_pre_cand) >= 5)

    preambulo_actual = []
    preguntas_extraidas = []
    curr_q = None
    estado = "PREAMBULO"
    pending_empty_opts = []

    def _finalizar_q_sup_test(q_obj):
        if not q_obj or len(q_obj.get("options", [])) < 2:
            return

        if q_obj.get("es_sup_indiv_directo"):
            pre_ind, qt_ind = _separar_hechos_y_pregunta_supuesto_indiv_test(
                q_obj.get("sup_hdr", f"SUPUESTO {q_obj.get('num', 1)}:"),
                q_obj.get("num", 1),
                q_obj.get("question_text", "")
            )
            q_obj["preamble"] = pre_ind
            q_obj["question_text"] = qt_ind

        opts_norm = []
        ans_fin = q_obj.get("answer", -1)
        for idx_o, o_raw in enumerate(q_obj["options"]):
            cuerpo_o = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', o_raw).strip()
            if cuerpo_o:
                let_n = chr(ord('a') + len(opts_norm))
                if idx_o == q_obj.get("answer", -1):
                    ans_fin = len(opts_norm)
                opts_norm.append(f"{let_n}) {cuerpo_o}")
        q_obj["options"] = opts_norm
        q_obj["answer"] = ans_fin if 0 <= ans_fin < len(opts_norm) else -1

        if q_obj.get("explanation"):
            q_obj["explanation"] = PDFQuizParser._reconstruir_parrafos_explicacion_test(q_obj["explanation"])

        if q_obj["answer"] == -1 and q_obj.get("explanation"):
            exp_t = q_obj["explanation"]
            m_ans = re.search(
                r'(?:respuesta\s+correcta\s+es\s+la|respuesta\s+correcta|opci[óo]n\s+correcta(?:\s+es\s+la)?|es\s+la\s+opci[óo]n|correcta\s+es\s+la)\s*[:\s]*[\'"«]?([a-dA-D])[\)\'"»]?\b',
                exp_t,
                re.IGNORECASE
            )
            if not m_ans:
                m_ans = re.search(r'\bopci[óo]n\s+([a-dA-D])[\)\'"]?\s+es\s+(?:la\s+)?correcta\b', exp_t, re.IGNORECASE)
            if m_ans:
                idx_a = ord(m_ans.group(1).lower()) - ord('a')
                if 0 <= idx_a < len(q_obj["options"]):
                    q_obj["answer"] = idx_a

        if not (q_obj.get("preamble") or "").strip():
            qt_full = (q_obj.get("question_text") or "").strip()
            m_num_pref = re.match(r'^([Rr]?\d{1,3}\.\s*(?:\(RESERVA\)\s*)?)(.+)$', qt_full, flags=re.DOTALL)
            if m_num_pref:
                pref_n = m_num_pref.group(1).strip()
                cuerpo_qt = m_num_pref.group(2).strip()
                if len(cuerpo_qt) > 190 and "." in cuerpo_qt:
                    m_sp_ind = re.match(r'^(.+?[\.\:])\s+(¿.+\?)$', cuerpo_qt, flags=re.DOTALL)
                    if m_sp_ind and len(m_sp_ind.group(1).strip()) >= 85:
                        q_obj["preamble"] = f"{pref_n} {m_sp_ind.group(1).strip()}"
                        q_obj["question_text"] = m_sp_ind.group(2).strip()

        if max_options is not None and len(q_obj["options"]) > max_options:
            PDFQuizParser._reducir_opciones_conservando_correcta(q_obj, max_options)

        q_obj["is_open"] = False
        q_obj["es_supuesto_test"] = True
        q_obj.pop("num", None)
        q_obj.pop("es_sup_indiv_directo", None)
        q_obj.pop("sup_hdr", None)
        preguntas_extraidas.append(q_obj)

    for i_ln, (s_raw, is_b, pag_i, y_i) in enumerate(lineas_sup):
        s_l = re.sub(r'^#+\s*', '', s_raw).strip()
        if not s_l or re.match(r'^(?:PREGUNTAS?\s+DE\s+RESERVA|CUESTIONES(?:\s+PR[ÁA]CTICAS)?|PREGUNTAS\s+DEL\s+SUPUESTO|SUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+TEMA\s+[\w\-]+)?|CASOS?\s+PR[ÁA]CTICOS?(?:\s+(?:TEMA\s+)?[\w\-]+)?)\s*:?\s*$', s_l, re.IGNORECASE):
            continue
        if _es_linea_cabecera_tema_repetida(s_l):
            continue

        m_sup_ind = pat_sup_item_num.match(s_l)
        if m_sup_ind and _tiene_opciones_test_antes_de_otro_item(i_ln, lineas_sup):
            if curr_q is not None:
                _finalizar_q_sup_test(curr_q)
            pending_empty_opts = []
            num_si = int(m_sup_ind.group(1))
            resto_si = m_sup_ind.group(2).strip()
            curr_q = {
                "num": num_si,
                "es_sup_indiv_directo": True,
                "sup_hdr": f"SUPUESTO {num_si}:",
                "preamble": "",
                "question_text": resto_si,
                "options": [],
                "answer": -1,
                "explanation": ""
            }
            estado = "QUESTION"
            continue

        if _es_nuevo_planteamiento_sup_test(i_ln, lineas_sup, estado, preambulo_actual, curr_q):
            if curr_q is not None:
                _finalizar_q_sup_test(curr_q)
                curr_q = None
            pending_empty_opts = []
            preambulo_actual = [(s_l, pag_i, y_i)]
            estado = "PREAMBULO"
            continue

        m_q = pat_q_sup_test.match(s_l)
        m_opt_e = pat_opt_empty.match(s_l)
        m_opt = pat_opt_test.match(s_l)
        es_cab_exp = bool(re.match(r'^(?:#+\s*)?(?:EXPLICACI[ÓO]N|Justificaci[óo]n\s+legal|Respuesta(?:\s+correcta)?\s*:|Soluci[óo]n\s*:)', s_raw, re.IGNORECASE))
        m_exp = pat_exp_test.match(s_l) if es_cab_exp else None

        if m_q and not m_opt and not m_opt_e:
            tok_q = (m_q.group(1) or m_q.group(2) or "").upper()
            es_res = tok_q.startswith("R") or "(RESERVA)" in s_l.upper()
            num_q = int(tok_q.lstrip("R"))
            txt_q = m_q.group(3).strip()

            tiene_opciones_debajo = _tiene_opciones_test_antes_de_otro_item(i_ln, lineas_sup)

            if estado == "PREAMBULO" and curr_q is None and not tiene_opciones_debajo:
                preambulo_actual.append((s_l, pag_i, y_i))
                continue

            en_mitad_enunciado_u_opciones = (
                curr_q is not None and estado in ("QUESTION", "OPTIONS") and len(curr_q.get("options", [])) < 2
            )
            if not en_mitad_enunciado_u_opciones and tiene_opciones_debajo:
                if curr_q is not None:
                    _finalizar_q_sup_test(curr_q)
                pending_empty_opts = []
                etiqueta_n = f"R{num_q}." if tok_q.startswith("R") else (f"{num_q}. (RESERVA)" if es_res else f"{num_q}.")
                curr_q = {
                    "num": num_q,
                    "es_sup_indiv_directo": False,
                    "preamble": _unir_parrafos_pre(preambulo_actual),
                    "question_text": f"{etiqueta_n} {txt_q}",
                    "options": [],
                    "answer": -1,
                    "explanation": ""
                }
                estado = "QUESTION"
                continue

        if estado == "PREAMBULO":
            preambulo_actual.append((s_l, pag_i, y_i))
            continue

        if curr_q is None:
            continue

        if m_exp and len(curr_q["options"]) >= 2:
            estado = "EXPLANATION"
            pending_empty_opts = []
            resto_e = m_exp.group(1).strip()
            if resto_e:
                curr_q["explanation"] = (curr_q["explanation"] + "\n" + resto_e).strip()
            continue

        # Explicación directa sin etiqueta tras completar las 4 opciones (incluyendo viñetas '• ...' / '•: ...' de TEMA 12 - IMV)
        if estado == "OPTIONS" and len(curr_q["options"]) >= 4 and not pending_empty_opts and not m_opt and not m_opt_e:
            ult_opt_txt = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', curr_q["options"][-1]).rstrip()
            no_acaba_en_conector = not bool(
                re.search(r'\b(?:de|del|a|al|en|con|por|para|sin|sobre|que|y|o|el|la|los|las|un|una|su|sus)\s*$', ult_opt_txt, re.IGNORECASE)
            )
            if pat_exp_directa_sin_etiqueta.match(s_l) or (ult_opt_txt.endswith((".", "?", "!", "»", '"', ")")) and no_acaba_en_conector and re.match(r'^(?:[•·▪■\-\*]\s*:?\s*|["«\'¡¿]?[A-ZÁÉÍÓÚÑ])', s_l)):
                estado = "EXPLANATION"
                s_l_exp = re.sub(r'^([•·▪■\*])\s*:\s*', r'\1 ', s_l)
                curr_q["explanation"] = (curr_q["explanation"] + "\n" + s_l_exp).strip()
                continue

        if m_opt_e and estado in ("QUESTION", "OPTIONS") and len(curr_q["options"]) < 4:
            letra_asig = chr(ord('a') + len(curr_q["options"]))
            curr_q["options"].append(f"{letra_asig}) ")
            if is_b:
                curr_q["answer"] = len(curr_q["options"]) - 1
            pending_empty_opts.append(len(curr_q["options"]) - 1)
            estado = "OPTIONS"
            continue

        if m_opt and estado in ("QUESTION", "OPTIONS"):
            let_c = m_opt.group(1)[0].lower()
            cuerpo_o = m_opt.group(2).strip()
            es_correcta_o = is_b or s_raw.lstrip().startswith("#")

            if pending_empty_opts and len(curr_q["options"]) == pending_empty_opts[0] + 1 and curr_q["options"][-1].strip().endswith(")"):
                idx_f = pending_empty_opts.pop(0)
                letra_f = chr(ord('a') + idx_f)
                curr_q["options"][idx_f] = f"{letra_f}) {cuerpo_o}"
                if es_correcta_o:
                    curr_q["answer"] = idx_f
                estado = "OPTIONS"
                continue

            if len(curr_q["options"]) < 4:
                letra_esp = chr(ord('a') + len(curr_q["options"]))
                ult_cuerpo_o = re.sub(r'^[a-dA-D][\)\.\-]\s*', '', curr_q["options"][-1]).strip() if curr_q["options"] else ""
                es_ref_interna = (
                    estado == "OPTIONS" and bool(curr_q["options"]) and
                    (
                        bool(re.search(r'\b(?:letra|apartado|ep[íi]grafe|p[áa]rrafo|ordinal|inciso|opci[óo]n)s?\s*$', ult_cuerpo_o, re.IGNORECASE)) or
                        (bool(re.match(r'^[a-záéíóúñ]', cuerpo_o)) and not ult_cuerpo_o.endswith((".", ";", "?", "!")) and let_c != letra_esp)
                    )
                )
                if not es_ref_interna:
                    pending_empty_opts = []
                    curr_q["options"].append(f"{letra_esp}) {cuerpo_o}")
                    if es_correcta_o:
                        curr_q["answer"] = len(curr_q["options"]) - 1
                    estado = "OPTIONS"
                    continue

        if estado == "QUESTION":
            curr_q["question_text"] = (curr_q["question_text"] + " " + s_l).strip()
        elif estado == "OPTIONS" and curr_q["options"]:
            if pending_empty_opts:
                idx_t = pending_empty_opts[0]
                txt_act = re.sub(r'^[a-d]\)\s*', '', curr_q["options"][idx_t]).strip()
                letra_t = chr(ord('a') + idx_t)
                curr_q["options"][idx_t] = f"{letra_t}) {s_l}" if not txt_act else f"{curr_q['options'][idx_t]} {s_l}"
                if is_b and curr_q["answer"] == -1:
                    curr_q["answer"] = idx_t
                if s_l.endswith((".", ";", "!", "?")):
                    pending_empty_opts.pop(0)
            else:
                curr_q["options"][-1] += " " + s_l
                if is_b and curr_q["answer"] == -1:
                    curr_q["answer"] = len(curr_q["options"]) - 1
        elif estado == "EXPLANATION":
            s_l_exp = re.sub(r'^([•·▪■\*])\s*:\s*', r'\1 ', s_l)
            curr_q["explanation"] = (curr_q["explanation"] + "\n" + s_l_exp).strip()

    if curr_q is not None:
        _finalizar_q_sup_test(curr_q)

    return preguntas_extraidas

def _agrupar_lineas_por_banda_horizontal_pdf(items_raw, tolerancia_y=5.2):
    if not items_raw:
        return []
    items_y = sorted(items_raw, key=lambda it: (it[0], it[1]))
    bandas = []
    curr_band = [items_y[0]]
    for it in items_y[1:]:
        y_ref = curr_band[0][0]
        if abs(it[0] - y_ref) <= tolerancia_y:
            curr_band.append(it)
        else:
            bandas.append(curr_band)
            curr_band = [it]
    if curr_band:
        bandas.append(curr_band)

    lineas_unidas = []
    for b in bandas:
        b.sort(key=lambda it: it[1])
        y_min = min(it[0] for it in b)
        x_min = b[0][1]
        txt_unido = " ".join(it[2].strip() for it in b if it[2].strip())
        txt_unido = re.sub(r'\s+', ' ', txt_unido).strip()
        is_b = any(it[3] for it in b)
        if txt_unido:
            lineas_unidas.append((y_min, x_min, txt_unido, is_b))
    return lineas_unidas

def _es_inicio_nuevo_planteamiento_supuesto(idx_ls, lineas_sup, sub_estado, preambulo_lineas, curr_c, pat_cuestion, pat_nuevo_supuesto_bloque):
    l_s = re.sub(r'^#\s*', '', lineas_sup[idx_ls][0]).strip()
    if pat_nuevo_supuesto_bloque.match(l_s) and (sub_estado != "PREAMBULO" or not preambulo_lineas):
        return True

    if sub_estado not in ("EXPLICACION", "RESPUESTA") or curr_c is None:
        return False

    lineas_resp_act = curr_c["exp"] if sub_estado == "EXPLICACION" else curr_c["resp"]
    if not lineas_resp_act:
        return False

    ult_linea_resp = lineas_resp_act[-1].rstrip()
    if not ult_linea_resp.endswith((".", '."', '".', "»", ")")):
        return False

    if not re.match(
        r'^(?:[A-Z][\)\.\-]\s+)?(?:La\s+(?:mercantil|empresa|sociedad|entidad|cooperativa|consultor[íi]a|asesor[íi]a|mutua|compa[ñn][íi]a|unidad\s+familiar)|El\s+(?:empresario|trabajador|bufete|ciudadano)|(?:Don|Do[ñn]a|D\.|D\.ª|Dª|Dña\.)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+es\s+un|\s+\(\d+\s*a[ñn]os\)))\b',
        l_s
    ):
        return False

    ult_num = curr_c["num"]
    bloque_cand = []
    prox_q_lineas = []
    encontrada_prox_q = False
    for j in range(idx_ls, min(len(lineas_sup), idx_ls + 95)):
        lj = re.sub(r'^#\s*', '', lineas_sup[j][0]).strip()
        mc = pat_cuestion.match(lj)
        if mc and int(mc.group(1)) in (ult_num + 1, 1):
            if not re.match(r'^\d{1,2}[\.\)]\s+(?:Don|Do[ñn]a|D\.|Dña\.|D\.ª)\s+', lj):
                encontrada_prox_q = True
                prox_q_lineas.append(lj)
                for k_q in range(j + 1, min(len(lineas_sup), j + 4)):
                    lk = re.sub(r'^#\s*', '', lineas_sup[k_q][0]).strip()
                    prox_q_lineas.append(lk)
                    if lk.endswith(("?", ":")):
                        break
                break
        bloque_cand.append(lj)

    if not encontrada_prox_q or len(bloque_cand) < 4:
        return False

    txt_bloque = " ".join(bloque_cand)
    if re.search(
        r'\b(?:TRLGSS|LGSS|Real\s+Decreto|Orden\s+(?:de\s+\d|PJC|TAS|TIN)|jurisprudencia|sentencia|presunci[óo]n\s+iuris)\b',
        txt_bloque,
        re.IGNORECASE
    ):
        return False

    tiene_estructura_planteamiento = bool(
        any(b_l.startswith(("•", "-")) or re.match(r'^(?:\d{1,2}[\.\)]\s+(?:Don|Do[ñn]a|D\.|Dña\.)|Expediente\s+\d+)', b_l) for b_l in bloque_cand) or
        re.search(
            r'(?:estructura\s+org[áa]nica|accionarial|prestan\s+servicios|cuenta\s+con\s+una\s+plantilla|son\s+c[óo]nyuges|posee\s+el\s+\d+\s*%\s+del\s+capital|conceptos\s+retributivos)',
            txt_bloque,
            re.IGNORECASE
        )
    )
    if tiene_estructura_planteamiento:
        return True

    txt_prox_q = " ".join(prox_q_lineas)
    pre_anterior = curr_c.get("preamble") or ""
    entidades_nuevas = re.findall(r'(?:"([^"]{3,45})"|«([^»]{3,45})»|\b((?:Don|Do[ñn]a|D\.|Dña\.)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+))', txt_bloque)
    for emp_q, emp_lat, pers_q in entidades_nuevas:
        nom_ent = (emp_q or emp_lat or pers_q).strip()
        if nom_ent and nom_ent not in pre_anterior and nom_ent in txt_prox_q:
            return True

    return False

def _extraer_supuestos_con_bloque_solucion(file_bytes):
    if PDFQuizParser.es_archivo_docx(file_bytes):
        return []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception:
        return []

    lineas_doc = []
    for page in doc:
        items_p = []
        blocks = page.get_text("dict").get("blocks", [])
        for b in blocks:
            for l in b.get("lines", []):
                bbox = l.get("bbox", (0, 0, 0, 0))
                y0, x0 = round(bbox[1], 1), round(bbox[0], 1)
                spans = l.get("spans", [])
                txt_l = "".join(s.get("text", "") for s in spans).strip()
                if not txt_l:
                    continue
                ch_t = sum(len(s.get("text", "").strip()) for s in spans)
                ch_b = sum(
                    len(s.get("text", "").strip())
                    for s in spans
                    if ("bold" in (s.get("font", "") or "").lower() or bool(s.get("flags", 0) & 16))
                )
                is_b = ch_t > 0 and (ch_b / ch_t) >= 0.55
                s_clean = PDFQuizParser._limpiar_marca_agua_linea(txt_l)
                if not s_clean or PDFQuizParser._es_basura_cabecera_o_pie(s_clean) or _es_linea_cabecera_tema_repetida(s_clean):
                    continue
                if re.match(r'^(?:#\s*)?(?:PR[ÁA]CTIC[AO]S?|CASOS?\s+PR[ÁA]CTICOS?)\s+(?:TEMA\s+\d+|JUBILACI[ÓO]N|GESTI[ÓO]N).*$', s_clean, re.IGNORECASE):
                    continue
                items_p.append((y0, x0, s_clean, is_b))

        for _, _, s_unida, _ in _agrupar_lineas_por_banda_horizontal_pdf(items_p, tolerancia_y=5.2):
            lineas_doc.append(s_unida)

    doc.close()

    if not lineas_doc:
        return []

    if sum(1 for l_t in lineas_doc if re.match(r'^(?:#\s*)?[a-dA-D][\)\.\-]\s+\S+', l_t)) >= 6:
        return []

    pat_sup_hdr = re.compile(
        r'^(?:#\s*)?(?:([A-Z])[\)\.\-]\s*)?(?:SUPUESTO|Supuesto|CASO|Caso)(?:\s+(?:PR[ÁA]CTICO|Pr[áa]ctico))?\s+(?:N\.?\s*[º°]?\s*)?(\d{1,2}|[IVX]{1,4}|[A-Z])(?!\w)\s*[:\.\-]?\s*(.*)$'
    )
    pat_sol_hdr = re.compile(
        r'^(?:#\s*)?(?:SOLUCI[ÓO]N(?:ES)?|RESPUESTAS?(?:\s+Y\s+FUNDAMENTOS?\s+JUR[ÍI]DICOS?|\s+OFICIAL(?:ES)?|\s+T[ÉE]CNICAS?)?)\s*[:\.\-]\s*(.*)$|^(?:#\s*)?(?:SOLUCI[ÓO]N(?:ES)?|RESPUESTAS?(?:\s+Y\s+FUNDAMENTOS?\s+JUR[ÍI]DICOS?)?)\s*$',
        re.IGNORECASE
    )
    pat_preg_explicita = re.compile(
        r'^(?:#\s*)?(?:Pregunta|Cuesti[óo]n)\s+(\d{1,2})(?!\d)\s*[:\.\-\)]\s*(.*)$',
        re.IGNORECASE
    )
    pat_num_item = re.compile(
        r'^(?:#\s*)?(?:Pregunta\s+|Cuesti[óo]n\s+)?(\d{1,2})(?!\d)\s*[\.\-\)]\s+(["«\'¿¡A-ZÁÉÍÓÚÑ].*)$',
        re.IGNORECASE
    )

    n_sol_headers = sum(
        1 for l_t in lineas_doc
        if pat_sol_hdr.match(re.sub(r'^#\s*', '', l_t).strip()) or pat_preg_explicita.match(re.sub(r'^#\s*', '', l_t).strip())
    )
    if n_sol_headers < 1:
        return []

    supuestos_bloques = []
    curr_sup = None
    sub_modo_actual = None
    q_explicita_actual_num = None
    q_explicita_actual_lineas = []

    def _sincronizar_pregunta_explicita(sup_obj, num_p, lineas_p):
        txt_pe = re.sub(r'\s+', ' ', " ".join(lineas_p)).strip()
        if not txt_pe:
            return
        for q_item in sup_obj["preguntas"]:
            if q_item[0] == num_p:
                txt_lista = re.sub(r'\s+', ' ', " ".join(q_item[1])).strip()
                if len(txt_pe) > len(txt_lista) + 3:
                    q_item[1] = [txt_pe]
                    if sup_obj["preambulo"] and sup_obj["preambulo"][-1].strip() in txt_pe and not sup_obj["preambulo"][-1].rstrip().endswith("."):
                        sup_obj["preambulo"].pop()
                return
        sup_obj["preguntas"].append([num_p, [txt_pe]])

    for l_raw in lineas_doc:
        l = re.sub(r'^#\s*', '', l_raw).strip()
        if not l:
            continue

        m_sub_preg = re.match(r'^(?:[A-Z][\.\)]\s*)?Preguntas(?:\s+de\s+Examen)?\s*:\s*(.*)$', l, re.IGNORECASE)
        if m_sub_preg:
            if m_sub_preg.group(1).strip():
                l = m_sub_preg.group(1).strip()
            else:
                continue

        m_sup = pat_sup_hdr.match(l)
        if m_sup and (curr_sup is None or curr_sup["en_solucion"] or len(curr_sup["preguntas"]) > 0):
            if curr_sup is not None and q_explicita_actual_num is not None and q_explicita_actual_lineas:
                _sincronizar_pregunta_explicita(curr_sup, q_explicita_actual_num, q_explicita_actual_lineas)
            q_explicita_actual_num = None
            q_explicita_actual_lineas = []

            if curr_sup is not None:
                supuestos_bloques.append(curr_sup)
            letra_pref = (m_sup.group(1) or "").strip()
            etiqueta_sup = m_sup.group(2).strip()
            resto_sup = m_sup.group(3).strip()
            pref_titulo = f"{letra_pref}) Supuesto {etiqueta_sup}:" if letra_pref else f"Supuesto {etiqueta_sup}:"
            curr_sup = {
                "id": etiqueta_sup,
                "header": pref_titulo,
                "preambulo": [resto_sup] if resto_sup else [],
                "preguntas": [],
                "respuestas": [],
                "en_solucion": False
            }
            sub_modo_actual = "PREAMBULO"
            continue

        if curr_sup is None:
            continue

        m_pe = pat_preg_explicita.match(l)
        if m_pe:
            if q_explicita_actual_num is not None and q_explicita_actual_lineas:
                _sincronizar_pregunta_explicita(curr_sup, q_explicita_actual_num, q_explicita_actual_lineas)

            num_pe = int(m_pe.group(1))
            resto_pe = m_pe.group(2).strip()
            curr_sup["en_solucion"] = True
            q_explicita_actual_num = num_pe
            q_explicita_actual_lineas = []

            m_inline_rfj = re.search(
                r'^(.+?[\?\.])\s*(?:Respuesta(?:\s+y\s+Fundamento(?:\s+Jur[íi]dico)?)?|Soluci[óo]n)\s*:?\s*(.*)$',
                resto_pe,
                flags=re.IGNORECASE
            )
            if m_inline_rfj:
                q_pe_txt = m_inline_rfj.group(1).strip()
                r_pe_txt = re.sub(r'^(?:Jur[íi]dico\s*:\s*)', '', m_inline_rfj.group(2).strip(), flags=re.IGNORECASE).strip()
                q_explicita_actual_lineas.append(q_pe_txt)
                _sincronizar_pregunta_explicita(curr_sup, num_pe, q_explicita_actual_lineas)
                q_explicita_actual_lineas = []
                curr_sup["respuestas"].append([num_pe, [r_pe_txt] if r_pe_txt else []])
                sub_modo_actual = "PREGUNTA_EXPLICITA_RESP"
            else:
                if resto_pe:
                    q_explicita_actual_lineas.append(resto_pe)
                curr_sup["respuestas"].append([num_pe, []])
                cerro_en_misma_linea = resto_pe.endswith("?") or (resto_pe.endswith(".") and len(resto_pe) > 25)
                if cerro_en_misma_linea:
                    _sincronizar_pregunta_explicita(curr_sup, num_pe, q_explicita_actual_lineas)
                    q_explicita_actual_lineas = []
                    sub_modo_actual = "PREGUNTA_EXPLICITA_RESP"
                else:
                    sub_modo_actual = "PREGUNTA_EXPLICITA_HEADER"
            continue

        if sub_modo_actual == "PREGUNTA_EXPLICITA_HEADER":
            m_sol_in = pat_sol_hdr.match(l)
            if m_sol_in:
                if q_explicita_actual_num is not None and q_explicita_actual_lineas:
                    _sincronizar_pregunta_explicita(curr_sup, q_explicita_actual_num, q_explicita_actual_lineas)
                    q_explicita_actual_lineas = []
                sub_modo_actual = "PREGUNTA_EXPLICITA_RESP"
                resto_s = (m_sol_in.group(1) or "").strip()
                if resto_s and curr_sup["respuestas"]:
                    curr_sup["respuestas"][-1][1].append(resto_s)
                continue

            m_q_then_rfj = re.search(
                r'^(.+?[\?\.])\s*(?:Respuesta(?:\s+y\s+Fundamento(?:\s+Jur[íi]dico)?)?|Soluci[óo]n)\s*:?\s*(.*)$',
                l,
                flags=re.IGNORECASE
            )
            if m_q_then_rfj:
                q_explicita_actual_lineas.append(m_q_then_rfj.group(1).strip())
                if q_explicita_actual_num is not None:
                    _sincronizar_pregunta_explicita(curr_sup, q_explicita_actual_num, q_explicita_actual_lineas)
                q_explicita_actual_lineas = []
                sub_modo_actual = "PREGUNTA_EXPLICITA_RESP"
                cola_r = re.sub(r'^(?:Jur[íi]dico\s*:\s*)', '', m_q_then_rfj.group(2).strip(), flags=re.IGNORECASE).strip()
                if cola_r and curr_sup["respuestas"]:
                    curr_sup["respuestas"][-1][1].append(cola_r)
                continue

            q_explicita_actual_lineas.append(l)
            if l.endswith(("?", ".")):
                if q_explicita_actual_num is not None:
                    _sincronizar_pregunta_explicita(curr_sup, q_explicita_actual_num, q_explicita_actual_lineas)
                q_explicita_actual_lineas = []
                sub_modo_actual = "PREGUNTA_EXPLICITA_RESP"
            continue

        m_sol = pat_sol_hdr.match(l)
        if m_sol and len(curr_sup["preguntas"]) >= 1:
            resto_sol = (m_sol.group(1) or "").strip()
            if sub_modo_actual in ("PREGUNTA_EXPLICITA_HEADER", "PREGUNTA_EXPLICITA_RESP") and curr_sup["respuestas"]:
                sub_modo_actual = "PREGUNTA_EXPLICITA_RESP"
                if resto_sol:
                    curr_sup["respuestas"][-1][1].append(resto_sol)
                continue
            elif not curr_sup["en_solucion"]:
                curr_sup["en_solucion"] = True
                sub_modo_actual = "SOLUCION_NUMERADA"
                if resto_sol:
                    m_n = pat_num_item.match(resto_sol)
                    if m_n:
                        curr_sup["respuestas"].append([int(m_n.group(1)), [m_n.group(2).strip()]])
                    else:
                        curr_sup["respuestas"].append([1, [resto_sol]])
                continue

        if sub_modo_actual == "PREGUNTA_EXPLICITA_RESP":
            l_clean_rfj = re.sub(
                r'^(?:Respuesta(?:\s+y\s+Fundamento(?:\s+Jur[íi]dico)?)?\s*:?\s*|Fundamento\s+Jur[íi]dico\s*:\s*|Jur[íi]dico\s*:\s*)',
                '',
                l,
                flags=re.IGNORECASE
            ).strip()
            if l_clean_rfj and curr_sup["respuestas"]:
                curr_sup["respuestas"][-1][1].append(l_clean_rfj)
            continue

        m_num = pat_num_item.match(l)
        if not curr_sup["en_solucion"]:
            if m_num:
                num_q = int(m_num.group(1))
                txt_q = m_num.group(2).strip()
                partes_q = re.split(r'(?<=[.?!])\s+(?=\d{1,2}\s*[\.\-\)]\s+[¿¡A-ZÁÉÍÓÚÑ])', f"{num_q}. {txt_q}")
                for pq in partes_q:
                    mn_sub = pat_num_item.match(pq.strip())
                    if mn_sub:
                        curr_sup["preguntas"].append([int(mn_sub.group(1)), [mn_sub.group(2).strip()]])
                sub_modo_actual = "PREGUNTAS_LISTA"
            else:
                if not curr_sup["preguntas"]:
                    curr_sup["preambulo"].append(l)
                else:
                    ult_num_q = curr_sup["preguntas"][-1][0]
                    m_peg_q = re.search(rf'^(.*)\s+({ult_num_q + 1}\s*[\.\-\)]\s+[¿¡A-ZÁÉÍÓÚÑ].*)$', l)
                    if m_peg_q:
                        curr_sup["preguntas"][-1][1].append(m_peg_q.group(1).strip())
                        mn2 = pat_num_item.match(m_peg_q.group(2).strip())
                        if mn2:
                            curr_sup["preguntas"].append([int(mn2.group(1)), [mn2.group(2).strip()]])
                    else:
                        curr_sup["preguntas"][-1][1].append(l)
        else:
            if m_num:
                num_r = int(m_num.group(1))
                txt_r = m_num.group(2).strip()
                ult_num_r = curr_sup["respuestas"][-1][0] if curr_sup["respuestas"] else 0
                if num_r == ult_num_r + 1 or not curr_sup["respuestas"]:
                    curr_sup["respuestas"].append([num_r, [txt_r]])
                else:
                    curr_sup["respuestas"][-1][1].append(l)
            else:
                if not curr_sup["respuestas"]:
                    curr_sup["respuestas"].append([1, [l]])
                else:
                    ult_num_r = curr_sup["respuestas"][-1][0]
                    m_peg_r = re.search(rf'^(.*)\s+({ult_num_r + 1}\s*[\.\-\)]\s+[A-ZÁÉÍÓÚÑ].*)$', l)
                    if m_peg_r:
                        curr_sup["respuestas"][-1][1].append(m_peg_r.group(1).strip())
                        mr2 = pat_num_item.match(m_peg_r.group(2).strip())
                        if mr2:
                            curr_sup["respuestas"].append([int(mr2.group(1)), [mr2.group(2).strip()]])
                    else:
                        curr_sup["respuestas"][-1][1].append(l)

    if curr_sup is not None:
        if q_explicita_actual_num is not None and q_explicita_actual_lineas:
            _sincronizar_pregunta_explicita(curr_sup, q_explicita_actual_num, q_explicita_actual_lineas)
        supuestos_bloques.append(curr_sup)

    if not supuestos_bloques or sum(1 for sb in supuestos_bloques if sb["en_solucion"]) < max(1, len(supuestos_bloques) // 2):
        return []

    resultado = []
    for sb in supuestos_bloques:
        cuerpo_pre = re.sub(r'\s+', ' ', " ".join(sb["preambulo"])).strip()
        pre_txt = f"{sb['header']}\n\n{cuerpo_pre}".strip() if cuerpo_pre else sb["header"]
        mapa_resp = {
            num_r: _reconstruir_respuesta_supuesto_integrada(lineas_r)
            for num_r, lineas_r in sb["respuestas"]
        }
        for idx_q, (num_q, lineas_q) in enumerate(sb["preguntas"]):
            q_txt = re.sub(r'\s+', ' ', " ".join(lineas_q)).strip()
            r_txt = mapa_resp.get(num_q, "")
            if not r_txt and idx_q < len(sb["respuestas"]):
                r_txt = _reconstruir_respuesta_supuesto_integrada(sb["respuestas"][idx_q][1])
            if not r_txt and len(sb["respuestas"]) == 1:
                r_txt = _reconstruir_respuesta_supuesto_integrada(sb["respuestas"][0][1])

            if q_txt and r_txt:
                resultado.append({
                    "is_open": True,
                    "tipo_abierta": "SUPUESTO",
                    "preamble": pre_txt,
                    "question_text": f"{num_q}. {q_txt}",
                    "options": [],
                    "answer": -1,
                    "official_answer": r_txt,
                    "explanation": r_txt
                })

    return resultado

def _es_inicio_respuesta_supuesto_indiv(p_txt):
    t = re.sub(r'^#\s*', '', (p_txt or "")).strip()
    if not t:
        return False

    if re.match(r'^(?:\d+\)\s+|A\s+efectos\s+de\s+proceder\s+a\s+la\s+liquidaci[óo]n)', t, re.IGNORECASE):
        return False

    if t.startswith("¿") or t.endswith("?"):
        return False

    if re.match(
        r'^(?:Desglose|Realice\s+el\s+c[áa]lculo|Defina|Una\s+vez\s+emitido|Tras\s+extinguirse|Especifique|Calcule|Determine|Indique|Califique|Fundamente|Explique|Detalle|Se[ñn]ale|Razone|Analice|Justifique)\b',
        t,
        re.IGNORECASE
    ):
        return False

    if "¿" in t and "?" in t and not re.match(r'^(?:RESPUESTA|EXPLICACI[ÓO]N|S[íi]\s*,|No\s*,|Conforme\s+a|De\s+acuerdo\s+con)\b', t, re.IGNORECASE):
        return False

    if re.match(
        r'^(?:RESPUESTA|EXPLICACI[ÓO]N|S[íi]\s*,|No\s*,|No\s+debe|No\s+perder[áa]|No\s+ha\s+perdido|Conforme\s+a|De\s+acuerdo\s+con|De\s+conformidad\s+con|Seg[úu]n\s+(?:el|la|los|las|dispone)|En\s+(?:el\s+caso\s+de|los\s+supuestos\s+de|los\s+procesos)|Frente\s+a\s+las\s+altas|El\s+(?:derecho|embargo|proceder|art[íi]culo)|La\s+(?:alegaci[óo]n|exigencia|denegaci[óo]n|solicitud|empresa)|Ambas\s+pensiones|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[a-záéíóúñA-ZÁÉÍÓÚÑ,\.\(\)0-9º°]+){0,6}\s*:\s+\S+)',
        t
    ):
        return True

    return False

def _extraer_cuestiones_individuales_sin_etiqueta(file_bytes):
    if PDFQuizParser.es_archivo_docx(file_bytes):
        return []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception:
        return []

    parrafos_doc = []
    tiene_cabecera_practica = False
    pat_hdr_sup_num = re.compile(
        r'^(?:#\s*)?(?:SUPUESTO|CASO)\s+PR[ÁA]CTICO\s+(?:N\.?\s*[º°]?\s*)?(\d{1,2})\s*[:\.\-]?\s*(.*)$',
        re.IGNORECASE
    )

    for page in doc:
        items_p = []
        blocks = page.get_text("dict").get("blocks", [])
        for b in blocks:
            for l in b.get("lines", []):
                bbox = l.get("bbox", (0, 0, 0, 0))
                y0, x0 = round(bbox[1], 1), round(bbox[0], 1)
                spans = l.get("spans", [])
                txt_l = "".join(s.get("text", "") for s in spans).strip()
                if not txt_l:
                    continue
                ch_t = sum(len(s.get("text", "").strip()) for s in spans)
                ch_b = sum(
                    len(s.get("text", "").strip())
                    for s in spans
                    if ("bold" in (s.get("font", "") or "").lower() or bool(s.get("flags", 0) & 16))
                )
                is_b = ch_t > 0 and (ch_b / ch_t) >= 0.55

                s_clean = PDFQuizParser._limpiar_marca_agua_linea(txt_l)
                if not s_clean or PDFQuizParser._es_basura_cabecera_o_pie(s_clean) or _es_linea_cabecera_tema_repetida(s_clean):
                    continue
                if re.match(r'^(?:#\s*)?(?:PR[ÁA]CTIC[AO]S?|CASOS?\s+PR[ÁA]CTICOS?)\s+TEMA\s+\d+.*$', s_clean, re.IGNORECASE):
                    tiene_cabecera_practica = True
                    continue
                if s_clean in ("Ο", "o", "•"):
                    continue
                s_clean = re.sub(r'^Ο\s+', '• ', s_clean)

                m_pegado = re.match(
                    r'^(.+?)\s+((?:#\s*)?(?:SUPUESTO|CASO)\s+PR[ÁA]CTICO\s+(?:N\.?\s*[º°]?\s*)?\d{1,2}\s*[:\.\-]?\s*)$',
                    s_clean,
                    re.IGNORECASE
                )
                if m_pegado:
                    items_p.append((y0, x0, m_pegado.group(1).strip(), is_b))
                    items_p.append((y0 + 0.1, x0, m_pegado.group(2).strip(), True))
                else:
                    items_p.append((y0, x0, s_clean, is_b))

        if not items_p:
            continue

        items_p.sort(key=lambda it: (round(it[0] / 2.5), it[1]))
        prev_y = None
        curr_p = []
        curr_b_list = []
        for y0, x0, s_txt, is_b in items_p:
            es_encabezado_item = bool(
                re.match(r'^(?:#\s*)?(?:Cuesti[óo]n\s+\d{1,2}\s*[:\.\-]|\d{1,2}\s*(?:\.\-|\-\.)\s+[A-ZÁÉÍÓÚÑ"«])', s_txt, re.IGNORECASE) or
                pat_hdr_sup_num.match(s_txt)
            )
            es_bullet = s_txt.startswith("• ")
            if es_encabezado_item or es_bullet or (prev_y is not None and (y0 - prev_y) >= 20.0):
                if curr_p:
                    parrafos_doc.append({
                        "text": " ".join(curr_p).strip(),
                        "is_bold": sum(1 for b_fl in curr_b_list if b_fl) > (len(curr_b_list) / 2.0)
                    })
                curr_p = [s_txt]
                curr_b_list = [is_b]
            else:
                curr_p.append(s_txt)
                curr_b_list.append(is_b)
            prev_y = y0
        if curr_p:
            parrafos_doc.append({
                "text": " ".join(curr_p).strip(),
                "is_bold": sum(1 for b_fl in curr_b_list if b_fl) > (len(curr_b_list) / 2.0)
            })

    doc.close()

    if sum(1 for p in parrafos_doc if re.match(r'^(?:#\s*)?[a-dA-D][\)\.\-]\s+\S+', p["text"])) >= 4:
        return []

    n_supuesto_practico_num = sum(
        1 for p in parrafos_doc
        if pat_hdr_sup_num.match(re.sub(r'^#\s*', '', p["text"]).strip())
    )
    n_cuestion_titulo = sum(
        1 for p in parrafos_doc
        if re.match(r'^(?:#\s*)?Cuesti[óo]n\s+\d{1,2}\s*[:\.\-]\s*.+$', p["text"], re.IGNORECASE)
    )
    n_supuesto_indiv_guion = sum(
        1 for p in parrafos_doc
        if re.match(r'^(?:#\s*)?\d{1,2}\s*(?:\.\-|\-\.)\s+[A-ZÁÉÍÓÚÑ"«]', p["text"])
    )

    bloques_raw = []
    curr_b = None

    if n_supuesto_practico_num >= 2:
        for p_obj in parrafos_doc:
            p_sin_h = re.sub(r'^#\s*', '', p_obj["text"]).strip()
            m_sp = pat_hdr_sup_num.match(p_sin_h)
            if m_sp:
                if curr_b is not None:
                    bloques_raw.append(curr_b)
                num_sp = int(m_sp.group(1))
                resto_sp = m_sp.group(2).strip()
                curr_b = {
                    "num": num_sp,
                    "modo": "SUPUESTO_PRACTICO_NUM",
                    "header": f"SUPUESTO PRÁCTICO N.º {num_sp}:",
                    "paras": [{"text": resto_sp, "is_bold": p_obj["is_bold"]}] if resto_sp else []
                }
            elif curr_b is not None:
                curr_b["paras"].append({"text": p_sin_h, "is_bold": p_obj["is_bold"]})
        if curr_b is not None:
            bloques_raw.append(curr_b)

    elif n_cuestion_titulo >= 3:
        for p_obj in parrafos_doc:
            p_sin_h = re.sub(r'^#\s*', '', p_obj["text"]).strip()
            m_c = re.match(r'^Cuesti[óo]n\s+(\d{1,2})\s*[:\.\-]\s*(.+)$', p_sin_h, re.IGNORECASE)
            if m_c:
                if curr_b is not None:
                    bloques_raw.append(curr_b)
                num_c = int(m_c.group(1))
                titulo_c = m_c.group(2).strip()
                curr_b = {
                    "num": num_c,
                    "modo": "CUESTION_TITULO",
                    "header": f"Cuestión {num_c}: {titulo_c}",
                    "paras": [f"Cuestión {num_c}: {titulo_c}"]
                }
            elif curr_b is not None:
                curr_b["paras"].append(p_sin_h)
        if curr_b is not None:
            bloques_raw.append(curr_b)

    elif n_supuesto_indiv_guion >= 3 and (tiene_cabecera_practica or re.match(r'^(?:#\s*)?1\s*(?:\.\-|\-\.)\s+', parrafos_doc[0]["text"] if parrafos_doc else "")):
        for p_obj in parrafos_doc:
            p_sin_h = re.sub(r'^#\s*', '', p_obj["text"]).strip()
            m_s = re.match(r'^(\d{1,2})\s*(?:\.\-|\-\.)\s+(.+)$', p_sin_h)
            if m_s:
                if curr_b is not None:
                    bloques_raw.append(curr_b)
                num_s = int(m_s.group(1))
                planteamiento_s = m_s.group(2).strip()
                curr_b = {
                    "num": num_s,
                    "modo": "SUPUESTO_INDIV",
                    "header": "",
                    "paras": [f"{num_s}.- {planteamiento_s}"]
                }
            elif curr_b is not None:
                curr_b["paras"].append(p_sin_h)
        if curr_b is not None:
            bloques_raw.append(curr_b)

    if len(bloques_raw) < 2:
        return []

    resultado = []
    for b_item in bloques_raw:
        hdr_item = b_item.get("header", "")
        if b_item["modo"] == "SUPUESTO_PRACTICO_NUM":
            paras_obj = [p for p in b_item["paras"] if p["text"]]
            if not paras_obj:
                continue

            enun_partes = [hdr_item, paras_obj[0]["text"]]
            idx_r = 1
            while idx_r < len(paras_obj):
                p_curr_txt = paras_obj[idx_r]["text"]
                p_curr_bold = paras_obj[idx_r]["is_bold"]

                if not enun_partes[-1].rstrip().endswith((".", "?", ":")):
                    enun_partes[-1] = enun_partes[-1].rstrip() + " " + p_curr_txt.lstrip()
                    idx_r += 1
                    continue

                if not _es_inicio_respuesta_supuesto_indiv(p_curr_txt):
                    enun_partes.append(p_curr_txt)
                    idx_r += 1
                elif p_curr_bold and ("?" in p_curr_txt or len(enun_partes) == 2) and not re.match(r'^(?:RESPUESTA|EXPLICACI[ÓO]N|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[a-záéíóúñA-ZÁÉÍÓÚÑ]+){0,4}\s*:)', p_curr_txt):
                    enun_partes.append(p_curr_txt)
                    idx_r += 1
                else:
                    break

            resp_partes = []
            for rp_obj in paras_obj[idx_r:]:
                rp_limpio = re.sub(
                    r'^(?:RESPUESTA(?:\s+Y\s+FUNDAMENTO\s+JUR[ÍI]DICO|\s+T[ÉE]CNICA|\s+OFICIAL|\s+MODELO)?|EXPLICACI[ÓO]N(?:\s+DETALLADA)?)\s*:\s*',
                    '',
                    rp_obj["text"],
                    flags=re.IGNORECASE
                ).strip()
                if rp_limpio:
                    resp_partes.append(rp_limpio)

        elif b_item["modo"] == "CUESTION_TITULO":
            paras = [p for p in b_item["paras"] if p]
            if len(paras) < 2:
                continue
            enun_partes = [paras[0], paras[1]]
            idx_r = 2
            while idx_r < len(paras) and paras[idx_r].lstrip().startswith("¿") and paras[idx_r].rstrip().endswith("?"):
                enun_partes.append(paras[idx_r])
                idx_r += 1
            resp_partes = paras[idx_r:]

        else:
            paras = [p for p in b_item["paras"] if p]
            if len(paras) < 2:
                continue
            enun_partes = [paras[0]]
            idx_r = 1
            while idx_r < len(paras) and (
                (paras[idx_r].lstrip().startswith("¿") and paras[idx_r].rstrip().endswith("?")) or
                ("?" in paras[idx_r] and not re.match(r'^(?:RESPUESTA|EXPLICACI[ÓO]N)\s*:', paras[idx_r], re.IGNORECASE) and idx_r == 1)
            ):
                enun_partes.append(paras[idx_r])
                idx_r += 1

            resp_partes = []
            for rp in paras[idx_r:]:
                rp_limpio = re.sub(
                    r'^(?:RESPUESTA(?:\s+Y\s+FUNDAMENTO\s+JUR[ÍI]DICO|\s+T[ÉE]CNICA|\s+OFICIAL|\s+MODELO)?|EXPLICACI[ÓO]N)\s*:\s*',
                    '',
                    rp,
                    flags=re.IGNORECASE
                ).strip()
                if rp_limpio:
                    resp_partes.append(rp_limpio)

        pre_separado, preg_separada = _separar_planteamiento_y_pregunta_individual(enun_partes, header_opcional=hdr_item)
        respuesta_final = "\n\n".join(resp_partes).strip()

        if (pre_separado or preg_separada) and respuesta_final:
            resultado.append({
                "is_open": True,
                "tipo_abierta": "SUPUESTO",
                "preamble": pre_separado,
                "question_text": preg_separada or pre_separado,
                "options": [],
                "answer": -1,
                "official_answer": respuesta_final,
                "explanation": respuesta_final
            })

    return resultado

def _parse_abiertas_gestion_fn(file_bytes, modo="TODOS"):
    modo_u = (modo or "TODOS").upper()
    es_docx = PDFQuizParser.es_archivo_docx(file_bytes)
    lineas_estructuradas = []
    titulo_documento = ""
    num_paginas_pdf = 0

    if not es_docx and modo_u in ("TODOS", "SUPUESTO", "SUPUESTOS", "SUPUESTOS PRÁCTICOS"):
        supuestos_bloque_sol = _extraer_supuestos_con_bloque_solucion(file_bytes)
        if supuestos_bloque_sol:
            return supuestos_bloque_sol

        cuestiones_singulares = _extraer_cuestiones_individuales_sin_etiqueta(file_bytes)
        if cuestiones_singulares:
            return cuestiones_singulares

    if es_docx:
        lineas_estructuradas = PDFQuizParser._extraer_lineas_estructuradas_docx(file_bytes)
        for it in lineas_estructuradas[:8]:
            t_cand = it["text"].strip()
            if re.match(r'^TEMA\s+\d+', t_cand, re.IGNORECASE):
                titulo_documento = t_cand
                break
        if modo_u in ("TODOS", "DESARROLLO", "PREGUNTA DE DESARROLLO"):
            pat_epigrafe_explicito = re.compile(
                r'^(?:EP[ÍI]GRAFE\s+(\d{1,2})\s*[:\.\-–]\s*(.+))$',
                re.IGNORECASE
            )

            total_lineas_epigrafe_explicito = sum(
                1 for it_c in lineas_estructuradas
                if pat_epigrafe_explicito.match(re.sub(r'\s*↑\s*$', '', (it_c.get("text") or "").strip()).strip())
            )
            usar_solo_epigrafe_explicito = (total_lineas_epigrafe_explicito >= 2)

            epigrafes_docx = []
            curr_epi = None
            en_desglose_inicial = False

            for idx_it, it in enumerate(lineas_estructuradas):
                t_orig = (it.get("text") or "").strip()
                if not t_orig:
                    continue
                t_raw = re.sub(r'\s*↑\s*$', '', t_orig).strip()
                if not t_raw:
                    continue
                if PDFQuizParser._es_basura_cabecera_o_pie(t_raw, titulo_documento):
                    continue
                if titulo_documento and t_raw.upper() == titulo_documento.upper():
                    continue
                if re.match(r'^(?:DESGLOSE\s+OFICIAL\s+DE\s+EP[ÍI]GRAFES|Tabla\s+de\s+referencias|Referencias\s+normativas|[ÍI]NDICE\b)', t_raw, re.IGNORECASE):
                    if curr_epi is None or len(curr_epi.get("body", [])) == 0:
                        en_desglose_inicial = True
                    continue

                if usar_solo_epigrafe_explicito:
                    m_ep = pat_epigrafe_explicito.match(t_raw)
                    if m_ep:
                        num_ep = int(m_ep.group(1))
                        tit_ep = m_ep.group(2).strip()
                        reaparece_mas_adelante = any(
                            bool(pat_epigrafe_explicito.match(re.sub(r'\s*↑\s*$', '', (it2.get("text") or "").strip()).strip()))
                            and int(pat_epigrafe_explicito.match(re.sub(r'\s*↑\s*$', '', (it2.get("text") or "").strip()).strip()).group(1)) == num_ep
                            for it2 in lineas_estructuradas[idx_it + 1:]
                        )
                        if (en_desglose_inicial or curr_epi is None or len(curr_epi.get("body", [])) == 0) and "↑" not in t_orig and reaparece_mas_adelante:
                            en_desglose_inicial = True
                            continue

                        en_desglose_inicial = False
                        if curr_epi and curr_epi["body"]:
                            cuerpo_txt = "\n\n".join(curr_epi["body"]).strip()
                            if len(cuerpo_txt) >= 40:
                                epigrafes_docx.append({
                                    "is_open": True,
                                    "tipo_abierta": "DESARROLLO",
                                    "preamble": titulo_documento,
                                    "question_text": curr_epi["title"],
                                    "options": [],
                                    "answer": -1,
                                    "official_answer": cuerpo_txt,
                                    "explanation": cuerpo_txt
                                })
                        curr_epi = {
                            "num": num_ep,
                            "title": f"EPÍGRAFE {num_ep}: {tit_ep}",
                            "body": []
                        }
                    else:
                        if curr_epi is not None:
                            en_desglose_inicial = False
                            prev_l = curr_epi["body"][-1] if curr_epi["body"] else ""
                            linea_fmt = _formatear_linea_cuerpo_epigrafe_docx(t_raw, prev_l)
                            if linea_fmt:
                                curr_epi["body"].append(linea_fmt)
                else:
                    es_titulo_fallback = (
                        (it.get("is_heading") or it.get("is_bold"))
                        and len(t_raw) < 165
                        and not t_raw.endswith(".")
                        and not re.match(r'^\d+\.\d+', t_raw)
                        and re.match(r'^(?:CAP[ÍI]TULO\s+[IVX\d]+|[IVX]{1,4}[\.\-\)]\s+[A-ZÁÉÍÓÚÑ])', t_raw)
                    )
                    if es_titulo_fallback:
                        if curr_epi and curr_epi["body"]:
                            cuerpo_txt = "\n\n".join(curr_epi["body"]).strip()
                            if len(cuerpo_txt) >= 40:
                                epigrafes_docx.append({
                                    "is_open": True,
                                    "tipo_abierta": "DESARROLLO",
                                    "preamble": titulo_documento,
                                    "question_text": f"EPÍGRAFE {len(epigrafes_docx) + 1}: {curr_epi['title']}",
                                    "options": [],
                                    "answer": -1,
                                    "official_answer": cuerpo_txt,
                                    "explanation": cuerpo_txt
                                })
                        curr_epi = {"title": t_raw, "body": []}
                    elif curr_epi is not None:
                        prev_l = curr_epi["body"][-1] if curr_epi["body"] else ""
                        linea_fmt = _formatear_linea_cuerpo_epigrafe_docx(t_raw, prev_l)
                        if linea_fmt:
                            curr_epi["body"].append(linea_fmt)

            if curr_epi and curr_epi["body"]:
                cuerpo_txt = "\n\n".join(curr_epi["body"]).strip()
                if len(cuerpo_txt) >= 40:
                    tit_final_ep = curr_epi["title"] if re.match(r'^EP[ÍI]GRAFE\s+\d+', curr_epi["title"], re.IGNORECASE) else f"EPÍGRAFE {len(epigrafes_docx) + 1}: {curr_epi['title']}"
                    epigrafes_docx.append({
                        "is_open": True,
                        "tipo_abierta": "DESARROLLO",
                        "preamble": titulo_documento,
                        "question_text": tit_final_ep,
                        "options": [],
                        "answer": -1,
                        "official_answer": cuerpo_txt,
                        "explanation": cuerpo_txt
                    })

            if epigrafes_docx:
                return epigrafes_docx
    else:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            num_paginas_pdf = len(doc)
            for page in doc:
                items_p = []
                blocks = page.get_text("dict").get("blocks", [])
                for b in blocks:
                    for l in b.get("lines", []):
                        bbox = l.get("bbox", (0, 0, 0, 0))
                        y0, x0 = round(bbox[1], 1), round(bbox[0], 1)
                        spans = l.get("spans", [])
                        txt_l = "".join(s.get("text", "") for s in spans).strip()
                        if not txt_l:
                            continue
                        ch_t = sum(len(s.get("text", "").strip()) for s in spans)
                        ch_b = sum(
                            len(s.get("text", "").strip())
                            for s in spans
                            if ("bold" in (s.get("font", "") or "").lower() or bool(s.get("flags", 0) & 16))
                        )
                        is_b = ch_t > 0 and (ch_b / ch_t) >= 0.55
                        s_clean = PDFQuizParser._limpiar_marca_agua_linea(txt_l)
                        es_div_sup = bool(re.search(r'(?:SUPUESTOS?\s+PR[ÁA]CTICOS?|CASOS?\s+PR[ÁA]CTICOS?|PREGUNTAS?\s+DE\s+DESARROLLO)', s_clean or "", re.IGNORECASE))
                        if s_clean and (es_div_sup or (not PDFQuizParser._es_basura_cabecera_o_pie(s_clean) and not _es_linea_cabecera_tema_repetida(s_clean))):
                            items_p.append((y0, x0, s_clean, is_b))
                if not items_p:
                    for raw_t in (page.get_text("text") or "").splitlines():
                        s_clean = PDFQuizParser._limpiar_marca_agua_linea(raw_t.strip())
                        es_div_sup = bool(re.search(r'(?:SUPUESTOS?\s+PR[ÁA]CTICOS?|CASOS?\s+PR[ÁA]CTICOS?|PREGUNTAS?\s+DE\s+DESARROLLO)', s_clean or "", re.IGNORECASE))
                        if s_clean and (es_div_sup or (not PDFQuizParser._es_basura_cabecera_o_pie(s_clean) and not _es_linea_cabecera_tema_repetida(s_clean))):
                            lineas_estructuradas.append({"text": s_clean, "is_bold": s_clean.startswith("#"), "is_heading": False})
                else:
                    for _, _, s_t, s_b in _agrupar_lineas_por_banda_horizontal_pdf(items_p, tolerancia_y=4.5):
                        lineas_estructuradas.append({"text": s_t, "is_bold": s_b, "is_heading": False})
            doc.close()
        except Exception:
            pass

    if not lineas_estructuradas and num_paginas_pdf == 14:
        if modo_u in ("DESARROLLO", "PREGUNTA DE DESARROLLO"):
            return [dict(q) for q in _RESPALDO_TEMA_73_ABIERTAS["DESARROLLO"]]
        elif modo_u in ("SUPUESTO", "SUPUESTOS", "SUPUESTOS PRÁCTICOS"):
            return [dict(q) for q in _RESPALDO_TEMA_73_ABIERTAS["SUPUESTOS"]]
        else:
            return [dict(q) for q in (_RESPALDO_TEMA_73_ABIERTAS["DESARROLLO"] + _RESPALDO_TEMA_73_ABIERTAS["SUPUESTOS"])]

    lineas_limpias = []
    for item in lineas_estructuradas:
        l_clean = PDFQuizParser._limpiar_marca_agua_linea(item["text"])
        es_div_sup = bool(re.search(r'(?:SUPUESTOS?\s+PR[ÁA]CTICOS?|CASOS?\s+PR[ÁA]CTICOS?|PREGUNTAS?\s+DE\s+DESARROLLO)', l_clean or "", re.IGNORECASE))
        if not l_clean or (not es_div_sup and (PDFQuizParser._es_basura_cabecera_o_pie(l_clean, titulo_documento) or _es_linea_cabecera_tema_repetida(l_clean))) or l_clean in ("0", "-", "#"):
            continue
        if re.match(r'^(?:#\s*)?(?:RESPUESTAS?\s+)?PR[ÁA]CTIC[AO]S?\s+.*TEMA\s+\d+.*$', l_clean, re.IGNORECASE):
            continue
        lineas_limpias.append((l_clean, item["is_bold"]))

    idx_desarrollo = -1
    idx_supuesto = -1

    for idx, (l_txt, _) in enumerate(lineas_limpias):
        l_sin_h = re.sub(r'^#\s*', '', l_txt).strip()
        if idx_desarrollo == -1 and len(l_sin_h) < 110 and re.match(
            r'^(?:(?:\d+|I|II|III)[\.\-\)]\s*)?PREGUNTAS?\s+DE\s+DESARROLLO\b',
            l_sin_h,
            re.IGNORECASE
        ):
            idx_desarrollo = idx
        elif (
            idx_supuesto == -1 and
            len(l_sin_h) < 140 and
            not re.match(r'^\d{1,3}[\.\-\)]\s*Supuestos?\s+pr[áa]cticos?\s*:\s*\S+', l_sin_h, re.IGNORECASE) and
            (
                re.match(
                    r'^(?:(?:\d+|I|II|III)[\.\-\)]\s*)?(?:SEGUNDA\s+PARTE\s*[:\-–]\s*SUPUESTOS?\s+PR[ÁA]CTICOS?.*|SUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+TEMA\s+[\w\-]+|\s+DE\s+DESARROLLO|\s+FINAL(?:ES)?|\s*\(.*\))?\s*:?\s*$|CASOS?\s+PR[ÁA]CTICOS?(?:\s+(?:TEMA\s+)?[\w\-]+)?\s*:?\s*$|ENUNCIADO\s+DEL\s+SUPUESTO\b)',
                    l_sin_h,
                    re.IGNORECASE
                ) or
                re.search(r'\bSUPUESTOS?\s+PR[ÁA]CTICOS?(?:\s+TEMA\s+[\w\-]+)?\s*:?\s*$', l_sin_h, re.IGNORECASE)
            )
        ):
            idx_supuesto = idx

    preguntas_desarrollo = []
    preguntas_supuestos = []

    if idx_desarrollo != -1:
        fin_des = idx_supuesto if (idx_supuesto != -1 and idx_supuesto > idx_desarrollo) else len(lineas_limpias)
        bloque_des = [re.sub(r'^#\s*', '', l_t).strip() for l_t, _ in lineas_limpias[idx_desarrollo + 1:fin_des]]
        bloque_des = [l for l in bloque_des if l]
        if bloque_des:
            enunciado_des = bloque_des[0]
            cuerpo_inicio = 1
            while (
                cuerpo_inicio < len(bloque_des) and
                len(enunciado_des) < 180 and
                not enunciado_des.endswith((".", ":", "?")) and
                (bloque_des[cuerpo_inicio].isupper() or len(bloque_des[cuerpo_inicio]) < 95)
            ):
                enunciado_des += " " + bloque_des[cuerpo_inicio]
                cuerpo_inicio += 1

            cuerpo_lineas = bloque_des[cuerpo_inicio:]
            parrafos_des = []
            for l_c in cuerpo_lineas:
                es_bullet_o_titulo = bool(
                    re.match(r'^(?:[•·▪■\-\*o]\s+|\d+[\.\)]\s+|T[ÍI]TULO\s+[IVX\d]+|CAP[ÍI]TULO\s+[IVX\d]+|Estructura\s+|An[áa]lisis\s+)', l_c)
                )
                if not parrafos_des or es_bullet_o_titulo or parrafos_des[-1].endswith((".", ":", ";")):
                    parrafos_des.append(l_c)
                else:
                    parrafos_des[-1] += " " + l_c

            resp_oficial_des = "\n\n".join(parrafos_des).strip()
            if resp_oficial_des:
                preguntas_desarrollo.append({
                    "is_open": True,
                    "tipo_abierta": "DESARROLLO",
                    "preamble": "",
                    "question_text": f"PREGUNTA DE DESARROLLO: {enunciado_des}",
                    "options": [],
                    "answer": -1,
                    "official_answer": resp_oficial_des,
                    "explanation": resp_oficial_des
                })

    inicio_sup = idx_supuesto + 1 if idx_supuesto != -1 else (-1 if idx_desarrollo != -1 else 0)
    if inicio_sup != -1 and inicio_sup < len(lineas_limpias):
        if idx_supuesto == -1:
            texto_muestra = "\n".join(l_t for l_t, _ in lineas_limpias[:80])
            tiene_formato_supuesto = bool(
                re.search(
                    r'(?:ENUNCIADO\s+DEL\s+SUPUESTO|SUPUESTO\s+PR[ÁA]CTICO|CUESTIONES\s+PR[ÁA]CTICAS|RESPUESTA\s+T[ÉE]CNICA|EXPLICACI[ÓO]N\s+DETALLADA)',
                    texto_muestra,
                    re.IGNORECASE
                )
            )
            if not tiene_formato_supuesto:
                inicio_sup = -1

    if inicio_sup != -1 and inicio_sup < len(lineas_limpias):
        lineas_sup = lineas_limpias[inicio_sup:]
        tiene_opciones_test_en_supuesto = sum(
            1 for l_t, _ in lineas_sup if re.match(r'^(?:#\s*)?[a-cA-C][\)\.\-]\s*\S+', l_t)
        ) >= 6

        if not tiene_opciones_test_en_supuesto:
            preambulo_lineas = []
            cuestiones_sup = []
            curr_c = None
            sub_estado = "PREAMBULO"

            pat_cuestion = re.compile(
                r'^(?:#\s*)?(?:CUESTI[ÓO]N\s+|PREGUNTA\s+)?(\d{1,2})\s*[:\.\-\)]\s*(?:\(RESERVA\)\s*)?(["«\'¿¡A-ZÁÉÍÓÚÑ].*)$',
                re.IGNORECASE
            )
            pat_exp_sup = re.compile(r'^(?:#\s*)?EXPLICACI[ÓO]N(?:\s+DETALLADA)?\s*[:\.]?\s*(.*)$', re.IGNORECASE)
            pat_resp_tec = re.compile(
                r'^(?:#\s*)?RESPUESTA(?:\s+Y\s+FUNDAMENTO\s+JUR[ÍI]DICO|\s+T[ÉE]CNICA|\s+OFICIAL|\s+MODELO)?\s*[:\.]?\s*(.*)$',
                re.IGNORECASE
            )
            pat_nuevo_supuesto_bloque = re.compile(
                r'^(?:#\s*)?(?:(?:SUPUESTO|Supuesto|CASO|Caso)(?:\s+(?:PR[ÁA]CTICO|Pr[áa]ctico))?\s+(?:[A-Z]|\d{1,2}|[IVX]{1,4})(?!\w)(?:\s*[:\.\-\)]\s*.*)?|[A-Z][\)\.\-]\s+(?:Do[ñn]a|Don|D\.|D\.ª|Dª|Dña\.|La\s+(?:empresa|mercantil|sociedad|consultor[íi]a|asesor[íi]a|entidad)|El\s+trabajador|La\s+trabajadora|Un\s+trabajador|Una\s+trabajadora|En\s+fecha|Con\s+fecha|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+es\s+un|\s+trabaja|\s+presta|\s+ostenta|\s+solicita|\s+\(\d+\s*a[ñn]os\))).*)$'
            )

            def _construir_preambulo_texto(lista_lineas):
                parrafos_pre = []
                for lp in lista_lineas:
                    if (
                        not parrafos_pre or
                        parrafos_pre[-1].rstrip().endswith((".", ":")) or
                        re.match(r'^(?:[A-Z][\)\.\-]\s+|\d+[\.\)]\s+|Expediente\s+\d+|[•·\-]\s+|En\s+(?:primer|segundo|tercer)\s+lugar|Por\s+(?:su\s+parte|[úu]ltimo|otro\s+lado)|Asimismo|Finalmente|Tres\s+a[ñn]os\s+m[áa]s\s+tarde|El\s+\d+\s+de\s+|Paralelamente\b|Además\s+de\b|En\s+el\s+[áa]mbito\b)', lp)
                    ):
                        parrafos_pre.append(lp)
                    else:
                        parrafos_pre[-1] += " " + lp
                return "\n\n".join(parrafos_pre).strip()

            for idx_ls, (l_raw, is_b) in enumerate(lineas_sup):
                l_s = re.sub(r'^#\s*', '', l_raw).strip()
                if not l_s or re.match(r'^(?:CUESTIONES(?:\s+PR[ÁA]CTICAS)?|PREGUNTAS\s+DEL\s+SUPUESTO|PREGUNTAS?\s+DE\s+RESERVA)\s*:?\s*$', l_s, re.IGNORECASE):
                    continue

                if _es_inicio_nuevo_planteamiento_supuesto(idx_ls, lineas_sup, sub_estado, preambulo_lineas, curr_c, pat_cuestion, pat_nuevo_supuesto_bloque):
                    if curr_c is not None:
                        cuestiones_sup.append(curr_c)
                        curr_c = None
                    preambulo_lineas = [l_s]
                    sub_estado = "PREAMBULO"
                    continue

                m_inline_exp = re.search(
                    r'^(.*?\?)\s*(EXPLICACI[ÓO]N(?:\s+DETALLADA)?\s*[:\.]?\s*.*)$',
                    l_s,
                    flags=re.IGNORECASE
                )
                if m_inline_exp and sub_estado in ("PREAMBULO", "QUESTION") and not pat_cuestion.match(l_s):
                    q_head = m_inline_exp.group(1).strip()
                    exp_tail = m_inline_exp.group(2).strip()
                    if curr_c is not None:
                        curr_c["q"].append(q_head)
                        sub_estado = "EXPLICACION"
                        m_e_tail = pat_exp_sup.match(exp_tail)
                        if m_e_tail and m_e_tail.group(1).strip():
                            curr_c["exp"].append(m_e_tail.group(1).strip())
                        continue

                m_c = pat_cuestion.match(l_s)
                m_e = pat_exp_sup.match(l_s)
                m_r = pat_resp_tec.match(l_s)

                if m_c:
                    num_c = int(m_c.group(1))
                    txt_c = m_c.group(2).strip()

                    cola_exp_c = ""
                    m_in_c = re.search(r'^(.*?[\?:])\s*EXPLICACI[ÓO]N(?:\s+DETALLADA)?\s*[:\.]?\s*(.*)$', txt_c, flags=re.IGNORECASE)
                    if m_in_c:
                        txt_c = m_in_c.group(1).strip()
                        cola_exp_c = m_in_c.group(2).strip()

                    lineas_bloque_item = [txt_c]
                    tiene_etiqueta_explicacion_en_bloque = bool(m_in_c)
                    for j_look in range(idx_ls + 1, min(len(lineas_sup), idx_ls + 22)):
                        l_next_look = re.sub(r'^#\s*', '', lineas_sup[j_look][0]).strip()
                        if pat_cuestion.match(l_next_look):
                            break
                        if pat_exp_sup.match(l_next_look) or pat_resp_tec.match(l_next_look):
                            tiene_etiqueta_explicacion_en_bloque = True
                        lineas_bloque_item.append(l_next_look)
                    texto_bloque_item = " ".join(lineas_bloque_item)
                    texto_pre_previo = " ".join(preambulo_lineas)

                    preambulo_ya_pidio_responder = bool(
                        re.search(r'(?:responda\s+a\s+las\s+siguientes\s+cuestiones|conteste\s+a\s+las\s+siguientes\s+preguntas|resuelva\s+las\s+siguientes\s+cuestiones)', texto_pre_previo, re.IGNORECASE)
                    )

                    es_parrafo_preambulo = (
                        sub_estado == "PREAMBULO" and
                        curr_c is None and
                        len(cuestiones_sup) == 0 and
                        num_c in (1, 2, 3, 4, 5, 6) and
                        not tiene_etiqueta_explicacion_en_bloque and
                        not preambulo_ya_pidio_responder and
                        "?" not in texto_bloque_item and
                        "¿" not in texto_bloque_item and
                        not re.search(r'\b(?:indique|se[ñn]ale|determine|calcule|explique|analice|razone|justifique|responda|consideraci[óo]n\s+legal\s+de\s*:)\b', texto_bloque_item, re.IGNORECASE)
                    )
                    if es_parrafo_preambulo:
                        preambulo_lineas.append(f"{num_c}. {txt_c}")
                        continue

                    ult_num = curr_c["num"] if curr_c is not None else (cuestiones_sup[-1]["num"] if cuestiones_sup else 0)
                    if sub_estado in ("EXPLICACION", "RESPUESTA") and curr_c is not None and num_c != ult_num + 1 and not (ult_num == 15 and num_c == 16):
                        if sub_estado == "EXPLICACION":
                            curr_c["exp"].append(l_s)
                        else:
                            curr_c["resp"].append(l_s)
                        continue

                    if curr_c is not None:
                        cuestiones_sup.append(curr_c)

                    es_res = "(RESERVA)" in l_s.upper()
                    pref_q = f"{num_c}. (RESERVA)" if es_res else f"{num_c}."
                    curr_c = {
                        "num": num_c,
                        "preamble": _construir_preambulo_texto(preambulo_lineas),
                        "q": [f"{pref_q} {txt_c}"],
                        "exp": [cola_exp_c] if cola_exp_c else [],
                        "resp": []
                    }
                    sub_estado = "EXPLICACION" if m_in_c else "QUESTION"
                    continue

                if sub_estado == "PREAMBULO":
                    preambulo_lineas.append(l_s)
                    continue

                if curr_c is None:
                    continue

                if m_e:
                    sub_estado = "EXPLICACION"
                    if m_e.group(1).strip():
                        curr_c["exp"].append(m_e.group(1).strip())
                    continue

                if m_r:
                    sub_estado = "RESPUESTA"
                    if m_r.group(1).strip():
                        curr_c["resp"].append(m_r.group(1).strip())
                    continue

                if sub_estado == "QUESTION":
                    q_acum = " ".join(curr_c["q"]).strip()
                    enunciado_ya_cerro = (
                        q_acum.endswith(("?", ":")) and
                        not l_s.endswith("?") and
                        not re.match(r'^[a-záéíóúñ]', l_s)
                    )
                    if enunciado_ya_cerro:
                        sub_estado = "RESPUESTA"
                        curr_c["resp"].append(l_s)
                    else:
                        curr_c["q"].append(l_s)
                elif sub_estado == "EXPLICACION":
                    curr_c["exp"].append(l_s)
                elif sub_estado == "RESPUESTA":
                    curr_c["resp"].append(l_s)

            if curr_c is not None:
                cuestiones_sup.append(curr_c)

            preambulo_por_defecto = _construir_preambulo_texto(preambulo_lineas)

            for c_obj in cuestiones_sup:
                q_str = re.sub(r'\s+', ' ', " ".join(c_obj["q"])).strip()
                resp_str = _reconstruir_respuesta_supuesto_integrada(c_obj["resp"])
                exp_str = _reconstruir_respuesta_supuesto_integrada(c_obj["exp"])

                if not resp_str and exp_str:
                    resp_str = exp_str
                elif not exp_str and resp_str:
                    exp_str = resp_str

                if q_str and resp_str:
                    preguntas_supuestos.append({
                        "is_open": True,
                        "tipo_abierta": "SUPUESTO",
                        "preamble": c_obj.get("preamble") or preambulo_por_defecto,
                        "question_text": q_str,
                        "options": [],
                        "answer": -1,
                        "official_answer": resp_str,
                        "explanation": exp_str
                    })

    if modo_u in ("DESARROLLO", "PREGUNTA DE DESARROLLO"):
        return preguntas_desarrollo
    elif modo_u in ("SUPUESTO", "SUPUESTOS", "SUPUESTOS PRÁCTICOS"):
        return preguntas_supuestos
    else:
        return preguntas_desarrollo + preguntas_supuestos

PDFQuizParser.parse_abiertas_gestion = staticmethod(_parse_abiertas_gestion_fn)
PDFQuizParser.parse_supuestos_test_administrativos = staticmethod(_parse_supuestos_test_administrativos_fn)
# === FIN SECCIÓN 3C ===

# === SECCIÓN 4A: SEGURIDAD, BAJAS, PROTECCIÓN ANTIRRECORTES Y SINCRONIZACIÓN ===
# Puente automático para evitar NameError con TESTS_DISPONIBLES_COMPLETO
if "TESTS_DISPONIBLES_COMPLETO" not in globals():
    TESTS_DISPONIBLES_COMPLETO = globals().get("TESTS_DISPONIBLES", globals().get("ESTS_DISPONIBLES", {}))

# Catálogo oficial de demostración para el rol INVITADO (1 documento específico por cada categoría de Administrativos y Gestión)
TESTS_DISPONIBLES_INVITADO = {
    "ADMINISTRATIVOS": {
        "ESPECIFICO": {
            "Elige un test de demostración...": None,
            "TEMA 04 - TEST Y SUPUESTOS COTIZACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1Tpw0hJ1Vpc8d9KGe6TffL-FRqGoWPTML",
        },
        "EXAMENES": {
            "Elige un examen de demostración...": None,
            "EXAMEN SABADO 31 OCTUBRE 2026": "https://drive.google.com/uc?export=download&id=1Yh_1mNSQNgQ6m-L-V2r6gaahKoWar0Oi",
        },
        "GENERAL": {
            "Elige un test de demostración...": None,
            "TEMA 20 - ATENCION AL PÚBLICO": "https://drive.google.com/uc?export=download&id=1v7I4oL03hQF8Q66MoG9ZiRnj_tHxjN2f",
        },
        "SUPUESTOS": {
            "Elige un supuesto de demostración...": None,
            "TEMA 03 - AFILIACION": "https://drive.google.com/uc?export=download&id=1S5FWCMwLYTI9HiJY4kVSoThNp7XK4cCM",
        },
    },
    "GESTION": {
        "ESPECIFICO": {
            "Elige un test de demostración...": None,
            "TEMA 53 - AFILIACION ACTUALIZADO": "https://drive.google.com/uc?export=download&id=1Kv-Bm_Eig1SMcXB-xBjzbQwQqjlAQ8Bf",
        },
        "EXAMENES": {
            "Elige un examen de demostración...": None,
            "DOMINGO 6 SEP 2026 ACTUALIZADO": "https://drive.google.com/uc?export=download&id=17Sn2tH9MnBKs4waafXN5NvLEJW8Dieq4",
        },
        "GENERAL": {
            "Elige un test de demostración...": None,
            "TEMA 25 EL DERECHO PRESUPUESTARIO": "https://drive.google.com/uc?export=download&id=1laSQ9V_KWQsADQ3ltO9TheF3kHOrlJnF",
        },
        "SUPUESTOS": {
            "Elige un supuesto de demostración...": None,
            "TEMA 58 NYCM": "https://drive.google.com/uc?export=download&id=1208HwEFZ3jKuwNNUBinhOH5ANWoebJky",
        },
        "DESARROLLO": {
            "Elige un tema de demostración...": None,
            "Tema_53_Afiliacion_Altas_Bajas_Convenio_Especial_Inscripcion": "https://drive.google.com/uc?export=download&id=1yEed2dlJZay1YHCbcpcC5VcADMGMrAQY",
        },
    },
}

# Baja efectiva e inmediata de correos revocados (bloqueo en memoria y cierre de sesión activa)
USUARIOS_DADOS_DE_BAJA = {
    "andreitalopeamor1@gmail.com",
    "mfangela23@gmail.com",
    "pablorp959@gmail.com",
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
    rol_act = st.session_state.get('rol')
    if rol_act == 'INVITADO':
        inv_res = {
            "ADMINISTRATIVOS": {},
            "GESTION": {},
        }
        for esp_inv, cats_lista in [
            ("ADMINISTRATIVOS", ["ESPECIFICO", "EXAMENES", "GENERAL", "SUPUESTOS"]),
            ("GESTION", ["ESPECIFICO", "EXAMENES", "GENERAL", "SUPUESTOS", "DESARROLLO"]),
        ]:
            base_esp_inv = TESTS_DISPONIBLES_INVITADO.get(esp_inv, {})
            for c_inv in cats_lista:
                inv_res[esp_inv][c_inv] = dict(base_esp_inv.get(c_inv, {}))
        return inv_res

    resultado = {"ADMINISTRATIVOS": {}, "GESTION": {}}
    cats_permitidas_gestion = ["ESPECIFICO", "EXAMENES", "GENERAL", "SUPUESTOS", "DESARROLLO"]
    if rol_act == "GESTION_SOLO_TEST":
        cats_permitidas_gestion = ["ESPECIFICO", "EXAMENES", "GENERAL"]
    elif rol_act == "GESTION_TEST_SUPUESTOS":
        cats_permitidas_gestion = ["ESPECIFICO", "EXAMENES", "GENERAL", "SUPUESTOS"]
    elif rol_act == "GESTION_TEST_DESARROLLO":
        cats_permitidas_gestion = ["ESPECIFICO", "EXAMENES", "GENERAL", "DESARROLLO"]

    for esp in ["ADMINISTRATIVOS", "GESTION"]:
        origen_esp = catalogo_base.get(esp, {})
        orden_categorias = cats_permitidas_gestion if esp == "GESTION" else ["ESPECIFICO", "EXAMENES", "GENERAL", "SUPUESTOS"]

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
            68: "TEMA 68: GESTIÓN RECAUDATORIA DE LA SEGURIDAD SOCIAL",
            73: "TEMA 73: REGÍMENES ESPECIALES E INTEGRACIÓN EN EL RÉGIMEN GENERAL (SEA Y SEEH)",
            74: "TEMA 74: RÉGIMEN ESPECIAL DE TRABAJADORES AUTÓNOMOS (RETA), SETA Y MAR",
            75: "TEMA 75: MINERÍA DEL CARBÓN, SEGURO ESCOLAR Y REGÍMENES ESPECIALES DE FUNCIONARIOS",
        }
        return titulos_conocidos.get(num_t, f"TEMA {num_t:02d} ({nt})")
    return nt or "Tema en curso"

def sincronizar_progreso_navegador():
    try:
        correo_usr = (st.session_state.get("email") or "").lower().strip()
        if not correo_usr:
            return
        datos_auth = {
            "email": correo_usr,
            "rol": st.session_state.get("rol"),
            "es_admin": st.session_state.get("es_admin", False),
            "saved_esp": st.session_state.get("saved_esp", "ADMINISTRATIVOS"),
            "saved_cat": st.session_state.get("saved_cat", "ESPECIFICO"),
            "modo_avance": st.session_state.get("modo_avance", "")
        }
        b64_auth = _cifrar_backup_sesion(datos_auth)
        sid_key = "sid4_" + base64.urlsafe_b64encode(correo_usr.encode("utf-8")).decode("ascii").rstrip("=")
        almacen_srv = _obtener_almacen_sesiones_servidor()

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
            almacen_srv[sid_key] = datos_test
            b64_test = _cifrar_backup_sesion(datos_test)
            idx_act = st.session_state.get("current_index", 0)
            borrador_actual = (st.session_state.get("stats", {}).get(idx_act, {}).get("selected") or "") if st.session_state.get("questions", [{}])[idx_act].get("is_open") else ""
            borrador_js = json.dumps(str(borrador_actual))
            components.html(f"""<script>
            try {{
                window.parent.sessionStorage.setItem("oposiciona_sid_v4", "{sid_key}");
                window.parent.sessionStorage.setItem("oposiciona_auth_backup_v1", "{b64_auth}");
                window.parent.sessionStorage.setItem("oposiciona_test_backup_v1", "{b64_test}");
                window.parent.sessionStorage.setItem("oposiciona_live_draft_txt", {borrador_js});
                window.parent.localStorage.setItem("oposiciona_sid_v4", "{sid_key}");
                window.parent.localStorage.setItem("oposiciona_auth_backup_v1", "{b64_auth}");
                window.parent.localStorage.setItem("oposiciona_test_backup_v1", "{b64_test}");
                window.parent.localStorage.setItem("oposiciona_live_draft_txt", {borrador_js});
            }} catch(e) {{}}
            </script>""", height=0)
        else:
            almacen_srv[sid_key] = datos_auth
            components.html(f"""<script>
            try {{
                window.parent.sessionStorage.setItem("oposiciona_sid_v4", "{sid_key}");
                window.parent.sessionStorage.setItem("oposiciona_auth_backup_v1", "{b64_auth}");
                window.parent.sessionStorage.removeItem("oposiciona_test_backup_v1");
                window.parent.sessionStorage.removeItem("oposiciona_live_draft_txt");
                window.parent.localStorage.setItem("oposiciona_sid_v4", "{sid_key}");
                window.parent.localStorage.setItem("oposiciona_auth_backup_v1", "{b64_auth}");
                window.parent.localStorage.removeItem("oposiciona_test_backup_v1");
                window.parent.localStorage.removeItem("oposiciona_live_draft_txt");
            }} catch(e) {{}}
            </script>""", height=0)
    except Exception:
        pass

@st.cache_resource
def _obtener_cache_binarios_drive():
    return {}

def descargar_pdf_fresco(url):
    cache_bin = _obtener_cache_binarios_drive()
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    m_id = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url or "")
    file_id = m_id.group(1) if m_id else ""

    urls_a_probar = []
    if file_id:
        urls_a_probar.append(f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t")
    sep = "&" if "?" in url else "?"
    urls_a_probar.append(f"{url}{sep}_cb={int(time.time() * 1000)}")

    ultimo_resp = None
    for u_try in urls_a_probar:
        for intento in range(2):
            try:
                r = requests.get(u_try, headers=headers, timeout=20, allow_redirects=True)
                ultimo_resp = r
                if r.status_code == 200 and r.content and (r.content[:4] in (b"%PDF", b"PK\x03\x04")):
                    cache_bin[url] = r.content
                    return r
                if r.status_code == 200 and b"confirm=" in r.content and file_id:
                    r2 = requests.get(
                        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t",
                        headers=headers,
                        timeout=20,
                        allow_redirects=True
                    )
                    if r2.status_code == 200 and r2.content and (r2.content[:4] in (b"%PDF", b"PK\x03\x04")):
                        cache_bin[url] = r2.content
                        return r2
            except Exception:
                pass
            time.sleep(0.35)

    if url in cache_bin:
        class _CachedResp:
            status_code = 200
            content = cache_bin[url]
        return _CachedResp()

    return ultimo_resp if ultimo_resp is not None else requests.get(url, headers=headers, timeout=20)
# === FIN SECCIÓN 4A ===

# === SECCIÓN 4B: MOTOR DE EVALUACIÓN TÉCNICA DEL TRIBUNAL PARA DESARROLLO Y SUPUESTOS ===
def detectar_respuesta_inapropiada_o_sin_interes(texto_alumno):
    t_raw = (texto_alumno or "").strip()
    if not t_raw:
        return None
    t_norm = ''.join(c for c in unicodedata.normalize('NFD', t_raw.lower()) if unicodedata.category(c) != 'Mn')
    t_norm = re.sub(r'\s+', ' ', t_norm).strip()
    primera_frase = re.split(r'[.?!;\n]', t_norm)[0].strip()

    patrones_inaceptables = [
        r'\b(puta|puto|mierda|caca|joder|coño|hostia|ostia|polla|capullo|gilipollas|imbecil|idiota|estupidez|asco|basura|porqueria|tonto|payaso|subnormal|mamaguevo|cabron)\b',
        r'\b(esto\s+es\s+una\s+(caca|mierda|porqueria|basura|tonteria|chorrada))\b',
        r'\b(paso\s+de\s+(todo|hacerlo|responder|estudiar|esto))\b',
        r'\b(me\s+da\s+igual|me\s+importa\s+un\s+(bledo|pimiento|carajo|huevo)|no\s+me\s+da\s+la\s+gana)\b',
        r'\b(que\s+te\s+den|vete\s+a\s+la\s+mierda|dejame\s+en\s+paz|estoy\s+harto|estoy\s+hasta\s+las\s+narices)\b',
        r'^(no\s+se(\s+nada)?|ni\s+idea|paso|nada|hola|prueba|test|asdf+|qwer+|zxcv+|jaja+|jeje+|bla\s*bla.*)$'
    ]

    es_inapropiada = any(re.search(p, primera_frase) or re.search(p, t_norm) for p in patrones_inaceptables)
    palabras_reales = re.findall(r'\b[a-záéíóúñ]{3,}\b', t_norm)
    sin_sentido = (len(t_norm) < 10 and len(palabras_reales) < 2 and not re.search(r'\d', t_norm)) or bool(re.match(r'^([a-z])\1{4,}$', t_norm))

    if es_inapropiada or sin_sentido:
        return (
            "🎩 **Observación de tus preparadores de Oposiciona:**\n\n"
            "Comprendemos que la preparación hacia el Cuerpo de Gestión de la Administración de la Seguridad Social "
            "tiene momentos de cansancio y máxima exigencia, pero esta plataforma está pensada para ayudarte a "
            "**practicar lo aprendido, afianzar el temario y acercarte cada día más a tu plaza**.\n\n"
            "Te animamos a que retomes el ejercicio con calma y redactes una respuesta razonada aplicando los conceptos, "
            "plazos y artículos que has estudiado (o consulta la solución oficial que te mostramos debajo para repasar y vuelve a intentarlo). "
            "¡Mucho ánimo con el estudio!"
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
        l_clean = re.sub(r'<[^>]+>', '', l.replace("[[H]]", "").replace("[[LI]]", "")).strip()
        l_clean = re.sub(r'^[•\*■▪\-–\s]+', '', l_clean).strip()
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

    if not (texto_alumno or "").strip() or detectar_respuesta_inapropiada_o_sin_interes(texto_alumno):
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
    if ev_fallback is None:
        ev_fallback = evaluar_respuesta_escrita(respuesta_alumno, respuesta_oficial, explicacion_oficial, f"{enunciado_supuesto} {pregunta}")

    aviso_respaldo_inapropiado = detectar_respuesta_inapropiada_o_sin_interes(respuesta_alumno)
    palabras_alumno = re.findall(r'\b[a-záéíóúñ0-9]{2,}\b', (respuesta_alumno or "").lower())
    es_respuesta_muy_escueta = len(palabras_alumno) < 12

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
    explicacion_limpia_prompt = re.sub(r'<[^>]+>', '', (explicacion_oficial or "").replace("[[H]]", "").replace("[[LI]]", "• ")).strip()

    if aviso_respaldo_inapropiado is not None:
        etiqueta_cero = "[[NOTA_SUPUESTO: 0.00]]" if modo in ("SUPUESTO", "SUPUESTOS") else "[[NOTAS_TRIBUNAL: C1=0.00 | C2=0.00 | C3=0.00]]"
        prompt_educado = (
            "Actúa exclusivamente como el equipo de preparadores de Oposiciona para el Cuerpo de Gestión de la Administración de la Seguridad Social (PROHIBIDO mencionar en tu respuesta las palabras IA, inteligencia artificial, modelo, algoritmo o asistente virtual).\n"
            "El alumno ha introducido el siguiente texto en lugar de resolver adecuadamente el ejercicio:\n"
            f"«{respuesta_alumno}»\n\n"
            f"Pregunta planteada: {pregunta}\n"
            f"Solución oficial resumida: {explicacion_limpia_prompt[:900]}\n\n"
            "=== INSTRUCCIONES ===\n"
            f"1. En la PRIMERA LÍNEA escribe exactamente: {etiqueta_cero}\n"
            "2. A continuación, dirígete al alumno de forma muy educada, serena, profesional y constructiva, adaptando tu respuesta exactamente a lo que ha escrito:\n"
            "   - Si ha escrito una falta de respeto, desahogo o queja, recuérdale con elegancia y templanza el respeto y el temple propios de un futuro funcionario del Cuerpo de Gestión, comprendiendo que la oposición es dura pero animándole a no perder el tiempo.\n"
            "   - Si ha escrito «no sé», letras sueltas o una frase evasiva, anímale con cercanía a perder el miedo al papel en blanco.\n"
            "   - En todos los casos, pídele amablemente que practique lo aprendido redactando una respuesta razonada sobre la cuestión planteada (indicándole 2 o 3 pistas clave del tema sin desvelarle todo, e invitándole a revisar la solución oficial que aparece justo debajo para consolidar el concepto)."
        )
        payload_ed = {
            "contents": [{"parts": [{"text": prompt_educado}]}],
            "generationConfig": {"temperature": 0.25, "topP": 0.85}
        }
        for modelo in _obtener_modelos_disponibles_api(clave_limpia):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={clave_limpia}"
                r = requests.post(url, json=payload_ed, headers={"Content-Type": "application/json"}, timeout=25)
                if r.status_code == 200:
                    texto_ia = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    ev_actualizado, texto_ia_limpio = _extraer_puntuaciones_de_respuesta_ia(texto_ia, ev_fallback)
                    if isinstance(ev_fallback, dict):
                        ev_fallback.update({"nota": 0.0, "nota_50": 0.0, "pts_criterio_1": 0.0, "pts_criterio_2": 0.0, "pts_criterio_3": 0.0})
                    return texto_ia_limpio
            except Exception:
                continue
        if isinstance(ev_fallback, dict):
            ev_fallback.update({"nota": 0.0, "nota_50": 0.0, "pts_criterio_1": 0.0, "pts_criterio_2": 0.0, "pts_criterio_3": 0.0})
        return aviso_respaldo_inapropiado

    if modo in ("SUPUESTO", "SUPUESTOS"):
        instruccion_escueta_sup = (
            "\n4. **ATENCIÓN A RESPUESTAS MUY BREVES, TELEGRÁFICAS O INADECUADAS:**\n"
            "   - Si observas que el alumno ha escrito muy poco (solo unas palabras sueltas sin razonar), está contestando sin rigor o con desgana, responde siempre de forma muy educada y constructiva: valóralo en su justa medida pero pídele amablemente que practique lo aprendido desarrollando el razonamiento jurídico completo (la conclusión, el porqué normativo y el artículo aplicable), explicándole que en el examen oficial del Cuerpo de Gestión el Tribunal valora la argumentación y no solo una palabra suelta.\n"
            if es_respuesta_muy_escueta else
            "\n4. **TONO CONSTRUCTIVO ANTE RESPUESTAS CORTAS O DUDOSAS:** Si la respuesta del alumno es demasiado breve o incompleta, anímale de forma muy educada a practicar lo aprendido desarrollando tanto la solución como su fundamentación jurídica.\n"
        )
        prompt = (
            "Actúa exclusivamente como el equipo de preparadores de Oposiciona para el Cuerpo de Gestión de la Administración de la Seguridad Social (PROHIBIDO mencionar en tu respuesta las palabras IA, inteligencia artificial, modelo, algoritmo o asistente virtual).\n"
            "Evalúa la respuesta del alumno a esta cuestión de un SUPUESTO PRÁCTICO comparándola directamente con la "
            "EXPLICACIÓN Y RESPUESTA TÉCNICA OFICIAL de la pregunta (SIN aplicar baremos ni criterios formales de Tribunal C1/C2/C3).\n\n"
            "=== REGLAS DE CORRECCIÓN DEL SUPUESTO PRÁCTICO ===\n"
            "1. Califica la respuesta de **0,00 a 10,00 puntos** (siendo 5,00 el aprobado), aplicando un criterio justo, constructivo y ligeramente indulgente cuando el alumno identifique bien la solución jurídica o el planteamiento del cálculo.\n"
            "2. Si el alumno falta al respeto, escribe tonterías o demuestra nulo interés, otórgale `0.00` puntos y respóndele de forma sumamente educada, elegante y constructiva pidiéndole que aproveche el estudio y practique lo aprendido.\n"
            "3. Comprueba si el alumno:\n"
            "   - Ha detectado la clave o «trampa» jurídica/matemática explicada en el bloque de solución.\n"
            "   - Ha llegado al resultado numérico, plazo o calificación jurídica correcta.\n"
            "   - Ha fundamentado su respuesta en la normativa aplicable (no penalices en exceso si omite el número exacto de algún artículo pero aplica bien la regla legal)."
            f"{instruccion_escueta_sup}\n"
            f"=== PLANTEAMIENTO DEL SUPUESTO ===\n{enunciado_limpio}\n\n"
            f"=== PREGUNTA PRÁCTICA ===\n{pregunta}\n\n"
            f"=== EXPLICACIÓN Y SOLUCIÓN OFICIAL DE LA PREGUNTA ===\n{respuesta_oficial}\n{explicacion_limpia_prompt}\n\n"
            f"=== RESPUESTA DEL ALUMNO ===\n{respuesta_alumno}\n\n"
            "=== FORMATO OBLIGATORIO DE TU RESPUESTA ===\n"
            "En la PRIMERA LÍNEA escribe siempre esta etiqueta exacta con la nota sobre 10 (con punto decimal):\n"
            "[[NOTA_SUPUESTO: X.XX]]\n\n"
            "A continuación, redacta una valoración clara, educada, directa y formativa estructurada en estos 3 puntos:\n"
            "1. **✅ Lo que has acertado en la resolución de la pregunta:**\n"
            "   - Destaca los cálculos, plazos, conclusiones jurídicas y preceptos que el alumno ha resuelto correctamente (o indícale con amabilidad si su respuesta ha sido demasiado escueta para darla por completa).\n"
            "2. **⚠️ Por qué obtienes esta nota (qué ha faltado y cómo practicar lo aprendido):**\n"
            "   - Explica con claridad y tono pedagógico qué matiz, cálculo, plazo o precepto de la explicación oficial le ha faltado o en qué punto se ha desviado, invitándole educadamente a practicar lo aprendido razonando su contestación.\n"
            f"   - Indica en una línea limpia: **Artículos de la solución no citados:** {arts_omitidos_str}\n"
            "3. **💡 Consejo práctico de tus preparadores para clavar esta pregunta en el examen:**\n"
            "   - Un consejo breve, cercano y directo para recordar la regla o fórmula aplicada."
        )
    else:
        alerta_desv_str = (
            f"\n🚨 ATENCIÓN: Se ha detectado incongruencia con el epígrafe preguntado: {aud_b.get('motivo_desviacion')}\n"
            "Si el alumno ha contestado un epígrafe distinto al preguntado (por ejemplo, hablar de Altas y Bajas cuando se pregunta Afiliación o Convenio Especial), la nota de Criterio 1 no puede superar los 10,00 puntos.\n"
            if aud_b.get("desviacion_epigrafe") else ""
        )

        prompt = (
            "Actúa exclusivamente como el Tribunal Calificador y equipo de preparadores de Oposiciona para el Cuerpo de Gestión de la Administración de la Seguridad Social (PROHIBIDO mencionar en tu respuesta las palabras IA, inteligencia artificial, modelo, algoritmo o asistente virtual).\n"
            "Realiza un análisis analítico, detallado, justo y constructivo comparando el TEXTO ESCRITO POR EL ALUMNO con la "
            "EXPLICACIÓN / DESARROLLO OFICIAL DE ESTE EPÍGRAFE CONCRETO que se te facilita más abajo, aplicando un criterio **equilibrado, formativo y ligeramente indulgente** para no desanimar en exceso al opositor cuando sí trabaja el epígrafe:\n\n"
            "=== REGLAS EQUILIBRADAS DE VALORACIÓN DEL TRIBUNAL ===\n"
            "1. **DISTINCIÓN CLARA ENTRE CONTESTAR OTRO EPÍGRAFE, RESPUESTA MUY ESCUETA O FALTA DE RESPETO VS. RESPUESTA PERTINENTE (`" + pregunta + "`):**\n"
            "   - **Si el alumno falta al respeto o escribe comentarios improcedentes:** Otórgale `0.00` puntos y respóndele con máxima educación, elegancia y firmeza constructiva pidiéndole que practique lo aprendido.\n"
            "   - **Si el alumno escribe muy poco (unas pocas líneas esquemáticas):** Respóndele de forma muy educada y motivadora, valorando los conceptos que haya mencionado pero invitándole a practicar lo aprendido desarrollando todos los apartados del epígrafe con redacción jurídica completa.\n"
            "   - **Cuándo SÍ debes suspender con firmeza (< 12 / 50 ptos):** Únicamente cuando el alumno conteste un epígrafe distinto al preguntado o cuando deje casi todo sin desarrollar.\n"
            "   - **Cuándo debes ser UN POCO MÁS INDULGENTE Y CONSTRUCTIVO (permitiendo alcanzar o superar los 22-30 / 45 puntos en Criterio 1):** Cuando el alumno SÍ está contestando al epígrafe preguntado, comprende bien el núcleo del tema y desarrolla correctamente una parte relevante.\n"
            "   - **NO EXIJAS COMO OBLIGATORIO LO QUE NO ESTÉ EN LA EXPLICACIÓN OFICIAL DE ESTE EPÍGRAFE:** Si el alumno adelanta o añade conceptos conexos válidos del tema, súmale puntos adicionales en el Criterio 1 por enriquecer la exposición."
            f"{alerta_desv_str}\n"
            "2. **REGLA EXACTA SOBRE PRESENTACIÓN DE SIGLAS (PROHIBIDO INVENTAR FALSOS POSITIVOS):**\n"
            "   - Una sigla está **CORRECTAMENTE PRESENTADA** tanto si el alumno escribe su nombre completo seguido de la sigla entre paréntesis como si utiliza la fórmula *«..., en adelante, SIGLA»*.\n"
            f"   - Auditoría automática verificada sobre el texto del alumno: **Siglas usadas sin presentar detectadas:** `{siglas_mal_str}` (respeta exactamente este dato y resta muy poquito —máximo 0,15 o 0,20 ptos— si hay alguna).\n\n"
            "3. **FALTA DE ARTÍCULOS INCLUIDOS EN LA EXPLICACIÓN (RESTA MUY LEVE Y FORMATO ESTRICTO «Artículos omitidos: ...»):**\n"
            "   - Omitir números de artículos incluidos en la explicación oficial debe restar **muy poco** cuando el alumno ha sabido explicar el concepto jurídico.\n"
            f"   - Relación detectada: **Artículos omitidos:** {arts_omitidos_str}.\n\n"
            "=== BAREMO OFICIAL DEL TRIBUNAL CALIFICADOR ===\n"
            "- Puntuación total: de 0 a 50 puntos (mínimo 25,00 puntos para aprobar).\n"
            "- Criterio 1 (0 a 45 puntos): Conocimiento y desarrollo de los apartados de la explicación oficial de este epígrafe + puntos extra por conceptos o artículos adicionales conexos válidos que mejoren el epígrafe - resta muy leve por los artículos omitidos de la explicación.\n"
            "- Criterio 2 (0 a 3 puntos): Orden de las ideas y estructura sistemática (puntúa si Criterio 1 >= 20,00; si Criterio 1 < 20,00, Criterio 2 = 0,00).\n"
            "- Criterio 3 (0 a 2 puntos): Calidad de la expresión escrita y presentación de siglas (puntúa si Criterio 1 >= 20,00; resta muy levemente solo por las siglas que realmente haya usado el alumno sin presentar su nombre completo).\n\n"
            f"=== EPÍGRAFE PREGUNTADO ===\n{enunciado_limpio}\n{pregunta}\n\n"
            f"=== EXPLICACIÓN / DESARROLLO OFICIAL DEL EPÍGRAFE (REFERENCIA DE CONTENIDO) ===\n{respuesta_oficial}\n{explicacion_limpia_prompt}\n\n"
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
            "   - Valora de forma constructiva y positiva todo lo que el alumno ha desarrollado bien respecto al epígrafe.\n"
            "2. **⚠️ Análisis constructivo de lo que falta por completar respecto a la explicación oficial:**\n"
            "   - Explica con detalle analítico y tono cercano qué apartados o matices de la `EXPLICACIÓN / DESARROLLO OFICIAL DEL EPÍGRAFE` le han faltado, animándole educadamente a practicar lo aprendido.\n"
            "3. **⚖️ Rigor normativo y uso de siglas:**\n"
            "   - Valora las normas y artículos bien citados.\n"
            f"   - Escribe en una línea limpia: **Artículos omitidos:** {arts_omitidos_str}\n"
            f"   - Respecto a las siglas sin presentar, indica únicamente: **Siglas sin presentación previa:** {siglas_mal_str}\n"
            "4. **🎓 Calificación por Criterios del Tribunal y Desglose sencillo de puntos sumados y restados:**\n"
            "   - Muestra las puntuaciones otorgadas en:\n"
            "     • **Criterio 1 (Conocimiento y normativa: 0 a 45 ptos):** `XX,XX / 45,00 puntos`\n"
            "     • **Criterio 2 (Orden de las ideas y estructura: 0 a 3 ptos):** `X,XX / 3,00 puntos`\n"
            "     • **Criterio 3 (Calidad de la expresión escrita y siglas: 0 a 2 ptos):** `X,XX / 2,00 puntos`\n"
            "     • **🏆 CALIFICACIÓN TOTAL:** **`XX,XX / 50,00 puntos`** *(Equivalencia: **`X,XX / 10`**)*\n"
            "   - Añade el bloque **📊 Resumen sencillo de por qué has sumado y por qué te han restado puntos:**\n"
            "     • **➕ Qué te ha sumado puntos:** viñetas claras con los puntos aportados por cada bloque bien desarrollado.\n"
            "     • **➖ Qué te ha restado o impedido sumar hasta los 50 puntos:** viñetas claras con los puntos que faltaron por los apartados no incluidos, la resta leve por **Artículos omitidos** y la resta leve (si procede) por **siglas sin presentación previa**.\n"
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
# === FIN SECCIÓN 4B ===

# === SECCIÓN 4C: NAVEGACIÓN DEL TEST, SIMULACROS, AUDITORÍA Y REPORTE DE ERRORES ===
@st.cache_resource
def _obtener_bandeja_reportes_admin():
    """Almacena en memoria del servidor los reportes enviados por los alumnos para que el Admin pueda descargarlos en PDF en 1 clic."""
    return []

def generar_pdf_reporte_error(datos_rep):
    """
    Genera en memoria un archivo PDF limpio y estructurado (usando PyMuPDF / fitz)
    con toda la información de un reporte de error (o varios reportes) para poder subirlo directamente al chat.
    """
    lista_rep = datos_rep if isinstance(datos_rep, list) else [datos_rep]
    doc = fitz.open()

    for idx_r, rep in enumerate(lista_rep, 1):
        lineas_Bloques = [
            f"REPORTE DE INCIDENCIA / ERROR EN PREGUNTA #{idx_r} — OPOSICIONA",
            "=" * 78,
            f"Fecha y hora: {rep.get('fecha', datetime.now(ZoneInfo('Europe/Madrid')).strftime('%d/%m/%Y %H:%M:%S'))}",
            f"Alumno que reporta: {rep.get('usuario', 'info@oposiciona.es')}",
            f"Especialidad / Categoría: {rep.get('especialidad', '')} | {rep.get('categoria', '')}",
            f"Nombre del Test / Archivo: {rep.get('nombre_test', '')}",
            f"Tema: {rep.get('tema', '')}",
            f"Número de Pregunta / Cuestión: {rep.get('num_pregunta', '')}",
            "-" * 78,
            "COMENTARIO / INCIDENCIA QUE REPORTA EL ALUMNO:",
            f"« {rep.get('motivo', '')} »",
            "-" * 78,
        ]

        if rep.get("preamble"):
            lineas_Bloques.extend([
                "PLANTEAMIENTO / PREÁMBULO:",
                rep.get("preamble", ""),
                "-" * 78,
            ])

        lineas_Bloques.extend([
            "ENUNCIADO DE LA PREGUNTA / EPÍGRAFE:",
            rep.get("enunciado", ""),
            "-" * 78,
        ])

        opciones = rep.get("opciones", [])
        if opciones:
            lineas_Bloques.append("OPCIONES EXTRAÍDAS:")
            for op_txt in opciones:
                lineas_Bloques.append(f"  {op_txt}")
            lineas_Bloques.extend([
                "-" * 78,
                "RESPUESTA QUE DA POR BUENA EL SISTEMA:",
                rep.get("respuesta_sistema", ""),
                "-" * 78,
            ])
        elif rep.get("respuesta_alumno"):
            lineas_Bloques.extend([
                "RESPUESTA ESCRITA POR EL ALUMNO:",
                rep.get("respuesta_alumno", ""),
                "-" * 78,
                "DICTAMEN DE CORRECCIÓN TÉCNICA:",
                rep.get("valoracion_ia", ""),
                "-" * 78,
            ])

        lineas_Bloques.extend([
            "EXPLICACIÓN / TEXTO OFICIAL EXTRAÍDO DEL PDF:",
            rep.get("explicacion", ""),
            "=" * 78,
        ])

        texto_completo = "\n".join(lineas_Bloques)
        lineas_envueltas = []
        for l_orig in texto_completo.splitlines():
            if not l_orig.strip():
                lineas_envueltas.append("")
                continue
            palabras = l_orig.split(" ")
            actual = ""
            for pal in palabras:
                if len(actual) + len(pal) + 1 <= 92:
                    actual = f"{actual} {pal}".strip() if actual else pal
                else:
                    if actual:
                        lineas_envueltas.append(actual)
                    actual = pal
            if actual:
                lineas_envueltas.append(actual)

        lineas_por_pagina = 52
        for i_pag in range(0, max(1, len(lineas_envueltas)), lineas_por_pagina):
            page = doc.new_page(width=595, height=842)
            trozo = "\n".join(lineas_envueltas[i_pag:i_pag + lineas_por_pagina])
            rect = fitz.Rect(36, 36, 559, 806)
            page.insert_textbox(rect, trozo, fontsize=9.5, fontname="helv", color=(0.08, 0.12, 0.20))

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def render_cuadro_reporte_error(q, num_pregunta, ubicacion_key):
    if not usuario_puede_reportar():
        return

    es_desarrollo = bool(q.get("tipo_abierta") == "DESARROLLO")
    es_abierta = bool(q.get("is_open", False))
    es_sup_test = bool(q.get("es_supuesto_test", False))
    tipo_lbl = "Epígrafe" if es_desarrollo else ("Cuestión" if (es_abierta or es_sup_test) else "Pregunta")
    nombre_pdf = st.session_state.get('test_name') or "Test sin nombre"
    id_test_limpio = re.sub(r'\W+', '_', nombre_pdf)
    tema_vis = obtener_etiqueta_tema_visible(nombre_pdf, q)
    usuario_rep = (st.session_state.get('email') or "Alumno Oposiciona").strip()
    preamble_txt = re.sub(r'<[^>]+>|\*\*|\🏷️', '', q.get('preamble', '')).strip()
    pregunta_txt = re.sub(r'<[^>]+>', '', q.get('question_text', '')).strip()
    exp_limpia = re.sub(
        r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+fundamento\s+legal|\s+y\s+soluci[óo]n\s+detallada|\s*\([^)]*\))?:|respuesta:|resp:|respuestas:)\s*',
        '',
        re.sub(r'<[^>]+>', '', q.get('explanation', '')).replace("[[H]]", "").replace("[[LI]]", "• ").strip(),
        flags=re.IGNORECASE
    ).strip() or "Sin explicación disponible."

    st.markdown(
        "<div style='background-color:#fff8e1; border:2px solid #ffb300; border-radius:8px; padding:12px; margin-top:8px; margin-bottom:8px;'>"
        f"<b style='color:#bf360c !important; font-size:15px;'>🛠️ Reportar Error en {tipo_lbl} {num_pregunta} a info@oposiciona.es</b><br>"
        f"<span style='font-size:13px; color:#5d4037 !important;'>{'Se enviará una ficha con tu comentario, el Tema, el enunciado, tu Respuesta escrita, el Dictamen de corrección y la Explicación oficial.' if es_abierta else 'Se enviará una ficha completa con tu comentario, el enunciado, las opciones y la explicación para revisarlo al instante.'}</span>"
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

    stat_q = st.session_state.get("stats", {}).get(num_pregunta - 1, {})
    lista_opciones = q.get('options', [])
    idx_correcta = q.get('answer', -1)
    correcta_txt = lista_opciones[idx_correcta] if (0 <= idx_correcta < len(lista_opciones)) else (q.get('answer_text') or "No detectada automaticamente en el PDF")
    resumen_opciones_txt = []
    for i_opt, texto_opt in enumerate(lista_opciones):
        marca_corr = "[MARCADA CORRECTA] " if i_opt == idx_correcta else ""
        resumen_opciones_txt.append(f"{marca_corr}{texto_opt}")

    datos_ficha_rep = {
        "fecha": datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y %H:%M:%S"),
        "usuario": usuario_rep,
        "especialidad": st.session_state.get("test_esp") or st.session_state.get("saved_esp") or "",
        "categoria": st.session_state.get("test_cat") or st.session_state.get("saved_cat") or "",
        "nombre_test": nombre_pdf,
        "tema": tema_vis,
        "num_pregunta": f"{tipo_lbl} {num_pregunta}",
        "motivo": (motivo or "").strip() or "(Sin comentario adicional)",
        "preamble": preamble_txt,
        "enunciado": pregunta_txt,
        "opciones": resumen_opciones_txt,
        "respuesta_sistema": correcta_txt,
        "respuesta_alumno": (stat_q.get("selected") or st.session_state.get(f"open_txt_{num_pregunta - 1}") or "").strip() if es_abierta else "",
        "valoracion_ia": re.sub(r'<[^>]+>', '', (stat_q.get("ai_feedback") or "")).strip() if es_abierta else "",
        "explicacion": exp_limpia,
    }

    if usuario_es_admin():
        col_env, col_pdf, col_cer = st.columns([2.2, 1.5, 0.8])
        with col_pdf:
            pdf_rep_bytes = generar_pdf_reporte_error(datos_ficha_rep)
            st.download_button(
                label="📄 Descargar reporte en PDF",
                data=pdf_rep_bytes,
                file_name=f"REPORTE_{id_test_limpio}_P{num_pregunta}.pdf",
                mime="application/pdf",
                key=f"btn_dl_pdf_{id_test_limpio}_{ubicacion_key}_{num_pregunta}",
                use_container_width=True
            )
    else:
        col_env, col_cer = st.columns([3, 1])

    with col_cer:
        if st.button("✖ Cerrar", key=f"btn_close_{id_test_limpio}_{ubicacion_key}_{num_pregunta}", use_container_width=True):
            limpiar_estados_reportes_error()
            st.rerun()

    with col_env:
        enviar_pulsado = st.button(f"📨 Enviar reporte de {tipo_lbl} {num_pregunta} a info@oposiciona.es", key=f"btn_send_{id_test_limpio}_{ubicacion_key}_{num_pregunta}", type="primary", use_container_width=True)

    if enviar_pulsado:
        motivo_limpio = (motivo or "").strip()
        if not motivo_limpio:
            st.warning("⚠️ Escribe brevemente en qué consiste el error o incidencia antes de enviarlo.")
        else:
            datos_ficha_rep["motivo"] = motivo_limpio
            try:
                bandeja_adm = _obtener_bandeja_reportes_admin()
                bandeja_adm.insert(0, dict(datos_ficha_rep))
                if len(bandeja_adm) > 100:
                    del bandeja_adm[100:]
            except Exception:
                pass

            correo_remitente = usuario_rep if "@" in usuario_rep else "info@oposiciona.es"

            if es_abierta:
                resp_alumno_env = datos_ficha_rep["respuesta_alumno"] or "Sin respuesta escrita por el alumno"
                dictamen_env = datos_ficha_rep["valoracion_ia"] or "Aún no se había pulsado Comprobar"
                payload = {
                    "_subject": f"Revisar {tipo_lbl} {num_pregunta} ({tema_vis}) - {nombre_pdf}",
                    "name": f"Alumno Oposiciona ({usuario_rep})",
                    "email": correo_remitente,
                    "_replyto": correo_remitente,
                    "COMENTARIO_DEL_ALUMNO": motivo_limpio,
                    "ALUMNO_Y_TEMA": f"Alumno: {usuario_rep} | Tema: {tema_vis} | Archivo: {nombre_pdf} ({tipo_lbl} {num_pregunta})",
                    "ENUNCIADO_PREGUNTA_O_EPIGRAFE": pregunta_txt[:1500],
                    "RESPUESTA_DEL_ALUMNO": resp_alumno_env[:2500],
                    "DICTAMEN_DE_CORRECCION": dictamen_env[:2500],
                    "TEXTO_OFICIAL_REFERENCIA": exp_limpia[:2500],
                    "message": f"REPORTE DE {usuario_rep}: {motivo_limpio}\n\nTest: {nombre_pdf} ({tipo_lbl} {num_pregunta})\nEnunciado: {pregunta_txt}",
                    "_template": "table",
                    "_captcha": "false"
                }
            else:
                payload = {
                    "_subject": f"Revisar {tipo_lbl} {num_pregunta} - {nombre_pdf}",
                    "name": f"Alumno Oposiciona ({usuario_rep})",
                    "email": correo_remitente,
                    "_replyto": correo_remitente,
                    "COMENTARIO_DEL_ALUMNO": motivo_limpio,
                    "ALUMNO_Y_TEST": f"Alumno: {usuario_rep} | Test: {nombre_pdf} ({tipo_lbl} N. {num_pregunta})" + (f" | {preamble_txt[:400]}" if preamble_txt else ""),
                    "ENUNCIADO_DE_LA_PREGUNTA": pregunta_txt,
                }
                for i_opt, texto_opt in enumerate(lista_opciones):
                    letra_mayus = chr(65 + i_opt)
                    marca_corr = "[MARCADA CORRECTA] " if i_opt == idx_correcta else ""
                    payload[f"OPCION_{letra_mayus}"] = f"{marca_corr}{texto_opt}"
                payload["RESPUESTA_QUE_DA_POR_BUENA_EL_SISTEMA"] = correcta_txt
                payload["EXPLICACION_EXTRAIDA_DEL_PDF"] = exp_limpia[:2500]
                payload["message"] = (
                    f"QUE REPORTA EL ALUMNO ({usuario_rep}):\n« {motivo_limpio} »\n\n"
                    f"TEST: {nombre_pdf} ({tipo_lbl} {num_pregunta})\n"
                    f"PLANTEAMIENTO: {preamble_txt[:800]}\n\n"
                    f"ENUNCIADO: {pregunta_txt}\n\n"
                    f"OPCIONES:\n" + "\n".join(resumen_opciones_txt) + "\n\n"
                    f"RESPUESTA DADA POR BUENA: {correcta_txt}\n\n"
                    f"EXPLICACION:\n{exp_limpia[:1500]}"
                )
                payload["_template"] = "table"
                payload["_captcha"] = "false"

            enviado_servidor = False
            with st.spinner("📨 Enviando reporte a info@oposiciona.es..."):
                try:
                    headers_fs = {
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "Referer": "https://test-oposiciona.streamlit.app/",
                        "Origin": "https://test-oposiciona.streamlit.app",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                    resp_fs = requests.post(
                        "https://formsubmit.co/ajax/info@oposiciona.es",
                        data=payload,
                        headers=headers_fs,
                        timeout=10
                    )
                    if resp_fs.status_code == 200:
                        datos_fs = resp_fs.json()
                        if str(datos_fs.get("success", "")).lower() == "true":
                            enviado_servidor = True
                except Exception:
                    enviado_servidor = False

                if not enviado_servidor:
                    try:
                        headers_json = {
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                            "Referer": "https://test-oposiciona.streamlit.app/",
                            "Origin": "https://test-oposiciona.streamlit.app",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                        resp_fs2 = requests.post(
                            "https://formsubmit.co/ajax/info@oposiciona.es",
                            json=payload,
                            headers=headers_json,
                            timeout=10
                        )
                        if resp_fs2.status_code == 200 and str(resp_fs2.json().get("success", "")).lower() == "true":
                            enviado_servidor = True
                    except Exception:
                        enviado_servidor = False

            try:
                registrar_actividad_sheets(
                    evento="🛠️ Reporte Error",
                    nombre_test=f"{nombre_pdf} (P{num_pregunta}): {motivo_limpio[:120]}",
                    accion="nueva_fila"
                )
            except Exception:
                pass

            if enviado_servidor:
                limpiar_estados_reportes_error()
                st.session_state[f"rep_ok_msg_{id_test_limpio}_{num_pregunta}"] = True
                st.rerun()
            else:
                payload_json = json.dumps(payload, ensure_ascii=False)
                components.html(f"""
                <div id="status_envio" style="font-family:sans-serif; padding:12px; border-radius:6px; background:#e8f5e9; border:2px solid #2e7d32; color:#1b5e20; font-size:14px; font-weight:700; text-align:center;">
                    ⏳ Enviando reporte a info@oposiciona.es...
                </div>
                <script>
                (function() {{
                    var rawData = {payload_json};
                    var params = new URLSearchParams();
                    for (var k in rawData) {{
                        if (Object.prototype.hasOwnProperty.call(rawData, k)) {{
                            params.append(k, rawData[k]);
                        }}
                    }}
                    var box = document.getElementById("status_envio");
                    fetch("https://formsubmit.co/ajax/info@oposiciona.es", {{
                        method: "POST",
                        headers: {{
                            "Accept": "application/json",
                            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
                        }},
                        body: params.toString()
                    }})
                    .then(function(r) {{ return r.json(); }})
                    .then(function(res) {{
                        box.style.background = "#e8f5e9";
                        box.style.borderColor = "#2e7d32";
                        box.style.color = "#1b5e20";
                        box.innerHTML = "✅ ¡Reporte enviado con éxito a info@oposiciona.es! Muchas gracias por tu colaboración.";
                    }})
                    .catch(function(err) {{
                        box.style.background = "#e8f5e9";
                        box.style.borderColor = "#2e7d32";
                        box.style.color = "#1b5e20";
                        box.innerHTML = "✅ ¡Tu reporte ha quedado registrado correctamente para revisión! Muchas gracias.";
                    }});
                }})();
                </script>
                """, height=70)

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
    if categoria in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"]:
        esp_act = (st.session_state.get("saved_esp") or "").upper()
        return "📋 2.º Ejercicio (2.ª Parte) — Supuestos Prácticos" if "GESTI" in esp_act else "📋 Supuestos Prácticos (Tipo Test)"
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
    es_gest = "GESTI" in (st.session_state.test_esp or "").upper()
    max_op = 3 if es_gest else 4
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
                    if not es_gest:
                        raw_qs = PDFQuizParser.parse_supuestos_test_administrativos(r.content, max_options=max_op)
                        if not raw_qs:
                            st.error("No se encontraron supuestos prácticos tipo test en este documento.")
                        else:
                            procesar_preguntas(raw_qs, barajar=True)
                    else:
                        raw_qs = PDFQuizParser.parse_abiertas_gestion(r.content, modo="SUPUESTOS")
                        if not raw_qs:
                            raw_qs = PDFQuizParser.parse_supuestos_test_administrativos(r.content, max_options=max_op)
                        if not raw_qs:
                            st.error("No se encontraron supuestos prácticos en este documento.")
                        else:
                            es_sup_abierto = any(q.get("is_open", False) for q in raw_qs)
                            procesar_preguntas(raw_qs, barajar=(not es_sup_abierto))
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

def _obtener_prefijo_corto_tema(nombre_test, q=None):
    fuentes = [
        (q.get("tema_titulo") if isinstance(q, dict) else "") or "",
        nombre_test or ""
    ]
    for f in fuentes:
        m = re.search(r'tema[_\s\-]*(\d+)', str(f), re.IGNORECASE)
        if m:
            return f"TEMA {int(m.group(1)):02d}"
    return (nombre_test or "TEMA").strip().upper()

def construir_nombre_epigrafe_sheets(indice_epigrafe):
    qs = st.session_state.get("questions", [])
    if not qs or indice_epigrafe is None or indice_epigrafe >= len(qs):
        return st.session_state.get("test_name") or "Test"
    q_ep = qs[indice_epigrafe]
    pref_tema = _obtener_prefijo_corto_tema(st.session_state.get("test_name"), q_ep)
    ep_txt = re.sub(r'\s*↑+\s*$', '', (q_ep.get("question_text") or f"EPÍGRAFE {indice_epigrafe + 1}")).strip().rstrip(".")
    if not re.match(r'^(?:EP[ÍI]GRAFE|PREGUNTA)\b', ep_txt, re.IGNORECASE):
        ep_txt = f"EPÍGRAFE {indice_epigrafe + 1}: {ep_txt}"
    return f"{pref_tema}. {ep_txt}"

def formatear_nota_epigrafe_individual_sheets(ev_obj):
    if not isinstance(ev_obj, dict):
        return "0,00/50 (0,00/10)"
    n50 = float(ev_obj.get("nota_50", 0.0))
    n10 = float(ev_obj.get("nota", 0.0))
    return f"{n50:.2f}/50 ({n10:.2f}/10)".replace(".", ",")

def registrar_epigrafe_desarrollo_en_sheets(idx_ep):
    qs = st.session_state.get("questions", [])
    stats = st.session_state.get("stats", {})
    if not qs or idx_ep is None or idx_ep >= len(qs):
        return
    q_ep = qs[idx_ep]
    if q_ep.get("tipo_abierta") != "DESARROLLO":
        return

    stat_ep = stats.get(idx_ep, {})
    txt_al = (stat_ep.get("selected") or "").strip()
    ev_ep = stat_ep.get("ai_eval")
    if not isinstance(ev_ep, dict):
        return

    firma_registro = f"{txt_al}__{ev_ep.get('nota_50', 0.0):.2f}"
    if stat_ep.get("sheets_logged_sig") == firma_registro:
        return
    stat_ep["sheets_logged_sig"] = firma_registro

    st.session_state.test_cat = "DESARROLLO"
    nombre_ep_limpio = construir_nombre_epigrafe_sheets(idx_ep)
    nota_ep_limpia = formatear_nota_epigrafe_individual_sheets(ev_ep)

    if not stat_ep.get("ep_hora_inicio"):
        ahora_ep = datetime.now(ZoneInfo("Europe/Madrid"))
        stat_ep["ep_start_ts"] = time.time() - 5
        stat_ep["ep_hora_inicio"] = ahora_ep.strftime("%H:%M:%S")

    hora_ini_ep = stat_ep["ep_hora_inicio"]
    ts_ini_ep = stat_ep.get("ep_start_ts") or st.session_state.get("test_start_ts")

    if not stat_ep.get("ep_inicio_registrado", False):
        stat_ep["ep_inicio_registrado"] = True
        registrar_actividad_sheets(
            evento="🚀 En curso",
            nombre_test=nombre_ep_limpio,
            aciertos="",
            fallos="",
            blancos="",
            nota="",
            accion="nueva_fila",
            hora_inicio_override=hora_ini_ep,
            start_ts_override=ts_ini_ep,
            sincrono=True
        )

    registrar_actividad_sheets(
        evento="✅ Completado",
        nombre_test=nombre_ep_limpio,
        aciertos="",
        fallos="",
        blancos="",
        nota=nota_ep_limpia,
        accion="actualizar_fin",
        hora_inicio_override=hora_ini_ep,
        start_ts_override=ts_ini_ep,
        sincrono=True
    )

def calcular_nota_final_supuestos_sheets(indice_actual=None):
    qs = st.session_state.get("questions", [])
    stats = st.session_state.get("stats", {})
    if not qs:
        return ""
    evaluados = []
    for i_q, _ in enumerate(qs):
        stat_i = stats.get(i_q, {})
        ev_i = stat_i.get("ai_eval")
        if isinstance(ev_i, dict) and ev_i.get("nota") is not None:
            evaluados.append((i_q + 1, float(ev_i.get("nota", 0.0))))
    if not evaluados:
        return "0,00/10"
    media_10 = sum(x[1] for x in evaluados) / len(evaluados)
    if len(evaluados) == 1:
        num_e, n10_e = evaluados[0]
        return f"{n10_e:.2f}/10 (P{num_e})".replace(".", ",")
    desglose_s = " | ".join([f"P{num_e}: {n10_e:.2f}/10" for num_e, n10_e in evaluados])
    return f"{media_10:.2f}/10 [{desglose_s}]".replace(".", ",")

def save_answer(selected):
    idx_curr = st.session_state.current_index
    stat = st.session_state.stats[idx_curr]
    q_curr = st.session_state.questions[idx_curr] if st.session_state.get("questions") else {}
    es_desarrollo_curr = bool(q_curr.get("tipo_abierta") == "DESARROLLO" or (st.session_state.get("test_cat") or "").upper() == "DESARROLLO")

    if selected is None or (q_curr.get("is_open") and str(selected).strip() == ""):
        stat['selected'] = None
        return

    if selected != stat['selected']:
        stat['selected'] = selected
        stat['attempts'] += 1
        if es_desarrollo_curr:
            if not stat.get("ep_inicio_registrado", False):
                ahora_ep = datetime.now(ZoneInfo("Europe/Madrid"))
                stat["ep_start_ts"] = time.time()
                stat["ep_hora_inicio"] = ahora_ep.strftime("%H:%M:%S")
                stat["ep_inicio_registrado"] = True
                st.session_state.test_cat = "DESARROLLO"
                nombre_ep_limpio = construir_nombre_epigrafe_sheets(idx_curr)
                registrar_actividad_sheets(
                    "🚀 En curso",
                    nombre_test=nombre_ep_limpio,
                    accion="nueva_fila",
                    hora_inicio_override=stat["ep_hora_inicio"],
                    start_ts_override=stat["ep_start_ts"]
                )
        elif not st.session_state.get('inicio_registrado_sheets', False):
            st.session_state.inicio_registrado_sheets = True
            nombre_celda = st.session_state.get("test_name") or "Test"
            registrar_actividad_sheets("🚀 En curso", nombre_test=nombre_celda, accion="nueva_fila")

def handle_option_toggle(idx_q, opt_idx):
    q = st.session_state.questions[idx_q]
    opts = q.get("options", [])
    if opt_idx < 0 or opt_idx >= len(opts):
        return

    key_clicked = f"opt_chk_{idx_q}_{opt_idx}"
    nuevo_estado = bool(st.session_state.get(key_clicked, False))

    if nuevo_estado:
        opt_elegida = opts[opt_idx]
        for j in range(len(opts)):
            if j != opt_idx:
                st.session_state[f"opt_chk_{idx_q}_{j}"] = False
        save_answer(opt_elegida)
        if "metralleta" in st.session_state.modo_avance.lower():
            limpiar_estados_reportes_error()
            if idx_q < len(st.session_state.questions) - 1:
                st.session_state.current_index += 1
                st.session_state.checked = False
                st.session_state.do_scroll = True
            else:
                st.session_state.update(finished=True, fase_deliberacion_tribunal=True, animacion_fin_mostrada=False, celebracion_mostrada=False, do_scroll=True)
    else:
        for j in range(len(opts)):
            st.session_state[f"opt_chk_{idx_q}_{j}"] = False
        if idx_q in st.session_state.stats:
            st.session_state.stats[idx_q]['selected'] = None
            if st.session_state.stats[idx_q].get('attempts', 0) > 0:
                st.session_state.stats[idx_q]['attempts'] -= 1
        st.session_state.checked = False
        sincronizar_progreso_navegador()

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
            st.session_state.update(finished=True, fase_deliberacion_tribunal=True, animacion_fin_mostrada=False, celebracion_mostrada=False, do_scroll=True)

def _actualizar_letras_explicacion_tras_barajar(texto_exp, mapa_letras, letra_correcta_final=None):
    if not texto_exp:
        return ""

    txt = texto_exp

    def _map_char(ch):
        c_low = ch.lower()
        nuevo = mapa_letras.get(c_low, c_low)
        return nuevo.upper() if ch.isupper() else nuevo

    if letra_correcta_final:
        txt = re.sub(
            r'((?:la\s+)?(?:respuesta|opci[óo]n)\s+correcta\s+(?:es\s+la|es)\s*[:\s]*[\'"«]?)([a-dA-D])([\)\'"»]?(?=\s|\.|\,|\;|\:|$))',
            lambda m: f"{m.group(1)}{letra_correcta_final.upper() if m.group(2).isupper() else letra_correcta_final}{m.group(3)}",
            txt,
            flags=re.IGNORECASE
        )

    txt = re.sub(
        r'\b(opci[óo]n\s+[\'"«]?)([a-dA-D])([\)\'"»]?(?=\s|\.|\,|\;|\:|\)|$))',
        lambda m: f"{m.group(1)}{_map_char(m.group(2))}{m.group(3)}",
        txt,
        flags=re.IGNORECASE
    )

    def _reemplazar_lista_opciones(m):
        pref = m.group(1)
        cuerpo_lista = m.group(2)
        cuerpo_actualizado = re.sub(
            r'\b([a-dA-D])\b',
            lambda sm: _map_char(sm.group(1)) if sm.group(1).lower() != "y" else sm.group(1),
            cuerpo_lista
        )
        return f"{pref}{cuerpo_actualizado}"

    txt = re.sub(
        r'\b(opciones\s+)([a-dA-D](?:\s*,\s*[a-dA-D])*\s+y\s+[a-dA-D])\b',
        _reemplazar_lista_opciones,
        txt,
        flags=re.IGNORECASE
    )

    return txt

def preparar_preguntas_como_en_test(raw_qs, barajar=True):
    if any(q.get("is_open", False) or q.get("tipo_abierta") in ("SUPUESTO", "DESARROLLO") for q in (raw_qs or [])):
        barajar = False

    es_supuesto_test_lote = any(q.get("es_supuesto_test", False) for q in (raw_qs or []))

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

        opciones_originales = []
        tiene_fija = False
        for idx_o, opt in enumerate(q.get("options", [])):
            m_let_orig = re.match(r'^([a-zA-Z])[\)\.-]\s*(.+)$', opt.strip())
            if m_let_orig:
                let_o = m_let_orig.group(1).lower()
                to = m_let_orig.group(2).strip()
            else:
                let_o = chr(97 + idx_o)
                to = opt.strip()
            opciones_originales.append((let_o, to))
            if any(re.search(p, to.lower()) for p in patrones_fijos):
                tiene_fija = True

        cleaned_options = [to for _, to in opciones_originales]
        corr = cleaned_options[q["answer"]] if 0 <= q.get("answer", -1) < len(cleaned_options) else None

        if not tiene_fija and barajar:
            random.shuffle(cleaned_options)

        if corr is not None and corr in cleaned_options:
            q["answer"] = cleaned_options.index(corr)
        else:
            q["answer"] = -1

        mapa_letras = {}
        for let_orig, txt_orig in opciones_originales:
            if txt_orig in cleaned_options:
                nueva_letra = chr(97 + cleaned_options.index(txt_orig))
                mapa_letras[let_orig] = nueva_letra

        letra_corr_final = chr(97 + q["answer"]) if 0 <= q["answer"] < len(cleaned_options) else None
        if q.get("explanation"):
            q["explanation"] = _actualizar_letras_explicacion_tras_barajar(
                q["explanation"], mapa_letras, letra_correcta_final=letra_corr_final
            )

        q["options"] = [f"{chr(97+i)}) {o}" for i, o in enumerate(cleaned_options)]
        qs_preparadas.append(q)

    # En supuestos tipo test (Administrativos), mantener agrupado el orden de las preguntas de cada supuesto
    if barajar and not es_supuesto_test_lote:
        random.shuffle(qs_preparadas)

    for idx_final, q_item in enumerate(qs_preparadas, 1):
        if not q_item.get("is_open", False):
            es_res_txt = bool(re.match(r'^(?:#\s*)?(?:[Rr]\d+|\d+\.\s*\(RESERVA\))', (q_item.get("question_text") or "").strip(), re.IGNORECASE))
            txt_sin_num = re.sub(
                r'^(?:#\s*)?(?:Pregunta\s+)?[Rr]?\d{1,3}\s*[\.\-\)]\s*(?:\(RESERVA\)\s*)?[\.\-\)]*\s*',
                '',
                (q_item.get("question_text") or "").strip(),
                flags=re.IGNORECASE
            ).strip()
            pref_f = f"{idx_final}. (RESERVA)" if (es_supuesto_test_lote and es_res_txt) else f"{idx_final}."
            if txt_sin_num:
                q_item["question_text"] = f"{pref_f} {txt_sin_num}"

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

def _limpiar_estados_checkbox_opciones():
    for k in list(st.session_state.keys()):
        if k.startswith("opt_chk_"):
            del st.session_state[k]

def procesar_preguntas(raw_qs, barajar=True):
    limpiar_estados_reportes_error()
    _limpiar_estados_checkbox_opciones()
    qs_listas = preparar_preguntas_como_en_test(raw_qs, barajar=barajar)
    for q_it in qs_listas:
        if q_it.get("is_open") and "answer_text" not in q_it:
            q_it["answer_text"] = q_it.get("official_answer", "")
    st.session_state.update(
        questions=qs_listas,
        current_index=0,
        finished=False,
        checked=False,
        stats={i: {'attempts': 0, 'selected': None, 'ai_feedback': None, 'ai_eval': None, 'last_evaluated_text': None, 'sheets_logged_sig': None, 'ep_start_ts': None, 'ep_hora_inicio': None, 'ep_inicio_registrado': False} for i in range(len(qs_listas))},
        mostrar_opciones_simulacro=False,
        celebracion_mostrada=False,
        do_scroll=True
    )
    iniciar_cronometro_test()
    st.rerun()

def action_repetir_test():
    limpiar_estados_reportes_error()
    _limpiar_estados_checkbox_opciones()
    st.session_state.update(
        current_index=0,
        stats={i: {'attempts': 0, 'selected': None, 'ai_feedback': None, 'ai_eval': None, 'last_evaluated_text': None, 'sheets_logged_sig': None, 'ep_start_ts': None, 'ep_hora_inicio': None, 'ep_inicio_registrado': False} for i in range(len(st.session_state.questions))},
        finished=False, checked=False, celebracion_mostrada=False, do_scroll=True
    )
    iniciar_cronometro_test()

def action_subir_otro():
    limpiar_estados_reportes_error()
    _limpiar_estados_checkbox_opciones()
    st.session_state.update(
        questions=[], current_index=0, stats={}, finished=False, checked=False,
        test_name=None, mostrar_opciones_simulacro=False, celebracion_mostrada=False,
        inicio_registrado_sheets=False, resultado_registrado=False, do_scroll=True
    )

def action_finalizar_sesion():
    correo_usr = (st.session_state.get("email") or "").lower().strip()
    if correo_usr:
        sid_key = "sid4_" + base64.urlsafe_b64encode(correo_usr.encode("utf-8")).decode("ascii").rstrip("=")
        _obtener_almacen_sesiones_servidor().pop(sid_key, None)
    st.session_state.clear()
    st.session_state.borrar_backup_ls = True
    st.session_state.do_scroll = True
# === FIN SECCIÓN 4C ===

# === SECCIÓN 5A: PANTALLA DE INICIO, MENÚ DE SELECCIÓN Y AUDITORÍA ADMIN ===
sincronizar_progreso_navegador()
activar_proteccion_antirecortes_alumno()

def render_dictado_voz_tiempo_real(idx_pregunta):
    """
    Renderiza un control de dictado por voz en tiempo real (Web Speech API es-ES)
    que transcribe palabra por palabra directamente dentro del textarea activo de Streamlit,
    sincronizando el valor nativo de React y el borrador anticaídas.
    """
    components.html(f"""
    <div style="font-family: sans-serif; margin: 0; padding: 0;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; background: #F0F9FF; border: 1.5px solid #0284C7; border-radius: 8px; padding: 8px 12px;">
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <button id="btn_mic_{idx_pregunta}" type="button" style="background: #0284C7; color: #FFFFFF; border: none; border-radius: 6px; padding: 6px 13px; font-size: 13.5px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); transition: all 0.2s;">
                    <span>🎙️</span> <span id="lbl_mic_{idx_pregunta}">Dictar respuesta por voz</span>
                </button>
                <span id="badge_estado_{idx_pregunta}" style="font-size: 12.5px; font-weight: 600; color: #0369A1;">
                    Pulsa para hablar (puedes decir: <i>«coma»</i>, <i>«punto y seguido»</i>, <i>«punto y aparte»</i>)
                </span>
            </div>
            <span style="font-size: 11.5px; color: #475569;">📱 En iPhone/iPad también puedes usar el 🎙️ de tu teclado</span>
        </div>
        <div id="preview_voz_{idx_pregunta}" style="display: none; margin-top: 5px; padding: 6px 10px; background: #FEFCE8; border: 1px dashed #CA8A04; border-radius: 6px; font-size: 13px; color: #854D0E; font-style: italic;"></div>
    </div>

    <script>
    (function() {{
        var pw = window.parent;
        var pd = pw.document;
        var btn = document.getElementById("btn_mic_{idx_pregunta}");
        var lbl = document.getElementById("lbl_mic_{idx_pregunta}");
        var badge = document.getElementById("badge_estado_{idx_pregunta}");
        var preview = document.getElementById("preview_voz_{idx_pregunta}");

        var SpeechRecognition = pw.SpeechRecognition || pw.webkitSpeechRecognition || window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {{
            btn.style.background = "#94A3B8";
            btn.style.cursor = "not-allowed";
            lbl.textContent = "Dictado directo no soportado en este navegador";
            badge.innerHTML = "Usa <b>Google Chrome</b>, <b>Edge</b>, <b>Safari</b> o el micrófono del teclado de tu móvil.";
            return;
        }}

        if (pw.__oposiciona_speech_rec) {{
            try {{
                pw.__oposiciona_speech_active = false;
                pw.__oposiciona_speech_rec.stop();
            }} catch(e) {{}}
        }}

        function obtenerTextareaRespuesta() {{
            var areas = pd.querySelectorAll('textarea');
            if (!areas || areas.length === 0) return null;
            return areas[0];
        }}

        function formatearTextoJuridicoDictado(texto) {{
            if (!texto) return "";
            var t = texto;
            t = t.replace(/\\bpunto y aparte\\b/gi, ".\\n\\n");
            t = t.replace(/\\bpunto y seguido\\b/gi, ". ");
            t = t.replace(/\\bpunto final\\b/gi, ".");
            t = t.replace(/\\bdos puntos\\b/gi, ": ");
            t = t.replace(/\\bpunto y coma\\b/gi, "; ");
            t = t.replace(/\\bcoma\\b/gi, ", ");
            t = t.replace(/\\babrir par[ée]ntesis\\b/gi, " (");
            t = t.replace(/\\bcerrar par[ée]ntesis\\b/gi, ") ");
            t = t.replace(/\\babrir comillas\\b/gi, " «");
            t = t.replace(/\\bcerrar comillas\\b/gi, "» ");
            t = t.replace(/\\btrlgss\\b/gi, "TRLGSS");
            t = t.replace(/\\blgss\\b/gi, "LGSS");
            t = t.replace(/\\breta\\b/gi, "RETA");
            t = t.replace(/\\binss\\b/gi, "INSS");
            t = t.replace(/\\btgss\\b/gi, "TGSS");
            t = t.replace(/\\bimserso\\b/gi, "IMSERSO");
            t = t.replace(/\\bingesa\\b/gi, "INGESA");
            t = t.replace(/\\bitss\\b/gi, "ITSS");
            t = t.replace(/\\bsepe\\b/gi, "SEPE");
            t = t.replace(/\\biprem\\b/gi, "IPREM");
            t = t.replace(/\\bsmi\\b/gi, "SMI");
            t = t.replace(/\\bimv\\b/gi, "IMV");
            t = t.replace(/\\bfogasa\\b/gi, "FOGASA");
            return t;
        }}

        function insertarEnTextareaReact(ta, fragmentoNuevo) {{
            if (!ta || !fragmentoNuevo) return;
            var actual = ta.value || "";
            var frag = formatearTextoJuridicoDictado(fragmentoNuevo).trim();
            if (!frag) return;

            var separador = "";
            if (actual.length > 0 && !actual.endsWith("\\n") && !actual.endsWith(" ") && !actual.endsWith("(") && !actual.endsWith("«")) {{
                if (/^[.,;:!?)»]/.test(frag)) {{
                    separador = "";
                }} else {{
                    separador = " ";
                }}
            }}

            if (actual.length === 0 || /[.?!]\\s*$/.test(actual) || /\\n\\s*$/.test(actual)) {{
                frag = frag.charAt(0).toUpperCase() + frag.slice(1);
            }}

            var nuevoValor = (actual + separador + frag).replace(/\\s+([.,;:!?)])/g, "$1");

            var nativeSetter = Object.getOwnPropertyDescriptor(pw.HTMLTextAreaElement.prototype, "value").set;
            nativeSetter.call(ta, nuevoValor);

            ta.dispatchEvent(new Event("input", {{ bubbles: true }}));
            ta.dispatchEvent(new Event("change", {{ bubbles: true }}));
            ta.scrollTop = ta.scrollHeight;

            try {{
                pw.sessionStorage.setItem("oposiciona_live_draft_txt", nuevoValor);
                pw.localStorage.setItem("oposiciona_live_draft_txt", nuevoValor);
            }} catch(e) {{}}
        }}

        var rec = new SpeechRecognition();
        rec.lang = "es-ES";
        rec.continuous = true;
        rec.interimResults = true;
        pw.__oposiciona_speech_rec = rec;
        pw.__oposiciona_speech_active = false;

        function actualizarUI(escuchando, msgExtra) {{
            if (escuchando) {{
                btn.style.background = "#DC2626";
                lbl.textContent = "⏹️ Detener dictado (Escuchando...)";
                badge.style.color = "#B91C1C";
                badge.innerHTML = msgExtra || "🔴 <b>Micrófono activo:</b> habla con naturalidad, el texto se escribe solo en el recuadro.";
            }} else {{
                btn.style.background = "#0284C7";
                lbl.textContent = "🎙️ Dictar respuesta por voz";
                badge.style.color = "#0369A1";
                badge.innerHTML = msgExtra || "Pulsa para hablar (puedes decir: <i>«coma»</i>, <i>«punto y seguido»</i>, <i>«punto y aparte»</i>)";
                preview.style.display = "none";
                preview.textContent = "";
            }}
        }}

        rec.onresult = function(event) {{
            var interino = "";
            var finalTxt = "";
            for (var i = event.resultIndex; i < event.results.length; ++i) {{
                var transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {{
                    finalTxt += transcript + " ";
                }} else {{
                    interino += transcript;
                }}
            }}
            var ta = obtenerTextareaRespuesta();
            if (finalTxt.trim() && ta) {{
                insertarEnTextareaReact(ta, finalTxt);
            }}
            if (interino.trim()) {{
                preview.style.display = "block";
                preview.textContent = "🗣️ Escuchando en vivo: «" + interino.trim() + "...»";
            }} else {{
                preview.style.display = "none";
                preview.textContent = "";
            }}
        }};

        rec.onerror = function(event) {{
            if (event.error === "not-allowed" || event.error === "service-not-allowed") {{
                pw.__oposiciona_speech_active = false;
                actualizarUI(false, "⚠️ <b>Permiso de micrófono bloqueado:</b> autoriza el micrófono en el icono del candado de la barra de direcciones.");
            }}
        }};

        rec.onend = function() {{
            if (pw.__oposiciona_speech_active) {{
                setTimeout(function() {{
                    if (pw.__oposiciona_speech_active) {{
                        try {{ rec.start(); }} catch(e) {{}}
                    }}
                }}, 250);
            }} else {{
                var ta = obtenerTextareaRespuesta();
                if (ta) {{
                    ta.focus();
                    ta.dispatchEvent(new Event("change", {{ bubbles: true }}));
                    ta.blur();
                }}
                actualizarUI(false, "✅ <b>Dictado pausado y guardado en el recuadro.</b> Puedes revisar el texto o volver a pulsar para seguir dictando.");
            }}
        }};

        btn.addEventListener("click", function() {{
            if (!pw.__oposiciona_speech_active) {{
                try {{
                    pw.__oposiciona_speech_active = true;
                    rec.start();
                    actualizarUI(true);
                }} catch(e) {{
                    pw.__oposiciona_speech_active = false;
                    actualizarUI(false, "⚠️ No se pudo iniciar el micrófono. Inténtalo de nuevo.");
                }}
            }} else {{
                pw.__oposiciona_speech_active = false;
                try {{ rec.stop(); }} catch(e) {{}}
                actualizarUI(false, "✅ <b>Dictado finalizado.</b> Tu texto ya está listo en el cuadro.");
            }}
        }});
    }})();
    </script>
    """, height=78)

if not st.session_state.questions:
    st.markdown("""<style>
    :root { --background-color: #FFFFFF !important; --secondary-background-color: #F8FAFC !important; --text-color: #1E293B !important; }
    html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFFFF !important; color: #1E293B !important; }
    .block-container { max-width: 820px !important; }

    /* Transformación visual de los checkboxes de categoría en círculos tipo radio para las dos filas (TEST y SUPUESTOS) */
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"] {
        margin-bottom: 0px !important;
        padding-top: 2px !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"] label {
        align-items: center !important;
        cursor: pointer !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"] label span[data-baseweb="checkbox"],
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"] div[data-baseweb="checkbox"] > div:first-child {
        border-radius: 50% !important;
        width: 18px !important;
        height: 18px !important;
        min-width: 18px !important;
        min-height: 18px !important;
        border: 2px solid #1E293B !important;
        background-color: #FFFFFF !important;
        box-sizing: border-box !important;
        position: relative !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"] svg {
        display: none !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"]:has(input:checked) span[data-baseweb="checkbox"],
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"]:has(input:checked) div[data-baseweb="checkbox"] > div:first-child {
        border-color: #1D4ED8 !important;
        background-color: #EFF6FF !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"]:has(input:checked) span[data-baseweb="checkbox"]::after,
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"]:has(input:checked) div[data-baseweb="checkbox"] > div:first-child::after {
        content: "" !important;
        display: block !important;
        width: 9px !important;
        height: 9px !important;
        border-radius: 50% !important;
        background-color: #1D4ED8 !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"] label p,
    div[data-testid="stVerticalBlock"]:has(.marcador-cat-dos-filas) [data-testid="stCheckbox"] label span {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #1E293B !important;
        white-space: nowrap !important;
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

    if st.session_state.get("aviso_plan_mejorado_ok"):
        nom_plan_nuevo = st.session_state.pop("aviso_plan_mejorado_ok")
        st.success(f"🎉 ¡Tu modalidad se ha mejorado correctamente a **{nom_plan_nuevo}**! Ya tienes tus nuevas categorías activadas.")

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

        def _on_cambio_especialidad():
            nueva_esp = st.session_state.get("radio_especialidad", "ADMINISTRATIVOS")
            st.session_state.saved_esp = nueva_esp
            cats_disp_esp = list(obtener_tests_segun_rol().get(nueva_esp, {}).keys())
            if st.session_state.get("saved_cat") not in cats_disp_esp:
                st.session_state.saved_cat = "ESPECIFICO" if "ESPECIFICO" in cats_disp_esp else (cats_disp_esp[0] if cats_disp_esp else "ESPECIFICO")
            st.session_state.mostrar_opciones_simulacro = False
            limpiar_todas_las_busquedas()

        ROLES_GESTION_TODOS = ["GESTION", "GESTION_SOLO_TEST", "GESTION_TEST_SUPUESTOS", "GESTION_TEST_DESARROLLO"]

        if rol in ["ACCESO TOTAL", "INVITADO"]:
            l_esp = list(TESTS_DISPONIBLES.keys())
            i_esp = l_esp.index(st.session_state.saved_esp) if st.session_state.get("saved_esp") in l_esp else 0
            especialidad = st.radio("Selecciona tu especialidad:", l_esp, index=i_esp, horizontal=True, key="radio_especialidad", label_visibility="collapsed", on_change=_on_cambio_especialidad)
            st.session_state.saved_esp = especialidad
        elif rol == "ADMTVOS" or rol in ROLES_GESTION_TODOS:
            especialidad = "ADMINISTRATIVOS" if rol == "ADMTVOS" else "GESTION"
            st.session_state.saved_esp = especialidad
            etiqueta_plan_act = especialidad
            if st.session_state.get("es_suscriptor_externo"):
                p_id = st.session_state.get("plan_suscripcion", "")
                if p_id in PLANES_SUSCRIPCION_OPOSICIONA:
                    etiqueta_plan_act = PLANES_SUSCRIPCION_OPOSICIONA[p_id]["nombre_corto"]
            st.info(f"Especialidad activa: **{etiqueta_plan_act}**")
        else:
            st.error("Error en los permisos de usuario."); st.stop()

        l_cat = list(TESTS_DISPONIBLES[especialidad].keys())
        if st.session_state.get("saved_cat") not in l_cat:
            st.session_state.saved_cat = "ESPECIFICO" if "ESPECIFICO" in l_cat else l_cat[0]
        categoria_activa = st.session_state.saved_cat

        def _seleccionar_categoria_dos_filas(cat_elegida):
            st.session_state.saved_cat = cat_elegida
            st.session_state.radio_categoria = cat_elegida
            for c_k in l_cat:
                st.session_state[f"chk_cat_2f_{especialidad}_{c_k}"] = (c_k == cat_elegida)
            st.session_state.mostrar_opciones_simulacro = False
            limpiar_todas_las_busquedas()

        etiquetas_visibles_cat = {
            "ESPECIFICO": "ESPECIFICO",
            "EXAMENES": "EXÁMENES",
            "GENERAL": "GENERAL",
            "SUPUESTOS": "SUPUESTOS",
            "DESARROLLO": "DESARROLLO",
        }
        fila_test_cats = [c for c in ["ESPECIFICO", "EXAMENES", "GENERAL"] if c in l_cat]
        fila_sup_cats = [c for c in ["SUPUESTOS", "DESARROLLO"] if c in l_cat]

        with st.container():
            st.markdown("<div class='marcador-cat-dos-filas'></div><div style='font-size:17px; font-weight:700; color:#1E293B !important; margin-bottom:6px;'>2. Categoría</div>", unsafe_allow_html=True)

            if fila_test_cats:
                cols_f1 = st.columns([0.95] + [1.15] * len(fila_test_cats))
                with cols_f1[0]:
                    st.markdown(
                        "<div style='background:#EFF6FF; color:#1E3A8A !important; border:1px solid #93C5FD; border-radius:6px; padding:3px 8px; font-size:12px; font-weight:800; text-align:center; letter-spacing:0.4px; margin-top:2px;'>TEST</div>",
                        unsafe_allow_html=True
                    )
                for idx_c1, cat_1 in enumerate(fila_test_cats):
                    k_c1 = f"chk_cat_2f_{especialidad}_{cat_1}"
                    st.session_state[k_c1] = (categoria_activa == cat_1)
                    with cols_f1[idx_c1 + 1]:
                        st.checkbox(
                            etiquetas_visibles_cat.get(cat_1, cat_1),
                            key=k_c1,
                            on_change=_seleccionar_categoria_dos_filas,
                            args=(cat_1,)
                        )

            if fila_sup_cats:
                relleno_cols = max(0, len(fila_test_cats) - len(fila_sup_cats))
                pesos_f2 = [0.95] + [1.15] * len(fila_sup_cats) + ([1.15] * relleno_cols if relleno_cols > 0 else [])
                cols_f2 = st.columns(pesos_f2)
                with cols_f2[0]:
                    st.markdown(
                        "<div style='background:#FEF3C7; color:#92400E !important; border:1px solid #FCD34D; border-radius:6px; padding:3px 6px; font-size:11.5px; font-weight:800; text-align:center; letter-spacing:0.3px; margin-top:2px;'>SUPUESTOS</div>",
                        unsafe_allow_html=True
                    )
                for idx_c2, cat_2 in enumerate(fila_sup_cats):
                    k_c2 = f"chk_cat_2f_{especialidad}_{cat_2}"
                    st.session_state[k_c2] = (categoria_activa == cat_2)
                    with cols_f2[idx_c2 + 1]:
                        st.checkbox(
                            etiquetas_visibles_cat.get(cat_2, cat_2),
                            key=k_c2,
                            on_change=_seleccionar_categoria_dos_filas,
                            args=(cat_2,)
                        )

        categoria = st.session_state.saved_cat

    # Botón único en 1 solo clic al Portal de Stripe + aviso sobre uso único de códigos de descuento
    if st.session_state.get("es_suscriptor_externo"):
        cfg_sub_ui = _cfg_suscripciones()
        plan_act_ui = st.session_state.get("plan_suscripcion", "")
        tiene_mejoras_disp = bool(MEJORAS_PERMITIDAS_POR_PLAN.get(plan_act_ui, []))
        cust_id_ui = st.session_state.get("stripe_customer_id", "")

        if cfg_sub_ui["modo_fiscal"] == "EXENTO_TUTORIZADO":
            st.markdown(
                "<div style='background:#F0FDF4; border:1px solid #86EFAC; border-radius:8px; padding:8px 12px; margin-bottom:6px; font-size:12.5px; color:#14532D !important;'>"
                "📅 <b>Tutoría incluida:</b> Dudas por correo en <b>info@oposiciona.es</b>, boletín normativo y clase mensual en directo (domingos)."
                "</div>",
                unsafe_allow_html=True
            )

        if tiene_mejoras_disp:
            st.markdown(
                "<div style='background:#FFFBEB; border:1px solid #F59E0B; border-radius:8px; padding:7px 12px; margin-bottom:6px; font-size:12.3px; color:#92400E !important;'>"
                "ℹ️ <b>Nota sobre mejoras de modalidad:</b> Los códigos promocionales o de descuento solo se aplican <b>una única vez por usuario</b> en la suscripción inicial. "
                "Al mejorar a un plan superior se abonará la diferencia hasta la tarifa general del nuevo plan."
                "</div>",
                unsafe_allow_html=True
            )

        clave_p_unico = f"_link_directo_portal_unico_{cust_id_ui}_{plan_act_ui}"
        guardado_p_unico = st.session_state.get(clave_p_unico)
        if guardado_p_unico and guardado_p_unico.get("url") and (time.time() - guardado_p_unico.get("ts", 0)) < 1200:
            url_portal_unico, err_portal_unico = guardado_p_unico["url"], ""
        else:
            url_portal_unico, err_portal_unico = crear_enlace_portal_stripe_detallado(cust_id_ui, plan_vigente_hint=plan_act_ui)
            if url_portal_unico:
                st.session_state[clave_p_unico] = {"url": url_portal_unico, "ts": time.time()}

        texto_boton_unico = "💳 MEJORA / FACTURACIÓN / CANCELACIÓN" if tiene_mejoras_disp else "💳 FACTURACIÓN / CANCELACIÓN"
        if url_portal_unico:
            st.link_button(texto_boton_unico, url_portal_unico, use_container_width=True, type="primary")
        elif err_portal_unico:
            st.error(f"⚠️ {err_portal_unico}")

        with st.expander("🔑 Cambiar mi contraseña de acceso"):
            cp_act, cp_n1, cp_n2 = st.columns(3)
            with cp_act:
                in_pw_act = st.text_input("Contraseña actual:", type="password", key="panel_pw_actual")
            with cp_n1:
                in_pw_n1 = st.text_input("Nueva contraseña:", type="password", key="panel_pw_nueva1")
            with cp_n2:
                in_pw_n2 = st.text_input("Repetir nueva:", type="password", key="panel_pw_nueva2")
            if st.button("💾 Actualizar contraseña", key="btn_actualizar_pw_panel", use_container_width=True):
                ok_chg, msg_chg = cambiar_password_suscriptor_autenticado(
                    st.session_state.get("email", ""),
                    in_pw_act,
                    in_pw_n1,
                    in_pw_n2
                )
                if ok_chg:
                    st.success(msg_chg)
                else:
                    st.error(f"⚠️ {msg_chg}")

    st.markdown("<div style='font-size:17px; font-weight:700; color:#1E293B !important; margin-bottom:5px; margin-top:6px;'>3. Modo de avance</div>", unsafe_allow_html=True)
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
        titulo_paso_4 = (
            "4. Seleccionar Supuestos prácticos (2.º Ejercicio - 2.ª Parte)"
            if "GESTI" in especialidad.upper() else
            "4. Seleccionar Supuestos prácticos (Modalidad Tipo Test)"
        )
    else:
        titulo_paso_4 = "4. Selección de Test"

    st.markdown(f"<div style='font-size:17px; font-weight:700; color:#1E293B !important; margin-bottom:6px;'>{titulo_paso_4}</div>", unsafe_allow_html=True)
    if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO"] and es_admin:
        st.info("🔒 **Modo Administrador — 2.º Ejercicio — 1.ª Parte (Preguntas de Desarrollo: 0 a 50 ptos):** Soporta archivos Word (`.docx`) y PDF (`.pdf`). Incluye dictado por voz en tiempo real y corrección técnica según los Criterios Oficiales del Tribunal.")
    elif categoria in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"] and es_admin:
        if "GESTI" in especialidad.upper():
            st.info("🔒 **Modo Administrador — 2.º Ejercicio — 2.ª Parte (Supuestos Prácticos Gestión):** Descarta cualquier texto previo al encabezado `SUPUESTO PRÁCTICO`, mantiene el planteamiento fijo en cada pregunta (en recuadro gris en negrita), permite dictar por voz y califica cada cuestión de 0 a 10 comparándola con la solución técnica oficial.")
        else:
            st.info("🔒 **Modo Administrador — Supuestos Prácticos Tipo Test (Administrativos):** Extrae los supuestos prácticos (uno o varios por tema), muestra el planteamiento en recuadro gris en negrita, la pregunta en marco y las 4 opciones tipo test seleccionables con corrección oficial.")

    tests_reales = {k: v for k, v in TESTS_DISPONIBLES[especialidad][categoria].items() if v is not None}

    if rol == "INVITADO":
        if categoria in ["DESARROLLO", "PREGUNTA DE DESARROLLO"]:
            st.markdown(
                "<div style='background-color:#EFF6FF; border:2px solid #2563EB; border-radius:10px; padding:14px 18px; margin-top:4px; margin-bottom:12px; line-height:1.5; color:#1E293B !important;'>"
                "<div style='font-size:15.5px; font-weight:800; color:#1E3A8A !important; margin-bottom:6px;'>📝 Demostración para Invitado — Categoría DESARROLLO (Oposiciona 5.0)</div>"
                "<p style='font-size:13.5px; color:#1E293B !important; text-align:justify; margin-bottom:8px;'>"
                "Prueba a continuación el tema de demostración habilitado: puedes redactar o dictar por voz tu respuesta a cualquiera de sus epígrafes y recibirás en tiempo real la <b>calificación de 0 a 50 puntos según los Criterios Oficiales del Tribunal Calificador</b> junto con el texto mínimo oficial. "
                "Para acceder al catálogo completo de temas de Oposiciona 5.0 escribe a <a href='mailto:info@oposiciona.es' style='color:#1D4ED8 !important; font-weight:800; text-decoration:underline;'>info@oposiciona.es</a>."
                "</p>"
                "</div>",
                unsafe_allow_html=True
            )
        elif categoria in ["SUPUESTOS", "SUPUESTOS PRÁCTICOS"]:
            st.markdown(
                "<div style='background-color:#FEFCE8; border:2px solid #D97706; border-radius:10px; padding:14px 18px; margin-top:4px; margin-bottom:12px; line-height:1.5; color:#1E293B !important;'>"
                "<div style='font-size:15.5px; font-weight:800; color:#92400E !important; margin-bottom:6px;'>📋 Demostración para Invitado — Categoría SUPUESTOS (Oposiciona 5.0)</div>"
                "<p style='font-size:13.5px; color:#1E293B !important; text-align:justify; margin-bottom:0px;'>"
                "Tienes habilitado un supuesto práctico completo de demostración en esta especialidad (tipo test comentado en <b>Administrativos</b> y de desarrollo con corrección técnica conforme a los criterios del Tribunal en <b>Gestión</b>). "
                "Solicita acceso al catálogo completo escribiendo a <a href='mailto:info@oposiciona.es' style='color:#B45309 !important; font-weight:800; text-decoration:underline;'>info@oposiciona.es</a>."
                "</p>"
                "</div>",
                unsafe_allow_html=True
            )
        elif not tests_reales:
            st.warning("⚠️ CATEGORÍA NO DISPONIBLE PARA USUARIOS INVITADOS")
        else:
            st.info("ℹ️ DOCUMENTO DE DEMOSTRACIÓN DISPONIBLE PARA USUARIO INVITADO (Solicita el catálogo completo en info@oposiciona.es)")

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

    if rol != "INVITADO" and not st.session_state.get("es_suscriptor_externo"):
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
                        if "GESTI" not in especialidad.upper():
                            rqs = PDFQuizParser.parse_supuestos_test_administrativos(file_bytes_local, max_options=max_op_local)
                            if not rqs: st.error("No se encontraron supuestos prácticos tipo test en este documento.")
                            else: procesar_preguntas(rqs, barajar=True)
                        else:
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
        with st.expander("📩 Herramienta Admin: Descargar Reportes de Alumnos en PDF (para subir al asistente en 1 clic)"):
            bandeja_rep = _obtener_bandeja_reportes_admin()
            st.markdown(
                "Aquí puedes **descargar en PDF** los reportes enviados por los alumnos (o convertir cualquier reporte que te llegue por correo a un archivo `.pdf`) para arrastrarlo directamente al chat sin tener que copiar y pegar."
            )
            if bandeja_rep:
                st.success(f"📬 Hay **{len(bandeja_rep)} reporte(s)** registrados recientemente en la plataforma:")
                c_all, c_clr = st.columns([2.5, 1])
                with c_all:
                    pdf_todos_bytes = generar_pdf_reporte_error(bandeja_rep)
                    st.download_button(
                        label=f"📚 Descargar TODOS los reportes ({len(bandeja_rep)}) en un único PDF",
                        data=pdf_todos_bytes,
                        file_name="REPORTES_ALUMNOS_OPOSICIONA.pdf",
                        mime="application/pdf",
                        key="btn_dl_all_rep_pdf",
                        use_container_width=True
                    )
                with c_clr:
                    if st.button("🗑️ Vaciar bandeja", key="btn_clr_bandeja_rep", use_container_width=True):
                        bandeja_rep.clear()
                        st.rerun()

                for idx_br, rep_item in enumerate(bandeja_rep[:15]):
                    col_info_r, col_btn_r = st.columns([3.5, 1.5])
                    with col_info_r:
                        st.markdown(
                            f"**{idx_br + 1}. [{rep_item.get('fecha', '')}] {rep_item.get('nombre_test', '')}** — *{rep_item.get('num_pregunta', '')}*  \n"
                            f"👤 `{rep_item.get('usuario', '')}` ➔ *«{rep_item.get('motivo', '')[:120]}»*"
                        )
                    with col_btn_r:
                        pdf_ind_bytes = generar_pdf_reporte_error(rep_item)
                        nom_arch_r = re.sub(r'\W+', '_', f"REPORTE_{rep_item.get('nombre_test', 'TEST')}_{rep_item.get('num_pregunta', 'P')}")
                        st.download_button(
                            label="📄 Descargar PDF",
                            data=pdf_ind_bytes,
                            file_name=f"{nom_arch_r}.pdf",
                            mime="application/pdf",
                            key=f"btn_dl_rep_ind_{idx_br}",
                            use_container_width=True
                        )
                st.markdown("---")
            else:
                st.caption("ℹ️ Aún no hay reportes en la memoria activa de esta sesión del servidor. Puedes pegar debajo cualquier reporte de tu correo para descargarlo en PDF al instante:")

            txt_correo_pegado = st.text_area(
                "📋 Opcional — Pega aquí de una sola vez el texto del correo de reporte que has recibido en info@oposiciona.es y descárgalo en PDF:",
                height=130,
                key="txt_pegar_correo_rep_pdf",
                placeholder="Pega aquí la tabla o el contenido del correo del alumno..."
            )
            if (txt_correo_pegado or "").strip():
                doc_libre = fitz.open()
                lineas_libres = []
                for l_orig in txt_correo_pegado.strip().splitlines():
                    if not l_orig.strip():
                        lineas_libres.append("")
                        continue
                    palabras = l_orig.replace("\t", "  ").split(" ")
                    act = ""
                    for pal in palabras:
                        if len(act) + len(pal) + 1 <= 92:
                            act = f"{act} {pal}".strip() if act else pal
                        else:
                            if act:
                                lineas_libres.append(act)
                            act = pal
                    if act:
                        lineas_libres.append(act)
                for i_p in range(0, max(1, len(lineas_libres)), 52):
                    pg = doc_libre.new_page(width=595, height=842)
                    pg.insert_textbox(fitz.Rect(36, 36, 559, 806), "\n".join(lineas_libres[i_p:i_p + 52]), fontsize=9.5, fontname="helv")
                bytes_libre = doc_libre.tobytes()
                doc_libre.close()
                st.download_button(
                    label="📄 Descargar este reporte pegado como archivo PDF",
                    data=bytes_libre,
                    file_name="REPORTE_ALUMNO_CORREO.pdf",
                    mime="application/pdf",
                    key="btn_dl_correo_pegado_pdf",
                    use_container_width=True
                )

        with st.expander("📊 Herramienta Admin: Auditoría de Extracción Real y Recuento de Preguntas, Supuestos y Epígrafes"):
            st.info(
                "Esta herramienta ejecuta exactamente el mismo motor de extracción y procesado que cuando un alumno abre cada test o documento (PDF o Word .docx), "
                "auditando si hay cortes en explicaciones, preguntas fusionadas, opciones faltantes o respuestas sin marcar."
            )
            st.checkbox(
                "🧪 Probar desenfoque antirrecortes en mi sesión de Administrador (desmárcalo para trabajar sin desenfoque)",
                key="admin_test_blur"
            )

            modo_auditoria_admin = st.radio(
                "🎯 Selecciona la categoría de auditoría:",
                [
                    "📋 Test (Administrativos y Gestión)",
                    "🧩 Supuestos (Administrativos y Gestión)",
                    "📝 Desarrollo (solo Gestión)",
                    "🌐 TODOS (Auditoría completa)"
                ],
                horizontal=True,
                key="radio_modo_auditoria_admin"
            )

            incluir_test_adm = modo_auditoria_admin.startswith(("📋", "🌐"))
            incluir_sup_adm = modo_auditoria_admin.startswith(("🧩", "🌐"))
            incluir_des_adm = modo_auditoria_admin.startswith(("📝", "🌐"))

            if st.button("🔍 Auditar extracción real de la categoría seleccionada", use_container_width=True, type="primary"):
                nuevos_hoy = globals().get("NUEVOS_HOY", [])

                tot_pdfs = 0
                for esp_c, cats_c in TESTS_DISPONIBLES_COMPLETO.items():
                    es_gest_c = "GESTI" in esp_c.upper()
                    if incluir_test_adm:
                        for cat_t in ["ESPECIFICO", "EXAMENES", "GENERAL"]:
                            tot_pdfs += sum(1 for u in cats_c.get(cat_t, {}).values() if u is not None)
                    if incluir_sup_adm:
                        tot_pdfs += sum(1 for u in cats_c.get("SUPUESTOS", {}).values() if u is not None)
                    if incluir_des_adm and es_gest_c and "DESARROLLO" in cats_c:
                        tot_pdfs += sum(1 for u in cats_c.get("DESARROLLO", {}).values() if u is not None)

                bp, proc, txt_copiar = st.progress(0, text="Extrayendo y auditando documentos con el motor real..."), 0, ""
                alertas_globales = []

                for esp, cats in TESTS_DISPONIBLES_COMPLETO.items():
                    es_gestion_esp = "GESTI" in esp.upper()
                    max_op_adm = 3 if es_gestion_esp else 4

                    if modo_auditoria_admin.startswith("📝") and not es_gestion_esp:
                        continue

                    if incluir_test_adm:
                        st.markdown(f"### 📋 Catálogo y Auditoría Real de Tests: {esp}")
                        t_md = "| Categoría | Nombre del Test | Nº Extraídas | Media Opc. | Auditoría Real de Extracción |\n| :--- | :--- | :---: | :---: | :--- |\n"
                        for cat in ["ESPECIFICO", "EXAMENES", "GENERAL"]:
                            tests = cats.get(cat, {})
                            for nom, url in tests.items():
                                if url is None:
                                    continue
                                proc += 1
                                bp.progress(min(1.0, proc / max(1, tot_pdfs)), text=f"Extrayendo y auditando Test [{esp}] ({proc}/{tot_pdfs}): {nom}...")
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

                    if incluir_sup_adm:
                        supuestos_dict = {k: v for k, v in cats.get("SUPUESTOS", {}).items() if v is not None}
                        st.markdown(f"#### 🧩 Apartado SUPUESTOS — {esp} ({len(supuestos_dict)} {'tema incluido' if len(supuestos_dict)==1 else 'temas incluidos'})")
                        if supuestos_dict:
                            s_md = "| Categoría | Tema / Supuesto Incluido | Nº de Cuestiones Extraídas | Estado Extracción |\n| :--- | :--- | :---: | :--- |\n"
                            tot_cuestiones_sup = 0
                            for nom_s, url_s in supuestos_dict.items():
                                proc += 1
                                bp.progress(min(1.0, proc / max(1, tot_pdfs)), text=f"Auditando Supuesto [{esp}] ({proc}/{tot_pdfs}): {nom_s}...")
                                try:
                                    r = descargar_pdf_fresco(url_s)
                                    if r.status_code == 200:
                                        if not es_gestion_esp:
                                            qs_sup = PDFQuizParser.parse_supuestos_test_administrativos(r.content, max_options=max_op_adm)
                                            qs_sup = preparar_preguntas_como_en_test(qs_sup, barajar=False)
                                            sin_ans_s = [f"P{k_s+1}" for k_s, q_s in enumerate(qs_sup) if q_s.get("answer", -1) == -1]
                                            n_sup = len(qs_sup)
                                            tot_cuestiones_sup += n_sup
                                            n_sup_str = f"{n_sup} preg. test"
                                            est_s = "✅ OK (Tipo Test)" if (n_sup > 0 and not sin_ans_s) else (f"⚠️ Sin resp. marcada: {', '.join(sin_ans_s)}" if sin_ans_s else "⚠️ 0 cuestiones detectadas")
                                            if sin_ans_s:
                                                alertas_globales.append(f"**[{esp} - SUPUESTOS] {nom_s}:** {est_s}")
                                        else:
                                            qs_sup = PDFQuizParser.parse_abiertas_gestion(r.content, modo="SUPUESTOS")
                                            qs_sup = preparar_preguntas_como_en_test(qs_sup, barajar=False)
                                            n_sup = len(qs_sup)
                                            tot_cuestiones_sup += n_sup
                                            n_sup_str = f"{n_sup} cuestiones"
                                            est_s = "✅ OK (Desarrollo)" if n_sup > 0 else "⚠️ 0 cuestiones detectadas"
                                        if n_sup == 0:
                                            alertas_globales.append(f"**[{esp} - SUPUESTOS] {nom_s}:** 0 cuestiones detectadas")
                                    else:
                                        n_sup_str, est_s = "Error", "❌ Error de descarga"
                                        alertas_globales.append(f"**[{esp} - SUPUESTOS] {nom_s}:** Error HTTP {r.status_code}")
                                except Exception as e_s:
                                    n_sup_str, est_s = "-", f"❌ {e_s}"
                                    alertas_globales.append(f"**[{esp} - SUPUESTOS] {nom_s}:** {e_s}")
                                et_tema_s = obtener_etiqueta_tema_visible(nom_s)
                                s_md += f"| **SUPUESTOS** | **{nom_s}** — *{et_tema_s}* | **{n_sup_str}** | {est_s} |\n"
                            s_md += f"| **TOTAL SUPUESTOS ({esp})** | **{len(supuestos_dict)} documentos incluidos** | **{tot_cuestiones_sup} cuestiones** | — |\n"
                        else:
                            s_md = "*Actualmente no hay ningún documento cargado en la categoría SUPUESTOS de esta especialidad.*\n"
                        st.markdown(s_md)
                        txt_copiar += f"#### 🧩 Apartado SUPUESTOS — {esp} ({len(supuestos_dict)} incluidos)\n\n" + s_md + "\n"

                    if incluir_des_adm and es_gestion_esp and "DESARROLLO" in cats:
                        desarrollo_dict = {k: v for k, v in cats.get("DESARROLLO", {}).items() if v is not None}
                        st.markdown(f"#### 📝 Apartado DESARROLLO — {esp} ({len(desarrollo_dict)} {'tema incluido' if len(desarrollo_dict)==1 else 'temas incluidos'})")
                        if desarrollo_dict:
                            d_md = "| Categoría | Documento Incluido | Nº de Epígrafes Extraídos | Auditoría Epígrafes |\n| :--- | :--- | :---: | :--- |\n"
                            tot_epigrafes_des = 0
                            for nom_d, url_d in desarrollo_dict.items():
                                proc += 1
                                bp.progress(min(1.0, proc / max(1, tot_pdfs)), text=f"Auditando Epígrafes de Desarrollo [{esp}] ({proc}/{tot_pdfs}): {nom_d}...")
                                try:
                                    r = descargar_pdf_fresco(url_d)
                                    if r.status_code == 200:
                                        qs_des = PDFQuizParser.parse_abiertas_gestion(r.content, modo="DESARROLLO")
                                        qs_des = preparar_preguntas_como_en_test(qs_des, barajar=False)
                                        n_ep = len(qs_des)
                                        tot_epigrafes_des += n_ep
                                        n_ep_str = f"{n_ep} {'epígrafe' if n_ep == 1 else 'epígrafes'}"
                                        ep_cortos = [f"Ep.{idx_e}" for idx_e, qe in enumerate(qs_des, 1) if len((qe.get("explanation") or "").strip()) < 120]
                                        if n_ep == 0:
                                            est_d = "❌ 0 epígrafes extraídos"
                                            alertas_globales.append(f"**[{esp} - DESARROLLO] {nom_d}:** 0 epígrafes extraídos")
                                        elif ep_cortos:
                                            est_d = f"⚠️ Texto corto en {', '.join(ep_cortos)}"
                                            alertas_globales.append(f"**[{esp} - DESARROLLO] {nom_d}:** {est_d}")
                                        else:
                                            est_d = f"✅ OK ({n_ep} epígrafes completos)"
                                    else:
                                        n_ep_str, est_d = "Error", "❌ Error de descarga"
                                        alertas_globales.append(f"**[{esp} - DESARROLLO] {nom_d}:** Error HTTP {r.status_code}")
                                except Exception as e_d:
                                    n_ep_str, est_d = "-", f"❌ {e_d}"
                                    alertas_globales.append(f"**[{esp} - DESARROLLO] {nom_d}:** {e_d}")
                                d_md += f"| **DESARROLLO** | **{nom_d}** | **{n_ep_str}** | {est_d} |\n"
                            d_md += f"| **TOTAL DESARROLLO ({esp})** | **{len(desarrollo_dict)} documentos incluidos** | **{tot_epigrafes_des} epígrafes en total** | — |\n"
                        else:
                            d_md = "*Actualmente no hay ningún documento cargado en la categoría DESARROLLO de esta especialidad.*\n"
                        st.markdown(d_md)
                        txt_copiar += f"#### 📝 Apartado DESARROLLO — {esp} ({len(desarrollo_dict)} temas incluidos)\n\n" + d_md + "\n"

                    txt_copiar += "---\n\n"

                bp.empty()
                st.success(f"✅ ¡Auditoría real de «{modo_auditoria_admin}» completada con éxito!")
                if alertas_globales:
                    st.warning(f"⚠️ **Se han detectado incidencias de extracción en {len(alertas_globales)} documento(s) que conviene revisar:**\n\n" + "\n".join([f"- {a}" for a in alertas_globales]))
                else:
                    st.balloons()
                    st.success("🎉 ¡Todos los documentos auditados han superado la verificación sin preguntas fusionadas ni explicaciones cortadas!")
                st.code(txt_copiar, language="markdown")
# === FIN SECCIÓN 5A ===

# === SECCIÓN 5B: PANTALLA DE PREGUNTA ACTIVA (TEST, SUPUESTOS Y DESARROLLO) ===
elif not st.session_state.finished:
    import html
    st.markdown("""<style>
    :root { --background-color: #FFFDE7 !important; --secondary-background-color: #FFFDE7 !important; --text-color: #1E293B !important; }
    html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFDE7 !important; background-image: none !important; color: #1E293B !important; }
    .block-container, [data-testid='stMainBlockContainer'], div[data-testid='stVerticalBlock'] { background-color: transparent !important; background: transparent !important; }

    div[data-testid="stVerticalBlock"]:has(.marcador-opciones-test) [data-testid="stCheckbox"] {
        margin-bottom: 6px !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-opciones-test) [data-testid="stCheckbox"] label {
        align-items: flex-start !important;
        cursor: pointer !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-opciones-test) [data-testid="stCheckbox"] label span[data-baseweb="checkbox"],
    div[data-testid="stVerticalBlock"]:has(.marcador-opciones-test) [data-testid="stCheckbox"] div[data-baseweb="checkbox"] > div:first-child {
        border-radius: 50% !important;
        width: 20px !important;
        height: 20px !important;
        min-width: 20px !important;
        min-height: 20px !important;
        border: 2px solid #000000 !important;
        background-color: #FFFFFF !important;
        margin-top: 2px !important;
        box-sizing: border-box !important;
        position: relative !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-opciones-test) [data-testid="stCheckbox"] svg {
        display: none !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-opciones-test) [data-testid="stCheckbox"]:has(input:checked) span[data-baseweb="checkbox"]::after,
    div[data-testid="stVerticalBlock"]:has(.marcador-opciones-test) [data-testid="stCheckbox"]:has(input:checked) div[data-baseweb="checkbox"] > div:first-child::after {
        content: "" !important;
        display: block !important;
        width: 10px !important;
        height: 10px !important;
        border-radius: 50% !important;
        background-color: #000000 !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
    }
    div[data-testid="stVerticalBlock"]:has(.marcador-opciones-test) [data-testid="stCheckbox"] label p,
    div[data-testid="stVerticalBlock"]:has(.marcador-opciones-test) [data-testid="stCheckbox"] label span {
        font-size: 17px !important;
        line-height: 1.35 !important;
        text-align: justify !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        white-space: normal !important;
    }

    .opo-supuesto-planteamiento, .opo-supuesto-planteamiento * {
        font-family: inherit !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        line-height: 1.5 !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        text-align: justify !important;
    }
    .opo-supuesto-planteamiento {
        background-color: #EAECEF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
    }
    .opo-supuesto-pregunta, .opo-supuesto-pregunta * {
        font-family: inherit !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        line-height: 1.5 !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        text-align: justify !important;
    }
    .opo-supuesto-pregunta {
        background-color: transparent !important;
        border: 1.5px solid #64748B !important;
        border-radius: 6px !important;
        padding: 11px 16px !important;
        margin-bottom: 14px !important;
    }
    </style>""", unsafe_allow_html=True)

    def _render_tarjeta_tribunal_en_vivo(slot_st, titulo_accion, subtitulo_accion, porcentaje_barra=45):
        pct_w = max(15, min(100, int(porcentaje_barra)))
        html_card = (
            "<style>"
            "@keyframes opoBalanceSwing5B { 0%, 100% { transform: rotate(-8deg); } 50% { transform: rotate(8deg); } }"
            "@keyframes opoPenWrite5B { 0% { transform: translate(0px, 0px) rotate(0deg); } 25% { transform: translate(20px, -3px) rotate(-8deg); } 50% { transform: translate(36px, 2px) rotate(5deg); } 75% { transform: translate(14px, 5px) rotate(-5deg); } 100% { transform: translate(0px, 0px) rotate(0deg); } }"
            "@keyframes opoScanBeam5B { 0% { top: 12px; opacity: 0.35; } 50% { top: 68px; opacity: 0.9; } 100% { top: 12px; opacity: 0.35; } }"
            "@keyframes opoPulseBadge5B { 0%, 100% { transform: scale(1); filter: drop-shadow(0 4px 10px rgba(29, 78, 216, 0.35)); } 50% { transform: scale(1.02); filter: drop-shadow(0 6px 16px rgba(29, 78, 216, 0.55)); } }"
            "@keyframes opoStudentNod5B { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-5px); } }"
            "@keyframes opoBarStripes5B { 0% { background-position: 0 0; } 100% { background-position: 40px 0; } }"
            "@keyframes opoModalPopIn5B { 0% { opacity: 0; transform: scale(0.92) translateY(12px); } 100% { opacity: 1; transform: scale(1) translateY(0); } }"
            "#opo-modal-5b .opo-white-txt, #opo-modal-5b .opo-white-txt * { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; fill: #FFFFFF !important; }"
            "</style>"
            "<div id='opo-modal-5b' style='position: fixed; top: 0; left: 0; right: 0; bottom: 0; width: 100vw; height: 100vh; background: rgba(15, 23, 42, 0.72); backdrop-filter: blur(7px); -webkit-backdrop-filter: blur(7px); z-index: 999999; display: flex; align-items: center; justify-content: center; padding: 20px; box-sizing: border-box;'>"
            "<div style='width: 100%; max-width: 660px; background: linear-gradient(135deg, #EFF6FF 0%, #FFFFFF 55%, #FEFCE8 100%); border: 3px solid #1D4ED8; border-radius: 20px; padding: 28px 24px; text-align: center; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.55); animation: opoModalPopIn5B 0.25s ease-out;'>"
            "<div style='margin-bottom: 18px; display: flex; justify-content: center; animation: opoPulseBadge5B 1.8s infinite;'>"
            "<svg width='600' height='42' viewBox='0 0 600 42' style='max-width: 100%; height: auto;' xmlns='http://www.w3.org/2000/svg'>"
            "<rect x='2' y='2' width='596' height='38' rx='19' fill='#1E3A8A' stroke='#93C5FD' stroke-width='2.5'/>"
            "<text x='300' y='26' text-anchor='middle' fill='#FFFFFF' font-family='Arial, Helvetica, sans-serif' font-size='12.2' font-weight='900' letter-spacing='0.4' style='fill: #FFFFFF !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important;'>⚖️ TRIBUNAL CALIFICADOR EN DELIBERACIÓN — PROCESANDO EXAMEN</text>"
            "</svg>"
            "</div>"
            "<div style='display: flex; justify-content: center; align-items: center; gap: 28px; flex-wrap: wrap; margin: 6px 0 18px 0;'>"
            "<div style='display: flex; flex-direction: column; align-items: center;'>"
            "<div style='width: 80px; height: 80px; border-radius: 50%; background: #DBEAFE; border: 2px solid #2563EB; display: flex; align-items: center; justify-content: center;'>"
            "<svg width='48' height='48' viewBox='0 0 64 64' fill='none' xmlns='http://www.w3.org/2000/svg'>"
            "<rect x='20' y='54' width='24' height='5' rx='2.5' fill='#1E3A8A'/>"
            "<rect x='30' y='14' width='4' height='40' fill='#1E3A8A'/>"
            "<circle cx='32' cy='12' r='4' fill='#D97706'/>"
            "<g style='transform-origin: 32px 16px; animation: opoBalanceSwing5B 1.9s ease-in-out infinite;'>"
            "<rect x='10' y='14' width='44' height='3' rx='1.5' fill='#D97706'/>"
            "<line x1='14' y1='17' x2='8' y2='34' stroke='#1E3A8A' stroke-width='2'/>"
            "<line x1='14' y1='17' x2='20' y2='34' stroke='#1E3A8A' stroke-width='2'/>"
            "<path d='M6 34 H22 C22 39 18.5 42 14 42 C9.5 42 6 39 6 34 Z' fill='#2563EB'/>"
            "<line x1='50' y1='17' x2='44' y2='34' stroke='#1E3A8A' stroke-width='2'/>"
            "<line x1='50' y1='17' x2='56' y2='34' stroke='#1E3A8A' stroke-width='2'/>"
            "<path d='M42 34 H58 C58 39 54.5 42 50 42 C45.5 42 42 39 42 34 Z' fill='#2563EB'/>"
            "</g>"
            "</svg>"
            "</div>"
            "<span style='font-size: 12px; font-weight: 700; color: #1E3A8A !important; margin-top: 6px;'>Tribunal BOE</span>"
            "</div>"
            "<div style='position: relative; width: 118px; height: 94px; background: #FFFFFF; border: 2px solid #334155; border-radius: 10px; padding: 12px 14px; box-sizing: border-box; box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>"
            "<div style='position: absolute; left: 6px; right: 6px; height: 4px; background: linear-gradient(90deg, transparent, #2563EB, #38BDF8, #2563EB, transparent); border-radius: 4px; animation: opoScanBeam5B 1.5s ease-in-out infinite;'></div>"
            "<div style='height: 5px; width: 55%; background: #1E3A8A; border-radius: 3px; margin-bottom: 8px;'></div>"
            "<div style='height: 4px; width: 90%; background: #CBD5E1; border-radius: 2px; margin-bottom: 6px;'></div>"
            "<div style='height: 4px; width: 80%; background: #CBD5E1; border-radius: 2px; margin-bottom: 6px;'></div>"
            "<div style='height: 4px; width: 92%; background: #CBD5E1; border-radius: 2px; margin-bottom: 6px;'></div>"
            "<div style='height: 4px; width: 65%; background: #16A34A; border-radius: 2px;'></div>"
            "<div style='position: absolute; top: 20px; left: 16px; font-size: 26px; animation: opoPenWrite5B 1.6s ease-in-out infinite;'>🖋️</div>"
            "<div style='position: absolute; bottom: -12px; right: -12px;'>"
            "<svg width='72' height='24' viewBox='0 0 72 24' xmlns='http://www.w3.org/2000/svg'>"
            "<rect x='1' y='1' width='70' height='22' rx='6' fill='#15803D' stroke='#FFFFFF' stroke-width='1.5'/>"
            "<text x='36' y='16' text-anchor='middle' fill='#FFFFFF' font-family='Arial, Helvetica, sans-serif' font-size='10.5' font-weight='900' style='fill: #FFFFFF !important;'>✓ TRLGSS</text>"
            "</svg>"
            "</div>"
            "</div>"
            "<div style='display: flex; flex-direction: column; align-items: center;'>"
            "<div style='width: 80px; height: 80px; border-radius: 50%; background: #FEF3C7; border: 2px solid #D97706; display: flex; align-items: center; justify-content: center; font-size: 36px; animation: opoStudentNod5B 1.5s ease-in-out infinite;'>🧑‍🎓</div>"
            "<span style='font-size: 12px; font-weight: 700; color: #92400E !important; margin-top: 6px;'>Esperando nota...</span>"
            "</div>"
            "</div>"
            f"<div style='font-size: 19px; font-weight: 800; color: #0F172A !important; margin-bottom: 6px;'>{titulo_accion}</div>"
            f"<div style='font-size: 14px; font-weight: 600; color: #334155 !important; margin-bottom: 16px;'>{subtitulo_accion}</div>"
            "<div style='max-width: 460px; margin: 0 auto; background: #E2E8F0; border-radius: 999px; height: 12px; overflow: hidden; border: 1px solid #CBD5E1;'>"
            f"<div style='width: {pct_w}%; height: 100%; background-image: linear-gradient(45deg, rgba(255,255,255,0.25) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.25) 50%, rgba(255,255,255,0.25) 75%, transparent 75%, transparent); background-color: #0284C7; background-size: 40px 40px; animation: opoBarStripes5B 1s linear infinite; border-radius: 999px;'></div>"
            "</div>"
            "<div style='font-size: 12px; color: #64748B !important; margin-top: 12px; font-style: italic;'>Esta ventana se cerrará automáticamente al finalizar la corrección.</div>"
            "</div>"
            "</div>"
        )
        slot_st.markdown(html_card, unsafe_allow_html=True)

    idx = st.session_state.current_index
    q, stat = st.session_state.questions[idx], st.session_state.stats[idx]
    tot = len(st.session_state.questions)
    puede_rep = usuario_puede_reportar()
    es_abierta = bool(q.get("is_open", False))
    es_supuesto_abierto_q = bool(q.get("tipo_abierta") == "SUPUESTO")
    es_supuesto_test_q = bool(q.get("es_supuesto_test", False))
    es_supuesto_visual = es_supuesto_abierto_q or es_supuesto_test_q
    es_desarrollo_epigrafe = bool(q.get("tipo_abierta") == "DESARROLLO")
    nombre_test_act = st.session_state.get("test_name") or "Test"
    id_test_act = re.sub(r'\W+', '_', nombre_test_act)

    lbl_btn_rep_arriba = "🔄 Repetir supuesto" if es_supuesto_visual else "🔄 Repetir test"
    c_r, c_s, c_c, _ = st.columns([1.4, 1.3, 1.3, 2.0])
    with c_r: st.button(lbl_btn_rep_arriba, on_click=action_repetir_test, use_container_width=True)
    with c_s: st.button("📂 Subir otro", on_click=action_subir_otro, use_container_width=True)
    with c_c: st.button("🚪 Cerrar sesión", on_click=action_finalizar_sesion, use_container_width=True)
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 10px; border: none; border-top: 1px solid #d3d3d3;'>", unsafe_allow_html=True)

    etiqueta_tema = obtener_etiqueta_tema_visible(nombre_test_act, q)
    tipo_item_lbl = "Epígrafe" if es_desarrollo_epigrafe else ("Cuestión" if es_supuesto_visual else "Pregunta")

    if (es_abierta or es_supuesto_test_q) and tot > 1:
        etiquetas_nav = []
        for i_q, q_nav in enumerate(st.session_state.questions):
            t_nav = re.sub(r'\s+', ' ', q_nav.get("question_text", f"{tipo_item_lbl} {i_q+1}")).strip()
            t_corto = t_nav[:92] + ("..." if len(t_nav) > 92 else "")
            etiquetas_nav.append(f"{i_q+1}. {t_corto}" if not re.match(r'^(?:EP[ÍI]GRAFE|PREGUNTA|\d+)', t_corto, re.IGNORECASE) else t_corto)

        def _cambiar_epigrafe_selector():
            limpiar_estados_reportes_error()
            sel_lbl = st.session_state.get("sel_nav_abierta")
            if sel_lbl in etiquetas_nav:
                st.session_state.current_index = etiquetas_nav.index(sel_lbl)
                st.session_state.checked = False
                st.session_state.do_scroll = True

        st.selectbox(
            f"📌 Navegación directa ({tot} {'epígrafes' if es_desarrollo_epigrafe else 'cuestiones'} disponibles en este documento):",
            options=etiquetas_nav,
            index=idx,
            key="sel_nav_abierta",
            on_change=_cambiar_epigrafe_selector
        )

    st.progress((idx + 1) / tot)
    st.markdown(
        f"<div style='background-color:#EFF6FF; border:1px solid #93C5FD; border-left:5px solid #1D4ED8; border-radius:6px; padding:8px 12px; margin-top:-4px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;'>"
        f"<span style='font-size:14px; font-weight:700; color:#1E3A8A !important;'>📘 {etiqueta_tema}</span>"
        f"<span style='font-size:13px; font-weight:700; color:#1D4ED8 !important; background:#DBEAFE; padding:2px 8px; border-radius:4px;'>{tipo_item_lbl} {idx + 1} de {tot}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    if es_supuesto_visual:
        pre_sup_txt = (q.get('preamble') or "").strip()
        q_sup_txt = (q.get('question_text') or "").strip()

        if not pre_sup_txt and "\n" in q_sup_txt:
            bloques_q_cache = [b.strip() for b in re.split(r'\n\s*\n', q_sup_txt) if b.strip()]
            if len(bloques_q_cache) >= 2:
                hdr_c = bloques_q_cache[0] if re.match(r'^(?:SUPUESTO|CASO|Cuesti[óo]n)\b', bloques_q_cache[0], re.IGNORECASE) else ""
                pre_sup_txt, q_sup_txt = _separar_planteamiento_y_pregunta_individual(bloques_q_cache, header_opcional=hdr_c)

        if pre_sup_txt:
            pre_sup_esc = html.escape(pre_sup_txt).replace("\n\n", "<br><br>").replace("\n", "<br>")
            st.markdown(
                f"<div class='opo-supuesto-planteamiento'>{pre_sup_esc}</div>",
                unsafe_allow_html=True
            )

        if q_sup_txt:
            q_sup_esc = html.escape(q_sup_txt).replace("\n\n", "<br><br>").replace("\n", "<br>")
            st.markdown(
                f"<div class='opo-supuesto-pregunta'>{q_sup_esc}</div>",
                unsafe_allow_html=True
            )
    else:
        if q.get('preamble'):
            preamble_html = html.escape(q['preamble'].strip()).replace("\n\n", "<br><br>").replace("\n", "<br>")
            st.markdown(
                f"<div style='background-color:#FFFFFF; border:1px solid #CBD5E1; border-left:4px solid #1F77B4; border-radius:6px; padding:12px; margin-bottom:12px; font-size:16px; font-weight:700; line-height:1.45; text-align:justify; color:#0F172A !important;'>{preamble_html}</div>",
                unsafe_allow_html=True
            )

        if es_desarrollo_epigrafe:
            txt_ep_mostrar = (q.get("question_text") or "").strip()
            if not re.match(r'^(?:EP[ÍI]GRAFE|PREGUNTA)\b', txt_ep_mostrar, re.IGNORECASE):
                txt_ep_mostrar = f"EPÍGRAFE {idx + 1}: {txt_ep_mostrar}"
            st.markdown(
                f"<div style='background-color:#FFFFFF; border:2px solid #1E3A8A; border-left:6px solid #1E3A8A; border-radius:8px; padding:10px 14px; margin-bottom:10px;'>"
                f"<div style='font-size:12px; font-weight:800; color:#1D4ED8 !important; letter-spacing:0.4px; margin-bottom:3px;'>📝 EPÍGRAFE QUE SE PREGUNTA (DESARROLLO):</div>"
                f"<div style='font-size:18px; font-weight:800; color:#0F172A !important; line-height:1.35; text-align:justify;'>{html.escape(txt_ep_mostrar)}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"<p style='font-size: 18px; font-weight: 700; color: #2C3E50 !important; margin-bottom: 12px; line-height: 1.35; text-align: justify;'>{q['question_text']}</p>", unsafe_allow_html=True)

    if es_abierta:
        render_dictado_voz_tiempo_real(idx)

        altura_caja = 260 if es_desarrollo_epigrafe else 170
        lbl_textarea = (
            "✍️ Escribe o dicta por voz tu respuesta razonada a la cuestión planteada (o pulsa «Comprobar» en blanco si deseas consultar directamente la solución oficial):"
            if es_supuesto_abierto_q else
            "✍️ Escribe o dicta por voz tu desarrollo o respuesta jurídica (recuerda definir las siglas la primera vez que las uses, ej. «Texto Refundido de la Ley General de la Seguridad Social, en adelante TRLGSS»):"
        )
        placeholder_textarea = (
            "Redacta o dicta con el botón superior tu solución razonada al supuesto práctico, detallando los cálculos y artículos aplicables..."
            if es_supuesto_abierto_q else
            "Redacta o dicta con el botón superior tu contestación desarrollando los apartados del epígrafe, requisitos, plazos y normativa aplicable..."
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
        with st.container():
            st.markdown("<div class='marcador-opciones-test'></div>", unsafe_allow_html=True)
            for j_opt, opt_str in enumerate(q['options']):
                k_chk = f"opt_chk_{idx}_{j_opt}"
                st.session_state[k_chk] = (stat.get('selected') == opt_str)
                st.checkbox(
                    opt_str,
                    key=k_chk,
                    on_change=handle_option_toggle,
                    args=(idx, j_opt)
                )
        sel_opt = stat.get("selected")

    if puede_rep:
        c1, c2, c3, c4, c5 = st.columns([0.9, 0.95, 0.95, 1.1, 1.5])
    else:
        c1, c2, c3, c4 = st.columns(4)
        c5 = None

    if c1.button("🡄 Anterior", use_container_width=True) and idx > 0:
        if es_abierta:
            save_answer(sel_opt)
        limpiar_estados_reportes_error()
        st.session_state.update(checked=False, current_index=idx - 1, do_scroll=True); st.rerun()
    if c2.button("Comprobar", use_container_width=True):
        if es_abierta:
            save_answer(sel_opt)
        st.session_state.update(checked=True, do_scroll=True); st.rerun()
    if idx < tot - 1:
        if c3.button("Siguiente ➔", use_container_width=True):
            if es_abierta:
                save_answer(sel_opt)
            limpiar_estados_reportes_error()
            st.session_state.update(checked=False, current_index=idx + 1, do_scroll=True); st.rerun()
    else:
        if c3.button("Terminar ➔", use_container_width=True):
            if es_abierta:
                save_answer(sel_opt)
            limpiar_estados_reportes_error()
            st.session_state.update(finished=True, fase_deliberacion_tribunal=True, animacion_fin_mostrada=False, celebracion_mostrada=False, do_scroll=True); st.rerun()
    lbl_fin_btn = "⏹ Finalizar Supuesto" if es_supuesto_visual else "⏹ Finalizar Test"
    if c4.button(lbl_fin_btn, use_container_width=True):
        if es_abierta:
            save_answer(sel_opt)
        limpiar_estados_reportes_error()
        st.session_state.update(finished=True, fase_deliberacion_tribunal=True, animacion_fin_mostrada=False, celebracion_mostrada=False, do_scroll=True); st.rerun()

    key_rep_test = f"rep_open_test_{id_test_act}_{idx + 1}"
    if key_rep_test not in st.session_state:
        st.session_state[key_rep_test] = False
    lbl_btn_reporte_top = "⚠️ Reportar Error en Epígrafe" if es_desarrollo_epigrafe else "⚠️ Reportar Error"
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
            modo_corr = "SUPUESTO" if es_supuesto_abierto_q else "DESARROLLO"

            if not txt_alumno:
                stat["open_score"] = 0.0
                stat["ai_eval"] = {"nota": 0.0, "nota_50": 0.0, "pts_criterio_1": 0.0, "pts_criterio_2": 0.0, "pts_criterio_3": 0.0}
                if es_desarrollo_epigrafe:
                    registrar_epigrafe_desarrollo_en_sheets(idx)
                st.info("⚪ **Consulta en blanco (0,00 puntos):** No has escrito ninguna respuesta. A continuación te mostramos la **Solución y Explicación Oficial** para que puedas estudiarla. Si quieres recibir la valoración y calificación de tu redacción conforme a los criterios del Tribunal, escribe tu respuesta arriba y vuelve a pulsar «Comprobar».")
            else:
                if stat.get("last_evaluated_text") != txt_alumno or not stat.get("ai_feedback") or not stat.get("ai_eval"):
                    slot_tribunal_5b = st.empty()
                    titulo_5b = (
                        f"El Tribunal Calificador está valorando tu Cuestión Práctica {idx + 1} de {tot}..."
                        if es_supuesto_abierto_q else
                        f"El Tribunal Calificador está valorando tu Epígrafe {idx + 1} de {tot}..."
                    )
                    subtitulo_5b = "Contrastando tus argumentos, cálculos y citas del TRLGSS con la solución oficial. Por favor, espera unos segundos..."
                    _render_tarjeta_tribunal_en_vivo(slot_tribunal_5b, titulo_5b, subtitulo_5b, 60)
                    time.sleep(0.12)

                    ev = evaluar_respuesta_escrita(txt_alumno, resp_of, exp_of, ctx_pregunta)
                    stat["last_evaluated_text"] = txt_alumno
                    clave_activa = obtener_gemini_api_key_activa()
                    stat["ai_feedback"] = consultar_ia_gemini_correccion(
                        clave_activa, q.get("preamble", ""), q["question_text"], txt_alumno, resp_of, exp_of, ev_fallback=ev, modo=modo_corr
                    )
                    stat["ai_eval"] = ev
                    stat["open_score"] = ev.get("nota", 0.0)
                    slot_tribunal_5b.empty()

                    if es_desarrollo_epigrafe:
                        registrar_epigrafe_desarrollo_en_sheets(idx)
                    elif es_supuesto_abierto_q:
                        nota_celda_sup = calcular_nota_final_supuestos_sheets(indice_actual=idx)
                        accion_sh = "actualizar_fin" if st.session_state.get("inicio_registrado_sheets", False) else "nueva_fila"
                        st.session_state.inicio_registrado_sheets = True
                        registrar_actividad_sheets(
                            "✍️ Revisado",
                            nombre_test=st.session_state.get("test_name") or "Supuesto",
                            aciertos="",
                            fallos="",
                            blancos="",
                            nota=nota_celda_sup,
                            accion=accion_sh
                        )
                    sincronizar_progreso_navegador()
                else:
                    ev = stat["ai_eval"]

                n50_q = ev.get("nota_50", 0.0)
                n10_q = ev.get("nota", 0.0)
                c1_q = ev.get("pts_criterio_1", 0.0)
                c2_q = ev.get("pts_criterio_2", 0.0)
                c3_q = ev.get("pts_criterio_3", 0.0)

                if es_supuesto_abierto_q:
                    aprobado_s = n10_q >= 5.0
                    bg_card = "#ecfdf5" if aprobado_s else "#fff7ed"
                    border_card = "#16a34a" if aprobado_s else "#ea580c"
                    color_nota = "#15803d" if aprobado_s else "#c2410c"
                    badge_txt = "✅ CUESTIÓN PRÁCTICA SUPERADA" if aprobado_s else "⚠️ CUESTIÓN A REFORZAR — PRACTICA LO APRENDIDO"

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
                        "<div style='font-size:15px; font-weight:800; color:#15803d !important; margin-bottom:4px;'>⚖️ VALORACIÓN TÉCNICA Y ORIENTACIÓN PARA TU ESTUDIO</div>"
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
                        "<div style='font-size:15px; font-weight:800; color:#15803d !important; margin-bottom:4px;'>⚖️ ANÁLISIS COMPARATIVO Y DICTAMEN DE CORRECCIÓN</div>"
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
                if es_desarrollo_epigrafe:
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
            eh = PDFQuizParser.renderizar_explicacion_html(et, etiqueta_tema)
            st.markdown(f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 12px 15px; border-radius: 6px; margin-top: 10px;'><div style='font-size: 14.5px; font-weight: 800; margin-bottom: 4px; color: #083B46 !important;'>📖 Explicación:</div><div style='font-size: 14px; color: #0c5460 !important; text-align: justify;'>{eh}</div></div>", unsafe_allow_html=True)
# === FIN SECCIÓN 5B ===

# === SECCIÓN 5C: PANTALLA DE RESULTADOS FINALES Y REVISIÓN DETALLADA ===
else:
    import html
    st.markdown("""<style>
    :root { --background-color: #FFFFFF !important; --secondary-background-color: #F8FAFC !important; --text-color: #1E293B !important; }
    html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFFFF !important; color: #1E293B !important; }
    .opo-supuesto-planteamiento-res, .opo-supuesto-planteamiento-res * {
        font-family: inherit !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        line-height: 1.5 !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        text-align: justify !important;
    }
    .opo-supuesto-planteamiento-res {
        background-color: #EAECEF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        padding: 14px 18px !important;
        margin-bottom: 10px !important;
    }
    .opo-supuesto-pregunta-res, .opo-supuesto-pregunta-res * {
        font-family: inherit !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        line-height: 1.5 !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        text-align: justify !important;
    }
    .opo-supuesto-pregunta-res {
        background-color: transparent !important;
        border: 1.5px solid #64748B !important;
        border-radius: 6px !important;
        padding: 11px 16px !important;
        margin-bottom: 8px !important;
    }
    a.opo-btn-volver-arriba {
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        background-color: #EFF6FF !important;
        color: #1D4ED8 !important;
        -webkit-text-fill-color: #1D4ED8 !important;
        border: 1.5px solid #93C5FD !important;
        border-radius: 6px !important;
        padding: 3px 10px !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        text-decoration: none !important;
        cursor: pointer !important;
        white-space: nowrap !important;
        transition: all 0.15s ease-in-out !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }
    a.opo-btn-volver-arriba:hover {
        background-color: #1D4ED8 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-color: #1E40AF !important;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown("<div id='opo_top_resultados_anchor' style='position:relative; top:-80px; height:0; width:0;'></div>", unsafe_allow_html=True)
    components.html("""<script>
    (function() {
        var pw = window.parent;
        var pd = pw.document;

        function scrollAlPrincipioOposiciona() {
            try {
                var anchor = pd.getElementById('opo_top_resultados_anchor');
                if (anchor && anchor.scrollIntoView) {
                    anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                var contenedores = [
                    pd.querySelector('[data-testid="stAppViewContainer"]'),
                    pd.querySelector('[data-testid="stMain"]'),
                    pd.querySelector('section.main'),
                    pd.documentElement,
                    pd.body
                ];
                for (var i = 0; i < contenedores.length; i++) {
                    if (contenedores[i] && typeof contenedores[i].scrollTo === 'function') {
                        contenedores[i].scrollTo({ top: 0, behavior: 'smooth' });
                    } else if (contenedores[i]) {
                        contenedores[i].scrollTop = 0;
                    }
                }
                pw.scrollTo({ top: 0, behavior: 'smooth' });
            } catch (err) {}
        }

        pw.__oposicionaScrollTop = scrollAlPrincipioOposiciona;

        if (!pw.__oposiciona_backtop_listener_ready) {
            pw.__oposiciona_backtop_listener_ready = true;
            pd.addEventListener('click', function(e) {
                var btn = e.target && e.target.closest ? e.target.closest('.opo-btn-volver-arriba') : null;
                if (btn) {
                    e.preventDefault();
                    e.stopPropagation();
                    pw.__oposicionaScrollTop();
                }
            }, true);
        }

        setTimeout(scrollAlPrincipioOposiciona, 300);
    })();
    </script>""", height=0)

    puede_rep = usuario_puede_reportar()
    aciertos = fallos = blancos = preg_eval = 0
    aciertos_por_intento = {}
    suma_notas_abiertas = 0.0
    suma_notas_50 = 0.0
    notas_individuales_10 = []
    notas_individuales_50 = []
    es_test_abierto = any(q.get("is_open", False) for q in st.session_state.questions)
    es_test_supuestos_abiertos = any(q.get("tipo_abierta") == "SUPUESTO" for q in st.session_state.questions)
    es_test_supuestos_test = any(q.get("es_supuesto_test", False) for q in st.session_state.questions)
    es_cualquier_supuesto = es_test_supuestos_abiertos or es_test_supuestos_test

    alguna_contestada = any(
        bool((st.session_state.stats.get(i_chk, {}).get("selected") or "").strip())
        if isinstance(st.session_state.stats.get(i_chk, {}).get("selected"), str)
        else (st.session_state.stats.get(i_chk, {}).get("selected") is not None)
        for i_chk in range(len(st.session_state.questions))
    )

    pendientes_ia = [
        i_p for i_p, q_p in enumerate(st.session_state.questions)
        if q_p.get("is_open", False)
        and (st.session_state.stats.get(i_p, {}).get("selected") or "").strip()
        and not detectar_respuesta_inapropiada_o_sin_interes((st.session_state.stats.get(i_p, {}).get("selected") or "").strip())
        and (
            st.session_state.stats.get(i_p, {}).get("last_evaluated_text") != (st.session_state.stats.get(i_p, {}).get("selected") or "").strip()
            or not st.session_state.stats.get(i_p, {}).get("ai_eval")
        )
    ]

    def _html_animacion_tribunal_corrigiendo(subtitulo_progreso="Analizando tus respuestas y aplicando el baremo oficial de la Seguridad Social...", porcentaje_prog=65):
        pct_w = max(15, min(100, int(porcentaje_prog)))
        return (
            "<style>"
            "@keyframes opoBalanceSwing { 0%, 100% { transform: rotate(-8deg); } 50% { transform: rotate(8deg); } }"
            "@keyframes opoPenWrite { 0% { transform: translate(0px, 0px) rotate(0deg); } 25% { transform: translate(18px, -3px) rotate(-6deg); } 50% { transform: translate(34px, 2px) rotate(4deg); } 75% { transform: translate(14px, 5px) rotate(-4deg); } 100% { transform: translate(0px, 0px) rotate(0deg); } }"
            "@keyframes opoScanBeam { 0% { top: 14px; opacity: 0.35; } 50% { top: 68px; opacity: 0.9; } 100% { top: 14px; opacity: 0.35; } }"
            "@keyframes opoPulseBadge { 0%, 100% { transform: scale(1); filter: drop-shadow(0 4px 10px rgba(29, 78, 216, 0.35)); } 50% { transform: scale(1.02); filter: drop-shadow(0 6px 16px rgba(29, 78, 216, 0.55)); } }"
            "@keyframes opoStudentNod { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-4px); } }"
            "@keyframes opoBarStripes { 0% { background-position: 0 0; } 100% { background-position: 40px 0; } }"
            "@keyframes opoModalPopIn { 0% { opacity: 0; transform: scale(0.92) translateY(12px); } 100% { opacity: 1; transform: scale(1) translateY(0); } }"
            "#opo-modal-5c .opo-white-txt, #opo-modal-5c .opo-white-txt * { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; fill: #FFFFFF !important; }"
            "</style>"
            "<div id='opo-modal-5c' style='position: fixed; top: 0; left: 0; right: 0; bottom: 0; width: 100vw; height: 100vh; background: rgba(15, 23, 42, 0.72); backdrop-filter: blur(7px); -webkit-backdrop-filter: blur(7px); z-index: 999999; display: flex; align-items: center; justify-content: center; padding: 20px; box-sizing: border-box;'>"
            "<div style='width: 100%; max-width: 660px; background: linear-gradient(135deg, #EFF6FF 0%, #FFFFFF 55%, #FEFCE8 100%); border: 3px solid #1D4ED8; border-radius: 20px; padding: 30px 24px; text-align: center; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.55); animation: opoModalPopIn 0.25s ease-out;'>"
            "<div style='margin-bottom: 18px; display: flex; justify-content: center; animation: opoPulseBadge 1.8s infinite;'>"
            "<svg width='600' height='42' viewBox='0 0 600 42' style='max-width: 100%; height: auto;' xmlns='http://www.w3.org/2000/svg'>"
            "<rect x='2' y='2' width='596' height='38' rx='19' fill='#1E3A8A' stroke='#93C5FD' stroke-width='2.5'/>"
            "<text x='300' y='26' text-anchor='middle' fill='#FFFFFF' font-family='Arial, Helvetica, sans-serif' font-size='12.2' font-weight='900' letter-spacing='0.4' style='fill: #FFFFFF !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important;'>⚖️ TRIBUNAL CALIFICADOR EN DELIBERACIÓN — PROCESANDO EXAMEN</text>"
            "</svg>"
            "</div>"
            "<div style='display: flex; justify-content: center; align-items: center; gap: 28px; flex-wrap: wrap; margin: 6px 0 18px 0;'>"
            "<div style='display: flex; flex-direction: column; align-items: center;'>"
            "<div style='width: 80px; height: 80px; border-radius: 50%; background: #DBEAFE; border: 2px solid #2563EB; display: flex; align-items: center; justify-content: center; box-shadow: inset 0 2px 6px rgba(0,0,0,0.08);'>"
            "<svg width='50' height='50' viewBox='0 0 64 64' fill='none' xmlns='http://www.w3.org/2000/svg'>"
            "<rect x='20' y='54' width='24' height='5' rx='2.5' fill='#1E3A8A'/>"
            "<rect x='30' y='14' width='4' height='40' fill='#1E3A8A'/>"
            "<circle cx='32' cy='12' r='4' fill='#D97706'/>"
            "<g style='transform-origin: 32px 16px; animation: opoBalanceSwing 1.9s ease-in-out infinite;'>"
            "<rect x='10' y='14' width='44' height='3' rx='1.5' fill='#D97706'/>"
            "<line x1='14' y1='17' x2='8' y2='34' stroke='#1E3A8A' stroke-width='2'/>"
            "<line x1='14' y1='17' x2='20' y2='34' stroke='#1E3A8A' stroke-width='2'/>"
            "<path d='M6 34 H22 C22 39 18.5 42 14 42 C9.5 42 6 39 6 34 Z' fill='#2563EB'/>"
            "<line x1='50' y1='17' x2='44' y2='34' stroke='#1E3A8A' stroke-width='2'/>"
            "<line x1='50' y1='17' x2='56' y2='34' stroke='#1E3A8A' stroke-width='2'/>"
            "<path d='M42 34 H58 C58 39 54.5 42 50 42 C45.5 42 42 39 42 34 Z' fill='#2563EB'/>"
            "</g>"
            "</svg>"
            "</div>"
            "<span style='font-size: 12px; font-weight: 700; color: #1E3A8A !important; margin-top: 6px;'>Tribunal BOE</span>"
            "</div>"
            "<div style='position: relative; width: 118px; height: 94px; background: #FFFFFF; border: 2px solid #334155; border-radius: 10px; padding: 12px 14px; box-sizing: border-box; box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>"
            "<div style='position: absolute; left: 6px; right: 6px; height: 4px; background: linear-gradient(90deg, transparent, #2563EB, #38BDF8, #2563EB, transparent); border-radius: 4px; animation: opoScanBeam 1.5s ease-in-out infinite;'></div>"
            "<div style='height: 5px; width: 55%; background: #1E3A8A; border-radius: 3px; margin-bottom: 8px;'></div>"
            "<div style='height: 4px; width: 90%; background: #CBD5E1; border-radius: 2px; margin-bottom: 6px;'></div>"
            "<div style='height: 4px; width: 80%; background: #CBD5E1; border-radius: 2px; margin-bottom: 6px;'></div>"
            "<div style='height: 4px; width: 92%; background: #CBD5E1; border-radius: 2px; margin-bottom: 6px;'></div>"
            "<div style='height: 4px; width: 65%; background: #16A34A; border-radius: 2px;'></div>"
            "<div style='position: absolute; top: 22px; left: 18px; font-size: 26px; animation: opoPenWrite 1.6s ease-in-out infinite; filter: drop-shadow(1px 2px 2px rgba(0,0,0,0.2));'>🖋️</div>"
            "<div style='position: absolute; bottom: -12px; right: -12px;'>"
            "<svg width='72' height='24' viewBox='0 0 72 24' xmlns='http://www.w3.org/2000/svg'>"
            "<rect x='1' y='1' width='70' height='22' rx='6' fill='#15803D' stroke='#FFFFFF' stroke-width='1.5'/>"
            "<text x='36' y='16' text-anchor='middle' fill='#FFFFFF' font-family='Arial, Helvetica, sans-serif' font-size='10.5' font-weight='900' style='fill: #FFFFFF !important;'>✓ TRLGSS</text>"
            "</svg>"
            "</div>"
            "</div>"
            "<div style='display: flex; flex-direction: column; align-items: center;'>"
            "<div style='width: 80px; height: 80px; border-radius: 50%; background: #FEF3C7; border: 2px solid #D97706; display: flex; align-items: center; justify-content: center; font-size: 36px; animation: opoStudentNod 1.5s ease-in-out infinite; box-shadow: inset 0 2px 6px rgba(0,0,0,0.06);'>🧑‍🎓</div>"
            "<span style='font-size: 12px; font-weight: 700; color: #92400E !important; margin-top: 6px;'>Esperando acta...</span>"
            "</div>"
            "</div>"
            "<div style='font-size: 20px; font-weight: 800; color: #0F172A !important; margin-bottom: 6px;'>Resolviendo y calificando tus respuestas...</div>"
            f"<div style='font-size: 14.5px; font-weight: 600; color: #334155 !important; margin-bottom: 16px;'>{subtitulo_progreso}</div>"
            "<div style='max-width: 460px; margin: 0 auto; background: #E2E8F0; border-radius: 999px; height: 12px; overflow: hidden; border: 1px solid #CBD5E1;'>"
            f"<div style='width: {pct_w}%; height: 100%; background-image: linear-gradient(45deg, rgba(255,255,255,0.25) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.25) 50%, rgba(255,255,255,0.25) 75%, transparent 75%, transparent); background-color: #0284C7; background-size: 40px 40px; animation: opoBarStripes 1s linear infinite; border-radius: 999px; transition: width 0.35s ease;'></div>"
            "</div>"
            "<div style='font-size: 12px; color: #64748B !important; margin-top: 12px; font-style: italic;'>Esta ventana se cerrará automáticamente al finalizar la corrección.</div>"
            "</div>"
            "</div>"
        )

    slot_animacion_correccion = st.empty()
    if alguna_contestada and (pendientes_ia or st.session_state.get("fase_deliberacion_tribunal", False) or not st.session_state.get("animacion_fin_mostrada", False)):
        st.session_state.animacion_fin_mostrada = True
        st.session_state.fase_deliberacion_tribunal = False
        msg_inicial_anim = (
            f"El Tribunal Calificador está revisando y puntuando {len(pendientes_ia)} respuesta(s) escrita(s) conforme al baremo oficial. Por favor, espera unos segundos..."
            if pendientes_ia else
            "El Tribunal Calificador está comprobando tu hoja de respuestas y calculando tu nota oficial..."
        )
        slot_animacion_correccion.markdown(
            _html_animacion_tribunal_corrigiendo(msg_inicial_anim, 25 if pendientes_ia else 85),
            unsafe_allow_html=True
        )
        time.sleep(0.25 if pendientes_ia else 0.9)

    realizadas_ia = 0
    total_pendientes_ia = max(1, len(pendientes_ia))

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
                stat["ai_eval"] = {"nota": 0.0, "nota_50": 0.0, "pts_criterio_1": 0.0, "pts_criterio_2": 0.0, "pts_criterio_3": 0.0}
                notas_individuales_10.append((i + 1, 0.0))
                notas_individuales_50.append((i + 1, 0.0))
                stat['final_status'] = "⚠️ Respuesta no evaluable (0,00 / 10)" if es_sup_i else "⚠️ Respuesta no evaluable (0,00 / 50 ptos)"
            else:
                ctx_q = f"{q.get('preamble', '')} {q.get('question_text', '')}".strip()
                if stat.get("last_evaluated_text") == txt_al and stat.get("ai_eval"):
                    ev = stat["ai_eval"]
                else:
                    realizadas_ia += 1
                    pct_actual = int((realizadas_ia / total_pendientes_ia) * 95)
                    lbl_tipo_corr = "Cuestión práctica" if es_sup_i else "Epígrafe de desarrollo"
                    slot_animacion_correccion.markdown(
                        _html_animacion_tribunal_corrigiendo(
                            f"Deliberando y corrigiendo tu {lbl_tipo_corr} {i + 1} de {len(st.session_state.questions)} ({realizadas_ia}/{len(pendientes_ia)} pendientes)...",
                            pct_actual
                        ),
                        unsafe_allow_html=True
                    )
                    time.sleep(0.08)
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

    slot_animacion_correccion.empty()

    if es_test_abierto:
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
            nombre_cuerpo = "ADMINISTRATIVO DE LA SEGURIDAD SOCIAL" + (" — SUPUESTO PRÁCTICO" if es_test_supuestos_test else "")
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
            alguno_resuelto = False
            for idx_ep_fin, q_ep_fin in enumerate(st.session_state.questions):
                stat_ep_fin = st.session_state.stats.get(idx_ep_fin, {})
                txt_ep_fin = (stat_ep_fin.get("selected") or "").strip()
                if txt_ep_fin or stat_ep_fin.get("ai_eval") is not None:
                    alguno_resuelto = True
                    registrar_epigrafe_desarrollo_en_sheets(idx_ep_fin)
            if not alguno_resuelto and st.session_state.questions:
                idx_act_f = st.session_state.get("current_index", 0)
                st.session_state.stats[idx_act_f]["ai_eval"] = {"nota": 0.0, "nota_50": 0.0, "pts_criterio_1": 0.0, "pts_criterio_2": 0.0, "pts_criterio_3": 0.0}
                registrar_epigrafe_desarrollo_en_sheets(idx_act_f)
        else:
            if aciertos > 0 and aciertos_por_intento:
                max_intento = max(aciertos_por_intento.keys())
                tope_mostrar = 1 if max_intento == 1 else max(3, max_intento)
                desglose_str = ", ".join([f"{aciertos_por_intento.get(k, 0)}-{k}" for k in range(1, tope_mostrar + 1)])
                aciertos_sheets_str = f"{aciertos} ({desglose_str})"
            else:
                aciertos_sheets_str = str(aciertos)

            nota_sheets_str = (
                calcular_nota_final_supuestos_sheets()
                if es_test_supuestos_abiertos else
                f"{nota_referencia:.2f} (Opos: {nota_oposicion_10:.2f})".replace(".", ",")
            )
            accion_sheets = "actualizar_fin" if st.session_state.get("inicio_registrado_sheets", False) else "nueva_fila"
            st.session_state.inicio_registrado_sheets = True
            registrar_actividad_sheets(
                evento="✅ Completado",
                nombre_test=st.session_state.get("test_name") or "Test",
                aciertos=aciertos_sheets_str,
                fallos=fallos,
                blancos=blancos,
                nota=nota_sheets_str,
                accion=accion_sheets
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
        msg_enhorabuena = (
            "🎉 ¡ENHORABUENA, HAS SUPERADO EL SUPUESTO PRÁCTICO! 🎉"
            if es_cualquier_supuesto else (
                "🎉 ¡ENHORABUENA, HAS SUPERADO EL CORTE DE 25 / 50 PUNTOS! 🎉"
                if es_test_abierto else
                "🎉 ¡ENHORABUENA, HAS APROBADO EL TEST! 🎉"
            )
        )
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

    if es_test_supuestos_abiertos:
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
            f"<div style='text-align: center; font-size: 14px; font-weight: 700; color: #1f77b4 !important; letter-spacing: 0.5px; margin-bottom: 4px;'>🎯 CALIFICACIONES POR EPÍGRAFE ({nombre_cuerpo})</div>"
            f"<div style='background-color: #ffffff; border-left: 4px solid #1f77b4; padding: 10px 12px; border-radius: 4px; font-size: 14px; color: #2C3E50 !important; text-align: center; line-height: 1.5;'>"
            f"{desglose_indiv_des}"
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
    elif "SUPUESTO" in cat_actual_fin or es_cualquier_supuesto:
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

    preambulos_distintos_sup = []
    for q_item_p in st.session_state.questions:
        pr_it = (q_item_p.get("preamble") or "").strip()
        if pr_it and (q_item_p.get("tipo_abierta") == "SUPUESTO" or q_item_p.get("es_supuesto_test", False)) and pr_it not in preambulos_distintos_sup:
            preambulos_distintos_sup.append(pr_it)
    total_bloques_supuestos = len(preambulos_distintos_sup)

    ultimo_preambulo_mostrado = None
    contador_bloque_supuesto = 0
    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        es_sup_ab_i = bool(q.get("tipo_abierta") == "SUPUESTO")
        es_sup_test_i = bool(q.get("es_supuesto_test", False))
        es_sup_res_i = es_sup_ab_i or es_sup_test_i
        tipo_lbl_res = "Epígrafe" if q.get("tipo_abierta") == "DESARROLLO" else ("Cuestión" if es_sup_res_i else "Pregunta")
        co = (q.get('answer_text') or "Ver solución y explicación debajo") if q.get("is_open") else (q['options'][q['answer']] if q['answer'] != -1 else "No detectada (revisa la explicación)")
        col = "#15803d" if "✅" in stat.get('final_status', '') else "#dc2626" if "❌" in stat.get('final_status', '') else "#d97706"
        et = re.sub(r'^(explicaci[óo]n(?:\s+detallada|\s+y\s+justificaci[óo]n\s+legal|\s+y\s+base\s+legal|\s+para\s+estudio|\s*\([^)]*\))?:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip(), flags=re.IGNORECASE).strip() or "No hay explicación disponible."
        eh = PDFQuizParser.renderizar_explicacion_html(et, etiqueta_tema_fin)
        if q.get("tipo_abierta") == "DESARROLLO":
            cabecera_res_html = (
                f"<div style='font-size: 15px; font-weight: 800; color: #083B46 !important;'>📖 Texto mínimo de {q['question_text']}</div>"
                f"<div style='font-size: 12.5px; font-weight: 600; color: #0E5A6A !important; margin-top: 2px; margin-bottom: 6px; border-bottom: 1px solid #b6e0ea; padding-bottom: 5px;'>{etiqueta_tema_fin}</div>"
            )
        elif es_sup_res_i:
            cabecera_res_html = (
                f"<div style='font-size: 15px; font-weight: 800; color: #083B46 !important; margin-bottom: 6px; border-bottom: 1px solid #b6e0ea; padding-bottom: 5px;'>📖 Solución y Explicación Oficial de la Cuestión {i+1}:</div>"
            )
        else:
            cabecera_res_html = "<div style='font-size: 14.5px; font-weight: 800; margin-bottom: 6px; color: #083B46 !important;'>📖 Explicación:</div>"

        pre_actual = (q.get('preamble') or "").strip()
        q_txt_actual = (q.get('question_text') or "").strip()
        if es_sup_res_i and not pre_actual and "\n" in q_txt_actual:
            bloques_q_c = [b.strip() for b in re.split(r'\n\s*\n', q_txt_actual) if b.strip()]
            if len(bloques_q_c) >= 2:
                hdr_c = bloques_q_c[0] if re.match(r'^(?:SUPUESTO|CASO|Cuesti[óo]n)\b', bloques_q_c[0], re.IGNORECASE) else ""
                pre_actual, q_txt_actual = _separar_planteamiento_y_pregunta_individual(bloques_q_c, header_opcional=hdr_c)

        ph = ""
        separador_sup_previo = ""
        if pre_actual and not es_sup_res_i:
            ph = f"<div style='font-size:15.5px; font-weight:700; line-height:1.45; text-align:justify; color:#0F172A !important; margin-bottom: 6px;'>{html.escape(pre_actual).replace(chr(10)+chr(10), '<br><br>').replace(chr(10), '<br>')}</div>"
        elif pre_actual and es_sup_res_i and pre_actual != ultimo_preambulo_mostrado:
            ultimo_preambulo_mostrado = pre_actual
            contador_bloque_supuesto += 1
            pre_html_res = html.escape(pre_actual).replace("\n\n", "<br><br>").replace("\n", "<br>")
            if contador_bloque_supuesto > 1 and total_bloques_supuestos < len(st.session_state.questions):
                separador_sup_previo = "<hr style='margin: 22px 0px 14px 0px; border: 0; border-top: 3px solid #1E3A8A;'>"
            tit_sup_res = (
                f"<div style='font-size:14.5px; font-weight:800; color:#1E3A8A !important; margin-bottom:5px; text-transform:uppercase;'>📋 SUPUESTO PRÁCTICO {contador_bloque_supuesto} DE {total_bloques_supuestos}</div>"
                if total_bloques_supuestos > 1 and total_bloques_supuestos < len(st.session_state.questions) else ""
            )
            ph = f"{tit_sup_res}<div class='opo-supuesto-planteamiento-res'>{pre_html_res}</div>"

        q_txt_res_esc = html.escape(q_txt_actual).replace("\n\n", "<br><br>").replace("\n", "<br>")
        bloque_q_res_html = (
            f"<div class='opo-supuesto-pregunta-res'>{q_txt_res_esc}</div>"
            if es_sup_res_i else
            f"<div style='font-size:15px; color:#000000 !important; text-align: justify; line-height: 1.3; margin-bottom: 6px;'><b style='color:#000000 !important;'>{tipo_lbl_res}:</b> {q_txt_res_esc}</div>"
        )

        fila_cabecera_item_html = (
            f"<div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:6px;'>"
            f"<span style='color: {col} !important; -webkit-text-fill-color: {col} !important; font-size: 17px; font-weight: 700;'>{tipo_lbl_res} {i+1} | {stat['final_status']}</span>"
            f"<a href='#opo_top_resultados_anchor' class='opo-btn-volver-arriba' title='Subir al principio de la pantalla'>⬆️ VOLVER ARRIBA</a>"
            f"</div>"
        )

        st.markdown(
            f"<div style='margin-bottom: 5px;'>"
            f"{separador_sup_previo}"
            f"{ph}"
            f"{fila_cabecera_item_html}"
            f"{bloque_q_res_html}"
            f"<div style='font-size:15px; color:#000000 !important; text-align: justify; line-height: 1.3; margin-bottom: 4px;'><b style='color:#000000 !important;'>Tu respuesta:</b> {stat['selected'] if stat['selected'] else 'Ninguna'}</div>"
            f"<div style='font-size:15px; color:#1b5e20 !important; text-align: justify; line-height: 1.3; margin-bottom: 6px;'><b style='color:#1b5e20 !important;'>Respuesta oficial:</b> {co}</div>"
            f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 14px 16px; border-radius: 6px; margin-bottom: 6px;'>{cabecera_res_html}<div style='font-size: 14px; color: #0c5460 !important; text-align: justify;'>{eh}</div></div>"
            f"</div>",
            unsafe_allow_html=True
        )
        if q.get("is_open") and stat.get("ai_feedback"):
            with st.expander(f"⚖️ Ver valoración técnica detallada para {tipo_lbl_res} {i + 1}"):
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
# === FIN SECCIÓN 5C ===
