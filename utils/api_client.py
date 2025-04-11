# utils/api_client.py
import streamlit as st
import requests
import json
from datetime import datetime

class FootballAPIClient:
    """Cliente para interactuar con la API de Football"""
    
    def __init__(self):
        """Inicializa el cliente con la clave de API desde secrets"""
        self.api_key = st.secrets.get("api_keys", {}).get("football_api_key", "")
        self.api_host = "v3.football.api-sports.io"
        self.base_url = f"https://{self.api_host}"
        self.headers = {
            "x-rapidapi-host": self.api_host,
            "x-rapidapi-key": self.api_key
        }
    
    def _request(self, endpoint, params=None):
        """
        Realiza una petición a la API
        
        Args:
            endpoint (str): Endpoint de la API
            params (dict, optional): Parámetros de la petición
        
        Returns:
            dict: Respuesta de la API
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error en la petición a la API: {str(e)}")
            return {"errors": [str(e)], "response": []}
    
    def get_live_matches(self):
        """
        Obtiene los partidos en vivo
        
        Returns:
            list: Lista de partidos en vivo
        """
        data = self._request("fixtures", {"live": "all"})
        return self._format_matches(data.get("response", []))
    
    def get_upcoming_matches(self, count=10, league=None):
        """
        Obtiene los próximos partidos
        
        Args:
            count (int): Número de partidos a obtener
            league (int, optional): ID de la liga
        
        Returns:
            list: Lista de próximos partidos
        """
        params = {"next": count}
        if league:
            params["league"] = league
            
        data = self._request("fixtures", params)
        return self._format_matches(data.get("response", []))
    
    def _format_matches(self, matches):
        """
        Formatea los partidos para uso en la aplicación
        
        Args:
            matches (list): Lista de partidos de la API
        
        Returns:
            list: Lista de partidos formateados
        """
        formatted_matches = []
        
        for match in matches:
            # Determinar resultado (L, E, V)
            result = None
            if match["fixture"]["status"]["short"] in ["FT", "AET", "PEN"] or match["fixture"]["status"].get("elapsed", 0) >= 90:
                if match["goals"]["home"] > match["goals"]["away"]:
                    result = "L"  # Local gana
                elif match["goals"]["home"] < match["goals"]["away"]:
                    result = "V"  # Visitante gana
                else:
                    result = "E"  # Empate
            
            formatted_matches.append({
                "id": match["fixture"]["id"],
                "date": match["fixture"]["date"],
                "home": match["teams"]["home"]["name"],
                "away": match["teams"]["away"]["name"],
                "homeScore": match["goals"]["home"],
                "awayScore": match["goals"]["away"],
                "status": match["fixture"]["status"]["short"],
                "minute": match["fixture"]["status"].get("elapsed", 0),
                "result": result,
                "homeLogo": match["teams"]["home"]["logo"],
                "awayLogo": match["teams"]["away"]["logo"]
            })
        
        return formatted_matches

class OpenAIClient:
    """Cliente para interactuar con la API de OpenAI"""
    
    def __init__(self):
        """Inicializa el cliente con la clave de API desde secrets"""
        self.api_key = st.secrets.get("api_keys", {}).get("openai_api_key", "")
        self.base_url = "https://api.openai.com/v1"
    
    def analyze_quiniela(self, image_data):
        """
        Analiza una imagen de quiniela usando GPT-4o
        
        Args:
            image_data (str): Datos de la imagen en formato base64
        
        Returns:
            dict: Respuesta del análisis
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente especializado en analizar imágenes de quinielas de Progol. Extrae la información de los partidos y las predicciones marcadas (L, E, V)."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analiza esta quiniela Progol y extrae los equipos y predicciones marcadas. Responde en formato JSON con dos arrays: \"main\" para los 14 partidos principales y \"revenge\" para los 7 de revancha. En cada array incluye objetos con \"home\", \"away\" y \"prediction\" (L, E, V). Si una predicción no está marcada, usa null."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.2
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error en la petición a OpenAI: {str(e)}")
            if response.text:
                st.error(f"Respuesta: {response.text}")
            return {"error": str(e)}