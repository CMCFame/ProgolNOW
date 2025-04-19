"""
Servicio de datos para la aplicación de quinielas.
Obtiene datos de partidos de fútbol desde SofaScore usando requests.
"""
import time
import requests
import random
import json
import os
import tempfile
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
    "EPL": "Premier League",
    "Serie A": "Serie A",
    "Bundesliga": "Bundesliga",
    "Eredivisie": "Eredivisie",
    "Ligue 1": "Ligue 1",
    "Liga NOS": "Primeira Liga",
    "Argentina Liga Profesional": "Argentina Liga Profesional",
    "Brasileirao": "Brasileirao",
    "MLS": "MLS",
    "Liga Chilena": "Primera División de Chile",
    "Liga Belga": "Jupiler Pro League",
    "RFPL": "Premier League Rusa"
}

# Inicialización básica de IDs de ligas (pueden ser actualizados dinámicamente)
# Estos valores son solo para inicialización en caso de que no se puedan descubrir automáticamente
DEFAULT_LEAGUE_IDS = {
    "Liga MX": 52,
    "Liga Expansion MX": 40378,
    "Liga Femenil MX": 16931,
    "Premier League": 17,
    "Serie A": 23,
    "Bundesliga": 35,
    "Eredivisie": 37,
    "Ligue 1": 34,
    "Primeira Liga": 238,
    "Argentina Liga Profesional": 155,
    "Brasileirao": 325,
    "MLS": 242,
    "Primera División de Chile": 127,
    "Jupiler Pro League": 38,
    "Premier League Rusa": 203
}

