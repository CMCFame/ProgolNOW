#!/bin/bash

echo "Configurando entorno para la aplicación de Quiniela Progol..."

# Verificar que estamos en un entorno Unix
if [ "$(uname)" == "Linux" ]; then
    echo "Ejecutando en entorno Linux"
elif [ "$(uname)" == "Darwin" ]; then
    echo "Ejecutando en macOS"
    echo "ADVERTENCIA: Este script está optimizado para entornos Linux/Streamlit Cloud"
else
    echo "Entorno no soportado. Este script está diseñado para Linux/macOS."
    exit 1
fi

# Crear directorio para archivos de configuración si no existe
mkdir -p .streamlit

# Verificar si ya existe el archivo de secretos
if [ ! -f .streamlit/secrets.toml ]; then
    echo "Creando archivo de secretos por defecto..."
    cat > .streamlit/secrets.toml << 'EOF'
[general]
environment = "production"

# Credenciales para RapidAPI
RAPIDAPI_KEY = "d4b4999861mshc077d4879aba6d4p19f6e7jsn1bc73c757992"
RAPIDAPI_HOST = "free-api-live-football-data.p.rapidapi.com"

# Configuración adicional
[config]
default_timezone = "America/Mexico_City"
auto_refresh_interval = 300  # en segundos
EOF
    echo "Archivo de secretos creado en .streamlit/secrets.toml"
else
    echo "Archivo de secretos ya existe, no se sobrescribirá"
fi

echo "¡Configuración completada con éxito!"