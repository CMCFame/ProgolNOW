##############################
# HEADER: IMPORTS Y CONFIG
##############################
import streamlit as st
import requests
import time
from io import BytesIO
from PIL import Image
import pytesseract
import pytz
import datetime

# Si necesitases señalar la ruta de tesseract (p.e. en Windows local), podrías usar:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# En Streamlit Cloud, con 'tesseract-ocr' instalado, no hace falta.

##############################
# HEADER: MÓDULO DE CONFIGURACIÓN (API, ZONA HORARIA)
##############################
def cargar_credenciales_api():
    """
    Carga credenciales de la API desde la sección [rapidapi] en 'Secrets' de Streamlit.
    En Streamlit Cloud: 
    - Menu -> Settings -> Secrets
    - Define la estructura:
        [rapidapi]
        key = "TU_API_KEY"
        host = "free-api-live-football-data.p.rapidapi.com"
    """
    api_key = st.secrets["rapidapi"]["key"]
    api_host = st.secrets["rapidapi"]["host"]
    
    return {
        "key": api_key,
        "host": api_host
    }

def configurar_zona_horaria():
    """
    Retorna la zona horaria según la selección del usuario. 
    """
    lista_zonas = ["UTC", "America/Mexico_City", "America/Bogota", "Europe/Madrid"]
    seleccion = st.sidebar.selectbox("Selecciona tu Zona Horaria", lista_zonas, index=0)
    return pytz.timezone(seleccion)

##############################
# HEADER: MÓDULO DE OCR Y PARSEO
##############################
def procesar_texto_quiniela(texto_detectado):
    """
    Ejemplo mínimo de parseo:
    Busca líneas que contengan la palabra 'vs' (indiferente a mayúsculas).
    Ajusta según la manera en que Tesseract reconozca el texto de tu quiniela.
    """
    partidos_extraidos = []
    lineas = texto_detectado.split("\n")
    
    for linea in lineas:
        linea_limpia = linea.strip()
        if not linea_limpia:
            continue
        
        # Ejemplo: detectamos la palabra "vs" (o "VS")
        if " vs " in linea_limpia.lower():
            partidos_extraidos.append(linea_limpia)
    
    return partidos_extraidos

def cargar_quiniela_desde_imagen_ocr():
    """
    Único método de carga: sube imagen y extrae texto con OCR.
    """
    st.header("Subir Imagen de Quiniela (OCR)")
    imagen_cargada = st.file_uploader("Arrastra o selecciona tu imagen (png/jpg/jpeg)", type=["png", "jpg", "jpeg"])
    
    if imagen_cargada is not None:
        # Mostramos la imagen
        img = Image.open(BytesIO(imagen_cargada.read()))
        st.image(img, caption="Quiniela cargada", use_column_width=True)
        
        st.write("Procesando la imagen con OCR, por favor espera...")
        with st.spinner("Extrayendo texto..."):
            # Ajusta lang según el idioma que necesites; si tu imagen está en español:
            # texto_detectado = pytesseract.image_to_string(img, lang='spa')
            texto_detectado = pytesseract.image_to_string(img, lang='eng')
            
            # Mostramos el resultado crudo del OCR
            st.write("**Texto detectado (OCR):**")
            st.write(texto_detectado)
            
            # Parseamos el texto (ejemplo muy básico)
            partidos_ocr = procesar_texto_quiniela(texto_detectado)
            if partidos_ocr:
                st.success(f"Se detectaron {len(partidos_ocr)} partidos con la palabra 'vs'.")
                for p in partidos_ocr:
                    st.write("-", p)
                
                # Retornamos la lista
                return partidos_ocr
            else:
                st.warning("No se detectaron partidos con la lógica actual (búsqueda de 'vs').")
                return []
    else:
        st.info("Por favor, sube una imagen en la parte superior.")
    return []

##############################
# HEADER: MÓDULO DE MOSTRAR PARTIDOS
##############################
def mostrar_partidos_quiniela(partidos, timezone):
    """
    Muestra en pantalla la lista de partidos y una hora simulada por cada uno.
    """
    st.header("Partidos detectados")
    if not partidos:
        st.info("Aún no hay partidos cargados.")
        return
    
    hora_base = datetime.datetime.utcnow()
    st.write("**Lista de Partidos:**")
    
    for i, partido in enumerate(partidos, 1):
        # offset mínimo para mostrar ejemplo de fecha/hora
        hora_local = hora_base.replace(hour=(hora_base.hour + i) % 24)
        hora_convertida = hora_local.astimezone(timezone)
        st.write(f"{i}. {partido} | {hora_convertida.strftime('%d-%m-%Y %H:%M %Z')}")

##############################
# HEADER: MÓDULO DE RESULTADOS EN TIEMPO REAL
##############################
def obtener_datos_en_tiempo_real():
    """
    Ejemplo: Llamada a la API de RapidAPI (búsqueda de jugadores).
    Ajusta con tu propio endpoint de partidos en tiempo real.
    """
    creds = cargar_credenciales_api()
    url = "https://free-api-live-football-data.p.rapidapi.com/football-players-search"
    querystring = {"search": "m"}
    
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
    st.header("Resultados en tiempo real (Ejemplo RapidAPI)")
    st.write("Pulsa el botón para consultar datos (ejemplo de jugadores con 'm'):")
    
    if st.button("Actualizar resultados"):
        data = obtener_datos_en_tiempo_real()
        if data:
            st.write("**Respuesta de la API:**")
            st.json(data)
        else:
            st.warning("No se obtuvieron datos de la API.")
    else:
        st.info("Presiona el botón para obtener datos en tiempo real.")

##############################
# HEADER: MAIN DE LA APLICACIÓN
##############################
def main():
    st.title("Quinielas con OCR (100% en Streamlit Cloud)")
    st.markdown("""
        **Uso**:  
        1. Ve a "Cargar Quiniela (OCR)".  
        2. Sube la imagen de tu quiniela.  
        3. Observa el texto detectado y los partidos extraídos.  
        4. Luego, opcionalmente, revisa "Ver Partidos" o "Resultados en Vivo".
    """)

    # Configuramos la zona horaria
    timezone = configurar_zona_horaria()
    
    # Mantenemos la lista de partidos en el estado de sesión
    if "partidos_quiniela" not in st.session_state:
        st.session_state.partidos_quiniela = []
    
    # Menú de navegación
    menu = st.sidebar.radio("Menú", ["Inicio", "Cargar Quiniela (OCR)", "Ver Partidos", "Resultados en Vivo"])
    
    if menu == "Inicio":
        st.write("Selecciona una opción en el menú para comenzar.")
    
    elif menu == "Cargar Quiniela (OCR)":
        # Único método de carga
        partidos_ocr = cargar_quiniela_desde_imagen_ocr()
        if partidos_ocr:
            st.session_state.partidos_quiniela = partidos_ocr
    
    elif menu == "Ver Partidos":
        mostrar_partidos_quiniela(st.session_state.partidos_quiniela, timezone)
    
    elif menu == "Resultados en Vivo":
        mostrar_resultados_tiempo_real()

##############################
# HEADER: EJECUCIÓN
##############################
if __name__ == "__main__":
    main()
