# modules/live_matches.py
import streamlit as st
import time
from utils.api_client import FootballAPIClient
from datetime import datetime

def show_live_matches():
    """
    Muestra los partidos en vivo y próximos utilizando la API-Football
    """
    # Crear cliente de API
    football_api = FootballAPIClient()
    
    # Contenedor para refrescar automáticamente
    refresh_container = st.empty()
    
    with refresh_container.container():
        # Encabezado de sección
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("Partidos en Vivo")
        with col2:
            # Opciones de actualización
            refresh_interval = st.selectbox(
                "Actualizar cada:",
                options=[30, 60, 300],
                format_func=lambda x: f"{x//60} min {x%60} seg" if x >= 60 else f"{x} seg",
                index=1
            )
            
            last_update = datetime.now().strftime("%H:%M:%S")
            st.caption(f"Última actualización: {last_update}")
        
        # Cargar datos de partidos en vivo
        try:
            with st.spinner("Cargando partidos en vivo..."):
                live_matches = football_api.get_live_matches()
            
            if not live_matches:
                st.info("No hay partidos en vivo en este momento.", icon="ℹ️")
            else:
                # Mostrar partidos en vivo
                for match in live_matches:
                    render_live_match(match)
        except Exception as e:
            st.error(f"Error al cargar partidos en vivo: {str(e)}")
            st.button("Reintentar", on_click=lambda: None)
        
        # Mostrar próximos partidos
        st.markdown("---")
        st.header("Próximos Partidos")
        
        try:
            upcoming_matches = football_api.get_upcoming_matches()
            
            if not upcoming_matches:
                st.info("No hay próximos partidos programados.")
            else:
                # Mostrar próximos partidos
                for match in upcoming_matches:
                    render_upcoming_match(match)
        except Exception as e:
            st.error(f"Error al cargar próximos partidos: {str(e)}")
    
    # Actualización automática
    if refresh_interval > 0:
        time.sleep(refresh_interval)
        st.rerun()

def render_live_match(match):
    """
    Renderiza un partido en vivo
    
    Args:
        match (dict): Datos del partido en vivo
    """
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 2])
        
        # Equipo local
        with col1:
            st.markdown(f"""
            <div class='team-container'>
                <img src="{match['homeLogo']}" class="team-logo">
                <div class="team-name">{match['home']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Marcador y minuto
        with col2:
            st.markdown(f"""
            <div class='score-container'>
                <div class="live-indicator">EN VIVO • {match['minute']}'</div>
                <div class="score">
                    <span class="score-number">{match['homeScore']}</span>
                    <span class="score-divider">-</span>
                    <span class="score-number">{match['awayScore']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Equipo visitante
        with col3:
            st.markdown(f"""
            <div class='team-container'>
                <img src="{match['awayLogo']}" class="team-logo">
                <div class="team-name">{match['away']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")

def render_upcoming_match(match):
    """
    Renderiza un próximo partido
    
    Args:
        match (dict): Datos del próximo partido
    """
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 2])
        
        # Equipo local
        with col1:
            st.markdown(f"""
            <div class='team-container'>
                <img src="{match['homeLogo']}" class="team-logo">
                <div class="team-name">{match['home']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Fecha y hora
        with col2:
            match_date = datetime.fromisoformat(match['date'].replace('Z', '+00:00'))
            date_str = match_date.strftime("%d/%m/%Y")
            time_str = match_date.strftime("%H:%M")
            
            st.markdown(f"""
            <div class='match-date-container'>
                <div class="match-date">{date_str}</div>
                <div class="match-time">{time_str}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Equipo visitante
        with col3:
            st.markdown(f"""
            <div class='team-container'>
                <img src="{match['awayLogo']}" class="team-logo">
                <div class="team-name">{match['away']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Botón recordatorio
        col1, col2, col3 = st.columns([4, 2, 4])
        with col2:
            if st.button(f"⏰ Recordarme", key=f"remind_{match['id']}"):
                st.toast(f"Te recordaremos el partido {match['home']} vs {match['away']}")
        
        st.markdown("---")