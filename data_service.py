"""
Servicio de datos para la aplicación de quinielas.
Obtiene datos de partidos de fútbol desde SofaScore usando requests.
"""
import time
import requests
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

# Configuración para requests
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

# Mapeo de ligas para Progol
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

# IDs de ligas en SofaScore
LEAGUE_IDS = {
    "Liga MX": 52,  # Liga MX
    "Liga Expansion MX": 40378,  # Liga Expansion MX
    "Liga Femenil MX": 16931,  # Liga MX Femenil
    "EPL": 17,  # Premier League
    "Serie A": 23,  # Serie A
    "Bundesliga": 35,  # Bundesliga
    "Eredivisie": 37,  # Eredivisie
    "Ligue 1": 34,  # Ligue 1
    "Liga NOS": 238,  # Primeira Liga
    "Argentina Liga Profesional": 155,  # Argentina Liga Profesional
    "Brasileirao": 325,  # Brasileirao
    "MLS": 242,  # MLS
    "Liga Chilena": 127,  # Primera División de Chile
    "Liga Belga": 38,  # Jupiler Pro League
    "RFPL": 203  # Premier League Rusa
}

class SofascoreDataService:
    """Servicio para obtener y procesar datos de partidos desde SofaScore."""
    
    def __init__(self, current_year: str = None):
        """
        Inicializa el servicio de datos.
        
        Args:
            current_year: Año actual para la temporada. Si es None, se usa el año actual.
        """
        self.current_year = current_year or str(datetime.now().year)
        self.headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.sofascore.com/"
        }
        
    def _get_random_user_agent(self):
        """Obtiene un User-Agent aleatorio para evitar restricciones."""
        return random.choice(USER_AGENTS)
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[dict]:
        """
        Realiza una solicitud HTTP a la API de SofaScore.
        
        Args:
            url: URL de la solicitud
            max_retries: Número máximo de reintentos
            
        Returns:
            Datos JSON de respuesta o None si hay error
        """
        retries = 0
        while retries < max_retries:
            try:
                # Actualizar User-Agent en cada intento
                self.headers["User-Agent"] = self._get_random_user_agent()
                
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()  # Lanzar excepción si hay error HTTP
                
                return response.json()
            except requests.RequestException as e:
                print(f"Error en solicitud a {url}: {e}")
                retries += 1
                # Esperar antes de reintentar (backoff exponencial)
                time.sleep(2 ** retries)
        
        return None
    
    def get_season_id(self, league: str) -> Optional[int]:
        """
        Obtiene el ID de la temporada actual para una liga.
        
        Args:
            league: Nombre de la liga
            
        Returns:
            ID de la temporada o None si no se encuentra
        """
        if league not in LEAGUE_IDS:
            print(f"Liga {league} no soportada")
            return None
        
        league_id = LEAGUE_IDS[league]
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/seasons"
        
        data = self._make_request(url)
        if not data or "seasons" not in data:
            return None
        
        # Buscar la temporada actual o la más reciente
        seasons = data["seasons"]
        for season in seasons:
            if str(season["year"]) == self.current_year:
                return season["id"]
        
        # Si no se encuentra la temporada del año actual, usar la más reciente
        if seasons:
            return seasons[0]["id"]
        
        return None
    
    def get_league_matches(self, league: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los partidos de una liga para la temporada actual.
        
        Args:
            league: Nombre de la liga
            
        Returns:
            Lista de diccionarios con información de partidos
        """
        if league not in LEAGUE_IDS:
            print(f"Liga {league} no soportada")
            return []
        
        season_id = self.get_season_id(league)
        if not season_id:
            print(f"No se pudo obtener ID de temporada para {league}")
            return []
        
        league_id = LEAGUE_IDS[league]
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/events"
        
        data = self._make_request(url)
        if not data or "events" not in data:
            return []
        
        return data["events"]
    
    def get_match_dict(self, match_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene detalles de un partido específico.
        
        Args:
            match_id: ID del partido en SofaScore
            
        Returns:
            Diccionario con información del partido o None si hay error
        """
        url = f"https://api.sofascore.com/api/v1/event/{match_id}"
        
        data = self._make_request(url)
        if not data or "event" not in data:
            return None
        
        return data["event"]
    
    def get_match_status(self, match_id: int) -> Dict[str, Any]:
        """
        Obtiene el estado actual de un partido específico.
        
        Args:
            match_id: ID del partido en SofaScore
            
        Returns:
            Diccionario con información del estado del partido
        """
        match_dict = self.get_match_dict(match_id)
        if not match_dict:
            return {}
        
        # Obtener información básica
        try:
            # Obtener nombres de equipos
            home_name = match_dict.get('homeTeam', {}).get('name', '')
            away_name = match_dict.get('awayTeam', {}).get('name', '')
            
            # Obtener marcador (con manejo de casos donde no hay puntuación)
            home_score = match_dict.get('homeScore', {}).get('current', 0)
            away_score = match_dict.get('awayScore', {}).get('current', 0)
            
            # Determinar resultado para quiniela (L/E/V)
            if home_score > away_score:
                result = 'L'  # Local gana
            elif home_score < away_score:
                result = 'V'  # Visitante gana
            else:
                result = 'E'  # Empate
            
            # Determinar si el partido está en progreso
            status = match_dict.get('status', {})
            status_code = status.get('code', 0)
            
            # Códigos de estado:
            # 0: No comenzado, 6-7: En progreso, 100,110,120: Finalizado, etc.
            is_live = status_code in [6, 7]  # 1er o 2do tiempo
            is_finished = status_code in [100, 110, 120]  # Finalizado (normal, AET, AP)
            
            return {
                'match_id': match_id,
                'home_team': home_name,
                'away_team': away_name,
                'home_score': home_score,
                'away_score': away_score,
                'result': result,
                'is_live': is_live,
                'is_finished': is_finished,
                'status_code': status_code,
                'timestamp': datetime.now().isoformat(),
                'league': match_dict.get('tournament', {}).get('name', 'Unknown')
            }
        except Exception as e:
            print(f"Error procesando estado del partido {match_id}: {e}")
            return {}
    
    def get_active_matches(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los partidos activos (en progreso) de las ligas soportadas.
        
        Returns:
            Lista de diccionarios con información de partidos activos
        """
        active_matches = []
        
        for league in LEAGUE_IDS.keys():
            try:
                matches = self.get_league_matches(league)
                
                # Filtrar partidos en progreso
                for match in matches:
                    status = match.get('status', {})
                    status_code = status.get('code', 0)
                    
                    # Solo considerar partidos en progreso
                    if status_code in [6, 7]:  # 1er o 2do tiempo
                        match_id = match.get('id')
                        if match_id:
                            # Obtener detalles completos del partido
                            match_details = self.get_match_status(match_id)
                            if match_details:
                                active_matches.append(match_details)
                            
                            # Pequeña pausa para no sobrecargar la API
                            time.sleep(0.5)
            except Exception as e:
                print(f"Error procesando partidos activos de {league}: {e}")
                
        return active_matches
    
    def get_upcoming_matches(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Obtiene los próximos partidos para los siguientes días.
        
        Args:
            days_ahead: Número de días hacia adelante para buscar partidos
            
        Returns:
            Lista de diccionarios con información de partidos próximos
        """
        upcoming_matches = []
        now = datetime.now()
        future_date = now + timedelta(days=days_ahead)
        
        for league in LEAGUE_IDS.keys():
            try:
                matches = self.get_league_matches(league)
                
                # Filtrar partidos que están programados para los próximos días
                for match in matches:
                    # Convertir timestamp a datetime
                    scheduled_time_str = match.get('startTimestamp')
                    if not scheduled_time_str:
                        continue
                    
                    scheduled_time = datetime.fromtimestamp(int(scheduled_time_str))
                    
                    # Solo considerar partidos que no han comenzado y están dentro del período
                    if now <= scheduled_time <= future_date:
                        # Extraer información básica
                        upcoming_match = {
                            'match_id': match.get('id'),
                            'home_team': match.get('homeTeam', {}).get('name', ''),
                            'away_team': match.get('awayTeam', {}).get('name', ''),
                            'scheduled_time': scheduled_time.isoformat(),
                            'league': match.get('tournament', {}).get('name', 'Unknown')
                        }
                        upcoming_matches.append(upcoming_match)
            except Exception as e:
                print(f"Error procesando próximos partidos de {league}: {e}")
                
        return upcoming_matches
    
    def format_match_for_display(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea un partido para su visualización en la interfaz.
        
        Args:
            match: Diccionario con información del partido
            
        Returns:
            Diccionario formateado para visualización
        """
        status_text = "En vivo" if match.get('is_live', False) else (
            "Finalizado" if match.get('is_finished', False) else "Programado"
        )
        
        result_text = {
            'L': "Local gana",
            'E': "Empate",
            'V': "Visitante gana"
        }.get(match.get('result', ''), "No disponible")
        
        return {
            'match_id': match.get('match_id', ''),
            'partido': f"{match.get('home_team', '')} vs {match.get('away_team', '')}",
            'marcador': f"{match.get('home_score', 0)} - {match.get('away_score', 0)}",
            'estado': status_text,
            'resultado_quiniela': match.get('result', ''),
            'resultado_texto': result_text,
            'liga': match.get('league', 'Desconocida'),
            'timestamp': match.get('timestamp', '')
        }

# Función de prueba
def test_service():
    """Función para probar el servicio de datos."""
    service = SofascoreDataService()
    
    # Probar obtención de partidos activos
    print("Obteniendo partidos activos...")
    active = service.get_active_matches()
    print(f"Partidos activos: {len(active)}")
    for match in active:
        print(service.format_match_for_display(match))
    
    # Probar obtención de próximos partidos
    print("\nObteniendo próximos partidos...")
    upcoming = service.get_upcoming_matches(days_ahead=3)
    print(f"Próximos partidos (3 días): {len(upcoming)}")
    for match in upcoming:
        print(match)

if __name__ == "__main__":
    test_service()