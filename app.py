import streamlit as st
import requests

# Set up the API endpoint
API_ENDPOINT = "https://api-football-v1.p.rapidapi.com/v3/"

# Function to make API requests with debugging
def get_football_data(endpoint):
    api_key = st.secrets.get("rapidapi", {}).get("api_key")
    if not api_key:
        st.error("API key not found in secrets.")
        return None

    url = API_ENDPOINT + endpoint
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    st.write(f"Request URL: {url}")
    st.write(f"Request Headers: {headers}")

    response = requests.get(url, headers=headers)
    st.write(f"Response Status Code: {response.status_code}")
    st.write(f"Response Headers: {response.headers}")
    st.write(f"Response Content: {response.content}")

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code}")
        st.error(f"Response Text: {response.text}")
        return None

# Streamlit app layout
st.title("Live Football Data App")

# Sidebar for navigation
st.sidebar.title("Navigation")
options = ["Live Scores", "Fixtures", "Standings", "Teams", "Players"]
choice = st.sidebar.selectbox("Select an option", options)

# Display data based on the selected option
if choice == "Live Scores":
    st.header("Live Scores")
    data = get_football_data("fixtures?live=all")
    if data:
        for match in data['response']:
            st.write(f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}")
            st.write(f"Score: {match['goals']['home']} - {match['goals']['away']}")
            st.write(f"Status: {match['fixture']['status']['long']}")
            st.write("---")

elif choice == "Fixtures":
    st.header("Fixtures")
    data = get_football_data("fixtures")
    if data:
        for match in data['response']:
            st.write(f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}")
            st.write(f"Date: {match['fixture']['date']}")
            st.write("---")

elif choice == "Standings":
    st.header("Standings")
    league_id = st.text_input("Enter League ID", "39")  # Default to Premier League
    data = get_football_data(f"standings?season=2023&league={league_id}")
    if data:
        for standing in data['response'][0]['league']['standings'][0]:
            st.write(f"{standing['rank']}. {standing['team']['name']} - {standing['points']} points")

elif choice == "Teams":
    st.header("Teams")
    league_id = st.text_input("Enter League ID", "39")  # Default to Premier League
    data = get_football_data(f"teams?league={league_id}&season=2023")
    if data:
        for team in data['response']:
            st.write(f"{team['team']['name']} - {team['team']['country']}")

elif choice == "Players":
    st.header("Players")
    team_id = st.text_input("Enter Team ID", "33")  # Default to Manchester United
    data = get_football_data(f"players?team={team_id}&season=2023")
    if data:
        for player in data['response']:
            st.write(f"{player['player']['name']} - {player['statistics'][0]['team']['name']}")