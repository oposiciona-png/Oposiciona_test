import streamlit as st
import streamlit.components.v1 as components
import fitz  # PyMuPDF
import re, random, requests, os, unicodedata, time, json

icono_ruta = "ICONO OPOSICIONA.png"
st.set_page_config(page_title="Plataforma de Tests Oposiciona", page_icon=icono_ruta if os.path.exists(icono_ruta) else "📚", layout="centered")

st.markdown("""<style>
#MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], .stDeployButton, [data-testid="stAppDeployButton"] {visibility: hidden !important; display: none !important;}
[class*="viewerBadge"], [class*="styles_viewerBadge"] {display: none !important; opacity: 0 !important; pointer-events: none !important;}
div[role="radiogroup"] label {margin-bottom: 12px !important;}
div[role="radiogroup"] label, div[role="radiogroup"] label p, div[role="radiogroup"] label div, div[role="radiogroup"] label span {font-size: 17px !important; line-height: 1.3 !important; text-align: justify !important; color: #000000 !important; white-space: normal !important;}
div[data-baseweb="radio"] > div:first-child {border-color: #000000 !important; border-width: 2px !important;}
div[data-baseweb="radio"][data-checked="true"] > div:first-child > div {background-color: #000000 !important;}
.block-container {padding-top: 1rem !important; padding-bottom: 6rem !important; max-width: 750px !important;}
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button {background-color: #2e7d32 !important; border-color: #2e7d32 !important;}
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button p {color: #ffffff !important; font-weight: 600 !important; font-size: 17px !important;}
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button:hover {background-color: #1b5e20 !important; border-color: #1b5e20 !important;}
body, .stApp, .block-container, p, h1, h2, h3, h4, h5, h6, span {-webkit-user-select: none !important; -moz-user-select: none !important; -ms-user-select: none !important; user-select: none !important;}
input, textarea, [data-baseweb="input"] {-webkit-user-select: text !important; -moz-user-select: text !important; -ms-user-select: text !important; user-select: text !important;}
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

for k, v in [
    ('autenticado', False), ('rol', None), ('email', None), ('es_admin', False),
    ('do_scroll', False), ('mostrar_opciones_simulacro', False), ('celebracion_mostrada', False),
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

USUARIOS_ADMIN = ["ponentes@oposiciona.es", "ponentes@oposicona.es"]
USUARIOS_AUTORIZADOS = {
    "ACCESO TOTAL": ["ponentes@oposiciona.es", "ponentes@oposicona.es", "gonzalogonzaleztejedor@gmail.com", "ignacio.garcia.heras@gmail.com", "alvarezpugamartin@gmail.com", "claratoledo06@gmail.com", "blancazortega@gmail.com", "mijurista@gmail.com", "isabelmgutierrogil@gmail.com", "carmenvl28@gmail.com", "leticiagenerelosolana@gmail.com", "cguinaldobravo@gmail.com", "alvaro20011996@gmail.com", "sion.nuba@gmail.com"],
    "ADMTVOS": ["andreitalopeamor1@gmail.com", "elenavegasanchez73@gmail.com", "josemurillomoreno.mail@gmail.com", "raulff1997.rfg@gmail.com", "sandradcastanares@gmail.com", "joycewayland@gmail.com", "celia.pks@gmail.com", "cynthiaflafla14@gmail.com", "fragosotorbellinocarmen@gmail.com", "pherrerojulian@gmail.com", "rsilveiraescudero@gmail.com", "delfijv19@gmail.com", "marielipedreira@hotmail.com", "vanessagarciajimenez87@gmail.com", "luiscacid@gmail.com", "miguelromanrmm@gmail.com", "raquelkmacho@gmail.com"],
    "GESTION": ["vsaurod@gmail.com", "mariaquirosmonge5@gmail.com", "vanessagomeztdla@gmail.com", "zoemorcor@gmail.com", "julianayem@gmail.com", "yasminkhalili@gmail.com", "miriamvazquezseoane2000@gmail.com", "monetcacerescc@gmail.com", "maariiamaji@gmail.com", "micastroespejo@gmail.com", "aisacarrerapexe@gmail.com", "csanchezssmm@gmail.com", "maria.concal@gmail.com", "mariachinchurreta@gmail.com", "rocio10460@gmail.com", "manuelmuriel97@gmail.com", "hfdiaz99@gmail.com", "ireneizquierdo22@gmail.com", "mfangela23@gmail.com", "manuelsan240902@gmail.com"],
    "INVITADO": ["invitado@oposiciona.es", "invitado"]
}
PASSWORD_ADMIN, PASSWORD_ACCESO, PASSWORD_INVITADO = "Gonz4loN4cho23", "plaza2026", "oposiciona"

col1, col2, col3 = st.columns([1, 0.8, 1])
with col2:
    try: st.image("oposiciona (320 x 132 px).png", use_container_width=True)
    except: pass
    st.markdown("<p style='text-align: center; font-size: 12px; margin-top: -15px; margin-bottom: 0px;'><a href='https://oposiciona.es/' style='text-decoration: none; color: #1f77b4;'>🌐 oposiciona.es</a></p>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 5px; margin-bottom: 12px; border: none; border-top: 1px solid #d3d3d3;'>", unsafe_allow_html=True)

if not st.session_state.autenticado:
    c_img1, c_img2, c_img3 = st.columns([1, 0.25, 1])
    with c_img2:
        try: st.image("test-utiles-768x768.png", use_container_width=True)
        except: pass
    st.markdown("<h3 style='text-align: center; color: #2C3E50; margin-top: -5px;'>🔒 Acceso Restringido</h3><p style='text-align: center; font-size: 14px; margin-bottom: 20px;'>Plataforma exclusiva de <b>Oposiciona</b>. Introduce tus credenciales para acceder.</p>", unsafe_allow_html=True)
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


class PDFQuizParser:
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
                                r'^oposiciona\$', r'oposicionaes', r'^pagina\s+\d+\s+de\s+\d+\$', r'^(administrativo|gestion)\s+de\s+la\s+seguridad\s+social',
                                r'^(administrativo|gestion)\s+202\d\s+tema\s+\d+[a-z]?', r'^tema\s+\d+[a-z]?\s+(administrativo|gestion)\s+202\d\$',
                                r'^tema\s+\d+[a-z]?\s+campo\s+de\s+aplicacion\s+y\s+composicion',
                                r'^(general|especifico|examen|test|respuestas|respuestas\s+(tipo\s+)?test:?|test\s+profesor)\s+temas?\s+\d+',
                                r'^examen\s+repaso', r'^examen\s+[a-záéíóúñ0-9\s]+\s*202\d', r'^normas\s+para\s+la\s+realizacion', r'^especial\s+simulacros?',
                                r'^test\s+administrativo\s+\d+\s+todo\s+el\s+temario', r'^respuestas\s+tipo\s+test:\s+temas?\s+\d+'
                            ]:
                                if re.search(pat, tl_clean_spaces): is_header = True; break
                        if is_header: continue

                        line_text = re.sub(r'(?<=[.?!;\)\]"\'”])\s*(Explicaci[óo]n:|Respuest[as]?:|Resp:)\s', r'\n\1 ', line_text, flags=re.IGNORECASE)
                        line_text = re.sub(r'(?<=\S)\s{2,}(Explicaci[óo]n:|Respuest[as]?:|Resp:)\s', r'\n\1 ', line_text, flags=re.IGNORECASE)
                        line_text = re.sub(r'(?<=\S)\s*(OJO|NOTA|IMPORTANTE|RECUERDA):', r'\n\1:', line_text, flags=re.IGNORECASE)
                        line_text = re.sub(r'(?<=[.?!;”"\'\)])\s*(Art[íi]culo aplicable:|Art[íi]culo|Art\.)\s', r'\n\1 ', line_text, flags=re.IGNORECASE)
                        line_text = re.sub(r'(?<=\S)\s+([•\*])(\s|$)', r'\n\1\2', line_text)
                        line_text = re.sub(r'(?<=[a-zA-ZáéíóúñÁÉÍÓÚÑ\)])(?<!\d)(\d{1,3}[\.\-\)])(?!\s*[ºª°])\s+(?=[A-ZÁÉÍÓÚÑ¿¡"\'«])', r'\n\1 ', line_text)
                        line_text = re.sub(r'([.?!;])\s+([a-eA-E][\)\.\-])\s*(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])', r'\1\n\2 ', line_text)
                        line_text = re.sub(r'(?<!\d)([.?!;])([a-eA-E][\)\.\-])\s*(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])', r'\1\n\2 ', line_text)
                        line_text = re.sub(r'(?<=[a-zA-ZáéíóúñÁÉÍÓÚÑ])\s+([a-eA-E][\)\.\-])\s*(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])', r'\n\1 ', line_text)
                        line_text = re.sub(r'(?<=\S)\s*(\(p[aá]gina\s+\d+[^)]*\))', r'\n\1', line_text, flags=re.IGNORECASE)

                        for part in line_text.split('\n'):
                            part = part.strip()
                            if part:
                                lines.append({"text": re.sub(r'^([a-fA-F][\)\.-])(?=[^\s])', r'\1 ', part), "bold": is_bold})
                    lines.append({"text": "<NEW_BLOCK>", "bold": False})

        # Unir referencias legales partidas al final de línea (ej. "art." + "136.2.o)")
        merged_lines, i = [], 0
        while i < len(lines):
            curr = lines[i]
            txt = curr["text"].strip()
            if txt != "<NEW_BLOCK>" and re.search(r'(?:«|"|“|\b)(?:Art[íi]culos?|Art\.|Ley|Real\s+Decreto|Decreto|n[º°\.]?)\s*$', txt, re.IGNORECASE):
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

        pdf_uses_explicit_exp = sum(1 for l in lines if re.match(r'^(explicaci[óo]n|respuesta|resp)s?:', l["text"].strip(), re.IGNORECASE)) >= 10
        current_q, preamble, expected_q_num = None, "", 1

        def match_question_number(s):
            """Reconoce números de pregunta reales (ej. '36.- Texto', '1. Texto', '1 ¿Texto') e ignora '136.2.o)' o '2º'."""
            return (
                re.match(r'^\s*(?:Pregunta\s+)?(\d+)[,\.\-\)]+(?!\d|[ºª°]|[a-zA-Z]\))\s+\S', s, re.IGNORECASE) or
                re.match(r'^\s*(?:Pregunta\s+)?(\d+)\s+[,\.\-\)]+(?!\d|[ºª°])\s*\S', s, re.IGNORECASE) or
                re.match(r'^\s*(?:Pregunta\s+)?(\d+)[,\.\-\)]*\s*¿', s, re.IGNORECASE)
            )

        for idx, line in enumerate(lines):
            text, is_bold = line["text"], line["bold"]
            if text == "<NEW_BLOCK>":
                if current_q and current_q["state"] == "E" and current_q["explanation"]:
                    if current_q["explanation"].strip()[-1:] in ['.', ':', '?', '!', '"', '”', '»', ')'] and not current_q["explanation"].endswith("\n\n"):
                        current_q["explanation"] = current_q["explanation"].rstrip() + "\n\n"
                continue

            text_lower = text.lower()
            is_option = bool(re.match(r'^[a-zA-Z][\)\.\-]\s*', text))
            is_explanation = False if (current_q and current_q["state"] == "E") else bool(re.match(r'^(explicaci|resp:|respuesta:|respuestas:)', text_lower))

            forced_not_option = False
            if is_option and current_q and current_q["state"] == "Q" and not current_q["options"]:
                if text.strip().endswith('?') and not re.match(r'^[a-zA-Z][\)\.\-]\s*[¿A-ZÁÉÍÓÚÑ]', text):
                    is_option, forced_not_option = False, True

            is_reserve = bool(re.search(r'\bpreguntas?\s+de\s+reserva\b', text_lower) or re.match(r'^\s*reserva\b', text_lower))
            is_case_study = bool(re.match(r'^\s*(supuestos?\s+pr[áa]cticos?)', text_lower))
            is_letter_block = bool(re.match(r'^[A-ZÑ][\)\.-]+\s*[A-ZÁÉÍÓÚÑ]', text))
            if is_letter_block and (re.search(r'\b(fals[ao]|verdader[ao]|correct[ao]|incorrect[ao])\b', text_lower) or (current_q and current_q["state"] == "E" and pdf_uses_explicit_exp)):
                is_letter_block = False

            if (is_reserve or is_case_study or is_letter_block) and (not current_q or current_q["state"] == "E"):
                is_real_preamble = any(
                    match_question_number(lines[j]["text"].strip()) or
                    (re.match(r'^\s*(¿|C[óo]mo|Cu[áa]l|Cu[áa]ntos|Qu[ée])\b', lines[j]["text"].strip(), re.IGNORECASE) and lines[j]["text"].strip().endswith('?'))
                    for j in range(idx + 1, min(idx + 30, len(lines)))
                )
                if is_real_preamble or is_reserve or is_case_study:
                    if current_q and current_q["options"]: questions.append(current_q)
                    current_q, preamble, expected_q_num = None, preamble + text + "\n", 1
                    continue

            is_new_q = False
            m_num = match_question_number(text)

            if m_num and current_q and current_q["state"] == "E":
                if re.search(r'(?:«|\b)(?:Art[íi]culos?|Art\.|Ley|Real\s+Decreto)\s*$', current_q["explanation"].strip()[-60:], re.IGNORECASE):
                    m_num = None

            m_rescue = False
            if not m_num and not is_option and not is_explanation and not pdf_uses_explicit_exp:
                tc = text.strip()
                if ((current_q and current_q["state"] in ["E", "O"]) or not current_q) and re.match(r'^\s*(¿|C[óo]mo|Cu[áa]l|Cu[áa]ntos|Qu[ée])\b', tc, re.IGNORECASE) and tc.endswith('?'):
                    m_rescue = True

            if m_num or m_rescue:
                is_real_q_candidate = found_a = found_b = aborted = False
                for j in range(idx + 1, min(idx + 60, len(lines))):
                    ft = lines[j]["text"].strip()
                    if ft == "<NEW_BLOCK>": continue
                    m_fnum = match_question_number(ft)
                    if not found_a:
                        if re.match(r'^(explicaci[óo]n|respuesta|resp)s?:', ft, re.IGNORECASE) or m_fnum:
                            aborted = True; break
                        if re.match(r'^a[\)\.\-](\s|$)', ft, re.IGNORECASE): found_a = True
                    elif not found_b:
                        if re.match(r'^(explicaci[óo]n|respuesta|resp)s?:', ft, re.IGNORECASE):
                            aborted = True; break
                        if re.match(r'^b[\)\.\-](\s|$)', ft, re.IGNORECASE):
                            found_b = True
                            if not pdf_uses_explicit_exp: is_real_q_candidate = True; break
                    else:
                        if re.match(r'^(explicaci[óo]n|respuesta|resp)s?:', ft, re.IGNORECASE):
                            is_real_q_candidate = True; break
                        if re.match(r'^\(p[aá]gina\s+\d+', ft, re.IGNORECASE) or m_fnum:
                            aborted = True; break

                if is_real_q_candidate and not aborted:
                    if m_num:
                        num = int(m_num.group(1))
                        prev_closed_with_pageref = bool(current_q and current_q["state"] == "E" and re.search(r'\(p[aá]gina\s+\d+', current_q["explanation"], re.IGNORECASE))
                        if current_q is None:
                            is_new_q, expected_q_num = True, num + 1
                        elif expected_q_num - 1 <= num <= expected_q_num + 5:
                            is_new_q, expected_q_num = True, num + 1
                        elif num == 1 and current_q["state"] in ["O", "E"] and expected_q_num >= 10:
                            is_new_q, expected_q_num = True, 2
                        elif prev_closed_with_pageref and expected_q_num < num <= expected_q_num + 35:
                            is_new_q, expected_q_num = True, num + 1
                    elif m_rescue:
                        is_new_q = True; expected_q_num += 1

            if is_new_q:
                if current_q and current_q["options"]: questions.append(current_q)
                ct = re.sub(r'^\s*(?:Pregunta\s+)?\d+\s*¿', '¿', re.sub(r'^\s*(?:Pregunta\s+)?\d+[,\.\-\)]+\s*(-*\s*)?', '', text, flags=re.IGNORECASE), flags=re.IGNORECASE)
                current_q, preamble = {"preamble": preamble.strip(), "question_text": ct, "options": [], "answer": -1, "explanation": "", "state": "Q"}, ""
                continue

            if not current_q:
                if not is_reserve: preamble += text + "\n"
                continue

            if is_option and current_q["state"] in ["Q", "O"] and re.match(r'^([a-eA-E])[\)\.-]\s*', text):
                current_q["options"].append(text)
                current_q["state"] = "O"
                if is_bold and current_q["answer"] == -1: current_q["answer"] = len(current_q["options"]) - 1
                continue

            if is_explanation:
                current_q["explanation"] = (current_q["explanation"].rstrip() + "\n\n" + text) if current_q["explanation"] else text
                current_q["state"] = "E"
                continue

            if current_q["state"] == "Q":
                if forced_not_option and re.search(r'[a-zA-Z]$', current_q["question_text"].strip()):
                    m = re.match(r'^([a-zA-Z])([\)\.\-])\s*(.*)', text)
                    current_q["question_text"] = (current_q["question_text"].strip() + m.group(1) + m.group(2) + " " + m.group(3)) if m else (current_q["question_text"] + " " + text)
                else:
                    current_q["question_text"] += " " + text
            elif current_q["state"] == "O":
                lo = current_q["options"][-1].strip()
                ep = bool(re.search(r'[\.;\?]$', lo))
                ec = bool(re.search(r'(,| y| o| que| de| a| con| en| por| para| el| la| los| las| un| una)$', lo, re.IGNORECASE))
                inp = len(current_q["options"]) >= 2 and ep and bool(re.match(r'^[A-Z0-9¿¡"\'«]', text))
                ilr = bool(re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|seg[úu]n)\b', text_lower))
                iie = len(current_q["options"]) >= 3 and bool(re.match(r'^[A-ZÁÉÍÓÚ¿¡"\'«]', text)) and (
                    bool(re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|seg[úu]n|normativa|de conformidad|conforme|en virtud)\b', text_lower)) or
                    (bool(re.match(r'^(el\b|la\b|los\b|las\b|para\b|de\b|en\b|cuando\b|se\b|es\b|esta\b|este\b|al\b|por\b|si\b)', text_lower)) and (ep or not ec))
                )
                if len(current_q["options"]) < 2 or ec or len(lo) <= 5: inp = ilr = iie = False
                if inp or ilr or iie:
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
                    io = bool(re.match(r'^[\s]*(OJO|NOTA|IMPORTANTE|RECUERDA)[\s:]', text, re.IGNORECASE))
                    ipr = bool(re.match(r'^\(p[aá]gina\s+\d+', text, re.IGNORECASE))
                    ins = lc in ['.', ':', '?', '!', '"', '”', '»'] and bool(re.match(r'^[\s]*([A-ZÁÉÍÓÚ¿¡"\'«]|\d)', text))
                    if ipr or ib or io or ins:
                        current_q["explanation"] = current_q["explanation"].rstrip() + "\n\n" + text
                    else:
                        current_q["explanation"] += (" " + text) if current_q["explanation"] else text

        if current_q and current_q["options"]: questions.append(current_q)
        return questions


_D = "https://drive.google.com/uc?export=download&id="

TESTS_DISPONIBLES_COMPLETO = {
    "ADMINISTRATIVOS": {
        "ESPECIFICO": {
            "Elige un test de especifico...": None,
            "TEMA 01 ESPECIFICO": _D + "1HXIJvogWzKXVg0lt5TqlnsGk3KtTR4oI",
            "TEMA 02A": _D + "1W_f3M0AytaH9K4tI5Puuwn3zDCGTpGEm",
            "TEMA 02B": _D + "1OGW-V2qE21Uu6CYWb6pklaGzjbpAgssO",
            "TEMA 02C": _D + "1LmGkZ6VNbLOK42XK784je_ePwZI1cUZm",
            "TEMA 02D": _D + "1QelSvHbUrl6WGXEwxmcaBsO5oTAhma2d",
            "TEMA 03 AFILIACION": _D + "1No5X4Yjoj2FwWw_jIGRvMuX27m7SXeIL",
            "TEMA 04 - TEST Y SUPUESTOS COTIZACION": _D + "1MQX-qeTgsqPliBN9lngLXL62YeSU1NCf",
            "Tema 04 COTIZACION": _D + "1V1vabkEbxPi_P8nnXtEjiLfHiYEkURDF",
            "TEMA 08 IP": _D + "1e_ZHpayJ6jm4mIOvQN4joteVAWIIZyPB",
            "TEMA 08 REPASO 1 IT E IP ESPECÍFICO": _D + "1MSNhFX96UrMQRFHdMgsg-t5b_TxdjD-l",
            "TEMA 08 REPASO 2 IT E IP ESPECÍFICO": _D + "1dumhT6HC4Hx_Pt8JdAKIFWQOPx9nA2RA",
            "TEMA 09 NYCM": _D + "17mH-VzUYRycZcsujzG2zJ77Dpm10DfEJ",
            "TEMA 09 REPASO 1 NYCM ESPECÍFICO": _D + "1GS2QAO6LF8AssgnEEGlEBcLnuZCb5i70",
            "TEMA 09 REPASO 2 NYCM ESPECÍFICO": _D + "16AgKFfosMJIx0mmrgBv3Rad5tNkKNSH5",
            "TEMA 10 JUBILACION": _D + "1LQSV7oG52ZNAmwR_Z46iQxZUN7VMtfEj",
            "TEMA 10 REPASO 1 JUBILACIÓN ESPECÍFICO": _D + "19EE33UzOmjga9OARfG_Ui_LEpHb4BtYl",
            "TEMA 10 REPASO 2 JUBILACIÓN ESPECÏFICO": _D + "1XXIvHSXKB-ocM-y_mzziaiJVBi-9u2lX",
            "TEMA 11 REPASO 1 MUERTE Y SUPERVIVENCIA ESPECÍFICO": _D + "1_y2UgAkXvCZzmHNDLrCWjqiwUtE2PvdQ",
            "TEMA 11 REPASO 2 MUERTE Y SUPERVIVENCIA ESPECÍFICO": _D + "1f5RPEipUNgF8HvYMGOChC0Hbw9tDFN7p",
            "TEMA 12 IREPASO 1 MV ESPECÍFICO": _D + "18eb8lGYuHF2zvI4hU9YN0X91SFBhlKGW",
            "TEMA 12 REPASO 2 IMV ESPECÍFICO": _D + "1jWPfnprPvL9uyCrfw4k3fkH816wEqE_C",
        },
        "EXAMENES": {
            "Elige un test de examenes...": None,
            "EXAMEN OFICIAL 2023 ACTUALIZADO A 2026": _D + "1zWrxEUexvs5IVFa3WSM96ezQ12-6NegN",
            "EXAMEN OFICIAL 2026 B ROJO": _D + "1fmh5zACnL7mPA29bxdAhhJqqm5cagv5L",
            "EXAMEN REPASO 1 TEMA 01 a 14 GENERAL": _D + "1k0eOdHU9ZYuXP2HXw172joKzi9P25l-m",
            "EXAMEN REPASO 1 TEMA 08 a 12 ESPECÍFICO": _D + "1Qau_6V0CjEoRAtxHigSqMjglkeCjfEB2",
            "EXAMEN REPASO TEMA 2 COMPLETO": _D + "1K60xc80vJAhbGKNs_2_UhooQ0ovSSUC2",
            "SABADO 10 OCT 2026": _D + "14rEqmgmwUPjcoAzA3H5EAux7aIWrFgsq",
            "SABADO 5 SEP 2026": _D + "1XGMVM7M0kRrNGyZYa3N-npLO7pYETxVa",
        },
        "GENERAL": {
            "Elige un test de general...": None,
            "TEMA 01 a 03 CONSTITUCIONAL": _D + "14z3ZzvLLVZQ0XiUKx4qmiyneMoldZIB2",
            "TEMA 01 a 03 REPASO CONSTITUCION GENERAL": _D + "153p-VAMdsxaXu47tqkkNOIjhO9mWhxVX",
            "TEMA 04 LA JEFATURA DEL ESTADO": _D + "1y-u-_wTqfIyB_fn0he0cvyKAPLjsM06A",
            "TEMA 04 REPASO LA CORONA GENERAL": _D + "1yeSHcMWRBtuotYSqUXUMgLQ-9KLXKbmG",
            "TEMA 05 REPASO CORTES GENERALES GENERAL": _D + "1gGNUiRh7Ia1rS-sCEr8B1et94OXOOc2k",
            "TEMA 05 y 06 PODER LEGISLATIVO Y JUDICIAL": _D + "1Hog53fH7CsG1FCk6CC0X4m4tIXZ2tPYd",
            "TEMA 06 REPASO PODER JUDICIAL GENERAL": _D + "1SQoWQlO1Cnoc_WpP0VTmUlPSumT5FgkG",
            "TEMA 07 PODER EJECUTIVO": _D + "1BXKLo950u1GSODuag-lds2SCbBTYF2UD",
            "TEMA 07 REPASO PODER EJECUTIVO GENERAL": _D + "1v9ms7CaSFNyZAPM2qQoC_3_TO9gQ8wC7",
            "Tema 08 ADM GRAL ESTADO": _D + "1sjO0bi2IwPJpPcESpQkWvqROPAHJ12L6",
            "TEMA 08 REPASO AGE GENRAL": _D + "1PnGmAEZwJkVOwfzG4YMgs3LRNZa19KIz",
            "TEMA 09 CCAA Y MUNICIPIOS general": _D + "1zk4mZRrMPIb8AnOD_8pFAPL-utUeFGKZ",
            "TEMA 09 REPASO CCAA GENERAL": _D + "198XcxyyIPDFTJe22rsqYkXmfE1CTsjDH",
            "TEMA 10 INSTITUCIONES DE LA UE general": _D + "1IGcXDNtMwW7MuhPon95EycFwOHrVQbW7",
            "TEMA 10 REPASO INSTITUCIONES DE LA UE GENERAL": _D + "1Hw1l1-2_zsGfX4tbjUuw1DDokmE682e9",
            "TEMA 11 REPASO FUENTES DE LA UE GENERAL": _D + "1YLmKCK14-W0TfRwndlhUSkeWoOMtWxY-",
            "TEMA 13 REPASO FUENTES DEL DERECHO GENERAL": _D + "1pMqfE5ThZaFgiqvqAWnXFeYfkOwCMUur",
            "TEMA 14 REPASO LA LEY GENERAL": _D + "1k4RXRU6DKUQZ-MCI9A0T3kgiGOL39zgN",
        },
    },
    "GESTION": {
        "ESPECIFICO": {
            "Elige un test de especifico...": None,
            "TEMA 51 - CONSTITUCION EN LA SS Y TRLGSS": _D + "1LlQvfrYuVXx2mJETTpfDGdhE2hyAWUZn",
            "TEMA 52 - CAMPO DE APLICACIÓN Y COMPOSICIÓN DEL SISTEMA": _D + "1ZcpNzh3IIu40K8eDcQCKpmWKrhvBUE_v",
            "TEMA 52 - REPASO 1 - CAMPO APLICACION": _D + "1oqziTFYRP3C4TQNqlAoiY1YohyrwRZTm",
            "TEMA 53 - AFILIACION": _D + "1CUhqhupF7_aiL5vjvP6aZlLjPay9xTOs",
            "TEMA 53 - REPASO 1 - AFILIACION": _D + "1DuFQD1pFPMXVFDdR9NWS9pmVGfv0JYR7",
            "TEMA 55 ACCIÓN PROTECTORA CONTENIDO Y CLASIFICACIÓN DE LAS PRESTACIONES": _D + "1OmVgiP6fGsGAYZ71v-vIKahly4V06-6o",
            "TEMA 55 REPASO PRESTACIONES ESPECÍFICO": _D + "1sZoz0-f-oMafO1pRuCnhpF835lt_-FgW",
            "TEMA 56 REPASO ACCION PROTECTORA ESPECÏFICO": _D + "1d0Q3K5dB3dT9rVjuXXCy-RX_37xIDKbO",
            "TEMA 56 REQUISITOS GENERALES DE LAS PRESTACIONES": _D + "1xLJwqD3zFtgGS-Q_jGa3fHFZPnNacGwz",
            "TEMA 57 INCAPACIDAD TEMPORAL": _D + "1lrSFSMDbecfW_aGYId5QChIhgVyYFKC5",
            "TEMA 57 REPASO INCAPACIDAD TEMPORAL ESPECÍFICO": _D + "1KwxD3UEy0VgtFf5Kf_z6RlKXCdh0vICF",
            "TEMA 58 - NYCM": _D + "1iw4NDqaC1gMGiMgd-VZTbtaoWyWKLE8L",
            "TEMA 58 REPASO NACIMIENTO Y CUIDADO DEL MENOR ESPECÍFICO": _D + "1eL8YOkh6PtaUkMMCHp8V1dDJHyN0V4bp",
            "TEMA 59 y 60 IP": _D + "16ahUMTSgXAcjTVH700BoL6eZgwQo2_7E",
            "TEMA 59 y 60 IP y LESIONES PERMANENTES": _D + "12_N6QFcTShR-w-yX9ptJD9pbfC_CQuUD",
            "TEMA 59 y 60 REPASO INCAPACIDAD PERMANETE ESPECÍFICO": _D + "1KCbfeYJhi8ANXEGcilye4IrYjtsOknfM",
            "TEMA 61 JUBILACION": _D + "1K2u4rSuqXjjBJ3wzKQbn84Ezu-9Ibg-d",
            "TEMA 61 REPASO  JUBILACIÓN ESPECÍFICO": _D + "1csf7oIdntqrXRhA2CLSMJqn7J1AMog0T",
            "TEMA 62 REPASO MUERTE SUPERVIVENCIA ESPECÍFICO": _D + "1j8MmXwrdpeLR7VEfzkEPixUZbn83KjNE",
            "TEMA 64 IMV REPASO ESPECÍFICO": _D + "1n6hNSEgl5w2sSqN2dNcVGe_pqKKQi36x",
            "TEMA 67 - REPASO 1 - COTIZACION": _D + "1uUEBkcwMwsOtS6LmQ2Q_PhxAzbO7TCyp",
            "Tema 67 COTIZACION": _D + "1kErdym1yxTP-Qd0Frx-5XIwOkI3aq5aL",
            "TEMA 73 - LOS REGIMENES ESPECIALES DE LA S SOCIAL": _D + "16JKTt0G8UycnAsclRtoHC1mGkgDtvHI0",
            "TEMA 73 - REPASO 1 - REGIMES ESPECIALES INTEGRADO EN RG": _D + "1A2tEioQS4Xfd7OAcOWsCOnDWfSMla1dW",
            "TEMA 74 - RETA, SETA  Y MAR": _D + "1N2ezL7ohgKxcoZVPex_oGday9JHMMxl7",
            "TEMA 74.- REPASO 1 - RETA SETA Y MAR": _D + "1VFu51nTOGd5fknYDmd5mUkc_Z_Ma0pwr",
            "TEMA 75 - MINERIA - SEGURO ESCOLAR FUNCIONARIOS": _D + "1eHZ9Ajqujk-wtnzcsAo_e6lpkH9kfrao",
        },
        "EXAMENES": {
            "Elige un test de examenes...": None,
            "DOMINGO 6 SEP 2026": _D + "1pEuW36jClxKZQjwAuSx6TpfFaxlmkcln",
            "Examen oficial 17 de mayo de 2026": _D + "1-ZFGIZGsixCwIS5Tr_4dZ5hX8mcX4yDL",
            "EXAMEN REPASO 1 TEMA 42 a 50 GENERAL": _D + "1WXCXKhlCSgPzm4TrWIvrrV1ffzUGYog3",
            "EXAMEN REPASO 1 TEMA 55 a 65 ESPECÍFICO": _D + "1ZpHomgomojh3AsKBton7A7OloVLfoKTk",
            "EXAMEN REPASO TEMA 6 a 10 DERECHO MERCANTIL": _D + "16vMfq7ToTQBXr1-f8nB89FVO_Y2yGG1A",
        },
        "GENERAL": {
            "Elige un test de general...": None,
            "TEMA 01 y 02 CIVIL general": _D + "1YsqXQvC-dWW6ybnrP3vgwfphjHwwPHuk",
            "TEMA 06 -  LA EMPRESA MERCANTIL": _D + "17myj2PoQaWv_wZn7OV13wESOS7gBVNSN",
            "TEMA 07 - SOCIEDAD ANONIMA": _D + "1_vZNRIHwJIcoPHdGyhbg7s-UEQEGrvMK",
            "TEMA 08 - TITULOS VALORES": _D + "1JjPfA7i3yP1Xuqx19IBJQrYYZMYh6MoS",
            "TEMA 09 - LAS OBLIGACIONES MERCANTILES": _D + "1ZhUqRGsA8SV8k4QPzVuGz0t2yXzdElXj",
            "TEMA 10 - DERECHO MERCANTIL - CONCURSO ACREEDORES": _D + "1Tcn1glkQI4DkbjnHap3SY9B2gU49tWgT",
            "TEMA 40 - IGUALDAD": _D + "1tJ3MrhWg8GafmEfT7zX1hqnFNzPFmhAg",
            "TEMA 41 GOBIERNO ABIERTO Y AGENDA 2030": _D + "1eCF7-MBTZ3SWJX2-agLKqQstxSXkdqJ_",
            "TEMA 42 a 50 REPASO LABORAL GENERAL": _D + "1-XZ-qj8ITF0lPkDJMbOWXS2xcku-pAR6",
            "TEMA 42 EL DERECHO DEL TRABAJO": _D + "1ARQ8PoNtyTykdcbixOxWgEr4SZ7sZV6c",
            "TEMA 42 REPASO DERECHO DEL TRABAJO GENERAL": _D + "1_CNXYhEr-9WeBn-w9TA-iH3fG8VwII_N",
            "TEMA 43 CONVENIOS COLECTIVOS": _D + "11uc4s9pZP5-vAnbUY7klhQOVR10rCpYg",
            "TEMA 43 REPASO CONVENIOS COLECTIVOS GENERAL": _D + "1euDzEZfvjhx_3jGFaTo5kbNBP7aynypY",
            "TEMA 44 CONTRATOS": _D + "1LRLQAx8Ql3MnMEe1kksaBQIiXUvuR2VT",
            "TEMA 44 REPASO CONTRATOS GENERAL": _D + "1IBvudhfW61OhkBC_MZuTskWyEoLjcIJR",
            "TEMA 45 REPASO SALARIO Y JORNADA 2 GENERAL": _D + "1KgsKYzyEHWFwf70i_WcmA7bCDMQ5IuGP",
            "TEMA 45 REPASO SALARIO Y JORNADA GENERAL": _D + "1QbifFgtRs2xui2vOPNeLbtBW5uVGTZE_",
            "TEMA 45 SALARIO Y JORNADA": _D + "1RRl35OdPYxOVs4f2L1GZkQO4EAgZoSWm",
            "TEMA 46 MODIFICACIÓN SUSTANCIAL": _D + "1LGFdvQcFjuinwdXWf6AM66QKoOL9_dn6",
            "TEMA 46 REPASO PODER DE DIRECCIÓN 2 GENERAL": _D + "1dnUG57MFsZguAWy2Di_Bp24UoeZZLO6o",
            "TEMA 46 REPASO PODER DE DIRECCIÓN GENERAL": _D + "1tz8uIUPD5Re1GgzgUh2TjhVryNeZGj-I",
            "TEMA 47 REPASO SUSPENSIÓN DEL CONTRATO GENERAL": _D + "1eWtbwM_wShFHNZOih5UyP8LfGVB_nUZR",
            "TEMA 47 SUSPENSIÓN": _D + "1-kTGpXGLGBbbdKe26Lhq9gPXxZKCc44L",
            "Tema 48 - Extinción del Contrato": _D + "1mbE4W0EnqJa9IosTYk2iEHbs2aBQOFdH",
            "TEMA 48 REPASO DESPIDO COLECTIVO GENERAL": _D + "1N66XYQvXIWdiEbd7B3E_yFn97a4nnf-_",
            "TEMA 49 REPASO DESPIDO GENERAL": _D + "1FXOlDF71QbID0Z9THcf8hO899XIWjtyu",
            "TEMA 49 y 50 DESPIDO Y HUELGA": _D + "1FFt9QtwAeTz-U0VvCZQMaf15xS4s33bd",
            "TEMA 50 REPASO CONFLICTOS COLECTIVOS GENERAL": _D + "10A9Fx_wO7Y-_Mw27YxR153ketgZ3WUB_",
        },
    },
}

TESTS_DISPONIBLES_INVITADO = {
    "ADMINISTRATIVOS": {
        "ESPECIFICO": {"Elige un test de especifico...": None, "TEMA 04 - TEST Y SUPUESTOS COTIZACION": _D + "1MQX-qeTgsqPliBN9lngLXL62YeSU1NCf"},
        "EXAMENES": {"Elige un test de examenes...": None},
        "GENERAL": {"Elige un test de general...": None},
    },
    "GESTION": {
        "ESPECIFICO": {"Elige un test de especifico...": None, "TEMA 53 - AFILIACION": _D + "1CUhqhupF7_aiL5vjvP6aZlLjPay9xTOs"},
        "EXAMENES": {"Elige un test de examenes...": None},
        "GENERAL": {"Elige un test de general...": None},
    },
}

def usuario_es_admin():
    correo_act = (st.session_state.get('email') or "").lower().strip()
    return bool(st.session_state.get('es_admin', False) or correo_act in USUARIOS_ADMIN)

def usuario_puede_reportar():
    """Permite reportar errores a todos los usuarios registrados excepto al rol INVITADO."""
    return st.session_state.get('rol') != 'INVITADO'

def obtener_tests_segun_rol():
    return TESTS_DISPONIBLES_INVITADO if st.session_state.get('rol') == 'INVITADO' else TESTS_DISPONIBLES_COMPLETO

def descargar_pdf_fresco(url):
    """Descarga el PDF desde Google Drive evitando cualquier caché intermedia de red o servidor."""
    sep = "&" if "?" in url else "?"
    url_nocache = f"{url}{sep}_cb={int(time.time() * 1000)}"
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    return requests.get(url_nocache, headers=headers)

def render_cuadro_reporte_error(q, num_pregunta, ubicacion_key):
    """Muestra un único botón válido para enviar el reporte de error directamente a info@oposiciona.es."""
    if not usuario_puede_reportar():
        return

    nombre_pdf = st.session_state.get('test_name') or "Test sin nombre"
    usuario_rep = st.session_state.get('email') or "Alumno Oposiciona"
    preamble_txt = q.get('preamble', '').strip()
    pregunta_txt = q.get('question_text', '').strip()
    opciones_txt = "\n".join(q.get('options', []))
    correcta_txt = q['options'][q['answer']] if q.get('answer', -1) != -1 and q['answer'] < len(q.get('options', [])) else "No detectada en el PDF"
    exp_limpia = re.sub(r'^(explicaci[óo]n:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip(), flags=re.IGNORECASE).strip() or "Sin explicación."

    st.markdown(
        "<div style='background-color:#fff8e1; border:2px solid #ffb300; border-radius:8px; padding:12px; margin-top:8px; margin-bottom:8px;'>"
        f"<b style='color:#bf360c; font-size:15px;'>🛠️ Reportar error en la Pregunta {num_pregunta} a info@oposiciona.es</b><br>"
        "<span style='font-size:13px; color:#5d4037;'>Se adjuntarán automáticamente el nombre del PDF, la pregunta, las respuestas y la explicación junto con tu comentario.</span>"
        "</div>",
        unsafe_allow_html=True
    )

    motivo = st.text_area(
        "Explica brevemente el error encontrado:",
        key=f"txt_rep_{ubicacion_key}_{num_pregunta}",
        placeholder="Ejemplo: Falta un 'NO' en el enunciado, la respuesta correcta está mal marcada, o se ha cortado el texto..."
    )

    if st.button("📨 Enviar a info@oposiciona.es", key=f"btn_send_{ubicacion_key}_{num_pregunta}", type="primary", use_container_width=True):
        if not motivo.strip():
            st.warning("⚠️ Escribe brevemente en qué consiste el error antes de enviarlo.")
        else:
            payload = {
                "_subject": f"⚠️ Error en Test: {nombre_pdf} (Pregunta {num_pregunta})",
                "Usuario_que_reporta": usuario_rep,
                "Nombre_del_PDF": nombre_pdf,
                "Numero_de_Pregunta": str(num_pregunta),
                "Preambulo_Fuente": preamble_txt if preamble_txt else "N/A",
                "Explicacion_del_Error": motivo.strip(),
                "Pregunta": pregunta_txt,
                "Opciones": opciones_txt,
                "Respuesta_Correcta_Detectada": correcta_txt,
                "Explicacion_Extraida": exp_limpia,
                "_template": "table",
                "_captcha": "false"
            }

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
    return bool(re.search(re.escape(q_norm) + r'(?!\d)', n_norm)) if re.search(r'\d+\$', q_norm) else (q_norm in n_norm)

def obtener_grupo_tema(nombre_test, categoria):
    if categoria == "EXAMENES": return "🏆 Exámenes y Simulacros Oficiales"
    m = re.match(r'^TEMAS?\s*[\.\-]?\s*(\d+(?:\s*(?:a|y)\s*\d+)?)', nombre_test, re.IGNORECASE)
    if m:
        b = m.group(1).upper().strip()
        nums = re.findall(r'\d+', b)
        return f"📁 TEMA {int(nums[0]):02d}" if len(nums) == 1 else f"📁 TEMAS {b}"
    return "📁 Otros Tests"

def cargar_test_desde_url(nombre_test, url_descarga):
    st.session_state.test_name = nombre_test
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
    st.rerun()

def action_repetir_test():
    st.session_state.update(
        current_index=0,
        stats={i: {'attempts': 0, 'selected': None} for i in range(len(st.session_state.questions))},
        finished=False, checked=False, celebracion_mostrada=False, do_scroll=True
    )

def action_subir_otro():
    st.session_state.update(
        questions=[], current_index=0, stats={}, finished=False, checked=False,
        test_name=None, mostrar_opciones_simulacro=False, celebracion_mostrada=False, do_scroll=True
    )

def action_finalizar_sesion():
    st.session_state.clear()
    st.session_state.do_scroll = True


if not st.session_state.questions:
    st.markdown("<style>:root { --background-color: #FFFFFF !important; --secondary-background-color: #FFFFFF !important; } html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFFFF !important; }</style>", unsafe_allow_html=True)
    es_admin = usuario_es_admin()
    col_texto, col_img = st.columns([2.5, 1])
    with col_img:
        try: st.image("test-utiles-768x768.png", use_container_width=True)
        except: pass
    with col_texto:
        st.markdown("<h3 style='color:#2C3E50; margin-top: -10px; margin-bottom: 10px;'>📚 Comienza a practicar</h3>", unsafe_allow_html=True)
        rol = st.session_state.rol
        TESTS_DISPONIBLES = obtener_tests_segun_rol()
        st.markdown("#### 1. Especialidad")
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

        st.markdown("#### 2. Categoría")
        l_cat = list(TESTS_DISPONIBLES[especialidad].keys())
        i_cat = l_cat.index(st.session_state.saved_cat) if st.session_state.get("saved_cat") in l_cat else 0
        categoria = st.radio("Selecciona el tipo de test:", l_cat, index=i_cat, horizontal=True, key="radio_categoria", label_visibility="collapsed", on_change=cambio_categoria_o_especialidad)
        st.session_state.saved_cat = categoria

    st.markdown("#### 3. Modo de avance")
    op_av = [
        "**Modo reflexivo** (puedes comprobar la pregunta y el paso a la siguiente es manual pulsando siguiente)",
        "**Modo metralleta** (pasa a la pregunta siguiente al pulsar una opción)"
    ]
    i_av = op_av.index(st.session_state.saved_avance) if st.session_state.get("saved_avance") in op_av else 0
    modo_avance = st.radio("Modo de avance:", op_av, index=i_av, label_visibility="collapsed")
    st.session_state.saved_avance = st.session_state.modo_avance = modo_avance

    st.markdown("#### 4. Selección de Test")
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
                        et = "<span style='background:#fff3cd; color:#856404; padding:2px 6px; border-radius:4px; font-size:11px; margin-left:6px;'>REPASO</span>" if es_r else ""
                        cn, cb = st.columns([3.2, 1])
                        with cn: st.markdown(f"<div style='padding-top:6px; font-size:15px;'>{ic} <b>{tn}</b> {et}</div>", unsafe_allow_html=True)
                        with cb:
                            if st.button("🚀 Iniciar", key=f"btn_grp_{especialidad}_{categoria}_{ig}_{it}", use_container_width=True, type="primary"):
                                cargar_test_desde_url(tn, tu)

    total_deseadas = 95 if especialidad == "GESTION" else 75
    with st.container():
        st.markdown('<div class="cargar-test-container"></div><div style="background-color: #fff3cd; border: 2px dashed #ffc107; border-radius: 8px; padding: 15px 15px 5px 15px; text-align: center; margin: 15px 0 10px 0;"><h4 style="color: #856404; margin-top: 0; margin-bottom: 5px;">🔥 SIMULACRO GLOBAL EXPERTO 🔥</h4><p style="color: #856404; font-size: 14px; margin-bottom: 10px;">Genera un examen aleatorio cruzando preguntas de los distintos temas disponibles en esta especialidad.</p></div>', unsafe_allow_html=True)
        if st.button(f"🚨 INICIAR SIMULACRO ({total_deseadas} PREGUNTAS) 🚨", use_container_width=True, type="primary"):
            if rol == "INVITADO": st.error("🔒 Función no disponible para usuarios invitados. Matricúlate para acceder al Simulacro Global Experto.")
            else: st.session_state.mostrar_opciones_simulacro = True

        if rol != "INVITADO" and st.session_state.get('mostrar_opciones_simulacro', False):
            st.markdown("<div style='background-color:#eef6ff; border:2px solid #1f77b4; border-radius:8px; padding:12px; margin-top:8px; margin-bottom:10px; text-align:center;'><b style='color:#1f77b4; font-size:16px;'>🎯 ¿Sobre qué bloques quieres realizar el Simulacro?</b></div>", unsafe_allow_html=True)
            cs1, cs2, cs3 = st.columns(3)
            for col_b, lbl, amb, t_lbl in [(cs1, "🌐 TODO", "TODO", "SIMULACRO GLOBAL"), (cs2, "📘 GENERAL", "GENERAL", "SIMULACRO"), (cs3, "🎯 ESPECÍFICO", "ESPECIFICO", "SIMULACRO")]:
                if col_b.button(lbl, use_container_width=True, type="primary"):
                    st.session_state.test_name = f"{t_lbl} ({especialidad} - {amb})"
                    with st.spinner("Generando simulacro..."):
                        ex = generar_simulacro_aleatorio(especialidad, amb, total_deseadas, TESTS_DISPONIBLES)
                        if ex: procesar_preguntas(ex)
                        else: st.error("No se pudo extraer ninguna pregunta.")

    if rol != "INVITADO":
        with st.expander("Opcional: Subir un test PDF manualmente desde tu dispositivo"):
            uf = st.file_uploader("", type="pdf")
            if uf is not None:
                st.session_state.update(modo_avance=modo_avance, test_name=uf.name)
                with st.spinner("Procesando documento local..."):
                    rqs = PDFQuizParser.parse(uf.read())
                    if not rqs: st.error("No se encontraron preguntas válidas en este PDF.")
                    else: procesar_preguntas(rqs)

    if es_admin:
        with st.expander("📊 Herramienta Admin: Generar tablas con Nº exacto de preguntas"):
            st.info("Esta herramienta es visible únicamente para el administrador.")
            if st.button("Contar preguntas de todos los PDFs y crear tablas", use_container_width=True, type="primary"):
                nuevos_hoy = [
                    "EXAMEN REPASO 1 TEMA 01 a 14 GENERAL", "EXAMEN REPASO 1 TEMA 08 a 12 ESPECÍFICO",
                    "TEMA 52 - REPASO 1 - CAMPO APLICACION", "TEMA 53 - REPASO 1 - AFILIACION",
                    "TEMA 67 - REPASO 1 - COTIZACION", "TEMA 73 - REPASO 1 - REGIMES ESPECIALES INTEGRADO EN RG",
                    "TEMA 74.- REPASO 1 - RETA SETA Y MAR", "EXAMEN REPASO 1 TEMA 42 a 50 GENERAL",
                    "EXAMEN REPASO 1 TEMA 55 a 65 ESPECÍFICO", "EXAMEN REPASO TEMA 6 a 10 DERECHO MERCANTIL"
                ]
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
    st.markdown("<style>:root { --background-color: #FFFDE7 !important; --secondary-background-color: #FFFDE7 !important; } html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFDE7 !important; background-image: none !important; } .block-container, [data-testid='stMainBlockContainer'], div[data-testid='stVerticalBlock'] { background-color: transparent !important; background: transparent !important; }</style>", unsafe_allow_html=True)
    idx = st.session_state.current_index
    q, stat = st.session_state.questions[idx], st.session_state.stats[idx]
    puede_rep = usuario_puede_reportar()

    st.markdown(f"<p style='color: #7f8c8d; font-size: 14px; margin-top: -10px; margin-bottom: 5px;'>Pregunta {idx + 1} de {len(st.session_state.questions)}</p>", unsafe_allow_html=True)
    if q['preamble']: st.write(q['preamble'])
    st.markdown(f"<p style='font-size: 19px; font-weight: 600; color: #2C3E50; margin-bottom: 15px; line-height: 1.3; text-align: justify;'>{q['question_text']}</p>", unsafe_allow_html=True)

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
        et = re.sub(r'(?i)^(explicaci[óo]n:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip()).strip() or "No hay explicación disponible."
        eh = "".join([f"<div style='margin-top: 3px; line-height: 1.3;'>{p.strip()}</div>" for p in et.split('\n') if p.strip()])
        st.markdown(f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 12px; border-radius: 4px; margin-top: 10px;'><div style='font-size: 14px; font-weight: 600; margin-bottom: 3px; color: #0c5460;'>Explicación:</div><div style='font-size: 14px; color: #0c5460; text-align: justify;'>{eh}</div></div>", unsafe_allow_html=True)

    if puede_rep and st.session_state.get(key_rep_test, False):
        render_cuadro_reporte_error(q, idx + 1, "test_activo")

else:
    st.markdown("<style>:root { --background-color: #FFFFFF !important; --secondary-background-color: #FFFFFF !important; } html, body, .stApp, .main, [data-testid='stAppViewContainer'] { background-color: #FFFFFF !important; }</style>", unsafe_allow_html=True)
    components.html("<script>setTimeout(function() { if(window.parent) window.parent.scrollTo({top: 0, behavior: 'smooth'}); }, 500);</script>", height=0)

    puede_rep = usuario_puede_reportar()
    aciertos = fallos = blancos = preg_eval = 0
    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        if q['answer'] != -1:
            preg_eval += 1
            co = q['options'][q['answer']]
            if stat['selected'] == co: aciertos += 1; stat['final_status'] = "✅ Correcta"
            elif stat['selected'] is None: blancos += 1; stat['final_status'] = "⚪ En blanco"
            else: fallos += 1; stat['final_status'] = "❌ Incorrecta"
        else:
            if stat['selected'] is None: blancos += 1; stat['final_status'] = "⚪ En blanco"
            else: stat['final_status'] = "⚠️ Sin corregir (PDF sin marcar)"

    nota = (aciertos / preg_eval) * 10 if preg_eval > 0 else 0

    if nota >= 5.0:
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
        st.markdown("<div style='background: linear-gradient(90deg, #e8f5e9, #c8e6c9, #e8f5e9); border: 2px solid #2e7d32; border-radius: 10px; padding: 12px; text-align: center; margin-bottom: 15px;'><h3 style='color: #1b5e20; margin: 0; font-size: 22px;'>🎉 ¡ENHORABUENA, HAS APROBADO EL TEST! 🎉</h3><p style='color: #2e7d32; margin: 4px 0 0 0; font-size: 14px; font-weight: 600;'>¡Sigue así, estás cada vez más cerca de tu plaza!</p></div>", unsafe_allow_html=True)
        cr1, cr2, cr3 = st.columns([1, 0.4, 1])
        with cr2:
            try: st.image("test-utiles-768x768.png", use_container_width=True)
            except: pass
    else:
        cr1, cr2, cr3 = st.columns([1, 1.5, 1])
        with cr2:
            try: st.image("llorona.jpeg", use_container_width=True)
            except: pass

    st.markdown("<h3 style='text-align: center; color: #2C3E50; margin-top: -10px;'>📊 RESULTADOS FINALES</h3>", unsafe_allow_html=True)
    if st.session_state.get('test_name'):
        st.markdown(f"<h5 style='text-align: center; color: #1f77b4; margin-top: -10px; margin-bottom: 15px;'>📄 {st.session_state.test_name}</h5>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; font-size: 16px; color: #555;'>✅ Acertadas: {aciertos} &nbsp;|&nbsp; ❌ Falladas: {fallos} &nbsp;|&nbsp; ⚪ En blanco: {blancos}</h4><h3 style='text-align: center; font-size: 22px; margin-bottom: 20px;'>🎓 NOTA FINAL: {nota:.2f} / 10</h3>", unsafe_allow_html=True)

    c1_t, c2_t, c3_t = st.columns(3)
    c1_t.button("🔄 Repetir Test", key="btn_rep_top", on_click=action_repetir_test, use_container_width=True)
    c2_t.button("📁 Cambiar de Test", key="btn_sub_top", on_click=action_subir_otro, use_container_width=True)
    c3_t.button("🚪 Finalizar Sesión", key="btn_out_top", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
    st.markdown("<hr style='margin-top: 15px; margin-bottom: 15px; border: none; border-top: 1px solid #d3d3d3;'>", unsafe_allow_html=True)

    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        co = q['options'][q['answer']] if q['answer'] != -1 else "No detectada (revisa la explicación)"
        col = "green" if stat['final_status'] == "✅ Correcta" else "red" if stat['final_status'] == "❌ Incorrecta" else "#FF8C00"
        et = re.sub(r'^(explicaci[óo]n:|respuesta:|resp:|respuestas:)\s*', '', q.get('explanation', '').strip(), flags=re.IGNORECASE).strip() or "No hay explicación disponible."
        eh = "".join([f"<div style='margin-top: 3px; line-height: 1.3;'>{p.strip()}</div>" for p in et.split('\n') if p.strip()])
        ph = f"<div style='text-align: justify; line-height: 1.3; margin-bottom: 4px; font-size: 14px; color: #555;'>{q['preamble']}</div>" if q.get('preamble') else ""
        st.markdown(
            f"<div style='margin-bottom: 5px;'><div style='color: {col}; font-size: 17px; font-weight: 600; margin-bottom: 4px;'>Pregunta {i+1} | {stat['final_status']} | Intentos: {stat['attempts']}</div>"
            f"{ph}<div style='font-size:15px; text-align: justify; line-height: 1.3; margin-bottom: 2px;'><b>Pregunta:</b> {q['question_text']}</div>"
            f"<div style='font-size:15px; text-align: justify; line-height: 1.3; margin-bottom: 2px;'><b>Tu respuesta:</b> {stat['selected'] if stat['selected'] else 'Ninguna'}</div>"
            f"<div style='font-size:15px; text-align: justify; line-height: 1.3; margin-bottom: 6px;'><b>Respuesta correcta:</b> {co}</div>"
            f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 10px; border-radius: 4px; margin-bottom: 6px;'><div style='font-size: 14px; font-weight: 600; margin-bottom: 2px; color: #0c5460;'>Explicación:</div><div style='font-size: 14px; color: #0c5460; text-align: justify;'>{eh}</div></div>"
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
# --- FIN DEL ARCHIVO ---
