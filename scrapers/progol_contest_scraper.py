# scrapers/progol_contest_scraper.py
"""
Scraper Maestro para obtener la lista oficial de partidos de Progol
de una fuente fiable como Oddschecker.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
import logging

class ProgolContestScraper:
    """
    Obtiene la lista de partidos del concurso de Progol de la semana.
    """
    def __init__(self):
        # La URL de Oddschecker es una fuente fiable que se puede scrapear.
        # En una versión avanzada, podríamos buscar "quiniela progol" en Google
        # y encontrar la URL dinámicamente.
        self.base_url = "https://www.oddschecker.com/es/pronosticos/futbol/quiniela-progol-revancha"
        self.user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_match_list(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Obtiene la lista de partidos de Progol y Revancha.

        Returns:
            Una tupla conteniendo (partidos_regulares, partidos_revancha).
            Cada partido es un diccionario {'local': str, 'visitante': str}.
        """
        partidos_regulares = []
        partidos_revancha = []

        try:
            self.logger.info(f"Accediendo a la URL: {self.base_url}")
            response = requests.get(self.base_url, headers=self.user_agent, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Oddschecker usa 'h2' para los títulos de las secciones.
            # Buscamos la sección de Progol y luego la de Revancha.
            
            # --- Procesa Quiniela Regular (Progol) ---
            progol_section_title = soup.find('h2', string=lambda t: t and 'Progol' in t and 'Revancha' not in t)
            if progol_section_title:
                match_container = progol_section_title.find_next_sibling()
                if match_container:
                    # Los partidos están en elementos con el atributo 'data-track-label'
                    match_elements = match_container.find_all(attrs={'data-track-label': 'Match'})
                    for match_el in match_elements:
                        home_team = match_el.find(class_='_homeTeam_1a72a')
                        away_team = match_el.find(class_='_awayTeam_1a72a')
                        if home_team and away_team:
                            partidos_regulares.append({'local': home_team.text.strip(), 'visitante': away_team.text.strip()})
            
            # --- Procesa Quiniela Revancha ---
            revancha_section_title = soup.find('h2', string=lambda t: t and 'Revancha' in t)
            if revancha_section_title:
                match_container = revancha_section_title.find_next_sibling()
                if match_container:
                    match_elements = match_container.find_all(attrs={'data-track-label': 'Match'})
                    for match_el in match_elements:
                        home_team = match_el.find(class_='_homeTeam_1a72a')
                        away_team = match_el.find(class_='_awayTeam_1a72a')
                        if home_team and away_team:
                            partidos_revancha.append({'local': home_team.text.strip(), 'visitante': away_team.text.strip()})

            self.logger.info(f"Encontrados {len(partidos_regulares)} partidos regulares y {len(partidos_revancha)} de revancha.")

            if not partidos_regulares:
                self.logger.warning("No se pudieron scrapear los partidos regulares. Se usarán datos de fallback.")
                partidos_regulares = self._get_fallback_matches(14)

            if not partidos_revancha:
                self.logger.warning("No se pudieron scrapear los partidos de revancha. Se usarán datos de fallback.")
                partidos_revancha = self._get_fallback_matches(7, offset=14)

            return partidos_regulares[:14], partidos_revancha[:7]

        except Exception as e:
            self.logger.error(f"CRÍTICO: No se pudo obtener la lista de partidos de Progol: {e}")
            return self._get_fallback_matches(14), self._get_fallback_matches(7, offset=14)

    def _get_fallback_matches(self, count, offset=0):
        """Genera partidos de fallback si el scraping falla."""
        # Lista de equipos genérica para usar en caso de fallo total
        equipos = [
            ('Correcaminos', 'Tepatitlan FC'), ('Pachuca', 'Necaxa'), ('Puebla', 'Tijuana'), 
            ('Juarez', 'U.N.A.M.'), ('Philadelphia', 'Inter Miami'), ('New England', 'Vancouver'),
            ('New York RB', 'Nashville SC'), ('Atlanta Utd', 'Houston Dynamo'), ('Charlotte', 'DC United'),
            ('Montreal', 'Real Salt Lake'), ('Orlando City', 'Los Angeles FC'), ('FC Dallas', 'St. Louis City'),
            ('Seattle', 'Minnesota Utd'), ('LA Galaxy', 'Kansas City'),
            # Revancha
            ('España', 'Croacia'), ('Italia', 'Albania'), ('Polonia', 'Países Bajos'),
            ('Eslovenia', 'Dinamarca'), ('Serbia', 'Inglaterra'), ('Rumania', 'Ucrania'),
            ('Bélgica', 'Eslovaquia')
        ]
        fallback_data = equipos[offset:offset+count]
        return [{'local': local, 'visitante': visitante} for local, visitante in fallback_data]