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
<<<<<<< HEAD
<<<<<<< HEAD
from typing import List, Dict, Optional

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
=======
>>>>>>> parent of d1a432e (ok)
=======
>>>>>>> parent of d1a432e (ok)

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
        league_urls = {
            'premier_league': '/football/england/premier-league/', 'la_liga': '/football/spain/laliga/',
            'serie_a': '/football/italy/serie-a/', 'bundesliga': '/football/germany/bundesliga/',
            'champions_league': '/football/europe/champions-league/', 'liga_mx': '/football/mexico/liga-mx/',
            'brasileirao': '/football/brazil/serie-a/'
        }
        
        league_url = league_urls.get(league.lower())
        if not league_url:
            self.logger.error(f"Liga no soportada: {league}")
            return matches
        
        try:
            matches = self._scrape_with_selenium(league_url) if self.use_selenium else self._scrape_with_requests(league_url)
            self.logger.info(f"Scraped {len(matches)} partidos de {league}")
            return matches
        except Exception as e:
            self.logger.error(f"Error scraping {league}: {str(e)}")
<<<<<<< HEAD
<<<<<<< HEAD
            return self._generate_fallback_matches(league)
=======
=======
>>>>>>> parent of d1a432e (ok)
        
        return matches
>>>>>>> parent of d1a432e (ok)
    
    def _scrape_with_selenium(self, league_url: str) -> List[Dict]:
        """Scraping usando Selenium"""
        if not self.driver: return self._generate_fallback_matches("unknown")
        matches = []
<<<<<<< HEAD
=======
        
        if not self.driver:
            return matches
        
>>>>>>> parent of d1a432e (ok)
        try:
            self.driver.get(f"{self.base_url}{league_url}fixtures/")
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "event__match")))
            for match_element in self.driver.find_elements(By.CLASS_NAME, "event__match")[:14]:
                try:
                    match_data = self._extract_match_data_selenium(match_element)
                    if match_data and self.validate_match_data(match_data):
                        matches.append(match_data)
                except Exception as e:
                    self.logger.warning(f"Error extrayendo partido: {e}")
        except Exception as e:
            self.logger.error(f"Error en Selenium scraping: {e}")
<<<<<<< HEAD
<<<<<<< HEAD
        return matches or self._generate_fallback_matches("selenium_failed")
    
    def _scrape_with_requests(self, league_url: str) -> List[Dict]:
        """Scraping usando requests y BeautifulSoup"""
        if not BS4_AVAILABLE: return self._generate_fallback_matches("no_bs4")
        matches = []
        try:
            response = self._safe_request(f"{self.base_url}{league_url}fixtures/")
            if response:
                soup = BeautifulSoup(response.content, 'html.parser')
                for match_element in soup.find_all(class_="event__match")[:14]:
                    try:
                        match_data = self._extract_match_data_bs4(match_element)
                        if match_data and self.validate_match_data(match_data):
                            matches.append(match_data)
                    except Exception as e:
                        self.logger.warning(f"Error extrayendo partido BS4: {e}")
        except Exception as e:
            self.logger.error(f"Error en requests scraping: {e}")
        return matches or self._generate_fallback_matches("requests_failed")
=======
        
        return matches
>>>>>>> parent of d1a432e (ok)
=======
        
        return matches
>>>>>>> parent of d1a432e (ok)
    
    def _extract_match_data_selenium(self, match_element) -> Dict:
        """Extrae datos de un partido usando Selenium"""
        try:
<<<<<<< HEAD
            return {
                'local': match_element.find_element(By.CLASS_NAME, "event__participant--home").text.strip(),
                'visitante': match_element.find_element(By.CLASS_NAME, "event__participant--away").text.strip(),
                'fecha': match_element.find_element(By.CLASS_NAME, "event__time").text,
                'liga': 'Flashscore', **self._default_probabilities()
=======
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
>>>>>>> parent of d1a432e (ok)
            }
        except Exception as e:
            self.logger.warning(f"Error extrayendo datos del partido: {e}")
            return {}
    
    def _extract_odds_selenium(self) -> Dict:
        """Extrae odds usando Selenium"""
        # Implementación básica - odds pueden estar en diferentes elementos
        try:
