# scrapers/template_generator.py
"""
Generador automático de templates CSV
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Optional

class TemplateGenerator:
    """Genera templates CSV automáticamente"""
    
    def __init__(self, odds_api_key: Optional[str] = None):
        self.odds_api_key = odds_api_key
        self.aggregator = None
        
        # Importación lazy del agregador
        try:
            from .data_aggregator import DataAggregator
            self.aggregator = DataAggregator(odds_api_key)
        except ImportError as e:
            print(f"Warning: No se pudo importar DataAggregator: {e}")
            self.aggregator = None
    
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
        
        # Intentar obtener datos reales
        matches = []
        if self.aggregator:
            try:
                matches = self.aggregator.get_matches(league, target_count)
            except Exception as e:
                print(f"Error obteniendo datos reales: {e}")
                matches = []
        
        if not matches:
            # Fallback a datos sintéticos
            return self._generate_synthetic_template(tipo, league, target_count)
        
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
                'local': match.get('local', 'Team A'),
                'visitante': match.get('visitante', 'Team B'),
                'prob_local': round(match.get('prob_local', 0.4), 3),
                'prob_empate': round(match.get('prob_empate', 0.3), 3),
                'prob_visitante': round(match.get('prob_visitante', 0.3), 3),
                'es_final': match.get('es_final', False),
                'forma_diferencia': match.get('forma_diferencia', 0),
                'lesiones_impact': match.get('lesiones_impact', 0)
            }
            writer.writerow(csv_row)
        
        return output.getvalue()
    
    def _generate_synthetic_template(self, tipo: str, league: str, count: int) -> str:
        """Genera template sintético cuando fallan los scrapers"""
        output = io.StringIO()
        
        # Comentarios de cabecera
        output.write(f"# Template {tipo.upper()} sintético (fallback)\n")
        output.write(f"# Liga objetivo: {league}\n")
        output.write(f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"# Razón: Scraping no disponible o falló\n")
        output.write(f"# Total partidos: {count}\n")
        output.write("#\n\n")
        
        # Equipos sintéticos por liga
        synthetic_teams = self._get_synthetic_teams(league, count)
        
        # Escribir datos
        fieldnames = ['local', 'visitante', 'prob_local', 'prob_empate', 
                     'prob_visitante', 'es_final', 'forma_diferencia', 'lesiones_impact']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        import random
        random.seed(42)  # Consistencia
        
        for i, (local, visitante) in enumerate(synthetic_teams):
            # Generar probabilidades realistas
            if i == 0:  # Primer partido como clásico
                prob_local, prob_empate, prob_visitante = 0.35, 0.30, 0.35
                es_final = True
            elif tipo == 'revancha' and i < 2:  # Más empates en revancha
                prob_local = random.uniform(0.28, 0.40)
                prob_empate = random.uniform(0.30, 0.42)
                prob_visitante = 1.0 - prob_local - prob_empate
                es_final = True
            else:
                prob_local = random.uniform(0.25, 0.50)
                prob_empate = random.uniform(0.20, 0.35)
                prob_visitante = 1.0 - prob_local - prob_empate
                es_final = False
            
            # Verificar validez
            if prob_visitante < 0.15:
                prob_visitante = 0.15
                total = prob_local + prob_empate + prob_visitante
                prob_local /= total
                prob_empate /= total
                prob_visitante /= total
            
            csv_row = {
                'local': local,
                'visitante': visitante,
                'prob_local': round(prob_local, 3),
                'prob_empate': round(prob_empate, 3),
                'prob_visitante': round(prob_visitante, 3),
                'es_final': es_final,
                'forma_diferencia': random.randint(-2, 2),
                'lesiones_impact': random.randint(-1, 1)
            }
            writer.writerow(csv_row)
        
        return output.getvalue()
    
    def _get_synthetic_teams(self, league: str, count: int) -> List[tuple]:
        """Obtiene equipos sintéticos por liga"""
        
        teams_by_league = {
            'premier_league': [
                ('Manchester United', 'Liverpool'), ('Chelsea', 'Arsenal'),
                ('Manchester City', 'Tottenham'), ('Newcastle', 'Brighton'),
                ('Aston Villa', 'West Ham'), ('Crystal Palace', 'Fulham'),
                ('Brentford', 'Wolves'), ('Nottingham Forest', 'Everton'),
                ('Bournemouth', 'Luton'), ('Burnley', 'Sheffield United'),
                ('Leeds United', 'Leicester'), ('Southampton', 'Norwich'),
                ('Watford', 'Cardiff'), ('Swansea', 'Millwall')
            ],
            'la_liga': [
                ('Real Madrid', 'Barcelona'), ('Atletico Madrid', 'Sevilla'),
                ('Valencia', 'Athletic Bilbao'), ('Real Sociedad', 'Villarreal'),
                ('Real Betis', 'Getafe'), ('Osasuna', 'Las Palmas'),
                ('Celta Vigo', 'Alaves'), ('Mallorca', 'Girona'),
                ('Cadiz', 'Granada'), ('Almeria', 'Rayo Vallecano'),
                ('Espanyol', 'Valladolid'), ('Elche', 'Leganes'),
                ('Deportivo', 'Sporting'), ('Racing', 'Tenerife')
            ],
            'liga_mx': [
                ('America', 'Chivas'), ('Cruz Azul', 'Pumas'),
                ('Monterrey', 'Tigres'), ('Santos', 'Leon'),
                ('Toluca', 'Atlas'), ('Puebla', 'Queretaro'),
                ('Tijuana', 'Juarez'), ('Necaxa', 'Pachuca'),
                ('Mazatlan', 'San Luis'), ('FC Juarez', 'Atletico San Luis'),
                ('Morelia', 'Veracruz'), ('Lobos BUAP', 'Dorados'),
                ('Tecos', 'Jaguares'), ('Indios', 'La Piedad')
            ],
            'brasileirao': [
                ('Flamengo', 'Palmeiras'), ('Corinthians', 'Sao Paulo'),
                ('Santos', 'Fluminense'), ('Atletico Mineiro', 'Cruzeiro'),
                ('Gremio', 'Internacional'), ('Botafogo', 'Vasco'),
                ('Athletico Paranaense', 'Coritiba'), ('Fortaleza', 'Ceara'),
                ('Bahia', 'Vitoria'), ('Sport', 'Nautico'),
                ('Goias', 'Vila Nova'), ('Cuiaba', 'Operario'),
                ('Bragantino', 'Ponte Preta'), ('America MG', 'Criciuma')
            ]
        }
        
        # Usar equipos de la liga o fallback
        teams = teams_by_league.get(league, teams_by_league['premier_league'])
        
        # Asegurar que tenemos suficientes equipos
        while len(teams) < count:
            teams.extend(teams)  # Duplicar si es necesario
        
        return teams[:count]
    
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
        if self.aggregator and hasattr(self.aggregator, 'close_all'):
            try:
                self.aggregator.close_all()
            except Exception as e:
                print(f"Error cerrando agregador: {e}")