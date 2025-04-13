import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import re
import base64
import io
import requests
import json
import plotly.express as px

# Set page config
st.set_page_config(page_title="Quiniela Match Tracker", layout="wide", page_icon="⚽")

# App title and description
st.title("⚽ Quiniela Match Tracker")
st.markdown("""
This app tracks the matches in your Quiniela spreadsheet and updates them with live results from Sofascore.
Upload your Quiniela CSV or Excel file to get started.
""")

# Set up session state for storing data between reruns
if 'search_completed' not in st.session_state:
    st.session_state.search_completed = False
if 'match_results' not in st.session_state:
    st.session_state.match_results = []
if 'match_info' not in st.session_state:
    st.session_state.match_info = {}
if 'leagues_to_search' not in st.session_state:
    st.session_state.leagues_to_search = [
        {"name": "Liga MX", "id": 10},
        {"name": "MLS", "id": 242},
        {"name": "EPL", "id": 17},
        {"name": "La Liga", "id": 8},
        {"name": "Bundesliga", "id": 35},
        {"name": "Serie A", "id": 23},
        {"name": "Ligue 1", "id": 34},
        {"name": "Champions League", "id": 7},
        {"name": "Europa League", "id": 679}
    ]

# Helper functions
# Direct Sofascore API interaction
def get_api_response(url):
    """Get response from Sofascore API with proper headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.sofascore.com/',
        'Origin': 'https://www.sofascore.com',
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

def search_team(team_name):
    """Search for a team by name on Sofascore."""
    # Encode the team name for the URL
    encoded_name = requests.utils.quote(team_name)
    url = f"https://api.sofascore.com/api/v1/search/teams/{encoded_name}"
    
    response = get_api_response(url)
    if response and 'teams' in response:
        return response['teams']
    return []

def get_team_events(team_id, limit=10):
    """Get recent events (matches) for a team."""
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0?limit={limit}"
    
    response = get_api_response(url)
    if response and 'events' in response:
        return response['events']
    return []

def get_league_events(league_id, season_id=None):
    """Get events for a specific league."""
    # If no season ID, first get the latest season
    if not season_id:
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/seasons"
        response = get_api_response(url)
        if response and 'seasons' in response and len(response['seasons']) > 0:
            season_id = response['seasons'][0]['id']
        else:
            return []
    
    # Get events for this season
    url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/events/last/0"
    response = get_api_response(url)
    if response and 'events' in response:
        return response['events']
    
    return []

def get_upcoming_events(league_id, season_id=None):
    """Get upcoming events for a specific league."""
    # If no season ID, first get the latest season
    if not season_id:
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/seasons"
        response = get_api_response(url)
        if response and 'seasons' in response and len(response['seasons']) > 0:
            season_id = response['seasons'][0]['id']
        else:
            return []
    
    # Get events for this season
    url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/events/next/0"
    response = get_api_response(url)
    if response and 'events' in response:
        return response['events']
    
    return []

def similar_team_name(name1, name2):
    """Check if two team names are similar."""
    if not name1 or not name2:
        return False
        
    # Convert to lowercase
    name1 = name1.lower()
    name2 = name2.lower()
    
    # Define mappings for common team names
    team_mappings = {
        'guadalajara': 'chivas',
        'america': 'club america',
        'cruz azul': 'club cruz azul',
        'monterrey': 'cf monterrey',
        'tigres': 'tigres uanl',
        'pumas': 'pumas unam',
        'atlas': 'atlas fc',
        'toluca': 'deportivo toluca',
        'juarez': 'fc juarez',
        'santos': 'santos laguna',
        'pachuca': 'cf pachuca',
        'queretaro': 'queretaro fc',
        'mazatlan': 'mazatlan fc',
        'puebla': 'club puebla',
        'tijuana': 'club tijuana',
        'necaxa': 'club necaxa',
        'leon': 'club leon',
        'atletico': 'atletico de madrid',
        'inter': 'inter milan',
        'man utd': 'manchester united',
        'man city': 'manchester city',
        'tottenham': 'tottenham hotspur',
        'wolves': 'wolverhampton',
        'st pauli': 'fc st pauli',
        'st. pauli': 'fc st pauli',
        'h. kiel': 'holstein kiel',
        'holstein': 'holstein kiel',
        'paris': 'paris saint-germain',
        'psg': 'paris saint-germain',
        'real': 'real madrid',
        'genoa': 'genoa cfc',
        'verona': 'hellas verona',
        'estudiantes': 'estudiantes de la plata',
        'gimnasia': 'gimnasia la plata',
        'gimnasia lp': 'gimnasia la plata',
        'millonarios': 'millonarios fc',
        'chicago': 'chicago fire',
        'columbus': 'columbus crew',
        'st. louis': 'st. louis city',
        'st louis': 'st. louis city',
        'betis': 'real betis',
        'villarreal': 'villarreal cf',
        'osasuna': 'ca osasuna',
        'girona': 'girona fc',
        'lazio': 'ss lazio',
        'roma': 'as roma',
        'a. nacional': 'atletico nacional',
        'niza': 'ogc nice',
        'nice': 'ogc nice',
        'estrasburgo': 'strasbourg',
        'strasbourg': 'rc strasbourg',
        'bragantino': 'rb bragantino',
        'botafogo': 'botafogo fr',
        'gremio': 'gremio fbpa',
        'flamengo': 'flamengo rj',
        'gdl fem': 'guadalajara women',
        'fem': 'women',
        'celaya': 'club celaya',
        'u de g': 'leones negros',
        'miami': 'inter miami'
    }
    
    # Check mappings
    for short, full in team_mappings.items():
        if (short in name1 and full in name2) or (full in name1 and short in name2):
            return True
    
    # Remove common words
    common_words = ['fc', 'cf', 'united', 'city', 'club', 'deportivo', 'sporting', 'real', 
                   'athletic', 'atletico', 'ac', 'as', 'rc', 'sc', 'cd', 'sd', 'afc', 'de']
    
    for word in common_words:
        name1 = name1.replace(f" {word} ", " ").replace(f" {word}", "").replace(f"{word} ", "")
        name2 = name2.replace(f" {word} ", " ").replace(f" {word}", "").replace(f"{word} ", "")
    
    # Remove non-alphanumeric characters
    name1 = re.sub(r'[^a-zA-Z0-9]', '', name1).strip()
    name2 = re.sub(r'[^a-zA-Z0-9]', '', name2).strip()
    
    # Check if one name is fully contained in the other
    return name1 in name2 or name2 in name1

def match_to_result_code(match_data):
    """Convert match data to result code (L, E, V)."""
    if 'status' not in match_data or match_data['status']['type'] != 'finished':
        return None
    
    home_score = match_data.get('homeScore', {}).get('current', 0)
    away_score = match_data.get('awayScore', {}).get('current', 0)
    
    if home_score > away_score:
        return 'L'  # Local/Home win
    elif home_score < away_score:
        return 'V'  # Visitante/Away win
    else:
        return 'E'  # Empate/Draw

def search_for_match(home_team, away_team):
    """Advanced search for a match with multiple approaches."""
    # 1. First try all leagues for both upcoming and recent events
    for league in st.session_state.leagues_to_search:
        # Check recent events
        events = get_league_events(league["id"])
        match = find_match_in_events(events, home_team, away_team)
        if match:
            return match, f"Found in {league['name']} (recent)"
        
        # Check upcoming events
        events = get_upcoming_events(league["id"])
        match = find_match_in_events(events, home_team, away_team)
        if match:
            return match, f"Found in {league['name']} (upcoming)"
        
        # Add a small delay to prevent API rate limiting
        time.sleep(0.2)
    
    # 2. Try searching by team name
    # Search for home team
    home_teams = search_team(home_team)
    for team in home_teams[:2]:  # Limit to first 2 to save time
        team_id = team['id']
        events = get_team_events(team_id)
        match = find_match_in_events(events, home_team, away_team)
        if match:
            return match, f"Found via team search ({team['name']})"
        time.sleep(0.2)
    
    # Search for away team if home team search didn't work
    away_teams = search_team(away_team)
    for team in away_teams[:2]:  # Limit to first 2 to save time
        team_id = team['id']
        events = get_team_events(team_id)
        match = find_match_in_events(events, home_team, away_team)
        if match:
            return match, f"Found via team search ({team['name']})"
        time.sleep(0.2)
    
    return None, "Not found"

def find_match_in_events(events, home_team, away_team):
    """Find a match involving both teams in a list of events."""
    for event in events:
        event_home = event['homeTeam']['name']
        event_away = event['awayTeam']['name']
        
        # Check if this event involves both teams (in correct order)
        if similar_team_name(home_team, event_home) and similar_team_name(away_team, event_away):
            return event
        
        # Also check for reversed order (rare but possible)
        if similar_team_name(home_team, event_away) and similar_team_name(away_team, event_home):
            return event
    
    return None

def update_quiniela_results(df, match_results):
    """Update the Quiniela dataframe with match results."""
    # Copy the dataframe to avoid modifying the original
    df_updated = df.copy()
    
    # Calculate total matches by result type
    locales_count = 0
    empates_count = 0
    visitas_count = 0
    
    # Update each row with match results
    for idx, row in df_updated.iterrows():
        if idx in match_results and match_results[idx]['result'] is not None:
            df_updated.at[idx, 'Resultado'] = match_results[idx]['result']
            
            # Count result types
            result = match_results[idx]['result']
            if result == 'L':
                locales_count += 1
            elif result == 'E':
                empates_count += 1
            elif result == 'V':
                visitas_count += 1
    
    # Get prediction columns - regex pattern to match Q-1 through Q-20, YO1, YO2, etc.
    prediction_cols = [col for col in df.columns if re.match(r'Q-\d+|YO\d+|QPOS|REYP|EQ', col)]
    
    aciertos_regular = [0] * 13  # Q-1 to Q-13
    aciertos_revancha = [0] * 7  # Q-14 to Q-20
    
    # Adjusted to only consider rows that have been updated with results
    for idx, row in df_updated.iterrows():
        resultado = row['Resultado']
        if pd.notna(resultado) and resultado in ['L', 'E', 'V']:
            # Count correct predictions for regular columns (Q-1 to Q-13)
            for i, col in enumerate([f'Q-{j}' for j in range(1, 14)]):
                if col in df.columns and row[col] == resultado:
                    aciertos_regular[i] += 1
            
            # Count correct predictions for revancha columns (Q-14 to Q-20)
            for i, col in enumerate([f'Q-{j}' for j in range(14, 21)]):
                if col in df.columns and row[col] == resultado:
                    aciertos_revancha[i] += 1
    
    # Find summary rows by looking for rows with specific labels
    locales_row = None
    empates_row = None
    visitas_row = None
    aciertos_reg_row = None
    aciertos_rev_row = None
    
    for idx, row in df.iterrows():
        # Skip if the first cell is not a string
        if not isinstance(row.iloc[0], str):
            continue
            
        first_cell = row.iloc[0].lower()
        if '# locales' in first_cell:
            locales_row = idx
        elif '# empates' in first_cell:
            empates_row = idx
        elif '# visitas' in first_cell:
            visitas_row = idx
        elif 'aciertos regular' in first_cell:
            aciertos_reg_row = idx
        elif 'aciertos revancha' in first_cell:
            aciertos_rev_row = idx
    
    # Update summary row values if found
    if locales_row is not None:
        df_updated.at[locales_row, 1] = locales_count  # Column B
        
    if empates_row is not None:
        df_updated.at[empates_row, 1] = empates_count  # Column B
        
    if visitas_row is not None:
        df_updated.at[visitas_row, 1] = visitas_count  # Column B
        
    # Update aciertos rows
    if aciertos_reg_row is not None:
        regular_cols = [f'Q-{j}' for j in range(1, 14)]
        for i, col in enumerate(regular_cols):
            if col in df.columns:
                col_idx = df.columns.get_loc(col)
                df_updated.at[aciertos_reg_row, col_idx] = aciertos_regular[i]
    
    if aciertos_rev_row is not None:
        revancha_cols = [f'Q-{j}' for j in range(14, 21)]
        for i, col in enumerate(revancha_cols):
            if col in df.columns:
                col_idx = df.columns.get_loc(col)
                df_updated.at[aciertos_rev_row, col_idx] = aciertos_revancha[i]
    
    return df_updated

# File uploader
uploaded_file = st.file_uploader("Upload your Quiniela CSV or Excel file", type=['csv', 'xlsx', 'xls'])

if uploaded_file:
    # Read the file
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Display the original data
        st.subheader("Original Quiniela Data")
        st.dataframe(df)
        
        # Create tabs for different sections
        tab1, tab2, tab3 = st.tabs(["Match Tracking", "Results Visualization", "Data Export"])
        
        with tab1:
            # Look for rows with matches - typically those with "vs" in a column
            partido_col = None
            fecha_col = None
            resultado_col = None
            
            # Try to identify the column names
            for col in df.columns:
                if col.lower() == 'partido':
                    partido_col = col
                elif col.lower() == 'fecha':
                    fecha_col = col
                elif col.lower() == 'resultado':
                    resultado_col = col
            
            # If columns weren't found by name, try to guess based on content
            if not partido_col:
                for col in df.columns:
                    # Check if this column contains "vs" strings
                    if df[col].astype(str).str.contains('vs').any():
                        partido_col = col
                        break
            
            if not resultado_col:
                # Look for a column that might be results (often empty or contains L/E/V)
                for col in df.columns:
                    values = df[col].dropna().astype(str).unique()
                    if len(values) <= 3 and all(val in ['L', 'E', 'V', ''] for val in values):
                        resultado_col = col
                        break
            
            if not partido_col:
                st.error("Could not find a column containing match information (with 'vs'). Please check your file.")
            else:
                st.success(f"Found match column: {partido_col}")
                if resultado_col:
                    st.success(f"Found result column: {resultado_col}")
                else:
                    st.warning("Could not identify a clear results column. Will use 'Resultado' if it exists.")
                    resultado_col = 'Resultado'
                    if resultado_col not in df.columns:
                        df[resultado_col] = ""
            
            # Ensure the Resultado column exists
            if resultado_col not in df.columns:
                df[resultado_col] = ""
            
            # Find rows with matches
            matches = []
            match_info = {}
            
            for idx, row in df.iterrows():
                # Skip rows that don't look like match rows or summary rows
                if pd.notna(row[partido_col]) and isinstance(row[partido_col], str) and 'vs' in row[partido_col]:
                    partido = row[partido_col]
                    
                    # Extract teams
                    teams = partido.split('vs')
                    if len(teams) != 2:
                        continue
                        
                    home_team = teams[0].strip()
                    away_team = teams[1].strip()
                    
                    match_info[idx] = {
                        'partido': partido,
                        'home_team': home_team,
                        'away_team': away_team,
                        'sofascore_match': None,
                        'result': None,
                        'source': None
                    }
                    
                    matches.append((idx, home_team, away_team))
            
            # Display matches found
            st.subheader(f"Found {len(matches)} matches to track")
            
            if matches:
                # League selection for search prioritization
                st.subheader("League Search Settings")
                st.markdown("Select the leagues to search in priority order:")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Allow adding new leagues
                    league_name = st.text_input("League Name (e.g., Liga MX)", "")
                    league_id = st.text_input("League ID (e.g., 10)", "")
                    
                    if st.button("Add League") and league_name and league_id:
                        try:
                            league_id = int(league_id)
                            st.session_state.leagues_to_search.append({"name": league_name, "id": league_id})
                            st.success(f"Added {league_name} (ID: {league_id}) to search priorities")
                        except ValueError:
                            st.error("League ID must be a number")
                
                with col2:
                    # Show current leagues and allow reordering
                    st.write("Current League Search Order:")
                    for i, league in enumerate(st.session_state.leagues_to_search):
                        st.write(f"{i+1}. {league['name']} (ID: {league['id']})")
                
                # Track matches button
                st.subheader("Find Match Results")
                search_button = st.button("Search for Match Results")
                
                if search_button or st.session_state.search_completed:
                    # Reset state if doing a new search
                    if search_button:
                        st.session_state.match_results = []
                        st.session_state.match_info = match_info.copy()
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # If we haven't completed the search yet, do it
                    if not st.session_state.search_completed:
                        match_results_table = []
                        
                        # Search for each match in Sofascore
                        for i, (idx, home_team, away_team) in enumerate(matches):
                            status_text.text(f"Searching for {home_team} vs {away_team}...")
                            
                            # Find match in Sofascore
                            match, source = search_for_match(home_team, away_team)
                            
                            if match:
                                # Store match details
                                st.session_state.match_info[idx]['sofascore_match'] = match
                                st.session_state.match_info[idx]['result'] = match_to_result_code(match)
                                st.session_state.match_info[idx]['source'] = source
                                
                                # Extract info for display
                                sofascore_home = match['homeTeam']['name']
                                sofascore_away = match['awayTeam']['name']
                                status = match['status']['description']
                                
                                # Get scores
                                home_score = match.get('homeScore', {}).get('current', 0)
                                away_score = match.get('awayScore', {}).get('current', 0)
                                score = f"{home_score} - {away_score}"
                                
                                result_code = st.session_state.match_info[idx]['result'] if st.session_state.match_info[idx]['result'] else "Pending"
                                
                                # Get scheduled date if available
                                scheduled_date = "N/A"
                                if 'startTimestamp' in match:
                                    try:
                                        scheduled_date = datetime.fromtimestamp(match['startTimestamp']).strftime('%Y-%m-%d %H:%M')
                                    except:
                                        pass
                                
                                match_results_table.append({
                                    "Match": f"{home_team} vs {away_team}",
                                    "Sofascore Match": f"{sofascore_home} vs {sofascore_away}",
                                    "Status": status,
                                    "Score": score,
                                    "Result": result_code,
                                    "Scheduled Date": scheduled_date,
                                    "Source": source
                                })
                                
                                status_text.text(f"✅ Found match: {sofascore_home} vs {sofascore_away}")
                            else:
                                # Not found
                                match_results_table.append({
                                    "Match": f"{home_team} vs {away_team}",
                                    "Sofascore Match": "Not found",
                                    "Status": "N/A",
                                    "Score": "N/A",
                                    "Result": "N/A",
                                    "Scheduled Date": "N/A",
                                    "Source": "Not found"
                                })
                                
                                status_text.text(f"❌ Couldn't find match for {home_team} vs {away_team}")
                            
                            # Update progress
                            progress_bar.progress((i + 1) / len(matches))
                            time.sleep(0.3)  # Delay to prevent API rate limiting
                        
                        st.session_state.match_results = match_results_table
                        st.session_state.search_completed = True
                        
                    status_text.text("Finished searching for matches")
                    
                    # Display match results
                    st.subheader("Match Results")
                    match_results_df = pd.DataFrame(st.session_state.match_results)
                    
                    # Allow manual override of results for matches
                    st.dataframe(match_results_df, use_container_width=True)
                    
                    # Manual result override section
                    st.subheader("Manual Result Override")
                    st.markdown("If a match wasn't found or has the wrong result, you can manually set it here:")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Dropdown to select match
                        match_options = [f"{i}: {match[1]} vs {match[2]}" for i, match in enumerate(matches)]
                        selected_match = st.selectbox("Select Match", match_options)
                        selected_idx = int(selected_match.split(":")[0])
                        idx, home_team, away_team = matches[selected_idx]
                    
                    with col2:
                        # Input for result
                        result_options = ["", "L", "E", "V"]
                        manual_result = st.selectbox("Result (L/E/V)", result_options)
                    
                    with col3:
                        # Button to apply override
                        if st.button("Apply Override"):
                            st.session_state.match_info[idx]['result'] = manual_result if manual_result else None
                            st.session_state.match_info[idx]['source'] = "Manual override"
                            
                            # Update the match results table
                            for i, result in enumerate(st.session_state.match_results):
                                if result["Match"] == f"{home_team} vs {away_team}":
                                    st.session_state.match_results[i]["Result"] = manual_result if manual_result else "N/A"
                                    st.session_state.match_results[i]["Source"] = "Manual override"
                                    break
                            
                            st.success(f"Updated result for {home_team} vs {away_team} to {manual_result}")
                            # Force rerun to update the display
                            st.experimental_rerun()
                    
                    # Update the Quiniela results
                    updated_df = update_quiniela_results(df, st.session_state.match_info)
                    
                    # Display updated Quiniela
                    st.subheader("Updated Quiniela")
                    st.dataframe(updated_df)
                    
                    # Store updated dataframe in session state for export
                    st.session_state['updated_df'] = updated_df
                    
                    # Auto-refresh option
                    st.subheader("Auto-Refresh")
                    auto_refresh = st.checkbox("Enable auto-refresh", value=False)
                    
                    if auto_refresh:
                        refresh_interval = st.slider("Refresh interval (seconds)", 30, 300, 60)
                        st.info(f"This page will refresh every {refresh_interval} seconds")
                        time.sleep(refresh_interval)
                        
                        # Reset search completed to force a fresh search
                        st.session_state.search_completed = False
                        st.experimental_rerun()
        
        with tab2:
            st.subheader("Results Visualization")
            
            if 'updated_df' in st.session_state:
                updated_df = st.session_state['updated_df']
                
                # Count results by type
                result_counts = {
                    "L (Local Win)": (updated_df['Resultado'] == 'L').sum(),
                    "E (Draw)": (updated_df['Resultado'] == 'E').sum(),
                    "V (Away Win)": (updated_df['Resultado'] == 'V').sum(),
                    "Pending": len(matches) - (updated_df['Resultado'].isin(['L', 'E', 'V'])).sum()
                }
                
                # Create a pie chart
                if sum(result_counts.values()) > 0:
                    fig = px.pie(
                        values=list(result_counts.values()),
                        names=list(result_counts.keys()),
                        title="Match Results Distribution"
                    )
                    st.plotly_chart(fig)
                
                # Create a bar chart for prediction column accuracy
                prediction_cols = [col for col in df.columns if re.match(r'Q-\d+|YO\d+|QPOS|REYP|EQ', col)]
                
                if prediction_cols:
                    accuracy_data = []
                    
                    for col in prediction_cols:
                        correct = 0
                        total = 0
                        
                        for idx, row in updated_df.iterrows():
                            if row['Resultado'] in ['L', 'E', 'V']:
                                total += 1
                                if row[col] == row['Resultado']:
                                    correct += 1
                        
                        if total > 0:
                            accuracy = (correct / total) * 100
                            accuracy_data.append({"Column": col, "Accuracy (%)": accuracy})
                    
                    if accuracy_data:
                        accuracy_df = pd.DataFrame(accuracy_data)
                        fig = px.bar(
                            accuracy_df,
                            x="Column",
                            y="Accuracy (%)",
                            title="Prediction Accuracy by Column"
                        )
                        st.plotly_chart(fig)
            else:
                st.info("Track matches first to see visualizations")
        
        with tab3:
            st.subheader("Export Updated Data")
            
            if 'updated_df' in st.session_state:
                updated_df = st.session_state['updated_df']
                
                # Convert dataframe to CSV for download
                csv = updated_df.to_csv(index=False)
                b64_csv = base64.b64encode(csv.encode()).decode()
                href_csv = f'<a href="data:file/csv;base64,{b64_csv}" download="quiniela_updated.csv">Download Updated CSV</a>'
                st.markdown(href_csv, unsafe_allow_html=True)
                
                # Also offer Excel format
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    updated_df.to_excel(writer, sheet_name='Quiniela', index=False)
                
                buffer.seek(0)
                b64_excel = base64.b64encode(buffer.read()).decode()
                href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="quiniela_updated.xlsx">Download Updated Excel</a>'
                st.markdown(href_excel, unsafe_allow_html=True)
            else:
                st.info("Track matches first to enable export")
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.exception(e)
else:
    st.info("Please upload your Quiniela CSV or Excel file to get started.")

# Footer
st.markdown("---")
st.markdown("""
**About this app:**
- Built with Streamlit
- Data source: Sofascore API
- This app updates your Quiniela with live match results
""")