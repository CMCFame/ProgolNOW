# utils/helpers.py
import json
import base64
from datetime import datetime
import streamlit as st

def format_date(date_string, format_out="%d/%m/%Y"):
    """
    Formatea una fecha ISO a un formato más legible
    
    Args:
        date_string (str): Fecha en formato ISO
        format_out (str): Formato de salida
    
    Returns:
        str: Fecha formateada
    """
    try:
        if isinstance(date_string, str):
            # Eliminar la parte Z o la zona horaria si existe
            if "Z" in date_string:
                date_string = date_string.replace("Z", "")
            if "+" in date_string:
                date_string = date_string.split("+")[0]
                
            # Diferentes formatos posibles
            formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
            
            # Intentar diferentes formatos
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_string, fmt)
                    return date_obj.strftime(format_out)
                except ValueError:
                    continue
                    
            # Si ninguno funciona, devolver el original
            return date_string
        else:
            return date_string
    except Exception as e:
        return date_string

def get_file_as_base64(file):
    """
    Convierte un archivo en base64
    
    Args:
        file: Archivo a convertir
    
    Returns:
        str: String en base64
    """
    return base64.b64encode(file.getvalue()).decode("utf-8")

def extract_json_from_text(text):
    """
    Extrae un objeto JSON de un texto
    
    Args:
        text (str): Texto que contiene JSON
    
    Returns:
        dict: Objeto JSON extraído o None si no se encuentra
    """
    try:
        # Buscar JSON entre triple comillas
        import re
        json_match = re.search(r'```json\n([\s\S]*?)\n```', text)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
        
        # Si no, buscar directamente un objeto JSON
        json_match = re.search(r'{[\s\S]*?}', text)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
    except Exception as e:
        st.error(f"Error al extraer JSON: {str(e)}")
    
    return None

def get_match_result_type(home_score, away_score):
    """
    Determina el tipo de resultado (L, E, V) a partir de los marcadores
    
    Args:
        home_score (int): Goles del equipo local
        away_score (int): Goles del equipo visitante
    
    Returns:
        str: Tipo de resultado (L, E, V)
    """
    if home_score is None or away_score is None:
        return None
        
    if home_score > away_score:
        return "L"
    elif home_score < away_score:
        return "V"
    else:
        return "E"

def validate_api_keys():
    """
    Valida que las claves de API estén configuradas
    
    Returns:
        bool: True si están configuradas, False en caso contrario
    """
    api_keys = st.secrets.get("api_keys", {})
    football_key = api_keys.get("football_api_key", "")
    openai_key = api_keys.get("openai_api_key", "")
    
    if not football_key or football_key == "tu_api_key_de_football":
        st.warning("⚠️ API key de Football no configurada. Algunas funciones estarán limitadas.")
        return False
        
    if not openai_key or openai_key == "tu_api_key_de_openai":
        st.warning("⚠️ API key de OpenAI no configurada. El análisis de quinielas no funcionará.")
        return False
        
    return True

def create_download_link(data, filename, text="Descargar datos"):
    """
    Crea un enlace para descargar datos
    
    Args:
        data: Datos a descargar
        filename (str): Nombre del archivo
        text (str): Texto del enlace
    
    Returns:
        str: HTML del enlace de descarga
    """
    if isinstance(data, dict) or isinstance(data, list):
        data = json.dumps(data, indent=4)
        
    b64 = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href