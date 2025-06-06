# scrapers/odds_scraper.py
"""
Scraper para obtener odds de múltiples casas de apuestas
"""

import requests
from .base_scraper import BaseScraper
from typing import Dict, List, Optional
import json

class OddsScraper(BaseScraper):
    """Scraper para odds de casas de apuestas"""
    
    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.odds_api_url = "https://api.the-odds-api.com/v4"
        
    def get_odds_from_api(self, sport: str = 'soccer_epl') -> List[Dict]:
        """Obtiene odds usando The Odds API"""
        if not self.api_key:
            self.logger.warning("No API key provided for odds API")
            return []
        
        try:
            url = f"{self.odds_api_url}/sports/{sport}/odds"
            params = {
                'apiKey': self.api_key,
                'regions': 'us,uk,eu',
                'markets': 'h2h',
                'oddsFormat': 'decimal'
            }
            
            response = self._safe_request(url, params=params)
            if response:
                data = response.json()
                return self._process_odds_api_data(data)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo odds de API: {e}")
        
        return []
    
    def _process_odds_api_data(self, data: List[Dict]) -> List[Dict]:
        """Procesa datos de The Odds API"""
        processed_matches = []
        
        for match in data:
            try:
                home_team = match['home_team']
                away_team = match['away_team']
                commence_time = match['commence_time']
                
                best_odds = self._get_best_odds(match['bookmakers'])
                
                if best_odds:
                    match_data = {
                        'local': home_team,
                        'visitante': away_team,
                        'fecha': commence_time,
                        'liga': match.get('sport_title', 'API'),
                        **best_odds
                    }
                    
                    if self.validate_match_data(match_data):
                        processed_matches.append(match_data)
                
            except Exception as e:
                self.logger.warning(f"Error procesando partido de API: {e}")
                continue
        
        return processed_matches
    
    def _get_best_odds(self, bookmakers: List[Dict]) -> Dict:
        """Obtiene las mejores odds promedio de todas las casas"""
        if not bookmakers:
            return self._default_probabilities()
        
        home_odds, draw_odds, away_odds = [], [], []
        
        for bookmaker in bookmakers:
            for market in bookmaker.get('markets', []):
                if market['key'] == 'h2h':
                    for outcome in market['outcomes']:
                        if outcome['name'] == bookmaker.get('home_team', ''):
                            home_odds.append(outcome['price'])
                        elif outcome['name'] == bookmaker.get('away_team', ''):
                            away_odds.append(outcome['price'])
                        else:
                            draw_odds.append(outcome['price'])
        
        if home_odds and draw_odds and away_odds:
            prob_home = 1 / (sum(home_odds) / len(home_odds))
            prob_draw = 1 / (sum(draw_odds) / len(draw_odds))
            prob_away = 1 / (sum(away_odds) / len(away_odds))
            total = prob_home + prob_draw + prob_away
            
            return {
                'prob_local': prob_home / total, 'prob_empate': prob_draw / total,
                'prob_visitante': prob_away / total, 'es_final': False,
                'forma_diferencia': 0, 'lesiones_impact': 0
            }
        
        return self._default_probabilities()
    
    def scrape_matches(self, league: str, date_range=None) -> List[Dict]:
        """Implementa método abstracto"""
        sport_mapping = {
            'premier_league': 'soccer_epl', 'la_liga': 'soccer_spain_la_liga',
            'serie_a': 'soccer_italy_serie_a', 'bundesliga': 'soccer_germany_bundesliga',
            'champions_league': 'soccer_uefa_champs_league', 'liga_mx': 'soccer_mexico_ligamx'
        }
        return self.get_odds_from_api(sport_mapping.get(league.lower(), 'soccer_epl'))
    
    def scrape_odds(self, match_id: str) -> Dict:
        """Implementa método abstracto"""
        return self._default_probabilities()

    def find_specific_match(self, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Busca un partido específico en The Odds API.
        La API no busca por equipo, sino que devuelve listas por liga.
        Buscamos en las ligas más comunes de Progol.
        """
        if not self.api_key:
            self.logger.warning("No hay API Key para The Odds API.")
            return None

        leagues_to_check = [
            'soccer_mexico_ligamx', 'soccer_epl', 'soccer_spain_la_liga',
            'soccer_italy_serie_a', 'soccer_germany_bundesliga', 'soccer_france_ligue_one',
            'soccer_uefa_champs_league', 'soccer_uefa_europa_league', 'soccer_brazil_campeonato'
        ]

        for league in leagues_to_check:
            self.logger.info(f"Buscando en '{league}' por '{home_team} vs {away_team}'")
            api_matches = self.get_odds_from_api(league)
            for match in api_matches:
                if (home_team.lower() in match.get('local', '').lower() and
                    away_team.lower() in match.get('visitante', '').lower()):
                    self.logger.info(f"¡Encontrado! {home_team} vs {away_team}")
                    return match
        
        self.logger.warning(f"No se encontró el partido '{home_team} vs {away_team}' en The Odds API.")
        return None