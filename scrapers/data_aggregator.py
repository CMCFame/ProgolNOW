# scrapers/data_aggregator.py
"""
Agregador de datos de múltiples fuentes
"""

from typing import List, Dict, Optional
from .flashscore_scraper import FlashscoreScraper
from .odds_scraper import OddsScraper
import logging
from datetime import datetime

class DataAggregator:
    """Agrega datos de múltiples scrapers"""
    
    def __init__(self, odds_api_key: Optional[str] = None):
        self.logger = self._setup_logging()
        
        # Inicializar scrapers
        self.scrapers = {
            'flashscore': FlashscoreScraper(),
            'odds_api': OddsScraper(api_key=odds_api_key) if odds_api_key else None
        }
        
        self.logger.info("DataAggregator inicializado")
    
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
    
    def get_matches(self, league: str, target_count: int = 14, 
                   preferred_sources: List[str] = None) -> List[Dict]:
        """
        Obtiene partidos de múltiples fuentes
        
        Args:
            league: Liga a buscar
            target_count: Número objetivo de partidos
            preferred_sources: Fuentes preferidas en orden
        
        Returns:
            Lista de partidos agregados
        """
        if preferred_sources is None:
            preferred_sources = ['odds_api', 'flashscore']
        
        all_matches = []
        
        for source in preferred_sources:
            if source not in self.scrapers or not self.scrapers[source]:
                continue
            
            try:
                self.logger.info(f"Obteniendo datos de {source} para {league}")
                scraper = self.scrapers[source]
                matches = scraper.scrape_matches(league)
                
                if matches:
                    self.logger.info(f"Obtenidos {len(matches)} partidos de {source}")
                    all_matches.extend(matches)
                    
                    # Si ya tenemos suficientes partidos, detener
                    if len(all_matches) >= target_count:
                        break
                
            except Exception as e:
                self.logger.error(f"Error obteniendo datos de {source}: {e}")
                continue
        
        # Limpiar y deduplicar
        cleaned_matches = self._clean_and_deduplicate(all_matches)
        
        # Limitar al número objetivo
        final_matches = cleaned_matches[:target_count]
        
        self.logger.info(f"Retornando {len(final_matches)} partidos para {league}")
        return final_matches
    
    def _clean_and_deduplicate(self, matches: List[Dict]) -> List[Dict]:
        """Limpia y elimina duplicados"""
        seen_matches = set()
        clean_matches = []
        
        for match in matches:
            # Crear clave única basada en equipos
            key = f"{match['local'].lower().strip()}_vs_{match['visitante'].lower().strip()}"
            
            if key not in seen_matches:
                # Limpiar nombres de equipos
                match['local'] = self._clean_team_name(match['local'])
                match['visitante'] = self._clean_team_name(match['visitante'])
                
                # Validar probabilidades
                if self._validate_probabilities(match):
                    seen_matches.add(key)
                    clean_matches.append(match)
        
        return clean_matches
    
    def _clean_team_name(self, name: str) -> str:
        """Limpia nombres de equipos"""
        # Remover caracteres especiales y espacios extra
        cleaned = name.strip()
        
        # Mapeo de nombres comunes
        name_mapping = {
            'Manchester United': 'Manchester United',
            'Man United': 'Manchester United',
            'Man Utd': 'Manchester United',
            'Manchester City': 'Manchester City',
            'Man City': 'Manchester City',
            'Real Madrid': 'Real Madrid',
            'Barcelona': 'Barcelona',
            'FC Barcelona': 'Barcelona',
        }
        
        return name_mapping.get(cleaned, cleaned)
    
    def _validate_probabilities(self, match: Dict) -> bool:
        """Valida que las probabilidades sean válidas"""
        required_probs = ['prob_local', 'prob_empate', 'prob_visitante']
        
        for prob_key in required_probs:
            if prob_key not in match:
                return False
            
            prob = match[prob_key]
            if not isinstance(prob, (int, float)) or not (0 <= prob <= 1):
                return False
        
        # Verificar que sumen aproximadamente 1
        total = sum(match[key] for key in required_probs)
        if abs(total - 1.0) > 0.1:
            return False
        
        return True
    
    def close_all(self):
        """Cierra todos los scrapers"""
        for scraper in self.scrapers.values():
            if scraper and hasattr(scraper, 'close'):
                scraper.close()
        
        self.logger.info("Todos los scrapers cerrados")