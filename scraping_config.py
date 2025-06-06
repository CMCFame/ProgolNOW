# scraping_config.py
"""
Configuración centralizada para el sistema de scraping
"""

import os
from typing import Dict, List

class ScrapingConfig:
    """Configuración para scrapers"""
    
    # APIs (opcionales, mejoran la calidad de datos)
    ODDS_API_KEY = os.getenv('ODDS_API_KEY', None)
    RAPID_API_KEY = os.getenv('RAPID_API_KEY', None)
    
    # Configuración de scraping
    DEFAULT_DELAY_RANGE = (1, 3)  # Segundos entre requests
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    
    # User agents rotativos
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15'
    ]
    
    # Mapeo de ligas
    LEAGUE_MAPPING = {
        'Premier League': 'premier_league',
        'La Liga': 'la_liga',
        'Serie A': 'serie_a',
        'Bundesliga': 'bundesliga',
        'Champions League': 'champions_league',
        'Liga MX': 'liga_mx',
        'Brasileirão': 'brasileirao',
        'Liga Argentina': 'liga_argentina',
        'Copa Libertadores': 'copa_libertadores'
    }
    
    # Fuentes por prioridad
    DATA_SOURCES_PRIORITY = [
        'odds_api',      # API comercial (más confiable)
        'flashscore',    # Scraping Flashscore
        'sofascore',     # Scraping SofaScore
        'fallback'       # Datos sintéticos
    ]
    
    # Configuración por liga
    LEAGUE_CONFIGS = {
        'premier_league': {
            'target_matches': 14,
            'typical_round_days': ['saturday', 'sunday'],
            'season_months': [8, 9, 10, 11, 12, 1, 2, 3, 4, 5]
        },
        'liga_mx': {
            'target_matches': 7,  # Para revancha
            'typical_round_days': ['friday', 'saturday', 'sunday'],
            'season_months': [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]
        }
    }

# requirements_scraping.txt
"""
Dependencias adicionales para scraping:

selenium>=4.15.0
webdriver-manager>=4.0.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
requests>=2.31.0
fake-useragent>=1.4.0
python-dotenv>=1.0.0
"""

# .env (archivo de configuración de entorno)
"""
# APIs opcionales (mejoran la calidad de datos)
ODDS_API_KEY=your_odds_api_key_here
RAPID_API_KEY=your_rapid_api_key_here

# Configuración de scraping
SCRAPING_DELAY_MIN=1
SCRAPING_DELAY_MAX=3
USE_PROXIES=false
PROXY_LIST=

# Logs
LOG_LEVEL=INFO
LOG_FILE=scraping.log
"""

# utils/scraping_helpers.py
"""
Helpers para integrar scraping con la aplicación principal
"""

import streamlit as st
import sys
import os
from typing import List, Dict, Optional

# Agregar path del scraper
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scrapers'))

try:
    from scrapers.template_generator import TemplateGenerator
    from scrapers.data_aggregator import DataAggregator
    from scraping_config import ScrapingConfig
    SCRAPING_AVAILABLE = True
except ImportError as e:
    SCRAPING_AVAILABLE = False
    st.warning(f"Sistema de scraping no disponible: {e}")

class ProgolScraper:
    """Interfaz principal para scraping en Progol Optimizer"""
    
    def __init__(self):
        self.available = SCRAPING_AVAILABLE
        if self.available:
            self.template_generator = TemplateGenerator(
                odds_api_key=ScrapingConfig.ODDS_API_KEY
            )
    
    def is_available(self) -> bool:
        """Verifica si el sistema de scraping está disponible"""
        return self.available
    
    def get_auto_template(self, tipo: str, liga: str) -> Optional[str]:
        """
        Genera template automático con datos reales
        
        Args:
            tipo: 'regular' o 'revancha'
            liga: Liga a obtener
        
        Returns:
            CSV string o None si falla
        """
        if not self.available:
            return None
        
        try:
            return self.template_generator.generate_auto_template(tipo, liga)
        except Exception as e:
            st.error(f"Error generando template automático: {e}")
            return None
    
    def get_available_leagues(self) -> List[str]:
        """Obtiene ligas disponibles para scraping"""
        if not self.available:
            return []
        
        try:
            return self.template_generator.get_available_leagues()
        except:
            return []
    
    def get_live_matches(self, liga: str, count: int = 14) -> List[Dict]:
        """
        Obtiene partidos en vivo para una liga
        
        Args:
            liga: Liga a buscar
            count: Número de partidos objetivo
        
        Returns:
            Lista de partidos o lista vacía si falla
        """
        if not self.available:
            return []
        
        try:
            aggregator = DataAggregator(ScrapingConfig.ODDS_API_KEY)
            matches = aggregator.get_matches(liga, count)
            aggregator.close_all()
            return matches
        except Exception as e:
            st.error(f"Error obteniendo partidos en vivo: {e}")
            return []
    
    def close(self):
        """Cierra conexiones del scraper"""
        if self.available and hasattr(self, 'template_generator'):
            self.template_generator.close()

# Funciones para actualizar app.py

def mostrar_opciones_scraping():
    """Muestra opciones de scraping en la interfaz"""
    scraper = ProgolScraper()
    
    if not scraper.is_available():
        st.warning("⚠️ Sistema de scraping no disponible. Instala dependencias adicionales.")
        return None
    
    st.success("✅ Sistema de scraping disponible")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🤖 Datos Automáticos**")
        liga_auto = st.selectbox(
            "Liga para datos automáticos:",
            options=['premier_league', 'la_liga', 'liga_mx', 'champions_league'],
            format_func=lambda x: x.replace('_', ' ').title(),
            key="liga_auto"
        )
    
    with col2:
        st.markdown("**📊 Configuración**")
        usar_api = st.checkbox("Usar APIs comerciales (más precisión)", value=True)
        solo_proximos = st.checkbox("Solo partidos próximos", value=True)
    
    return {
        'liga': liga_auto,
        'usar_api': usar_api,
        'solo_proximos': solo_proximos,
        'scraper': scraper
    }

def generar_template_automatico(tipo: str, config_scraping: Dict) -> Optional[str]:
    """Genera template con datos automáticos"""
    if not config_scraping or not config_scraping['scraper'].is_available():
        return None
    
    with st.spinner(f"🔄 Obteniendo datos reales de {config_scraping['liga']}..."):
        template_csv = config_scraping['scraper'].get_auto_template(
            tipo, 
            config_scraping['liga']
        )
    
    if template_csv:
        st.success("✅ Template generado con datos reales")
        return template_csv
    else:
        st.warning("⚠️ No se pudieron obtener datos reales, usando template sintético")
        return None

def cargar_partidos_automatico(liga: str, count: int) -> List[Dict]:
    """Carga partidos automáticamente desde scrapers"""
    scraper = ProgolScraper()
    
    if not scraper.is_available():
        return []
    
    with st.spinner(f"🔄 Obteniendo {count} partidos de {liga}..."):
        partidos = scraper.get_live_matches(liga, count)
        scraper.close()
    
    return partidos