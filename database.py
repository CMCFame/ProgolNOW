"""
Operaciones de base de datos para la aplicación de quinielas.
Utiliza SQLite para almacenar historial de partidos y cambios.
"""
import os
import sqlite3
import json
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Usar un directorio temporal para la base de datos
TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "quiniela_data.db")

def get_connection():
    """
    Obtiene una conexión a la base de datos.
    
    Returns:
        Conexión a SQLite
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para obtener resultados como diccionarios
    return conn

def init_db():
    """Inicializa la base de datos con las tablas necesarias."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla para partidos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY,
        league TEXT,
        home_team TEXT,
        away_team TEXT,
        home_score INTEGER,
        away_score INTEGER,
        result TEXT,
        status_code INTEGER,
        is_live BOOLEAN,
        is_finished BOOLEAN,
        last_updated TEXT
    )
    ''')
    
    # Tabla para historial de cambios en resultados
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS score_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER,
        timestamp TEXT,
        old_result TEXT,
        new_result TEXT,
        home_score INTEGER,
        away_score INTEGER,
        FOREIGN KEY (match_id) REFERENCES matches (match_id)
    )
    ''')
    
    # Tabla para quinielas activas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quinielas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE,
        fecha_creacion TEXT,
        ultima_actualizacion TEXT,
        partidos TEXT,
        selecciones TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def save_match(match_data: Dict[str, Any]) -> None:
    """
    Guarda o actualiza información de un partido.
    
    Args:
        match_data: Diccionario con información del partido
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Comprobar si el partido ya existe
    cursor.execute(
        "SELECT * FROM matches WHERE match_id = ?", 
        (match_data.get('match_id'),)
    )
    existing = cursor.fetchone()
    
    if existing:
        # Actualizar partido existente
        cursor.execute('''
        UPDATE matches
        SET league = ?, home_team = ?, away_team = ?, 
            home_score = ?, away_score = ?, result = ?,
            status_code = ?, is_live = ?, is_finished = ?, last_updated = ?
        WHERE match_id = ?
        ''', (
            match_data.get('league', ''),
            match_data.get('home_team', ''),
            match_data.get('away_team', ''),
            match_data.get('home_score', 0),
            match_data.get('away_score', 0),
            match_data.get('result', ''),
            match_data.get('status_code', 0),
            match_data.get('is_live', False),
            match_data.get('is_finished', False),
            datetime.now().isoformat(),
            match_data.get('match_id')
        ))
    else:
        # Insertar nuevo partido
        cursor.execute('''
        INSERT INTO matches
        (match_id, league, home_team, away_team, home_score, away_score, 
         result, status_code, is_live, is_finished, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_data.get('match_id'),
            match_data.get('league', ''),
            match_data.get('home_team', ''),
            match_data.get('away_team', ''),
            match_data.get('home_score', 0),
            match_data.get('away_score', 0),
            match_data.get('result', ''),
            match_data.get('status_code', 0),
            match_data.get('is_live', False),
            match_data.get('is_finished', False),
            datetime.now().isoformat()
        ))
    
    conn.commit()
    conn.close()

def save_score_change(change_data: Dict[str, Any]) -> None:
    """
    Guarda un cambio en el resultado de un partido.
    
    Args:
        change_data: Diccionario con información del cambio
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO score_changes
    (match_id, timestamp, old_result, new_result, home_score, away_score)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        change_data.get('match_id'),
        change_data.get('timestamp', datetime.now().isoformat()),
        change_data.get('resultado_anterior', ''),
        change_data.get('resultado_nuevo', ''),
        change_data.get('home_score', 0),
        change_data.get('away_score', 0)
    ))
    
    conn.commit()
    conn.close()

def get_active_matches() -> List[Dict[str, Any]]:
    """
    Obtiene todos los partidos activos (en vivo).
    
    Returns:
        Lista de diccionarios con información de partidos activos
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM matches WHERE is_live = 1 ORDER BY league, home_team"
    )
    rows = cursor.fetchall()
    
    result = [dict(row) for row in rows]
    conn.close()
    
    return result

def get_match_by_id(match_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene información de un partido por su ID.
    
    Args:
        match_id: ID del partido
        
    Returns:
        Diccionario con información del partido o None si no existe
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    return dict(row) if row else None

def get_recent_changes(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene los cambios de resultado más recientes.
    
    Args:
        limit: Número máximo de cambios a obtener
        
    Returns:
        Lista de diccionarios con información de cambios recientes
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT sc.*, m.home_team, m.away_team, m.league
    FROM score_changes sc
    JOIN matches m ON sc.match_id = m.match_id
    ORDER BY sc.timestamp DESC
    LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    
    result = [dict(row) for row in rows]
    conn.close()
    
    return result

def save_quiniela(quiniela_data: Dict[str, Any]) -> None:
    """
    Guarda o actualiza una quiniela.
    
    Args:
        quiniela_data: Diccionario con información de la quiniela
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Comprobar si la quiniela ya existe
    cursor.execute(
        "SELECT * FROM quinielas WHERE nombre = ?", 
        (quiniela_data.get('nombre'),)
    )
    existing = cursor.fetchone()
    
    # Convertir listas y diccionarios a JSON
    partidos_json = json.dumps(quiniela_data.get('partidos', []), ensure_ascii=False)
    selecciones_json = json.dumps(quiniela_data.get('selecciones', {}), ensure_ascii=False)
    
    if existing:
        # Actualizar quiniela existente
        cursor.execute('''
        UPDATE quinielas
        SET ultima_actualizacion = ?, partidos = ?, selecciones = ?
        WHERE nombre = ?
        ''', (
            quiniela_data.get('ultima_actualizacion', datetime.now().isoformat()),
            partidos_json,
            selecciones_json,
            quiniela_data.get('nombre')
        ))
    else:
        # Insertar nueva quiniela
        cursor.execute('''
        INSERT INTO quinielas
        (nombre, fecha_creacion, ultima_actualizacion, partidos, selecciones)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            quiniela_data.get('nombre'),
            quiniela_data.get('fecha_creacion', datetime.now().isoformat()),
            quiniela_data.get('ultima_actualizacion', datetime.now().isoformat()),
            partidos_json,
            selecciones_json
        ))
    
    conn.commit()
    conn.close()

def get_quiniela(nombre: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene una quiniela por su nombre.
    
    Args:
        nombre: Nombre de la quiniela
        
    Returns:
        Diccionario con información de la quiniela o None si no existe
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM quinielas WHERE nombre = ?", (nombre,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    # Convertir JSON a estructuras de datos
    quiniela = dict(row)
    quiniela['partidos'] = json.loads(quiniela.get('partidos', '[]'))
    quiniela['selecciones'] = json.loads(quiniela.get('selecciones', '{}'))
    
    conn.close()
    
    return quiniela

def list_quinielas() -> List[Dict[str, Any]]:
    """
    Lista todas las quinielas disponibles.
    
    Returns:
        Lista de diccionarios con información básica de quinielas
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, nombre, fecha_creacion, ultima_actualizacion FROM quinielas ORDER BY nombre"
    )
    rows = cursor.fetchall()
    
    result = [dict(row) for row in rows]
    conn.close()
    
    return result

def delete_quiniela(nombre: str) -> bool:
    """
    Elimina una quiniela.
    
    Args:
        nombre: Nombre de la quiniela a eliminar
        
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM quinielas WHERE nombre = ?", (nombre,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    except Exception as e:
        print(f"Error al eliminar quiniela: {e}")
        return False
    finally:
        conn.close()

# Inicializar la base de datos al importar este módulo
init_db()