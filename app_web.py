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
                    parent.scrollTo({top: 0, behavior: 'smooth'});
                }, 200);
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
        "mfangela23@gmail.com",
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
                                if re.match(r'^[a-eA-E][\)\.-]?\$', text):
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
                                        r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\_nacid[ao]\s+el\s+\d+',
                                        r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\_camarer[ao]\s+desde',
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
                                
                            # NO descartar la referencia de la página/tema entre paréntesis
                            is_page_ref = bool(re.match(r'^\(p[aá]gina\s+\d+.*?\)\$', tl_clean_spaces, re.IGNORECASE))
                            
                            if not is_header and not is_page_ref and len(tl_clean_spaces) < 120:
                                header_patterns = [
                                    r'^oposiciona\$',
                                    r'oposicionaes',
                                    r'^pagina\s+\d+\s+de\s+\d+\$', # Solo borra "Página X de Y" sueltos
                                    r'^(administrativo|gestion)\s+de\s+la\s+seguridad\s+social',
                                    r'^(administrativo|gestion)\s+202\d\s+tema\s+\d+[a-z]?',
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
                            line_text = re.sub(r'(?<=\S)\s+([•\*])(\s|\$)', r'\n\1\2', line_text)
                            
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

        # --- PARCHE QUIRÚRGICO DE EXCEPCIONES DE FORMATO PARA TESTS ESPECÍFICOS ---
        for i in range(len(lines)):
            txt = lines[i]["text"].strip()
            
            # Arreglo para el test TEMA 59 y 60 (carencia cortada y viñeta fantasma)
            if txt.endswith("carenci") and i+1 < len(lines) and lines[i+1]["text"].strip().startswith("a) se exige"):
                lines[i]["text"] = lines[i]["text"].replace("carenci", "carencia)")
                lines[i+1]["text"] = lines[i+1]["text"].replace("a) se exige", "se exige", 1)
            
            # Arreglo para el test TEMA 2A (D. Carlos confundido con opción D)
            if txt.startswith("D. Carlos"):
                lines[i]["text"] = lines[i]["text"].replace("D. Carlos", "Don Carlos", 1)
                            
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
                        if current_q["explanation"].strip()[-1:] in ['.', ':', '?', '!', '"', '”', '»', ')']:
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
                    if (re.match(r'^\s*(?:Pregunta\s+)?(\d+)[,\.\-\)]+(?!\d)', fut, re.IGNORECASE) or 
                        re.match(r'^\s*(?:Pregunta\s+)?(\d+)\s+[,\.\-\)]', fut, re.IGNORECASE) or 
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
            
            # BLINDAJE PARA TESTS QUE USAN "Pregunta X." EN LUGAR DE "X."
            m_num = (re.match(r'^\s*(?:Pregunta\s+)?(\d+)[,\.\-\)]+(?!\d)', text, re.IGNORECASE) or 
                     re.match(r'^\s*(?:Pregunta\s+)?(\d+)\s+[,\.\-\)]', text
