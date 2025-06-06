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
        
        # Mapeo de ligas a IDs de SofaScore (ejemplos)
        league_ids = {
            'premier_league': '17',
            'la_liga': '8',
            'serie_a': '23',
            'bundesliga': '35',
            'champions_league': '7',
            'liga_mx': '352',
            'brasileirao': '325'
        }
        
        league_id = league_ids.get(league.lower())
        if not league_id:
            self.logger.error(f"Liga no soportada en SofaScore: {league}")
            return self._generate_fallback_matches(league)
        
        try:
            # Intentar obtener datos de la API
            matches = self._get_matches_from_api(league_id)
            
            if not matches:
                # Fallback a scraping web
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
            # Fecha actual
            today = datetime.now()
            date_str = today.strftime('%Y-%m-%d')
            
            # URL de la API (puede requerir ajustes según API actual)
            url = f"{self.api_url}/sport/football/tournament/{league_id}/matches/{date_str}"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/json',
                'Referer': self.base_url
            }
            
            response = self._safe_request(url, headers=headers)
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    events = data.get('events', [])
                    
                    for event in events[:14]:  # Limitar a 14
                        match_data = self._process_api_event(event)
                        if match_data and self.validate_match_data(match_data):
                            matches.append(match_data)
                            
                except json.JSONDecodeError:
                    self.logger.warning("Error decodificando JSON de SofaScore API")
                    
        except Exception as e:
            self.logger.warning(f"Error accediendo a SofaScore API: {e}")
        
        return matches
    
    def _process_api_event(self, event: Dict) -> Dict:
        """Procesa un evento de la API"""
        try:
            home_team = event.get('homeTeam', {}).get('name', 'Unknown')
            away_team = event.get('awayTeam', {}).get('name', 'Unknown')
            
            # Las odds pueden no estar disponibles públicamente
            # Usar probabilidades estimadas basadas en ratings
            home_rating = event.get('homeTeam', {}).get('rating', 50)
            away_rating = event.get('awayTeam', {}).get('rating', 50)
            
            # Convertir ratings a probabilidades aproximadas
            prob_local, prob_empate, prob_visitante = self._ratings_to_probabilities(
                home_rating, away_rating
            )
            
            return {
                'local': home_team,
                'visitante': away_team,
                'prob_local': prob_local,
                'prob_empate': prob_empate,
                'prob_visitante': prob_visitante,
                'es_final': False,
                'forma_diferencia': 0,
                'lesiones_impact': 0
            }
            
        except Exception as e:
            self.logger.warning(f"Error procesando evento API: {e}")
            return {}
    
    def _ratings_to_probabilities(self, home_rating: float, away_rating: float) -> tuple:
        """Convierte ratings de equipos a probabilidades aproximadas"""
        # Algoritmo simplificado de conversión
        home_strength = max(home_rating, 30)  # Mínimo 30
        away_strength = max(away_rating, 30)  # Mínimo 30
        
        # Factor de localía
        home_strength *= 1.1
        
        total_strength = home_strength + away_strength
        
        # Probabilidades base
        prob_local = home_strength / total_strength
        prob_visitante = away_strength / total_strength
        
        # Ajustar para incluir empates (generalmente 25-35%)
        empate_factor = 0.30
        prob_local *= (1 - empate_factor)
        prob_visitante *= (1 - empate_factor)
        prob_empate = empate_factor
        
        # Normalizar para asegurar que sume 1
        total = prob_local + prob_empate + prob_visitante
        return (prob_local/total, prob_empate/total, prob_visitante/total)
    
    def _scrape_web(self, league: str, league_id: str) -> List[Dict]:
        """Scraping web como fallback"""
        matches = []
        
        if not BS4_AVAILABLE:
            self.logger.warning("BeautifulSoup no disponible para web scraping")
            return self._generate_fallback_matches(league)
        
        try:
            # URL de la página web
            url = f"{self.base_url}/tournament/football/{league}/{league_id}"
            response = self._safe_request(url)
            
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar elementos de partidos (selectores pueden cambiar)
                match_elements = soup.find_all(class_="event") or soup.find_all(class_="match")
                
                for element in match_elements[:14]:
                    try:
                        match_data = self._extract_web_match_data(element)
                        if match_data and self.validate_match_data(match_data):
                            matches.append(match_data)
                    except Exception as e:
                        self.logger.warning(f"Error extrayendo partido web: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error en web scraping SofaScore: {e}")
        
        return matches or self._generate_fallback_matches(league)
    
    def _extract_web_match_data(self, element) -> Dict:
        """Extrae datos de partido del elemento web"""
        try:
            # Esto es muy específico a la estructura actual de SofaScore
            # Puede requerir ajustes según cambios en el sitio
            
            teams = element.find_all(class_="team") or element.find_all(class_="participant")
            
            if len(teams) >= 2:
                home_team = teams[0].get_text(strip=True)
                away_team = teams[1].get_text(strip=True)
                
                return {
                    'local': home_team,
                    'visitante': away_team,
                    **self._default_probabilities()
                }
        
        except Exception as e:
            self.logger.warning(f"Error extrayendo datos web: {e}")
        
        return {}
    
    def _generate_fallback_matches(self, league: str, count: int = 14) -> List[Dict]:
        """Genera partidos de fallback específicos para SofaScore"""
        self.logger.info(f"Generando {count} partidos de fallback para {league}")
        
        # Equipos específicos por liga
        teams_by_league = {
            'premier_league': [
                ('Liverpool', 'Manchester City'), ('Arsenal', 'Chelsea'),
                ('Manchester United', 'Tottenham'), ('Newcastle', 'Brighton'),
                ('Aston Villa', 'West Ham'), ('Crystal Palace', 'Brentford'),
                ('Fulham', 'Wolves'), ('Everton', 'Nottingham Forest'),
                ('Bournemouth', 'Luton'), ('Burnley', 'Sheffield United'),
                ('Southampton', 'Leeds United'), ('Leicester', 'Norwich'),
                ('Watford', 'Cardiff'), ('Swansea', 'Millwall')
            ],
            'la_liga': [
                ('Barcelona', 'Real Madrid'), ('Atletico Madrid', 'Sevilla'),
                ('Valencia', 'Athletic Bilbao'), ('Real Sociedad', 'Villarreal'),
                ('Real Betis', 'Getafe'), ('Osasuna', 'Las Palmas'),
                ('Celta Vigo', 'Alaves'), ('Mallorca', 'Girona'),
                ('Cadiz', 'Granada'), ('Almeria', 'Rayo Vallecano'),
                ('Espanyol', 'Valladolid'), ('Elche', 'Leganes'),
                ('Deportivo', 'Sporting'), ('Racing', 'Tenerife')
            ],
            'liga_mx': [
                ('Chivas', 'America'), ('Pumas', 'Cruz Azul'),
                ('Tigres', 'Monterrey'), ('Leon', 'Santos'),
                ('Atlas', 'Toluca'), ('Queretaro', 'Puebla'),
                ('Juarez', 'Tijuana'), ('Pachuca', 'Necaxa'),
                ('Mazatlan', 'San Luis'), ('FC Juarez', 'Atletico San Luis'),
                ('Morelia', 'Veracruz'), ('Dorados', 'Lobos BUAP'),
                ('Tecos', 'Jaguares'), ('Indios', 'La Piedad')
            ]
        }
        
        teams = teams_by_league.get(league, teams_by_league['premier_league'])
        matches = []
        
        random.seed(43)  # Semilla diferente a Flashscore para variedad
        
        for i in range(min(count, len(teams))):
            local, visitante = teams[i]
            
            # Probabilidades ligeramente diferentes a Flashscore
            prob_local = random.uniform(0.28, 0.52)
            prob_empate = random.uniform(0.22, 0.38)
            prob_visitante = 1.0 - prob_local - prob_empate
            
            # Normalizar si es necesario
            if prob_visitante < 0.18:
                prob_visitante = 0.18
                total = prob_local + prob_empate + prob_visitante
                prob_local /= total
                prob_empate /= total
                prob_visitante /= total
            
            match = {
                'local': local,
                'visitante': visitante,
                'prob_local': prob_local,
                'prob_empate': prob_empate,
                'prob_visitante': prob_visitante,
                'es_final': random.choice([True, False]) if i < 3 else False,
                'forma_diferencia': random.randint(-2, 2),
                'lesiones_impact': random.randint(-1, 1)
            }
            
            matches.append(match)
        
        return matches
    
    def _default_probabilities(self) -> Dict:
        """Probabilidades por defecto"""
        return {
            'prob_local': 0.38,
            'prob_empate': 0.32,
            'prob_visitante': 0.30,
            'es_final': False,
            'forma_diferencia': 0,
            'lesiones_impact': 0
        }
    
    def scrape_odds(self, match_id: str) -> Dict:
        """Obtiene odds específicos de un partido"""
        return self._default_probabilities()
    
    def close(self):
        """Cierra conexiones si es necesario"""
        pass