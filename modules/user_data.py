# modules/user_data.py
import streamlit as st
import json
import os
from datetime import datetime

def load_user_data():
    """
    Carga los datos del usuario desde el almacenamiento
    
    Returns:
        dict: Datos del usuario o datos por defecto si no existen
    """
    # En un entorno de producción, estos datos vendrían de una base de datos
    # o archivos persistentes. Para desarrollo, usamos datos de sesión y/o archivo local.
    
    # Intentar cargar desde archivo local
    try:
        if os.path.exists("user_data.json"):
            with open("user_data.json", "r") as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"No se pudieron cargar datos: {str(e)}")
    
    # Datos por defecto
    return {
        "current_journey": "Jornada #24",
        "predictions": {
            "main": [None] * 14,
            "revenge": [None] * 7
        },
        "stats": {
            "quinielas": 8,
            "aciertos": 76,
            "puntos": 112,
            "mejor_jornada": {
                "numero": 18,
                "fecha": "12/02/2023",
                "aciertos": 14
            }
        },
        "history": [
            {"id": 1, "week": 23, "date": "05/04/2023", "correct": 9, "points": 12},
            {"id": 2, "week": 22, "date": "29/03/2023", "correct": 7, "points": 10},
            {"id": 3, "week": 21, "date": "22/03/2023", "correct": 11, "points": 15},
            {"id": 4, "week": 20, "date": "15/03/2023", "correct": 8, "points": 11},
            {"id": 5, "week": 19, "date": "08/03/2023", "correct": 10, "points": 14},
            {"id": 6, "week": 18, "date": "01/03/2023", "correct": 14, "points": 20},
            {"id": 7, "week": 17, "date": "22/02/2023", "correct": 6, "points": 8},
            {"id": 8, "week": 16, "date": "15/02/2023", "correct": 9, "points": 12}
        ]
    }

def save_user_data(user_data):
    """
    Guarda los datos del usuario en el almacenamiento
    
    Args:
        user_data (dict): Datos del usuario a guardar
    """
    # Actualizar fecha de modificación
    user_data["last_updated"] = datetime.now().isoformat()
    
    # Guardar en el estado de sesión
    st.session_state.user_data = user_data
    
    # En desarrollo, también guardamos en archivo local
    try:
        with open("user_data.json", "w") as f:
            json.dump(user_data, f, indent=4)
    except Exception as e:
        st.warning(f"No se pudieron guardar datos: {str(e)}")
    
    return user_data