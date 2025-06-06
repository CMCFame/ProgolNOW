# scrapers/data_aggregator.py
"""
Agregador de datos de múltiples fuentes para partidos específicos de Progol.
"""

from typing import List, Dict, Optional
import logging
import re

# Importación segura de los scrapers que usará
try:
    from .flashscore_scraper import FlashscoreScraper
except ImportError:
    FlashscoreScraper = None
try:
    from .sofascore_scrapper import SofascoreScraper
except ImportError:
    SofascoreScraper = None
try:
    from .odds_scraper import OddsScraper
except ImportError:
    OddsScraper = None


class DataAggregator:
    """Agrega datos para una lista predefinida de partidos."""
    
    def __init__(self, odds_api_key: Optional[str] = None):
        self.logger = self._setup_logging()
        
        # Inicializar scrapers disponibles
        self.scrapers = {}
        if OddsScraper:
            self.scrapers['odds_api'] = OddsScraper(api_key=odds_api_key)
        if FlashscoreScraper:
            self.scrapers['flashscore'] = FlashscoreScraper()
        if SofascoreScraper:
             self.scrapers['sofascore'] = SofascoreScraper()
        
        # Prioridad de las fuentes
        self.source_priority = ['odds_api', 'sofascore', 'flashscore']

        self.logger.info(f"DataAggregator inicializado con fuentes: {list(self.scrapers.keys())}")
    
    def _setup_logging(self):
        """Configura logging"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def get_details_for_match_list(self, match_list: List[Dict]) -> List[Dict]:
        """
        Busca datos detallados para una lista de partidos predefinida.
        
        Args:
            match_list: Lista de partidos, cada uno un dict con {'local': str, 'visitante': str}
            
        Returns:
            Lista de partidos con datos enriquecidos (probabilidades, etc.).
        """
        detailed_matches = []
        
        for match_to_find in match_list:
            local_team = match_to_find['local']
            away_team = match_to_find['visitante']
            
            self.logger.info(f"Buscando detalles para: {local_team} vs {away_team}")
            
            found_match_data = None
            
            # Iterar sobre las fuentes de datos por prioridad
            for source_name in self.source_priority:
                if source_name in self.scrapers:
                    scraper = self.scrapers[source_name]
                    if scraper and hasattr(scraper, 'find_specific_match'):
                        try:
                            match_data = scraper.find_specific_match(local_team, away_team)
                            if match_data:
                                self.logger.info(f"Partido encontrado en '{source_name}'.")
                                found_match_data = match_data
                                break  # Encontrado, pasar al siguiente partido
                        except Exception as e:
                            self.logger.warning(f"Error buscando '{local_team} vs {away_team}' en {source_name}: {e}")
            
            if found_match_data:
                detailed_matches.append(found_match_data)
            else:
                # Si no se encontró en ninguna fuente, agregar con datos de fallback
                self.logger.warning(f"No se encontraron datos para '{local_team} vs {away_team}'. Usando fallback.")
                detailed_matches.append({
                    'local': local_team,
                    'visitante': away_team,
                    'prob_local': 0.34, 'prob_empate': 0.33, 'prob_visitante': 0.33,
                    'es_final': False, 'forma_diferencia': 0, 'lesiones_impact': 0
                })

        return detailed_matches

    def close_all(self):
        """Cierra todos los scrapers que lo necesiten."""
        for scraper_name, scraper in self.scrapers.items():
            if scraper and hasattr(scraper, 'close'):
                try:
                    scraper.close()
                    self.logger.info(f"Scraper '{scraper_name}' cerrado.")
                except Exception as e:
                    self.logger.warning(f"Error cerrando scraper '{scraper_name}': {e}")