# ==============================================================================
# >>> INICIO DE LA SECCIÓN 1 DE 5: IMPORTACIONES, CONFIGURACIÓN Y SESSION STATE
# ==============================================================================
import streamlit as st
import pandas as pd
import requests
import io
import PyPDF2

st.set_page_config(
    page_title="Plataforma de Oposiciones - Tests y Desarrollo",
    page_icon="📚",
    layout="wide"
)

# Inicialización de variables en session_state para mantener el progreso del alumno
if "respuestas_usuario" not in st.session_state:
    st.session_state.respuestas_usuario = {}
if "test_corregido" not in st.session_state:
    st.session_state.test_corregido = False
if "ultimo_item_cargado" not in st.session_state:
    st.session_state.ultimo_item_cargado = None
if "desarrollo_evaluado" not in st.session_state:
    st.session_state.desarrollo_evaluado = False
# ==============================================================================
# <<< FIN DE LA SECCIÓN 1 DE 5 (No falta nada en esta sección)
# ==============================================================================

# ==============================================================================
# >>> INICIO DE LA SECCIÓN 2 DE 5: DICCIONARIO DE DATOS (TESTS_DISPONIBLES)
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
            "Elige un tema de desarrollo...": None,
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
# <<< FIN DE LA SECCIÓN 2 DE 5 (No falta nada en esta sección)
# ==============================================================================

# ==============================================================================
# >>> INICIO DE LA SECCIÓN 3 DE 5: FUNCIONES DE DESCARGA, LECTURA PDF Y EVALUACIÓN
# ==============================================================================
@st.cache_data(show_spinner="Descargando y extrayendo PDF desde Drive...")
def descargar_pdf_drive(url):
    """Descarga el PDF de desarrollo desde Drive y extrae su texto por páginas."""
    respuesta = requests.get(url)
    respuesta.raise_for_status()
    pdf_bytes = io.BytesIO(respuesta.content)
    
    lector = PyPDF2.PdfReader(pdf_bytes)
    texto_completo = ""
    for num_pag, pagina in enumerate(lector.pages, start=1):
        texto_pag = pagina.extract_text()
        if texto_pag:
            texto_completo += f"--- PÁGINA {num_pag} ---\n{texto_pag}\n\n"
            
    return texto_completo, respuesta.content


@st.cache_data(show_spinner="Cargando preguntas del test desde Drive...")
def cargar_test_drive(url):
    """Descarga el archivo de preguntas (Excel o CSV) desde Google Drive."""
    respuesta = requests.get(url)
    respuesta.raise_for_status()
    contenido = io.BytesIO(respuesta.content)
    
    try:
        df = pd.read_excel(contenido)
    except Exception:
        contenido.seek(0)
        df = pd.read_csv(contenido, sep=None, engine="python")
    return df


def evaluar_desarrollo_con_pdf(texto_referencia, respuesta_alumno):
    """Compara el desarrollo del alumno con los términos del PDF oficial."""
    palabras_ref = set(
        p.lower().strip(".,;:()\"'«»¿?¡!-")
        for p in texto_referencia.split()
        if len(p) > 4
    )
    palabras_alumno = set(
        p.lower().strip(".,;:()\"'«»¿?¡!-")
        for p in respuesta_alumno.split()
        if len(p) > 4
    )
    if not palabras_ref:
        return 0, 0, []
    
    coincidencias = palabras_ref.intersection(palabras_alumno)
    faltantes_muestra = sorted(list(palabras_ref - palabras_alumno))[:25]
    porcentaje = round((len(coincidencias) / len(palabras_ref)) * 100, 1)
    return len(coincidencias), porcentaje, faltantes_muestra
# ==============================================================================
# <<< FIN DE LA SECCIÓN 3 DE 5 (No falta nada en esta sección)
# ==============================================================================

# ==============================================================================
# >>> INICIO DE LA SECCIÓN 4 DE 5: BARRA LATERAL Y SELECTORES EN CASCADA
# ==============================================================================
st.sidebar.title("🗂️ Panel del Opositor")

# 1. Selección de Cuerpo (ADMINISTRATIVOS / GESTION)
cuerpo_seleccionado = st.sidebar.selectbox(
    "1. Selecciona el Cuerpo:",
    list(TESTS_DISPONIBLES.keys())
)

