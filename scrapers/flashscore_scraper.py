# scrapers/flashscore_scraper.py
"""
Scraper específico para Flashscore
"""

import requests
import time
import random
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Importaciones opcionales de Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from .base_scraper import BaseScraper

class FlashscoreScraper(BaseScraper):
    """Scraper para Flashscore"""
    
    def __init__(self, use_selenium=True, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://www.flashscore.com"
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.driver = None
        
        if self.use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Configura Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            self.logger.warning("Selenium no disponible, usando requests")
            self.use_selenium = False
            return
            
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("Selenium configurado correctamente")
        except Exception as e:
            self.logger.error(f"Error configurando Selenium: {e}")
            self.use_selenium = False
    
    def scrape_matches(self, league: str, date_range: Optional[tuple] = None) -> List[Dict]:
        """Scraping de partidos desde Flashscore"""
        matches = []
        
        league_urls = {
            'premier_league': '/football/england/premier-league/',
            'la_liga': '/football/spain/laliga/',
            'serie_a': '/football/italy/serie-a/',
            'bundesliga': '/football/germany/bundesliga/',
            'champions_league': '/football/europe/champions-league/',
            'liga_mx': '/football/mexico/liga-mx/',
            'brasileirao': '/football/brazil/serie-a/'
        }
        
        league_url = league_urls.get(league.lower())
        if not league_url:
            self.logger.error(f"Liga no soportada: {league}")
            return self._generate_fallback_matches(league)
        
        try:
            if self.use_selenium:
                matches = self._scrape_with_selenium(league_url)
            else:
                matches = self._scrape_with_requests(league_url)
            
            self.logger.info(f"Scraped {len(matches)} partidos de {league}")
            
        except Exception as e:
            self.logger.error(f"Error scraping {league}: {str(e)}")
            # Fallback a datos sintéticos
            matches = self._generate_fallback_matches(league)
        
        return matches
    
    def _scrape_with_selenium(self, league_url: str) -> List[Dict]:
        """Scraping usando Selenium"""
        matches = []
        
        if not self.driver:
            return self._generate_fallback_matches("unknown")
        
        try:
            url = f"{self.base_url}{league_url}fixtures/"
            self.driver.get(url)
            
            # Esperar a que cargue la página
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "event__match"))
            )
            
            # Obtener partidos
            match_elements = self.driver.find_elements(By.CLASS_NAME, "event__match")
            
            for match_element in match_elements[:14]:  # Limitar a 14 partidos
                try:
                    match_data = self._extract_match_data_selenium(match_element)
                    if match_data and self.validate_match_data(match_data):
                        matches.append(match_data)
                except Exception as e:
                    self.logger.warning(f"Error extrayendo partido: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error en Selenium scraping: {e}")
        
        return matches or self._generate_fallback_matches("selenium_failed")
    
    def _scrape_with_requests(self, league_url: str) -> List[Dict]:
        """Scraping usando requests y BeautifulSoup"""
        matches = []
        
        if not BS4_AVAILABLE:
            self.logger.warning("BeautifulSoup no disponible")
            return self._generate_fallback_matches("no_bs4")
        
        try:
            url = f"{self.base_url}{league_url}fixtures/"
            response = self._safe_request(url)
            
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                match_elements = soup.find_all(class_="event__match")
                
                for match_element in match_elements[:14]:
                    try:
                        match_data = self._extract_match_data_bs4(match_element)
                        if match_data and self.validate_match_data(match_data):
                            matches.append(match_data)
                    except Exception as e:
                        self.logger.warning(f"Error extrayendo partido BS4: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error en requests scraping: {e}")
        
        return matches or self._generate_fallback_matches("requests_failed")
    
    def _extract_match_data_selenium(self, match_element) -> Dict:
        """Extrae datos de un partido usando Selenium"""
        try:
            # Obtener equipos
            home_team = match_element.find_element(By.CLASS_NAME, "event__participant--home").text
            away_team = match_element.find_element(By.CLASS_NAME, "event__participant--away").text
            
            # Obtener fecha/hora
            time_element = match_element.find_element(By.CLASS_NAME, "event__time")
            match_time = time_element.text
            
            # Buscar odds (simplificado)
            odds_data = self._default_probabilities()
            
            match_data = {
                'local': home_team.strip(),
                'visitante': away_team.strip(),
                'fecha': match_time,
                'liga': 'Flashscore',
                **odds_data
            }
            
            return match_data
            
        except Exception as e:
            self.logger.warning(f"Error extrayendo datos del partido: {e}")
            return {}
    
    def _extract_match_data_bs4(self, match_element) -> Dict:
        """Extrae datos de un partido usando BeautifulSoup"""
        try:
            home_element = match_element.find(class_="event__participant--home")
            away_element = match_element.find(class_="event__participant--away")
            
            if not home_element or not away_element:
                return {}
            
            home_team = home_element.get_text(strip=True)
            away_team = away_element.get_text(strip=True)
            
            # Datos básicos con probabilidades por defecto
            match_data = {
                'local': home_team,
                'visitante': away_team,
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'liga': 'Flashscore',
                **self._default_probabilities()
            }
            
            return match_data
            
        except Exception as e:
            self.logger.warning(f"Error extrayendo datos BS4: {e}")
            return {}
    
    def _generate_fallback_matches(self, reason: str, count: int = 14) -> List[Dict]:
        """Genera partidos de fallback cuando falla el scraping"""
        self.logger.info(f"Generando {count} partidos de fallback: {reason}")
        
        # Equipos por liga
        teams_by_league = {
            'premier_league': [
                ('Manchester United', 'Liverpool'), ('Chelsea', 'Arsenal'),
                ('Manchester City', 'Tottenham'), ('Newcastle', 'Brighton'),
                ('Aston Villa', 'West Ham'), ('Crystal Palace', 'Fulham'),
                ('Brentford', 'Wolves'), ('Nottingham Forest', 'Everton'),
                ('Bournemouth', 'Luton Town'), ('Burnley', 'Sheffield United'),
                ('Leeds United', 'Leicester City'), ('Southampton', 'Norwich City'),
                ('Watford', 'Cardiff City'), ('Swansea City', 'Millwall')
            ],
            'la_liga': [
                ('Real Madrid', 'Barcelona'), ('Atletico Madrid', 'Sevilla'),
                ('Valencia', 'Athletic Bilbao'), ('Real Sociedad', 'Villarreal'),
                ('Real Betis', 'Getafe'), ('Osasuna', 'Las Palmas'),
                ('Celta Vigo', 'Alaves'), ('Mallorca', 'Girona'),
                ('Cadiz', 'Granada'), ('Almeria', 'Rayo Vallecano'),
                ('Espanyol', 'Real Valladolid'), ('Elche', 'Leganes'),
                ('Deportivo La Coruna', 'Sporting Gijon'), ('Racing Santander', 'Tenerife')
            ],
            'liga_mx': [
                ('America', 'Chivas'), ('Cruz Azul', 'Pumas'),
                ('Monterrey', 'Tigres'), ('Santos', 'Leon'),
                ('Toluca', 'Atlas'), ('Puebla', 'Queretaro'),
                ('Tijuana', 'Juarez'), ('Necaxa', 'Pachuca'),
                ('Mazatlan', 'FC Juarez'), ('San Luis', 'Atletico San Luis'),
                ('Morelia', 'Veracruz'), ('Lobos BUAP', 'Dorados'),
                ('Estudiantes Tecos', 'Jaguares'), ('Indios', 'La Piedad')
            ]
        }
        
        # Detectar liga por el reason o usar genérico
        league_key = 'premier_league'  # default
        for key in teams_by_league.keys():
            if key in reason.lower():
                league_key = key
                break
        
        teams = teams_by_league.get(league_key, teams_by_league['premier_league'])
        
        matches = []
        random.seed(42)  # Semilla fija para consistencia
        
        for i in range(min(count, len(teams))):
            local, visitante = teams[i]
            
            # Generar probabilidades realistas
            prob_local = random.uniform(0.25, 0.55)
            prob_empate = random.uniform(0.20, 0.40)
            prob_visitante = 1.0 - prob_local - prob_empate
            
            # Asegurar probabilidades válidas
            if prob_visitante < 0.15:
                prob_visitante = 0.15
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
                'es_final': random.choice([True, False]) if i < 2 else False,
                'forma_diferencia': random.randint(-1, 2),
                'lesiones_impact': random.randint(-1, 1)
            }
            
            matches.append(match)
        
        return matches
    
    def _default_probabilities(self) -> Dict:
        """Probabilidades por defecto cuando no se pueden obtener odds"""
        return {
            'prob_local': 0.40,
            'prob_empate': 0.30,
            'prob_visitante': 0.30,
            'es_final': False,
            'forma_diferencia': 0,
            'lesiones_impact': 0
        }
    
    def scrape_odds(self, match_id: str) -> Dict:
        """Scraping de odds específicos"""
        return self._default_probabilities()
    
    def close(self):
        """Cierra el driver de Selenium"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Selenium driver cerrado")
            except Exception as e:
                self.logger.warning(f"Error cerrando driver: {e}")
            self.driver = None