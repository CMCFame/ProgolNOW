# scrapers/template_generator.py
"""
Generador automático de templates CSV
"""

import csv
import io
from datetime import datetime
from typing import List, Dict
from .data_aggregator import DataAggregator

class TemplateGenerator:
    """Genera templates CSV automáticamente"""
    
    def __init__(self, odds_api_key: str = None):
        self.aggregator = DataAggregator(odds_api_key)
    
    def generate_auto_template(self, tipo: str = 'regular', 
                             league: str = 'premier_league') -> str:
        """
        Genera template CSV con datos reales obtenidos automáticamente
        
        Args:
            tipo: 'regular' o 'revancha'
            league: Liga a obtener
        
        Returns:
            Contenido CSV como string
        """
        target_count = 14 if tipo == 'regular' else 7
        
        # Obtener datos reales
        matches = self.aggregator.get_matches(league, target_count)
        
        if not matches:
            # Fallback a datos sintéticos si no se pueden obtener datos reales
            from utils.helpers import generate_csv_template
            return generate_csv_template(tipo)
        
        # Generar CSV con datos reales
        return self._create_csv_from_matches(matches, tipo, league)
    
    def _create_csv_from_matches(self, matches: List[Dict], 
                               tipo: str, league: str) -> str:
        """Crea CSV desde lista de partidos"""
        output = io.StringIO()
        
        # Escribir comentarios de cabecera
        output.write(f"# Template {tipo.upper()} generado automáticamente\n")
        output.write(f"# Liga: {league}\n")
        output.write(f"# Datos obtenidos: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"# Total partidos: {len(matches)}\n")
        output.write("# Fuente: Datos reales agregados de múltiples scrapers\n")
        output.write("#\n\n")
        
        # Escribir datos
        fieldnames = ['local', 'visitante', 'prob_local', 'prob_empate', 
                     'prob_visitante', 'es_final', 'forma_diferencia', 'lesiones_impact']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for match in matches:
            # Asegurar que todos los campos estén presentes
            csv_row = {
                'local': match['local'],
                'visitante': match['visitante'],
                'prob_local': round(match['prob_local'], 3),
                'prob_empate': round(match['prob_empate'], 3),
                'prob_visitante': round(match['prob_visitante'], 3),
                'es_final': match.get('es_final', False),
                'forma_diferencia': match.get('forma_diferencia', 0),
                'lesiones_impact': match.get('lesiones_impact', 0)
            }
            writer.writerow(csv_row)
        
        return output.getvalue()
    
    def get_available_leagues(self) -> List[str]:
        """Obtiene ligas disponibles"""
        return [
            'premier_league',
            'la_liga', 
            'serie_a',
            'bundesliga',
            'champions_league',
            'liga_mx',
            'brasileirao'
        ]
    
    def close(self):
        """Cierra el agregador"""
        self.aggregator.close_all()