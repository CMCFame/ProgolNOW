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
if 'team_mappings' not in st.session_state:
    # Initialize with common mappings
    st.session_state.team_mappings = {
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
        'betis': 'real betis',
        'villarreal': 'villarreal cf',
        'osasuna': 'ca osasuna',
        'girona': 'girona fc',
        'h. kiel': 'holstein kiel',
        'st. pauli': 'fc st pauli',
        'verona': 'hellas verona',
        'lazio': 'ss lazio',
        'roma': 'as roma',
        'genoa': 'genoa cfc',
        'u de g': 'leones negros',
        'celaya': 'club celaya',
        'fem': 'women',
        'st. louis': 'st. louis city',
        'columbus': 'columbus crew'
    }

# Helper functions
# Date parsing function that handles MM/DD format
def parse_date(date_str):
    """Parse date string in MM/DD format to datetime object."""
    if not date_str or not isinstance(date_str, str):
        return None
        
    # Clean up the date string (remove non-numeric and slash characters)
    date_str = re.sub(r'[^\d/]', '', date_str)
    
    # Extract date parts (assuming MM/DD format)
    match = re.match(r'(\d+)/(\d+)', date_str)
    if not match:
        return None
    
    month, day = map(int, match.groups())
    
    # Get current year
    current_year = datetime.now().year
    
    # Create datetime object (at midnight)
    try:
        dt = datetime(current_year, month, day)
        
        # If the date is in the past by more than 6 months, it's probably next year
        if (datetime.now() - dt).days > 180:
            dt = dt.replace(year=current_year + 1)
            
        return dt
    except ValueError:
        return None

# Function to extract time from a string like "HH:MM" or any text containing time
def extract_time(time_str):
    """Extract time from a string."""
    if not time_str or not isinstance(time_str, str):
        return None
    
    # Look for a time pattern (HH:MM)
    match = re.search(r'(\d{1,2}):(\d{2})', time_str)
    if not match:
        return None
    
    hour, minute = map(int, match.groups())
    return hour, minute

# Function to combine date and time
def combine_date_time(date_obj, time_tuple):
    """Combine date object and time tuple into a datetime object."""
    if not date_obj or not time_tuple:
        return date_obj  # Return just the date if time is not available
    
    hour, minute = time_tuple
    return date_obj.replace(hour=hour, minute=minute)

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

def get_league_events(league_id, season_id=None, date_range=None):
    """Get events for a specific league with optional date filtering."""
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
    events = []
    
    if response and 'events' in response:
        events.extend(response['events'])
    
    # If we have a date range, filter events
    if date_range and len(date_range) == 2 and date_range[0] and date_range[1]:
        start_date, end_date = date_range
        filtered_events = []
        
        for event in events:
            if 'startTimestamp' in event:
                event_date = datetime.fromtimestamp(event['startTimestamp'])
                if start_date <= event_date <= end_date:
                    filtered_events.append(event)
            
        return filtered_events
    
    return events

def get_upcoming_events(league_id, season_id=None, date_range=None):
    """Get upcoming events for a specific league with optional date filtering."""
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
    events = []
    
    if response and 'events' in response:
        events.extend(response['events'])
    
    # If we have a date range, filter events
    if date_range and len(date_range) == 2 and date_range[0] and date_range[1]:
        start_date, end_date = date_range
        filtered_events = []
        
        for event in events:
            if 'startTimestamp' in event:
                event_date = datetime.fromtimestamp(event['startTimestamp'])
                if start_date <= event_date <= end_date:
                    filtered_events.append(event)
            
        return filtered_events
    
    return events

def similar_team_name(name1, name2, custom_mappings=None):
    """Check if two team names are similar using mappings and fuzzy matching."""
    if not name1 or not name2:
        return False
        
    # Convert to lowercase
    name1 = name1.lower()
    name2 = name2.lower()
    
    # Direct match
    if name1 == name2:
        return True
    
    # Use custom mappings if provided, otherwise use default mappings
    team_mappings = custom_mappings if custom_mappings else st.session_state.team_mappings
    
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

