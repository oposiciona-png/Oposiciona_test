import streamlit as st
import streamlit.components.v1 as components  
import fitz  # PyMuPDF
import re
import random
import requests
import os

# --- CONFIGURACIÓN VISUAL DE LA PÁGINA (SIEMPRE LO PRIMERO) ---
icono_ruta = "ICONO OPOSICIONA.png"
if os.path.exists(icono_ruta):
    st.set_page_config(page_title="Plataforma de Tests Oposiciona", page_icon=icono_ruta, layout="centered")
else:
    st.set_page_config(page_title="Plataforma de Tests Oposiciona", page_icon="📚", layout="centered")


# INYECCIÓN DE CSS (Bomba nuclear contra iconos, blindaje de letras y diseño compacto)
st.markdown("""
<style>
/* --- ANIQUILAR RASTROS INTERNOS DE STREAMLIT --- */
#MainMenu, footer, header {visibility: hidden !important; display: none !important;}
[data-testid="stHeader"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}

/* --- ANIQUILAR BOTONES FLOTANTES DE STREAMLIT CLOUD (Método seguro) --- */
.stDeployButton {display: none !important;}
[data-testid="stAppDeployButton"] {display: none !important;}
[class*="viewerBadge"] {display: none !important; opacity: 0 !important; pointer-events: none !important;}
[class*="styles_viewerBadge"] {display: none !important;}

/* --- TEXTO DE LAS OPCIONES DE RESPUESTA BLINDADO CONTRA EL MODO OSCURO --- */
div[role="radiogroup"] label {margin-bottom: 12px !important;}
div[role="radiogroup"] label, 
div[role="radiogroup"] label p, 
div[role="radiogroup"] label div,
div[role="radiogroup"] label span {
    font-size: 17px !important; 
    line-height: 1.3 !important;
    text-align: justify !important;
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

/* Espaciado del contenedor principal super-compacto pero con colchón final */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 6rem !important; /* <-- COLCHÓN INVISIBLE PARA LIBRAR EL BOTÓN FLOTANTE */
    max-width: 750px !important; 
}

/* --- BOTÓN VERDE CARGAR TEST (Blindado contra Modo Oscuro) --- */
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button {
    background-color: #2e7d32 !important; /* Verde oscuro elegante */
    border-color: #2e7d32 !important;
}
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button p {
    color: #ffffff !important; /* Blanco puro garantizado */
    font-weight: 600 !important;
    font-size: 17px !important;
}
div[data-testid="stVerticalBlock"]:has(.cargar-test-container) button:hover {
    background-color: #1b5e20 !important; /* Verde más oscuro al pasar el ratón */
    border-color: #1b5e20 !important;
}

/* --- ESCUDO PASIVO ANTI-COPIA DE TEXTO --- */
body, .stApp, .block-container, p, h1, h2, h3, h4, h5, h6, span {
    -webkit-user-select: none !important;
    -moz-user-select: none !important;
    -ms-user-select: none !important;
    user-select: none !important;
}
/* Permitimos selección y escritura únicamente en los campos de usuario y contraseña */
input, textarea, [data-baseweb="input"] {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}

/* --- ESCUDO ANTI-IMPRESIÓN (Destruye el PDF si intentan imprimir) --- */
@media print {
    html, body * {
        display: none !important;
        visibility: hidden !important;
    }
    html, body {
        display: block !important;
        background-color: white !important;
    }
    body::before {
        content: "Acción no permitida.\\A Test propiedad de Oposiciona 5.0." !important;
        white-space: pre-wrap !important;
        display: block !important;
        text-align: center !important;
        font-size: 30px !important;
        font-family: sans-serif !important;
        margin-top: 20% !important;
        color: #d32f2f !important;
    }
}
</style>
""", unsafe_allow_html=True)


# --- ESCUDO ACTIVO INVISIBLE (ANTI CLICK DERECHO Y ANTI-IMPRESIÓN JS) ---
components.html(
    """
    <script>
        try {
            setTimeout(function() {
                var parentDoc = window.parent.document;
                if (!parentDoc.getElementById("escudo-oposiciona")) {
                    var script = parentDoc.createElement("script");
                    script.id = "escudo-oposiciona";
                    script.type = "text/javascript";
                    script.innerHTML = `
                        // 1. Bloquear el menú de click derecho
                        document.addEventListener('contextmenu', function(e) {
                            e.preventDefault();
                        });
                        
                        // 2. Interceptar Ctrl+C y forzar la marca de agua
                        document.addEventListener('copy', function(e) {
                            var selectedText = window.getSelection().toString();
                            if (selectedText.length > 0) {
                                var watermark = "\\n\\n-----------------------------------\\nTest propiedad de Oposiciona 5.0";
                                e.clipboardData.setData('text/plain', selectedText + watermark);
                                e.preventDefault();
                            }
                        });

                        // 3. Interceptar Ctrl+P / Cmd+P para bloquear impresión directa
                        document.addEventListener('keydown', function(e) {
                            if ((e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key === 'P')) {
                                e.preventDefault();
                                e.stopPropagation();
                            }
                        });
                    `;
                    parentDoc.head.appendChild(script);
                }
            }, 1000); 
        } catch(e) {}
    </script>
    """,
    height=0
)

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None
    st.session_state.email = None
