##############################
# HEADER: IMPORTS Y CONFIG
##############################
import streamlit as st
import requests
import time
from io import BytesIO
from PIL import Image
import pytz
import datetime

# Ejemplo de cómo leer la key desde streamlit secrets.
# Debes crear un archivo 'secrets.toml' (sin comillas) con el siguiente contenido:
#
# [rapidapi]
# key = "TU_API_KEY_DE_RAPIDAPI"
# host = "free-api-live-football-data.p.rapidapi.com"
#
# O bien, guardar estos valores desde el "Secrets" manager de Streamlit Cloud.

##############################
# HEADER: MÓDULO DE CONFIGURACIÓN
##############################
def cargar_credenciales_api():
    """
    Carga las credenciales de la API desde los secretos de Streamlit.
    Retorna un dict con la clave y el host.
    """
    api_key = st.secrets["rapidapi"]["key"]
    api_host = st.secrets["rapidapi"]["host"]
    
    return {
        "key": api_key,
        "host": api_host
    }

def configurar_zona_horaria():
    """
    Retorna un objeto de zona horaria (pytz) de acuerdo a la selección del usuario en la app.
    Por defecto, se asume la zona horaria local del sistema o la elegida por el usuario.
    """
    # Puedes cambiar la lista de zonas horarias según tu preferencia.
    lista_zonas = ["UTC", "America/Mexico_City", "America/Bogota", "Europe/Madrid"]
    seleccion = st.sidebar.selectbox("Selecciona tu Zona Horaria", lista_zonas, index=0)
    return pytz.timezone(seleccion)

##############################
# HEADER: MÓDULO DE CARGA DE QUINIELA
##############################
def cargar_quiniela_desde_imagen():
    """
    Permite subir una imagen con la quiniela y procesarla (versión simulada).
    Idealmente, aquí podrías hacer uso de OCR para extraer los datos de los partidos.
    """
    st.subheader("Carga tu quiniela desde una imagen")
    imagen_cargada = st.file_uploader("Subir imagen de la quiniela", type=["png", "jpg", "jpeg"])
    
    if imagen_cargada is not None:
        # Mostramos la imagen para confirmación
        img = Image.open(BytesIO(imagen_cargada.read()))
        st.image(img, caption="Quiniela cargada", use_column_width=True)
        
        # Procesamiento OCR (simulado)
        st.write("Procesando la imagen...")
        time.sleep(1)
        st.success("Imagen procesada (ejemplo). Aquí se extraerían los partidos reconocidos.")
        return ["Partido 1: Equipo A vs Equipo B", "Partido 2: Equipo C vs Equipo D"]
    return []

def cargar_quiniela_manual():
    """
    Permite al usuario introducir manualmente la lista de partidos de su quiniela.
    Esta función regresa una lista de strings con los partidos ingresados.
    """
    st.subheader("Carga manual de quiniela")
    
    num_partidos = st.number_input("¿Cuántos partidos quieres ingresar?", min_value=1, max_value=20, value=3)
    partidos = []
    for i in range(int(num_partidos)):
        partido = st.text_input(f"Ingrese descripción del partido #{i+1}", f"Ej: EquipoX vs EquipoY")
        if partido:
            partidos.append(partido)
    
    if st.button("Guardar quiniela manual"):
        st.success("Quiniela guardada manualmente.")
        return partidos
    return []

def cargar_quiniela_desde_web():
    """
    Carga la quiniela desde una URL externa (simulación).
    En un caso real, llamarías a la web de Progol o sitios similares para extraer los datos.
    """
    st.subheader("Cargar quiniela desde web")
    url_quiniela = st.text_input("Ingresa la URL de la quiniela", "https://alegrialoteria.com/Progol")
    
    if st.button("Cargar datos"):
        st.write(f"Conectando a {url_quiniela}...")
        # Aquí iría la lógica real para extraer los datos de la quiniela.
        time.sleep(1)
        st.success("Quiniela cargada desde la web (simulada).")
        # Simulamos una lista de partidos
        return ["Partido WEB 1: Equipo A vs Equipo B", "Partido WEB 2: Equipo C vs Equipo D"]
    return []

