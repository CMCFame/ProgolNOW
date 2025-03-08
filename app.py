import streamlit as st
import requests
from datetime import datetime, timedelta

# ----------------------------
# 1) Specify the leagues you want
# ----------------------------
# The dictionary keys are league IDs from your "Get Leagues List All with Countries" response
# The values are just friendly display labels.
TARGET_LEAGUE_IDS = {
    # England
    47:  "Premier League",   # English Premier League
    132: "FA Cup",

    # Spain
    87:  "LaLiga",
    138: "Copa del Rey",

    # Germany
    54:  "Bundesliga",

    # France
    53:  "Ligue 1",

    # Italy
    55:  "Serie A",

    # Mexico
    230:  "Liga MX",
    8976: "Liga de Expansión MX",
    9906: "Liga MX Femenil",

    # Tournaments that don't appear in the big JSON because they're under UEFA
    # Please replace ??? with the correct integer IDs once you have them.
    # "Champions League"
    ???: "Champions League", 
    # "Europa League"
    ???: "Europa League"
}

API_HOST = "free-api-live-football-data.p.rapidapi.com"

# ----------------------------
# 2) Data Fetching Functions
# ----------------------------
def fetch_live_matches():
    """
    Fetch current live matches from the RapidAPI endpoint.
    Expects to find them under JSON path: response -> live
    """
    url = f"https://{API_HOST}/football-current-live"
    headers = {
        "x-rapidapi-key": st.secrets["rapidapi"]["api_key"],  # Make sure your secrets.toml or Streamlit Cloud secrets are set up
        "x-rapidapi-host": API_HOST
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        st.error(f"Error fetching live matches: {resp.status_code}")
        return None
    return resp.json()

def fetch_matches_by_date(date_str):
    """
    Fetch matches for a given date (YYYYMMDD) from the RapidAPI endpoint.
    Expects to find them under JSON path: response -> matches
    """
    url = f"https://{API_HOST}/football-get-matches-by-date"
    headers = {
        "x-rapidapi-key": st.secrets["rapidapi"]["api_key"],
        "x-rapidapi-host": API_HOST
    }
    params = {"date": date_str}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        st.error(f"Error fetching matches for {date_str}: {resp.status_code}")
        return None
    return resp.json()

def filter_matches(matches):
    """
    Given a list of match objects, return only those whose leagueId
    matches one of the IDs in TARGET_LEAGUE_IDS.
    """
    if not matches:
        return []
    return [m for m in matches if m.get("leagueId") in TARGET_LEAGUE_IDS]

# ----------------------------
# 3) Streamlit App Layout
# ----------------------------
st.title("Football Data Filtered by Favorite Leagues")

# ----------------------------
# LIVE MATCHES
# ----------------------------
st.header("Live Matches (Filtered)")

live_data = fetch_live_matches()
if live_data:
    # Typically, matches are under live_data["response"]["live"]
    all_live = live_data.get("response", {}).get("live", [])
    wanted_live = filter_matches(all_live)
    
    if not wanted_live:
        st.write("No live matches found in your specified leagues.")
    else:
        for match in wanted_live:
            league_id = match["leagueId"]
            league_name = TARGET_LEAGUE_IDS.get(league_id, "Unknown League")
            home = match["home"]["name"]
            away = match["away"]["name"]
            home_score = match["home"].get("score", "N/A")
            away_score = match["away"].get("score", "N/A")
            match_time = match.get("time", "N/A")
            status_info = match.get("status", {})

            with st.expander(f"{league_name}: {home} vs {away}"):
                st.write(f"**Time**: {match_time}")
                st.write(f"**Score**: {home_score} - {away_score}")
                st.write(f"**Status**: {status_info.get('scoreStr', 'N/A')}")
                st.write(f"**Live Time**: {status_info.get('liveTime', {}).get('long', 'N/A')}")
else:
    st.write("No live data returned from the endpoint.")

# ----------------------------
# HISTORICAL MATCHES (Past 3 Days)
# ----------------------------
st.header("Historical Matches (Past 3 Days)")

today = datetime.now()
for i in range(1, 4):
    # Example: 3 days. You can adjust or pick a single date.
    date_str = (today - timedelta(days=i)).strftime("%Y%m%d")
    st.subheader(f"Matches on {date_str}")

    hist_data = fetch_matches_by_date(date_str)
    if hist_data:
        # Typically, matches are under hist_data["response"]["matches"]
        all_hist = hist_data.get("response", {}).get("matches", [])
        wanted_hist = filter_matches(all_hist)

        if not wanted_hist:
            st.write("No matches from your leagues on this date.")
        else:
            for match in wanted_hist:
                league_id = match["leagueId"]
                league_name = TARGET_LEAGUE_IDS.get(league_id, "Unknown League")
                home = match["home"]["name"]
                away = match["away"]["name"]
                home_score = match["home"].get("score", "N/A")
                away_score = match["away"].get("score", "N/A")
                match_time = match.get("time", "N/A")
                status_info = match.get("status", {})

                with st.expander(f"{league_name}: {home} vs {away}"):
                    st.write(f"**Time**: {match_time}")
                    st.write(f"**Score**: {home_score} - {away_score}")
                    st.write(f"**Status**: {status_info.get('scoreStr', 'N/A')}")
    else:
        st.write(f"No data returned for {date_str}.")