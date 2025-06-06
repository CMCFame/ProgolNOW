import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import io
import sys
import os

# Configuración de la página
st.set_page_config(
    page_title="Progol Optimizer - Metodología Definitiva",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar módulos locales con manejo de errores
try:
    from models.match_classifier import MatchClassifier
    from models.portfolio_generator import PortfolioGenerator
    from models.validators import PortfolioValidator
    from utils.helpers import (
        create_sample_data, 
        clean_for_json, 
        safe_json_dumps, 
        load_partidos_from_csv, 
        generate_csv_template, 
        validate_partido_data
    )
    from config import Config
except ImportError as e:
    st.error(f"❌ Error importando módulos principales: {str(e)}")
    st.error("Verifica que todos los archivos estén en su lugar correcto")
    st.stop()

# Configuración de scraping usando Streamlit Secrets
SCRAPING_CONFIG = {
    'odds_api_key': st.secrets.get("ODDS_API_KEY", None) if hasattr(st, 'secrets') else None,
    'rapid_api_key': st.secrets.get("RAPID_API_KEY", None) if hasattr(st, 'secrets') else None,
    'delay_range': (1, 3),
    'timeout': 30,
    'enabled': False,
    'available_scrapers': [],
    'error_message': None
}

# Intentar importar sistema de scraping de manera robusta
def initialize_scraping_system():
    """Inicializa el sistema de scraping de manera segura"""
    try:
        scraper_path = os.path.join(os.path.dirname(__file__), 'scrapers')
        if not os.path.exists(scraper_path):
            SCRAPING_CONFIG['error_message'] = "Carpeta 'scrapers' no encontrada"
            return False
        
        if scraper_path not in sys.path:
            sys.path.append(scraper_path)
        
        try:
            import scrapers
            available_scrapers = scrapers.get_available_scrapers() if hasattr(scrapers, 'get_available_scrapers') else []
            SCRAPING_CONFIG['available_scrapers'] = available_scrapers
            
            if available_scrapers:
                SCRAPING_CONFIG['enabled'] = True
                st.success(f"✅ Sistema de scraping disponible: {', '.join(available_scrapers)}")
                return True
            else:
                SCRAPING_CONFIG['error_message'] = "No hay scrapers disponibles"
                return False
                
        except ImportError as e:
            SCRAPING_CONFIG['error_message'] = f"Error importando scrapers: {str(e)}"
            return False
            
    except Exception as e:
        SCRAPING_CONFIG['error_message'] = f"Error inicializando scraping: {str(e)}"
        return False

# Inicializar sistema de scraping
try:
    scraping_initialized = initialize_scraping_system()
    if scraping_initialized:
        # Importaciones lazy - solo si el sistema está disponible
        _template_generator = None
        _data_aggregator = None
        _progol_contest_scraper = None # NUEVO
        
        def get_template_generator():
            global _template_generator
            if _template_generator is None:
                try:
                    from scrapers.template_generator import TemplateGenerator
                    _template_generator = TemplateGenerator(odds_api_key=SCRAPING_CONFIG['odds_api_key'])
                except Exception as e:
                    st.warning(f"Error inicializando TemplateGenerator: {e}")
            return _template_generator
        
        def get_data_aggregator():
            global _data_aggregator
            if _data_aggregator is None:
                try:
                    from scrapers.data_aggregator import DataAggregator
                    _data_aggregator = DataAggregator(odds_api_key=SCRAPING_CONFIG['odds_api_key'])
                except Exception as e:
                    st.warning(f"Error inicializando DataAggregator: {e}")
            return _data_aggregator

        # NUEVO: Getter para el scraper de la quiniela de Progol
        def get_progol_contest_scraper():
            global _progol_contest_scraper
            if _progol_contest_scraper is None:
                try:
                    from scrapers.progol_contest_scraper import ProgolContestScraper
                    _progol_contest_scraper = ProgolContestScraper()
                except Exception as e:
                    st.warning(f"Error inicializando ProgolContestScraper: {e}")
            return _progol_contest_scraper
    else:
        # Funciones dummy si no está disponible
        def get_template_generator(): return None
        def get_data_aggregator(): return None
        def get_progol_contest_scraper(): return None
        if SCRAPING_CONFIG['error_message']:
            st.info(f"ℹ️ Scraping no disponible: {SCRAPING_CONFIG['error_message']}")
            
except Exception as e:
    SCRAPING_CONFIG['enabled'] = False
    SCRAPING_CONFIG['error_message'] = f"Error general de scraping: {str(e)}"
    def get_template_generator(): return None
    def get_data_aggregator(): return None
    def get_progol_contest_scraper(): return None

# La clase ProgolScraper sigue siendo útil como interfaz, la mantenemos
class ProgolScraper:
    """Interfaz principal para scraping en Progol Optimizer - VERSIÓN ROBUSTA"""
    
    def __init__(self):
        self.available = SCRAPING_CONFIG['enabled']
        self.template_generator = get_template_generator()
        self.data_aggregator = get_data_aggregator()
        self.contest_scraper = get_progol_contest_scraper() # NUEVO
            
        if not self.data_aggregator and not self.contest_scraper:
            self.available = False
            st.warning("⚠️ Componentes de scraping no se pudieron inicializar")
    
    def is_available(self) -> bool:
        """Verifica si el sistema de scraping está disponible"""
        return self.available and self.data_aggregator is not None and self.contest_scraper is not None

    # ... (el resto de la clase ProgolScraper puede mantenerse, ya que es una buena abstracción)
    def get_auto_template(self, tipo: str, liga: str) -> str:
        if not self.available or not self.template_generator: return None
        try:
            return self.template_generator.generate_auto_template(tipo, liga)
        except Exception as e:
            st.error(f"Error generando template automático: {e}")
            return None
            
    def close(self):
        try:
            if self.data_aggregator and hasattr(self.data_aggregator, 'close_all'):
                self.data_aggregator.close_all()
        except Exception as e:
            st.warning(f"Error cerrando scrapers: {e}")


def main():
    """Función principal de la aplicación"""
    st.title("🎯 Progol Optimizer - Metodología Definitiva")
    st.markdown("*Sistema avanzado de optimización basado en arquitectura Core + Satélites*")
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
    if 'scraping_config' not in st.session_state:
        st.session_state.scraping_config = {
            'enabled': SCRAPING_CONFIG['enabled'], 'auto_update': True,
            'preferred_source': 'Automático'
        }

def configurar_sidebar():
    """Configura el sidebar con parámetros - CON SCRAPING"""
    with st.sidebar:
        st.header("⚙️ Configuración")
        st.info(f"📊 **{Config.APP_NAME}** v{Config.APP_VERSION}\n\n🎯 {Config.APP_DESCRIPTION}")
        
        with st.expander("🤖 Sistema de Scraping"):
            if SCRAPING_CONFIG['enabled']:
                st.success("✅ Scraping disponible")
                if SCRAPING_CONFIG['odds_api_key']:
                    st.success("🔑 The Odds API configurada")
                else:
                    st.info("💡 Agregue ODDS_API_KEY en secrets para mayor precisión")
                st.session_state.scraping_config['enabled'] = st.checkbox("Habilitar scraping automático", value=True)
            else:
                st.warning("⚠️ Scraping no disponible")
                st.caption("Para habilitar: crear carpeta 'scrapers' con módulos de scraping")
                st.session_state.scraping_config['enabled'] = False

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
                        disabled=not st.session_state.scraping_config.get('enabled', False)):
                cargar_datos_automaticos()
        
        st.divider()
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
        
        with st.expander("📊 Distribución Histórica Progol"):
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Locales", f"{Config.DISTRIBUCION_HISTORICA['L']:.1%}")
            with col2: st.metric("Empates", f"{Config.DISTRIBUCION_HISTORICA['E']:.1%}")
            with col3: st.metric("Visitantes", f"{Config.DISTRIBUCION_HISTORICA['V']:.1%}")
            st.caption(f"📈 Promedio histórico: {Config.EMPATES_PROMEDIO_HISTORICO} empates por quiniela")