if 'modo_avance' not in st.session_state:
    st.session_state.modo_avance = "**Modo reflexivo** (puedes comprobar la pregunta y el paso a la siguiente es manual pulsando siguiente)"
if 'do_scroll' not in st.session_state:
    st.session_state.do_scroll = False

# --- GATILLO DE AUTOSCROLL SEGURO Y CONTROLADO ---
if st.session_state.do_scroll:
    st.session_state.do_scroll = False  
    components.html(
        """
        <script>
            try {
                setTimeout(function() {
                    var parent = window.parent;
                    var doc = parent.document;
                    var els = [
                        doc.querySelector('.main'),
                        doc.querySelector('[data-testid="stMainBlockContainer"]'),
                        doc.querySelector('.block-container'),
                        doc.documentElement,
                        doc.body
                    ];
                    els.forEach(el => {
                        if (el) {
                            el.scrollTop = 0;
                        }
                    });
                    parent.scrollTo(0, 0);
                }, 150);
            } catch(e) {}
        </script>
        """,
        height=0
    )


# ==============================================================================
# 🔒 SISTEMA DE SEGURIDAD Y ACCESO POR ROLES
# ==============================================================================

USUARIOS_AUTORIZADOS = {
    "ACCESO TOTAL": [
        "ponentes@oposiciona.es",
        "gonzalogonzaleztejedor@gmail.com",
        "ignacio.garcia.heras@gmail.com",
        "alvarezpugamartin@gmail.com",
        "claratoledo06@gmail.com",
        "blancazortega@gmail.com",
        "mijurista@gmail.com",
        "isabelmgutierrogil@gmail.com",
        "carmenvl28@gmail.com",
        "leticiagenerelosolana@gmail.com",
        "invitado@oposiciona.es",
        "cguinaldobravo@gmail.com",
        "alvaro20011996@gmail.com",
        "sion.nuba@gmail.com"
    ],
    "ADMTVOS": [
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
        "vanessagarciajimenez87@gmail.com",
        "luiscacid@gmail.com",
        "raquelkmacho@gmail.com"
    ],
    "GESTION": [
        "vsaurod@gmail.com",
        "mariaquirosmonge5@gmail.com",
        "vanessagomeztdla@gmail.com",
        "zoemorcor@gmail.com",
        "julianayem@gmail.com",
        "yasminkhalili@gmail.com",
        "miriamvazquezseoane2000@gmail.com",
        "monetcacerescc@gmail.com",
        "maariiamaji@gmail.com",
        "micastroespejo@gmail.com",
        "aisacarrerapexe@gmail.com",
        "csanchezssmm@gmail.com",
        "maria.concal@gmail.com",
        "mariachinchurreta@gmail.com",
        "rocio10460@gmail.com",
        "manuelmuriel97@gmail.com",
        "hfdiaz99@gmail.com",
        "ireneizquierdo22@gmail.com",
        "manuelsan240902@gmail.com"
    ]
}

PASSWORD_ACCESO = "plaza2026" 

col1, col2, col3 = st.columns([1, 0.8, 1]) 
with col2:
    try:
        st.image("oposiciona (320 x 132 px).png", use_container_width=True)
    except:
        pass
    st.markdown("<p style='text-align: center; font-size: 12px; margin-top: -15px; margin-bottom: 0px;'><a href='https://oposiciona.es/' style='text-decoration: none; color: #1f77b4;'>🌐 oposiciona.es</a></p>", unsafe_allow_html=True)

# Línea divisoria súper compacta sin el margen gigante por defecto de Streamlit
st.markdown("<hr style='margin-top: 5px; margin-bottom: 12px; border: none; border-top: 1px solid #d3d3d3;'>", unsafe_allow_html=True)

if not st.session_state.autenticado:
    
    c_img1, c_img2, c_img3 = st.columns([1, 0.25, 1])
    with c_img2:
        try:
            st.image("test-utiles-768x768.png", use_container_width=True)
        except:
            pass
            
    st.markdown("<h3 style='text-align: center; color: #2C3E50; margin-top: -5px;'>🔒 Acceso Restringido</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; margin-bottom: 20px;'>Plataforma exclusiva de <b>Oposiciona</b>. Introduce tus credenciales para acceder.</p>", unsafe_allow_html=True)
    
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
            st.session_state.email = correo_limpio
            st.session_state.do_scroll = True
            st.rerun()
        else:
            st.error("❌ Correo o contraseña incorrectos, o no tienes autorización activa.")
    
    st.stop()


# ==============================================================================
# 🧠 MOTOR MAESTRO DE EXTRACCIÓN (BLINDAJE DE BLOQUES Y EXPLICACIONES)
# ==============================================================================

