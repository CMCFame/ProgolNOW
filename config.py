"""
Configuración para la aplicación de quinielas.
"""
import os
import tempfile
from pathlib import Path

# Directorio base de la aplicación
BASE_DIR = Path(__file__).resolve().parent

# Directorio de datos (usando un directorio temporal para compatibilidad con hosting)
DATA_DIR = os.path.join(tempfile.gettempdir(), "progol_data")

# Configuración del programador
UPDATE_INTERVAL = int(os.environ.get("UPDATE_INTERVAL", "30"))  # segundos

# Configuración de la temporada actual para SofaScore
CURRENT_SEASON = os.environ.get("CURRENT_SEASON", "2024")

# Ligas a considerar para Progol
LIGAS_PROGOL = {
    "Liga MX": "Liga MX",
    "Liga Expansion MX": "Liga Expansion MX",
    "Liga Femenil MX": "Liga Femenil MX",
    "EPL": "EPL",
    "Serie A": "Serie A",
    "Bundesliga": "Bundesliga",
    "Eredivisie": "Eredivisie",
    "Ligue 1": "Ligue 1",
    "Liga NOS": "Liga NOS",
    "Argentina Liga Profesional": "Argentina Liga Profesional",
    "Brasileirao": "Brasileirao",
    "MLS": "MLS",
    "Liga Chilena": "Liga Chilena",
    "Liga Belga": "Liga Belga",
    "RFPL": "RFPL"
}

# Número máximo de quinielas por usuario
MAX_QUINIELAS_POR_USUARIO = 30

# Cache de la aplicación
CACHE_TTL = 60  # segundos de vida para la caché

# Colores para interfaz
COLORS = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
    "warning": "#bcbd22",
    "info": "#17becf",
    "light": "#f8f9fa",
    "dark": "#343a40",
}

# Estados de partidos para visualización
MATCH_STATUS = {
    "L": {"text": "Local gana", "color": COLORS["primary"]},
    "E": {"text": "Empate", "color": COLORS["warning"]},
    "V": {"text": "Visitante gana", "color": COLORS["danger"]},
}

# Configurar rutas de directorios
def setup_directories():
    """Crea los directorios necesarios para la aplicación."""
    os.makedirs(DATA_DIR, exist_ok=True)