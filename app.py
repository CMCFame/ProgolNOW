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
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
    'odds_api_key': st.secrets.get("ODDS_API_KEY", None),
    'rapid_api_key': st.secrets.get("RAPID_API_KEY", None),
    'delay_range': (1, 3),
    'timeout': 30,
    'enabled': False
}

=======
    'odds_api_key': st.secrets.get("ODDS_API_KEY", None),
    'rapid_api_key': st.secrets.get("RAPID_API_KEY", None),
    'delay_range': (1, 3),
    'timeout': 30,
    'enabled': False
}

>>>>>>> parent of d1a432e (ok)
# Intentar importar sistema de scraping
try:
    # Agregar path del scraper
    scraper_path = os.path.join(os.path.dirname(__file__), 'scrapers')
    if scraper_path not in sys.path:
        sys.path.append(scraper_path)
    
    from scrapers.template_generator import TemplateGenerator
    from scrapers.data_aggregator import DataAggregator
    SCRAPING_CONFIG['enabled'] = True
    
except ImportError as e:
    st.warning(f"⚠️ Sistema de scraping no disponible: {str(e)}")
    SCRAPING_CONFIG['enabled'] = False

class ProgolScraper:
    """Interfaz principal para scraping en Progol Optimizer"""
    
    def __init__(self):
        self.available = SCRAPING_CONFIG['enabled']
        if self.available:
            try:
                self.template_generator = TemplateGenerator(
                    odds_api_key=SCRAPING_CONFIG['odds_api_key']
                )
                self.data_aggregator = DataAggregator(
                    odds_api_key=SCRAPING_CONFIG['odds_api_key']
                )
            except Exception as e:
                st.warning(f"Error inicializando scrapers: {e}")
                self.available = False
    
    def is_available(self) -> bool:
        """Verifica si el sistema de scraping está disponible"""
        return self.available
    
    def get_auto_template(self, tipo: str, liga: str) -> str:
        """Genera template automático con datos reales"""
        if not self.available:
            return None
        
>>>>>>> parent of d1a432e (ok)
        try:
            from scrapers.data_aggregator import DataAggregator
            _data_aggregator = DataAggregator(api_key=SCRAPING_CONFIG['odds_api_key'])
        except Exception as e:
<<<<<<< HEAD
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
=======
            st.error(f"Error generando template automático: {e}")
            return None
    
    def get_available_leagues(self) -> list:
        """Obtiene ligas disponibles para scraping"""
        if not self.available:
            return []
        
        return [
            'premier_league',
            'la_liga', 
            'serie_a',
            'bundesliga',
            'champions_league',
            'liga_mx',
            'brasileirao'
        ]
    
    def get_live_matches(self, liga: str, count: int = 14) -> list:
        """Obtiene partidos en vivo para una liga"""
        if not self.available:
            return []
        
        try:
            matches = self.data_aggregator.get_matches(liga, count)
            return matches
        except Exception as e:
            st.error(f"Error obteniendo partidos en vivo: {e}")
            return []
    
    def close(self):
        """Cierra conexiones del scraper"""
        if self.available:
            if hasattr(self, 'template_generator'):
                self.template_generator.close()
            if hasattr(self, 'data_aggregator'):
                self.data_aggregator.close_all()
<<<<<<< HEAD
>>>>>>> parent of d1a432e (ok)
=======
>>>>>>> parent of d1a432e (ok)

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
        
