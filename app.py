import streamlit as st
import http.client
import json
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the API endpoint and headers
API_HOST = "free-api-live-football-data.p.rapidapi.com"
LIVE_ENDPOINT = "/football-current-live"
HISTORICAL_ENDPOINT = "/football-get-matches-by-date"
POPULAR_LEAGUES_ENDPOINT = "/football-popular-leagues"

# List of top leagues to filter
TOP_LEAGUES = [
    "Serie A",
    "Eredivisie",
    "LaLiga",
    "Bundesliga",
    "Primeira Liga",
    "Liga MX",
    "Liga Profesional",
    "Premier League",
    "Ligue 1",
    "Liga de Ascenso MX",
    "Liga Femenil MX"
]

# Function to make API requests with debugging
@st.cache_data(ttl=60)  # Cache the data for 60 seconds
def get_football_data(endpoint, date=None):
    api_key = st.secrets.get("rapidapi", {}).get("api_key")
    if not api_key:
        st.error("API key not found in secrets.")
        logger.error("API key not found in secrets.")
        return None

    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': API_HOST
    }

    logger.info(f"Request Headers: {headers}")

    try:
        if date:
            endpoint += f"?date={date}"
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()

        logger.info(f"Response Status Code: {res.status}")
        logger.info(f"Response Headers: {res.getheaders()}")
        logger.info(f"Response Content: {data.decode('utf-8')}")
        st.write(f"Response Content: {data.decode('utf-8')}")  # Debug print

        if res.status == 200:
            return json.loads(data)
        else:
            st.error(f"Error: {res.status}")
            logger.error(f"Error: {res.status}")
            st.error(f"Response Text: {data.decode('utf-8')}")
            logger.error(f"Response Text: {data.decode('utf-8')}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        logger.error(f"An error occurred: {e}")
        return None

# Function to get popular leagues
def get_popular_leagues():
    data = get_football_data(POPULAR_LEAGUES_ENDPOINT)
    if data:
        leagues_dict = {}
        for country in data.get("response", {}).get("leagues", []):
            for league in country.get("leagues", []):
                leagues_dict[league['name']] = league['id']
        return leagues_dict
    return {}

# Streamlit app layout
st.title("Football Data App")

# Get popular leagues
popular_leagues = get_popular_leagues()
top_league_ids = {name: league_id for name, league_id in popular_leagues.items() if name in TOP_LEAGUES}
st.write("Top League IDs:", top_league_ids)  # Debug print

# Display live football data
st.header("Live Football Data")
live_data = get_football_data(LIVE_ENDPOINT)
if live_data:
    live_matches = live_data.get("response", {}).get("live", [])
    if live_matches:
        for match in live_matches:
            st.write(f"Match: {match}")  # Debug print
            if match['leagueId'] in top_league_ids.values():
                with st.expander(f"{match['home']['name']} vs {match['away']['name']} (Live)"):
                    st.write(f"**League**: {match.get('leagueName', 'N/A')}")
                    st.write(f"**Time**: {match.get('time', 'N/A')}")
                    st.write(f"**Score**: {match['home'].get('score', 'N/A')} - {match['away'].get('score', 'N/A')}")
                    status = match.get('status', {})
                    st.write(f"**Status**: {status.get('scoreStr', 'N/A')}")
                    st.write(f"**Live Time**: {status.get('liveTime', {}).get('long', 'N/A')}")
                    st.write(f"**Tournament Stage**: {match.get('tournamentStage', 'N/A')}")
    else:
        st.write("No live matches available.")
else:
    st.write("No live data available.")

# Display historical football data for the past 24 hours
st.header("Historical Football Data (Past 24 Hours)")
yesterday = (datetime.now() - timedelta(hours=24)).strftime("%Y%m%d")
historical_data = get_football_data(HISTORICAL_ENDPOINT, date=yesterday)
if historical_data:
    historical_matches = historical_data.get("response", {}).get("matches", [])
    if historical_matches:
        for match in historical_matches:
            if match['leagueId'] in top_league_ids.values():
                with st.expander(f"{match['home']['name']} vs {match['away']['name']} (Historical)"):
                    st.write(f"**League**: {match.get('leagueName', 'N/A')}")
                    st.write(f"**Time**: {match.get('time', 'N/A')}")
                    st.write(f"**Score**: {match['home'].get('score', 'N/A')} - {match['away'].get('score', 'N/A')}")
                    status = match.get('status', {})
                    st.write(f"**Status**: {status.get('scoreStr', 'N/A')}")
                    st.write(f"**Tournament Stage**: {match.get('tournamentStage', 'N/A')}")
    else:
        st.write("No historical matches available.")
else:
    st.write("No historical data available.")