# =========================================================================
# FUNCIÓN DE CARGA AUTOMÁTICA COMPLETAMENTE REFACTORIZADA
# =========================================================================
def cargar_datos_automaticos():
    """
    Carga datos automáticamente usando el nuevo flujo de scraping:
    1. Obtiene la lista oficial de partidos de Progol.
    2. Busca los datos (momios/probabilidades) para cada uno de esos partidos.
    """
    scraper_interface = ProgolScraper()
    if not scraper_interface.is_available():
        st.error("❌ Sistema de scraping no disponible o incompleto.")
        st.info("💡 Usando datos de muestra como alternativa.")
        sample_data = create_sample_data()
        st.session_state.partidos_regular = sample_data['partidos_regular'][:14]
        st.session_state.partidos_revancha = sample_data['partidos_revancha'][:7]
        st.success("✅ Datos de muestra cargados como fallback.")
        st.rerun()
        return

    try:
        # FASE 1: Obtener la lista de nombres de partidos de la quiniela oficial
        with st.spinner("🔄 Obteniendo la quiniela oficial de Progol de esta semana..."):
            contest_scraper = scraper_interface.contest_scraper
            partidos_regulares_nombres, partidos_revancha_nombres = contest_scraper.get_match_list()

        if not partidos_regulares_nombres:
            st.error("❌ No se pudo obtener la lista de partidos de la quiniela actual. Puede que la fuente no esté disponible.")
            return

        st.success(f"✅ Quiniela oficial obtenida: {len(partidos_regulares_nombres)} partidos regulares y {len(partidos_revancha_nombres)} de revancha.")

        # FASE 2: Obtener los detalles (probabilidades) para cada partido
        with st.spinner("🔄 Buscando momios y datos para cada partido de la quiniela..."):
            data_aggregator = scraper_interface.data_aggregator
            
            # Cargar datos para la quiniela regular
            if partidos_regulares_nombres:
                partidos_regulares_detalles = data_aggregator.get_details_for_match_list(partidos_regulares_nombres)
                st.session_state.partidos_regular = partidos_regulares_detalles
                st.success(f"✅ {len(partidos_regulares_detalles)} partidos regulares cargados con sus datos.")
            
            # Cargar datos para la revancha
            if partidos_revancha_nombres:
                partidos_revancha_detalles = data_aggregator.get_details_for_match_list(partidos_revancha_nombres)
                st.session_state.partidos_revancha = partidos_revancha_detalles
                st.success(f"✅ {len(partidos_revancha_detalles)} partidos de revancha cargados con sus datos.")

        scraper_interface.close()
        st.balloons()
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error general cargando datos automáticamente: {str(e)}")
        st.info("💡 Usando datos de muestra como fallback.")
        sample_data = create_sample_data()
        st.session_state.partidos_regular = sample_data['partidos_regular'][:14]
        st.session_state.partidos_revancha = sample_data['partidos_revancha'][:7]
        st.success("✅ Datos de muestra cargados.")
        st.rerun()

# ... (El resto del archivo app.py puede permanecer sin cambios)
# La lógica de mostrar_entrada_datos, generar_template_automatico, etc.,
# se mantiene, aunque generar_template_automatico ahora es menos relevante
# que el botón "Datos Auto", que es el flujo principal.

if __name__ == "__main__":
    # Esta es una estructura simplificada de las funciones que faltan para que el
    # código sea ejecutable y puedas ver los cambios. Debes usar tu código original
    # para estas funciones.
    def mostrar_entrada_datos(): st.header("📊 Entrada de Datos")
    def mostrar_estado_scraping(): pass
    def entrada_partidos_con_csv(partidos, tipo): pass
    def mostrar_generacion(): st.header("🎯 Generación")
    def mostrar_resultados(): st.header("📈 Resultados")
    def mostrar_exportacion(): st.header("📄 Exportar")

    main()