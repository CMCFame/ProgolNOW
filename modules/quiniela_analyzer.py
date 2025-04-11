# modules/quiniela_analyzer.py
import streamlit as st
from utils.api_client import OpenAIClient
from modules.predictions import update_predictions
import base64
import json
import re

def show_quiniela_analyzer():
    """
    Muestra el componente para analizar quinielas usando OpenAI
    """
    st.header("Analizar Quiniela con Inteligencia Artificial")
    
    # Widget para cargar archivos
    uploaded_file = st.file_uploader(
        "Arrastra tu quiniela aquí o haz clic para seleccionar",
        type=["pdf", "jpg", "jpeg", "png"],
        help="Formatos soportados: PDF, JPG, PNG"
    )
    
    if uploaded_file:
        # Mostrar vista previa
        file_type = uploaded_file.type
        
        if "pdf" in file_type:
            # Para PDFs usamos un iframe
            base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            # Para imágenes mostramos directamente
            st.image(uploaded_file, caption="Vista previa de quiniela", use_column_width=True)
        
        # Botón para analizar
        analyze_col, save_col = st.columns([1, 1])
        
        with analyze_col:
            analyze_button = st.button("🔍 Analizar con IA", use_container_width=True)
        
        # Analizar el archivo cuando se presiona el botón
        if analyze_button:
            with st.spinner("Analizando quiniela con IA..."):
                try:
                    # Convertir archivo a base64
                    file_bytes = uploaded_file.getvalue()
                    base64_file = base64.b64encode(file_bytes).decode("utf-8")
                    file_uri = f"data:{uploaded_file.type};base64,{base64_file}"
                    
                    # Llamar a OpenAI para análisis
                    openai_client = OpenAIClient()
                    response = openai_client.analyze_quiniela(file_uri)
                    
                    # Extraer JSON de la respuesta
                    predictions = extract_json_from_response(response)
                    
                    if predictions:
                        # Guardar en el estado de la sesión
                        st.session_state.predictions = predictions
                        
                        # Mostrar resultados
                        display_predictions(predictions)
                        
                        # Botón para guardar predicciones
                        with save_col:
                            if st.button("💾 Guardar Predicciones", use_container_width=True):
                                update_predictions(predictions)
                                st.success("Predicciones guardadas correctamente")
                                st.balloons()
                    else:
                        st.error("No se pudieron extraer predicciones de la respuesta.")
                
                except Exception as e:
                    st.error(f"Error al analizar la quiniela: {str(e)}")
                    st.info("Intenta con una imagen más clara o un PDF mejor escaneado.")

def extract_json_from_response(response):
    """
    Extrae el JSON de la respuesta de OpenAI
    
    Args:
        response (dict): Respuesta de OpenAI
    
    Returns:
        dict: Predicciones extraídas o None si no se pudo extraer
    """
    try:
        # Obtener el contenido de la respuesta
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Buscar JSON en el contenido
        json_match = re.search(r'```json\n([\s\S]*?)\n```', content)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
        
        # Si no está en formato código, buscar directamente
        json_match = re.search(r'{[\s\S]*?}', content)
        if json_match:
            return json.loads(json_match.group(0))
            
        return None
    except Exception as e:
        st.error(f"Error al extraer JSON: {str(e)}")
        return None

def display_predictions(predictions):
    """
    Muestra las predicciones extraídas
    
    Args:
        predictions (dict): Predicciones extraídas
    """
    st.subheader("Predicciones Detectadas")
    
    # Partidos principales
    st.write("**Partidos Principales**")
    
    for i, match in enumerate(predictions.get("main", [])):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.write(f"{i+1}. {match.get('home', 'N/A')} vs {match.get('away', 'N/A')}")
        
        with col2:
            prediction = match.get("prediction")
            if prediction == "L":
                st.markdown("<span class='prediction local'>L</span>", unsafe_allow_html=True)
            elif prediction == "E":
                st.markdown("<span class='prediction empate'>E</span>", unsafe_allow_html=True)
            elif prediction == "V":
                st.markdown("<span class='prediction visitante'>V</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='prediction none'>-</span>", unsafe_allow_html=True)
    
    # Partidos de revancha
    st.write("**Revancha**")
    
    for i, match in enumerate(predictions.get("revenge", [])):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.write(f"{i+15}. {match.get('home', 'N/A')} vs {match.get('away', 'N/A')}")
        
        with col2:
            prediction = match.get("prediction")
            if prediction == "L":
                st.markdown("<span class='prediction local'>L</span>", unsafe_allow_html=True)
            elif prediction == "E":
                st.markdown("<span class='prediction empate'>E</span>", unsafe_allow_html=True)
            elif prediction == "V":
                st.markdown("<span class='prediction visitante'>V</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='prediction none'>-</span>", unsafe_allow_html=True)