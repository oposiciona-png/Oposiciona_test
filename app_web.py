import streamlit as st
import streamlit.components.v1 as components  
import fitz  # PyMuPDF
import re
import random
import requests
import os
from datetime import datetime

# --- AUTO-CONFIGURADOR DE RESPALDO ---
try:
    os.makedirs(".streamlit", exist_ok=True)
    if not os.path.exists(".streamlit/config.toml"):
        with open(".streamlit/config.toml", "w") as f:
            f.write('[client]\ntoolbarMode = "minimal"\n')
except:
    pass

# --- CONFIGURACIÓN VISUAL DE LA PÁGINA ---
icono_ruta = "ICONO OPOSICIONA.png"
if os.path.exists(icono_ruta):
    st.set_page_config(page_title="Plataforma de Tests Oposiciona", page_icon=icono_ruta, layout="centered")
else:
    st.set_page_config(page_title="Plataforma de Tests Oposiciona", page_icon="📚", layout="centered")


# INYECCIÓN DE CSS (Bomba nuclear contra iconos y blindaje de letras)
st.markdown("""
<style>
/* --- ANIQUILAR RASTROS INTERNOS DE STREAMLIT --- */
#MainMenu, footer, header {visibility: hidden !important; display: none !important;}
[data-testid="stHeader"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}

/* --- ANIQUILAR BOTONES FLOTANTES DE STREAMLIT CLOUD --- */
.stDeployButton {display: none !important;}
[data-testid="stAppDeployButton"] {display: none !important;}
[class*="viewerBadge"] {display: none !important; opacity: 0 !important; pointer-events: none !important;}
[class*="styles_viewerBadge"] {display: none !important;}
[data-testid*="manage-app"] {display: none !important;}

div[style*="position: fixed"][style*="bottom"][style*="right"],
div[style*="position: absolute"][style*="bottom"][style*="right"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    z-index: -9999 !important;
}

/* --- TEXTO DE LAS OPCIONES DE RESPUESTA BLINDADO CONTRA EL MODO OSCURO --- */
div[role="radiogroup"] label {margin-bottom: 12px !important;}
div[role="radiogroup"] label, 
div[role="radiogroup"] label p, 
div[role="radiogroup"] label div,
div[role="radiogroup"] label span {
    font-size: 17px !important; 
    line-height: 1.5 !important;
    color: #000000 !important; /* NEGRO PURO siempre */
    white-space: normal !important; 
}

/* --- CÍRCULOS DE OPCIONES NÍTIDOS Y NEGROS --- */
div[data-baseweb="radio"] > div:first-child {
    border-color: #000000 !important; 
    border-width: 2px !important;
}
div[data-baseweb="radio"][data-checked="true"] > div:first-child > div {
    background-color: #000000 !important; 
}

/* Espaciado del contenedor principal */
.block-container {
    padding-top: 1.5rem !important;
    max-width: 750px !important; 
}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 🔒 SISTEMA DE SEGURIDAD Y ACCESO POR ROLES
# ==============================================================================

USUARIOS_AUTORIZADOS = {
    "ACCESO TOTAL": [
        "ponentes@oposiciona.es",
        "gonzalogonzaleztejedor@gmail.com",
        "ignacio.garcia.heras@gmai.com",
        "alvarezpugamartin@gmail.com",
        "claratoledo06@gmail.com",
        "blancazortega@gmail.com",
        "mijurista@gmail.com",
        "silviacabello81@gmail.com",
        "isabelmgutierrogil@gmail.com",
        "carmenvl28@gmail.com",
        "leticiagenerelosolana@gmail.com",
        "sion.nuba@gmail.com",
        "alumno_total2@gmail.com"
    ],
    "ADMTVOS": [
        "alumno1@gmail.com",
        "andreitalopeamor1@gmail.com",
        "elenavegasanchez73@gmail.com",
        "josemurillomoreno.mail@gmail.com",
        "raulff1997.rfg@gmail.com",
        "sandradcastanares@gmail.com",
        "joycewayland@gmail.com",
        "celia.pks@gmail.com",
        "cynthiaflafla14@gmail.com",
        "fragosotorbellinocarmen@gmail.com",
        "pherrerojulian@gmail.com",
        "rsilveiraescudero@gmail.com",
        "delfijv19@gmail.com",
        "marielipedreira@hotmail.com",
        "raquelkmacho@gmail.com",
        "juan_admtvo@hotmail.com"
    ],
    "GESTION": [
        "alumno2@gmail.com",
        "mariafolgoso@gmail.com",
        "vsaurod@gmail.com",
        "mariaquirosmonge5@gmail.com",
        "vanessagomeztdla@gmail.com",
        "zoemorcor@gmail.com",
        "julianayem@gmail.com",
        "yasminkhalili@gmail.com",
        "monetcacerescc@gmail.com",
        "maariiamaji@gmail.com",
        "micastroespejo@gmail.com",
        "aisacarrerapexe@gmail.com",
        "csanchezssmm@gmail.com",
        "maria.concal@gmail.com",
        "manuelsan240902@gmail.com",
        "maria_gestion@gmail.com"
    ]
}

PASSWORD_ACCESO = "plaza2026" 

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None
if 'modo_avance' not in st.session_state:
    st.session_state.modo_avance = "**Modo reflexivo** (puedes comprobar la pregunta y el paso a la siguiente es manual pulsando siguiente)"

col1, col2, col3 = st.columns([1, 0.8, 1]) 
with col2:
    try:
        st.image("oposiciona (320 x 132 px).png", use_container_width=True)
    except:
        pass
    st.markdown("<p style='text-align: center; font-size: 12px; margin-top: -15px;'><a href='https://oposiciona.es/' style='text-decoration: none; color: #1f77b4;'>🌐 oposiciona.es</a></p>", unsafe_allow_html=True)
st.markdown("---")

if not st.session_state.autenticado:
    c_img1, c_img2, c_img3 = st.columns([1, 0.25, 1])
    with c_img2:
        try:
            st.image("test-utiles-768x768.png", use_container_width=True)
        except:
            pass
            
    st.markdown("<h3 style='text-align: center; color: #2C3E50; margin-top: 5px;'>🔒 Acceso Restringido</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px;'>Plataforma exclusiva de <b>Oposiciona</b>. Introduce tus credenciales para acceder.</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    email_input = st.text_input("Correo electrónico asociado a tu cuenta")
    password_input = st.text_input("Contraseña de acceso", type="password")
    
    if st.button("Entrar a la plataforma", use_container_width=True, type="primary"):
        correo_limpio = email_input.lower().strip()
        
        rol_usuario = None
        for rol, lista_correos in USUARIOS_AUTORIZADOS.items():
            if correo_limpio in lista_correos:
                rol_usuario = rol
                break
                
        if rol_usuario and password_input == PASSWORD_ACCESO:
            st.session_state.autenticado = True
            st.session_state.rol = rol_usuario
            st.rerun()
        else:
            st.error("❌ Correo o contraseña incorrectos, o no tienes autorización activa.")
    
    st.stop()


# ==============================================================================
# 🧠 MOTOR MAESTRO DE EXTRACCIÓN (CON LOOKAHEAD COMPLETO)
# ==============================================================================

class PDFQuizParser:
    @staticmethod
    def parse(pdf_bytes):
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        questions = []
        lines = []
        stop_reading = False 
        
        for page in doc:
            if stop_reading: break
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if stop_reading: break
                if b.get("type", 0) == 0:  
                    for l in b["lines"]:
                        if stop_reading: break
                        line_text = ""
                        is_bold = False
                        for s in l["spans"]:
                            text = s["text"].strip()
                            if not text: continue
                            line_text += text + " "
                            if "bold" in s["font"].lower() or (s["flags"] & 2 != 0):
                                is_bold = True
                        
                        line_text = line_text.strip()
                        
                        # --- CIRUGÍA DE CABECERAS FUSIONADAS CON PÁRRAFOS ---
                        if line_text:
                            prefixes_to_strip = [
                                r'^OPOSICIONA\s*',
                                r'^GESTI[OÓ]N DE LA SEGURIDAD SOCIAL\s*',
                                r'^ADMINISTRATIVO DE LA SEGURIDAD SOCIAL\s*',
                                r'^(?:GENERAL\s+|ESPEC[IÍ]FICO\s+|EXAMEN\s+|TEST\s+|RESPUESTAS\s+)?TEMAS?\s+\d+[a-zA-Z]?\s*[\-–]\s*[A-ZÁÉÍÓÚÑ\s]+\b\.?\s*'
                            ]
                            for pat in prefixes_to_strip:
                                m = re.match(pat, line_text, flags=re.IGNORECASE)
                                if m and m.group(0).isupper():
                                    line_text = line_text[m.end():].strip()
                        
                        if not line_text:
                            continue
                            
                        if line_text:
                            tl = line_text.lower()
                            
                            # Normalización exhaustiva
                            tl_norm = tl.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ä", "a")
                            tl_norm = tl_norm.replace("τ", "t").replace("ε", "e").replace("μ", "m").replace("α", "a") 
                            tl_clean = re.sub(r'[^a-z0-9\s]', '', tl_norm).strip()
                            tl_clean_spaces = re.sub(r'\s+', ' ', tl_clean) 
                            
                            # CORTAFUEGOS
                            is_stop_phrase = (
                                tl_clean_spaces.startswith("supuesto practico") or 
                                tl_clean_spaces.startswith("supuestos practicos") or 
                                tl_clean_spaces.startswith("pregunta de desarrollo") or 
                                tl_clean_spaces.startswith("preguntas de desarrollo") or 
                                tl_clean_spaces.startswith("plantilla de respuesta") or
                                tl_clean_spaces.startswith("plantillas de respuesta") or
                                re.match(r'^preguntas?\s+\d+$', tl_clean_spaces) or
                                re.match(r'^supuestos?\s+\d+$', tl_clean_spaces)
                            )
                            
                            is_stop_word_upper = (tl_clean_spaces in ["supuesto", "supuestos", "pregunta", "preguntas"]) and line_text.isupper()
                            
                            if is_stop_phrase or is_stop_word_upper:
                                stop_reading = True
                                break
                            
                            # FILTRO DE CABECERAS DINÁMICO
                            is_header = False
                            if line_text.isupper() and re.match(r'^(RESPUESTAS\s+|GENERAL\s+|ESPECIFICO\s+|EXAMEN\s+|TEST\s+)?TEMAS?\s+\d+', line_text):
                                is_header = True
                                
                            if not is_header and len(tl_clean_spaces) < 120:
                                header_patterns = [
                                    r'^oposiciona$',
                                    r'oposicionaes',
                                    r'^pagina\s+\d+',
                                    r'^(administrativo|gestion)\s+de\s+la\s+seguridad\s+social',
                                    r'^(administrativo|gestion)\s+202\d\s+tema\s+\d+[a-z]?',
                                    r'^tema\s+\d+[a-z]?\s+(administrativo|gestion)\s+202\d',
                                    r'^tema\s+\d+\s+cotizacion',
                                    r'^tema\s+\d+[a-z]?\s+campo\s+de\s+aplicacion\s+y\s+composicion',
                                    r'^(general|especifico|examen|test|respuestas|respuestas\s+test|test\s+profesor)\s+temas?\s+\d+',
                                    r'^examen\s+repaso',
                                    r'^normas\s+para\s+la\s+realizacion'
                                ]
                                for pat in header_patterns:
                                    if re.search(pat, tl_clean_spaces):
                                        is_header = True
                                        break
                            
                            if is_header: continue
                            lines.append({"text": line_text, "bold": is_bold})
                            
        current_q = None
        preamble = "" 
        expected_q_num = 1  
        
        # Iteramos con índice para poder mirar hacia adelante (lookahead)
        for idx, line in enumerate(lines):
            text = line["text"]
            is_bold = line["bold"]
            text_lower = text.lower()
            
            is_option = bool(re.match(r'^[a-zA-Z][\)\.]\s', text))
            is_explanation = text_lower.startswith("explicaci") or text_lower.startswith("resp:") or text_lower.startswith("respuesta:")
            
            if re.match(r'^\s*(preguntas?\s+de\s+reserva)', text_lower):
                if current_q and current_q["options"]: questions.append(current_q)
                current_q = None 
                preamble += text + "\n"
                expected_q_num = 1 
                continue

            is_new_q = False
            
            # 1. Reconocimiento de números
            m_num = (re.match(r'^\s*(\d+)[\.-]+(?!\d)', text) or 
                     re.match(r'^\s*(\d+)\s+[\.-]', text) or
                     re.match(r'^\s*(\d+)\s*¿', text))
                     
            m_rescue = False
            
            # 2. Reconocimiento de preguntas retóricas / de rescate sin número
            if not m_num and not is_option and not is_explanation:
                text_clean = text.strip()
                if (current_q and current_q["state"] in ["E", "O"]) or not current_q:
                    # Detecta frases que empiezan y terminan con interrogación pura
                    if re.match(r'^\s*(¿|C[óo]mo|Cu[áa]l|Cu[áa]ntos|Qu[ée])\b', text_clean, re.IGNORECASE) and text_clean.endswith('?'):
                        m_rescue = True

            # --- ALGORITMO LOOKAHEAD (Mirar hacia adelante) MEJORADO ---
            if m_num or m_rescue:
                is_real_q_candidate = False
                for j in range(idx + 1, min(idx + 25, len(lines))):
                    future_text = lines[j]["text"].strip()
                    # Si encontramos una opción clara cerca, es una pregunta de verdad
                    if re.match(r'^[a-eA-E][\)\.]\s', future_text):
                        is_real_q_candidate = True
                        break
                    # Si vemos otro número o pregunta de rescate antes de encontrar opciones, rompemos 
                    m_future_num = (re.match(r'^\s*(\d+)[\.-]+(?!\d)', future_text) or 
                                    re.match(r'^\s*(\d+)\s+[\.-]', future_text) or
                                    re.match(r'^\s*(\d+)\s*¿', future_text))
                    m_future_rescue = (re.match(r'^\s*(¿|C[óo]mo|Cu[áa]l|Cu[áa]ntos|Qu[ée])\b', future_text, re.IGNORECASE) and future_text.endswith('?'))
                    
                    if m_future_num or m_future_rescue:
                        break
                
                # Solo si hemos confirmado que hay opciones debajo, procedemos a crear la nueva pregunta
                if is_real_q_candidate:
                    if m_num:
                        num = int(m_num.group(1))
                        if current_q is None:
                            is_new_q = True
                            expected_q_num = num + 1
                        # Margen de seguridad tolerante
                        elif expected_q_num - 2 <= num <= expected_q_num + 15:
                            is_new_q = True
                            expected_q_num = num + 1
                    elif m_rescue:
                        is_new_q = True
                        expected_q_num += 1

            if is_new_q:
                if current_q and current_q["options"]: questions.append(current_q)
                clean_text = re.sub(r'^\s*\d+[\.-]+\s*(-*\s*)?', '', text)
                clean_text = re.sub(r'^\s*\d+\s*¿', '¿', clean_text)
                current_q = {"preamble": preamble.strip(), "question_text": clean_text, "options": [], "answer": -1, "explanation": "", "state": "Q"}
                preamble = "" 
                continue
                
            if not current_q:
                preamble += text + "\n"
                continue
                
            if is_option and current_q["state"] in ["Q", "O"]:
                current_q["options"].append(text)
                current_q["state"] = "O"
                if is_bold and current_q["answer"] == -1: current_q["answer"] = len(current_q["options"]) - 1
                continue
                
            if is_explanation:
                if current_q:
                    current_q["explanation"] += text + " "
                    current_q["state"] = "E"
                continue
                
            if current_q["state"] == "Q":
                current_q["question_text"] += " " + text
            elif current_q["state"] == "O":
                last_opt = current_q["options"][-1].strip()
                is_new_paragraph = len(current_q["options"]) >= 2 and re.search(r'[\.;]$', last_opt) and re.match(r'^[A-Z0-9¿¡"\'«]', text)
                is_legal_ref = re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|según|normativa)', text_lower)
                
                is_implicit_explanation = False
                
                if len(current_q["options"]) >= 3 and re.match(r'^[A-ZÁÉÍÓÚ¿¡"\'«]', text):
                    if re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|seg[úu]n|normativa|de conformidad|conforme|en virtud)\b', text_lower):
                        is_implicit_explanation = True
                    elif re.match(r'^(el\b|la\b|los\b|las\b|para\b|de\b|en\b|cuando\b|se\b|es\b|esta\b|este\b|al\b|por\b|si\b)', text_lower):
                        if re.search(r'[\.;]$', last_opt):
                            is_implicit_explanation = True
                        elif not re.search(r'(,| y| o| que| de| a| con| en| por| para| el| la| los| las| un| una)$', last_opt, re.IGNORECASE):
                            is_implicit_explanation = True

                if is_new_paragraph or is_legal_ref or is_implicit_explanation:
                    current_q["state"] = "E"
                    current_q["explanation"] = text
                else:
                    if is_bold and current_q["answer"] == -1: current_q["answer"] = len(current_q["options"]) - 1
                    current_q["options"][-1] += " " + text
                    
            elif current_q["state"] == "E":
                # Lógica para inyectar saltos de párrafo en las explicaciones
                last_char = current_q["explanation"].strip()[-1:] if current_q["explanation"].strip() else ""
                
                is_list_item = bool(re.match(r'^([•\-\*]|\d+[\.\)]|[a-zA-Z][\)\.])\s', text))
                is_new_sentence = (last_char in ['.', ':', ';'] and bool(re.match(r'^[A-ZÁÉÍÓÚ¿¡"\'«]', text)))
                
                if is_list_item or is_new_sentence:
                    current_q["explanation"] += "\n\n" + text
                else:
                    current_q["explanation"] += " " + text

        if current_q and current_q["options"]: questions.append(current_q)
        return questions

# ==============================================================================
# 💻 APLICACIÓN WEB INTERFAZ
# ==============================================================================

TESTS_DISPONIBLES = {
    "ADMINISTRATIVOS": {
        "ESPECIFICO": {
            "Elige un test de especifico...": None,
            "TEMA 1 ESPECIFICO": "https://drive.google.com/uc?export=download&id=1HXIJvogWzKXVg0lt5TqlnsGk3KtTR4oI",
            "TEMA 2A": "https://drive.google.com/uc?export=download&id=1Wt-_iiVjHVeII_11jCU4CF8SBZ0nYrjl",
            "TEMA 2B": "https://drive.google.com/uc?export=download&id=1OGW-V2qE21Uu6CYWb6pklaGzjbpAgssO",
            "TEMA 2C": "https://drive.google.com/uc?export=download&id=1LmGkZ6VNbLOK42XK784je_ePwZI1cUZm",
            "TEMA 2D": "https://drive.google.com/uc?export=download&id=1QelSvHbUrl6WGXEwxmcaBsO5oTAhma2d",
            "TEMA 3 AFILIACION": "https://drive.google.com/uc?export=download&id=1No5X4Yjoj2FwWw_jIGRvMuX27m7SXeIL",
            "Tema 4 COTIZACION": "https://drive.google.com/uc?export=download&id=1V1vabkEbxPi_P8nnXtEjiLfHiYEkURDF",
            "TEMA 8B IP": "https://drive.google.com/uc?export=download&id=1e_ZHpayJ6jm4mIOvQN4joteVAWIIZyPB",
            "TEMA 9 NYCM": "https://drive.google.com/uc?export=download&id=17mH-VzUYRycZcsujzG2zJ77Dpm10DfEJ",
        },
        "EXAMENES": {
            "Elige un test de examenes...": None,
            "SABADO 5 SEP 2026": "https://drive.google.com/uc?export=download&id=1XGMVM7M0kRrNGyZYa3N-npLO7pYETxVa",
        },
        "GENERAL": {
            "Elige un test de general...": None,
            "TEMA 1 a 3 CONSTITUCIONAL": "https://drive.google.com/uc?export=download&id=14z3ZzvLLVZQ0XiUKx4qmiyneMoldZIB2",
            "TEMA 4 LA JEFATURA DEL ESTADO": "https://drive.google.com/uc?export=download&id=1y-u-_wTqfIyB_fn0he0cvyKAPLjsM06A",
            "TEMA 5 y 6 PODER LEGISLATIVO Y JUDICIAL": "https://drive.google.com/uc?export=download&id=1Hog53fH7CsG1FCk6CC0X4m4tIXZ2tPYd",
            "TEMA 7 PODER EJECUTIVO": "https://drive.google.com/uc?export=download&id=1BXKLo950u1GSODuag-lds2SCbBTYF2UD",
        },
    },
    "GESTION": {
        "ESPECIFICO": {
            "Elige un test de especifico...": None,
            "TEMA 51 - CONSTITUCION EN LA SS Y TRLGSS": "https://drive.google.com/uc?export=download&id=1LlQvfrYuVXx2mJETTpfDGdhE2hyAWUZn",
            "TEMA 52 - CAMPO DE APLICACIÓN Y COMPOSICIÓN DEL SISTEMA": "https://drive.google.com/uc?export=download&id=1ZcpNzh3IIu40K8eDcQCKpmWKrhvBUE_v",
            "TEMA 53 - AFILIACION": "https://drive.google.com/uc?export=download&id=1CUhqhupF7_aiL5vjvP6aZlLjPay9xTOs",
            "TEMA 55 ACCIÓN PROTECTORA CONTENIDO Y CLASIFICACIÓN DE LAS PRESTACIONES": "https://drive.google.com/uc?export=download&id=1OmVgiP6fGsGAYZ71v-vIKahly4V06-6o",
            "TEMA 56 REQUISITOS GENERALES DE LAS PRESTACIONES": "https://drive.google.com/uc?export=download&id=1xLJwqD3zFtgGS-Q_jGa3fHFZPnNacGwz",
            "TEMA 57 INCAPACIDAD TEMPORAL": "https://drive.google.com/uc?export=download&id=1lrSFSMDbecfW_aGYId5QChIhgVyYFKC5",
            "TEMA 58 - NYCM": "https://drive.google.com/uc?export=download&id=1iw4NDqaC1gMGiMgd-VZTbtaoWyWKLE8L",
            "TEMA 59 y 60 IP": "https://drive.google.com/uc?export=download&id=16ahUMTSgXAcjTVH700BoL6eZgwQo2_7E",
            "Tema 67 COTIZACION": "https://drive.google.com/uc?export=download&id=1kErdym1yxTP-Qd0Frx-5XIwOkI3aq5aL",
            "TEMA 73 - LOS REGIMENES ESPECIALES DE LA S SOCIAL": "https://drive.google.com/uc?export=download&id=16JKTt0G8UycnAsclRtoHC1mGkgDtvHI0",
            "TEMA 74 - RETA, SETA  Y MAR": "https://drive.google.com/uc?export=download&id=1N2ezL7ohgKxcoZVPex_oGday9JHMMxl7",
            "TEMA 75 - MINERIA - SEGURO ESCOLAR FUNCIONARIOS": "https://drive.google.com/uc?export=download&id=1eHZ9Ajqujk-wtnzcsAo_e6lpkH9kfrao",
        },
        "EXAMENES": {
            "Elige un test de examenes...": None,
            "DOMINGO 6 SEP 2026": "https://drive.google.com/uc?export=download&id=1pEuW36jClxKZQjwAuSx6TpfFaxlmkcln",
        },
        "GENERAL": {
            "Elige un test de general...": None,
            "TEMA 06 -  LA EMPRESA MERCANTIL": "https://drive.google.com/uc?export=download&id=17myj2PoQaWv_wZn7OV13wESOS7gBVNSN",
            "TEMA 07 - SOCIEDAD ANONIMA": "https://drive.google.com/uc?export=download&id=1_vZNRIHwJIcoPHdGyhbg7s-UEQEGrvMK",
            "TEMA 08 - TITULOS VALORES": "https://drive.google.com/uc?export=download&id=1JjPfA7i3yP1Xuqx19IBJQrYYZMYh6MoS",
            "TEMA 09 - LAS OBLIGACIONES MERCANTILES": "https://drive.google.com/uc?export=download&id=1ZhUqRGsA8SV8k4QPzVuGz0t2yXzdElXj",
            "TEMA 10 - DERECHO MERCANTIL - CONCURSO ACREEDORES": "https://drive.google.com/uc?export=download&id=1Tcn1glkQI4DkbjnHap3SY9B2gU49tWgT",
            "TEMA 40 - IGUALDAD": "https://drive.google.com/uc?export=download&id=1tJ3MrhWg8GafmEfT7zX1hqnFNzPFmhAg",
            "TEMA 41 GOBIERNO ABIERTO Y AGENDA 2030": "https://drive.google.com/uc?export=download&id=1eCF7-MBTZ3SWJX2-agLKqQstxSXkdqJ_",
            "TEMA 42 EL DERECHO DEL TRABAJO": "https://drive.google.com/uc?export=download&id=1ARQ8PoNtyTykdcbixOxWgEr4SZ7sZV6c",
            "TEMA 43 CONVENIOS COLECTIVOS": "https://drive.google.com/uc?export=download&id=11uc4s9pZP5-vAnbUY7klhQOVR10rCpYg",
            "TEMA 44 CONTRATOS": "https://drive.google.com/uc?export=download&id=1LRLQAx8Ql3MnMEe1kksaBQIiXUvuR2VT",
            "TEMA 45 SALARIO Y JORNADA": "https://drive.google.com/uc?export=download&id=1RRl35OdPYxOVs4f2L1GZkQO4EAgZoSWm",
            "TEMA 46 MODIFICACIÓN SUSTANCIAL": "https://drive.google.com/uc?export=download&id=1LGFdvQcFjuinwdXWf6AM66QKoOL9_dn6",
            "TEMA 47 SUSPENSIÓN": "https://drive.google.com/uc?export=download&id=1-kTGpXGLGBbbdKe26Lhq9gPXxZKCc44L",
            "TEMA 48 EXTINCIÓN": "https://drive.google.com/uc?export=download&id=1Vhy345KHpLoebUVENZOLVlUzHYPWXd-g",
        },
    },
}

if 'questions' not in st.session_state:
    st.session_state.questions = []
    st.session_state.current_index = 0
    st.session_state.stats = {}
    st.session_state.finished = False
    st.session_state.checked = False

def save_answer(selected):
    idx = st.session_state.current_index
    stat = st.session_state.stats[idx]
    if selected and selected != stat['selected']:
        stat['selected'] = selected
        stat['attempts'] += 1

def handle_radio_change():
    """Función que se activa al pinchar una opción de respuesta."""
    idx = st.session_state.current_index
    selected = st.session_state.get(f"radio_{idx}")
    
    # 1. Guardar la respuesta elegida
    save_answer(selected)
    
    # 2. Si el modo es Metralleta y ha seleccionado algo, avanzar
    if "metralleta" in st.session_state.modo_avance.lower() and selected:
        if idx < len(st.session_state.questions) - 1:
            st.session_state.current_index += 1
            st.session_state.checked = False
        else:
            st.session_state.finished = True

def procesar_preguntas(raw_qs):
    for q in raw_qs:
        cleaned_options = []
        for opt in q["options"]:
            cleaned_options.append(re.sub(r'^[a-zA-Z][\)\.-]\s*', '', opt).strip())
        
        correct_opt_text = None
        if q["answer"] != -1 and q["answer"] < len(cleaned_options):
            correct_opt_text = cleaned_options[q["answer"]]
            
        random.shuffle(cleaned_options)
        if correct_opt_text:
            q["answer"] = cleaned_options.index(correct_opt_text)
        
        q["options"] = [f"{chr(97+i)}) {opt}" for i, opt in enumerate(cleaned_options)]
    
    random.shuffle(raw_qs)
    st.session_state.questions = raw_qs
    st.session_state.stats = {i: {'attempts': 0, 'selected': None} for i in range(len(raw_qs))}
    st.rerun()

def action_repetir_test():
    st.session_state.current_index = 0
    st.session_state.stats = {i: {'attempts': 0, 'selected': None} for i in range(len(st.session_state.questions))}
    st.session_state.finished = False
    st.session_state.checked = False

def action_subir_otro():
    st.session_state.questions = []
    st.session_state.current_index = 0
    st.session_state.stats = {}
    st.session_state.finished = False
    st.session_state.checked = False

def action_finalizar_sesion():
    st.session_state.clear()


if not st.session_state.questions:

    st.markdown("""
    <style>
    :root { --background-color: #FFFFFF !important; --secondary-background-color: #FFFFFF !important; }
    html, body, .stApp, .main, [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

    col_texto, col_img = st.columns([2.5, 1])
    with col_img:
        try:
            st.image("test-utiles-768x768.png", use_container_width=True)
        except:
            pass
            
    with col_texto:
        st.markdown("<h3 style='color:#2C3E50; margin-top: 10px;'>📚 Comienza a practicar</h3>", unsafe_allow_html=True)
        
        rol = st.session_state.rol
        
        st.markdown("#### 1. Especialidad")
        if rol == "ACCESO TOTAL":
            lista_especialidades = list(TESTS_DISPONIBLES.keys())
            
            idx_esp = 0
            if "saved_esp" in st.session_state and st.session_state.saved_esp in lista_especialidades:
                idx_esp = lista_especialidades.index(st.session_state.saved_esp)
                
            especialidad = st.radio("Selecciona tu especialidad:", lista_especialidades, index=idx_esp, horizontal=True, label_visibility="collapsed")
            st.session_state.saved_esp = especialidad
            
        elif rol == "ADMTVOS":
            especialidad = "ADMINISTRATIVOS"
            st.info(f"Tienes acceso directo a tu especialidad: **{especialidad}**")
        elif rol == "GESTION":
            especialidad = "GESTION"
            st.info(f"Tienes acceso directo a tu especialidad: **{especialidad}**")
        else:
            st.error("Error en los permisos de usuario.")
            st.stop()
        
        st.markdown("#### 2. Categoría")
        lista_categorias = list(TESTS_DISPONIBLES[especialidad].keys())
        
        idx_cat = 0
        if "saved_cat" in st.session_state and st.session_state.saved_cat in lista_categorias:
            idx_cat = lista_categorias.index(st.session_state.saved_cat)
            
        categoria = st.radio("Selecciona el tipo de test:", lista_categorias, index=idx_cat, horizontal=True, label_visibility="collapsed")
        st.session_state.saved_cat = categoria
        
        st.markdown("#### 3. Selección de Test")
        tests_categoria = TESTS_DISPONIBLES[especialidad][categoria]
        opcion_seleccionada = st.selectbox(f"Tests de {categoria}:", list(tests_categoria.keys()), label_visibility="collapsed")
        
        # --- SECCIÓN MODO AVANCE ---
        st.markdown("#### 4. Modo de avance")
        opciones_avance = [
            "**Modo reflexivo** (puedes comprobar la pregunta y el paso a la siguiente es manual pulsando siguiente)", 
            "**Modo metralleta** (pasa a la pregunta siguiente al pulsar una opción)"
        ]
        idx_avance = 0
        if "saved_avance" in st.session_state and st.session_state.saved_avance in opciones_avance:
            idx_avance = opciones_avance.index(st.session_state.saved_avance)
            
        modo_avance = st.radio("Modo de avance:", opciones_avance, index=idx_avance, label_visibility="collapsed")
        st.session_state.saved_avance = modo_avance
        st.session_state.modo_avance = modo_avance
    
    st.markdown("<br>", unsafe_allow_html=True)
    if opcion_seleccionada and not opcion_seleccionada.startswith("Elige"):
        if st.button(f"🚀 Cargar Test Seleccionado", type="primary", use_container_width=True):
            url_descarga = tests_categoria[opcion_seleccionada]
            with st.spinner(f"Extrayendo archivo de forma segura..."):
                try:
                    respuesta = requests.get(url_descarga)
                    if respuesta.status_code == 200:
                        raw_qs = PDFQuizParser.parse(respuesta.content)
                        if not raw_qs:
                            st.error("No se encontraron preguntas válidas en este PDF.")
                        else:
                            procesar_preguntas(raw_qs)
                    else:
                        st.error("Error de descarga. Comprueba que el archivo en Drive tiene permisos de lectura ('Cualquier persona con el enlace').")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    with st.expander("Opcional: Subir un test PDF manualmente desde tu dispositivo"):
        uploaded_file = st.file_uploader("", type="pdf")
        if uploaded_file is not None:
            st.session_state.modo_avance = modo_avance
            with st.spinner("Procesando documento local..."):
                raw_qs = PDFQuizParser.parse(uploaded_file.read())
                if not raw_qs:
                    st.error("No se encontraron preguntas válidas en este PDF.")
                else:
                    procesar_preguntas(raw_qs)

elif not st.session_state.finished:
    
    st.markdown("""
    <style>
    :root {
        --background-color: #FFFDE7 !important;
        --secondary-background-color: #FFFDE7 !important;
    }
    html, body, .stApp, .main, [data-testid="stAppViewContainer"] {
        background-color: #FFFDE7 !important;
        background-image: none !important;
    }
    .block-container, [data-testid="stMainBlockContainer"], div[data-testid="stVerticalBlock"] {
        background-color: transparent !important;
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    components.html(
        """
        <script>
            try {
                var doc = window.parent.document;
                var main = doc.querySelector('.main') || doc.querySelector('[data-testid="stMainBlockContainer"]');
                if (main) {
                    main.scrollTo({top: 0, behavior: 'smooth'});
                } else {
                    window.parent.scrollTo(0, 0);
                }
            } catch(e) {}
        </script>
        """,
        height=0
    )
    
    idx = st.session_state.current_index
    q = st.session_state.questions[idx]
    stat = st.session_state.stats[idx]
    
    st.markdown(f"<p style='color: #7f8c8d; font-size: 14px;'>Pregunta {idx + 1} de {len(st.session_state.questions)}</p>", unsafe_allow_html=True)
    
    if q['preamble']:
        st.write(q['preamble'])
        
    st.markdown(f"<p style='font-size: 19px; font-weight: 600; color: #2C3E50; margin-bottom: 20px; line-height: 1.4;'>{q['question_text']}</p>", unsafe_allow_html=True)
    
    default_idx = q['options'].index(stat['selected']) if stat['selected'] in q['options'] else None
    
    # Vinculamos el evento on_change a la selección
    selected_option = st.radio("Elige tu respuesta:", q['options'], index=default_idx, key=f"radio_{idx}", label_visibility="collapsed", on_change=handle_radio_change)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    if col1.button("🡄 Anterior", use_container_width=True) and idx > 0:
        save_answer(selected_option)
        st.session_state.checked = False
        st.session_state.current_index -= 1
        st.rerun()
        
    if col2.button("Comprobar", use_container_width=True):
        save_answer(selected_option)
        st.session_state.checked = True
        st.rerun()
        
    if idx < len(st.session_state.questions) - 1:
        if col3.button("Siguiente ➔", use_container_width=True):
            save_answer(selected_option)
            st.session_state.checked = False
            st.session_state.current_index += 1
            st.rerun()
    else:
        if col3.button("Terminar ➔", use_container_width=True):
            save_answer(selected_option)
            st.session_state.finished = True
            st.rerun()
            
    if col4.button("⏹ Finalizar Test", use_container_width=True):
        save_answer(selected_option)
        st.session_state.finished = True
        st.rerun()

    if st.session_state.checked:
        correct_opt = q['options'][q['answer']] if q['answer'] != -1 else "?"
        if selected_option == correct_opt:
            st.success("✅ ¡CORRECTO!")
        elif not selected_option:
            st.warning(f"⚪ EN BLANCO. La correcta era: {correct_opt}")
        else:
            st.error(f"❌ INCORRECTO. La respuesta correcta era: {correct_opt}")
            
        exp = q.get('explanation', '').strip()
        # Aquí renderizamos la explicación inyectando los saltos de párrafo para Markdown
        st.info(f"**Explicación:**\n\n{exp if exp else 'No hay explicación disponible.'}")

else:
    # --- RESULTADOS FINALES ---
    
    st.markdown("""
    <style>
    :root { --background-color: #FFFFFF !important; --secondary-background-color: #FFFFFF !important; }
    html, body, .stApp, .main, [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)
    
    components.html(
        """
        <script>
            try {
                var doc = window.parent.document;
                var main = doc.querySelector('.main') || doc.querySelector('[data-testid="stMainBlockContainer"]');
                if (main) {
                    main.scrollTo({top: 0, behavior: 'smooth'});
                } else {
                    window.parent.scrollTo(0, 0);
                }
            } catch(e) {}
        </script>
        """,
        height=0
    )

    aciertos = 0
    fallos = 0
    blancos = 0
    
    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        correct_opt = q['options'][q['answer']] if q['answer'] != -1 else "?"
        if stat['selected'] == correct_opt:
            aciertos += 1
            stat['final_status'] = "✅ Correcta"
        elif stat['selected'] is None:
            blancos += 1
            stat['final_status'] = "⚪ En blanco"
        else:
            fallos += 1
            stat['final_status'] = "❌ Incorrecta"
            
    nota = (aciertos / len(st.session_state.questions)) * 10 if len(st.session_state.questions) > 0 else 0
    
    if nota >= 5.0:
        c_res1, c_res2, c_res3 = st.columns([1, 0.4, 1])
        with c_res2:
            try:
                st.image("test-utiles-768x768.png", use_container_width=True)
            except:
                pass
    else:
        c_res1, c_res2, c_res3 = st.columns([1, 1.5, 1])
        with c_res2:
            try:
                st.image("llorona.jpeg", use_container_width=True)
            except:
                pass
    
    st.markdown("<h3 style='text-align: center; color: #2C3E50;'>📊 RESULTADOS FINALES</h3>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; font-size: 16px; color: #555;'>✅ Acertadas: {aciertos} &nbsp;|&nbsp; ❌ Falladas: {fallos} &nbsp;|&nbsp; ⚪ En blanco: {blancos}</h4>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; font-size: 22px;'>🎓 NOTA FINAL: {nota:.2f} / 10</h3>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1_top, c2_top, c3_top = st.columns(3)
    c1_top.button("🔄 Repetir Test", key="btn_rep_top", on_click=action_repetir_test, use_container_width=True)
    c2_top.button("📁 Cambiar de Test", key="btn_sub_top", on_click=action_subir_otro, use_container_width=True)
    c3_top.button("🚪 Finalizar Sesión", key="btn_out_top", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
    st.markdown("---")
    
    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        correct_opt = q['options'][q['answer']] if q['answer'] != -1 else "?"
        color = "green" if stat['final_status'] == "✅ Correcta" else "red" if stat['final_status'] == "❌ Incorrecta" else "#FF8C00"
        
        st.markdown(f"<h4 style='color: {color}; font-size: 18px;'>Pregunta {i+1} | {stat['final_status']} | Intentos: {stat['attempts']}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:15px;'><b>Pregunta:</b> {q['question_text']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:15px;'><b>Tu respuesta:</b> {stat['selected'] if stat['selected'] else 'Ninguna'}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:15px;'><b>Respuesta correcta:</b> {correct_opt}</p>", unsafe_allow_html=True)
        
        exp_text = q.get('explanation', 'No disponible.').replace('\n', '<br>')
        st.markdown(f"<div style='background-color:#ffffff; border: 1px solid #e0e0e0; padding:12px; border-radius:8px;'><p style='font-size:14px; margin: 0;'><b>Explicación:</b><br>{exp_text}</p></div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1_bot, c2_bot, c3_bot = st.columns(3)
    c1_bot.button("🔄 Repetir Test", key="btn_rep_bot", on_click=action_repetir_test, use_container_width=True)
    c2_bot.button("📁 Cambiar de Test", key="btn_sub_bot", on_click=action_subir_otro, use_container_width=True)
    c3_bot.button("🚪 Finalizar Sesión", key="btn_out_bot", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
