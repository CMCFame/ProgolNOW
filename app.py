import streamlit as st
import http.client
import json
import pytz
from datetime import datetime
import pandas as pd
import requests
from PIL import Image
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import io
import yaml
import os
import sys
from dotenv import load_dotenv
from typing_extensions import TypedDict

# Importación condicional de pdf2image para mayor compatibilidad
try:
    import pdf2image
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("pdf2image no está disponible. No se podrán procesar archivos PDF.")

import re
import io
import os
from bs4 import BeautifulSoup
import time

# Configuración inicial de la página
st.set_page_config(
    page_title="Seguimiento Quiniela Progol",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Módulo de configuración y manejo de secretos
def load_api_credentials():
    """
    Carga las credenciales de la API desde los secretos de Streamlit.
    
    Returns:
        dict: Diccionario con las credenciales de la API.
    """
    rapid_api_key = st.secrets["RAPIDAPI_KEY"]
    rapid_api_host = "free-api-live-football-data.p.rapidapi.com"
    
    credentials = {
        "key": rapid_api_key,
        "host": rapid_api_host
    }
    
    return credentials

# Módulo para comunicarse con la API de fútbol
def get_football_data(endpoint, params=None):
    """
    Realiza una petición a la API de fútbol.
    
    Args:
        endpoint (str): Ruta del endpoint a consultar.
        params (dict, optional): Parámetros opcionales para la consulta.
        
    Returns:
        dict: Datos obtenidos de la API en formato JSON.
    """
    credentials = load_api_credentials()
    
    conn = http.client.HTTPSConnection(credentials["host"])
    
    headers = {
        'x-rapidapi-key': credentials["key"],
        'x-rapidapi-host': credentials["host"]
    }
    
    query_string = ""
    if params:
        query_string = "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    
    try:
        conn.request("GET", f"{endpoint}{query_string}", headers=headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        st.error(f"Error al obtener datos: {str(e)}")
        return None

# Módulo para obtener los partidos actuales (próximos y en juego)
def get_current_matches():
    """
    Obtiene los partidos actuales (próximos y en juego).
    
    Returns:
        dict: Información de los partidos actuales.
    """
    # Esta función dependerá de los endpoints específicos disponibles en la API
    # Por ahora usamos un endpoint genérico para partidos en vivo
    return get_football_data("/fixtures/live")

# Módulo para obtener los resultados en tiempo real
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

# Módulo para manejar la zona horaria
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
        utc_dt = datetime.fromisoformat(utc_time.replace('Z', '+00:00'))
        local_tz = pytz.timezone(local_timezone)
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        st.error(f"Error al convertir zona horaria: {str(e)}")
        return utc_time

# Definición de tipos para equipos de fútbol
class TeamMatch(TypedDict):
    local: str
    visitante: str

# Base de datos local de equipos para reconocimiento
def load_teams_database():
    """
    Carga la base de datos de equipos desde un archivo YAML o crea una por defecto.
    
    Returns:
        dict: Diccionario con equipos y sus posibles variaciones de nombre.
    """
    # Intentar cargar desde un archivo si existe
    try:
        if os.path.exists('teams_database.yaml'):
            with open('teams_database.yaml', 'r', encoding='utf-8') as file:
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

# Módulo para procesar la imagen de la quiniela
def process_quiniela_image(image):
    """
    Procesa una imagen de quiniela utilizando técnicas básicas de procesamiento de imágenes
    y reconocimiento basado en plantillas.
    
    Args:
        image: Imagen en formato PIL o bytes.
        
    Returns:
        list: Lista de partidos extraídos de la quiniela.
    """
    if isinstance(image, bytes):
        image = Image.open(io.BytesIO(image))
    
    # Preprocesamiento de la imagen para mejorar resultados
    try:
        # Convertir a escala de grises
        image = ImageOps.grayscale(image)
        
        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Aplicar filtro para mejorar detalles
        image = image.filter(ImageFilter.SHARPEN)
        
        # Mostrar la imagen procesada
        st.image(image, caption="Imagen procesada", use_column_width=True, width=400)
        
        # Extraer características de la imagen (zonas de texto)
        # Este es un método simple; en una implementación real,
        # se usarían técnicas más avanzadas
        
        # Para demostración, usamos un enfoque basado en reglas con equipos conocidos
        return extract_teams_from_structure(image)
    
    except Exception as e:
        st.error(f"Error al procesar la imagen: {str(e)}")
        return []

def extract_teams_from_structure(image):
    """
    Extrae equipos de la imagen basándose en la estructura típica de una quiniela.
    
    Args:
        image: Imagen PIL procesada.
        
    Returns:
        list: Lista de partidos encontrados.
    """
    # Cargar la base de datos de equipos
    teams_db = load_teams_database()
    
    # Para esta demostración, ofrecemos al usuario seleccionar equipos
    # de una lista predefinida, simulando lo que haría un sistema de reconocimiento
    
    st.write("Selecciona los equipos que aparecen en tu quiniela:")
    
    matches = []
    
    # Crear hasta 9 partidos (típico en quinielas Progol)
    for i in range(9):
        st.write(f"### Partido {i+1}")
        col1, col2 = st.columns(2)
        
        with col1:
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
        
        with col2:
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
    
    # Botón para confirmar la selección
    if st.button("Confirmar Partidos"):
        st.success(f"Se han registrado {len(matches)} partidos correctamente")
    
    return matches

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

# Módulo para scrapear la información de la quiniela Progol
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
            home_team = element.select_one('.local').text.strip()
            away_team = element.select_one('.visitante').text.strip()
            matches.append({"local": home_team, "visitante": away_team})
        
        return matches
    except Exception as e:
        st.error(f"Error al scrapear datos de Progol: {str(e)}")
        return []

# Módulo para relacionar partidos de la quiniela con la API
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
    
    if not current_fixtures:
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

# Función auxiliar para calcular similitud entre cadenas
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

# Módulo principal de la aplicación
def main():
    """
    Función principal que ejecuta la aplicación Streamlit.
    """
    # Cargar variables de entorno si existe un archivo .env
    load_dotenv()
    
    st.title("📊 Seguimiento de Quiniela Progol")
    
    # Sidebar para opciones de configuración
    st.sidebar.title("⚙️ Configuración")
    
    # Selección de zona horaria
    timezones = pytz.all_timezones
    default_tz = 'America/Mexico_City'
    selected_timezone = st.sidebar.selectbox(
        "Selecciona tu zona horaria:",
        timezones,
        index=timezones.index(default_tz) if default_tz in timezones else 0
    )
    
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
            uploaded_file = st.file_uploader("Sube la imagen de tu quiniela", type=["jpg", "jpeg", "png", "pdf"])
            
            if uploaded_file is not None:
                # Manejar PDFs o imágenes
                if uploaded_file.name.lower().endswith('.pdf'):
                    if PDF_SUPPORT:
                        try:
                            st.info("Procesando archivo PDF. Se utilizará solo la primera página.")
                            # Convertir PDF a imagen usando pdf2image
                            pdf_pages = pdf2image.convert_from_bytes(
                                uploaded_file.read(),
                                first_page=1,
                                last_page=1
                            )
                            if pdf_pages:
                                image = pdf_pages[0]
                                st.image(image, caption="Primera página del PDF", use_column_width=True, width=400)
                                
                                if st.button("Procesar Quiniela desde PDF"):
                                    with st.spinner("Procesando imagen desde PDF..."):
                                        quiniela_matches = process_quiniela_image(image)
                                        
                                        if quiniela_matches:
                                            st.session_state.quiniela_matches = quiniela_matches
                                        else:
                                            st.warning("No se detectaron partidos automáticamente. Utiliza la opción 'Selección manual'.")
                            else:
                                st.error("No se pudo extraer ninguna página del PDF.")
                        except Exception as e:
                            st.error(f"Error al procesar el PDF: {str(e)}")
                            st.info("Por favor, sube una imagen en formato JPG, PNG o JPEG.")
                    else:
                        st.warning("El soporte para PDF no está disponible en este entorno.")
                        st.info("Por favor, sube una imagen en formato JPG, PNG o JPEG.")
                else:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Imagen cargada", use_column_width=True, width=400)
                
                    if st.button("Procesar Quiniela"):
                        with st.spinner("Procesando imagen..."):
                            quiniela_matches = process_quiniela_image(image)
                            
                            if quiniela_matches:
                                st.session_state.quiniela_matches = quiniela_matches
                            else:
                                st.warning("No se detectaron partidos automáticamente. Utiliza la opción 'Selección manual'.")
        
        elif upload_method == "Selección manual":
            # La función actual muestra un formulario para selección manual
            st.write("Selecciona los equipos de la quiniela manualmente:")
            quiniela_matches = process_quiniela_image(None)
            
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
                if hasattr(st.session_state, 'quiniela_matches') and st.session_state.quiniela_matches:
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
        if hasattr(st.session_state, 'fixtures_data') and st.session_state.fixtures_data:
            df = pd.DataFrame(st.session_state.fixtures_data)
            st.dataframe(df)
    
    # Tab 3: Resultados en Vivo
    with tab3:
        st.header("Resultados en Vivo")
        
        if st.button("Actualizar Resultados"):
            with st.spinner("Obteniendo resultados en vivo..."):
                # Verificar si hay fixtures en session state
                if hasattr(st.session_state, 'fixtures_data') and st.session_state.fixtures_data:
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
        if hasattr(st.session_state, 'results_data') and st.session_state.results_data:
            df = pd.DataFrame(st.session_state.results_data)
            st.dataframe(df)
            
            # Opción para actualización automática
            auto_refresh = st.checkbox("Actualizar automáticamente cada 5 minutos")
            
            if auto_refresh:
                st.info("La actualización automática está habilitada. Los resultados se actualizarán cada 5 minutos.")
                time.sleep(300)  # Esperar 5 minutos
                st.experimental_rerun()

# Ejecutar la aplicación
if __name__ == "__main__":
    main()