##############################
# HEADER: MÓDULO DE MOSTRAR PARTIDOS
##############################
def mostrar_partidos_quiniela(partidos, timezone):
    """
    Muestra en pantalla la lista de partidos y sus horarios ajustados a la zona horaria.
    Esta función recibe la zona horaria para convertir la hora de cada partido (simulada).
    """
    st.subheader("Lista de partidos de la quiniela")
    
    if not partidos:
        st.info("Aún no hay partidos cargados.")
        return
    
    # Ejemplo de hora simulada
    hora_base = datetime.datetime.utcnow()
    
    st.write("**Partidos Cargados:**")
    for i, partido in enumerate(partidos, 1):
        # Simulamos fecha/hora
        hora_local = hora_base.replace(hour=hora_base.hour + i)  # Simple offset
        hora_convertida = hora_local.astimezone(timezone)
        st.write(f"**{partido}** | {hora_convertida.strftime('%d-%m-%Y %H:%M %Z')}")

##############################
# HEADER: MÓDULO DE RESULTADOS EN TIEMPO REAL
##############################
def obtener_datos_en_tiempo_real():
    """
    Ejemplo de llamada a la API de RapidAPI para obtener datos en tiempo real.
    Se usa la búsqueda de jugadores como ejemplo, pero podrías consultar endpoints de partidos.
    """
    creds = cargar_credenciales_api()
    url = "https://free-api-live-football-data.p.rapidapi.com/football-players-search"
    querystring = {"search":"m"}  # Ejemplo: buscar jugadores que contengan la letra 'm'
    
    headers = {
        "x-rapidapi-key": creds["key"],
        "x-rapidapi-host": creds["host"]
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

def mostrar_resultados_tiempo_real():
    st.subheader("Resultados en tiempo real (Ejemplo con RapidAPI)")
    
    if st.button("Actualizar resultados"):
        data = obtener_datos_en_tiempo_real()
        if data:
            st.write("Datos recibidos de la API:")
            st.json(data)
        else:
            st.warning("No se pudieron obtener datos de la API.")
    else:
        st.info("Haz clic en 'Actualizar resultados' para obtener datos en tiempo real de la API.")

##############################
# HEADER: MAIN DE LA APLICACIÓN
##############################
def main():
    st.title("Aplicación de Quinielas de Fútbol")
    st.markdown("""
        Esta aplicación permite a los usuarios dar seguimiento a sus quinielas deportivas,
        enfocada principalmente en quinielas de fútbol (ej. Progol). 
        Puedes cargar tu quiniela por diferentes medios y ver resultados en tiempo real.
    """)

    # Configuramos la zona horaria elegida por el usuario
    timezone = configurar_zona_horaria()
    
    # Sidebar con opciones de navegación
    menu = st.sidebar.radio("Navega por la aplicación", ["Inicio", "Cargar Quiniela", "Ver Partidos", "Resultados en Vivo"])
    
    # Estado en sesión para almacenar los partidos cargados
    if "partidos_quiniela" not in st.session_state:
        st.session_state.partidos_quiniela = []
    
    if menu == "Inicio":
        st.write("Bienvenido. Selecciona una opción en el menú lateral para comenzar.")
    
    elif menu == "Cargar Quiniela":
        # Carga desde imagen
        partidos_imagen = cargar_quiniela_desde_imagen()
        if partidos_imagen:
            st.session_state.partidos_quiniela.extend(partidos_imagen)
        
        # Separador visual
        st.write("---")
        
        # Carga manual
        partidos_manuales = cargar_quiniela_manual()
        if partidos_manuales:
            st.session_state.partidos_quiniela.extend(partidos_manuales)
        
        # Separador visual
        st.write("---")
        
        # Carga desde Web
        partidos_web = cargar_quiniela_desde_web()
        if partidos_web:
            st.session_state.partidos_quiniela.extend(partidos_web)
    
    elif menu == "Ver Partidos":
        mostrar_partidos_quiniela(st.session_state.partidos_quiniela, timezone)
    
    elif menu == "Resultados en Vivo":
        mostrar_resultados_tiempo_real()

##############################
# HEADER: EJECUCIÓN
##############################
if __name__ == "__main__":
    main()
