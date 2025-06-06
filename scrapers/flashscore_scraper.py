# scrapers/flashscore_scraper.py
"""
Scraper específico para Flashscore
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_scraper import BaseScraper
import json
import re
from datetime import datetime, timedelta

class FlashscoreScraper(BaseScraper):
    """Scraper para Flashscore"""
    
    def __init__(self, use_selenium=True, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://www.flashscore.com"
        self.use_selenium = use_selenium
        self.driver = None
        
        if use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Configura Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
        
        try:
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
            return matches
        
        try:
            if self.use_selenium:
                matches = self._scrape_with_selenium(league_url)
            else:
                matches = self._scrape_with_requests(league_url)
            
            self.logger.info(f"Scraped {len(matches)} partidos de {league}")
            
        except Exception as e:
            self.logger.error(f"Error scraping {league}: {str(e)}")
        
        return matches
    
    def _scrape_with_selenium(self, league_url: str) -> List[Dict]:
        """Scraping usando Selenium"""
        matches = []
        
        if not self.driver:
            return matches
        
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
        
        return matches
    
    def _extract_match_data_selenium(self, match_element) -> Dict:
        """Extrae datos de un partido usando Selenium"""
        try:
            # Obtener equipos
            home_team = match_element.find_element(By.CLASS_NAME, "event__participant--home").text
            away_team = match_element.find_element(By.CLASS_NAME, "event__participant--away").text
            
            # Obtener fecha/hora
            time_element = match_element.find_element(By.CLASS_NAME, "event__time")
            match_time = time_element.text
            
            # Hacer clic para obtener odds
            match_element.click()
            time.sleep(1)
            
            # Buscar odds (esto puede variar según la estructura de Flashscore)
            odds_data = self._extract_odds_selenium()
            
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
    
    def _extract_odds_selenium(self) -> Dict:
        """Extrae odds usando Selenium"""
        # Implementación básica - odds pueden estar en diferentes elementos
        try:
            # Buscar elementos de odds (ajustar selectores según Flashscore actual)
            odds_elements = self.driver.find_elements(By.CLASS_NAME, "ui-odd")
            
            if len(odds_elements) >= 3:
                odd_home = float(odds_elements[0].text)
                odd_draw = float(odds_elements[1].text)
                odd_away = float(odds_elements[2].text)
                
                # Convertir odds a probabilidades
                prob_home = 1 / odd_home
                prob_draw = 1 / odd_draw
                prob_away = 1 / odd_away
                
                # Normalizar
                total = prob_home + prob_draw + prob_away
                
                return {
                    'prob_local': prob_home / total,
                    'prob_empate': prob_draw / total,
                    'prob_visitante': prob_away / total,
                    'es_final': False,
                    'forma_diferencia': 0,
                    'lesiones_impact': 0
                }
            else:
                # Fallback con probabilidades por defecto
                return self._default_probabilities()
                
        except Exception as e:
            self.logger.warning(f"Error extrayendo odds: {e}")
            return self._default_probabilities()
    
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
        # Implementar según necesidades específicas
        return self._default_probabilities()
    
    def close(self):
        """Cierra el driver de Selenium"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Selenium driver cerrado")
