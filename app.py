import streamlit as st
from modules.live_matches import show_live_matches
from modules.predictions import show_predictions
from modules.user_data import load_user_data, save_user_data
import modules.ui_components as ui

# Configuración de la página
st.set_page_config(
    page_title="Progol Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar CSS personalizado
def load_css():
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Estado de la aplicación
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_user_data()

# Encabezado principal
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Progol Tracker")
    st.markdown("*Sigue los partidos y registra tus quinielas*")

with col2:
    current_journey = st.session_state.user_data.get("current_journey", "Jornada #24")
    st.markdown(f"<div class='current-journey'>{current_journey}</div>", unsafe_allow_html=True)

# Tabs principales
tabs = ["Partidos en Vivo", "Mi Quiniela", "Historial", "Estadísticas"]
selected_tab = ui.create_tabs(tabs)

# Contenido según la pestaña seleccionada
if selected_tab == "Partidos en Vivo":
    show_live_matches()
elif selected_tab == "Mi Quiniela":
    show_predictions()
elif selected_tab == "Historial":
    ui.show_history(st.session_state.user_data)
elif selected_tab == "Estadísticas":
    ui.show_statistics(st.session_state.user_data)

# Columna lateral
with st.sidebar:
    st.image("assets/logo.png", width=100)
    st.header("Mis Estadísticas")
    
    # Datos estadísticos del usuario
    user_stats = st.session_state.user_data.get("stats", {})
    quinielas = user_stats.get("quinielas", 8)
    aciertos = user_stats.get("aciertos", 76)
    puntos = user_stats.get("puntos", 112)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Quinielas", quinielas)
    col2.metric("Aciertos", aciertos)
    col3.metric("Puntos", puntos)
    
    st.divider()
    st.subheader("Mejor Jornada")
    mejor_jornada = user_stats.get("mejor_jornada", {"numero": 18, "fecha": "12/02/2023", "aciertos": 14})
    st.info(f"Jornada #{mejor_jornada['numero']} ({mejor_jornada['fecha']}): {mejor_jornada['aciertos']} aciertos")
    
    st.divider()
    st.subheader("Clasificación")
    
    # Mostrar tabla de clasificación
    clasificacion = [
        {"pos": 1, "nombre": "Carlos M.", "puntos": 158},
        {"pos": 2, "nombre": "Ana R.", "puntos": 142},
        {"pos": 3, "nombre": "Luis G.", "puntos": 136},
        {"pos": 4, "nombre": "Tú", "puntos": 112},
        {"pos": 5, "nombre": "María J.", "puntos": 98}
    ]
    
    for persona in clasificacion:
        ui.render_clasificacion_item(persona)
    
    if st.button("Ver clasificación completa"):
        st.toast("Funcionalidad en desarrollo")
    
    st.divider()
    st.subheader("Acciones Rápidas")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📌 Llenado Rápido"):
            # Implementar llenado rápido
            st.session_state.user_data["predictions"]["main"] = ["L"] * 14
            st.session_state.user_data["predictions"]["revenge"] = ["L"] * 7
            save_user_data(st.session_state.user_data)
            st.toast("¡Predicciones completadas rápidamente!")
            st.rerun()
        
        if st.button("📊 Exportar"):
            # Exportar datos
            st.toast("Exportando datos...")
            ui.download_user_data(st.session_state.user_data)
    
    with col2:
        if st.button("🔄 Compartir"):
            # Compartir resultados
            st.toast("Compartiendo resultados...")
            st.balloons()
        
        if st.button("📥 Importar"):
            # Importar datos
            st.toast("Función de importación en desarrollo")