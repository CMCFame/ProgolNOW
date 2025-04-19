"""
Servicio de datos para la aplicación de quinielas.
Obtiene datos de partidos de fútbol desde SofaScore usando ScraperFC.
"""
import time
from datetime import datetime, timedelta
import pandas as pd
from ScraperFC.sofascore import Sofascore
from typing import List, Dict, Any, Optional, Tuple

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

class SofascoreDataService:
    """Servicio para obtener y procesar datos de partidos desde SofaScore."""
    
    def __init__(self, current_year: str = None):
        """
        Inicializa el servicio de datos.
        
        Args:
            current_year: Año actual para la temporada. Si es None, se usa el año actual.
        """
        self.scraper = Sofascore()
        self.current_year = current_year or str(datetime.now().year)
        
    def get_league_matches(self, league: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los partidos de una liga para la temporada actual.
        
        Args:
            league: Nombre de la liga (debe estar en los keys de LIGAS_PROGOL)
            
        Returns:
            Lista de diccionarios con información de partidos
        """
        if league not in LIGAS_PROGOL:
            raise ValueError(f"Liga {league} no soportada. Ligas disponibles: {list(LIGAS_PROGOL.keys())}")
        
        try:
            # Obtenemos todos los partidos de la liga para la temporada actual
            matches = self.scraper.get_match_dicts(self.current_year, league)
            return matches
        except Exception as e:
            print(f"Error obteniendo partidos de {league}: {e}")
            return []
    
    def get_match_status(self, match_id: int) -> Dict[str, Any]:
        """
        Obtiene el estado actual de un partido específico.
        
        Args:
            match_id: ID del partido en SofaScore
            
        Returns:
            Diccionario con información del estado del partido
        """
        try:
            match_dict = self.scraper.get_match_dict(match_id)
            
            # Obtener información relevante
            home_name = match_dict['homeTeam']['name']
            away_name = match_dict['awayTeam']['name']
            
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
            
            # Códigos de estado (véase la documentación de SofaScore):
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
            print(f"Error obteniendo estado del partido {match_id}: {e}")
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
                        # Obtener detalles completos del partido
                        match_details = self.get_match_status(match['id'])
                        if match_details:
                            active_matches.append(match_details)
                        
                        # Pequeña pausa para no sobrecargar la API
                        time.sleep(0.2)
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
                            'match_id': match['id'],
                            'home_team': match['homeTeam']['name'],
                            'away_team': match['awayTeam']['name'],
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