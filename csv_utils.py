"""
Utilidades para trabajar con archivos CSV de partidos Progol.
"""
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

def parse_progol_csv(csv_content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parsea el contenido de un CSV con los partidos de Progol.
    
    Formato esperado del CSV:
    fecha,hora,local,visitante,liga,revancha
    2025-04-19,19:00,Equipo A,Equipo B,Liga MX,0
    
    Donde revancha=1 indica partidos de revancha (opcionales)
    
    Args:
        csv_content: Contenido del archivo CSV como string
        
    Returns:
        Tupla de (partidos_regulares, partidos_revancha)
    """
    partidos_regulares = []
    partidos_revancha = []
    
    try:
        # Leer el CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        
        for i, row in enumerate(reader):
            # Validar campos requeridos
            required_fields = ['fecha', 'hora', 'local', 'visitante', 'liga']
            if not all(field in row for field in required_fields):
                missing = [field for field in required_fields if field not in row]
                raise ValueError(f"Fila {i+1}: Faltan campos requeridos: {', '.join(missing)}")
            
            # Crear fecha completa
            try:
                fecha_str = f"{row['fecha']} {row['hora']}"
                fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
                fecha_iso = fecha_obj.isoformat()
            except ValueError:
                # Si hay error de formato, usar la fecha actual
                fecha_iso = datetime.now().isoformat()
            
            # Determinar si es partido regular o revancha
            es_revancha = int(row.get('revancha', '0')) == 1
            
            # Crear objeto de partido
            partido = {
                'match_id': 1000000 + i,  # ID temporal
                'home_team': row['local'],
                'away_team': row['visitante'],
                'league': row['liga'],
                'scheduled_time': fecha_iso,
                'is_revancha': es_revancha
            }
            
            # Agregar a la lista correspondiente
            if es_revancha:
                partidos_revancha.append(partido)
            else:
                partidos_regulares.append(partido)
        
        # Verificar que haya exactamente 14 partidos regulares y hasta 7 de revancha
        if len(partidos_regulares) != 14:
            raise ValueError(f"Se esperaban exactamente 14 partidos regulares, pero se encontraron {len(partidos_regulares)}")
        
        if len(partidos_revancha) > 7:
            raise ValueError(f"Se permiten máximo 7 partidos de revancha, pero se encontraron {len(partidos_revancha)}")
        
        return partidos_regulares, partidos_revancha
        
    except Exception as e:
        raise ValueError(f"Error al procesar el CSV: {str(e)}")

def generate_sample_csv() -> str:
    """
    Genera un CSV de ejemplo con partidos Progol.
    
    Returns:
        Contenido del CSV de ejemplo
    """
    sample_data = [
        "fecha,hora,local,visitante,liga,revancha",
        "2025-04-19,19:00,Juárez,Querétaro,Liga MX,0",
        "2025-04-19,19:00,Oaxaca,Sinaloa,Liga Expansion MX,0",
        "2025-04-19,19:00,Tampico,Atlante,Liga Expansion MX,0",
        "2025-04-19,21:00,Tigres,Pumas,Liga MX,0",
        "2025-04-19,19:05,Toluca,Cruz Azul,Liga MX,0",
        "2025-04-19,21:15,Atlas,Guadalajara,Liga MX,0",
        "2025-04-19,14:30,Columbus,Miami,MLS,0",
        "2025-04-19,18:00,Gremio,Inter P.A.,Brasileirao,0",
        "2025-04-19,07:00,Lecce,Como,Serie A,0",
        "2025-04-19,08:00,Brentford,Brighton,EPL,0",
        "2025-04-19,10:30,Aston Villa,Newcastle,EPL,0",
        "2025-04-19,10:30,Union Berlin,Stuttgart,Bundesliga,0",
        "2025-04-20,07:00,Fulham,Chelsea,EPL,0",
        "2025-04-20,09:15,Brestois,Lens,Ligue 1,0",
        "2025-04-20,17:00,Santos,Tijuana,Liga MX,1",
        "2025-04-20,19:05,León,Monterrey,Liga MX,1",
        "2025-04-20,12:45,Milan,Atalanta,Serie A,1",
        "2025-04-20,13:00,O. Higgins,Palestino,Liga Chilena,1",
        "2025-04-20,15:00,Sarmiento,Platense,Argentina Liga Profesional,1",
        "2025-04-20,19:00,San Luis,Pachuca,Liga MX,1",
        "2025-04-21,20:00,Puebla,Necaxa,Liga MX,1"
    ]
    
    return "\n".join(sample_data)