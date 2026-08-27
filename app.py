import os
import glob
import time
import cv2
import requests
import numpy as np
import pytesseract
import streamlit as st
from PIL import Image
from gtts import gTTS

# Configuración de la página
st.set_page_config(
    page_title="OCR & Traductor Studio",
    page_icon="🔍",
    layout="wide"
)

# Estilos CSS
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    section[data-testid="stSidebar"] { background-color: #1E293B; border-right: 1px solid #334155; }
    
    .main-title {
        background: linear-gradient(135deg, #FFFFFF 0%, #A855F7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-title { text-align: center; color: #CBD5E1; font-size: 1.1rem; margin-bottom: 1.5rem; }

    .custom-box-ocr {
        background-color: #1E293B; border-left: 5px solid #38BDF8;
        border-radius: 10px; padding: 1rem; color: #E2E8F0; font-size: 1.1rem; margin-bottom: 1rem;
    }
    .custom-box-trans {
        background-color: #1E293B; border-left: 5px solid #E879F9;
        border-radius: 10px; padding: 1rem; color: #F472B6; font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #A855F7 0%, #D946EF 100%);
        color: #FFFFFF !important; border: none; border-radius: 12px;
        padding: 0.6rem 2rem; font-weight: 700; font-size: 1rem; transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(217, 70, 239, 0.6); }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🔍 Scanner OCR & Traductor</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Extrae texto desde una imagen o cámara y conviértelo a audio traducido</p>", unsafe_allow_html=True)

# Idiomas compatibles con gTTS y Google Translate
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

# Función directa de traducción mediante HTTP sin depender de librerías inestables
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
        raise Exception("Error en el servicio de traducción HTTP")

# Limpieza de temporales
def remove_files(n_days):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        for f in mp3_files:
            if os.stat(f).st_mtime < now - (n_days * 86400):
                try: os.remove(f)
                except OSError: pass

remove_files(7)

# Barra lateral
with st.sidebar:
    st.markdown("### ⚙️ Procesamiento de Cámara")
    filtro = st.radio("Filtro para imagen:", ('No', 'Sí (Invertir)'))
    st.divider()
    st.markdown("### 🌐 Parámetros de Traducción")
    in_lang = st.selectbox("Seleccione el lenguaje de entrada", list(LANGUAGES.keys()))
    out_lang = st.selectbox("Seleccione el lenguaje de salida", list(LANGUAGES.keys()), index=0)
    english_accent = st.selectbox("Seleccione el acento", list(ACCENTS.keys()))
    display_output_text = st.checkbox("Mostrar texto traducido", value=True)

# Entrada de Imagen
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

# Procesamiento al presionar el botón
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

            # 1. Obtener texto traducido
            translated_text = traducir_texto(clean_text, input_language, output_language)

            # 2. Mapeo del código de idioma para gTTS (gTTS usa 'zh-cn' para chino)
            gtts_lang = "zh-cn" if output_language.lower() == "zh-cn" else output_language

            # 3. Generar audio en el idioma de SALIDA seleccionado
            tts = gTTS(text=translated_text, lang=gtts_lang, tld=tld, slow=False)
            audio_path = "temp/traduccion_audio.mp3"
            tts.save(audio_path)

            # 4. Renderizar texto de la traducción en pantalla
            if display_output_text:
                st.markdown(f"### 📄 Texto traducido ({out_lang}):")
                st.markdown(f'<div class="custom-box-trans">{translated_text}</div>', unsafe_allow_html=True)

            # 5. Renderizar audio en pantalla
            st.markdown(f"### 🔊 Audio traducido ({out_lang}):")
            with open(audio_path, "rb") as audio_file:
                st.audio(audio_file.read(), format="audio/mp3")

        except Exception as e:
            st.error(f"Error durante el proceso: {e}")
