import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import io
import sys
import os

# =========================================================================
# INICIO: CÓDIGO MEJORADO PARA DETECCIÓN DE RUTAS Y MÓDULOS
# Esto hace que la app sea más robusta.
# =========================================================================
try:
    # Agrega el directorio raíz del proyecto al path de Python para asegurar
    # que los módulos como 'models', 'utils' y 'scrapers' sean encontrados.
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)

    from models.match_classifier import MatchClassifier
    from models.portfolio_generator import PortfolioGenerator
    from models.validators import PortfolioValidator
    from utils.helpers import (
        create_sample_data, clean_for_json, safe_json_dumps,
        load_partidos_from_csv, generate_csv_template, validate_partido_data
    )
    from config import Config
except ImportError as e:
    st.error(f"❌ Error Crítico de Importación: {e}")
    st.error("No se pudieron cargar los módulos base (models, utils, config). Asegúrate de que la estructura de carpetas es correcta y que las dependencias base están instaladas.")
    st.stop()

# Configuración de scraping
SCRAPING_CONFIG = {
    'odds_api_key': st.secrets.get("ODDS_API_KEY", None) if hasattr(st, 'secrets') else None,
    'enabled': False,
    'error_message': "Sistema de scraping no inicializado."
}

# Inicialización segura del sistema de scraping
def initialize_scraping_system():
    """Inicializa el sistema de scraping de manera segura y reporta errores específicos."""
    scraper_path = os.path.join(APP_DIR, 'scrapers')
    if not os.path.isdir(scraper_path):
        SCRAPING_CONFIG['error_message'] = "La carpeta 'scrapers' no fue encontrada en el directorio del proyecto."
        return

    try:
        # Intenta importar el paquete. Si falla, es probable que falte una dependencia.
        import scrapers
        # Si la importación tiene éxito, el paquete y sus dependencias existen.
        SCRAPING_CONFIG['enabled'] = True
        SCRAPING_CONFIG['error_message'] = None # Sin errores
        st.sidebar.success("✅ Sistema de scraping disponible.")
    except ImportError as e:
        # Este es el error clave: nos dirá exactamente qué librería falta.
        SCRAPING_CONFIG['enabled'] = False
        SCRAPING_CONFIG['error_message'] = f"Error al importar 'scrapers': {e}. Es muy probable que falten dependencias. Ejecuta 'pip install -r requirements.txt' en tu terminal."
    except Exception as e:
        SCRAPING_CONFIG['enabled'] = False
        SCRAPING_CONFIG['error_message'] = f"Error inesperado al inicializar scraping: {e}"

# --- Getters para componentes de scraping (Lazy Loading) ---
_data_aggregator = None
_progol_contest_scraper = None

def get_data_aggregator():
    global _data_aggregator
    if _data_aggregator is None and SCRAPING_CONFIG['enabled']:
        try:
            from scrapers.data_aggregator import DataAggregator
            _data_aggregator = DataAggregator(api_key=SCRAPING_CONFIG['odds_api_key'])
        except Exception as e:
            st.warning(f"No se pudo inicializar DataAggregator: {e}")
    return _data_aggregator

def get_progol_contest_scraper():
    global _progol_contest_scraper
    if _progol_contest_scraper is None and SCRAPING_CONFIG['enabled']:
        try:
            from scrapers.progol_contest_scraper import ProgolContestScraper
            _progol_contest_scraper = ProgolContestScraper()
        except Exception as e:
            st.warning(f"No se pudo inicializar ProgolContestScraper: {e}")
    return _progol_contest_scraper

# =========================================================================
# FIN: CÓDIGO MEJORADO
# =========================================================================

def main():
    """Función principal de la aplicación"""
    st.title("🎯 Progol Optimizer - Metodología Definitiva")
    st.markdown("*Sistema avanzado de optimización basado en arquitectura Core + Satélites*")

    # La inicialización ahora se hace aquí para que los mensajes aparezcan en el sidebar
    initialize_scraping_system()
    
    inicializar_session_state()
    configurar_sidebar()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Entrada de Datos", "🎯 Generación", "📈 Resultados", "📄 Exportar"])
    
    with tab1:
        mostrar_entrada_datos()
    with tab2:
        mostrar_generacion()
    with tab3:
        mostrar_resultados()
    with tab4:
        mostrar_exportacion()

def inicializar_session_state():
    """Inicializa el estado de la sesión"""
    if 'partidos_regular' not in st.session_state:
        st.session_state.partidos_regular = []
    if 'partidos_revancha' not in st.session_state:
        st.session_state.partidos_revancha = []
    if 'config' not in st.session_state:
        st.session_state.config = {
            'num_quinielas': 20, 'empates_min': 4, 'empates_max': 6,
            'concentracion_general': 0.70, 'concentracion_inicial': 0.60,
            'correlacion_target': -0.35, 'seed': 42
        }