<<<<<<< HEAD
        with st.expander("⚙️ Configuración Avanzada"):
            concentracion_general = st.slider("Concentración máxima general (%)", 60, 80, 70) / 100
            concentracion_inicial = st.slider("Concentración máxima partidos 1-3 (%)", 50, 70, 60) / 100
            correlacion_target = st.slider("Correlación negativa objetivo", -0.5, -0.2, -0.35, 0.05)
            seed = st.number_input("Semilla aleatoria", 1, 1000, 42)
        
        st.session_state.config.update({
            'num_quinielas': num_quinielas, 'empates_min': empates_min, 'empates_max': empates_max,
            'concentracion_general': concentracion_general, 'concentracion_inicial': concentracion_inicial,
            'correlacion_target': correlacion_target, 'seed': seed
=======
        # Guardar en session state
        st.session_state.config.update({
            'num_quinielas': num_quinielas,
            'empates_min': empates_min,
            'empates_max': empates_max
>>>>>>> parent of 7c169dc (ok)
        })

def cargar_datos_automaticos():
<<<<<<< HEAD
<<<<<<< HEAD
    """Carga datos automáticamente usando el nuevo flujo de scraping."""
    contest_scraper = get_progol_contest_scraper()
    data_aggregator = get_data_aggregator()

    if not contest_scraper or not data_aggregator:
        st.error("❌ Los componentes de scraping no están disponibles. Revisa los logs.")
=======
    """Carga datos automáticamente usando scraping"""
    if not SCRAPING_CONFIG['enabled']:
        st.error("❌ Sistema de scraping no disponible")
>>>>>>> parent of d1a432e (ok)
=======
    """Carga datos automáticamente usando scraping"""
    if not SCRAPING_CONFIG['enabled']:
        st.error("❌ Sistema de scraping no disponible")
>>>>>>> parent of d1a432e (ok)
        return

    try:
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
=======
>>>>>>> parent of d1a432e (ok)
        scraper = ProgolScraper()
        
<<<<<<< HEAD
        if not scraper.is_available():
            st.error("❌ No se pudo inicializar el scraper")
            return
        
        with st.spinner("🔄 Obteniendo datos automáticamente..."):
            # Cargar partidos regulares (Premier League por defecto)
            partidos_regular = scraper.get_live_matches('premier_league', 14)
            
            # Cargar partidos de revancha (Liga MX por defecto)
            partidos_revancha = scraper.get_live_matches('liga_mx', 7)
            
            success_count = 0
            
            if partidos_regular:
                st.session_state.partidos_regular = partidos_regular
                st.success(f"✅ {len(partidos_regular)} partidos regulares cargados automáticamente")
                success_count += 1
            
            if partidos_revancha:
                st.session_state.partidos_revancha = partidos_revancha
                st.success(f"✅ {len(partidos_revancha)} partidos de revancha cargados automáticamente")
                success_count += 1
            
            if success_count == 0:
                st.warning("⚠️ No se pudieron obtener datos automáticamente. Usando datos de muestra.")
                # Fallback a datos de muestra
                sample_data = create_sample_data()
                st.session_state.partidos_regular = sample_data['partidos_regular'][:14]
                st.session_state.partidos_revancha = sample_data['partidos_revancha'][:7]
            
            scraper.close()
            st.rerun()
>>>>>>> parent of d1a432e (ok)
            
<<<<<<< HEAD
            if partidos_revancha_nombres:
                st.session_state.partidos_revancha = data_aggregator.get_details_for_match_list(partidos_revancha_nombres)
                st.success(f"✅ {len(st.session_state.partidos_revancha)} partidos de revancha cargados con datos.")

        st.balloons()
        st.rerun()

    except Exception as e:
<<<<<<< HEAD
        st.error(f"❌ Error general durante la carga automática: {e}")


# El resto de las funciones (mostrar_entrada_datos, mostrar_generacion, etc.)
# no necesitan cambios. Solo debes asegurarte de tenerlas en tu archivo.
# Por brevedad, las omito aquí, pero debes mantener las tuyas.
def mostrar_entrada_datos(): st.header("Función 'mostrar_entrada_datos' sin implementar en este bloque")
def mostrar_generacion(): st.header("Función 'mostrar_generacion' sin implementar en este bloque")
def mostrar_resultados(): st.header("Función 'mostrar_resultados' sin implementar en este bloque")
def mostrar_exportacion(): st.header("Función 'mostrar_exportacion' sin implementar en este bloque")
=======
=======
    except Exception as e:
>>>>>>> parent of d1a432e (ok)
        st.error(f"❌ Error cargando datos automáticamente: {str(e)}")
        st.info("💡 Usando datos de muestra como fallback")
        sample_data = create_sample_data()
        st.session_state.partidos_regular = sample_data['partidos_regular'][:14]
        st.session_state.partidos_revancha = sample_data['partidos_revancha'][:7]
        st.rerun()

def mostrar_entrada_datos():
    """Muestra la interfaz de entrada de datos - CON SCRAPING"""
    st.header("📊 Información de Partidos")
    
    # NUEVO: Mostrar estado de scraping
    mostrar_estado_scraping()
    
    # Mostrar progreso actual
    num_regular = len(st.session_state.partidos_regular)
    num_revancha = len(st.session_state.partidos_revancha)
    
    # Barra de progreso
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        progress_regular = min(num_regular / 14, 1.0)
        st.metric("Partidos Regulares", f"{num_regular}/14")
        st.progress(progress_regular)
    
    with col2:
        progress_revancha = min(num_revancha / 7, 1.0) if num_revancha > 0 else 0
        st.metric("Partidos Revancha", f"{num_revancha}/7")
        st.progress(progress_revancha)
    
    with col3:
        total_progress = (num_regular + num_revancha) / 21
        if total_progress >= 0.67:  # Al menos 14 partidos
            st.success("✅ Listo para generar")
        else:
            st.warning("⏳ Faltan partidos")
    
    # Información general
    if num_regular < 14:
        st.info("💡 **Mínimo requerido:** 14 partidos regulares para generar quinielas")
    if num_regular >= 14 and num_revancha == 0:
        st.info("🎯 **Opcional:** Agrega 7 partidos de revancha para portafolio completo")
    
    # Tabs principales
=======
        # Mostrar distribución histórica
        with st.expander("📊 Distribución Histórica Progol"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Locales", f"{Config.DISTRIBUCION_HISTORICA['L']:.1%}")
            with col2:
                st.metric("Empates", f"{Config.DISTRIBUCION_HISTORICA['E']:.1%}")
            with col3:
                st.metric("Visitantes", f"{Config.DISTRIBUCION_HISTORICA['V']:.1%}")

def mostrar_entrada_datos():
    """Muestra la interfaz de entrada de datos"""
    st.header("Información de Partidos")
    
>>>>>>> parent of 7c169dc (ok)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚽ Partidos Regulares (14)")
        entrada_partidos_con_csv(st.session_state.partidos_regular, 'regular')
    
    with col2:
        st.subheader("🔄 Partidos Revancha (7)")
        entrada_partidos_con_csv(st.session_state.partidos_revancha, 'revancha')

def mostrar_estado_scraping():
    """Muestra estado del sistema de scraping en la interfaz"""
    if SCRAPING_CONFIG['enabled']:
        scraper = ProgolScraper()
        
        if scraper.is_available():
            with st.expander("🤖 Estado del Sistema de Scraping"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.success("✅ Sistema Activo")
                    st.caption("Scraping disponible")
                
                with col2:
                    ligas_disponibles = scraper.get_available_leagues()
                    st.metric("Ligas Disponibles", len(ligas_disponibles))
                
                with col3:
                    if st.button("🔄 Actualizar Datos", help="Obtiene datos frescos"):
                        cargar_datos_automaticos()
                
                # Mostrar configuración actual
                if SCRAPING_CONFIG['odds_api_key']:
                    st.success("🔑 API comercial configurada")
                else:
                    st.info("💡 Sin API comercial - usando scraping directo")
                
                # Mostrar ligas disponibles
                if ligas_disponibles:
                    st.caption("**Ligas soportadas:**")
                    st.caption(" • ".join([liga.replace('_', ' ').title() for liga in ligas_disponibles[:5]]))
        
        scraper.close()
    else:
        with st.expander("⚠️ Sistema de Scraping No Disponible"):
            st.warning("Para habilitar scraping automático:")
            st.code("1. Crear carpeta 'scrapers/'")
            st.code("2. Agregar módulos de scraping")
            st.code("3. (Opcional) Configurar API keys en secrets")

def entrada_partidos_con_csv(partidos_list, tipo):
    """Interfaz para entrada de partidos con opción CSV"""
    
    tab1, tab2 = st.tabs(["✏️ Entrada Manual", "📄 Cargar CSV"])
    
    with tab1:
        entrada_manual(partidos_list, tipo)
    
    with tab2:
        entrada_csv(partidos_list, tipo)

def entrada_manual(partidos_list, tipo):
    """Entrada manual de partidos"""
    max_partidos = 14 if tipo == 'regular' else 7
    key_suffix = tipo
    
    with st.form(f"agregar_partido_{tipo}"):
        col1, col2 = st.columns(2)
        
        with col1:
            equipo_local = st.text_input("Equipo Local", key=f"local_{key_suffix}")
        with col2:
            equipo_visitante = st.text_input("Equipo Visitante", key=f"visit_{key_suffix}")
        
        # Probabilidades
        col1, col2, col3 = st.columns(3)
        with col1:
            prob_local = st.slider("Prob. Local (%)", 0, 100, 40, key=f"prob_l_{key_suffix}")
        with col2:
            prob_empate = st.slider("Prob. Empate (%)", 0, 100, 30, key=f"prob_e_{key_suffix}")
        with col3:
            prob_visitante = st.slider("Prob. Visitante (%)", 0, 100, 30, key=f"prob_v_{key_suffix}")
        
        # Factores contextuales
        es_final = st.checkbox("Es Final/Derby", key=f"final_{key_suffix}")
        
        submitted = st.form_submit_button("Agregar Partido")
        
        if submitted and equipo_local and equipo_visitante:
            # Normalizar probabilidades
            total_prob = prob_local + prob_empate + prob_visitante
            if total_prob > 0:
                partido = {
                    'local': equipo_local,
                    'visitante': equipo_visitante,
                    'prob_local': prob_local / total_prob,
                    'prob_empate': prob_empate / total_prob,
                    'prob_visitante': prob_visitante / total_prob,
                    'es_final': es_final,
                    'forma_diferencia': 0,
                    'lesiones_impact': 0
                }
                
                if len(partidos_list) < max_partidos:
                    partidos_list.append(partido)
                    st.success(f"✅ Partido agregado: {equipo_local} vs {equipo_visitante}")
                    st.rerun()
                else:
                    st.error(f"❌ Ya tienes {max_partidos} partidos {tipo}.")
    
    # Mostrar partidos existentes
    if partidos_list:
        st.subheader(f"Partidos ingresados ({len(partidos_list)}/{max_partidos})")
        
        for i, partido in enumerate(partidos_list):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.text(f"{partido['local']} vs {partido['visitante']}")
            with col2:
                st.text(f"L:{partido['prob_local']:.2f} E:{partido['prob_empate']:.2f} V:{partido['prob_visitante']:.2f}")
            with col3:
                if st.button("🗑️", key=f"del_{key_suffix}_{i}"):
                    partidos_list.pop(i)
                    st.rerun()

def entrada_csv(partidos_list, tipo):
<<<<<<< HEAD
    """Entrada de partidos desde CSV - CON SCRAPING AUTOMÁTICO"""
    max_partidos = 14 if tipo == 'regular' else 7
    tipo_desc = "regulares" if tipo == 'regular' else "de revancha"
    
    st.subheader(f"📄 Cargar partidos {tipo_desc} desde CSV")
    
    # Información específica del tipo
    if tipo == 'regular':
        st.info("📋 **Partidos Regulares (14):** Ligas principales, competencias europeas, torneos internacionales")
    else:
        st.info("🏆 **Partidos Revancha (7):** Clásicos latinoamericanos, derbis regionales, finales continentales")
    
    # NUEVA SECCIÓN: Templates automáticos vs manuales
    if SCRAPING_CONFIG['enabled']:
        template_tab1, template_tab2 = st.tabs(["🤖 Template Automático", "📝 Template Manual"])
        
        with template_tab1:
            generar_template_automatico(tipo)
        
        with template_tab2:
            generar_template_manual(tipo, max_partidos, tipo_desc)
    else:
        # Solo template manual si no hay scraping
        generar_template_manual(tipo, max_partidos, tipo_desc)
    
    st.divider()
    
    # Subida de archivo CSV
    uploaded_file = st.file_uploader(
        f"📤 Subir CSV ({max_partidos} partidos {tipo_desc})",
        type=['csv'],
        key=f"csv_upload_{tipo}",
        help=f"Archivo CSV con máximo {max_partidos} partidos {tipo_desc}"
    )
=======
    """Entrada de partidos desde CSV"""
    st.subheader(f"📄 Cargar partidos desde CSV ({tipo})")
    
    # Botón para descargar template
    col1, col2 = st.columns(2)
    
    with col1:
        template_csv = generate_csv_template(tipo)
        st.download_button(
            label="📥 Descargar Template CSV",
            data=template_csv,
            file_name=f"template_partidos_{tipo}.csv",
            mime="text/csv",
            help="Descarga este template, llénalo con tus datos y súbelo aquí"
        )
    
    with col2:
        uploaded_file = st.file_uploader(
            f"Subir CSV de partidos {tipo}",
            type=['csv'],
            key=f"csv_upload_{tipo}",
            help="Sube un archivo CSV con el formato del template"
        )
>>>>>>> parent of 7c169dc (ok)
    
    if uploaded_file is not None:
<<<<<<< HEAD
        procesar_archivo_csv(uploaded_file, partidos_list, tipo, max_partidos, tipo_desc)

def generar_template_automatico(tipo):
    """Genera template con datos reales automáticos"""
    st.markdown("**✨ Genera template con datos REALES obtenidos automáticamente**")
    
    col1, col2 = st.columns(2)
    with col1:
        liga_options = {
            'Premier League': 'premier_league',
            'La Liga': 'la_liga', 
            'Serie A': 'serie_a',
            'Bundesliga': 'bundesliga',
            'Champions League': 'champions_league',
            'Liga MX': 'liga_mx',
            'Brasileirão': 'brasileirao'
        }
        
        liga_seleccionada = st.selectbox(
            f"Liga para template {tipo}:",
            options=list(liga_options.keys()),
            key=f"liga_auto_{tipo}"
        )
        
        # Mostrar información de la liga
        if liga_seleccionada:
            liga_info = {
                'Premier League': "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Equipos ingleses de élite",
                'La Liga': "🇪🇸 Real Madrid, Barcelona, etc.",
                'Liga MX': "🇲🇽 América, Chivas, Cruz Azul, etc.",
                'Champions League': "🏆 Competencia europea de élite",
                'Brasileirão': "🇧🇷 Flamengo, Palmeiras, etc."
            }
            st.caption(liga_info.get(liga_seleccionada, "Liga profesional"))
    
    with col2:
        # Opciones avanzadas
        st.markdown("**⚙️ Opciones:**")
        usar_odds_reales = st.checkbox("Usar odds reales", value=True, key=f"odds_{tipo}")
        incluir_contexto = st.checkbox("Incluir contexto (finales, derbis)", value=True, key=f"ctx_{tipo}")
        
        if st.button(f"🚀 Generar Template Automático", 
                   key=f"gen_auto_{tipo}", use_container_width=True):
            
            liga_codigo = liga_options[liga_seleccionada]
            
            try:
                scraper = ProgolScraper()
                
                with st.spinner(f"🔄 Obteniendo datos reales de {liga_seleccionada}..."):
                    template_auto = scraper.get_auto_template(tipo, liga_codigo)
                
                if template_auto:
                    # Mostrar botón de descarga
                    st.download_button(
                        label="📥 Descargar Template AUTOMÁTICO",
                        data=template_auto,
                        file_name=f"progol_AUTO_{tipo}_{liga_codigo}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key=f"download_auto_{tipo}"
                    )
                    
                    st.success("✅ Template generado con datos reales")
                    
                    # Preview de los datos
                    with st.expander("👀 Preview del template automático"):
                        preview_lines = template_auto.split('\n')
                        non_comment_lines = [line for line in preview_lines if not line.startswith('#')]
                        st.code('\n'.join(non_comment_lines[:8]), language='csv')
                else:
                    st.warning("⚠️ No se pudieron obtener datos reales")
                    st.info("💡 Intenta con otra liga o usa template manual")
                
                scraper.close()
                
            except Exception as e:
                st.error(f"❌ Error generando template automático: {e}")

def generar_template_manual(tipo, max_partidos, tipo_desc):
    """Genera template manual (código existente)"""
    template_csv = generate_csv_template(tipo)
    
    st.download_button(
        label=f"📥 Descargar Template Manual {tipo.title()}",
        data=template_csv,
        file_name=f"progol_template_manual_{tipo}_{max_partidos}partidos.csv",
        mime="text/csv",
        help=f"Template manual con {max_partidos} partidos {tipo_desc} sintéticos",
        use_container_width=True
    )
    
    # Mostrar información del template manual
    st.caption(f"📊 Template manual incluye:")
    if tipo == 'regular':
        st.caption("• 14 partidos sintéticos de ligas europeas")
        st.caption("• Equipos: Real-Barça, Man U-Liverpool, etc.")
        st.caption("• Probabilidades generadas algorítmicamente")
    else:
        st.caption("• 7 partidos sintéticos latinoamericanos")
        st.caption("• Equipos: Boca-River, América-Chivas, etc.")
        st.caption("• Probabilidades ajustadas para clásicos")

def procesar_archivo_csv(uploaded_file, partidos_list, tipo, max_partidos, tipo_desc):
    """Procesa archivo CSV subido"""
    try:
        # Preview del archivo
        st.write("**🔍 Preview del archivo subido:**")
        preview_df = pd.read_csv(uploaded_file)
        
        # Validar número de filas
        if len(preview_df) > max_partidos:
            st.warning(f"⚠️ El archivo tiene {len(preview_df)} filas, se tomarán las primeras {max_partidos}")
            preview_df = preview_df.head(max_partidos)
        elif len(preview_df) < max_partidos:
            st.warning(f"⚠️ El archivo tiene solo {len(preview_df)} partidos, se recomienda {max_partidos} para {tipo}")
        
        st.dataframe(preview_df, use_container_width=True)
        
        # Resetear puntero
        uploaded_file.seek(0)
        
        # Botón para confirmar carga
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Cargar {len(preview_df)} partidos {tipo_desc}", 
                       key=f"confirm_load_{tipo}", use_container_width=True):
                partidos_cargados = load_partidos_from_csv(uploaded_file, tipo)
                
                # Actualizar session state
                if tipo == 'regular':
                    st.session_state.partidos_regular = partidos_cargados
                    st.balloons()  # Celebración para carga exitosa
                else:
                    st.session_state.partidos_revancha = partidos_cargados
                    st.balloons()
                
                st.success(f"🎉 {len(partidos_cargados)} partidos {tipo_desc} cargados exitosamente")
                st.rerun()
        
        with col2:
            st.caption("📝 Revisa los datos antes de confirmar")
            
    except Exception as e:
        st.error(f"❌ Error cargando CSV: {str(e)}")
        st.info("💡 Verifica que el archivo tenga el formato correcto del template")

def mostrar_formato_csv_especifico(tipo):
    """Muestra información específica del formato CSV según el tipo"""
    max_partidos = 14 if tipo == 'regular' else 7
    tipo_desc = "regulares" if tipo == 'regular' else "de revancha"
    
    st.markdown(f"### 📋 Formato para partidos {tipo_desc} ({max_partidos} partidos)")
    
    # Columnas requeridas
    st.markdown("#### Columnas **OBLIGATORIAS:**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - **local**: Nombre del equipo local
        - **visitante**: Nombre del equipo visitante  
        - **prob_local**: Probabilidad victoria local (0.0-1.0)
        """)
    with col2:
        st.markdown("""
        - **prob_empate**: Probabilidad empate (0.0-1.0)
        - **prob_visitante**: Probabilidad victoria visitante (0.0-1.0)
        """)
    
    # Columnas opcionales
    st.markdown("#### Columnas **OPCIONALES:**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - **es_final**: TRUE/FALSE (es final o derby importante)
        - **forma_diferencia**: -3 a +3 (diferencia de forma reciente)
        """)
    with col2:
        st.markdown("""
        - **lesiones_impact**: -2 a +2 (impacto de lesiones)
        """)
    
    # Notas específicas por tipo
    st.markdown("#### 📌 Notas importantes:")
    
    if tipo == 'regular':
        st.markdown("""
        - **Máximo 14 partidos** (jornada regular completa)
        - **Ligas recomendadas:** Premier League, La Liga, Serie A, Bundesliga, Champions League
        - **Variedad:** Mezcla equipos grandes y medianos para diversidad
        - **Empates:** Generalmente 3-5 empates por jornada
        """)
    else:
        st.markdown("""
        - **Máximo 7 partidos** (jornada de revancha)
        - **Ligas recomendadas:** Liga MX, Brasileirão, Liga Argentina, Copa Libertadores
        - **Clásicos:** Incluye derbis y rivalidades tradicionales
        - **Empates:** Generalmente 2-3 empates por jornada (más competitivos)
        """)
    
    st.markdown("""
    - Las probabilidades se **normalizarán automáticamente** a 1.0
    - Puedes usar formato decimal (0.35) o el sistema las convertirá
    - La suma de prob_local + prob_empate + prob_visitante puede ser cualquier valor positivo
    """)
    
    # Ejemplo específico
    st.markdown(f"#### 💡 Ejemplo de {tipo_desc}:")
    
    if tipo == 'regular':
        ejemplo_data = {
            'local': ['Real Madrid', 'Manchester City', 'PSG', 'Bayern Munich'],
            'visitante': ['Barcelona', 'Arsenal', 'Juventus', 'Borussia Dortmund'],
            'prob_local': [0.35, 0.45, 0.40, 0.50],
            'prob_empate': [0.30, 0.28, 0.35, 0.25],
            'prob_visitante': [0.35, 0.27, 0.25, 0.25],
            'es_final': ['TRUE', 'FALSE', 'TRUE', 'FALSE']
        }
        st.caption("🏆 Mezcla de clásicos europeos y partidos Champions League")
    else:
        ejemplo_data = {
            'local': ['Boca Juniors', 'América', 'Flamengo'],
            'visitante': ['River Plate', 'Chivas', 'Palmeiras'],
            'prob_local': [0.30, 0.40, 0.35],
            'prob_empate': [0.40, 0.30, 0.32],
            'prob_visitante': [0.30, 0.30, 0.33],
            'es_final': ['TRUE', 'TRUE', 'FALSE']
        }
        st.caption("🔥 Clásicos latinoamericanos con alta probabilidad de empate")
    
    ejemplo_df = pd.DataFrame(ejemplo_data)
    st.dataframe(ejemplo_df, use_container_width=True)
=======
        try:
            # Preview del archivo
            st.write("**Preview del archivo subido:**")
            preview_df = pd.read_csv(uploaded_file)
            st.dataframe(preview_df.head(), use_container_width=True)
            
            # Resetear puntero
            uploaded_file.seek(0)
            
            # Botón para confirmar carga
            if st.button(f"✅ Cargar {len(preview_df)} partidos", key=f"confirm_load_{tipo}"):
                partidos_cargados = load_partidos_from_csv(uploaded_file, tipo)
                
                # Actualizar session state
                if tipo == 'regular':
                    st.session_state.partidos_regular = partidos_cargados
                else:
                    st.session_state.partidos_revancha = partidos_cargados
                
                st.success(f"✅ {len(partidos_cargados)} partidos {tipo} cargados exitosamente")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error cargando CSV: {str(e)}")
            st.info("Verifica que el archivo tenga el formato correcto del template")
>>>>>>> parent of 7c169dc (ok)

def mostrar_generacion():
    """Muestra la interfaz de generación de portafolio"""
    st.header("Generación de Portafolio")
    
    if len(st.session_state.partidos_regular) >= 14:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Generar Core (4)", type="primary", use_container_width=True):
                generar_quinielas_core()
        
        with col2:
            if st.button("🔄 Generar Satélites", use_container_width=True):
                generar_quinielas_satelites()
        
        with col3:
            if st.button("⚡ Optimizar GRASP", use_container_width=True):
                ejecutar_optimizacion_grasp()
        
        # Mostrar progreso
        if 'quinielas_core' in st.session_state:
            st.success(f"✅ Core: {len(st.session_state.quinielas_core)} quinielas generadas")
        
        if 'quinielas_satelites' in st.session_state:
            st.success(f"✅ Satélites: {len(st.session_state.quinielas_satelites)} quinielas generadas")
        
        if 'quinielas_final' in st.session_state:
            st.success(f"✅ Optimización: {len(st.session_state.quinielas_final)} quinielas finales")
    else:
        st.warning("⚠️ Necesitas ingresar al menos 14 partidos regulares para continuar.")

def generar_quinielas_core():
    """Genera las 4 quinielas core"""
    try:
        with st.spinner("🔄 Generando quinielas Core..."):
            classifier = MatchClassifier()
            generator = PortfolioGenerator()
            
            # Clasificar partidos
            partidos_clasificados = classifier.classify_matches(st.session_state.partidos_regular)
            
            # Generar quinielas core
            quinielas_core = generator.generate_core_quinielas(partidos_clasificados)
            
            st.session_state.partidos_clasificados = partidos_clasificados
            st.session_state.quinielas_core = quinielas_core
            
            st.success(f"✅ {len(quinielas_core)} quinielas Core generadas exitosamente")
            
    except Exception as e:
        st.error(f"❌ Error generando quinielas core: {str(e)}")

def generar_quinielas_satelites():
    """Genera quinielas satélites"""
    if 'quinielas_core' not in st.session_state:
        st.error("❌ Primero debes generar las quinielas Core")
        return
    
    try:
        with st.spinner("🔄 Generando quinielas Satélites..."):
            generator = PortfolioGenerator()
            config = st.session_state.config
            
            num_total = config['num_quinielas']
            num_satelites = num_total - 4  # Restar las 4 Core
            
            quinielas_satelites = generator.generate_satellite_quinielas(
                st.session_state.partidos_clasificados,
                st.session_state.quinielas_core,
                num_satelites
            )
            
            st.session_state.quinielas_satelites = quinielas_satelites
            
            st.success(f"✅ {len(quinielas_satelites)} quinielas satélites generadas")
            
    except Exception as e:
        st.error(f"❌ Error generando satélites: {str(e)}")

def ejecutar_optimizacion_grasp():
    """Ejecuta la optimización GRASP-Annealing"""
    if 'quinielas_core' not in st.session_state or 'quinielas_satelites' not in st.session_state:
        st.error("❌ Necesitas generar Core y Satélites primero")
        return
    
    try:
        with st.spinner("🔄 Ejecutando optimización GRASP..."):
            generator = PortfolioGenerator()
            validator = PortfolioValidator()
            
            # Combinar todas las quinielas
            todas_quinielas = st.session_state.quinielas_core + st.session_state.quinielas_satelites
            
            # Optimizar
            quinielas_optimizadas = generator.optimize_portfolio_grasp(
                todas_quinielas,
                st.session_state.partidos_clasificados
            )
            
            # Validar
            validacion = validator.validate_portfolio(quinielas_optimizadas)
            
            st.session_state.quinielas_final = quinielas_optimizadas
            st.session_state.validacion = validacion
            
            if validacion['es_valido']:
                st.success("✅ Optimización completada exitosamente")
            else:
                st.warning("⚠️ Optimización completada con advertencias")
                
    except Exception as e:
        st.error(f"❌ Error en optimización: {str(e)}")

def mostrar_resultados():
    """Muestra análisis de resultados"""
    st.header("Análisis de Resultados")
    
    if 'quinielas_final' not in st.session_state:
        st.info("💡 Genera las quinielas primero para ver los resultados")
        return
    
    quinielas = st.session_state.quinielas_final
    validacion = st.session_state.get('validacion', {})
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Quinielas", len(quinielas))
    with col2:
        empates_promedio = np.mean([q['resultados'].count('E') for q in quinielas])
        st.metric("Empates Promedio", f"{empates_promedio:.1f}")
    with col3:
        prob_11_plus = np.mean([q.get('prob_11_plus', 0) for q in quinielas])
        st.metric("Pr[≥11] Promedio", f"{prob_11_plus:.1%}")
    with col4:
        if validacion.get('es_valido'):
            st.metric("Validación", "✅ Válido")
        else:
            st.metric("Validación", "⚠️ Advertencias")
    
    # Tabla de quinielas
    if quinielas:
        st.subheader("Quinielas Generadas")
        
        # Crear DataFrame para mostrar
        data = []
        for i, quiniela in enumerate(quinielas):
            row = {'Quiniela': f'Q-{i+1}'}
            for j, resultado in enumerate(quiniela['resultados']):
                row[f'P{j+1}'] = resultado
            row['Empates'] = quiniela['resultados'].count('E')
            row['Prob≥11'] = f"{quiniela.get('prob_11_plus', 0):.1%}"
            data.append(row)
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

def mostrar_exportacion():
    """Muestra opciones de exportación"""
    st.header("Exportación de Resultados")
    
    if 'quinielas_final' not in st.session_state:
        st.info("💡 Genera las quinielas primero para poder exportar")
        return
    
    quinielas = st.session_state.quinielas_final
    partidos = st.session_state.partidos_regular
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Exportar CSV
        if st.button("📁 Generar CSV", use_container_width=True):
            csv_data = generar_csv_export(quinielas, partidos)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv_data,
                file_name=f"progol_quinielas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        # Exportar JSON
        if st.button("📄 Generar JSON", use_container_width=True):
            try:
                json_data = {
<<<<<<< HEAD
                    'metadata': {
                        'fecha_generacion': datetime.now().isoformat(),
                        'total_quinielas': len(quinielas),
                        'metodologia': 'Core + Satélites GRASP-Annealing',
                        'scraping_enabled': SCRAPING_CONFIG['enabled']
                    },
=======
                    'fecha_generacion': datetime.now().isoformat(),
>>>>>>> parent of 7c169dc (ok)
                    'partidos': partidos,
                    'quinielas': quinielas,
                    'total_quinielas': len(quinielas)
                }
                
                # Limpiar datos para JSON
                json_data_clean = clean_for_json(json_data)
                json_string = safe_json_dumps(json_data_clean, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="📥 Descargar JSON",
                    data=json_string,
                    file_name=f"progol_quinielas_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Error generando JSON: {str(e)}")
    
    with col3:
        # Exportar formato Progol
        if st.button("🎯 Generar Formato Progol", use_container_width=True):
            progol_format = generar_formato_progol(quinielas)
            st.download_button(
                label="📥 Descargar Progol",
                data=progol_format,
                file_name=f"progol_boletos_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )

def generar_csv_export(quinielas, partidos):
    """Genera CSV para exportación"""
    output = io.StringIO()
    
    # Crear datos
    data = []
    for i, quiniela in enumerate(quinielas):
        row = {'Quiniela': f'Q-{i+1}'}
        for j, resultado in enumerate(quiniela['resultados']):
            row[f'Partido_{j+1}'] = resultado
        row['Empates'] = quiniela['resultados'].count('E')
        row['Prob_11_Plus'] = quiniela.get('prob_11_plus', 0)
        data.append(row)
    
    # Convertir a DataFrame y CSV
    df = pd.DataFrame(data)
    df.to_csv(output, index=False)
    
    return output.getvalue()

def generar_formato_progol(quinielas):
    """Genera formato específico para Progol"""
    output = []
    output.append("PROGOL OPTIMIZER - QUINIELAS GENERADAS")
    output.append("=" * 50)
    output.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output.append(f"Total de quinielas: {len(quinielas)}")
    
    if SCRAPING_CONFIG['enabled']:
        output.append("Sistema: Metodología + Scraping Automático")
    else:
        output.append("Sistema: Metodología Definitiva")
    
    output.append("")
    
    for i, quiniela in enumerate(quinielas):
        output.append(f"QUINIELA {i+1:02d}: {' '.join(quiniela['resultados'])}")
    
    return "\n".join(output)
>>>>>>> parent of d1a432e (ok)

if __name__ == "__main__":
    main()