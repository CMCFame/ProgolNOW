import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import re
import base64
import io
import ScraperFC.sofascore as sfs
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(page_title="Quiniela Match Tracker", layout="wide", page_icon="⚽")

# Initialize Sofascore scraper
@st.cache_resource
def get_scraper():
    return sfs.Sofascore()

scraper = get_scraper()

# App title and description
st.title("⚽ Quiniela Match Tracker")
st.markdown("""
This app tracks the matches in your Quiniela spreadsheet and updates them with live results from Sofascore.
Upload your Quiniela CSV or Excel file to get started.
""")

# Helper functions
def parse_date_time(date_str, time_str):
    """Parse date and time strings into a datetime object."""
    if not date_str or not time_str:
        return None
    
    # Extract date parts (assuming MM/DD format)
    match = re.match(r'(\d+)/(\d+)', date_str)
    if not match:
        return None
    
    month, day = map(int, match.groups())
    
    # Get current year
    current_year = datetime.now().year
    
    # Extract time parts
    match = re.match(r'(\d+):(\d+)', time_str)
    if not match:
        return None
    
    hour, minute = map(int, match.groups())
    
    # Create datetime object
    try:
        dt = datetime(current_year, month, day, hour, minute)
        
        # If the date is in the past by more than 6 months, it's probably next year
        if (datetime.now() - dt).days > 180:
            dt = dt.replace(year=current_year + 1)
            
        return dt
    except ValueError:
        return None

def find_team_match(team_name):
    """Find a match in Sofascore based on team name."""
    # Try to find the most appropriate league based on the team name
    possible_leagues = determine_possible_leagues(team_name)
    
    # For each possible league, try to find matches
    for league_name in possible_leagues:
        if league_name not in scraper.comps:
            continue
            
        try:
            # Get the most recent season
            seasons = scraper.get_valid_seasons(league_name)
            if not seasons:
                continue
                
            latest_season = list(seasons.keys())[0]
            
            # Get matches for this league and season
            matches = scraper.get_match_dicts(latest_season, league_name)
            
            # Search for matches containing the team name
            for match in matches:
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                
                if similar_team_name(team_name, home_team) or similar_team_name(team_name, away_team):
                    return match
        except Exception as e:
            st.error(f"Error searching in {league_name}: {e}")
    
    return None

def similar_team_name(name1, name2):
    """Check if two team names are similar."""
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

