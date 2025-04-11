# modules/ui_components.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import matplotlib.pyplot as plt
import base64
from utils.helpers import format_date, create_download_link

def create_tabs(tabs_list):
    """
    Crea un conjunto de pestañas y devuelve la seleccionada
    
    Args:
        tabs_list (list): Lista de nombres de pestañas
    
    Returns:
        str: Nombre de la pestaña seleccionada
    """
    # Si ya hay una pestaña seleccionada, la mantenemos
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = tabs_list[0]
    
    # Crear contenedor para las pestañas
    tab_cols = st.columns(len(tabs_list))
    
    # Para cada pestaña, crear un botón
    for i, tab in enumerate(tabs_list):
        with tab_cols[i]:
            # Si se hace clic en una pestaña, actualizar la seleccionada
            if st.button(
                tab, 
                key=f"tab_{i}",
                use_container_width=True,
                type="primary" if st.session_state.selected_tab == tab else "secondary"
            ):
                st.session_state.selected_tab = tab
                st.rerun()
    
    # Devolver la pestaña seleccionada
    return st.session_state.selected_tab

def show_history(user_data):
    """
    Muestra el historial de quinielas
    
    Args:
        user_data (dict): Datos del usuario
    """
    st.header("Historial de Quinielas")
    
    # Datos de historial
    history_data = user_data.get("history", [
        {"id": 1, "week": 23, "date": "05/04/2023", "correct": 9, "points": 12},
        {"id": 2, "week": 22, "date": "29/03/2023", "correct": 7, "points": 10},
        {"id": 3, "week": 21, "date": "22/03/2023", "correct": 11, "points": 15},
        {"id": 4, "week": 20, "date": "15/03/2023", "correct": 8, "points": 11},
        {"id": 5, "week": 19, "date": "08/03/2023", "correct": 10, "points": 14},
        {"id": 6, "week": 18, "date": "01/03/2023", "correct": 14, "points": 20},
        {"id": 7, "week": 17, "date": "22/02/2023", "correct": 6, "points": 8},
        {"id": 8, "week": 16, "date": "15/02/2023", "correct": 9, "points": 12}
    ])
    
    # Convertir a DataFrame para mostrar como tabla
    df = pd.DataFrame(history_data)
    df = df[["week", "date", "correct", "points"]]
    df.columns = ["Jornada", "Fecha", "Aciertos", "Puntos"]
    
    # Mostrar tabla con estilo
    st.dataframe(
        df,
        column_config={
            "Jornada": st.column_config.NumberColumn(format="%d"),
            "Aciertos": st.column_config.ProgressColumn(
                "Aciertos", format="%d", min_value=0, max_value=14,
                help="Número de aciertos en la jornada"
            ),
            "Puntos": st.column_config.NumberColumn(
                "Puntos", format="%d",
                help="Puntos obtenidos"
            )
        },
        use_container_width=True
    )
    
    # Botón para ver detalles
    with st.expander("Ver detalles de una jornada", expanded=False):
        selected_id = st.selectbox(
            "Selecciona una jornada",
            options=[item["id"] for item in history_data],
            format_func=lambda x: f"Jornada #{history_data[x-1]['week']} ({history_data[x-1]['date']})"
        )
        
        if st.button("Ver resultados detallados", use_container_width=True):
            show_history_details(selected_id, history_data)

def show_history_details(history_id, history_data):
    """
    Muestra los detalles de una jornada específica del historial
    
    Args:
        history_id (int): ID de la jornada
        history_data (list): Datos del historial
    """
    # Encontrar la jornada seleccionada
    item = next((item for item in history_data if item["id"] == history_id), None)
    
    if not item:
        st.error("No se encontró la jornada seleccionada")
        return
    
    # Mostrar detalles en un modal
    with st.container():
        st.subheader(f"Jornada #{item['week']} - {item['date']}")
        st.success(f"¡Buen trabajo! Acertaste {item['correct']} de 14 partidos principales y ganaste {item['points']} puntos.")
        
        # Mostrar predicciones vs resultados reales
        st.markdown("#### Tus predicciones vs Resultados reales")
        
        # Datos de ejemplo para ilustrar
        match_results = [
            {"match": "América 2-1 Cruz Azul", "prediction": "L", "result": "L", "correct": True},
            {"match": "Guadalajara 0-0 Monterrey", "prediction": "E", "result": "E", "correct": True},
            {"match": "Tigres 1-0 Puebla", "prediction": "L", "result": "L", "correct": True},
            {"match": "Santos 2-3 Pachuca", "prediction": "L", "result": "V", "correct": False},
            {"match": "Atlas 1-1 León", "prediction": "E", "result": "E", "correct": True},
            {"match": "Necaxa 0-2 Mazatlán", "prediction": "L", "result": "V", "correct": False},
            {"match": "Juárez 1-0 Toluca", "prediction": "L", "result": "L", "correct": True}
        ]
        
        for result in match_results:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(result["match"])
            
            with col2:
                if result["correct"]:
                    st.success(f"Acertaste ({result['prediction']})")
                else:
                    st.error(f"Fallaste ({result['prediction']})")

