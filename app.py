"""
Aplicación principal para Quiniela Progol.
Interfaces de usuario con Streamlit.
"""
import streamlit as st
import pandas as pd
import time
import threading
import os
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Importar módulos de la aplicación
from data_service import SofascoreDataService
from quiniela_manager import QuinielaManager, ProgolQuiniela
from scheduler import QuinielaScheduler, UpdateEvent
import database as db
from csv_utils import parse_progol_csv, generate_sample_csv
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
    # Configurar el scheduler pero no iniciarlo automáticamente
    st.session_state.scheduler.set_data_service(st.session_state.data_service)
    st.session_state.scheduler.set_quiniela_manager(st.session_state.quiniela_manager)

# Inicializar esta variable siempre, no solo la primera vez
st.session_state.scheduler_running = getattr(st.session_state, 'scheduler_running', False)

if 'notifications' not in st.session_state:
    st.session_state.notifications = []

if 'last_update' not in st.session_state:
    st.session_state.last_update = None

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

# Función para iniciar el scheduler manualmente
def start_scheduler():
    """Inicia el servicio de actualización de datos."""
    try:
        # Usar un try-except para capturar cualquier error
        if not st.session_state.scheduler_running:
            st.session_state.scheduler.start()
            st.session_state.scheduler_running = True
            add_notification('success', 'Servicio de actualización iniciado correctamente')
            return True
        else:
            add_notification('info', 'El servicio de actualización ya está en ejecución')
            return False
    except Exception as e:
        st.session_state.scheduler_running = False
        add_notification('error', f'Error al iniciar servicio de actualización: {str(e)}')
        return False

# En la sidebar de la aplicación principal
if st.sidebar.button("▶️ Iniciar servicio de actualización"):
    if start_scheduler():
        st.sidebar.success("Servicio de actualización iniciado correctamente")
    else:
        st.sidebar.error("No se pudo iniciar el servicio de actualización")

