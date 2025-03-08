# -------------------------------------------------------
# Librerías e Importaciones necesarias
# -------------------------------------------------------
import streamlit as st
import numpy as np
import pandas as pd
import requests
import yaml
import os
import io
import logging
import re
import datetime
from datetime import datetime as dt
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from typing import Dict, List, Optional, TypedDict, Union, Any
import pytz
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import base64
import time

# Condicional OpenCV
CV2_AVAILABLE = False
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    pass

# -------------------------------------------------------
# Configuración inicial de Streamlit
# -------------------------------------------------------
st.set_page_config(
    page_title="Seguimiento Quiniela Progol",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------
# Configuración de Logging
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Versión de la aplicación
# -------------------------------------------------------
APP_VERSION = "1.0.3"

# -------------------------------------------------------
# Clase Config (corregida y simplificada)
# -------------------------------------------------------
class Config:
    """Clase centralizada para manejar configuraciones"""
    RAPIDAPI_KEY = None
    RAPIDAPI_HOST = "free-api-live-football-data.p.rapidapi.com"
    DEFAULT_TIMEZONE = "America/Mexico_City"
    AUTO_REFRESH_INTERVAL = 300
    TEAMS_DB_PATH = "teams_database.yaml"
    
    @classmethod
    def load_config(cls):
        """Carga la configuración desde Streamlit secrets o entorno"""
        try:
            if 'general' in st.secrets:
                cls.RAPIDAPI_KEY = st.secrets.general.get("RAPIDAPI_KEY", cls.RAPIDAPI_KEY)
                cls.RAPIDAPI_HOST = st.secrets.general.get("RAPIDAPI_HOST", cls.RAPIDAPI_HOST)
            if 'config' in st.secrets:
                cls.DEFAULT_TIMEZONE = st.secrets.config.get("default_timezone", cls.DEFAULT_TIMEZONE)
                cls.AUTO_REFRESH_INTERVAL = int(st.secrets.config.get("auto_refresh_interval", cls.AUTO_REFRESH_INTERVAL))
        except:
            logger.warning("Streamlit secrets no disponibles o incompletos.")
        
        # Variables de entorno (fallback)
        load_dotenv()
        cls.RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", cls.RAPIDAPI_KEY)
        cls.RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", cls.RAPIDAPI_HOST)
        cls.DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", cls.DEFAULT_TIMEZONE)
        cls.AUTO_REFRESH_INTERVAL = int(os.getenv("AUTO_REFRESH_INTERVAL", cls.AUTO_REFRESH_INTERVAL))

# Carga inicial de configuraciones
Config.load_config()

# -------------------------------------------------------
# Clases y Tipos
# -------------------------------------------------------
class TeamMatch(TypedDict):
    local: str
    visitante: str
# -------------------------------------------------------
# Funciones Utilitarias generales
# -------------------------------------------------------
def get_image_base64(image):
    """Convierte una imagen PIL a base64"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def load_teams_database():
    """Carga la base de datos YAML de equipos"""
    try:
        yaml_path = os.path.join(os.path.dirname(__file__), Config.TEAMS_DB_PATH)
        with open(yaml_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        st.warning(f"No se pudo cargar teams database: {e}")
        return {}

def load_default_matches():
    """Proporciona partidos por defecto para pruebas"""
    return [
        {"local": "América", "visitante": "Guadalajara"},
        {"local": "Cruz Azul", "visitante": "Pumas"},
        {"local": "Monterrey", "visitante": "Tigres"},
        {"local": "Atlas", "visitante": "Toluca"},
        {"local": "Santos", "visitante": "León"},
        {"local": "Puebla", "visitante": "Tijuana"},
        {"local": "Pachuca", "visitante": "Querétaro"},
        {"local": "Necaxa", "visitante": "San Luis"},
        {"local": "Mazatlán", "visitante": "Juárez"}
    ]
# -------------------------------------------------------
# 📡 Interacción con RapidAPI
# -------------------------------------------------------
def get_football_data(endpoint: str, params: Optional[dict] = None) -> dict:
    """
    Realiza una solicitud GET a la API de fútbol mediante RapidAPI.

    Args:
        endpoint (str): Ruta del endpoint en RapidAPI.
        params (dict, opcional): Parámetros para la solicitud HTTP.

    Returns:
        dict: Respuesta en formato JSON de la API o datos simulados.
    """
    if Config.RAPIDAPI_KEY is None:
        st.warning("API Key no configurada. Respuesta simulada.")
        return simulate_api_response(endpoint, params)

    headers = {
        'x-rapidapi-key': Config.RAPIDAPI_KEY,
        'x-rapidapi-host': Config.RAPIDAPI_HOST
    }

    base_url = f"https://{Config.RAPIDAPI_HOST}{endpoint}"

    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error en solicitud a RapidAPI: {e}")
        st.error(f"Error al obtener datos de la API: {e}")
        return simulate_api_response(endpoint, params)

def simulate_api_response(endpoint: str, params: Optional[dict] = None) -> dict:
    """
    Proporciona una respuesta simulada para el desarrollo sin acceso a la API.

    Args:
        endpoint (str): Ruta del endpoint solicitado.
        params (dict, opcional): Parámetros adicionales de la consulta.

    Returns:
        dict: Respuesta simulada similar a la estructura de la API real.
    """
    logger.info(f"Simulando respuesta para el endpoint: {endpoint}")

    if "/fixtures/id/" in endpoint:
        fixture_id = endpoint.split("/")[-1]
        return {
            "fixture_id": fixture_id,
            "fixture_date": dt.now(pytz.UTC).isoformat(),
            "home_team": {"team_name": "Equipo Local"},
            "away_team": {"team_name": "Equipo Visitante"},
            "venue": "Estadio Simulado",
            "league": {"name": "Liga Simulada"},
            "status": "Programado",
            "goals_home": 0,
            "goals_away": 0
        }

    elif endpoint == "/fixtures/live":
        return {
            "fixtures": [
                {
                    "fixture_id": "12345",
                    "fixture_date": dt.now(pytz.UTC).isoformat(),
                    "home_team": {"team_name": "Equipo Local"},
                    "away_team": {"team_name": "Equipo Visitante"},
                    "status": "En Juego",
                    "goals_home": 1,
                    "goals_away": 1
                }
            ]
        }

    return {"fixtures": []}

def get_current_matches() -> dict:
    """
    Obtiene partidos que están en juego actualmente.

    Returns:
        dict: Datos de partidos en vivo.
    """
    return get_football_data("/fixtures/live")

def get_live_results(fixture_ids: List[str]) -> Dict[str, dict]:
    """
    Consulta resultados en vivo de partidos específicos.

    Args:
        fixture_ids (List[str]): IDs de partidos a consultar.

    Returns:
        Dict[str, dict]: Resultados actuales por fixture_id.
    """
    results = {}
    for fixture_id in fixture_ids:
        fixture_data = get_football_data(f"/fixtures/id/{fixture_id}")
        if fixture_data:
            results[fixture_id] = fixture_data
    return results

def convert_to_local_time(utc_time: str, local_timezone: str = Config.DEFAULT_TIMEZONE) -> str:
    """
    Convierte fecha/hora UTC a la zona horaria local del usuario.

    Args:
        utc_time (str): Fecha y hora en formato UTC (ISO8601).
        local_timezone (str, opcional): Zona horaria destino.

    Returns:
        str: Fecha y hora local formateada.
    """
    try:
        utc_dt = dt.fromisoformat(utc_time.replace("Z", "+00:00"))
        local_tz = pytz.timezone(local_timezone)
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error al convertir hora UTC a local: {e}")
        return utc_time

# ------------------------------------------------------------------

### 🔧 **Función corregida para relacionar partidos con la API**
def match_quiniela_with_api(quiniela_matches: List[TeamMatch]) -> Dict[str, str]:
    """
    Relaciona los partidos cargados de la quiniela con fixtures de la API.

    Args:
        quiniela_matches (List[TeamMatch]): Partidos extraídos de la quiniela.

    Returns:
        Dict[str, str]: Diccionario con el nombre del partido como clave y el ID del fixture como valor.
    """
    matched_fixtures = {}
    current_date = dt.now().strftime("%Y-%m-%d")
    fixtures_data = get_football_data("/fixtures/date/current")

    if not fixtures_data or 'fixtures' not in fixtures_data:
        logger.warning("No se obtuvieron fixtures actuales de la API.")
        return matched_fixtures

    fixtures = fixtures_data['fixtures']

    for quiniela_match in quiniela_matches:
        local_team = quiniela_match["local"].lower()
        away_team = quiniela_match["visitante"].lower()

        for fixture in fixtures:
            api_home = fixture.get("home_team", {}).get("team_name", "").lower()
            api_away = fixture.get("away_team", {}).get("team_name", "").lower()

            home_similarity = calculate_similarity(local_team, api_home)
            away_similarity = calculate_similarity(visitante_team, api_away)

            if home_similarity > 0.7 and away_similarity > 0.7:
                fixture_id = fixture.get("fixture_id")
                match_name = f"{quiniela_match['local']} vs {quiniela_match['visitante']}"
                matched_fixtures[match_name] = fixture_id
                break

    return matched_fixtures
def scrape_progol_info() -> List[TeamMatch]:
    """
    Realiza web scraping en 'alegrialoteria.com' para obtener los partidos de Progol.

    Returns:
        List[TeamMatch]: Lista con partidos obtenidos desde la web.
    """
    url = "https://alegrialoteria.com/Progol"
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        partidos = []

        # Adaptar los selectores de acuerdo al HTML real (verificado)
        for partido in soup.select('table tr'):
            columnas = partido.select('td')
            if len(columnas) >= 3:
                local = columnas[0].get_text(strip=True)
                vs = columnas[1].get_text(strip=True).lower()
                visitante = columnas[2].get_text(strip=True)
                if 'vs' in vs.lower():
                    partidos.append({"local": local, "visitante": visitante})

        if not partidos:
            logger.warning("No se encontraron partidos con scraping estándar.")
        return partidos

    except requests.RequestException as e:
        logger.error(f"Error durante scraping de Progol: {e}")
        return []
def process_quiniela_image(image: Image.Image) -> List[TeamMatch]:
    """
    Realiza OCR básico para extraer partidos desde una imagen subida.

    Args:
        image (PIL.Image): Imagen cargada desde Streamlit.

    Returns:
        List[TeamMatch]: Lista de partidos detectados en la imagen.
    """
    try:
        import pytesseract
        from pytesseract import Output
    except ImportError:
        st.error("pytesseract no está instalado.")
        return []

    image_gray = ImageOps.grayscale(image)
    enhanced = ImageEnhance.Contrast(image_gray).enhance(2.0)

    # Realizar OCR
    text = pytesseract.image_to_string(enhanced, lang='spa')

    st.text_area("Texto extraído de la imagen (para debug)", text, height=200)

    # Procesar texto extraído (simplificado para demostración)
    lines = text.split('\n')
    partidos = []
    pattern = re.compile(r'(\w.+?)\s+vs\s+(\w.+)', re.IGNORECASE)

    for line in lines:
        match = pattern.search(line)
        if match:
            partidos.append({
                "local": match.group(1).strip(),
                "visitante": match.group(2).strip()
            })

    if not partidos:
        st.warning("No se pudieron detectar partidos automáticamente.")
    else:
        st.success(f"Se detectaron {len(partidos)} partidos mediante OCR.")

    return partidos
def main():
    """
    Función principal que ejecuta la aplicación Streamlit.
    """
    st.title("📊 Seguimiento de Quiniela Progol")
    Config.load_config()

    # Sidebar (Configuración)
    st.sidebar.title("⚙️ Configuración")
    selected_timezone = st.sidebar.selectbox(
        "Selecciona tu zona horaria:",
        pytz.all_timezones,
        index=pytz.all_timezones.index(Config.DEFAULT_TIMEZONE)
    )

    st.sidebar.info(f"Versión: {APP_VERSION}")

    # Inicialización de estado
    if 'quiniela_matches' not in st.session_state:
        st.session_state.quiniela_matches = []
    if 'fixtures_data' not in st.session_state:
        st.session_state.fixtures_data = []
    if 'results_data' not in st.session_state:
        st.session_state.results_data = []

    # Pestañas
    tab1, tab2, tab3 = st.tabs(["Cargar Quiniela", "Partidos y Horarios", "Resultados en Vivo"])

    # Tab 1: Cargar Quiniela
    with tab1:
        st.header("Cargar Quiniela")
        method = st.radio("Elige método:", ["Imagen (OCR)", "Selección Manual", "Web Scraping"])

        if method == "Imagen (OCR)":
            uploaded_file = st.file_uploader("Sube imagen", type=['png', 'jpg', 'jpeg'])
            if uploaded_file and st.button("Procesar Imagen"):
                image = Image.open(uploaded_file)
                st.image(image, caption="Quiniela cargada", width=400)
                matches = process_quiniela_image(image)
                st.session_state.quiniela_matches = matches

        elif method == "Selección Manual":
            matches = extract_teams_from_structure(None)
            st.session_state.quiniela_matches = matches

        else:
            if st.button("Obtener Quiniela Progol"):
                matches = scrape_progol_info()
                if matches:
                    st.session_state.quiniela_matches = matches
                    st.success("Quiniela obtenida correctamente.")
                else:
                    st.warning("No se pudieron obtener los datos desde la web.")

        # Mostrar partidos cargados
        if st.session_state.quiniela_matches:
            st.subheader("Partidos registrados:")
            for match in st.session_state.quiniela_matches:
                st.write(f"- {match['local']} vs {match['visitante']}")

    # Tab 2: Partidos y Horarios
    with tab2:
        st.header("Partidos y Horarios")
        if st.button("Actualizar Horarios"):
            with st.spinner("Actualizando..."):
                matched = match_quiniela_with_api(st.session_state.quiniela_matches)
                fixtures_data = []
                for partido, fixture_id in matched_fixtures.items():
                    fixture_info = get_football_data(f"/fixtures/id/{fixture_id}")
                    utc_time = fixture_info.get("fixture_date", "")
                    local_time = convert_to_local_time(utc_time, selected_timezone)
                    fixtures_data.append({
                        "Partido": partido,
                        "Fecha y hora local": local_time,
                        "Estadio": fixture_info.get("venue", "N/D"),
                        "Liga": fixture_info.get("league", {}).get("name", ""),
                        "Fixture ID": fixture_id
                    })
                st.session_state.fixtures_data = fixtures_data
                st.dataframe(pd.DataFrame(fixtures_data))

    # Tab 3: Resultados en Vivo
    with tab3:
        st.header("Resultados en Vivo")
        if st.button("Actualizar resultados"):
            fixture_ids = [f["Fixture ID"] for f in st.session_state.fixtures_data]
            live_results = get_live_results(fixture_ids)
            results_data = []
            for f in st.session_state.fixtures_data:
                result = live_results.get(f["Fixture ID"], {})
                results_data.append({
                    "Partido": f["Partido"],
                    "Estado": result.get("status", "Sin datos"),
                    "Marcador": f"{result.get('goals_home', 0)} - {result.get('goals_away', 0)}",
                    "Última Actualización": dt.now().strftime("%H:%M:%S")
                })
            st.session_state.results_data = results_data
            st.dataframe(pd.DataFrame(results_data))
