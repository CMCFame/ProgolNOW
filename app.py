import streamlit as st
import http.client
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the API endpoint and headers
API_HOST = "free-api-live-football-data.p.rapidapi.com"
API_ENDPOINT = "/football-current-live"

# Function to make API requests with debugging
@st.cache_data(ttl=60)  # Cache the data for 60 seconds
def get_football_data():
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
        conn.request("GET", API_ENDPOINT, headers=headers)
        res = conn.getresponse()
        data = res.read()

        logger.info(f"Response Status Code: {res.status}")
        logger.info(f"Response Headers: {res.getheaders()}")
        logger.info(f"Response Content: {data.decode('utf-8')}")

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

# Streamlit app layout
st.title("Live Football Data App")

# Display live football data
st.header("Live Football Data")
data = get_football_data()
if data:
    matches = data.get("response", {}).get("live", [])
    if matches:
        for match in matches:
            with st.expander(f"{match['home']['name']} vs {match['away']['name']}"):
                st.write(f"**League ID**: {match['leagueId']}")
                st.write(f"**Time**: {match['time']}")
                st.write(f"**Score**: {match['home']['score']} - {match['away']['score']}")
                st.write(f"**Status**: {match['status']['scoreStr']}")
                st.write(f"**Live Time**: {match['status']['liveTime']['long']}")
                st.write(f"**Tournament Stage**: {match['tournamentStage']}")
    else:
        st.write("No live matches available.")
else:
    st.write("No data available.")