# También podemos agregar un botón para detener el scheduler
if st.session_state.scheduler_running and st.sidebar.button("⏹️ Detener servicio de actualización"):
    try:
        st.session_state.scheduler.stop()
        st.session_state.scheduler_running = False
        add_notification('info', 'Servicio de actualización detenido')
        st.sidebar.info("Servicio de actualización detenido")
    except Exception as e:
        st.sidebar.error(f"Error al detener el servicio: {e}")

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
        # Mostrar en formato de cuadrícula
        cols = st.columns(3)  # Mostrar 3 quinielas por fila
        
        for i, quiniela_info in enumerate(quinielas):
            col_idx = i % 3
            with cols[col_idx]:
                nombre = quiniela_info['nombre']
                fecha = format_timestamp(quiniela_info['ultima_actualizacion'])
                
                # Crear un contenedor con borde para cada quiniela
                with st.container():
                    st.markdown(f"""
                    <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px;">
                        <h3>{nombre}</h3>
                        <p>Última actualización: {fecha}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
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
        st.write(f"Partidos regulares: {len(quiniela.partidos_regulares)}")
        st.write(f"Partidos de revancha: {len(quiniela.partidos_revancha)}")
    
    # Obtener resultados actuales
    resultados_actuales = st.session_state.quiniela_manager.obtener_resultados_actuales()
    resultados_revancha = st.session_state.quiniela_manager.obtener_resultados_actuales(solo_revancha=True)
    
    # Calcular aciertos
    estadisticas = quiniela.calcular_aciertos(resultados_actuales, resultados_revancha)
    
    # Mostrar estadísticas
    st.subheader("Estadísticas")
    
    # Estadísticas regulares
    st.markdown("##### Partidos Regulares")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Partidos con resultado", f"{estadisticas['regulares_con_resultado']} / {estadisticas['total_regulares']}")
    with col2:
        st.metric("Aciertos", f"{estadisticas['aciertos_regulares']} / {estadisticas['regulares_con_resultado']}")
    with col3:
        st.metric("Porcentaje de aciertos", f"{estadisticas['porcentaje_aciertos_regulares']:.1f}%")
    
    # Estadísticas revancha
    if quiniela.partidos_revancha:
        st.markdown("##### Partidos de Revancha")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Partidos con resultado", f"{estadisticas['revancha_con_resultado']} / {estadisticas['total_revancha']}")
        with col2:
            st.metric("Aciertos", f"{estadisticas['aciertos_revancha']} / {estadisticas['revancha_con_resultado']}")
        with col3:
            st.metric("Porcentaje de aciertos", f"{estadisticas['porcentaje_aciertos_revancha']:.1f}%")
    
    # Mostrar partidos y pronósticos
    st.subheader("Partidos regulares y pronósticos")
    
    # Tabla para hacer pronósticos
    st.markdown("##### Partidos regulares (14)")
    
    # Crear la tabla con selecciones
    cols = st.columns([1, 3, 1, 1, 1, 1, 1])
    with cols[0]:
        st.markdown("**Fecha**")
    with cols[1]:
        st.markdown("**Partido**")
    with cols[2]:
        st.markdown("**Estado**")
    with cols[3]:
        st.markdown("**Marcador**")
    with cols[4]:
        st.markdown("**L**")
    with cols[5]:
        st.markdown("**E**")
    with cols[6]:
        st.markdown("**V**")
    
    # Datos para actualizar
    selecciones_actualizadas = {}
    
    # Mostrar partidos regulares
    for partido in quiniela.partidos_regulares:
        match_id = partido.get('match_id')
        match_info = db.get_match_by_id(match_id) or {}
        
        # Determinar estado del partido
        estado = "No iniciado"
        if match_info.get('is_live'):
            estado = "En vivo"
        elif match_info.get('is_finished'):
            estado = "Finalizado"
        
        # Determinar el pronóstico actual
        pronostico_actual = quiniela.obtener_pronostico(match_id) or ""
        
        # Preparar la fecha para mostrar
        fecha_str = "Programado"
        try:
            fecha_obj = datetime.fromisoformat(partido.get('scheduled_time', ''))
            fecha_str = fecha_obj.strftime("%d/%m %H:%M")
        except:
            pass
        
        # Mostrar fila de partido
        cols = st.columns([1, 3, 1, 1, 1, 1, 1])
        with cols[0]:
            st.text(fecha_str)
        with cols[1]:
            st.text(f"{partido.get('home_team', '')} vs {partido.get('away_team', '')}")
        with cols[2]:
            st.text(estado)
        with cols[3]:
            marcador = f"{match_info.get('home_score', '-')} - {match_info.get('away_score', '-')}" if match_info else "-"
            st.text(marcador)
            
        # Radio buttons para selección
        seleccion_key = f"sel_{match_id}"
        col4, col5, col6 = cols[4], cols[5], cols[6]
        
        # Usar columnas individuales en lugar de radio button para controlar mejor la apariencia
        with col4:
            local = st.checkbox("", value=pronostico_actual == "L", key=f"L_{match_id}", disabled=estado=="Finalizado")
        with col5:
            empate = st.checkbox("", value=pronostico_actual == "E", key=f"E_{match_id}", disabled=estado=="Finalizado")
        with col6:
            visitante = st.checkbox("", value=pronostico_actual == "V", key=f"V_{match_id}", disabled=estado=="Finalizado")
        
        # Lógica para asegurar que solo una opción esté seleccionada
        if local and not (pronostico_actual == "L"):
            selecciones_actualizadas[match_id] = "L"
            # Desactivar las otras opciones
            st.session_state[f"E_{match_id}"] = False
            st.session_state[f"V_{match_id}"] = False
        elif empate and not (pronostico_actual == "E"):
            selecciones_actualizadas[match_id] = "E"
            st.session_state[f"L_{match_id}"] = False
            st.session_state[f"V_{match_id}"] = False
        elif visitante and not (pronostico_actual == "V"):
            selecciones_actualizadas[match_id] = "V"
            st.session_state[f"L_{match_id}"] = False
            st.session_state[f"E_{match_id}"] = False
        elif not (local or empate or visitante) and pronostico_actual:
            # Si se desactivaron todas, limpiar el pronóstico
            selecciones_actualizadas[match_id] = None
    
    # Sección de partidos de revancha, si existen
    if quiniela.partidos_revancha:
        st.subheader("Partidos de revancha")
        
        # Crear la tabla para partidos de revancha
        cols = st.columns([1, 3, 1, 1, 1, 1, 1])
        with cols[0]:
            st.markdown("**Fecha**")
        with cols[1]:
            st.markdown("**Partido**")
        with cols[2]:
            st.markdown("**Estado**")
        with cols[3]:
            st.markdown("**Marcador**")
        with cols[4]:
            st.markdown("**L**")
        with cols[5]:
            st.markdown("**E**")
        with cols[6]:
            st.markdown("**V**")
        
        # Diccionario para almacenar selecciones de revancha
        selecciones_revancha_actualizadas = {}
        
        # Mostrar partidos de revancha
        for partido in quiniela.partidos_revancha:
            match_id = partido.get('match_id')
            match_info = db.get_match_by_id(match_id) or {}
            
            # Determinar estado del partido
            estado = "No iniciado"
            if match_info.get('is_live'):
                estado = "En vivo"
            elif match_info.get('is_finished'):
                estado = "Finalizado"
            
            # Determinar el pronóstico actual
            pronostico_actual = quiniela.obtener_pronostico(match_id, es_revancha=True) or ""
            
            # Preparar la fecha para mostrar
            fecha_str = "Programado"
            try:
                fecha_obj = datetime.fromisoformat(partido.get('scheduled_time', ''))
                fecha_str = fecha_obj.strftime("%d/%m %H:%M")
            except:
                pass
            
            # Mostrar fila de partido
            cols = st.columns([1, 3, 1, 1, 1, 1, 1])
            with cols[0]:
                st.text(fecha_str)
            with cols[1]:
                st.text(f"{partido.get('home_team', '')} vs {partido.get('away_team', '')}")
            with cols[2]:
                st.text(estado)
            with cols[3]:
                marcador = f"{match_info.get('home_score', '-')} - {match_info.get('away_score', '-')}" if match_info else "-"
                st.text(marcador)
                
            # Checkboxes para selección (revancha)
            col4, col5, col6 = cols[4], cols[5], cols[6]
            
            with col4:
                local = st.checkbox("", value=pronostico_actual == "L", key=f"LR_{match_id}", disabled=estado=="Finalizado")
            with col5:
                empate = st.checkbox("", value=pronostico_actual == "E", key=f"ER_{match_id}", disabled=estado=="Finalizado")
            with col6:
                visitante = st.checkbox("", value=pronostico_actual == "V", key=f"VR_{match_id}", disabled=estado=="Finalizado")
            
            # Lógica para asegurar que solo una opción esté seleccionada
            if local and not (pronostico_actual == "L"):
                selecciones_revancha_actualizadas[match_id] = "L"
                # Desactivar las otras opciones
                st.session_state[f"ER_{match_id}"] = False
                st.session_state[f"VR_{match_id}"] = False
            elif empate and not (pronostico_actual == "E"):
                selecciones_revancha_actualizadas[match_id] = "E"
                st.session_state[f"LR_{match_id}"] = False
                st.session_state[f"VR_{match_id}"] = False
            elif visitante and not (pronostico_actual == "V"):
                selecciones_revancha_actualizadas[match_id] = "V"
                st.session_state[f"LR_{match_id}"] = False
                st.session_state[f"ER_{match_id}"] = False
            elif not (local or empate or visitante) and pronostico_actual:
                # Si se desactivaron todas, limpiar el pronóstico
                selecciones_revancha_actualizadas[match_id] = None
    
    # Botón para guardar pronósticos
    cambios_realizados = False
    
    # Verificar si hay cambios en los pronósticos regulares
    if selecciones_actualizadas:
        for match_id, resultado in selecciones_actualizadas.items():
            try:
                if resultado is None:
                    # Implementar la funcionalidad para borrar un pronóstico si es necesario
                    pass
                else:
                    quiniela.establecer_pronostico(match_id, resultado)
                    cambios_realizados = True
            except Exception as e:
                st.error(f"Error al establecer pronóstico: {e}")
    
    # Verificar si hay cambios en los pronósticos de revancha
    if quiniela.partidos_revancha and selecciones_revancha_actualizadas:
        for match_id, resultado in selecciones_revancha_actualizadas.items():
            try:
                if resultado is None:
                    # Implementar la funcionalidad para borrar un pronóstico si es necesario
                    pass
                else:
                    quiniela.establecer_pronostico(match_id, resultado, es_revancha=True)
                    cambios_realizados = True
            except Exception as e:
                st.error(f"Error al establecer pronóstico de revancha: {e}")
    
    # Si hubo cambios, guardar la quiniela actualizada
    if cambios_realizados:
        try:
            db.save_quiniela(quiniela.to_dict())
            st.success("Pronósticos guardados correctamente")
        except Exception as e:
            st.error(f"Error al guardar quiniela: {e}")
    
    # Botón para eliminar la quiniela
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
    
    # Dos métodos para crear quiniela: manual o mediante archivo CSV
    metodo = st.radio(
        "Método para crear quiniela", 
        ["Cargar desde archivo CSV", "Ingresar manualmente"],
        horizontal=True
    )
    
    if metodo == "Cargar desde archivo CSV":
        st.subheader("Cargar partidos desde archivo CSV")
        
        # Mostrar instrucciones y formato
        with st.expander("Instrucciones y formato del archivo CSV", expanded=True):
            st.markdown("""
            ### Formato del archivo CSV
            El archivo CSV debe tener los siguientes campos:
            
            - **fecha**: Fecha del partido en formato YYYY-MM-DD
            - **hora**: Hora del partido en formato HH:MM
            - **local**: Nombre del equipo local
            - **visitante**: Nombre del equipo visitante
            - **liga**: Liga del partido (debe ser una de las ligas soportadas)
            - **revancha**: 1 para partidos de revancha, 0 para partidos regulares
            
            Los primeros 14 partidos regulares (revancha=0) serán considerados para la quiniela regular.
            Los siguientes partidos con revancha=1 (máximo 7) se considerarán para la quiniela de revancha.
            """)
            
            # Botón para descargar plantilla
            sample_csv = generate_sample_csv()
            st.download_button(
                "📄 Descargar plantilla CSV",
                data=sample_csv,
                file_name="partidos_progol_plantilla.csv",
                mime="text/csv"
            )
        
        # Opción para cargar archivo CSV
        uploaded_file = st.file_uploader("Selecciona un archivo CSV", type=["csv"])
        
        # Procesar archivo
        partidos_regulares = []
        partidos_revancha = []
        
        if uploaded_file:
            try:
                # Leer el contenido del archivo
                csv_content = uploaded_file.read().decode('utf-8')
                
                # Parsear el CSV
                partidos_regulares, partidos_revancha = parse_progol_csv(csv_content)
                
                st.success(f"Archivo cargado correctamente. Se encontraron {len(partidos_regulares)} partidos regulares y {len(partidos_revancha)} partidos de revancha.")
                
                # Mostrar resumen
                st.subheader("Resumen de partidos")
                
                # Mostrar partidos regulares
                st.markdown("##### Partidos regulares")
                for i, partido in enumerate(partidos_regulares):
                    st.markdown(f"{i+1}. {partido['home_team']} vs {partido['away_team']} ({partido['league']})")
                
                # Mostrar partidos de revancha
                if partidos_revancha:
                    st.markdown("##### Partidos de revancha")
                    for i, partido in enumerate(partidos_revancha):
                        st.markdown(f"{i+1}. {partido['home_team']} vs {partido['away_team']} ({partido['league']})")
                
            except Exception as e:
                st.error(f"Error al procesar el archivo CSV: {str(e)}")
                partidos_regulares = []
                partidos_revancha = []
        
        # Formulario para completar la creación
        with st.form("form_crear_quiniela_csv"):
            nombre = st.text_input("Nombre de la quiniela", placeholder="Ej: Progol 3480")
            
            # Botón para crear
            submitted = st.form_submit_button("Crear quiniela")
            
            if submitted:
                if not nombre:
                    st.error("Debes proporcionar un nombre para la quiniela.")
                elif not partidos_regulares:
                    st.error("Debes cargar un archivo CSV válido con partidos.")
                else:
                    # Verificar si ya existe
                    quinielas = db.list_quinielas()
                    if nombre in [q['nombre'] for q in quinielas]:
                        st.error(f"Ya existe una quiniela con el nombre '{nombre}'.")
                    else:
                        # Crear quiniela
                        try:
                            quiniela = st.session_state.quiniela_manager.crear_quiniela(
                                nombre, 
                                partidos_regulares, 
                                partidos_revancha
                            )
                            
                            # Guardar en la base de datos
                            db.save_quiniela(quiniela.to_dict())
                            
                            st.success(f"Quiniela '{nombre}' creada correctamente con {len(partidos_regulares)} partidos regulares y {len(partidos_revancha)} partidos de revancha.")
                            
                            # Volver a la lista y mostrar la quiniela creada
                            st.session_state.pop("creando_quiniela", None)
                            st.session_state.quiniela_seleccionada = nombre
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear la quiniela: {e}")
    
    else:  # Método manual
        st.subheader("Ingresar partidos manualmente")
        
        # Formulario para crear quiniela
        with st.form("form_crear_quiniela_manual"):
            nombre = st.text_input("Nombre de la quiniela", placeholder="Ej: Progol 3480")
            
            # Sección para partidos regulares
            st.markdown("### Partidos regulares (14)")
            
            partidos_regulares = []
            for i in range(14):  # Exactamente 14 partidos regulares
                st.markdown(f"#### Partido {i+1}")
                col1,col1, col2, col3 = st.columns([3, 1, 3])
                
                with col1:
                    equipo_local = st.text_input(f"Equipo Local #{i+1}", key=f"local_{i}")
                
                with col2:
                    st.markdown("<p style='text-align: center; margin-top: 30px;'>vs</p>", unsafe_allow_html=True)
                
                with col3:
                    equipo_visitante = st.text_input(f"Equipo Visitante #{i+1}", key=f"visitante_{i}")
                
                col4, col5 = st.columns(2)
                with col4:
                    liga = st.selectbox(f"Liga #{i+1}", options=list(LIGAS_PROGOL.keys()), key=f"liga_{i}")
                
                with col5:
                    fecha_hora = st.text_input(f"Fecha y hora (YYYY-MM-DD HH:MM)", key=f"fecha_{i}", placeholder="2025-04-20 19:00")
                
                # Añadir partido si se han ingresado datos
                if equipo_local and equipo_visitante:
                    try:
                        fecha_obj = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M") if fecha_hora else datetime.now()
                        fecha_iso = fecha_obj.isoformat()
                    except ValueError:
                        fecha_iso = datetime.now().isoformat()
                    
                    partido = {
                        'match_id': 1000000 + i,  # ID temporal para identificar el partido
                        'home_team': equipo_local,
                        'away_team': equipo_visitante,
                        'league': liga,
                        'scheduled_time': fecha_iso,
                        'is_revancha': False
                    }
                    partidos_regulares.append(partido)
            
            # Sección para partidos de revancha (opcional)
            st.markdown("### Partidos de revancha (opcional, máximo 7)")
            incluir_revancha = st.checkbox("Incluir partidos de revancha", value=False)
            
            partidos_revancha = []
            if incluir_revancha:
                num_revancha = st.slider("Número de partidos de revancha", min_value=1, max_value=7, value=7)
                
                for i in range(num_revancha):
                    st.markdown(f"#### Partido de revancha {i+1}")
                    col1, col2, col3 = st.columns([3, 1, 3])
                    
                    with col1:
                        equipo_local = st.text_input(f"Equipo Local Revancha #{i+1}", key=f"local_r_{i}")
                    
                    with col2:
                        st.markdown("<p style='text-align: center; margin-top: 30px;'>vs</p>", unsafe_allow_html=True)
                    
                    with col3:
                        equipo_visitante = st.text_input(f"Equipo Visitante Revancha #{i+1}", key=f"visitante_r_{i}")
                    
                    col4, col5 = st.columns(2)
                    with col4:
                        liga = st.selectbox(f"Liga Revancha #{i+1}", options=list(LIGAS_PROGOL.keys()), key=f"liga_r_{i}")
                    
                    with col5:
                        fecha_hora = st.text_input(f"Fecha y hora (YYYY-MM-DD HH:MM)", key=f"fecha_r_{i}", placeholder="2025-04-20 19:00")
                    
                    # Añadir partido si se han ingresado datos
                    if equipo_local and equipo_visitante:
                        try:
                            fecha_obj = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M") if fecha_hora else datetime.now()
                            fecha_iso = fecha_obj.isoformat()
                        except ValueError:
                            fecha_iso = datetime.now().isoformat()
                        
                        partido = {
                            'match_id': 2000000 + i,  # ID temporal para identificar el partido
                            'home_team': equipo_local,
                            'away_team': equipo_visitante,
                            'league': liga,
                            'scheduled_time': fecha_iso,
                            'is_revancha': True
                        }
                        partidos_revancha.append(partido)
            
            # Botón para crear
            submitted = st.form_submit_button("Crear quiniela")
            
            if submitted:
                if not nombre:
                    st.error("Debes proporcionar un nombre para la quiniela.")
                    return
                
                # Verificar cantidad de partidos
                if len(partidos_regulares) != 14:
                    st.error(f"Se requieren exactamente 14 partidos regulares. Has ingresado {len(partidos_regulares)}.")
                    return
                
                # Verificar si ya existe
                quinielas = db.list_quinielas()
                if nombre in [q['nombre'] for q in quinielas]:
                    st.error(f"Ya existe una quiniela con el nombre '{nombre}'.")
                    return
                
                # Crear quiniela
                try:
                    quiniela = st.session_state.quiniela_manager.crear_quiniela(
                        nombre, 
                        partidos_regulares, 
                        partidos_revancha if incluir_revancha else []
                    )
                    
                    # Guardar en la base de datos
                    db.save_quiniela(quiniela.to_dict())
                    
                    st.success(f"Quiniela '{nombre}' creada correctamente con {len(partidos_regulares)} partidos regulares y {len(partidos_revancha) if incluir_revancha else 0} partidos de revancha.")
                    
                    # Volver a la lista y mostrar la quiniela creada
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
        es_revancha = change_data.get('es_revancha', False)
        
        old_result_text = MATCH_STATUS.get(old_result, {}).get('text', old_result)
        new_result_text = MATCH_STATUS.get(new_result, {}).get('text', new_result)
        
        revancha_text = " (Revancha)" if es_revancha else ""
        mensaje = f"Cambio en {home_team} vs {away_team}{revancha_text}: {home_score}-{away_score}. {old_result_text} → {new_result_text}"
        
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

# Botón para actualizar manualmente
if st.sidebar.button("🔄 Actualizar ahora"):
    with st.spinner("Actualizando datos..."):
        st.session_state.scheduler.force_update()
        time.sleep(2)  # Pequeña pausa para que se procesen los datos
        st.rerun()

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