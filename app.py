import streamlit as st
import os
import time
import glob
import cv2
import numpy as np
import pytesseract
from PIL import Image
from gtts import gTTS
from googletrans import Translator

# Configuración de página
st.set_page_config(
    page_title="OCR & Traductor de Voz",
    page_icon="🌐",
    layout="wide"
)

# Inicialización de servicios
translator = Translator()

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
    translation = translator.translate(text, src=input_language, dest=output_language)
    trans_text = translation.text
    
    tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
    
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
