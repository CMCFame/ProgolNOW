# Quiniela Progol Tracker

Una aplicación web para seguimiento en tiempo real de resultados de fútbol para quinielas Progol. Recibe actualizaciones cuando cambia un resultado en tus quinielas.

![Logo Quiniela](https://i.imgur.com/CChLqSG.png)

## Características

- **Seguimiento en tiempo real**: Actualización automática de resultados cada 30 segundos.
- **Soporte para múltiples ligas**: Liga MX, Liga Expansión MX, Liga Femenil MX, Premier League, Serie A, Bundesliga, Eredivisie, Ligue 1, y muchas más.
- **Gestión de quinielas**: Crea y gestiona hasta 30 quinielas diferentes.
- **Notificaciones**: Recibe alertas cuando cambia un resultado en tus quinielas.
- **Interfaz responsive**: Diseñada para funcionar tanto en dispositivos móviles como de escritorio.

## Tecnologías utilizadas

- **Streamlit**: Framework para la interfaz de usuario.
- **ScraperFC**: Librería para obtener datos de fútbol de SofaScore.
- **SQLite**: Base de datos para almacenar partidos y quinielas.
- **APScheduler**: Programador para actualizaciones periódicas.

## Instalación

### Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. Clona este repositorio:
```bash
git clone https://github.com/tu-usuario/quiniela-progol-tracker.git
cd quiniela-progol-tracker
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación estará disponible en tu navegador en `http://localhost:8501`.

### Estructura del proyecto

- **app.py**: Aplicación principal de Streamlit.
- **data_service.py**: Servicio para obtener datos de partidos desde SofaScore.
- **quiniela_manager.py**: Gestiona las quinielas de usuarios.
- **scheduler.py**: Programador de tareas para actualización periódica.
- **database.py**: Operaciones de base de datos.
- **config.py**: Configuración de la aplicación.

## Personalización

Puedes personalizar varios aspectos de la aplicación modificando el archivo `config.py`:

- **UPDATE_INTERVAL**: Intervalo en segundos entre actualizaciones (por defecto: 30).
- **CURRENT_SEASON**: Temporada actual para SofaScore (por defecto: "2024").
- **LIGAS_PROGOL**: Lista de ligas a considerar para Progol.
- **MAX_QUINIELAS_POR_USUARIO**: Número máximo de quinielas por usuario (por defecto: 30).

## Despliegue

Para desplegar esta aplicación en producción, puedes utilizar servicios como:

- [Streamlit Cloud](https://streamlit.io/cloud)
- [Heroku](https://heroku.com)
- [PythonAnywhere](https://pythonanywhere.com)

## Contribuciones

Las contribuciones son bienvenidas. Por favor, siente libre de abrir un issue o pull request.

## Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).

## Agradecimientos

- A [Owen](https://github.com/oseymour) por crear la librería [ScraperFC](https://github.com/oseymour/ScraperFC).
- A [SofaScore](https://www.sofascore.com/) por proporcionar los datos de partidos.

## Descargo de responsabilidad

Esta aplicación es solo para uso educativo y personal. No está afiliada oficialmente con Progol o SofaScore. El uso de los datos obtenidos debe cumplir con los términos y condiciones de las fuentes originales.