def show_statistics(user_data):
    """
    Muestra estadísticas detalladas del usuario
    
    Args:
        user_data (dict): Datos del usuario
    """
    st.header("Mis Estadísticas Detalladas")
    
    # Distribución de predicciones
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribución de Predicciones")
        
        # Datos para el gráfico
        prediction_counts = {"L": 45, "E": 25, "V": 30}
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(
            prediction_counts.values(), 
            labels=["Local (L)", "Empate (E)", "Visitante (V)"],
            autopct='%1.1f%%',
            colors=['#3b82f6', '#9ca3af', '#ef4444'],
            startangle=90,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}
        )
        ax.axis('equal')
        st.pyplot(fig)
    
    with col2:
        st.subheader("Evolución de Aciertos")
        
        # Datos para el gráfico
        evolution_data = {
            "Jornada": [16, 17, 18, 19, 20, 21, 22, 23],
            "Aciertos": [9, 6, 14, 10, 8, 11, 7, 9],
            "Puntos": [12, 8, 20, 14, 11, 15, 10, 12]
        }
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(evolution_data["Jornada"], evolution_data["Aciertos"], marker='o', linestyle='-', color='#10b981', label='Aciertos')
        ax.plot(evolution_data["Jornada"], evolution_data["Puntos"], marker='s', linestyle='-', color='#8b5cf6', label='Puntos')
        ax.set_xlabel('Jornada')
        ax.set_ylabel('Cantidad')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        st.pyplot(fig)
    
    # Rendimiento por equipo
    st.subheader("Rendimiento por Equipo")
    
    # Datos de ejemplo
    team_stats = [
        {"team": "América", "predictions": 12, "correct": 8, "percentage": 67},
        {"team": "Cruz Azul", "predictions": 10, "correct": 6, "percentage": 60},
        {"team": "Guadalajara", "predictions": 11, "correct": 7, "percentage": 64},
        {"team": "Monterrey", "predictions": 9, "correct": 5, "percentage": 56},
        {"team": "Tigres", "predictions": 8, "correct": 5, "percentage": 63},
        {"team": "Pachuca", "predictions": 7, "correct": 4, "percentage": 57}
    ]
    
    # Convertir a DataFrame
    df_teams = pd.DataFrame(team_stats)
    
    # Mostrar tabla con barras de progreso
    st.dataframe(
        df_teams,
        column_config={
            "team": "Equipo",
            "predictions": "Predicciones",
            "correct": "Aciertos",
            "percentage": st.column_config.ProgressColumn(
                "% Acierto",
                format="%d%%",
                min_value=0,
                max_value=100
            )
        },
        use_container_width=True
    )

def render_clasificacion_item(item):
    """
    Renderiza un elemento de la clasificación
    
    Args:
        item (dict): Datos del elemento de clasificación
    """
    # Crear contenedor para el elemento
    with st.container():
        col1, col2, col3 = st.columns([1, 4, 2])
        
        with col1:
            # Posición
            if item["pos"] == 1:
                st.markdown("🥇")
            elif item["pos"] == 2:
                st.markdown("🥈")
            elif item["pos"] == 3:
                st.markdown("🥉")
            else:
                st.write(f"{item['pos']}.")
        
        with col2:
            # Nombre
            if item["nombre"] == "Tú":
                st.markdown(f"**{item['nombre']}**")
            else:
                st.write(item["nombre"])
        
        with col3:
            # Puntos
            st.markdown(f"<div style='background-color: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px; text-align: center; font-size: 0.9em;'>{item['puntos']} pts</div>", unsafe_allow_html=True)

def download_user_data(user_data):
    """
    Permite descargar los datos del usuario en formato JSON
    
    Args:
        user_data (dict): Datos del usuario
    """
    # Generar JSON
    json_str = json.dumps(user_data, indent=4)
    
    # Generar nombre de archivo con fecha
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"progol_data_{now}.json"
    
    # Botón de descarga
    st.download_button(
        label="Descargar datos en JSON",
        data=json_str,
        file_name=filename,
        mime="application/json",
        use_container_width=True
    )