class PDFQuizParser:
    @staticmethod
    def parse(pdf_bytes):
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        questions = []
        lines = []
        stop_reading = False 
        ignoring_mode = False  
        entered_supuestos = False  
        
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
                                # Blindaje contra falsos positivos: ignorar negritas en la pura letra de la opción
                                if re.match(r'^[a-eA-E][\)\.-]?$', text):
                                    continue
                                is_bold = True
                        
                        line_text = line_text.strip()
                        
                        # --- CIRUGÍA DE CABECERAS FUSIONADAS ---
                        if line_text:
                            prefixes_to_strip = [
                                r'^OPOSICIONA\s*',
                                r'^GESTI[OÓ]N DE LA SEGURIDAD SOCIAL\s*',
                                r'^ADMINISTRATIVO DE LA SEGURIDAD SOCIAL\s*',
                                r'^(?:GENERAL\s+|ESPEC[IÍ]FICO\s+|EXAMEN\s+|TEST\s+|RESPUESTAS\s+)?TEMAS?\s+\d+[a-zA-Z]?\s*[\-–:]\s*[A-ZÁÉÍÓÚÑ0-9\s\-–:,\.\(\)\/]+\b\.?\s*',
                                r'^ESPECIAL\s+SIMULACROS?\s+\d+\s*[\-–]\s*\d+\s+[A-ZÁÉÍÓÚÑ0-9\s\-–:,\.\(\)\/]+\s*',
                                r'^TEST\s+ADMINISTRATIVO\s+\d+\s+TODO\s+EL\s+TEMARIO\s*',
                                r'^RESPUESTAS\s+(?:TIPO\s+)?TEST:?\s+TEMAS?\s+\d+\s+[A-ZÁÉÍÓÚÑ0-9\s\-–:,\.\(\)\/]+\b\.?\s*',
                                r'^EXAMEN\s+[A-ZÁÉÍÓÚÑ0-9\s]+\s*202\d\s*'
                            ]
                            for pat in prefixes_to_strip:
                                m = re.match(pat, line_text, flags=re.IGNORECASE)
                                if m and m.group(0).isupper():
                                    line_text = line_text[m.end():].strip()
                        
                        if not line_text:
                            continue
                            
                        if line_text:
                            tl = line_text.lower()
                            
                            tl_norm = tl.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ä", "a")
                            tl_norm = tl_norm.replace("τ", "t").replace("ε", "e").replace("μ", "m").replace("α", "a") 
                            tl_clean = re.sub(r'[^a-z0-9\s]', '', tl_norm).strip()
                            tl_clean_spaces = re.sub(r'\s+', ' ', tl_clean) 
                            
                            # --- INTERRUPTOR CORTAFUEGOS ---
                            if "plantilla de respuesta" in tl_clean_spaces or "plantillas de respuesta" in tl_clean_spaces:
                                stop_reading = True
                                break
                            
                            # --- CORTAFUEGOS CASOS PRÁCTICOS ---
                            if (
                                "supuesto practico" in tl_clean_spaces or 
                                "supuestos practicos" in tl_clean_spaces or 
                                "pregunta de desarrollo" in tl_clean_spaces or 
                                "preguntas de desarrollo" in tl_clean_spaces or
                                "casos practicos" in tl_clean_spaces or
                                "caso practico" in tl_clean_spaces
                            ):
                                if line_text.isupper() or len(tl_clean_spaces) < 45:
                                    ignoring_mode = True
                                    entered_supuestos = True  
                            
                            if "preguntas de reserva" in tl_clean_spaces or "pregunta de reserva" in tl_clean_spaces or tl_clean_spaces == "reserva":
                                if not entered_supuestos:
                                    ignoring_mode = False
                                
                            if not ignoring_mode and len(questions) > 0:
                                current_q = questions[-1] if len(questions) > 0 else None
                                if current_q and current_q.get("state") == "E":
                                    implicit_case_patterns = [
                                        r'^(La mercantil|La empresa)\s+["\'«][A-ZÁÉÍÓÚÑ]',
                                        r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+y\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+son\s+',
                                        r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+de\s+\d+\s+y\s+\d+\s+años',
                                        r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+de\s+\d+\s+años,\s+',
                                        r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+forma\s+una\s+familia',
                                        r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+cumple\s+\d+\s+años\s+el',
                                        r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+nacid[ao]\s+el\s+\d+',
                                        r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+camarer[ao]\s+desde',
                                        r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+trabaja\s+en\s+la\s+empresa'
                                    ]
                                    for pat in implicit_case_patterns:
                                        if re.match(pat, line_text):
                                            ignoring_mode = True
                                            entered_supuestos = True  
                                            break
                            
                            if ignoring_mode:
                                continue
                            
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
                                    r'^(general|especifico|examen|test|respuestas|respuestas\s+(tipo\s+)?test:?|test\s+profesor)\s+temas?\s+\d+', 
                                    r'^examen\s+repaso',
                                    r'^examen\s+[a-záéíóúñ0-9\s]+\s*202\d',
                                    r'^normas\s+para\s+la\s+realizacion',
                                    r'^especial\s+simulacros?',
                                    r'^test\s+administrativo\s+\d+\s+todo\s+el\s+temario',
                                    r'^respuestas\s+tipo\s+test:\s+temas?\s+\d+' 
                                ]
                                for pat in header_patterns:
                                    if re.search(pat, tl_clean_spaces):
                                        is_header = True
                                        break
                            
                            if is_header: continue
                            
                            # --- BISTURÍ TOTAL (PREGUNTAS, OPCIONES Y EXPLICACIONES PEGADAS) ---
                            line_text = re.sub(r'(?<=[.?!;\)\]"\'”])\s*(Explicaci[óo]n:|Respuest[as]?:|Resp:)\s', r'\n\1 ', line_text, flags=re.IGNORECASE)
                            line_text = re.sub(r'(?<=\S)\s{2,}(Explicaci[óo]n:|Respuest[as]?:|Resp:)\s', r'\n\1 ', line_text, flags=re.IGNORECASE)
                            
                            line_text = re.sub(r'(?<=\S)\s*(OJO|NOTA|IMPORTANTE|RECUERDA):', r'\n\1:', line_text, flags=re.IGNORECASE)
                            
                            line_text = re.sub(r'(?<=[.?!;”"\'\)])\s*(Art[íi]culo aplicable:|Art[íi]culo|Art\.)\s', r'\n\1 ', line_text, flags=re.IGNORECASE)
                            line_text = re.sub(r'(?<=\S)\s+([•\*])(\s|$)', r'\n\1\2', line_text)
                            
                            line_text = re.sub(r'(?<=[a-zA-ZáéíóúñÁÉÍÓÚÑ\)])(\d{1,3}[\.\-\)])\s+(?=[A-ZÁÉÍÓÚÑ¿¡"\'«])', r'\n\1 ', line_text)
                            
                            line_text = re.sub(r'([.?!;])\s+([a-eA-E][\)\.\-])\s*(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])', r'\1\n\2 ', line_text)
                            line_text = re.sub(r'(?<!\d)([.?!;])([a-eA-E][\)\.\-])\s*(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])', r'\1\n\2 ', line_text)
                            line_text = re.sub(r'(?<=[a-zA-ZáéíóúñÁÉÍÓÚÑ])\s+([a-eA-E][\)\.\-])\s*(?=[A-ZÁÉÍÓÚÑ0-9¿¡"\'«])', r'\n\1 ', line_text)
                            
                            parts = line_text.split('\n')
                            for part in parts:
                                part = part.strip()
                                if part:
                                    part = re.sub(r'^([a-fA-F][\)\.-])(?=[^\s])', r'\1 ', part)
                                    lines.append({"text": part, "bold": is_bold})
                                    
                    # --- MARCADOR DE BLOQUES PARA RESPETAR LOS INTROS ORIGINALES DE LAS EXPLICACIONES ---
                    lines.append({"text": "<NEW_BLOCK>", "bold": False})
                            
        current_q = None
        preamble = "" 
        expected_q_num = 1  
        
        for idx, line in enumerate(lines):
            text = line["text"]
            is_bold = line["bold"]
            
            # --- PROCESADOR DE BLOQUES ---
            if text == "<NEW_BLOCK>":
                if current_q and current_q["state"] == "E":
                    if current_q["explanation"]:
                        # Solo añade salto de bloque si terminó en puntuación para EVITAR FRASES ROTAS
                        if current_q["explanation"].strip()[-1:] in ['.', ':', '?', '!', '"', '”', '»']:
                            if not current_q["explanation"].endswith("\n\n"):
                                current_q["explanation"] = current_q["explanation"].rstrip() + "\n\n"
                continue

            text_lower = text.lower()
            is_option = bool(re.match(r'^[a-zA-Z][\)\.\-]\s*', text))
            
            if current_q and current_q["state"] == "E":
                is_explanation = False
            else:
                is_explanation = text_lower.startswith("explicaci") or text_lower.startswith("resp:") or text_lower.startswith("respuesta:") or text_lower.startswith("respuestas:")
            
            forced_not_option = False
            if is_option and current_q and current_q["state"] == "Q" and len(current_q["options"]) == 0:
                if text.strip().endswith('?') and not re.match(r'^[a-zA-Z][\)\.\-]\s*[¿A-ZÁÉÍÓÚÑ]', text):
                    is_option = False
                    forced_not_option = True

            is_reserve = bool(re.search(r'\bpreguntas?\s+de\s+reserva\b', text_lower)) or bool(re.match(r'^\s*reserva\b', text_lower))
            is_case_study = bool(re.match(r'^\s*(supuestos?\s+pr[áa]cticos?)', text_lower))
            
            is_letter_block = bool(re.match(r'^[A-ZÑ][\)\.-]+\s*[A-ZÁÉÍÓÚÑ]', text))
            if is_letter_block and re.search(r'\b(fals[ao]|verdader[ao]|correct[ao]|incorrect[ao])\b', text_lower):
                is_letter_block = False

            if (is_reserve or is_case_study or is_letter_block) and (not current_q or current_q["state"] == "E"):
                is_real_preamble = False
                for j in range(idx + 1, min(idx + 30, len(lines))):
                    fut = lines[j]["text"].strip()
                    if (re.match(r'^\s*(\d+)[,\.\-\)]+(?!\d)', fut) or 
                        re.match(r'^\s*(\d+)\s+[,\.\-\)]', fut) or 
                        (re.match(r'^\s*(¿|C[óo]mo|Cu[áa]l|Cu[áa]ntos|Qu[ée])\b', fut, re.IGNORECASE) and fut.endswith('?'))):
                        is_real_preamble = True
                        break
                
                if is_real_preamble or is_reserve or is_case_study:
                    if current_q and current_q["options"]: 
                        questions.append(current_q)
                    current_q = None 
                    
                    preamble += text + "\n"
                        
                    expected_q_num = 1 
                    continue

            is_new_q = False
            
            m_num = (re.match(r'^\s*(\d+)[,\.\-\)]+(?!\d)', text) or 
                     re.match(r'^\s*(\d+)\s+[,\.\-\)]', text) or
                     re.match(r'^\s*(\d+)\s*¿', text))
                     
            m_rescue = False
            
            if not m_num and not is_option and not is_explanation:
                text_clean = text.strip()
                if (current_q and current_q["state"] in ["E", "O"]) or not current_q:
                    if re.match(r'^\s*(¿|C[óo]mo|Cu[áa]l|Cu[áa]ntos|Qu[ée])\b', text_clean, re.IGNORECASE) and text_clean.endswith('?'):
                        m_rescue = True

            if m_num or m_rescue:
                is_real_q_candidate = False
                for j in range(idx + 1, min(idx + 25, len(lines))):
                    future_text = lines[j]["text"].strip()
                    if re.match(r'^[a-eA-E][\)\.]\s', future_text):
                        is_real_q_candidate = True
                        break
                    
                    m_future_num = (re.match(r'^\s*(\d+)[,\.\-\)]+(?!\d)', future_text) or 
                                    re.match(r'^\s*(\d+)\s+[,\.\-\)]', future_text) or
                                    re.match(r'^\s*(\d+)\s*¿', future_text))
                    
                    if m_future_num:
                        break
                
                if is_real_q_candidate:
                    if m_num:
                        num = int(m_num.group(1))
                        if current_q is None:
                            is_new_q = True
                            expected_q_num = num + 1
                        elif expected_q_num - 2 <= num <= expected_q_num + 15:
                            is_new_q = True
                            expected_q_num = num + 1
                    elif m_rescue:
                        is_new_q = True
                        expected_q_num += 1

            if is_new_q:
                if current_q and current_q["options"]: questions.append(current_q)
                clean_text = re.sub(r'^\s*\d+[,\.\-\)]+\s*(-*\s*)?', '', text)
                clean_text = re.sub(r'^\s*\d+\s*¿', '¿', clean_text)
                current_q = {"preamble": preamble.strip(), "question_text": clean_text, "options": [], "answer": -1, "explanation": "", "state": "Q"}
                preamble = "" 
                continue
                
            if not current_q:
                if not is_reserve:
                    preamble += text + "\n"
                continue
            
            if is_option and current_q:
                match_opt = re.match(r'^([a-zA-Z])[\)\.-]\s*', text)
                if match_opt:
                    letter = match_opt.group(1).lower()
                    expected_letter = chr(97 + len(current_q["options"]))
                    
                    if current_q["state"] in ["Q", "O"] or (current_q["state"] == "E" and letter == expected_letter):
                        current_q["options"].append(text)
                        current_q["state"] = "O"
                        if is_bold and current_q["answer"] == -1: 
                            current_q["answer"] = len(current_q["options"]) - 1
                        continue
                
            if is_explanation:
                if current_q:
                    if current_q["explanation"]:
                        current_q["explanation"] = current_q["explanation"].rstrip() + "\n\n" + text
                    else:
                        current_q["explanation"] = text
                    current_q["state"] = "E"
                continue
                
            if current_q["state"] == "Q":
                if forced_not_option and re.search(r'[a-zA-Z]$', current_q["question_text"].strip()):
                    match = re.match(r'^([a-zA-Z])([\)\.\-])\s*(.*)', text)
                    if match:
                        current_q["question_text"] = current_q["question_text"].strip() + match.group(1) + match.group(2) + " " + match.group(3)
                    else:
                        current_q["question_text"] += " " + text
                else:
                    current_q["question_text"] += " " + text
                
            elif current_q["state"] == "O":
                last_opt = current_q["options"][-1].strip()
                ended_with_punct = bool(re.search(r'[\.;\?]$', last_opt))
                ended_with_connector = bool(re.search(r'(,| y| o| que| de| a| con| en| por| para| el| la| los| las| un| una)$', last_opt, re.IGNORECASE))
                
                is_new_paragraph = len(current_q["options"]) >= 2 and ended_with_punct and bool(re.match(r'^[A-Z0-9¿¡"\'«]', text))
                
                is_legal_ref = bool(re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|seg[úu]n)\b', text_lower))
                
                is_implicit_explanation = False
                if len(current_q["options"]) >= 3 and bool(re.match(r'^[A-ZÁÉÍÓÚ¿¡"\'«]', text)):
                    if re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|seg[úu]n|normativa|de conformidad|conforme|en virtud)\b', text_lower):
                        is_implicit_explanation = True
                    elif re.match(r'^(el\b|la\b|los\b|las\b|para\b|de\b|en\b|cuando\b|se\b|es\b|esta\b|este\b|al\b|por\b|si\b)', text_lower):
                        if ended_with_punct or not ended_with_connector:
                            is_implicit_explanation = True

                if len(current_q["options"]) < 2 or ended_with_connector or len(last_opt) <= 5:
                    is_new_paragraph = False
                    is_legal_ref = False
                    is_implicit_explanation = False

                if is_new_paragraph or is_legal_ref or is_implicit_explanation:
                    current_q["state"] = "E"
                    current_q["explanation"] = text
                else:
                    if is_bold and current_q["answer"] == -1: current_q["answer"] = len(current_q["options"]) - 1
                    current_q["options"][-1] += " " + text
                    
            elif current_q["state"] == "E":
                if current_q["explanation"].endswith("\n\n"):
                    current_q["explanation"] += text
                else:
                    last_char = current_q["explanation"].strip()[-1:] if current_q["explanation"].strip() else ""
                    
                    is_bullet = bool(re.match(r'^[\s]*[•\*]', text))
                    is_ojo = bool(re.match(r'^[\s]*(OJO|NOTA|IMPORTANTE|RECUERDA)[\s:]', text, re.IGNORECASE))
                    starts_with_upper_or_num = bool(re.match(r'^[\s]*([A-ZÁÉÍÓÚ¿¡"\'«]|\d)', text))
                    is_new_sentence = (last_char in ['.', ':', '?', '!', '"', '”', '»'] and starts_with_upper_or_num)
                    
                    if current_q["explanation"].strip().endswith(('-', '•', '*', '', '')) and not is_bullet:
                        current_q["explanation"] += " " + text
                    elif is_bullet or is_ojo or is_new_sentence:
                        current_q["explanation"] = current_q["explanation"].rstrip() + "\n\n" + text
                    else:
                        current_q["explanation"] += " " + text if current_q["explanation"] else text

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
            "TEMA 10": "https://drive.google.com/uc?export=download&id=1iLabrwSF9Phm2Qvcazdds4F6nTAHajjo",
            "TEMA 2A": "https://drive.google.com/uc?export=download&id=1W_f3M0AytaH9K4tI5Puuwn3zDCGTpGEm",
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
            "EXAMEN OFICIAL 2023 ACTUALIZADO A 2026": "https://drive.google.com/uc?export=download&id=1zWrxEUexvs5IVFa3WSM96ezQ12-6NegN",
            "EXAMEN OFICIAL 2026 B ROJO": "https://drive.google.com/uc?export=download&id=1fmh5zACnL7mPA29bxdAhhJqqm5cagv5L",
            "EXAMEN REPASO TEMA 2 COMPLETO": "https://drive.google.com/uc?export=download&id=1K60xc80vJAhbGKNs_2_UhooQ0ovSSUC2",
            "SABADO 5 SEP 2026": "https://drive.google.com/uc?export=download&id=1XGMVM7M0kRrNGyZYa3N-npLO7pYETxVa",
        },
        "GENERAL": {
            "Elige un test de general...": None,
            "Tema 08 ADM GRAL ESTADO": "https://drive.google.com/uc?export=download&id=1sjO0bi2IwPJpPcESpQkWvqROPAHJ12L6",
            "TEMA 1 a 3 CONSTITUCIONAL": "https://drive.google.com/uc?export=download&id=14z3ZzvLLVZQ0XiUKx4qmiyneMoldZIB2",
            "TEMA 4 LA JEFATURA DEL ESTADO": "https://drive.google.com/uc?export=download&id=1y-u-_wTqfIyB_fn0he0cvyKAPLjsM06A",
            "TEMA 5 y 6 PODER LEGISLATIVO Y JUDICIAL": "https://drive.google.com/uc?export=download&id=1Hog53fH7CsG1FCk6CC0X4m4tIXZ2tPYd",
            "TEMA 7 PODER EJECUTIVO": "https://drive.google.com/uc?export=download&id=1BXKLo950u1GSODuag-lds2SCbBTYF2UD",
            "TEMA 8 AGE": "https://drive.google.com/uc?export=download&id=1ePiNyJ97TS68SUHDbHQVMmNdycyk6Olo",
            "TEMA 9 CCAA Y MUNICIPIOS": "https://drive.google.com/uc?export=download&id=1Po-Aw8DKSWwBEypwNCk6PfkPe19ZJb2i",
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
            "TEMA 59 y 60 IP y LESIONES PERMANENTES": "https://drive.google.com/uc?export=download&id=12_N6QFcTShR-w-yX9ptJD9pbfC_CQuUD",
            "Tema 67 COTIZACION": "https://drive.google.com/uc?export=download&id=1kErdym1yxTP-Qd0Frx-5XIwOkI3aq5aL",
            "TEMA 73 - LOS REGIMENES ESPECIALES DE LA S SOCIAL": "https://drive.google.com/uc?export=download&id=16JKTt0G8UycnAsclRtoHC1mGkgDtvHI0",
            "TEMA 74 - RETA, SETA  Y MAR": "https://drive.google.com/uc?export=download&id=1N2ezL7ohgKxcoZVPex_oGday9JHMMxl7",
            "TEMA 75 - MINERIA - SEGURO ESCOLAR FUNCIONARIOS": "https://drive.google.com/uc?export=download&id=1eHZ9Ajqujk-wtnzcsAo_e6lpkH9kfrao",
        },
        "EXAMENES": {
            "Elige un test de examenes...": None,
            "DOMINGO 6 SEP 2026": "https://drive.google.com/uc?export=download&id=1pEuW36jClxKZQjwAuSx6TpfFaxlmkcln",
            "Examen oficial 17 de mayo de 2026": "https://drive.google.com/uc?export=download&id=1-ZFGIZGsixCwIS5Tr_4dZ5hX8mcX4yDL",
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
            "Tema 48 - Extinción del Contrato": "https://drive.google.com/uc?export=download&id=1mbE4W0EnqJa9IosTYk2iEHbs2aBQOFdH",
            "TEMAS 49 y 50 DESPIDO Y HUELGA": "https://drive.google.com/uc?export=download&id=1FFt9QtwAeTz-U0VvCZQMaf15xS4s33bd",
        },
    },
}