def configurar_sidebar():
    """Configura el sidebar con parámetros y estado de scraping."""
    with st.sidebar:
        st.header("⚙️ Configuración")
        st.info(f"📊 **{Config.APP_NAME}** v{Config.APP_VERSION}\n\n🎯 {Config.APP_DESCRIPTION}")
        
        with st.expander("🤖 Sistema de Scraping", expanded=True):
            if not SCRAPING_CONFIG['enabled']:
                # Muestra el mensaje de error detallado que obtuvimos en la inicialización
                st.warning(SCRAPING_CONFIG['error_message'])
        
        st.subheader("📊 Carga de Datos")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Datos Muestra", type="secondary", use_container_width=True):
                sample_data = create_sample_data()
                st.session_state.partidos_regular = sample_data['partidos_regular'][:14]
                st.session_state.partidos_revancha = sample_data['partidos_revancha'][:7]
                st.success("✅ Datos de muestra cargados")
                st.rerun()
        with col2:
            if st.button("🤖 Datos Auto", type="primary", use_container_width=True, 
                        disabled=not SCRAPING_CONFIG['enabled']):
                cargar_datos_automaticos()
        
        st.divider()
        # ... (El resto de la configuración del sidebar se mantiene igual)
        st.subheader("⚙️ Parámetros")
        num_quinielas = st.slider("Número de quinielas", 10, 35, 20, 1)
        empates_min = st.slider("Empates mínimos por quiniela", 3, 6, 4)
        empates_max = st.slider("Empates máximos por quiniela", 4, 7, 6)
        
        with st.expander("⚙️ Configuración Avanzada"):
            concentracion_general = st.slider("Concentración máxima general (%)", 60, 80, 70) / 100
            concentracion_inicial = st.slider("Concentración máxima partidos 1-3 (%)", 50, 70, 60) / 100
            correlacion_target = st.slider("Correlación negativa objetivo", -0.5, -0.2, -0.35, 0.05)
            seed = st.number_input("Semilla aleatoria", 1, 1000, 42)
        
        st.session_state.config.update({
            'num_quinielas': num_quinielas, 'empates_min': empates_min, 'empates_max': empates_max,
            'concentracion_general': concentracion_general, 'concentracion_inicial': concentracion_inicial,
            'correlacion_target': correlacion_target, 'seed': seed
        })

def cargar_datos_automaticos():
    """Carga datos automáticamente usando el nuevo flujo de scraping."""
    contest_scraper = get_progol_contest_scraper()
    data_aggregator = get_data_aggregator()

    if not contest_scraper or not data_aggregator:
        st.error("❌ Los componentes de scraping no están disponibles. Revisa los logs.")
        return

    try:
        with st.spinner("🔄 Obteniendo la quiniela oficial de Progol..."):
            partidos_regulares_nombres, partidos_revancha_nombres = contest_scraper.get_match_list()

        if not partidos_regulares_nombres:
            st.error("❌ No se pudo obtener la lista de partidos de la quiniela actual.")
            return

        st.success(f"✅ Quiniela oficial obtenida: {len(partidos_regulares_nombres)} reg. + {len(partidos_revancha_nombres)} rev.")

        with st.spinner("🔄 Buscando momios y datos para cada partido..."):
            if partidos_regulares_nombres:
                st.session_state.partidos_regular = data_aggregator.get_details_for_match_list(partidos_regulares_nombres)
                st.success(f"✅ {len(st.session_state.partidos_regular)} partidos regulares cargados con datos.")
            
            if partidos_revancha_nombres:
                st.session_state.partidos_revancha = data_aggregator.get_details_for_match_list(partidos_revancha_nombres)
                st.success(f"✅ {len(st.session_state.partidos_revancha)} partidos de revancha cargados con datos.")

        st.balloons()
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error general durante la carga automática: {e}")


# El resto de las funciones (mostrar_entrada_datos, mostrar_generacion, etc.)
# no necesitan cambios. Solo debes asegurarte de tenerlas en tu archivo.
# Por brevedad, las omito aquí, pero debes mantener las tuyas.
def mostrar_entrada_datos(): st.header("Función 'mostrar_entrada_datos' sin implementar en este bloque")
def mostrar_generacion(): st.header("Función 'mostrar_generacion' sin implementar en este bloque")
def mostrar_resultados(): st.header("Función 'mostrar_resultados' sin implementar en este bloque")
def mostrar_exportacion(): st.header("Función 'mostrar_exportacion' sin implementar en este bloque")

if __name__ == "__main__":
    main()