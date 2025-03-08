"""
Aplicación Streamlit para seguimiento de quinielas Progol.
Permite cargar quinielas, obtener horarios de partidos y seguir resultados en tiempo real.
"""
import streamlit as st
import numpy as np
import pandas as pd
import requests
import yaml
import os
import io
import logging
import sys
import re
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from datetime import datetime
from typing import Dict, List, Optional, TypedDict, Union, Any
import pytz
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import base64
import time

# -------------------------------------------------------
# Configuración inicial
# -------------------------------------------------------

# Configuración de la página
st.set_page_config(
    page_title="Seguimiento Quiniela Progol",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Versión de la aplicación
APP_VERSION = "1.0.2"

# Disponibilidad condicional de CV2
CV2_AVAILABLE = False
try:
    import cv2
    CV2_AVAILABLE = True
    logger.info("OpenCV está disponible")
except ImportError:
    logger.warning("OpenCV no está disponible, usando alternativas")
    
# -------------------------------------------------------
# Clases y tipos
# -------------------------------------------------------

# Definición de tipos para equipos de fútbol
class TeamMatch(TypedDict):
    local: str
    visitante: str

class Config:
    """Centraliza la configuración de la aplicación"""
    # API RapidAPI
    RAPIDAPI_KEY = None
    RAPIDAPI_HOST = "free-api-live-football-data.p.rapidapi.com"
    
    # Configuración de la aplicación
    DEFAULT_TIMEZONE = "America/Mexico_City"
    AUTO_REFRESH_INTERVAL = 300  # en segundos
    
    # Rutas
    TEAMS_DB_PATH = "teams_database.yaml"
    
    @classmethod
    def load_from_secrets(cls):
        """Carga configuración desde secrets de Streamlit"""
        try:
            if 'general' in st.secrets:
                if 'RAPIDAPI_KEY' in st.secrets:
                    cls.RAPIDAPI_KEY = st.secrets["RAPIDAPI_KEY"]
                elif 'general' in st.secrets and 'RAPIDAPI_KEY' in st.secrets.general:
                    cls.RAPIDAPI_KEY = st.secrets.general["RAPIDAPI_KEY"]
                    
                if 'RAPIDAPI_HOST' in st.secrets.general:
                    cls.RAPIDAPI_HOST = st.secrets.general["RAPIDAPI_HOST"]
                    
            if 'config' in st.secrets:
                if 'default_timezone' in st.secrets.config:
                    cls.DEFAULT_TIMEZONE = st.secrets.config["default_timezone"]
                if 'auto_refresh_interval' in st.secrets.config:
                    cls.AUTO_REFRESH_INTERVAL = int(st.secrets.config["auto_refresh_interval"])
        except Exception as e:
            logger.warning(f"Error cargando secrets: {e}")
            
    @classmethod
    def load_from_env(cls):
        """Carga configuración desde variables de entorno"""
        try:
            load_dotenv()
            cls.RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", cls.RAPIDAPI_KEY)
            cls.RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", cls.RAPIDAPI_HOST)
            cls.DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", cls.DEFAULT_TIMEZONE)
            cls.AUTO_REFRESH_INTERVAL = int(os.getenv("AUTO_REFRESH_INTERVAL", cls.AUTO_REFRESH_INTERVAL))
        except Exception as e:
            logger.warning(f"Error cargando variables de entorno: {e}")

# -------------------------------------------------------
# Funciones utilitarias
# -------------------------------------------------------

# Función para codificar imágenes en base64 para mostrar en HTML
def get_image_base64(image):
    """Convierte una imagen PIL a string base64"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def load_teams_database():
    """
    Carga la base de datos de equipos desde un archivo YAML o crea una por defecto.
    
    Returns:
        dict: Diccionario con equipos y sus posibles variaciones de nombre.
    """
    # Intentar cargar desde un archivo si existe
    try:
        yaml_path = os.path.join(os.path.dirname(__file__), Config.TEAMS_DB_PATH)
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
    except Exception as e:
        st.warning(f"No se pudo cargar la base de datos de equipos: {str(e)}")
    
    # Base de datos predeterminada de equipos mexicanos con variaciones de nombre
    return {
        "america": ["América", "Club América", "Aguilas", "Águilas del América"],
        "guadalajara": ["Guadalajara", "Chivas", "Chivas Rayadas", "Club Deportivo Guadalajara"],
        "cruzazul": ["Cruz Azul", "La Máquina", "La Maquina Celeste"],
        "pumas": ["Pumas", "UNAM", "Universidad", "Pumas UNAM"],
        "monterrey": ["Monterrey", "Rayados", "Club de Futbol Monterrey"],
        "tigres": ["Tigres", "UANL", "Tigres UANL"],
        "atlas": ["Atlas", "Rojinegros", "Atlas FC"],
        "toluca": ["Toluca", "Diablos Rojos", "Deportivo Toluca"],
        "santos": ["Santos", "Santos Laguna", "Guerreros"],
        "leon": ["León", "Leon", "Club León", "La Fiera"],
        "puebla": ["Puebla", "Camoteros", "Club Puebla"],
        "tijuana": ["Tijuana", "Xolos", "Xoloitzcuintles"],
        "pachuca": ["Pachuca", "Tuzos", "Club Pachuca"],
        "queretaro": ["Querétaro", "Queretaro", "Gallos Blancos"],
        "necaxa": ["Necaxa", "Rayos", "Club Necaxa"],
        "sanluis": ["San Luis", "Atlético San Luis", "Atletico San Luis"],
        "mazatlan": ["Mazatlán", "Mazatlan FC", "Mazatlan"],
        "juarez": ["Juárez", "Juarez", "FC Juárez", "Bravos de Juárez"]
    }

def load_default_matches():
    """
    Carga una lista predeterminada de partidos para demostración.
    
    Returns:
        list: Lista de partidos de demostración.
    """
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
# Funciones de procesamiento de imágenes
# -------------------------------------------------------

def process_quiniela_image(image):
    """
    Procesa una imagen de quiniela utilizando Pillow y/o OpenCV si está disponible.
    
    Args:
        image: Imagen en formato PIL o bytes.
        
    Returns:
        list: Lista de partidos extraídos de la quiniela.
    """
    if isinstance(image, bytes):
        image = Image.open(io.BytesIO(image))
    
    # Preprocesamiento de la imagen para mejorar resultados
    processed_image = None
    try:
        # Convertir a escala de grises
        image_gray = ImageOps.grayscale(image)
        
        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(image_gray)
        enhanced_image = enhancer.enhance(2.0)
        
        # Aplicar filtro para mejorar detalles
        filtered_image = enhanced_image.filter(ImageFilter.SHARPEN)
        processed_image = filtered_image
        
        # Mostrar la imagen procesada
        st.image(filtered_image, caption="Imagen procesada", use_column_width=True, width=400)
        
        # Si OpenCV está disponible, intentar procesamiento adicional
        if CV2_AVAILABLE:
            try:
                # Convertir imagen PIL a formato CV2
                cv2_image = np.array(filtered_image)
                
                # Aplicar umbral adaptativo para mejorar bordes y texto
                _, thresholded = cv2.threshold(cv2_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                
                # Mostrar resultados del procesamiento con OpenCV
                st.image(thresholded, caption="Procesado con OpenCV", use_column_width=True, width=400)
                processed_image = Image.fromarray(thresholded)
            except Exception as e:
                st.warning(f"No se pudo procesar con OpenCV: {str(e)}")
        
        # Para esta demostración, usamos la interfaz manual con una lista predefinida
        return extract_teams_from_structure(processed_image or filtered_image)
    
    except Exception as e:
        st.error(f"Error al procesar la imagen: {str(e)}")
        logger.exception("Error procesando imagen")
        return []

def extract_teams_from_structure(image):
    """
    Extrae equipos de la imagen basándose en la estructura típica de una quiniela.
    Implementa un formulario interactivo para selección de equipos.
    
    Args:
        image: Imagen PIL procesada.
        
    Returns:
        list: Lista de partidos encontrados.
    """
    # Cargar la base de datos de equipos
    teams_db = load_teams_database()
    
    # Para esta demostración, ofrecemos al usuario seleccionar equipos
    # de una lista predefinida, simulando lo que haría un sistema de reconocimiento
    
    st.write("### Selecciona los equipos que aparecen en tu quiniela")
    
    matches = []
    
    # Agregar imagen de referencia en la barra lateral
    if image is not None:
        with st.sidebar:
            st.write("### Imagen de referencia")
            st.image(image, use_column_width=True, width=300)
    
    # Crear una columna lateral para ayudar al usuario
    with st.expander("📋 Instrucciones"):
        st.write("""
        1. Selecciona el equipo local y visitante para cada partido
        2. Si un partido no aparece en la quiniela, deja ambos campos vacíos
        3. Cuando termines, presiona el botón "Confirmar Partidos" 
        4. Los partidos se guardarán automáticamente
        """)
    
    # Crear hasta 9 partidos (típico en quinielas Progol)
    container = st.container()
    total_matches_selected = 0
    
    # Crear una cuadrícula para los partidos
    num_columns = 3
    max_rows = 3 
    
    for row in range(max_rows):
        cols = st.columns(num_columns)
        for col_idx in range(num_columns):
            i = row * num_columns + col_idx
            with cols[col_idx]:
                st.write(f"#### Partido {i+1}")
                
                # Convertir diccionario a lista plana de nombres de equipos
                all_team_names = []
                for variations in teams_db.values():
                    all_team_names.extend(variations)
                
                # Ordenar alfabéticamente para facilitar la búsqueda
                all_team_names.sort()
                
                local_team = st.selectbox(
                    "Equipo Local:",
                    [""] + all_team_names,
                    key=f"local_{i}"
                )
                
                # Filtrar para no mostrar el mismo equipo como visitante
                filtered_teams = [""] + [team for team in all_team_names if team != local_team]
                
                away_team = st.selectbox(
                    "Equipo Visitante:",
                    filtered_teams,
                    key=f"away_{i}"
                )
                
                # Solo agregar si ambos equipos fueron seleccionados
                if local_team and away_team:
                    matches.append({"local": local_team, "visitante": away_team})
                    total_matches_selected += 1
    
    # Botón para confirmar la selección
    if total_matches_selected > 0:
        confirm_text = f"Confirmar {total_matches_selected} Partidos"
    else:
        confirm_text = "No hay partidos seleccionados"
    
    if st.button(confirm_text, disabled=total_matches_selected == 0):
        st.success(f"Se han registrado {len(matches)} partidos correctamente")
    
    return matches

# -------------------------------------------------------
# Funciones de scraping y web
# -------------------------------------------------------

def scrape_progol_info():
    """
    Obtiene la información de la quiniela Progol mediante web scraping.
    
    Returns:
        list: Lista de partidos de la quiniela actual.
    """
    try:
        url = "https://alegrialoteria.com/Progol"
        response = requests.get(url)
        if response.status_code != 200:
            st.error("No se pudo obtener la información de la quiniela Progol")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Obtener los partidos de la quiniela
        matches = []
        
        # Este código necesitará ser ajustado según la estructura HTML de la página
        match_elements = soup.select('.partido')  # Selector CSS a ajustar
        
        for element in match_elements:
            try:
                home_team = element.select_one('.local').text.strip()
                away_team = element.select_one('.visitante').text.strip()
                matches.append({"local": home_team, "visitante": away_team})
            except AttributeError:
                continue
        
        if not matches:
            # Intento alternativo de scraping si el primer método falla
            table_elements = soup.select('table')
            for table in table_elements:
                rows = table.select('tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 3:  # Patrón típico: Local | vs | Visitante
                        try:
                            home_team = cells[0].text.strip()
                            away_team = cells[2].text.strip()
                            if home_team and away_team and "vs" in cells[1].text.strip().lower():
                                matches.append({"local": home_team, "visitante": away_team})
                        except (IndexError, AttributeError):
                            continue
        
        return matches
    except Exception as e:
        logger.exception(f"Error al scrapear datos de Progol: {str(e)}")
        st.error(f"Error al scrapear datos de Progol: {str(e)}")
        return []

# -------------------------------------------------------
# Funciones de API y datos
# -------------------------------------------------------

def get_football_data(endpoint, params=None):
    """
    Realiza una petición a la API de fútbol.
    
    Args:
        endpoint (str): Ruta del endpoint a consultar.
        params (dict, optional): Parámetros opcionales para la consulta.
        
    Returns:
        dict: Datos obtenidos de la API en formato JSON.
    """
    if Config.RAPIDAPI_KEY is None:
        st.warning("No se ha configurado la API Key de RapidAPI. Los datos serán simulados.")
        return simulate_api_response(endpoint, params)
    
    headers = {
        'x-rapidapi-key': Config.RAPIDAPI_KEY,
        'x-rapidapi-host': Config.RAPIDAPI_HOST
    }
    
    query_string = ""
    if params:
        query_string = "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    
    try:
        full_endpoint = f"https://{Config.RAPIDAPI_HOST}{endpoint}{query_string}"
        response = requests.get(full_endpoint, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Error API ({response.status_code}): {response.text}")
            st.error(f"Error al obtener datos: Código {response.status_code}")
            return simulate_api_response(endpoint, params)
        
        return response.json()
    except Exception as e:
        logger.exception(f"Error al obtener datos: {str(e)}")
        st.error(f"Error al obtener datos: {str(e)}")
        return simulate_api_response(endpoint, params)

def simulate_api_response(endpoint, params=None):
    """
    Simula una respuesta de la API para desarrollo y demostración
    
    Args:
        endpoint (str): Ruta del endpoint solicitado
        params (dict, optional): Parámetros de la consulta
        
    Returns:
        dict: Datos simulados en formato similar a la API
    """
    logger.info(f"Simulando respuesta para: {endpoint}")
    
    # Simulación de respuesta para fixture_id
    if endpoint.startswith("/fixtures/id/"):
        fixture_id = endpoint.split("/")[-1]
        return {
            "fixture_id": fixture_id,
            "fixture_date": datetime.now().isoformat(),
            "home_team": "Equipo Local",
            "away_team": "Equipo Visitante",
            "venue": "Estadio Simulado",
            "league": {"name": "Liga Simulada"},
            "status": "Programado",
            "goals_home": 0,
            "goals_away": 0
        }
    
    # Simulación de respuesta para partidos en vivo
    if endpoint == "/fixtures/live":
        return {
            "fixtures": [
                {
                    "fixture_id": "12345",
                    "fixture_date": datetime.now().isoformat(),
                    "home_team": "Equipo Local",
                    "away_team": "Equipo Visitante",
                    "status": "En Juego",
                    "goals_home": 1,
                    "goals_away": 1
                }
            ]
        }
    
    # Simulación genérica para otros endpoints
    return {
        "fixtures": [
            {
                "fixture_id": "12345",
                "fixture_date": datetime.now().isoformat(),
                "home_team": "Equipo Local",
                "away_team": "Equipo Visitante",
                "venue": "Estadio Simulado",
                "league": {"name": "Liga Simulada"}
            }
        ]
    }

def get_current_matches():
    """
    Obtiene los partidos actuales (próximos y en juego).
    
    Returns:
        dict: Información de los partidos actuales.
    """
    # Esta función dependerá de los endpoints específicos disponibles en la API
    # Por ahora usamos un endpoint genérico para partidos en vivo
    return get_football_data("/fixtures/live")

def get_live_results(fixture_ids):
    """
    Obtiene los resultados en tiempo real de los partidos especificados.
    
    Args:
        fixture_ids (list): Lista de IDs de los partidos a consultar.
        
    Returns:
        dict: Resultados de los partidos.
    """
    results = {}
    
    for fixture_id in fixture_ids:
        fixture_data = get_football_data(f"/fixtures/id/{fixture_id}")
        if fixture_data:
            results[fixture_id] = fixture_data
    
    return results

def convert_to_local_time(utc_time, local_timezone):
    """
    Convierte una hora UTC a la zona horaria local del usuario.
    
    Args:
        utc_time (str): Hora en formato UTC.
        local_timezone (str): Zona horaria local del usuario.
        
    Returns:
        str: Hora convertida a la zona horaria local.
    """
    try:
        # Manejar formatos de fecha ISO diferentes
        # Algunos pueden venir con la 'Z' al final para indicar UTC
        if utc_time.endswith('Z'):
            utc_time = utc_time[:-1] + "+00:00"
        # Si no tiene información de zona horaria, asumimos UTC
        elif not ('+' in utc_time or '-' in utc_time[-6:]):
            utc_time = utc_time + "+00:00"
            
        try:
            utc_dt = datetime.fromisoformat(utc_time)
        except ValueError:
            # Intentar otro formato común si el primero falla
            utc_dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%S%z")
            
        # Convertir a la zona horaria solicitada
        local_tz = pytz.timezone(local_timezone)
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=pytz.UTC)
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error al convertir zona horaria: {str(e)}")
        return utc_time

def match_quiniela_with_api(quiniela_matches):
    """
    Relaciona los partidos de la quiniela con los datos de la API.
    
    Args:
        quiniela_matches (list): Lista de partidos extraídos de la quiniela.
        
    Returns:
        dict: Partidos de la quiniela relacionados con IDs de fixture de la API.
    """
    matched_fixtures = {}
    
    # Obtener partidos de la semana actual
    # Necesitamos ajustar este endpoint según la documentación de la API
    current_fixtures = get_football_data("/fixtures/date/current")
    
    if not current_fixtures or 'fixtures' not in current_fixtures:
        return matched_fixtures
    
    for quiniela_match in quiniela_matches:
        local_team = quiniela_match["local"].lower()
        visitante_team = quiniela_match["visitante"].lower()
        
        # Buscar coincidencias en los fixtures
        for fixture in current_fixtures.get("fixtures", []):
            api_home = fixture.get("home_team", "").lower()
            api_away = fixture.get("away_team", "").lower()
            
            # Calcular similitud entre nombres
            home_similarity = calculate_similarity(local_team, api_home)
            away_similarity = calculate_similarity(visitante_team, api_away)
            
            # Si hay suficiente similitud, consideramos que es el mismo partido
            if home_similarity > 0.7 and away_similarity > 0.7:
                fixture_id = fixture.get("fixture_id")
                matched_fixtures[f"{local_team} vs {visitante_team}"] = fixture_id
    
    return matched_fixtures

def calculate_similarity(str1, str2):
    """
    Calcula la similitud entre dos cadenas usando la distancia de Levenshtein.
    
    Args:
        str1 (str): Primera cadena.
        str2 (str): Segunda cadena.
        
    Returns:
        float: Valor de similitud entre 0 y 1.
    """
    from difflib import SequenceMatcher
    return SequenceMatcher(None, str1, str2).ratio()

# -------------------------------------------------------
# Función principal
# -------------------------------------------------------

def main():
    """
    Función principal que ejecuta la aplicación Streamlit.
    """
    # Inicializar configuración
    Config.load_from_secrets()
    Config.load_from_env()
    
    st.title("📊 Seguimiento de Quiniela Progol")
    
    # Sidebar para opciones de configuración
    st.sidebar.title("⚙️ Configuración")
    
    # Selección de zona horaria
    timezones = pytz.all_timezones
    default_tz = Config.DEFAULT_TIMEZONE
    selected_timezone = st.sidebar.selectbox(
        "Selecciona tu zona horaria:",
        timezones,
        index=timezones.index(default_tz) if default_tz in timezones else 0
    )
    
    # Mostrar versión de la aplicación
    st.sidebar.info(f"Versión: {APP_VERSION}")
    
    # Inicializar session_state para almacenar partidos
    if 'quiniela_matches' not in st.session_state:
        st.session_state.quiniela_matches = []
    
    # Tabs para organizar la interfaz
    tab1, tab2, tab3 = st.tabs(["Cargar Quiniela", "Partidos y Horarios", "Resultados en Vivo"])
    
    # Tab 1: Cargar Quiniela
    with tab1:
        st.header("Cargar Quiniela")
        
        upload_method = st.radio(
            "Método para obtener la quiniela:",
            ["Cargar imagen", "Selección manual", "Obtener automáticamente de la web"]
        )
        
        quiniela_matches = []
        
        if upload_method == "Cargar imagen":
            uploaded_file = st.file_uploader("Sube la imagen de tu quiniela", type=["jpg", "jpeg", "png"])
            
            if uploaded_file is not None:
                # Manejar distintos formatos de imagen
                try:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Imagen cargada", use_column_width=True, width=400)
                
                    if st.button("Procesar Quiniela"):
                        with st.spinner("Procesando imagen..."):
                            quiniela_matches = process_quiniela_image(image)
                            
                            if quiniela_matches:
                                st.session_state.quiniela_matches = quiniela_matches
                            else:
                                st.warning("No se detectaron partidos automáticamente. Utiliza la opción 'Selección manual'.")
                except Exception as e:
                    st.error(f"Error al procesar la imagen: {str(e)}")
                    st.info("Por favor, sube una imagen en formato JPG, PNG o JPEG válido.")
        
        elif upload_method == "Selección manual":
            # La función actual muestra un formulario para selección manual
            st.write("Selecciona los equipos de la quiniela manualmente:")
            quiniela_matches = extract_teams_from_structure(None)
            
            if quiniela_matches:
                st.session_state.quiniela_matches = quiniela_matches
        
        else:  # Obtener automáticamente
            if st.button("Obtener Quiniela de Progol"):
                with st.spinner("Descargando información..."):
                    quiniela_matches = scrape_progol_info()
                    
                    if quiniela_matches:
                        st.success(f"Se obtuvieron {len(quiniela_matches)} partidos de la quiniela Progol")
                        
                        # Mostrar los partidos encontrados
                        st.subheader("Partidos de la quiniela:")
                        for i, match in enumerate(quiniela_matches):
                            st.write(f"{i+1}. {match['local']} vs {match['visitante']}")
                        
                        # Guardar en session state
                        st.session_state.quiniela_matches = quiniela_matches
                    else:
                        st.error("No se pudo obtener la información de la quiniela.")
                        
                        # Cargar partidos de demostración
                        if st.button("Usar partidos de demostración"):
                            st.session_state.quiniela_matches = load_default_matches()
                            st.success("Se han cargado partidos de demostración.")
        
        # Mostrar los partidos actuales en session_state
        if st.session_state.quiniela_matches:
            st.subheader("Partidos registrados:")
            for i, match in enumerate(st.session_state.quiniela_matches):
                st.write(f"{i+1}. {match['local']} vs {match['visitante']}")
    
    # Tab 2: Partidos y Horarios
    with tab2:
        st.header("Partidos y Horarios")
        
        if st.button("Actualizar Horarios"):
            with st.spinner("Obteniendo horarios de partidos..."):
                # Verificar si hay partidos en session state
                if st.session_state.quiniela_matches:
                    # Relacionar partidos de la quiniela con la API
                    matched_fixtures = match_quiniela_with_api(st.session_state.quiniela_matches)
                    
                    if matched_fixtures:
                        st.success(f"Se relacionaron {len(matched_fixtures)} partidos con la API")
                        
                        # Obtener detalles de cada partido
                        fixtures_data = []
                        
                        for match_name, fixture_id in matched_fixtures.items():
                            fixture_details = get_football_data(f"/fixtures/id/{fixture_id}")
                            
                            if fixture_details:
                                # Obtener y convertir horario
                                utc_time = fixture_details.get("fixture_date", "")
                                local_time = convert_to_local_time(utc_time, selected_timezone)
                                
                                fixtures_data.append({
                                    "Partido": match_name,
                                    "Fecha (Local)": local_time.split()[0],
                                    "Hora (Local)": local_time.split()[1],
                                    "Estadio": fixture_details.get("venue", ""),
                                    "Liga": fixture_details.get("league", {}).get("name", ""),
                                    "ID_Fixture": fixture_id
                                })
                        
                        # Guardar en session state
                        st.session_state.fixtures_data = fixtures_data
                        
                        # Mostrar tabla de partidos
                        if fixtures_data:
                            df = pd.DataFrame(fixtures_data)
                            st.dataframe(df)
                        else:
                            st.warning("No se pudieron obtener detalles de los partidos.")
                    else:
                        st.warning("No se pudieron relacionar los partidos de la quiniela con la API.")
                else:
                    st.warning("Primero debes cargar una quiniela en la pestaña 'Cargar Quiniela'.")
        
        # Mostrar datos guardados si existen
        if 'fixtures_data' in st.session_state and st.session_state.fixtures_data:
            df = pd.DataFrame(st.session_state.fixtures_data)
            st.dataframe(df)
    
    # Tab 3: Resultados en Vivo
    with tab3:
        st.header("Resultados en Vivo")
        
        if st.button("Actualizar Resultados"):
            with st.spinner("Obteniendo resultados en vivo..."):
                # Verificar si hay fixtures en session state
                if 'fixtures_data' in st.session_state and st.session_state.fixtures_data:
                    fixture_ids = [item["ID_Fixture"] for item in st.session_state.fixtures_data]
                    
                    # Obtener resultados en vivo
                    live_results = get_live_results(fixture_ids)
                    
                    if live_results:
                        # Preparar datos para mostrar
                        results_data = []
                        
                        for match_data in st.session_state.fixtures_data:
                            fixture_id = match_data["ID_Fixture"]
                            match_name = match_data["Partido"]
                            
                            if fixture_id in live_results:
                                fixture_result = live_results[fixture_id]
                                
                                # Extraer información relevante
                                status = fixture_result.get("status", "No iniciado")
                                home_score = fixture_result.get("goals_home", 0)
                                away_score = fixture_result.get("goals_away", 0)
                                
                                results_data.append({
                                    "Partido": match_name,
                                    "Estado": status,
                                    "Marcador": f"{home_score} - {away_score}",
                                    "Última Actualización": datetime.now().strftime("%H:%M:%S")
                                })
                            else:
                                results_data.append({
                                    "Partido": match_name,
                                    "Estado": "Sin datos",
                                    "Marcador": "- - -",
                                    "Última Actualización": "-"
                                })
                        
                        # Guardar en session state
                        st.session_state.results_data = results_data
                        
                        # Mostrar resultados
                        if results_data:
                            df = pd.DataFrame(results_data)
                            st.dataframe(df)
                        else:
                            st.warning("No hay resultados disponibles.")
                    else:
                        st.warning("No se pudieron obtener resultados en vivo.")
                else:
                    st.warning("Primero debes cargar una quiniela y obtener los horarios.")
        
        # Mostrar datos guardados si existen
        if 'results_data' in st.session_state and st.session_state.results_data:
            df = pd.DataFrame(st.session_state.results_data)
            st.dataframe(df)
            
            # Opción para actualización automática
            auto_refresh = st.checkbox("Actualizar automáticamente cada 5 minutos")
            
            if auto_refresh:
                st.info("La actualización automática está habilitada. Los resultados se actualizarán cada 5 minutos.")
                st.success(f"Próxima actualización en {Config.AUTO_REFRESH_INTERVAL//60} minutos.")
                time_placeholder = st.empty()
                with time_placeholder:
                    countdown = Config.AUTO_REFRESH_INTERVAL
                    while countdown > 0 and auto_refresh:
                        minutes, seconds = divmod(countdown, 60)
                        time_placeholder.info(f"Próxima actualización en: {minutes:02d}:{seconds:02d}")
                        time.sleep(1)
                        countdown -= 1
                        if countdown <= 0:
                            st.experimental_rerun()

# Iniciar configuración
Config.load_from_secrets()
Config.load_from_env()

# Ejecutar la aplicación
if __name__ == "__main__":
    try:
        # Mostrar versión de la aplicación
        print(f"Iniciando Quiniela Progol v{APP_VERSION}")
        main()
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
        logger.exception("Error no controlado en la aplicación:")