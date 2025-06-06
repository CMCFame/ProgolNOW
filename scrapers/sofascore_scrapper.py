# scrapers/sofascore_scraper.py
"""
Scraper específico para SofaScore
"""

import requests
import time
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from .base_scraper import BaseScraper

class SofascoreScraper(BaseScraper):
    """Scraper para SofaScore"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://www.sofascore.com"
        self.api_url = "https://api.sofascore.com/api/v1"
    
    def scrape_matches(self, league: str, date_range: Optional[tuple] = None) -> List[Dict]:
        """Scraping de partidos desde SofaScore"""
        league_ids = {
            'premier_league': '17', 'la_liga': '8', 'serie_a': '23', 'bundesliga': '35',
            'champions_league': '7', 'liga_mx': '352', 'brasileirao': '325'
        }
        league_id = league_ids.get(league.lower())
        if not league_id:
            self.logger.error(f"Liga no soportada en SofaScore: {league}")
            return self._generate_fallback_matches(league)
        
        try:
            matches = self._get_matches_from_api(league_id)
            if not matches:
                matches = self._scrape_web(league, league_id)
            self.logger.info(f"Obtenidos {len(matches)} partidos de SofaScore para {league}")
            return matches
        except Exception as e:
            self.logger.error(f"Error en SofaScore scraping: {e}")
            return self._generate_fallback_matches(league)
    
    def _get_matches_from_api(self, league_id: str) -> List[Dict]:
        """Intenta obtener partidos desde la API de SofaScore"""
        matches = []
        try:
            url = f"{self.api_url}/sport/football/tournament/{league_id}/matches/{datetime.now().strftime('%Y-%m-%d')}"
            headers = {'User-Agent': random.choice(self.user_agents), 'Accept': 'application/json', 'Referer': self.base_url}
            response = self._safe_request(url, headers=headers)
            if response and response.status_code == 200:
                for event in response.json().get('events', [])[:14]:
                    match_data = self._process_api_event(event)
                    if match_data and self.validate_match_data(match_data):
                        matches.append(match_data)
        except Exception as e:
            self.logger.warning(f"Error accediendo a SofaScore API: {e}")
        return matches
    
    def _process_api_event(self, event: Dict) -> Dict:
        """Procesa un evento de la API"""
        try:
            home_team, away_team = event.get('homeTeam', {}).get('name', 'Unknown'), event.get('awayTeam', {}).get('name', 'Unknown')
            home_rating, away_rating = event.get('homeTeam', {}).get('rating', 50), event.get('awayTeam', {}).get('rating', 50)
            prob_local, prob_empate, prob_visitante = self._ratings_to_probabilities(home_rating, away_rating)
            return {
                'local': home_team, 'visitante': away_team, 'prob_local': prob_local,
                'prob_empate': prob_empate, 'prob_visitante': prob_visitante,
                'es_final': False, 'forma_diferencia': 0, 'lesiones_impact': 0
            }
        except Exception as e:
            self.logger.warning(f"Error procesando evento API: {e}")
            return {}
    
    def _ratings_to_probabilities(self, home_rating: float, away_rating: float) -> tuple:
        """Convierte ratings de equipos a probabilidades aproximadas"""
        home_strength, away_strength = max(home_rating, 30) * 1.1, max(away_rating, 30)
        total_strength = home_strength + away_strength
        prob_local, prob_visitante = home_strength / total_strength, away_strength / total_strength
        empate_factor = 0.30
        prob_local, prob_visitante = prob_local * (1 - empate_factor), prob_visitante * (1 - empate_factor)
        total = prob_local + empate_factor + prob_visitante
        return (prob_local/total, empate_factor/total, prob_visitante/total)
    
    def _scrape_web(self, league: str, league_id: str) -> List[Dict]:
        """Scraping web como fallback"""
        if not BS4_AVAILABLE: return self._generate_fallback_matches(league)
        matches = []
        try:
            response = self._safe_request(f"{self.base_url}/tournament/football/{league}/{league_id}")
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                for element in (soup.find_all(class_="event") or soup.find_all(class_="match"))[:14]:
                    try:
                        match_data = self._extract_web_match_data(element)
                        if match_data and self.validate_match_data(match_data):
                            matches.append(match_data)
                    except Exception as e:
                        self.logger.warning(f"Error extrayendo partido web: {e}")
        except Exception as e:
            self.logger.error(f"Error en web scraping SofaScore: {e}")
        return matches or self._generate_fallback_matches(league)
    
    def _extract_web_match_data(self, element) -> Dict:
        """Extrae datos de partido del elemento web"""
        try:
            teams = element.find_all(class_="team") or element.find_all(class_="participant")
            if len(teams) >= 2:
                return {'local': teams[0].get_text(strip=True), 'visitante': teams[1].get_text(strip=True), **self._default_probabilities()}
        except Exception as e:
            self.logger.warning(f"Error extrayendo datos web: {e}")
        return {}
    
    def _generate_fallback_matches(self, league: str, count: int = 14) -> List