# 2. Selección de Bloque / Carpeta (DESARROLLO, ESPECIFICO, EXAMENES, GENERAL, SUPUESTOS)
categorias_disponibles = list(TESTS_DISPONIBLES[cuerpo_seleccionado].keys())
categoria_seleccionada = st.sidebar.selectbox(
    "2. Selecciona el Bloque / Modalidad:",
    categorias_disponibles
)

# 3. Selección del Archivo concreto dentro de la carpeta
archivos_disponibles = TESTS_DISPONIBLES[cuerpo_seleccionado][categoria_seleccionada]
item_seleccionado = st.sidebar.selectbox(
    "3. Selecciona el Tema o Examen:",
    list(archivos_disponibles.keys())
)

url_activa = archivos_disponibles[item_seleccionado]

# Si el usuario cambia de tema o test, reiniciamos el estado de corrección
identificador_actual = f"{cuerpo_seleccionado}_{categoria_seleccionada}_{item_seleccionado}"
if st.session_state.ultimo_item_cargado != identificador_actual:
    st.session_state.respuestas_usuario = {}
    st.session_state.test_corregido = False
    st.session_state.desarrollo_evaluado = False
    st.session_state.ultimo_item_cargado = identificador_actual
# ==============================================================================
# <<< FIN DE LA SECCIÓN 4 DE 5 (No falta nada en esta sección)
# ==============================================================================

# ==============================================================================
# >>> INICIO DE LA SECCIÓN 5 DE 5: INTERFAZ PRINCIPAL (DESARROLLO Y TESTS)
# ==============================================================================
if not url_activa:
    st.info("👈 Selecciona un Cuerpo, un Bloque y un Tema o Examen en el menú lateral para comenzar.")