# Archivo para guardar los IDs actualizados de ligas y temporadas
CACHE_FILE = os.path.join(tempfile.gettempdir(), "sofascore_ids_cache.json")

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
        
        # Cargar IDs de ligas y temporadas desde caché si existe
        self.league_ids = self._load_cache("league_ids") or DEFAULT_LEAGUE_IDS.copy()
        self.season_ids = self._load_cache("season_ids") or {}
        
        # Actualizar IDs de ligas automáticamente al inicio
        self.update_league_ids()
    
    def _load_cache(self, key: str) -> Dict:
        """Carga datos de caché del archivo."""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get(key, {})
        except Exception as e:
            print(f"Error al cargar caché: {e}")
        return {}
    
    def _save_cache(self) -> None:
        """Guarda IDs de ligas y temporadas en un archivo de caché."""
        try:
            data = {
                "league_ids": self.league_ids,
                "season_ids": self.season_ids,
                "updated_at": datetime.now().isoformat()
            }
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar caché: {e}")
    
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
    
    def update_league_ids(self) -> bool:
        """
        Actualiza los IDs de las ligas buscando nombres conocidos en SofaScore.
        
        Returns:
            True si se actualizaron con éxito, False en caso contrario
        """
        try:
            # Buscar cada liga y encontrar su ID actual
            updated = False
            
            for internal_name, display_name in LIGAS_PROGOL.items():
                # Realizar búsqueda por nombre de liga
                search_url = f"https://api.sofascore.com/api/v1/search/tournaments/{display_name}"
                data = self._make_request(search_url)
                
                if not data or 'tournaments' not in data:
                    continue
                
                # Buscar la mejor coincidencia
                for tournament in data['tournaments']:
                    if tournament.get('name', '').lower() == display_name.lower() or \
                       tournament.get('name', '').lower() in display_name.lower() or \
                       display_name.lower() in tournament.get('name', '').lower():
                        
                        tournament_id = tournament.get('id')
                        if tournament_id:
                            # Verificar que el ID funciona obteniendo las temporadas
                            test_url = f"https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}/seasons"
                            test_data = self._make_request(test_url)
                            
                            if test_data and 'seasons' in test_data and len(test_data['seasons']) > 0:
                                # Actualizar el ID de la liga
                                self.league_ids[display_name] = tournament_id
                                updated = True
                                print(f"ID actualizado para {display_name}: {tournament_id}")
                                break
            
            if updated:
                self._save_cache()
                return True
            
            return False
        except Exception as e:
            print(f"Error al actualizar IDs de ligas: {e}")
            return False
    
    def get_season_id(self, league: str) -> Optional[int]:
        """
        Obtiene el ID de la temporada actual para una liga.
        
        Args:
            league: Nombre de la liga (debe ser el nombre interno usado en LIGAS_PROGOL)
            
        Returns:
            ID de la temporada o None si no se encuentra
        """
        if league not in LIGAS_PROGOL:
            print(f"Liga {league} no soportada")
            return None
        
        display_name = LIGAS_PROGOL[league]
        
        # Comprobar si tenemos el ID en caché y es reciente (menos de 1 día)
        cache_key = f"{display_name}_{self.current_year}"
        if cache_key in self.season_ids:
            cache_timestamp = self.season_ids.get(f"{cache_key}_timestamp", "")
            if cache_timestamp:
                try:
                    cached_time = datetime.fromisoformat(cache_timestamp)
                    if (datetime.now() - cached_time).total_seconds() < 86400:  # 24 horas
                        return self.season_ids[cache_key]
                except:
                    pass
        
        # Si no tenemos el ID de la liga, intentar actualizarlo
        if display_name not in self.league_ids:
            self.update_league_ids()
            if display_name not in self.league_ids:
                print(f"No se pudo obtener ID para {display_name}")
                return None
        
        league_id = self.league_ids[display_name]
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/seasons"
        
        data = self._make_request(url)
        if not data or "seasons" not in data:
            return None
        
        # Buscar la temporada actual o la más reciente
        seasons = data["seasons"]
        target_year = self.current_year
        
        # Buscar coincidencia exacta primero
        for season in seasons:
            if str(season.get("year")) == target_year:
                season_id = season.get("id")
                # Guardar en caché
                self.season_ids[cache_key] = season_id
                self.season_ids[f"{cache_key}_timestamp"] = datetime.now().isoformat()
                self._save_cache()
                return season_id
        
        # Si no hay coincidencia exacta, usar la temporada más reciente
        if seasons:
            # Ordenar por año de forma descendente
            seasons_sorted = sorted(seasons, key=lambda x: x.get("year", 0), reverse=True)
            season_id = seasons_sorted[0].get("id")
            
            # Guardar en caché
            self.season_ids[cache_key] = season_id
            self.season_ids[f"{cache_key}_timestamp"] = datetime.now().isoformat()
            self._save_cache()
            
            return season_id
        
        return None
    
    def get_league_matches(self, league: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los partidos de una liga para la temporada actual.
        
        Args:
            league: Nombre de la liga (debe ser el nombre interno usado en LIGAS_PROGOL)
            
        Returns:
            Lista de diccionarios con información de partidos
        """
        if league not in LIGAS_PROGOL:
            print(f"Liga {league} no soportada")
            return []
        
        season_id = self.get_season_id(league)
        if not season_id:
            print(f"No se pudo obtener ID de temporada para {league}")
            return []
        
        display_name = LIGAS_PROGOL[league]
        if display_name not in self.league_ids:
            self.update_league_ids()
            if display_name not in self.league_ids:
                return []
        
        league_id = self.league_ids[display_name]
        
        # Primero intentamos obtener eventos futuros
        future_url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/events/next/0"
        future_data = self._make_request(future_url)
        future_events = future_data.get('events', []) if future_data else []
        
        # Luego obtenemos eventos pasados
        past_url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/events/last/0"
        past_data = self._make_request(past_url)
        past_events = past_data.get('events', []) if past_data else []
        
        # Combinar todos los eventos
        all_events = past_events + future_events
        
        return all_events
    
    def search_match(self, home_team: str, away_team: str) -> Optional[Dict[str, Any]]:
        """
        Busca un partido específico por nombres de equipos.
        
        Args:
            home_team: Nombre del equipo local
            away_team: Nombre del equipo visitante
            
        Returns:
            Diccionario con información del partido o None si no se encuentra
        """
        # Buscar en todas las ligas soportadas
        for league in LIGAS_PROGOL.keys():
            matches = self.get_league_matches(league)
            
            for match in matches:
                match_home = match.get('homeTeam', {}).get('name', '').lower()
                match_away = match.get('awayTeam', {}).get('name', '').lower()
                
                home_search = home_team.lower()
                away_search = away_team.lower()
                
                # Comprobar coincidencias exactas y parciales
                if ((home_search in match_home or match_home in home_search) and 
                    (away_search in match_away or match_away in away_search)):
                    return match
        
        return None
    
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
            
            # Obtener información de la liga
            tournament = match_dict.get('tournament', {})
            league_name = tournament.get('name', 'Unknown')
            
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
                'league': league_name
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
        
        for league in LIGAS_PROGOL.keys():
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
        
        for league in LIGAS_PROGOL.keys():
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
    
    # Probar actualización de IDs de ligas
    print("Actualizando IDs de ligas...")
    service.update_league_ids()
    print(f"IDs de ligas actualizados: {service.league_ids}")
    
    # Probar obtención de IDs de temporadas
    for league in list(LIGAS_PROGOL.keys())[:3]:  # Probar solo algunas ligas para no sobrecargar
        print(f"\nObteniendo ID de temporada para {league}...")
        season_id = service.get_season_id(league)
        print(f"ID de temporada: {season_id}")
        
        if season_id:
            print(f"Obteniendo partidos para {league}...")
            matches = service.get_league_matches(league)
            print(f"Partidos encontrados: {len(matches)}")
            
            if matches:
                print(f"Primer partido: {matches[0].get('homeTeam', {}).get('name', '')} vs {matches[0].get('awayTeam', {}).get('name', '')}")
    
    # Probar búsqueda de partido
    print("\nBuscando partido Real Madrid vs Barcelona...")
    match = service.search_match("Real Madrid", "Barcelona")
    if match:
        print(f"Partido encontrado: {match.get('id')} - {match.get('homeTeam', {}).get('name', '')} vs {match.get('awayTeam', {}).get('name', '')}")
    else:
        print("Partido no encontrado")
    
    # Probar obtención de partidos activos
    print("\nObteniendo partidos activos...")
    active = service.get_active_matches()
    print(f"Partidos activos: {len(active)}")
    
    # Probar obtención de próximos partidos
    print("\nObteniendo próximos partidos...")
    upcoming = service.get_upcoming_matches(days_ahead=3)
    print(f"Próximos partidos (3 días): {len(upcoming)}")

if __name__ == "__main__":
    test_service()