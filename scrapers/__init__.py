# scrapers/__init__.py
"""
Sistema de scraping automatizado para datos futbolísticos
Soporta múltiples fuentes: Flashscore, SofaScore, APIs, etc.

Importaciones opcionales para evitar errores cuando faltan dependencias
"""

# Lista de componentes disponibles
__all__ = []

# Importar componentes de manera segura
try:
    from .data_aggregator import DataAggregator
    __all__.append('DataAggregator')
except ImportError as e:
    print(f"Warning: DataAggregator no disponible: {e}")

try:
    from .flashscore_scraper import FlashscoreScraper
    __all__.append('FlashscoreScraper')
except ImportError as e:
    print(f"Warning: FlashscoreScraper no disponible: {e}")

try:
    from .sofascore_scraper import SofascoreScraper
    __all__.append('SofascoreScraper')
except ImportError as e:
    print(f"Warning: SofascoreScraper no disponible: {e}")

try:
    from .odds_scraper import OddsScraper
    __all__.append('OddsScraper')
except ImportError as e:
    print(f"Warning: OddsScraper no disponible: {e}")

try:
    from .template_generator import TemplateGenerator
    __all__.append('TemplateGenerator')
except ImportError as e:
    print(f"Warning: TemplateGenerator no disponible: {e}")

# Información sobre disponibilidad
def get_available_scrapers():
    """Retorna lista de scrapers disponibles"""
    available = []
    
    if 'FlashscoreScraper' in __all__:
        available.append('flashscore')
    if 'SofascoreScraper' in __all__:
        available.append('sofascore')
    if 'OddsScraper' in __all__:
        available.append('odds_api')
    if 'DataAggregator' in __all__:
        available.append('aggregator')
    if 'TemplateGenerator' in __all__:
        available.append('template_generator')
    
    return available

def is_scraping_available():
    """Verifica si el sistema de scraping está disponible"""
    return len(__all__) > 0

# Información de la versión
__version__ = '1.0.0'
__author__ = 'Progol Optimizer Team'