elif categoria_seleccionada == "DESARROLLO":
    # --------------------------------------------------------------------------
    # 5.1 MÓDULO DE DESARROLLO (TRABAJO CON LOS PDFs DE EPÍGRAFES DE GESTIÓN)
    # --------------------------------------------------------------------------
    st.header(f"📝 Examen de Desarrollo: {item_seleccionado}")
    st.caption(f"Cuerpo: **{cuerpo_seleccionado}** | Carpeta: **DESARROLLO**")
    
    try:
        texto_referencia, pdf_bytes = descargar_pdf_drive(url_activa)
        
        col_estado, col_descarga = st.columns([3, 1])
        with col_estado:
            st.success(f"PDF oficial cargado correctamente ({len(texto_referencia)} caracteres extraídos).")
        with col_descarga:
            st.download_button(
                label="📥 Descargar PDF Original",
                data=pdf_bytes,
                file_name=f"{item_seleccionado}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with st.expander("📖 Ver contenido extraído del PDF (Epígrafes / Resumen oficial)", expanded=False):
            st.text_area("Texto de referencia del PDF:", texto_referencia, height=300, disabled=True)
            
        st.divider()
        
        st.subheader("✍️ Redacción del Opositor")
        epigrafe_elegido = st.text_input(
            "Epígrafe o apartado a desarrollar:",
            placeholder="Ej: Epígrafe 1 - Configuración constitucional de la Seguridad Social"
        )
        
        respuesta_opositor = st.text_area(
            "Desarrolla aquí tu exposición:",
            height=350,
            placeholder="Redacta el tema completo o el epígrafe seleccionado citando artículos y normativa..."
        )
        
        if st.button("🚀 Evaluar Desarrollo contra el PDF", type="primary"):
            if not respuesta_opositor.strip():
                st.warning("⚠️ Escribe primero tu desarrollo antes de evaluar.")
            else:
                st.session_state.desarrollo_evaluado = True
                
        if st.session_state.desarrollo_evaluado and respuesta_opositor.strip():
            coincidencias, porcentaje, sugerencias = evaluar_desarrollo_con_pdf(texto_referencia, respuesta_opositor)
            
            st.markdown("### 📊 Resultado de la Evaluación")
            c1, c2, c3 = st.columns(3)
            c1.metric("Palabras escritas", len(respuesta_opositor.split()))
            c2.metric("Términos clave del PDF incluidos", coincidencias)
            c3.metric("Cobertura léxica del tema", f"{porcentaje}%")
            
            with st.expander("🔍 Términos presentes en el PDF que podrías incorporar"):
                st.write(", ".join(sugerencias) if sugerencias else "¡Has cubierto todos los términos principales!")

    except Exception as e:
        st.error(f"❌ Error al leer el PDF desde Google Drive: {e}")

else:
    # --------------------------------------------------------------------------
    # 5.2 MOTOR INTERACTIVO DE PREGUNTAS TIPO TEST
    # --------------------------------------------------------------------------
    st.header(f"✅ Test: {item_seleccionado}")
    st.caption(f"Cuerpo: **{cuerpo_seleccionado}** | Bloque: **{categoria_seleccionada}**")
    
    try:
        df_preguntas = cargar_test_drive(url_activa)
        df_preguntas = df_preguntas.dropna(how="all").reset_index(drop=True)
        
        st.success(f"Test cargado: **{len(df_preguntas)} preguntas** disponibles.")
        
        cols = list(df_preguntas.columns)
        if len(cols) >= 6:
            col_pregunta = cols[0]
            col_op_a, col_op_b, col_op_c, col_op_d = cols[1], cols[2], cols[3], cols[4]
            col_correcta = cols[5]
            col_explicacion = cols[6] if len(cols) > 6 else None
            
            for idx, fila in df_preguntas.iterrows():
                st.markdown(f"**{idx + 1}. {fila[col_pregunta]}**")
                
                opciones = {
                    "A": f"A) {fila[col_op_a]}",
                    "B": f"B) {fila[col_op_b]}",
                    "C": f"C) {fila[col_op_c]}",
                    "D": f"D) {fila[col_op_d]}",
                }
                
                seleccion_actual = st.session_state.respuestas_usuario.get(idx, None)
                respuesta_marcada = st.radio(
                    label=f"Pregunta {idx + 1}",
                    options=list(opciones.keys()),
                    format_func=lambda x: opciones[x],
                    index=list(opciones.keys()).index(seleccion_actual) if seleccion_actual in opciones else None,
                    key=f"preg_{identificador_actual}_{idx}",
                    label_visibility="collapsed",
                    disabled=st.session_state.test_corregido
                )
                
                if respuesta_marcada:
                    st.session_state.respuestas_usuario[idx] = respuesta_marcada
                    
                if st.session_state.test_corregido:
                    letra_correcta = str(fila[col_correcta]).strip().upper()[:1]
                    if respuesta_marcada == letra_correcta:
                        st.success(f"✔️ ¡Correcta! ({letra_correcta})")
                    elif respuesta_marcada is None:
                        st.warning(f"⚪ En blanco. La respuesta correcta era la **{letra_correcta}**.")
                    else:
                        st.error(f"❌ Incorrecta. Marcaste {respuesta_marcada}, pero la correcta es la **{letra_correcta}**.")
                        
                    if col_explicacion and pd.notna(fila[col_explicacion]):
                        st.info(f"💡 **Justificación:** {fila[col_explicacion]}")
                        
                st.divider()
                
            col_btn_corregir, col_btn_reiniciar = st.columns(2)
            with col_btn_corregir:
                if st.button("📊 Corregir Test", type="primary", use_container_width=True):
                    st.session_state.test_corregido = True
                    st.rerun()
            with col_btn_reiniciar:
                if st.button("🔄 Reiniciar Test", use_container_width=True):
                    st.session_state.respuestas_usuario = {}
                    st.session_state.test_corregido = False
                    st.rerun()
                    
            if st.session_state.test_corregido:
                aciertos, fallos, blancos = 0, 0, 0
                for idx, fila in df_preguntas.iterrows():
                    correcta = str(fila[col_correcta]).strip().upper()[:1]
                    marcada = st.session_state.respuestas_usuario.get(idx, None)
                    if marcada is None:
                        blancos += 1
                    elif marcada == correcta:
                        aciertos += 1
                    else:
                        fallos += 1
                        
                total_preg = len(df_preguntas)
                nota_sobre_10 = max(0.0, round(((aciertos - (fallos / 3)) / total_preg) * 10, 2))
                
                st.subheader("🏁 Resumen de Calificación")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("✅ Aciertos", aciertos)
                m2.metric("❌ Errores", fallos)
                m3.metric("⚪ En blanco", blancos)
                m4.metric("🎯 Nota final (sobre 10)", nota_sobre_10)
        else:
            st.dataframe(df_preguntas, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo del test: {e}")
# ==============================================================================
# <<< FIN DE LA SECCIÓN 5 DE 5 Y FIN DEL ARCHIVO COMPLETO (No falta nada)
# ==============================================================================
