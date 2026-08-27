import streamlit as st
import os
import time
import glob
import cv2
import requests
import numpy as np
import pytesseract
from PIL import Image
from gtts import gTTS

# Configuración de página
st.set_page_config(
    page_title="OCR & Traductor de Voz",
    page_icon="🌐",
    layout="wide"
)

# --- ESTILOS DE COLOR PERSONALIZADOS (CSS) ---
st.markdown("""
    <style>
    /* Fondo principal de la aplicación */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }

    /* Títulos y Subtítulos */
    h1 {
        background: linear-gradient(135deg, #A855F7 0%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    h2, h3, h4, label, .stMarkdown {
        color: #F1F5F9 !important;
    }

    /* Contenedores con borde */
    div[data-testid="stForm"], div[data-testid="stBlock"] > div[data-testid="stVerticalBlock"] > div[data-baseweb="card"] {
        background-color: #1E293B;
        border: 1px solid #334155 !important;
        border-radius: 12px;
    }

    /* Modificación de contenedores con borde activado (border=True) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }

    /* Pestañas (Tabs) */
    button[data-baseweb="tab"] {
        background-color: transparent;
        color: #94A3B8 !important;
        border-radius: 8px 8px 0 0;
    }
    button[aria-selected="true"] {
        background-color: #334155 !important;
        color: #38BDF8 !important;
        border-bottom: 3px solid #38BDF8 !important;
    }

    /* Botón Principal */
    div.stButton > button {
        background: linear-gradient(135deg, #8B5CF6 0%, #D946EF 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(217, 70, 239, 0.6);
    }

    /* Cajas de Alerta e Info */
    div[data-testid="stNotification"] {
        background-color: #1E293B !important;
        border: 1px solid #38BDF8 !important;
        color: #F8FAFC !important;
    }

    /* Áreas de Texto e Inputs */
    textarea, input, select {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Función nativa de traducción directa HTTP (estable y sin bloqueos)
def traducir_texto(text_to_translate, source_lang, target_lang):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": source_lang,
        "tl": target_lang,
        "dt": "t",
        "q": text_to_translate
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json()
        translated_text = "".join([item[0] for item in result[0] if item[0]])
        return translated_text
    else:
        raise Exception("Error en la conexión con el servidor de traducción")

# Crear directorio temporal si no existe
if not os.path.exists("temp"):
    os.makedirs("temp")

# Función de limpieza de archivos antiguos
def remove_files(n_days_old=7):
    mp3_files = glob.glob("temp/*.mp3")
    now = time.time()
    n_seconds = n_days_old * 86400
    for f in mp3_files:
        if os.stat(f).st_mtime < now - n_seconds:
            try:
                os.remove(f)
            except Exception:
                pass

remove_files(7)

def text_to_speech(input_language, output_language, text, tld):
    trans_text = traducir_texto(text, input_language, output_language)
    
    # Ajuste de código para idioma Chino en gTTS
    gtts_lang = "zh-cn" if output_language.lower() == "zh-cn" else output_language
    
    tts = gTTS(trans_text, lang=gtts_lang, tld=tld, slow=False)
    
    # Formatear nombre de archivo válido
    file_prefix = "".join(x for x in text[:15] if x.isalnum()).strip()
    my_file_name = file_prefix if file_prefix else "audio_result"
    
    file_path = f"temp/{my_file_name}.mp3"
    tts.save(file_path)
    return file_path, trans_text

# Mapeo de idiomas
LANGUAGES = {
    "Español": "es",
    "Inglés": "en",
    "Bengalí": "bn",
    "Coreano": "ko",
    "Mandarín": "zh-cn",
    "Japonés": "ja"
}

ACCENTS = {
    "Predeterminado": "com",
    "Estados Unidos": "com",
    "Reino Unido": "co.uk",
    "Canadá": "ca",
    "Australia": "com.au",
    "India": "co.in",
    "Irlanda": "ie",
    "Sudáfrica": "co.za"
}

# --- INTERFAZ PRINCIPAL ---
st.title("🌐 Reconocimiento Óptico y Traductor de Voz")
st.caption("Extrae texto de imágenes (cámara o archivo) y conviértelo a audio traducido.")
st.divider()

# Variables de estado
extracted_text = ""
img_rgb = None

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.subheader("1. Procesamiento de Imagen")
    aplicar_filtro = st.toggle("Aplicar filtro de inversión", value=False)
    
    st.subheader("2. Idiomas y Voz")
    in_lang_name = st.selectbox("Idioma de origen (Imagen)", list(LANGUAGES.keys()), index=0)
    out_lang_name = st.selectbox("Idioma de destino (Audio)", list(LANGUAGES.keys()), index=1)
    
    accent_name = st.selectbox("Acento de voz (Para Inglés)", list(ACCENTS.keys()))
    
    display_output_text = st.checkbox("Mostrar texto traducido", value=True)

# --- CUERPO PRINCIPAL ---
tab1, tab2 = st.tabs(["📷 Usar Cámara", "📁 Subir Imagen"])

with tab1:
    img_file_buffer = st.camera_input("Toma una fotografía:")
    if img_file_buffer is not None:
        bytes_data = img_file_buffer.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        if aplicar_filtro:
            cv2_img = cv2.bitwise_not(cv2_img)
        img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

with tab2:
    bg_image = st.file_uploader("Selecciona un archivo (PNG o JPG):", type=["png", "jpg", "jpeg"])
    if bg_image is not None:
        bytes_data = bg_image.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        if aplicar_filtro:
            cv2_img = cv2.bitwise_not(cv2_img)
        img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

# --- EXTRACTION & RESULTADOS ---
if img_rgb is not None:
    col_img, col_txt = st.columns(2)
    
    with col_img:
        with st.container(border=True):
            st.subheader("🖼️ Imagen cargada")
            st.image(img_rgb, use_container_width=True)
            
    with col_txt:
        with st.container(border=True):
            st.subheader("📝 Texto Detectado")
            with st.spinner("Procesando imagen con OCR..."):
                extracted_text = pytesseract.image_to_string(img_rgb)
            
            if extracted_text.strip():
                st.text_area("Texto extraído:", value=extracted_text, height=180)
            else:
                st.warning("No se logró detectar texto en la imagen.")

    # --- SECCIÓN DE TRADUCCIÓN Y AUDIO ---
    if extracted_text.strip():
        st.divider()
        st.subheader("🔊 Traducción y Lectura en Audio")
        
        if st.button("Convertir y Generar Audio", type="primary"):
            input_language = LANGUAGES[in_lang_name]
            output_language = LANGUAGES[out_lang_name]
            tld = ACCENTS[accent_name]
            
            with st.spinner("Traduciendo y generando archivo de audio..."):
                try:
                    file_path, output_text = text_to_speech(
                        input_language, output_language, extracted_text, tld
                    )
                    
                    st.success("¡Audio generado con éxito!")
                    
                    if display_output_text:
                        st.markdown("*Texto traducido:*")
                        st.info(output_text)
                        
                    st.markdown("*Escuchar:*")
                    with open(file_path, "rb") as f:
                        audio_bytes = f.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    
                except Exception as e:
                    st.error(f"Ocurrió un error al procesar el audio: {e}")
