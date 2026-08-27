import os
import glob
import time
import cv2
import numpy as np
import pytesseract
import streamlit as st
from PIL import Image
from gtts import gTTS
from deep_translator import GoogleTranslator

# Configuración de la página
st.set_page_config(
    page_title="OCR & Traductor Studio",
    page_icon="🔍",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }

    section[data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }

    .main-title {
        background: linear-gradient(135deg, #FFFFFF 0%, #A855F7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.2rem;
    }

    .sub-title {
        text-align: center;
        color: #CBD5E1;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }

    .custom-box-ocr {
        background-color: #1E293B;
        border-left: 5px solid #38BDF8;
        border-radius: 10px;
        padding: 1rem;
        color: #E2E8F0;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }

    .custom-box-trans {
        background-color: #1E293B;
        border-left: 5px solid #E879F9;
        border-radius: 10px;
        padding: 1rem;
        color: #F472B6;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #A855F7 0%, #D946EF 100%);
        color: #FFFFFF !important;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(217, 70, 239, 0.6);
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado principal
st.markdown("<h1 class='main-title'>🔍 Scanner OCR & Traductor</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Extrae texto desde una imagen o cámara y conviértelo a audio traducido</p>", unsafe_allow_html=True)

# Diccionarios de idiomas y acentos
LANGUAGES = {
    "Ingles": "en",
    "Español": "es",
    "Bengali": "bn",
    "koreano": "ko",
    "Mandarin": "zh-CN",
    "Japones": "ja"
}

ACCENTS = {
    "Default": "com",
    "India": "co.in",
    "United Kingdom": "co.uk",
    "United States": "com",
    "Canada": "ca",
    "Australia": "com.au",
    "Ireland": "ie",
    "South Africa": "co.za"
}

def remove_files(n_days):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        for f in mp3_files:
            if os.stat(f).st_mtime < now - (n_days * 86400):
                try:
                    os.remove(f)
                except OSError:
                    pass

remove_files(7)

# Panel lateral
with st.sidebar:
    st.markdown("### ⚙️ Procesamiento de Cámara")
    filtro = st.radio("Filtro para imagen:", ('No', 'Sí (Invertir)'))
    
    st.divider()
    
    st.markdown("### 🌐 Parámetros de Traducción")
    in_lang = st.selectbox("Seleccione el lenguaje de entrada", list(LANGUAGES.keys()))
    out_lang = st.selectbox("Seleccione el lenguaje de salida", list(LANGUAGES.keys()), index=1)
    english_accent = st.selectbox("Seleccione el acento", list(ACCENTS.keys()))
    display_output_text = st.checkbox("Mostrar texto traducido", value=True)

# Elección de fuente de imagen
st.markdown("### 📷 Fuente de la imagen")
cam_ = st.checkbox("Usar Cámara")

img_rgb = None
text = ""

col_input, col_preview = st.columns(2)

with col_input:
    if cam_:
        img_file_buffer = st.camera_input("Toma una Foto")
        if img_file_buffer is not None:
            bytes_data = img_file_buffer.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            if filtro == 'Sí (Invertir)':
                cv2_img = cv2.bitwise_not(cv2_img)
            img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    else:
        bg_image = st.file_uploader("Cargar Imagen:", type=["png", "jpg", "jpeg"])
        if bg_image is not None:
            uploaded_file = bg_image
            os.makedirs("temp", exist_ok=True)
            file_path = os.path.join("temp", uploaded_file.name)
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.read())
            img_cv = cv2.imread(file_path)
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)

with col_preview:
    if img_rgb is not None:
        st.markdown("### 🖼️ Vista Previa")
        st.image(img_rgb, use_container_width=True)
        text = pytesseract.image_to_string(img_rgb)

# Procesamiento de la traducción y audio
if text.strip():
    st.divider()
    st.markdown("### 📝 Texto Detectado por OCR")
    st.markdown(f'<div class="custom-box-ocr">{text}</div>', unsafe_allow_html=True)

    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col2:
        convert_btn = st.button("✨ Traducir y Generar Audio", use_container_width=True)

    if convert_btn:
        try:
            os.makedirs("temp", exist_ok=True)
            input_language = LANGUAGES[in_lang]
            output_language = LANGUAGES[out_lang]
            tld = ACCENTS[english_accent]

            clean_text = text.strip()

            # Traducción estable con deep-translator
            translated_text = GoogleTranslator(
                source=input_language, 
                target=output_language
            ).translate(clean_text)

            # Generación de audio
            # Para gTTS en chino simplificado se usa 'zh-cn'
            gtts_lang = "zh-cn" if output_language.lower() == "zh-cn" else output_language
            tts = gTTS(translated_text, lang=gtts_lang, tld=tld, slow=False)
            
            audio_path = "temp/resultado_traduccion.mp3"
            tts.save(audio_path)

            st.markdown("### 🔊 Audio de salida:")
            with open(audio_path, "rb") as audio_file:
                st.audio(audio_file.read(), format="audio/mp3", start_time=0)

            if display_output_text:
                st.markdown("### 📄 Texto traducido:")
                st.markdown(f'<div class="custom-box-trans">{translated_text}</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error al procesar la traducción: {e}")