<<<<<<< HEAD
<<<<<<< HEAD
            home_element = match_element.find(class_="event__participant--home")
            away_element = match_element.find(class_="event__participant--away")
            if not home_element or not away_element: return {}
            return {
                'local': home_element.get_text(strip=True), 'visitante': away_element.get_text(strip=True),
                'fecha': datetime.now().strftime('%Y-%m-%d'), 'liga': 'Flashscore', **self._default_probabilities()
            }
        except Exception as e:
            self.logger.warning(f"Error extrayendo datos BS4: {e}")
            return {}
    
    def _generate_fallback_matches(self, reason: str, count: int = 14) -> List[Dict]:
        """Genera partidos de fallback cuando falla el scraping"""
        self.logger.info(f"Generando {count} partidos de fallback: {reason}")
        teams_by_league = {
            'premier_league': [('Man United', 'Liverpool'), ('Chelsea', 'Arsenal')],
            'la_liga': [('Real Madrid', 'Barcelona'), ('Atletico', 'Sevilla')],
            'liga_mx': [('America', 'Chivas'), ('Cruz Azul', 'Pumas')]
        }
        league_key = next((key for key in teams_by_league if key in reason.lower()), 'premier_league')
        teams = teams_by_league.get(league_key, []) * (count // 2 + 1)
        matches = []
        random.seed(42)
        for i in range(min(count, len(teams))):
            prob_local = random.uniform(0.25, 0.55)
            prob_empate = random.uniform(0.20, 0.40)
            prob_visitante = 1.0 - prob_local - prob_empate
            if prob_visitante < 0.15:
                total = prob_local + prob_empate + 0.15
                prob_local /= total; prob_empate /= total; prob_visitante = 0.15 / total
            matches.append({
                'local': teams[i][0], 'visitante': teams[i][1], 'prob_local': prob_local,
                'prob_empate': prob_empate, 'prob_visitante': prob_visitante,
                'es_final': i < 2, 'forma_diferencia': random.randint(-1, 2),
                'lesiones_impact': random.randint(-1, 1)
            })
        return matches
=======
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
>>>>>>> parent of d1a432e (ok)
=======
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
>>>>>>> parent of d1a432e (ok)
    
    def _default_probabilities(self) -> Dict:
        """Probabilidades por defecto"""
        return {
            'prob_local': 0.40, 'prob_empate': 0.30, 'prob_visitante': 0.30,
            'es_final': False, 'forma_diferencia': 0, 'lesiones_impact': 0
        }
    
    def scrape_odds(self, match_id: str) -> Dict:
        """Scraping de odds específicos"""
        # Implementar según necesidades específicas
        return self._default_probabilities()
    
    def close(self):
        """Cierra el driver de Selenium"""
        if self.driver:
<<<<<<< HEAD
<<<<<<< HEAD
            try:
                self.driver.quit()
                self.logger.info("Selenium driver cerrado")
            except Exception as e:
                self.logger.warning(f"Error cerrando driver: {e}")
            self.driver = None

    def find_specific_match(self, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Stub para buscar un partido específico en Flashscore.
        Una implementación real requeriría usar la barra de búsqueda del sitio,
        lo cual es complejo y lento. Por ahora, este método sirve como placeholder
        y permite al DataAggregator pasar a la siguiente fuente.
        """
        self.logger.info(f"Búsqueda en Flashscore para '{home_team} vs {away_team}' no implementada. Saltando fuente.")
        return None
=======
            self.driver.quit()
            self.logger.info("Selenium driver cerrado")
>>>>>>> parent of d1a432e (ok)
=======
            self.driver.quit()
            self.logger.info("Selenium driver cerrado")
>>>>>>> parent of d1a432e (ok)