def search_for_match(home_team, away_team, date_range=None):
    """Advanced search for a match with multiple approaches."""
    # 1. First try all leagues for both upcoming and recent events
    for league in st.session_state.leagues_to_search:
        # Check recent events
        events = get_league_events(league["id"], date_range=date_range)
        match = find_match_in_events(events, home_team, away_team)
        if match:
            return match, f"Found in {league['name']} (recent)"
        
        # Check upcoming events
        events = get_upcoming_events(league["id"], date_range=date_range)
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
        
        # Filter events by date range if provided
        if date_range and date_range[0] and date_range[1]:
            filtered_events = []
            for event in events:
                if 'startTimestamp' in event:
                    event_date = datetime.fromtimestamp(event['startTimestamp'])
                    if date_range[0] <= event_date <= date_range[1]:
                        filtered_events.append(event)
            events = filtered_events
            
        match = find_match_in_events(events, home_team, away_team)
        if match:
            return match, f"Found via team search ({team['name']})"
        time.sleep(0.2)
    
    # Search for away team if home team search didn't work
    away_teams = search_team(away_team)
    for team in away_teams[:2]:  # Limit to first 2 to save time
        team_id = team['id']
        events = get_team_events(team_id)
        
        # Filter events by date range if provided
        if date_range and date_range[0] and date_range[1]:
            filtered_events = []
            for event in events:
                if 'startTimestamp' in event:
                    event_date = datetime.fromtimestamp(event['startTimestamp'])
                    if date_range[0] <= event_date <= date_range[1]:
                        filtered_events.append(event)
            events = filtered_events
            
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
    
    # Find the Resultado column index
    resultado_idx = None
    for i, col in enumerate(df.columns):
        if isinstance(col, str) and 'resultado' in col.lower():
            resultado_idx = i
            break
    
    # If Resultado column is not found, try to use the known index
    if resultado_idx is None and 'resultado_col' in st.session_state:
        resultado_idx = st.session_state.resultado_col
    
    # If still not found, can't update results
    if resultado_idx is None:
        st.error("Cannot find Resultado column to update results.")
        return df
    
    # Calculate total matches by result type
    locales_count = 0
    empates_count = 0
    visitas_count = 0
    
    # Update each row with match results
    for idx, row in df_updated.iterrows():
        if idx in match_results and match_results[idx]['result'] is not None:
            df_updated.iloc[idx, resultado_idx] = match_results[idx]['result']
            
            # Count result types
            result = match_results[idx]['result']
            if result == 'L':
                locales_count += 1
            elif result == 'E':
                empates_count += 1
            elif result == 'V':
                visitas_count += 1
    
    # Find summary rows by looking for keywords
    locales_row = None
    empates_row = None
    visitas_row = None
    aciertos_reg_row = None
    aciertos_rev_row = None
    
    for idx, row in df.iterrows():
        # Check the first cell for summary row identifiers
        first_cell = str(row.iloc[0]).lower() if not pd.isna(row.iloc[0]) else ''
        
        if '# locales' in first_cell or 'locales' in first_cell:
            locales_row = idx
        elif '# empates' in first_cell or 'empates' in first_cell:
            empates_row = idx
        elif '# visitas' in first_cell or 'visitas' in first_cell:
            visitas_row = idx
        elif 'aciertos regular' in first_cell or 'regular' in first_cell:
            aciertos_reg_row = idx
        elif 'aciertos revancha' in first_cell or 'revancha' in first_cell:
            aciertos_rev_row = idx
    
    # Update summary row values if found
    if locales_row is not None:
        df_updated.iloc[locales_row, 1] = locales_count  # Column B
        
    if empates_row is not None:
        df_updated.iloc[empates_row, 1] = empates_count  # Column B
        
    if visitas_row is not None:
        df_updated.iloc[visitas_row, 1] = visitas_count  # Column B
    
    # Calculate prediction accuracy if possible
    if aciertos_reg_row is not None or aciertos_rev_row is not None:
        # Get columns that look like prediction columns
        q_cols = {}
        for i, col in enumerate(df.columns):
            col_str = str(col).lower()
            if col_str.startswith('q-'):
                q_num = col_str.replace('q-', '')
                try:
                    q_num = int(q_num)
                    q_cols[q_num] = i
                except ValueError:
                    pass
            elif col_str in ['yo1', 'yo2', 'qpos', 'reyp', 'eq']:
                q_cols[col_str] = i
        
        # Calculate regular aciertos (Q-1 to Q-13)
        reg_aciertos = {}
        for q_num in range(1, 14):
            if q_num in q_cols:
                col_idx = q_cols[q_num]
                correct = 0
                
                for idx, row in df_updated.iterrows():
                    if idx in match_results and match_results[idx]['result'] is not None:
                        if row.iloc[col_idx] == match_results[idx]['result']:
                            correct += 1
                
                reg_aciertos[q_num] = correct
        
        # Calculate revancha aciertos (Q-14 to Q-20)
        rev_aciertos = {}
        for q_num in range(14, 21):
            if q_num in q_cols:
                col_idx = q_cols[q_num]
                correct = 0
                
                for idx, row in df_updated.iterrows():
                    if idx in match_results and match_results[idx]['result'] is not None:
                        if row.iloc[col_idx] == match_results[idx]['result']:
                            correct += 1
                
                rev_aciertos[q_num] = correct
        
        # Update aciertos rows
        if aciertos_reg_row is not None:
            for q_num, correct in reg_aciertos.items():
                col_idx = q_cols[q_num]
                df_updated.iloc[aciertos_reg_row, col_idx] = correct
        
        if aciertos_rev_row is not None:
            for q_num, correct in rev_aciertos.items():
                col_idx = q_cols[q_num]
                df_updated.iloc[aciertos_rev_row, col_idx] = correct
    
    return df_updated

