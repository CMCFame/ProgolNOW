import streamlit as st
import http.client
import json

# Set up the API endpoint and headers
API_HOST = "free-api-live-football-data.p.rapidapi.com"
API_ENDPOINT = "/football-current-live"

# Function to make API requests with debugging
def get_football_data():
    api_key = st.secrets.get("rapidapi", {}).get("api_key")
    if not api_key:
        st.error("API key not found in secrets.")
        return None

    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': API_HOST
    }

    st.write(f"Request Headers: {headers}")

    conn.request("GET", API_ENDPOINT, headers=headers)
    res = conn.getresponse()
    data = res.read()

    st.write(f"Response Status Code: {res.status}")
    st.write(f"Response Headers: {res.getheaders()}")
    st.write(f"Response Content: {data.decode('utf-8')}")

    if res.status == 200:
        return json.loads(data)
    else:
        st.error(f"Error: {res.status}")
        st.error(f"Response Text: {data.decode('utf-8')}")
        return None

# Streamlit app layout
st.title("Live Football Data App")

# Display live football data
st.header("Live Football Data")
data = get_football_data()
if data:
    st.write(json.dumps(data, indent=2))
