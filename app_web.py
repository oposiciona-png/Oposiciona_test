import streamlit as st
import streamlit.components.v1 as components  
import fitz  # PyMuPDF
import re
import random
import requests

# --- CONFIGURACIÓN Y ESTILOS VISUALES DE LA PÁGINA ---
st.set_page_config(page_title="Plataforma de Tests Oposiciona", layout="centered")

# Inyección de CSS general para mejorar tipografías, opciones y botones
st.markdown("""
<style>
/* Aumentar tamaño de las opciones de respuesta y añadir separación */
div[role="radiogroup"] > label {
    margin-bottom: 12px !important; 
}
div[role="radiogroup"] > label > div:first-child > p {
    font-size: 17px !important; 
    line-height: 1.5 !important;
}

/* --- CÍRCULOS DE OPCIONES SÚPER NÍTIDOS, MÁS GRANDES Y NEGRO PURO --- */
div[data-baseweb="radio"] > div:first-child {
    border: 3px solid #000000 !important; /* Borde negro puro y grueso */
    width: 22px !important; /* Círculo un poco más grande */
    height: 22px !important;
    background-color: transparent !important;
}
div[data-baseweb="radio"][data-checked="true"] > div:first-child > div {
    background-color: #000000 !important; /* Punto interior negro puro */
    width: 12px !important; /* Punto interior un poco más grande */
    height: 12px !important;
}

/* Ajustes del contenedor para aprovechar el espacio */
.block-container {
    padding-top: 1.5rem !important;
    max-width: 750px !important; 
}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 🔒 SISTEMA DE SEGURIDAD Y ACCESO POR ROLES (AGRUPADO)
# ==============================================================================

# Lista actualizada de correos
USUARIOS_AUTORIZADOS = {
    "ACCESO TOTAL": [
        "ignacio@gmail.com",
        "alumno_total1@gmail.com",
        "ponentes@oposiciona.es",
        "gonzalogonzaleztejedor@gmail.com",
        "ignacio.garcia.heras@gmai.com",
        "alumno_total2@gmail.com"
    ],
    "ADMTVOS": [
        "alumno_admtvo1@gmail.com",
        "alumno1@gmail.com",
        "juan_admtvo@hotmail.com"
    ],
    "GESTION": [
        "alumno_gestion1@gmail.com",
        "alumno2@gmail.com",
        "maria_gestion@gmail.com"
    ]
}

PASSWORD_ACCESO = "plaza2026" 

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None

# CABECERA VISUAL (Ajustada para que el logo se vea completo)
col1, col2, col3 = st.columns([1, 0.8, 1]) 
with col2:
    try:
        st.image("oposiciona (320 x 132 px).png", use_container_width=True)
    except:
        pass
    st.markdown("<p style='text-align: center; font-size: 12px; margin-top: -15px;'><a href='https://oposiciona.es/' style='text-decoration: none; color: #1f77b4;'>🌐 oposiciona.es</a></p>", unsafe_allow_html=True)
st.markdown("---")


if not st.session_state.autenticado:
    # ADORNO DE BIENVENIDA (Muy pequeño y bajo el enlace)
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
# 🧠 MOTOR MAESTRO DE EXTRACCIÓN
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
                        line_text = ""
                        is_bold = False
                        for s in l["spans"]:
                            text = s["text"].strip()
                            if not text: continue
                            line_text += text + " "
                            if "bold" in s["font"].lower() or (s["flags"] & 2 != 0):
                                is_bold = True
                        
                        line_text = line_text.strip()
                        if line_text:
                            tl = line_text.lower()
                            tl_nospace = tl.replace(" ", "").replace(".", "").replace("-", "").replace(":", "")
                            
                            if ("preguntadedesarrollo" in tl_nospace or 
                                "preguntasdedesarrollo" in tl_nospace or 
                                "supuestopractico" in tl_nospace or 
                                "supuestopráctico" in tl_nospace or 
                                "plantilladerespuesta" in tl_nospace or 
                                "plantillasderespuesta" in tl_nospace):
                                stop_reading = True
                                break
                            
                            is_header = False
                            if len(tl) < 80:
                                if "www.oposiciona.es" in tl or re.search(r'^p[áa]gina\s+\d+\s+de\s+\d+', tl) or tl == "oposiciona":
                                    is_header = True
                                elif "administrativo de la seguridad social" in tl or "gestion de la seguridad social" in tl or "gestión de la seguridad social" in tl:
                                    is_header = True
                                elif "examen repaso" in tl or "test tema" in tl or "respuestas test" in tl or re.search(r'^tema\s+\d+', tl) or re.search(r'^examen\s+', tl) or "normas para la realización" in tl:
                                    is_header = True
                            
                            if is_header: continue
                            lines.append({"text": line_text, "bold": is_bold})
                            
        current_q = None
        preamble = "" 
        expected_q_num = 1  
        
        for line in lines:
            text = line["text"]
            is_bold = line["bold"]
            text_lower = text.lower()
            
            is_option = bool(re.match(r'^[a-zA-Z][\)\.]\s', text))
            is_explanation = text_lower.startswith("explicaci") or text_lower.startswith("resp:") or text_lower.startswith("respuesta:")
            
            if re.match(r'^\s*(preguntas?\s+de\s+reserva)', text_lower):
                if current_q and current_q["options"]: questions.append(current_q)
                current_q = None 
                preamble += text + "\n"
                continue

            is_new_q = False
            m_num = re.match(r'^\s*(\d+)[\.-]+(?!\d)', text) or re.match(r'^\s*(\d+)\s+[\.-]', text)
            m_rescue = False
            
            if not m_num and not is_option and not is_explanation:
                text_clean = text.strip()
                if (current_q and current_q["state"] in ["E", "O"]) or not current_q:
                    if re.match(r'^\s*\d+¿', text_clean) or (re.match(r'^\s*(¿|C[óo]mo|Cu[áa]l|Cu[áa]ntos|Qu[ée])\b', text_clean, re.IGNORECASE) and text_clean.endswith('?')):
                        m_rescue = True

            if m_num:
                num = int(m_num.group(1))
                if current_q is None:
                    is_new_q = True
                    expected_q_num = num + 1
                elif expected_q_num - 20 <= num <= expected_q_num + 50:
                    is_new_q = True
                    expected_q_num = num + 1
            elif m_rescue:
                is_new_q = True
                expected_q_num += 1

            if is_new_q:
                if current_q and current_q["options"]: questions.append(current_q)
                clean_text = re.sub(r'^\s*\d+[\.-]+\s*(-*\s*)?', '', text)
                clean_text = re.sub(r'^\s*\d+¿', '¿', clean_text)
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
                
                if is_new_paragraph or is_legal_ref:
                    current_q["state"] = "E"
                    current_q["explanation"] = text
                else:
                    if is_bold and current_q["answer"] == -1: current_q["answer"] = len(current_q["options"]) - 1
                    current_q["options"][-1] += " " + text
            elif current_q["state"] == "E":
                current_q["explanation"] += " " + text

        if current_q and current_q["options"]: questions.append(current_q)
        return questions

# ==============================================================================
# 💻 APLICACIÓN WEB INTERFAZ
# ==============================================================================

# 📂 LISTADO DE TESTS OBTENIDO DE DRIVE
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
    # Mostramos el adorno junto al selector de tests
    col_texto, col_img = st.columns([2.5, 1])
    with col_img:
        try:
            st.image("test-utiles-768x768.png", use_container_width=True)
        except:
            pass
            
    with col_texto:
        st.markdown("<h3 style='color:#2C3E50; margin-top: 10px;'>📚 Comienza a practicar</h3>", unsafe_allow_html=True)
        
        rol = st.session_state.rol
        
        # --- 1. MENÚ DE ESPECIALIDAD SEGÚN EL ROL ---
        st.markdown("#### 1. Especialidad")
        
        if rol == "ACCESO TOTAL":
            lista_especialidades = list(TESTS_DISPONIBLES.keys())
            especialidad = st.radio("Selecciona tu especialidad:", lista_especialidades, horizontal=True, label_visibility="collapsed")
        elif rol == "ADMTVOS":
            especialidad = "ADMINISTRATIVOS"
            st.info(f"Tienes acceso directo a tu especialidad: **{especialidad}**")
        elif rol == "GESTION":
            especialidad = "GESTION"
            st.info(f"Tienes acceso directo a tu especialidad: **{especialidad}**")
        else:
            st.error("Error en los permisos de usuario.")
            st.stop()
        
        # --- 2. CATEGORÍA ---
        st.markdown("#### 2. Categoría")
        lista_categorias = list(TESTS_DISPONIBLES[especialidad].keys())
        categoria = st.radio("Selecciona el tipo de test:", lista_categorias, horizontal=True, label_visibility="collapsed")
        
        # --- 3. SELECCIÓN FINAL DE TEST ---
        st.markdown("#### 3. Selección de Test")
        tests_categoria = TESTS_DISPONIBLES[especialidad][categoria]
        opcion_seleccionada = st.selectbox(f"Tests de {categoria}:", list(tests_categoria.keys()), label_visibility="collapsed")
    
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
    
    # CARGA MANUAL DE EMERGENCIA
    with st.expander("Opcional: Subir un test PDF manualmente desde tu dispositivo"):
        uploaded_file = st.file_uploader("", type="pdf")
        if uploaded_file is not None:
            with st.spinner("Procesando documento local..."):
                raw_qs = PDFQuizParser.parse(uploaded_file.read())
                if not raw_qs:
                    st.error("No se encontraron preguntas válidas en este PDF.")
                else:
                    procesar_preguntas(raw_qs)

elif not st.session_state.finished:
    
    # 🌟 FONDO AMARILLO MUY CLARO (SOLO DURANTE EL TEST)
    st.markdown("""
    <style>
    .stApp {
        background-color: #FFFDE7 !important; /* Amarillo pastel muy suave */
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 🌟 AUTO-SCROLL AL TOP EN CADA PREGUNTA
    components.html(
        """
        <script>
            var main = window.parent.document.querySelector('.main');
            if (main) {
                main.scrollTo(0, 0);
            }
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
        
    # TEXTO DE LA PREGUNTA
    st.markdown(f"<p style='font-size: 19px; font-weight: 600; color: #2C3E50; margin-bottom: 20px; line-height: 1.4;'>{q['question_text']}</p>", unsafe_allow_html=True)
    
    default_idx = q['options'].index(stat['selected']) if stat['selected'] in q['options'] else None
    selected_option = st.radio("Elige tu respuesta:", q['options'], index=default_idx, key=f"radio_{idx}", label_visibility="collapsed")
    
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
        st.info(f"**Explicación:**\n\n{exp if exp else 'No hay explicación disponible.'}")

else:
    # --- RESULTADOS FINALES ---
    
    # 🌟 AUTO-SCROLL AL TOP EN LOS RESULTADOS
    components.html(
        """
        <script>
            var main = window.parent.document.querySelector('.main');
            if (main) {
                main.scrollTo(0, 0);
            }
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
    
    # MOSTRAR IMAGEN SEGÚN LA NOTA OBTENIDA
    if nota >= 5.0:
        c_res1, c_res2, c_res3 = st.columns([1, 0.4, 1])
        with c_res2:
            try:
                st.image("test-utiles-768x768.png", use_container_width=True)
            except:
                pass
    else:
        # Columna central gigante para la llorona si suspende
        c_res1, c_res2, c_res3 = st.columns([1, 1.5, 1])
        with c_res2:
            try:
                st.image("llorona.jpeg", use_container_width=True)
            except:
                pass
    
    st.markdown("<h3 style='text-align: center; color: #2C3E50;'>📊 RESULTADOS FINALES</h3>", unsafe_allow_html=True)
    
    # TEXTOS DE RESUMEN MÁS PEQUEÑOS Y CENTRADOS
    st.markdown(f"<h4 style='text-align: center; font-size: 16px; color: #555;'>✅ Acertadas: {aciertos} &nbsp;|&nbsp; ❌ Falladas: {fallos} &nbsp;|&nbsp; ⚪ En blanco: {blancos}</h4>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; font-size: 22px;'>🎓 NOTA FINAL: {nota:.2f} / 10</h3>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1_top, c2_top, c3_top = st.columns(3)
    c1_top.button("🔄 Repetir Test", key="btn_rep_top", on_click=action_repetir_test, use_container_width=True)
    c2_top.button("📁 Cambiar de Test", key="btn_sub_top", on_click=action_subir_otro, use_container_width=True)
    c3_top.button("🚪 Finalizar Sesión", key="btn_out_top", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
    st.markdown("---")
    
    # DETALLE DE PREGUNTAS (Con letras reducidas para mayor estética)
    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        correct_opt = q['options'][q['answer']] if q['answer'] != -1 else "?"
        color = "green" if stat['final_status'] == "✅ Correcta" else "red" if stat['final_status'] == "❌ Incorrecta" else "#FF8C00"
        
        st.markdown(f"<h4 style='color: {color}; font-size: 18px;'>Pregunta {i+1} | {stat['final_status']} | Intentos: {stat['attempts']}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:15px;'><b>Pregunta:</b> {q['question_text']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:15px;'><b>Tu respuesta:</b> {stat['selected'] if stat['selected'] else 'Ninguna'}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:15px;'><b>Respuesta correcta:</b> {correct_opt}</p>", unsafe_allow_html=True)
        exp_text = q.get('explanation', 'No disponible.')
        st.markdown(f"<div style='background-color:#ffffff; border: 1px solid #e0e0e0; padding:12px; border-radius:8px;'><p style='font-size:14px; margin: 0;'><b>Explicación:</b><br>{exp_text}</p></div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1_bot, c2_bot, c3_bot = st.columns(3)
    c1_bot.button("🔄 Repetir Test", key="btn_rep_bot", on_click=action_repetir_test, use_container_width=True)
    c2_bot.button("📁 Cambiar de Test", key="btn_sub_bot", on_click=action_subir_otro, use_container_width=True)
    c3_bot.button("🚪 Finalizar Sesión", key="btn_out_bot", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