def show_notification(message, type="info"):
    """
    Muestra una notificación al usuario
    
    Args:
        message (str): Mensaje a mostrar
        type (str): Tipo de notificación (info, success, warning, error)
    """
    if type == "success":
        st.success(message)
    elif type == "warning":
        st.warning(message)
    elif type == "error":
        st.error(message)
    else:
        st.info(message)

def render_prediction_badge(prediction):
    """
    Renderiza una insignia con la predicción (L, E, V)
    
    Args:
        prediction (str): Predicción (L, E, V)
    
    Returns:
        str: HTML de la insignia
    """
    if prediction == "L":
        return """<span style="background-color: #dbeafe; color: #1e40af; padding: 2px 10px; border-radius: 12px; font-weight: bold;">L</span>"""
    elif prediction == "E":
        return """<span style="background-color: #e5e7eb; color: #374151; padding: 2px 10px; border-radius: 12px; font-weight: bold;">E</span>"""
    elif prediction == "V":
        return """<span style="background-color: #fee2e2; color: #b91c1c; padding: 2px 10px; border-radius: 12px; font-weight: bold;">V</span>"""
    else:
        return """<span style="background-color: #f8fafc; color: #94a3b8; padding: 2px 10px; border-radius: 12px; font-weight: bold; border: 1px dashed #94a3b8;">?</span>"""

def create_match_card(match, show_prediction=False, prediction=None, show_result=False):
    """
    Crea una tarjeta para mostrar un partido
    
    Args:
        match (dict): Datos del partido
        show_prediction (bool): Mostrar predicción
        prediction (str): Predicción (L, E, V)
        show_result (bool): Mostrar resultado
    
    Returns:
        None
    """
    with st.container():
        # Crear marco con sombra y bordes redondeados
        st.markdown("""
        <style>
        .match-card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            background-color: white;
            margin-bottom: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="match-card">', unsafe_allow_html=True)
        
        # Distribución: Equipo local - Resultado/Hora - Equipo visitante
        col1, col2, col3 = st.columns([5, 4, 5])
        
        # Equipo local
        with col1:
            st.markdown(f"""
            <div style="display: flex; align-items: center;">
                <img src="{match.get('homeLogo', 'https://via.placeholder.com/30')}" style="width: 30px; height: 30px; margin-right: 8px;">
                <span style="font-weight: 500;">{match.get('home', 'Equipo Local')}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Marcador o fecha
        with col2:
            if show_result and 'homeScore' in match and 'awayScore' in match:
                # Mostrar marcador
                status = match.get('status', '')
                minute = match.get('minute', '')
                
                # Status indicator color
                status_color = "#ef4444" if status == "live" else "#9ca3af"
                
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="font-size: 0.8em; color: {status_color}; margin-bottom: 4px;">
                        {status.upper() if status else ''} {f"• {minute}'" if minute else ''}
                    </div>
                    <div style="font-size: 1.4em; font-weight: bold;">
                        {match.get('homeScore', '-')} - {match.get('awayScore', '-')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Mostrar fecha/hora
                date_str = format_date(match.get('date', ''), "%d/%m/%Y")
                time_str = format_date(match.get('date', ''), "%H:%M")
                
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="font-size: 0.9em; font-weight: 500;">{date_str}</div>
                    <div style="font-size: 0.8em; color: #6b7280;">{time_str}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Equipo visitante
        with col3:
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: flex-end;">
                <span style="font-weight: 500;">{match.get('away', 'Equipo Visitante')}</span>
                <img src="{match.get('awayLogo', 'https://via.placeholder.com/30')}" style="width: 30px; height: 30px; margin-left: 8px;">
            </div>
            """, unsafe_allow_html=True)
        
        # Mostrar predicción si se solicita
        if show_prediction:
            st.markdown(f"""
            <div style="display: flex; justify-content: center; margin-top: 8px;">
                <div style="font-size: 0.9em; color: #6b7280; margin-right: 6px;">Tu predicción:</div>
                {render_prediction_badge(prediction)}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def import_user_data():
    """
    Función para importar datos de usuario desde un archivo JSON
    
    Returns:
        dict: Datos importados o None si hay error
    """
    uploaded_file = st.file_uploader(
        "Selecciona un archivo JSON para importar", 
        type=["json"],
        help="Archivo exportado previamente de Progol Tracker"
    )
    
    if uploaded_file:
        try:
            content = uploaded_file.getvalue().decode("utf-8")
            data = json.loads(content)
            return data
        except Exception as e:
            st.error(f"Error al importar el archivo: {str(e)}")
            return None
    
    return None