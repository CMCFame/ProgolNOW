# scrapers/__init__.py
"""
Sistema de scraping automatizado para datos futbolísticos
Soporta múltiples fuentes: Flashscore, SofaScore, APIs, etc.
"""

from .data_aggregator import DataAggregator
from .flashscore_scraper import FlashscoreScraper
from .sofascore_scraper import SofascoreScraper
from .odds_scraper import OddsScraper
from .template_generator import TemplateGenerator

__all__ = [
    'DataAggregator',
    'FlashscoreScraper', 
    'SofascoreScraper',
    'OddsScraper',
    'TemplateGenerator'
]