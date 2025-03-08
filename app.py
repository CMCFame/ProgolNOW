import streamlit as st
import requests
from datetime import datetime, timedelta

# ----------------------------
# 1) Configure the leagues you want to show
# ----------------------------
# These numeric IDs come from the "Get Leagues List" response.
TARGET_LEAGUE_IDS = {
    # England
    47:  "Premier League",  # English Premier League

    # Spain
    87:  "LaLiga",

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

    # Argentina
    112:  "Liga Profesional",

    # Portugal
    61:   "Liga Portugal",

    # Belgium
    40:   "First Division A",
}

API_HOST = "free-api-live-football-data.p.rapidapi.com"

# ----------------------------
# 2) Data Fetching Functions (with debug)
# ----------------------------
def fetch_live_matches():
    """
    Fetch current live matches from the RapidAPI endpoint.
    Includes debug output in the Streamlit UI.
    """
    url = f"https://{API_HOST}/football-current-live"
    headers = {
        "x-rapidapi-key": st.secrets["rapidapi"]["api_key"],
        "x-rapidapi-host": API_HOST
    }

    # ---- Debug info before making the request ----
    st.write("DEBUG: Fetching live matches...")
    st.write("DEBUG: URL:", url)
    st.write("DEBUG: Headers:", headers)

    resp = requests.get(url, headers=headers)

    # ---- Debug info after receiving the response ----
    st.write("DEBUG: Response Status:", resp.status_code)
    st.write("DEBUG: Response Text:", resp.text)

    if resp.status_code == 200:
        return resp.json()
    else:
        st.error(f"Error fetching live matches (HTTP {resp.status_code}).")
        return None

def fetch_matches_by_date(date_str):
    """
    Fetch matches for a specific date (YYYYMMDD) from the RapidAPI endpoint.
    Includes debug output in the Streamlit UI.
    """
    url = f"https://{API_HOST}/football-get-matches-by-date"
    headers = {
        "x-rapidapi-key": st.secrets["rapidapi"]["api_key"],
        "x-rapidapi-host": API_HOST
    }
    params = {"date": date_str}

    # ---- Debug info before making the request ----
    st.write(f"DEBUG: Fetching matches for date {date_str}...")
    st.write("DEBUG: URL:", url)
    st.write("DEBUG: Headers:", headers)
    st.write("DEBUG: Query Params:", params)

    resp = requests.get(url, headers=headers, params=params)

    # ---- Debug info after receiving the response ----
    st.write("DEBUG: Response Status:", resp.status_code)
    st.write("DEBUG: Response Text:", resp.text)

    if resp.status_code == 200:
        return resp.json()
    else:
        st.error(f"Error fetching matches for {date_str} (HTTP {resp.status_code}).")
        return None

def filter_matches(matches):
    """
    Given a list of match objects, return only those whose 'leagueId'
    is in our TARGET_LEAGUE_IDS.
    """
    if not matches:
        return []
    return [m for m in matches if m.get("leagueId") in TARGET_LEAGUE_IDS]

# ----------------------------
# 3) Streamlit App Layout
# ----------------------------
st.title("Football Matches (With Debug)")

# 3.1 Live Matches
st.header("Live Matches (Filtered)")

live_data = fetch_live_matches()
if live_data:
    all_live = live_data.get("response", {}).get("live", [])
    filtered_live = filter_matches(all_live)

    if not filtered_live:
        st.write("No live matches from your target leagues at the moment.")
    else:
        for match in filtered_live:
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
    st.write("No live data returned (request failed).")

# 3.2 Historical Matches - Past 3 Days
st.header("Historical Matches (Past 3 Days)")

today = datetime.now()
for i in range(1, 4):
    date_str = (today - timedelta(days=i)).strftime("%Y%m%d")
    st.subheader(f"Matches on {date_str}")
    
    hist_data = fetch_matches_by_date(date_str)
    if hist_data:
        all_hist = hist_data.get("response", {}).get("matches", [])
        filtered_hist = filter_matches(all_hist)

        if not filtered_hist:
            st.write("No matches found from your leagues for this date.")
        else:
            for match in filtered_hist:
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
        st.write("No data returned for this date.")
