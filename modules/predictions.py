# modules/predictions.py
import streamlit as st
from modules.user_data import save_user_data
from modules.quiniela_analyzer import show_quiniela_analyzer
from utils.api_client import FootballAPIClient
import random
from data.sample_data import progol_matches

def show_predictions():
    """
    Muestra la interfaz para gestionar predicciones de quiniela
    """
    # Datos iniciales
    if "user_data" not in st.session_state:
        st.session_state.user_data = {}
    
    if "predictions" not in st.session_state.user_data:
        st.session_state.user_data["predictions"] = {
            "main": [None] * 14,
            "revenge": [None] * 7
        }
    
    # Tabs para organizar
    tabs = ["Mis Predicciones", "Analizar Quiniela"]
    selected_tab = st.radio("", tabs, horizontal=True)
    
    if selected_tab == "Mis Predicciones":
        render_predictions_ui()
    else:
        show_quiniela_analyzer()

def render_predictions_ui():
    """
    Muestra la interfaz para introducir predicciones manualmente
    """
    st.header("Registra tu Quiniela")
    st.caption("Selecciona L (Local), E (Empate) o V (Visitante) para cada partido")
    
    # Progreso de llenado de quiniela principal
    main_predictions = st.session_state.user_data["predictions"]["main"]
    completed_main = sum(1 for p in main_predictions if p is not None)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Partidos Principales (14)")
    with col2:
        st.caption(f"Completado: {completed_main}/14")
        st.progress(completed_main / 14)
    
    # Renderizar partidos principales
    for i, match in enumerate(progol_matches["main"]):
        render_match_prediction(match, i, "main")
    
    # Progreso de llenado de revancha
    revenge_predictions = st.session_state.user_data["predictions"]["revenge"]
    completed_revenge = sum(1 for p in revenge_predictions if p is not None)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Revancha (7)")
    with col2:
        st.caption(f"Completado: {completed_revenge}/7")
        st.progress(completed_revenge / 7)
    
    # Renderizar partidos de revancha
    for i, match in enumerate(progol_matches["revenge"]):
        render_match_prediction(match, i, "revenge")
    
    # Botones de acción
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎲 Generar Aleatorio", use_container_width=True):
            generate_random_predictions()
            st.toast("Predicciones aleatorias generadas")
            st.rerun()
    
    with col2:
        if st.button("💾 Guardar Quiniela", use_container_width=True):
            save_user_data(st.session_state.user_data)
            st.success("¡Quiniela guardada correctamente!")
            st.balloons()

def render_match_prediction(match, index, match_type):
    """
    Renderiza un partido con opciones de predicción
    
    Args:
        match (dict): Datos del partido
        index (int): Índice del partido
        match_type (str): Tipo de partido ('main' o 'revenge')
    """
    match_index = index if match_type == "main" else index + 14
    
    with st.container():
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.write(f"**{match_index + 1}. {match['home']} vs {match['away']}**")
            st.caption(f"Fecha: {match['date']}")
        
        with col2:
            # Obtener predicción actual
            current_prediction = st.session_state.user_data["predictions"][match_type][index]
            
            # Crear selector de predicción
            key = f"{match_type}_{index}"
            selection = st.radio(
                f"Predicción para partido #{match_index + 1}",
                options=["L", "E", "V"],
                horizontal=True,
                key=key,
                label_visibility="collapsed",
                index=["L", "E", "V"].index(current_prediction) if current_prediction in ["L", "E", "V"] else None
            )
            
            # Actualizar predicción
            if selection:
                st.session_state.user_data["predictions"][match_type][index] = selection
        
        st.markdown("---")

def generate_random_predictions():
    """
    Genera predicciones aleatorias para todos los partidos
    """
    options = ["L", "E", "V"]
    
    # Generar predicciones para partidos principales
    st.session_state.user_data["predictions"]["main"] = [
        random.choice(options) for _ in range(14)
    ]
    
    # Generar predicciones para partidos de revancha
    st.session_state.user_data["predictions"]["revenge"] = [
        random.choice(options) for _ in range(7)
    ]

def update_predictions(predictions_data):
    """
    Actualiza las predicciones a partir de datos analizados por IA
    
    Args:
        predictions_data (dict): Datos de predicciones analizados por IA
    """
    # Actualizar partidos principales
    for i, match in enumerate(predictions_data.get("main", [])):
        if i < 14:  # Asegurar que no exceda el límite
            prediction = match.get("prediction")
            if prediction in ["L", "E", "V"]:
                st.session_state.user_data["predictions"]["main"][i] = prediction
    
    # Actualizar partidos de revancha
    for i, match in enumerate(predictions_data.get("revenge", [])):
        if i < 7:  # Asegurar que no exceda el límite
            prediction = match.get("prediction")
            if prediction in ["L", "E", "V"]:
                st.session_state.user_data["predictions"]["revenge"][i] = prediction
    
    # Guardar cambios
    save_user_data(st.session_state.user_data)