# File uploader
uploaded_file = st.file_uploader("Upload your Quiniela CSV or Excel file", type=['csv', 'xlsx', 'xls'])

if uploaded_file:
    # Checkbox for header handling
    st.sidebar.markdown("## File Import Options")
    has_header = st.sidebar.checkbox("File has headers", value=True)
    
    # Read the file
    try:
        if uploaded_file.name.endswith('.csv'):
            # For CSV, explicitly handle headers
            df = pd.read_csv(uploaded_file, header=0 if has_header else None)
            if not has_header:
                # If no headers, create generic ones
                df.columns = [f'Column {i+1}' for i in range(len(df.columns))]
        else:
            df = pd.read_excel(uploaded_file, header=0 if has_header else None)
            if not has_header:
                # If no headers, create generic ones
                df.columns = [f'Column {i+1}' for i in range(len(df.columns))]
        
        # Display the original data
        st.subheader("Original Quiniela Data")
        st.dataframe(df)
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["Match Tracking", "Team Mappings", "Results Visualization", "Data Export"])
        
        with tab1:
            # Look for columns with match and date info
            partido_col = None
            fecha_col = None
            resultado_col = None
            
            # Try to identify the column names
            for i, col in enumerate(df.columns):
                col_str = str(col).lower()
                if 'partido' in col_str or ('vs' in col_str and col_str != 'visitas'):
                    partido_col = i
                elif 'fecha' in col_str or 'date' in col_str:
                    fecha_col = i
                elif 'resultado' in col_str or 'result' in col_str:
                    resultado_col = i
            
            # If partido column still not found, try to find one with "vs" in the values
            if partido_col is None:
                for i, col in enumerate(df.columns):
                    if df[col].astype(str).str.contains('vs').any():
                        partido_col = i
                        break
            
            # If Resultado column still not found, look for a column with L, E, V values
            if resultado_col is None:
                for i, col in enumerate(df.columns):
                    values = df[col].dropna().astype(str).unique()
                    # Check if most values are L, E, or V
                    lev_count = sum(1 for val in values if val in ['L', 'E', 'V'])
                    if lev_count >= len(values) / 2:  # If half or more values are L, E, or V
                        resultado_col = i
                        break
            
            # Allow user to select columns if not found or to override automatic detection
            st.subheader("Column Selection")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                partido_col = st.selectbox(
                    "Match Column", 
                    options=list(range(len(df.columns))),
                    format_func=lambda x: f"{x}: {df.columns[x]}",
                    index=partido_col if partido_col is not None else 0
                )
            
            with col2:
                fecha_col = st.selectbox(
                    "Date Column", 
                    options=list(range(len(df.columns))),
                    format_func=lambda x: f"{x}: {df.columns[x]}",
                    index=fecha_col if fecha_col is not None else 0
                )
            
            with col3:
                resultado_col = st.selectbox(
                    "Result Column", 
                    options=list(range(len(df.columns))),
                    format_func=lambda x: f"{x}: {df.columns[x]}",
                    index=resultado_col if resultado_col is not None else 0
                )
            
            # Store the selected column indices in session state
            st.session_state.partido_col = partido_col
            st.session_state.fecha_col = fecha_col
            st.session_state.resultado_col = resultado_col
            
            # Find rows with matches
            matches = []
            match_info = {}
            
            for idx, row in df.iterrows():
                # Skip rows that don't look like match rows or summary rows
                partido = str(row.iloc[partido_col])
                if 'vs' in partido and not any(keyword in str(row.iloc[0]).lower() for keyword in ['locales', 'empates', 'visitas', 'aciertos']):
                    # Extract teams
                    teams = partido.split('vs')
                    if len(teams) != 2:
                        continue
                        
                    home_team = teams[0].strip()
                    away_team = teams[1].strip()
                    
                    # Extract date if available
                    match_date = None
                    match_time = None
                    
                    if fecha_col is not None:
                        date_str = str(row.iloc[fecha_col])
                        match_date = parse_date(date_str)
                        match_time = extract_time(date_str)
                    
                    # Combine date and time if both are available
                    match_datetime = None
                    if match_date and match_time:
                        match_datetime = combine_date_time(match_date, match_time)
                    elif match_date:
                        match_datetime = match_date
                    
                    match_info[idx] = {
                        'partido': partido,
                        'home_team': home_team,
                        'away_team': away_team,
                        'date': match_datetime,
                        'sofascore_match': None,
                        'result': None,
                        'source': None
                    }
                    
                    matches.append((idx, home_team, away_team, match_datetime))
            
            # Display matches found
            st.subheader(f"Found {len(matches)} matches to track")
            
            if matches:
                # Date range selection
                st.subheader("Date Range Selection")
                st.write("Select the date range to search for matches:")
                
                # Find min and max dates from matches
                match_dates = [m[3] for m in matches if m[3] is not None]
                
                if match_dates:
                    min_date = min(match_dates).date()
                    max_date = max(match_dates).date()
                    
                    # Add buffer days
                    min_date = min_date - timedelta(days=2)
                    max_date = max_date + timedelta(days=2)
                else:
                    # Default to current week
                    today = datetime.now().date()
                    min_date = today - timedelta(days=today.weekday())
                    max_date = min_date + timedelta(days=6)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    start_date = st.date_input("Start Date", min_date)
                
                with col2:
                    end_date = st.date_input("End Date", max_date)
                
                # Convert to datetime for search
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                
                date_range = (start_datetime, end_datetime)
                
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
                        for i, (idx, home_team, away_team, match_datetime) in enumerate(matches):
                            status_text.text(f"Searching for {home_team} vs {away_team}...")
                            
                            # Find match in Sofascore
                            match, source = search_for_match(home_team, away_team, date_range)
                            
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
                        idx, home_team, away_team, _ = matches[selected_idx]
                    
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
            st.subheader("Team Name Mappings")
            st.write("These mappings help match team names between your Quiniela and Sofascore:")
            
            # Allow user to add new team mappings
            col1, col2, col3 = st.columns(3)
            
            with col1:
                team_a = st.text_input("Team Name in Quiniela", "")
            
            with col2:
                team_b = st.text_input("Team Name in Sofascore", "")
            
            with col3:
                if st.button("Add Mapping") and team_a and team_b:
                    # Add new mapping to session state
                    team_a = team_a.lower().strip()
                    team_b = team_b.lower().strip()
                    st.session_state.team_mappings[team_a] = team_b
                    st.success(f"Added mapping: {team_a} → {team_b}")
            
            # Display current mappings
            st.write("Current Team Mappings:")
            
            # Convert mappings to DataFrame for display
            mapping_data = []
            for key, value in st.session_state.team_mappings.items():
                mapping_data.append({"Team in Quiniela": key, "Team in Sofascore": value})
            
            mapping_df = pd.DataFrame(mapping_data)
            st.dataframe(mapping_df, use_container_width=True)
            
            # Button to clear all custom mappings
            if st.button("Reset to Default Mappings"):
                # Reset to default mappings
                st.session_state.team_mappings = {
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
                    'betis': 'real betis',
                    'villarreal': 'villarreal cf',
                    'osasuna': 'ca osasuna',
                    'girona': 'girona fc',
                    'h. kiel': 'holstein kiel',
                    'st. pauli': 'fc st pauli',
                    'verona': 'hellas verona',
                    'lazio': 'ss lazio',
                    'roma': 'as roma',
                    'genoa': 'genoa cfc',
                    'u de g': 'leones negros',
                    'celaya': 'club celaya',
                    'fem': 'women',
                    'st. louis': 'st. louis city',
                    'columbus': 'columbus crew'
                }
                st.success("Reset to default team mappings")
                st.experimental_rerun()
        
        with tab3:
            st.subheader("Results Visualization")
            
            if 'updated_df' in st.session_state:
                updated_df = st.session_state['updated_df']
                
                # Count results by type
                result_counts = {
                    "L (Local Win)": sum(1 for idx in st.session_state.match_info if st.session_state.match_info[idx]['result'] == 'L'),
                    "E (Draw)": sum(1 for idx in st.session_state.match_info if st.session_state.match_info[idx]['result'] == 'E'),
                    "V (Away Win)": sum(1 for idx in st.session_state.match_info if st.session_state.match_info[idx]['result'] == 'V'),
                    "Pending": len(matches) - sum(1 for idx in st.session_state.match_info if st.session_state.match_info[idx]['result'] in ['L', 'E', 'V'])
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
                prediction_cols = []
                for col in df.columns:
                    col_str = str(col).lower()
                    if col_str.startswith('q-') or col_str in ['yo1', 'yo2', 'qpos', 'reyp', 'eq']:
                        prediction_cols.append(col)
                
                if prediction_cols:
                    accuracy_data = []
                    
                    for col in prediction_cols:
                        correct = 0
                        total = 0
                        
                        for idx in st.session_state.match_info:
                            if st.session_state.match_info[idx]['result'] in ['L', 'E', 'V']:
                                total += 1
                                col_idx = df.columns.get_loc(col)
                                if idx < len(df) and df.iloc[idx, col_idx] == st.session_state.match_info[idx]['result']:
                                    correct += 1
                        
                        if total > 0:
                            accuracy = (correct / total) * 100
                            accuracy_data.append({"Column": str(col), "Accuracy (%)": accuracy})
                    
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
        
        with tab4:
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