if 'questions' not in st.session_state:
    st.session_state.questions = []
    st.session_state.current_index = 0
    st.session_state.stats = {}
    st.session_state.finished = False
    st.session_state.checked = False
    st.session_state.test_name = None

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
    
    save_answer(selected)
    
    if "metralleta" in st.session_state.modo_avance.lower() and selected:
        if idx < len(st.session_state.questions) - 1:
            st.session_state.current_index += 1
            st.session_state.checked = False
            st.session_state.do_scroll = True
        else:
            st.session_state.finished = True
            st.session_state.do_scroll = True

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
    st.session_state.do_scroll = True
    st.rerun()

def action_repetir_test():
    st.session_state.current_index = 0
    st.session_state.stats = {i: {'attempts': 0, 'selected': None} for i in range(len(st.session_state.questions))}
    st.session_state.finished = False
    st.session_state.checked = False
    st.session_state.do_scroll = True

def action_subir_otro():
    st.session_state.questions = []
    st.session_state.current_index = 0
    st.session_state.stats = {}
    st.session_state.finished = False
    st.session_state.checked = False
    st.session_state.test_name = None
    st.session_state.do_scroll = True

def action_finalizar_sesion():
    st.session_state.clear()
    st.session_state.do_scroll = True


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
        st.markdown("<h3 style='color:#2C3E50; margin-top: -10px; margin-bottom: 10px;'>📚 Comienza a practicar</h3>", unsafe_allow_html=True)
        
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
        
        total_deseadas = 95 if especialidad == "GESTION" else 75
        
        with st.container():
            st.markdown('<div class="cargar-test-container"></div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background-color: #fff3cd; border: 2px dashed #ffc107; border-radius: 8px; padding: 15px 15px 5px 15px; text-align: center; margin: 15px 0 10px 0;">
                <h4 style="color: #856404; margin-top: 0; margin-bottom: 5px;">🔥 SIMULACRO GLOBAL EXPERTO 🔥</h4>
                <p style="color: #856404; font-size: 14px; margin-bottom: 10px;">Genera un examen aleatorio y equilibrado cruzando preguntas de <b>todos los bloques y temas</b> disponibles en esta especialidad.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🚨 INICIAR SIMULACRO ({total_deseadas} PREGUNTAS) 🚨", use_container_width=True, type="primary"):
                st.session_state.test_name = None
                with st.spinner(f"Extrayendo y mezclando preguntas de TODOS los PDFs de {especialidad} (puede tardar un minuto)..."):
                    preguntas_por_pdf = []
                    for cat, tests in TESTS_DISPONIBLES[especialidad].items():
                        for test_name, url in tests.items():
                            if url is None: continue
                            try:
                                resp = requests.get(url)
                                if resp.status_code == 200:
                                    qs = PDFQuizParser.parse(resp.content)
                                    if qs:
                                        for q in qs:
                                            fuente = f"🏷️ **Fuente: {cat} - {test_name}**"
                                            if q["preamble"]:
                                                q["preamble"] = fuente + "\n\n" + q["preamble"]
                                            else:
                                                q["preamble"] = fuente
                                        preguntas_por_pdf.append(qs)
                            except Exception as e:
                                pass
                    
                    if not preguntas_por_pdf:
                        st.error("No se pudo extraer ninguna pregunta.")
                    else:
                        num_pdfs = len(preguntas_por_pdf)
                        cuotas = [0] * num_pdfs
                        
                        for _ in range(total_deseadas):
                            disponibles = [i for i in range(num_pdfs) if len(preguntas_por_pdf[i]) > cuotas[i]]
                            if not disponibles:
                                break
                            min_cuota = min(cuotas[i] for i in disponibles)
                            candidatos_min = [i for i in disponibles if cuotas[i] == min_cuota]
                            idx = random.choice(candidatos_min)
                            cuotas[idx] += 1
                            
                        examen_total = []
                        for i in range(num_pdfs):
                            if cuotas[i] > 0:
                                seleccionadas = random.sample(preguntas_por_pdf[i], cuotas[i])
                                examen_total.extend(seleccionadas)
                        
                        random.shuffle(examen_total)
                        procesar_preguntas(examen_total)

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
    
    if opcion_seleccionada and not opcion_seleccionada.startswith("Elige"):
        with st.container():
            st.markdown('<div class="cargar-test-container"></div>', unsafe_allow_html=True)
            if st.button(f"🚀 Cargar Test Seleccionado", use_container_width=True):
                st.session_state.test_name = opcion_seleccionada
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
    
    with st.expander("Opcional: Subir un test PDF manualmente desde tu dispositivo"):
        uploaded_file = st.file_uploader("", type="pdf")
        if uploaded_file is not None:
            st.session_state.modo_avance = modo_avance
            st.session_state.test_name = uploaded_file.name
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
    
    idx = st.session_state.current_index
    q = st.session_state.questions[idx]
    stat = st.session_state.stats[idx]
    
    st.markdown(f"<p style='color: #7f8c8d; font-size: 14px; margin-top: -10px; margin-bottom: 5px;'>Pregunta {idx + 1} de {len(st.session_state.questions)}</p>", unsafe_allow_html=True)
    
    if q['preamble']:
        st.write(q['preamble'])
        
    st.markdown(f"<p style='font-size: 19px; font-weight: 600; color: #2C3E50; margin-bottom: 15px; line-height: 1.3; text-align: justify;'>{q['question_text']}</p>", unsafe_allow_html=True)
    
    default_idx = q['options'].index(stat['selected']) if stat['selected'] in q['options'] else None
    
    selected_option = st.radio("Elige tu respuesta:", q['options'], index=default_idx, key=f"radio_{idx}", label_visibility="collapsed", on_change=handle_radio_change)
    
    col1, col2, col3, col4 = st.columns(4)
    
    if col1.button("🡄 Anterior", use_container_width=True) and idx > 0:
        save_answer(selected_option)
        st.session_state.checked = False
        st.session_state.current_index -= 1
        st.session_state.do_scroll = True
        st.rerun()
        
    if col2.button("Comprobar", use_container_width=True):
        save_answer(selected_option)
        st.session_state.checked = True
        st.session_state.do_scroll = True
        st.rerun()
        
    if idx < len(st.session_state.questions) - 1:
        if col3.button("Siguiente ➔", use_container_width=True):
            save_answer(selected_option)
            st.session_state.checked = False
            st.session_state.current_index += 1
            st.session_state.do_scroll = True
            st.rerun()
    else:
        if col3.button("Terminar ➔", use_container_width=True):
            save_answer(selected_option)
            st.session_state.finished = True
            st.session_state.do_scroll = True
            st.rerun()
            
    if col4.button("⏹ Finalizar Test", use_container_width=True):
        save_answer(selected_option)
        st.session_state.finished = True
        st.session_state.do_scroll = True
        st.rerun()

    if st.session_state.checked:
        if q['answer'] != -1:
            correct_opt = q['options'][q['answer']]
            if selected_option == correct_opt:
                st.success("✅ ¡CORRECTO!")
            elif not selected_option:
                st.warning(f"⚪ EN BLANCO. La correcta era: {correct_opt}")
            else:
                st.error(f"❌ INCORRECTO. La respuesta correcta era: {correct_opt}")
        else:
            if not selected_option:
                st.warning("⚪ EN BLANCO. La correcta no se detectó automáticamente en el PDF.")
            else:
                st.info("⚠️ Tu respuesta ha sido guardada. (La opción correcta no estaba remarcada en el PDF original, revisa la explicación).")
            
        exp_text = q.get('explanation', '').strip()
        exp_text = re.sub(r'(?i)^(explicaci[óo]n:|respuesta:|resp:|respuestas:)\s*', '', exp_text).strip()
        if not exp_text:
            exp_text = "No hay explicación disponible."
            
        exp_html = "".join([f"<div style='margin-top: 3px; line-height: 1.3;'>{p.strip()}</div>" for p in exp_text.split('\n') if p.strip()])
        
        st.markdown(
            f"<div style='background-color: #e8f4f8; border-left: 4px solid #17a2b8; padding: 12px; border-radius: 4px; margin-top: 10px;'>"
            f"<div style='font-size: 14px; font-weight: 600; margin-bottom: 3px; color: #0c5460;'>Explicación:</div>"
            f"<div style='font-size: 14px; color: #0c5460; text-align: justify;'>{exp_html}</div>"
            f"</div>", 
            unsafe_allow_html=True
        )

else:
    # --- RESULTADOS FINALES ---
    
    st.markdown("""
    <style>
    :root { --background-color: #FFFFFF !important; --secondary-background-color: #FFFFFF !important; }
    html, body, .stApp, .main, [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

    aciertos = 0
    fallos = 0
    blancos = 0
    preguntas_evaluables = 0
    
    for i, q in enumerate(st.session_state.questions):
        stat = st.session_state.stats[i]
        
        if q['answer'] != -1:
            preguntas_evaluables += 1
            correct_opt = q['options'][q['answer']]
            if stat['selected'] == correct_opt:
                aciertos += 1
                stat['final_status'] = "✅ Correcta"
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
            
    nota = (aciertos / preguntas_evaluables) * 10 if preguntas_evaluables > 0 else 0
    
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
    
    st.markdown("<h3 style='text-align: center; color: #2C3E50; margin-top: -10px;'>📊 RESULTADOS FINALES</h3>", unsafe_allow_html=True)
    if st.session_state.get('test_name'):
        st.markdown(f"<h5 style='text-align: center; color: #1f77b4; margin-top: -10px; margin-bottom: 15px;'>📄 {st.session_state.test_name}</h5>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; font-size: 16px; color: #555;'>✅ Acertadas: {aciertos} &nbsp;|&nbsp; ❌ Falladas: {fallos} &nbsp;|&nbsp; ⚪ En blanco: {blancos}</h4>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; font-size: 22px; margin-bottom: 20px;'>🎓 NOTA FINAL: {nota:.2f} / 10</h3>", unsafe_allow_html=True)
    
    c1_top, c2_top, c3_top = st.columns(3)
    c1_top.button("🔄 Repetir Test", key="btn_rep_top", on_click=action_repetir_test, use_container_width=True)
    c2_top.button("📁 Cambiar de Test", key="btn_sub_top", on_click=action_subir_otro, use_container_width=True)
    c3_top.button("🚪 Finalizar Sesión", key="btn_out_top", on_click=action_finalizar_sesion, use_container_width=True, type="primary")