def determine_possible_leagues(team_name):
    """Determine possible leagues based on team name."""
    team_name = team_name.lower()
    
    # Mexican teams
    if any(name in team_name for name in ['guadalajara', 'chivas', 'america', 'cruz azul', 'monterrey', 'tigres', 'pumas', 
                       'atlas', 'toluca', 'juarez', 'santos', 'pachuca', 'queretaro', 'mazatlan', 
                       'puebla', 'tijuana', 'necaxa', 'leon']):
        return ['Liga MX', 'MLS']
    
    # South American teams
    if any(name in team_name for name in ['flamengo', 'boca', 'river', 'palmeiras', 'santos', 'gremio', 'botafogo', 
                             'fluminense', 'corinthians', 'estudiantes', 'racing', 'nacional', 'penarol', 
                             'bragantino', 'millonarios', 'atletico nacional']):
        return ['Brazilian Serie A', 'Argentina Liga Profesional', 'Argentina Copa de la Liga Profesional', 'Copa Libertadores']
    
    # North American teams
    if any(name in team_name for name in ['miami', 'chicago', 'columbus', 'st. louis', 'atlanta', 'toronto', 'montreal']):
        return ['MLS', 'USL Championship']
    
    # Spanish teams
    if any(name in team_name for name in ['barcelona', 'madrid', 'atletico', 'sevilla', 'betis', 'villarreal', 'valencia']):
        return ['La Liga', 'Champions League', 'Europa League']
    
    # English teams
    if any(name in team_name for name in ['manchester', 'liverpool', 'chelsea', 'arsenal', 'tottenham', 'everton', 'leeds']):
        return ['EPL', 'Champions League', 'Europa League']
    
    # German teams
    if any(name in team_name for name in ['bayern', 'dortmund', 'leipzig', 'leverkusen', 'frankfurt', 'schalke', 'kiel', 'pauli']):
        return ['Bundesliga', 'Champions League', 'Europa League']
    
    # Italian teams
    if any(name in team_name for name in ['juventus', 'inter', 'milan', 'napoli', 'roma', 'lazio', 'genoa', 'verona']):
        return ['Serie A', 'Champions League', 'Europa League']
    
    # French teams
    if any(name in team_name for name in ['psg', 'paris', 'lyon', 'marseille', 'monaco', 'nice', 'strasbourg']):
        return ['Ligue 1', 'Champions League', 'Europa League']
    
    # Default to popular leagues
    return ['Liga MX', 'MLS', 'EPL', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1', 'Champions League']

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
        first_cell = str(row.iloc[0]).lower() if not pd.isna(row.iloc[0]) else ''
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

def find_both_teams_match(home_team, away_team):
    """Find a match with both specific teams."""
    # Try all possible leagues
    leagues_to_try = determine_possible_leagues(home_team)
    leagues_to_try.extend(determine_possible_leagues(away_team))
    leagues_to_try = list(set(leagues_to_try))  # Remove duplicates
    
    for league_name in leagues_to_try:
        if league_name not in scraper.comps:
            continue
            
        try:
            # Get the most recent season
            seasons = scraper.get_valid_seasons(league_name)
            if not seasons:
                continue
                
            latest_season = list(seasons.keys())[0]
            
            # Get matches for this league and season
            matches = scraper.get_match_dicts(latest_season, league_name)
            
            # Search for a match with both teams
            for match in matches:
                sofascore_home = match['homeTeam']['name']
                sofascore_away = match['awayTeam']['name']
                
                # Check if both teams match in correct order
                if similar_team_name(home_team, sofascore_home) and similar_team_name(away_team, sofascore_away):
                    return match, league_name
                
                # Check if teams match in reversed order
                if similar_team_name(home_team, sofascore_away) and similar_team_name(away_team, sofascore_home):
                    return match, league_name
                    
        except Exception as e:
            continue
    
    # If not found through league search, try searching for each team individually
    home_match = find_team_match(home_team)
    if home_match:
        sofascore_home = home_match['homeTeam']['name']
        sofascore_away = home_match['awayTeam']['name']
        
        if similar_team_name(away_team, sofascore_home) or similar_team_name(away_team, sofascore_away):
            return home_match, "Found via team search"
    
    away_match = find_team_match(away_team)
    if away_match:
        sofascore_home = away_match['homeTeam']['name']
        sofascore_away = away_match['awayTeam']['name']
        
        if similar_team_name(home_team, sofascore_home) or similar_team_name(home_team, sofascore_away):
            return away_match, "Found via team search"
    
    return None, None

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
        
        # Extract matches from the dataframe
        matches = []
        match_info = {}
        
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
            for idx, row in df.iterrows():
                # Skip rows that don't look like match rows or summary rows
                if not pd.isna(row[partido_col]) and isinstance(row[partido_col], str) and 'vs' in row[partido_col]:
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
                        'league': None
                    }
                    
                    matches.append((idx, home_team, away_team))
            
            # Display matches found
            st.subheader(f"Found {len(matches)} matches to track")
            
            if matches:
                # Track matches
                st.write("Click the button below to search for match results:")
                search_button = st.button("Find Match Results")
                
                if search_button:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Search for each match in Sofascore
                    match_results_table = []
                    
                    for i, (idx, home_team, away_team) in enumerate(matches):
                        status_text.text(f"Searching for {home_team} vs {away_team}...")
                        
                        # Find match in Sofascore
                        match, league = find_both_teams_match(home_team, away_team)
                        
                        if match:
                            # Verify it's the correct match
                            sofascore_home = match['homeTeam']['name']
                            sofascore_away = match['awayTeam']['name']
                            
                            # Store match details
                            match_info[idx]['sofascore_match'] = match
                            match_info[idx]['result'] = match_to_result_code(match)
                            match_info[idx]['league'] = league
                            
                            # Add to results table
                            status = match['status']['description']
                            score = f"{match['homeScore'].get('current', 0)} - {match['awayTeam'].get('current', 0)}"
                            result_code = match_info[idx]['result'] if match_info[idx]['result'] else "Pending"
                            
                            match_results_table.append({
                                "Match": f"{home_team} vs {away_team}",
                                "Sofascore Match": f"{sofascore_home} vs {sofascore_away}",
                                "League": league,
                                "Status": status,
                                "Score": score,
                                "Result": result_code
                            })
                            
                            status_text.text(f"✅ Found match: {sofascore_home} vs {sofascore_away}")
                        else:
                            # Not found
                            match_results_table.append({
                                "Match": f"{home_team} vs {away_team}",
                                "Sofascore Match": "Not found",
                                "League": "N/A",
                                "Status": "N/A",
                                "Score": "N/A",
                                "Result": "N/A"
                            })
                            
                            status_text.text(f"❌ Couldn't find match for {home_team} vs {away_team}")
                        
                        # Update progress
                        progress_bar.progress((i + 1) / len(matches))
                        time.sleep(0.2)  # Small delay to prevent API rate limiting
                    
                    status_text.text("Finished searching for matches")
                    
                    # Display match results
                    st.subheader("Match Results")
                    match_results_df = pd.DataFrame(match_results_table)
                    st.dataframe(match_results_df)
                    
                    # Update the Quiniela results
                    updated_df = update_quiniela_results(df, match_info)
                    
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
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload your Quiniela CSV or Excel file to get started.")

# Footer
st.markdown("---")
st.markdown("""
**About this app:**
- Built with Streamlit and ScraperFC
- Data source: Sofascore
- This app updates your Quiniela with live match results
""")