"""
Aplicación principal para Quiniela Progol.
Interfaces de usuario con Streamlit.
"""
import streamlit as st
import pandas as pd
import time
import threading
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Importar módulos de la aplicación
from data_service import SofascoreDataService
from quiniela_manager import QuinielaManager, ProgolQuiniela
from scheduler import QuinielaScheduler, UpdateEvent
import database as db
from config import COLORS, MATCH_STATUS, UPDATE_INTERVAL, MAX_QUINIELAS_POR_USUARIO, setup_directories, LIGAS_PROGOL

# Configurar página de Streamlit
st.set_page_config(
    page_title="Quiniela Progol Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Asegurar que los directorios necesarios existen
setup_directories()

# Inicializar el estado de la sesión
if 'data_service' not in st.session_state:
    st.session_state.data_service = SofascoreDataService()

if 'quiniela_manager' not in st.session_state:
    st.session_state.quiniela_manager = QuinielaManager()

if 'scheduler' not in st.session_state:
    st.session_state.scheduler = QuinielaScheduler(update_interval=UPDATE_INTERVAL)
    # Configurar el scheduler pero no iniciarlo automáticamente mediante un hilo
    st.session_state.scheduler.set_data_service(st.session_state.data_service)
    st.session_state.scheduler.set_quiniela_manager(st.session_state.quiniela_manager)
    
    # Variable para controlar si el scheduler está en ejecución
    st.session_state.scheduler_running = False

if 'notifications' not in st.session_state:
    st.session_state.notifications = []

if 'last_update' not in st.session_state:
    st.session_state.last_update = None

# Función para iniciar el scheduler manualmente
def start_scheduler():
    if not st.session_state.scheduler_running:
        try:
            st.session_state.scheduler.start()
            st.session_state.scheduler_running = True
            st.success("Servicio de actualización iniciado correctamente")
        except Exception as e:
            st.error(f"Error al iniciar servicio de actualización: {e}")

# Botón para iniciar actualizaciones (en sidebar)
if st.sidebar.button("▶️ Iniciar servicio de actualización"):
    start_scheduler()

# Funciones auxiliares de la interfaz
def add_notification(tipo: str, mensaje: str, timestamp: Optional[datetime] = None):
    """Añade una notificación al sistema."""
    timestamp = timestamp or datetime.now()
    st.session_state.notifications.insert(0, {
        'tipo': tipo,
        'mensaje': mensaje,
        'timestamp': timestamp
    })
    
    # Limitar a 50 notificaciones
    if len(st.session_state.notifications) > 50:
        st.session_state.notifications = st.session_state.notifications[:50]

def format_timestamp(timestamp):
    """Formatea un timestamp para mostrar."""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return timestamp
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.total_seconds() < 60:
        return "hace unos segundos"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"hace {minutes} {'minuto' if minutes == 1 else 'minutos'}"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"hace {hours} {'hora' if hours == 1 else 'horas'}"
    else:
        return timestamp.strftime("%d/%m/%Y %H:%M")

def mostrar_resultado_quiniela(resultado: str):
    """Muestra un resultado de quiniela con formato y color."""
    if resultado not in MATCH_STATUS:
        return resultado
    
    color = MATCH_STATUS[resultado]["color"]
    text = MATCH_STATUS[resultado]["text"]
    
    return f"<span style='color:{color};font-weight:bold;'>{resultado} ({text})</span>"

# Funciones para las secciones de la aplicación
def seccion_partidos_activos():
    """Muestra los partidos activos actualmente."""
    st.header("🎮 Partidos en vivo")
    
    # Obtener partidos activos de la base de datos
    active_matches = db.get_active_matches()
    
    # Si no hay partidos activos, mostrar mensaje
    if not active_matches:
        st.info("No hay partidos en vivo en este momento.")
        if st.button("🔄 Buscar partidos en vivo"):
            with st.spinner("Buscando partidos..."):
                st.session_state.scheduler.force_update()
                st.rerun()
        return
    
    # Agrupar por liga
    matches_by_league = {}
    for match in active_matches:
        league = match.get('league', 'Otra liga')
        if league not in matches_by_league:
            matches_by_league[league] = []
        matches_by_league[league].append(match)
    
    # Mostrar partidos por liga
    for league, matches in matches_by_league.items():
        with st.expander(f"{league} ({len(matches)} partidos en vivo)", expanded=True):
            for match in matches:
                col1, col2, col3 = st.columns([4, 2, 1])
                
                # Información básica del partido
                with col1:
                    st.markdown(f"**{match['home_team']} vs {match['away_team']}**")
                
                # Marcador
                with col2:
                    st.markdown(
                        f"<h2 style='text-align: center;'>{match['home_score']} - {match['away_score']}</h2>",
                        unsafe_allow_html=True
                    )
                
                # Resultado para quiniela
                with col3:
                    st.markdown(
                        mostrar_resultado_quiniela(match['result']),
                        unsafe_allow_html=True
                    )
                
                st.markdown("---")

def seccion_mis_quinielas():
    """Gestiona las quinielas del usuario."""
    st.header("🎲 Mis Quinielas")
    
    # Obtener lista de quinielas
    quinielas = db.list_quinielas()
    
    if not quinielas:
        st.info("No tienes quinielas registradas.")
    else:
        # Mostrar lista de quinielas
        st.subheader(f"Tienes {len(quinielas)} quinielas")
        
        for quiniela_info in quinielas:
            nombre = quiniela_info['nombre']
            fecha = format_timestamp(quiniela_info['ultima_actualizacion'])
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{nombre}** (última actualización: {fecha})")
            
            with col2:
                if st.button("Ver detalle", key=f"btn_ver_{nombre}"):
                    st.session_state.quiniela_seleccionada = nombre
                    st.rerun()
    
    # Botón para crear nueva quiniela
    if len(quinielas) < MAX_QUINIELAS_POR_USUARIO:
        if st.button("➕ Crear nueva quiniela"):
            st.session_state.creando_quiniela = True
            st.rerun()

def seccion_detalle_quiniela(nombre_quiniela: str):
    """Muestra el detalle de una quiniela específica."""
    st.header(f"📋 Quiniela: {nombre_quiniela}")
    
    # Botón para volver a la lista
    if st.button("⬅️ Volver a mis quinielas"):
        del st.session_state.quiniela_seleccionada
        st.rerun()
    
    # Obtener datos de la quiniela
    quiniela_data = db.get_quiniela(nombre_quiniela)
    if not quiniela_data:
        st.error(f"No se encontró la quiniela {nombre_quiniela}")
        return
    
    # Crear objeto quiniela
    quiniela = ProgolQuiniela.from_dict(quiniela_data)
    
    # Mostrar información general
    st.subheader("Información general")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Fecha de creación: {format_timestamp(quiniela.fecha_creacion)}")
        st.write(f"Última actualización: {format_timestamp(quiniela.ultima_actualizacion)}")
    with col2:
        st.write(f"Partidos: {len(quiniela.partidos)}")
        st.write(f"Pronósticos: {len(quiniela.selecciones)} de {len(quiniela.partidos)}")
    
    # Obtener resultados actuales
    resultados_actuales = st.session_state.quiniela_manager.obtener_resultados_actuales()
    
    # Calcular aciertos
    estadisticas = quiniela.calcular_aciertos(resultados_actuales)
    
    # Mostrar estadísticas
    st.subheader("Estadísticas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Partidos con resultado", f"{estadisticas['partidos_con_resultado']} / {estadisticas['total_partidos']}")
    with col2:
        st.metric("Aciertos", f"{estadisticas['aciertos']} / {estadisticas['partidos_con_resultado']}")
    with col3:
        st.metric("Porcentaje de aciertos", f"{estadisticas['porcentaje_aciertos']:.1f}%")
    
    # Mostrar partidos y pronósticos
    st.subheader("Partidos y pronósticos")
    
    # Crear DataFrame para mostrar
    datos_partidos = []
    for partido in quiniela.partidos:
        match_id = partido.get('match_id')
        # Obtener información actualizada del partido
        match_info = db.get_match_by_id(match_id) or {}
        
        # Determinar estado del partido
        estado = "No iniciado"
        if match_info.get('is_live'):
            estado = "En vivo"
        elif match_info.get('is_finished'):
            estado = "Finalizado"
        
        # Determinar si el pronóstico es correcto
        pronostico = quiniela.obtener_pronostico(match_id) or "Sin pronóstico"
        resultado_actual = match_info.get('result', '')
        
        acierto = None
        if pronostico != "Sin pronóstico" and resultado_actual:
            acierto = pronostico == resultado_actual
        
        datos_partidos.append({
            'ID': match_id,
            'Partido': f"{partido.get('home_team', '')} vs {partido.get('away_team', '')}",
            'Liga': partido.get('league', ''),
            'Estado': estado,
            'Marcador': f"{match_info.get('home_score', '-')} - {match_info.get('away_score', '-')}" if match_info else "-",
            'Resultado': resultado_actual,
            'Pronóstico': pronostico,
            'Acierto': "✅" if acierto == True else ("❌" if acierto == False else "")
        })
    
    # Mostrar tabla
    if datos_partidos:
        df = pd.DataFrame(datos_partidos)
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("No hay partidos en esta quiniela.")
    
    # Botón para eliminar
    with st.expander("Opciones avanzadas"):
        if st.button("🗑️ Eliminar esta quiniela", key=f"btn_eliminar_{nombre_quiniela}"):
            if st.session_state.get("confirmar_eliminar") == nombre_quiniela:
                # Eliminar y volver a la lista
                if db.delete_quiniela(nombre_quiniela):
                    st.success(f"Quiniela {nombre_quiniela} eliminada correctamente.")
                    del st.session_state.quiniela_seleccionada
                    st.session_state.pop("confirmar_eliminar", None)
                    st.rerun()
                else:
                    st.error("Error al eliminar la quiniela.")
            else:
                st.session_state.confirmar_eliminar = nombre_quiniela
                st.warning("Haz clic de nuevo para confirmar la eliminación.")

def seccion_crear_quiniela():
    """Interfaz para crear una nueva quiniela."""
    st.header("➕ Crear nueva quiniela")
    
    # Botón para volver a la lista
    if st.button("⬅️ Volver a mis quinielas"):
        st.session_state.pop("creando_quiniela", None)
        st.rerun()
    
    # Formulario para crear quiniela
    with st.form("form_crear_quiniela"):
        nombre = st.text_input("Nombre de la quiniela", placeholder="Ej: Mi Quiniela Semana 15")
        
        # Sección para ingresar partidos manualmente
        st.subheader("Ingresa los partidos para tu quiniela")
        
        # Opciones de añadir partidos
        add_method = st.radio(
            "Método para añadir partidos", 
            ["Ingresar manualmente", "Buscar partidos"], 
            horizontal=True
        )
        
        partidos_seleccionados = []
        
        if add_method == "Ingresar manualmente":
            # Crear campos para agregar partidos
            num_partidos = st.number_input("Número de partidos", min_value=1, max_value=14, value=9)
            
            for i in range(int(num_partidos)):
                st.markdown(f"#### Partido {i+1}")
                col1, col2, col3 = st.columns([3, 1, 3])
                
                with col1:
                    equipo_local = st.text_input(f"Equipo Local #{i+1}", key=f"local_{i}")
                
                with col2:
                    st.markdown("<p style='text-align: center; margin-top: 30px;'>vs</p>", unsafe_allow_html=True)
                
                with col3:
                    equipo_visitante = st.text_input(f"Equipo Visitante #{i+1}", key=f"visitante_{i}")
                
                liga = st.selectbox(f"Liga del Partido #{i+1}", options=list(LIGAS_PROGOL.keys()), key=f"liga_{i}")
                
                # Añadir partido si se han ingresado ambos equipos
                if equipo_local and equipo_visitante:
                    partido = {
                        'match_id': 1000000 + i,  # ID temporal para identificar el partido
                        'home_team': equipo_local,
                        'away_team': equipo_visitante,
                        'league': liga,
                        'scheduled_time': datetime.now().isoformat()
                    }
                    partidos_seleccionados.append(partido)
        else:  # Buscar partidos
            st.markdown("##### Búsqueda de partidos")
            st.markdown("Ingresa los equipos para buscar partidos en SofaScore.")
            
            # Opción para actualizar IDs
            st.info("Si no encuentras un partido, intenta actualizar los IDs de las ligas y temporadas.")
            actualizar_ids = st.checkbox("Actualizar IDs de ligas y temporadas", value=False)
            
            if actualizar_ids:
                with st.spinner("Actualizando IDs de ligas y temporadas..."):
                    updated = st.session_state.data_service.update_league_ids()
                    if updated:
                        st.success("IDs actualizados correctamente")
                    else:
                        st.warning("No se pudieron actualizar algunos IDs. Intenta más tarde.")
            
            # Agregar partidos mediante búsqueda individual
            col1, col2 = st.columns([1, 1])
            with col1:
                equipo_local_busqueda = st.text_input("Equipo Local", key="local_search")
            with col2:
                equipo_visitante_busqueda = st.text_input("Equipo Visitante", key="away_search")
            
            buscar_partido = st.checkbox("Buscar este partido", key="search_match")
            
            if buscar_partido and equipo_local_busqueda and equipo_visitante_busqueda:
                with st.spinner(f"Buscando partido {equipo_local_busqueda} vs {equipo_visitante_busqueda}..."):
                    match = st.session_state.data_service.search_match(equipo_local_busqueda, equipo_visitante_busqueda)
                    
                    if match:
                        match_id = match.get('id')
                        home_team = match.get('homeTeam', {}).get('name', '')
                        away_team = match.get('awayTeam', {}).get('name', '')
                        league = match.get('tournament', {}).get('name', '')
                        
                        st.success(f"¡Partido encontrado! {home_team} vs {away_team} ({league})")
                        agregar_partido = st.checkbox(f"Agregar {home_team} vs {away_team}", value=True)
                        
                        if agregar_partido:
                            partido = {
                                'match_id': match_id,
                                'home_team': home_team,
                                'away_team': away_team,
                                'league': league,
                                'scheduled_time': datetime.fromtimestamp(match.get('startTimestamp', 0)).isoformat()
                            }
                            partidos_seleccionados.append(partido)
                    else:
                        st.error(f"No se encontró ningún partido para {equipo_local_busqueda} vs {equipo_visitante_busqueda}")
            
            # Opción para buscar partidos próximos
            st.markdown("##### O busca entre los próximos partidos")
            buscar_proximos = st.checkbox("Buscar próximos partidos", key="search_upcoming")
            
            if buscar_proximos:
                dias_adelante = st.slider("Días a buscar", min_value=1, max_value=14, value=7)
                liga_filtro = st.multiselect("Filtrar por ligas", options=list(LIGAS_PROGOL.keys()), default=[])
                
                with st.spinner(f"Buscando próximos partidos para los próximos {dias_adelante} días..."):
                    proximos_partidos = st.session_state.data_service.get_upcoming_matches(days_ahead=dias_adelante)
                    
                    if proximos_partidos:
                        # Filtrar por ligas si es necesario
                        if liga_filtro:
                            ligas_a_buscar = [LIGAS_PROGOL[liga] for liga in liga_filtro]
                            proximos_partidos = [p for p in proximos_partidos if p.get('league') in ligas_a_buscar]
                        
                        st.success(f"Se encontraron {len(proximos_partidos)} partidos")
                        
                        # Mostrar partidos para seleccionar
                        for idx, partido in enumerate(proximos_partidos):
                            home = partido.get('home_team', '')
                            away = partido.get('away_team', '')
                            league = partido.get('league', '')
                            
                            try:
                                fecha = datetime.fromisoformat(partido.get('scheduled_time')).strftime("%d/%m/%Y %H:%M")
                            except:
                                fecha = "Fecha desconocida"
                            
                            agregar = st.checkbox(f"{home} vs {away} ({league}) - {fecha}", key=f"add_match_{idx}")
                            
                            if agregar:
                                partidos_seleccionados.append(partido)
                    else:
                        st.warning("No se encontraron próximos partidos")
        
        # Mostrar resumen de partidos seleccionados
        if partidos_seleccionados:
            st.subheader(f"Partidos seleccionados ({len(partidos_seleccionados)})")
            for idx, partido in enumerate(partidos_seleccionados):
                st.markdown(f"- {partido.get('home_team', '')} vs {partido.get('away_team', '')} ({partido.get('league', '')})")
        
        # Botón para crear
        submitted = st.form_submit_button("Crear quiniela")
        
        if submitted:
            if not nombre:
                st.error("Debes proporcionar un nombre para la quiniela.")
                return
            
            # Verificar si ya existe
            quinielas = db.list_quinielas()
            if nombre in [q['nombre'] for q in quinielas]:
                st.error(f"Ya existe una quiniela con el nombre '{nombre}'.")
                return
            
            if not partidos_seleccionados:
                st.error("Debes ingresar al menos un partido.")
                return
            
            # Crear quiniela
            try:
                quiniela = st.session_state.quiniela_manager.crear_quiniela(nombre, partidos_seleccionados)
                st.success(f"Quiniela '{nombre}' creada correctamente con {len(partidos_seleccionados)} partidos.")
                
                # Guardar en la base de datos
                db.save_quiniela(quiniela.to_dict())
                
                # Volver a la lista
                st.session_state.pop("creando_quiniela", None)
                st.session_state.quiniela_seleccionada = nombre
                st.rerun()
            except Exception as e:
                st.error(f"Error al crear la quiniela: {e}")

def seccion_notificaciones():
    """Muestra las notificaciones del sistema."""
    st.sidebar.header("📢 Notificaciones")
    
    if not st.session_state.notifications:
        st.sidebar.info("No hay notificaciones.")
    else:
        for notif in st.session_state.notifications[:10]:  # Mostrar solo las 10 más recientes
            tipo = notif.get('tipo', 'info')
            mensaje = notif.get('mensaje', '')
            timestamp = format_timestamp(notif.get('timestamp', datetime.now()))
            
            if tipo == 'error':
                st.sidebar.error(f"{mensaje} ({timestamp})")
            elif tipo == 'warning':
                st.sidebar.warning(f"{mensaje} ({timestamp})")
            elif tipo == 'success':
                st.sidebar.success(f"{mensaje} ({timestamp})")
            else:
                st.sidebar.info(f"{mensaje} ({timestamp})")
    
    # Mostrar último tiempo de actualización
    if st.session_state.last_update:
        last_update = format_timestamp(st.session_state.last_update)
        st.sidebar.caption(f"Última actualización: {last_update}")

# Manejar eventos del programador
def handle_scheduler_event(event: UpdateEvent):
    """Maneja eventos del programador."""
    if event.event_type == "score_change":
        # Datos del cambio
        change_data = event.data
        
        # Guardar en la base de datos
        db.save_score_change(change_data)
        
        # Crear mensaje para notificación
        home_team = change_data.get('home_team', '')
        away_team = change_data.get('away_team', '')
        home_score = change_data.get('home_score', 0)
        away_score = change_data.get('away_score', 0)
        
        old_result = change_data.get('resultado_anterior', '')
        new_result = change_data.get('resultado_nuevo', '')
        
        old_result_text = MATCH_STATUS.get(old_result, {}).get('text', old_result)
        new_result_text = MATCH_STATUS.get(new_result, {}).get('text', new_result)
        
        mensaje = f"Cambio en {home_team} vs {away_team}: {home_score}-{away_score}. {old_result_text} → {new_result_text}"
        
        # Añadir notificación
        add_notification('success', mensaje, event.timestamp)
    
    elif event.event_type == "periodic_update":
        # Actualizar timestamp de última actualización
        st.session_state.last_update = event.timestamp
    
    elif event.event_type == "update_error":
        # Notificar error
        add_notification('error', f"Error en actualización: {event.data}", event.timestamp)

# Registrar manejador de eventos
st.session_state.scheduler.add_event_listener(handle_scheduler_event)

# Estructura principal de la aplicación
def main():
    """Función principal de la aplicación."""
    # Título y descripción
    st.title("⚽ Quiniela Progol Tracker")
    st.markdown(
        "Seguimiento en tiempo real de resultados para quinielas Progol. "
        "Recibe actualizaciones cuando cambia un resultado en tus quinielas."
    )
    
    # Sidebar
    st.sidebar.title("⚽ Quiniela Progol Tracker")
    seccion_notificaciones()
    
    # Mostrar última actualización y siguiente actualización
    if st.session_state.last_update:
        last_update = st.session_state.last_update
        next_update = last_update + timedelta(seconds=UPDATE_INTERVAL)
        
        # Calcular tiempo restante
        now = datetime.now()
        if next_update > now:
            seconds_remaining = (next_update - now).total_seconds()
            mins = int(seconds_remaining // 60)
            secs = int(seconds_remaining % 60)
            
            with st.sidebar.container():
                st.markdown("### ⏱️ Próxima actualización")
                st.progress(1 - (seconds_remaining / UPDATE_INTERVAL))
                st.caption(f"En {mins}:{secs:02d}")
    
    # Botón para actualizar manualmente
    if st.sidebar.button("🔄 Actualizar ahora"):
        with st.spinner("Actualizando datos..."):
            st.session_state.scheduler.force_update()
            time.sleep(2)  # Pequeña pausa para que se procesen los datos
            st.rerun()
    
    # Navegación principal
    if 'creando_quiniela' in st.session_state:
        seccion_crear_quiniela()
    elif 'quiniela_seleccionada' in st.session_state:
        seccion_detalle_quiniela(st.session_state.quiniela_seleccionada)
    else:
        # Dividir en dos columnas
        col1, col2 = st.columns(2)
        
        with col1:
            seccion_partidos_activos()
        
        with col2:
            seccion_mis_quinielas()

# Ejecutar la aplicación
if __name__ == "__main__":
    main()