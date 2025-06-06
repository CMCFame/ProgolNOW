# scrapers/base_scraper.py
"""
Clase base para todos los scrapers
"""

import requests
import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BaseScraper(ABC):
    """Clase base para todos los scrapers"""
    
    def __init__(self, delay_range=(1, 3), timeout=30):
        self.delay_range = delay_range
        self.timeout = timeout
        self.session = self._create_session()
        self.logger = self._setup_logging()
        
        # User agents rotativos
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
    
    def _create_session(self):
        """Crea sesión HTTP con retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _setup_logging(self):
        """Configura logging"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _get_random_headers(self):
        """Obtiene headers aleatorios"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _random_delay(self):
        """Aplica delay aleatorio"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def _safe_request(self, url, **kwargs):
        """Realiza request seguro con manejo de errores"""
        try:
            self._random_delay()
            headers = kwargs.pop('headers', {})
            headers.update(self._get_random_headers())
            
            response = self.session.get(
                url, 
                headers=headers, 
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en request a {url}: {str(e)}")
            return None
    
    @abstractmethod
    def scrape_matches(self, league: str, date_range: Optional[tuple] = None) -> List[Dict]:
        """Método abstracto para scraping de partidos"""
        pass
    
    @abstractmethod
    def scrape_odds(self, match_id: str) -> Dict:
        """Método abstracto para scraping de odds"""
        pass
    
    def validate_match_data(self, match_data: Dict) -> bool:
        """Valida que los datos del partido sean correctos"""
        required_fields = ['local', 'visitante', 'prob_local', 'prob_empate', 'prob_visitante']
        
        for field in required_fields:
            if field not in match_data:
                return False
        
        # Validar probabilidades
        probs = [match_data['prob_local'], match_data['prob_empate'], match_data['prob_visitante']]
        if not all(isinstance(p, (int, float)) and 0 <= p <= 1 for p in probs):
            return False
        
        # Validar que sumen aproximadamente 1
        if abs(sum(probs) - 1.0) > 0.1:
            return False
        
        return True