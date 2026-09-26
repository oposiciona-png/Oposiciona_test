import streamlit as st
import fitz  # PyMuPDF
import re
import random
import requests

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Practicador de Tests Oposiciona", layout="centered")

# ==============================================================================
# 🔒 SISTEMA DE SEGURIDAD Y ACCESO RESTRINGIDO
# ==============================================================================

CORREOS_AUTORIZADOS = [
    "ignacio@gmail.com",
    "alumno1@gmail.com",
    "juan@hotmail.com"
]

PASSWORD_ACCESO = "plaza2026" 

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    try:
        st.image("oposiciona (320 x 132 px).png", width=320)
    except:
        pass
    
    st.markdown("## 🔒 Acceso Restringido")
    st.markdown("Plataforma exclusiva de Oposiciona. Introduce tus credenciales para acceder.")
    
    email_input = st.text_input("Correo electrónico asociado a tu cuenta")
    password_input = st.text_input("Contraseña de acceso", type="password")
    
    if st.button("Entrar a la plataforma", use_container_width=True, type="primary"):
        if email_input.lower().strip() in CORREOS_AUTORIZADOS and password_input == PASSWORD_ACCESO:
            st.session_state.autenticado = True
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

try:
    st.image("oposiciona (320 x 132 px).png", width=320)
except:
    pass

st.markdown("[www.oposiciona.es](https://oposiciona.es/)")
st.markdown("---")

