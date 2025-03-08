import streamlit as st
import requests
from datetime import datetime, timedelta

# Constants
API_HOST = "free-api-live-football-data.p.rapidapi.com"

def get_live_matches():
    """Fetch current live matches from the RapidAPI endpoint."""
    url = f"https://{API_HOST}/football-current-live"
    headers = {
        "x-rapidapi-key": st.secrets["rapidapi"]["api_key"],  # Load from secrets
        "x-rapidapi-host": API_HOST
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"Live Matches Request Failed: {response.status_code}")
        return None
    
    return response.json()

def get_matches_by_date(date_str):
    """
    Fetch matches for a given date (e.g. '20241107') 
    from the RapidAPI endpoint.
    """
    url = f"https://{API_HOST}/football-get-matches-by-date"
    headers = {
        "x-rapidapi-key": st.secrets["rapidapi"]["api_key"],
        "x-rapidapi-host": API_HOST
    }
    params = {"date": date_str}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        st.error(f"Historical Matches Request Failed ({date_str}): {response.status_code}")
        return None
    
    return response.json()

# ------------------- Streamlit App Layout --------------------
st.title("Live & Historical Football Matches")

# ---- Live Matches ----
st.header("Live Matches")
live_data = get_live_matches()
if live_data:
    live_matches = live_data.get("response", {}).get("live", [])
    if live_matches:
        for match in live_matches:
            home_team = match["home"]["name"]
            away_team = match["away"]["name"]
            home_score = match["home"].get("score", "N/A")
            away_score = match["away"].get("score", "N/A")
            time_info = match.get("time", "N/A")
            status_info = match.get("status", {})

            with st.expander(f"{home_team} vs {away_team} — Live Scoreboard"):
                st.write(f"**Time**: {time_info}")
                st.write(f"**Score**: {home_score} - {away_score}")
                st.write(f"**Status**: {status_info.get('scoreStr', 'N/A')}")
                st.write(f"**Live Time**: {status_info.get('liveTime', {}).get('long', 'N/A')}")
    else:
        st.write("No ongoing matches at the moment.")

# ---- Historical Matches (past 3 days) ----
st.header("Historical Matches (Past 3 Days)")
today = datetime.now()
for i in range(1, 4):
    date_str = (today - timedelta(days=i)).strftime("%Y%m%d")
    st.subheader(f"Matches on {date_str}")

    hist_data = get_matches_by_date(date_str)
    if hist_data:
        hist_matches = hist_data.get("response", {}).get("matches", [])
        if hist_matches:
            for match in hist_matches:
                home_team = match["home"]["name"]
                away_team = match["away"]["name"]
                home_score = match["home"].get("score", "N/A")
                away_score = match["away"].get("score", "N/A")
                time_info = match.get("time", "N/A")
                status_info = match.get("status", {})

                with st.expander(f"{home_team} vs {away_team} — Past Match"):
                    st.write(f"**Time**: {time_info}")
                    st.write(f"**Score**: {home_score} - {away_score}")
                    st.write(f"**Status**: {status_info.get('scoreStr', 'N/A')}")
        else:
            st.write("No matches found for this date.")
    else:
        st.write("No data returned for this date.")