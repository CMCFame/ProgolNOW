import streamlit as st
import http.client
import json
import logging
from datetime import datetime, timedelta

API_HOST = "free-api-live-football-data.p.rapidapi.com"
LIVE_ENDPOINT = "/football-current-live"
HISTORICAL_ENDPOINT = "/football-get-matches-by-date"
POPULAR_LEAGUES_ENDPOINT = "/football-popular-leagues"

TOP_LEAGUES = [
    "Premier League",
    "Champions League",
    "LaLiga",
    "Bundesliga",
    "Europa League",
    "Ligue 1",
    "Serie A",
    "Copa del Rey",
    "FA Cup"
]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=60)
def fetch_football_data(endpoint, date=None):
    """Fetch data from the football API. No Streamlit UI calls in here."""
    try:
        api_key = st.secrets["rapidapi"]["api_key"]
    except KeyError:
        logger.error("API key not found in secrets.")
        return None
    
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': API_HOST
    }
    logger.info(f"Request Headers: {headers}")

    if date:
        endpoint += f"?date={date}"

    try:
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()

        logger.info(f"Response Status Code: {res.status}")
        logger.info(f"Response Headers: {res.getheaders()}")
        logger.info(f"Response Content: {data.decode('utf-8')}")

        if res.status == 200:
            return json.loads(data)
        else:
            logger.error(f"Error: {res.status} - {data.decode('utf-8')}")
            return None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None

def get_popular_leagues():
    data = fetch_football_data(POPULAR_LEAGUES_ENDPOINT)
    if not data:
        return {}
    leagues_dict = {}
    for league in data.get("response", {}).get("popular", []):
        # example: "Premier League": 123
        leagues_dict[league['name']] = league['id']
    return leagues_dict

st.title("Football Data App")

# 1. Popular Leagues
st.subheader("Fetching Popular Leagues")
popular_leagues = get_popular_leagues()
if not popular_leagues:
    st.error("Failed to retrieve popular leagues.")
else:
    st.write("Leagues fetched. For debugging, here they are:")
    st.write(popular_leagues)

# Filter top leagues by name
top_league_ids = {name: league_id 
                  for name, league_id in popular_leagues.items()
                  if name in TOP_LEAGUES}
st.write("Top League IDs:", top_league_ids)

# 2. Live Football Data
st.header("Live Football Data")
live_data = fetch_football_data(LIVE_ENDPOINT)
if not live_data:
    st.error("No live data available or failed to fetch.")
else:
    live_matches = live_data.get("response", {}).get("live", [])
    if not live_matches:
        st.write("No live matches available.")
    else:
        for match in live_matches:
            # Show only matches from top leagues:
            if match['leagueId'] in top_league_ids.values():
                home_name = match['home']['name']
                away_name = match['away']['name']
                with st.expander(f"{home_name} vs {away_name} (Live)"):
                    st.write(f"**League**: {match.get('leagueName', 'N/A')}")
                    st.write(f"**Time**: {match.get('time', 'N/A')}")
                    home_score = match['home'].get('score', 'N/A')
                    away_score = match['away'].get('score', 'N/A')
                    st.write(f"**Score**: {home_score} - {away_score}")
                    status = match.get('status', {})
                    st.write(f"**Status**: {status.get('scoreStr', 'N/A')}")
                    st.write(f"**Live Time**: {status.get('liveTime', {}).get('long', 'N/A')}")
                    st.write(f"**Tournament Stage**: {match.get('tournamentStage', 'N/A')}")

# 3. Historical Football Data
st.header("Historical Football Data (Past 24 Hours)")
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")  # check API format
historical_data = fetch_football_data(HISTORICAL_ENDPOINT, date=yesterday)
if not historical_data:
    st.error("No historical data available or failed to fetch.")
else:
    historical_matches = historical_data.get("response", {}).get("matches", [])
    if not historical_matches:
        st.write("No historical matches available.")
    else:
        for match in historical_matches:
            if match['leagueId'] in top_league_ids.values():
                with st.expander(f"{match['home']['name']} vs {match['away']['name']} (Historical)"):
                    st.write(f"**League**: {match.get('leagueName', 'N/A')}")
                    st.write(f"**Time**: {match.get('time', 'N/A')}")
                    home_score = match['home'].get('score', 'N/A')
                    away_score = match['away'].get('score', 'N/A')
                    st.write(f"**Score**: {home_score} - {away_score}")
                    status = match.get('status', {})
                    st.write(f"**Status**: {status.get('scoreStr', 'N/A')}")
                    st.write(f"**Tournament Stage**: {match.get('tournamentStage', 'N/A')}")