# 📂 LISTADO DE TESTS AUTOMÁTICOS CLASIFICADOS
TESTS_DISPONIBLES = {
    "Administrativo": {
        "Elige un test de Administrativo...": None,
    "ADMINISTRATIVOS - ESPECIFICO - Copia de RESPUESTAS TEST  TEMA 9 NYCM": "https://drive.google.com/uc?export=download&id=17mH-VzUYRycZcsujzG2zJ77Dpm10DfEJ",
    "ADMINISTRATIVOS - ESPECIFICO - Copia de RESPUESTAS CASO PRÁCTICO TEMA 8B INCAPACIDAD PERMANENTE": "https://drive.google.com/uc?export=download&id=1MTmYVUK5nSCgI6L8iM_Zg1kz0E0nycho",
    "ADMINISTRATIVOS - ESPECIFICO - Copia de profesor TEST + SUPUESTO tema 4": "https://drive.google.com/uc?export=download&id=1V1vabkEbxPi_P8nnXtEjiLfHiYEkURDF",
    "ADMINISTRATIVOS - ESPECIFICO - Copia de PROFESOR TEST + SUPUESTO TEMA 3 AFILIACION": "https://drive.google.com/uc?export=download&id=1No5X4Yjoj2FwWw_jIGRvMuX27m7SXeIL",
    "ADMINISTRATIVOS - ESPECIFICO - Copia de PROFESOR TEST y SUPUESTOS TEMA 2C": "https://drive.google.com/uc?export=download&id=1LmGkZ6VNbLOK42XK784je_ePwZI1cUZm",
    "ADMINISTRATIVOS - ESPECIFICO - Copia de PROFESOR TEST y SUPUESTOS TEMA 2B": "https://drive.google.com/uc?export=download&id=1OGW-V2qE21Uu6CYWb6pklaGzjbpAgssO",
    "ADMINISTRATIVOS - ESPECIFICO - Copia de PROFESOR TEST y SUPUESTOS TEMA 2D": "https://drive.google.com/uc?export=download&id=1QelSvHbUrl6WGXEwxmcaBsO5oTAhma2d",
    "ADMINISTRATIVOS - ESPECIFICO - Copia de PROFESOR TEST y SUPUESTOS TEMA 2A": "https://drive.google.com/uc?export=download&id=1Wt-_iiVjHVeII_11jCU4CF8SBZ0nYrjl",
    "ADMINISTRATIVOS - ESPECIFICO - Copia de PROFESOR TEST Y SUPUESTOS TEMA 1 ESPECIFICO": "https://drive.google.com/uc?export=download&id=1HXIJvogWzKXVg0lt5TqlnsGk3KtTR4oI",
    },
    "Gestión": {
        "Elige un test de Gestión...": None,
        "GESTION - ESPECIFICO - Copia de PROFESOR TEST + PREGUNTA +  SUPUESTOS TEMA 51 ESPECIFICO": "https://drive.google.com/uc?export=download&id=1WZRt_NvefPgaDGGYymwxO7k2JNwd8vqB",
    }
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
    st.header("Comienza a practicar")
    
    # --- SELECTOR DE ESPECIALIDAD ---
    especialidad = st.radio("Selecciona tu especialidad:", ["Administrativo", "Gestión"], horizontal=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. CARGA AUTOMÁTICA DESDE DRIVE DEPENDIENDO DE LA ESPECIALIDAD
    tests_categoria = TESTS_DISPONIBLES[especialidad]
    opcion_seleccionada = st.selectbox(f"Tests oficiales de {especialidad}:", list(tests_categoria.keys()))
    
    if opcion_seleccionada and not opcion_seleccionada.startswith("Elige"):
        if st.button(f"Cargar {opcion_seleccionada}", type="primary", use_container_width=True):
            url_descarga = tests_categoria[opcion_seleccionada]
            with st.spinner(f"Extrayendo {opcion_seleccionada} de forma segura..."):
                try:
                    respuesta = requests.get(url_descarga)
                    if respuesta.status_code == 200:
                        raw_qs = PDFQuizParser.parse(respuesta.content)
                        if not raw_qs:
                            st.error("No se encontraron preguntas válidas en este PDF.")
                        else:
                            procesar_preguntas(raw_qs)
                    else:
                        st.error("Error de descarga. Comprueba que el enlace tiene permisos de lectura ('Cualquier persona con el enlace').")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 2. CARGA MANUAL
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
    idx = st.session_state.current_index
    q = st.session_state.questions[idx]
    stat = st.session_state.stats[idx]
    
    st.subheader(f"Pregunta {idx + 1} de {len(st.session_state.questions)}")
    if q['preamble']:
        st.write(q['preamble'])
    st.markdown(f"#### {q['question_text']}")
    
    default_idx = q['options'].index(stat['selected']) if stat['selected'] in q['options'] else None
    selected_option = st.radio("Elige tu respuesta:", q['options'], index=default_idx, key=f"radio_{idx}")
    
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
    st.header("📊 RESULTADOS FINALES")
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
    
    st.markdown(f"### ✅ Acertadas: {aciertos} | ❌ Falladas: {fallos} | ⚪ En blanco: {blancos}")
    st.markdown(f"## 🎓 NOTA FINAL: {nota:.2f} / 10")
    
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
        
        st.markdown(f"<h3 style='color: {color}; font-size: 22px;'>Pregunta {i+1} | {stat['final_status']} | Intentos: {stat['attempts']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:18px;'><b>Pregunta:</b> {q['question_text']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:18px;'><b>Tu respuesta:</b> {stat['selected'] if stat['selected'] else 'Ninguna'}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:18px;'><b>Respuesta correcta:</b> {correct_opt}</p>", unsafe_allow_html=True)
        exp_text = q.get('explanation', 'No disponible.')
        st.markdown(f"<div style='background-color:#f0f2f6; padding:15px; border-radius:5px;'><p style='font-size:18px;'><b>Explicación:</b><br>{exp_text}</p></div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1_bot, c2_bot, c3_bot = st.columns(3)
    c1_bot.button("🔄 Repetir Test", key="btn_rep_bot", on_click=action_repetir_test, use_container_width=True)
    c2_bot.button("📁 Cambiar de Test", key="btn_sub_bot", on_click=action_subir_otro, use_container_width=True)
    c3_bot.button("🚪 Finalizar Sesión", key="btn_out_bot", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
