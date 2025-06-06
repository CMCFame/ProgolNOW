"""
Módulos de modelado para Progol Optimizer
Implementa la metodología definitiva Core + Satélites
"""

from .match_classifier import MatchClassifier
from .portfolio_generator import PortfolioGenerator
from .validators import PortfolioValidator

__all__ = [
    'MatchClassifier',
    'PortfolioGenerator', 
    'PortfolioValidator'
]

__version__ = '1.0.0'
__author__ = 'Progol Optimizer Team'