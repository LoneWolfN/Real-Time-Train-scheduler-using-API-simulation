import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from itertools import islice
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Optimized Route Viewer", layout="wide")

API_URL = "http://localhost:5000"

st.sidebar.title("📘 Navigation")
tabs = st.sidebar.radio("Go to:", ["🚦 Dashboard", "📊 Statistical Dashboard", "🧑‍🤝‍🧑 Team Contributions"])

if tabs == "🚦 Dashboard":
    st.markdown("<h2 style='text-align: left;'>🚦 Train Route Intelligence Dashboard</h2>", unsafe_allow_html=True)

    station_df = pd.read_csv("preprocessed_capstone_merged_train_data.csv")
    station_df = station_df.dropna(subset=["from_station_code", "from_station_name", "latitude", "longitude"])
    station_df = station_df.drop_duplicates(subset=["from_station_code"])
    station_map = station_df.set_index("from_station_code").to_dict("index")
    station_code_to_name = station_df.set_index("from_station_code")["from_station_name"].to_dict()
    station_name_to_code = station_df.set_index("from_station_name")["from_station_code"].to_dict()
    station_code_list = sorted(station_code_to_name.keys())
    station_name_list = sorted(station_name_to_code.keys())

    if "route_result" not in st.session_state:
        st.session_state.route_result = None

    with st.container():
        st.markdown("<h4 style='margin-bottom: 5px;'>🧭 Select View Mode</h4>", unsafe_allow_html=True)
        view_option = st.radio("", ["🔎 Station Live Status", "🚄 Optimized Path Finder"])

    st.markdown("<hr style='margin-top: 5px; margin-bottom: 10px;'>", unsafe_allow_html=True)

    if view_option == "🔎 Station Live Status":
        search_mode_station = st.radio("Search by:", ["Station Name", "Station Code"], horizontal=True)

        if search_mode_station == "Station Name":
            selected_station_name = st.selectbox("Select Station Name", station_name_list)
            selected_station = station_name_to_code[selected_station_name]
        else:
            selected_station = st.selectbox("Select Station Code", station_code_list)
            selected_station_name = station_code_to_name.get(selected_station, "Unknown")

        if selected_station:
            response = requests.get(f"{API_URL}/live/station/{selected_station}")
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data["live_status"])
                st.markdown(f"<h5 style='margin-top: 10px;'>📍 Live Train Activity for {selected_station_name}</h5>", unsafe_allow_html=True)
                if not df.empty:
                    def highlight(row):
                        if row['status'] == "Departed": return ['background-color: gray'] * len(row)
                        elif row['status'] == "At station": return ['background-color: blue'] * len(row)
                        elif "Expected in" in row['status']: return ['background-color: yellow'] * len(row)
                        return [''] * len(row)
                    st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)
                else:
                    st.warning("No active train data found for this station.")
            else:
                st.error("API failed to return station data.")
    elif view_option == "🚄 Optimized Path Finder":
        st.markdown("<h4 style='margin-bottom: 5px;'>🔍 Route Search Preferences</h4>", unsafe_allow_html=True)
        search_mode = st.radio("Search by:", ["Station Name", "Station Code"])

        if search_mode == "Station Name":
            col1, col2 = st.columns(2)
            with col1:
                source_name = st.selectbox("Select Source Station Name", station_name_list)
            with col2:
                destination_name = st.selectbox("Select Destination Station Name", station_name_list)
            source = station_name_to_code[source_name]
            destination = station_name_to_code[destination_name]
        else:
            col1, col2 = st.columns(2)
            with col1:
                source = st.selectbox("Select Source Station Code", station_code_list)
            with col2:
                destination = st.selectbox("Select Destination Station Code", station_code_list)
            source_name = station_code_to_name.get(source, source)
            destination_name = station_code_to_name.get(destination, destination)

        if source != destination and st.button("🔍 Find Best Route"):
            response = requests.get(f"{API_URL}/live/route?source={source}&destination={destination}&alternates=3")
            if response.status_code == 200:
                st.session_state.route_result = response.json()
            else:
                st.session_state.route_result = {"error": "No route found"}

        data = st.session_state.route_result
        if data:
            if 'error' not in data:
                st.success(f"Fastest route from {source_name} to {destination_name} takes {data['time_min']} mins")
                st.markdown("### 🚄 Primary Route:")
                st.write(" ➝ ".join([f"{code} ({station_code_to_name.get(code, '')})" for code in data['route']]))

                m = folium.Map(location=[22.3511, 78.6677], zoom_start=5)
                coords = [[station_map[st]['latitude'], station_map[st]['longitude']] for st in data['route'] if st in station_map]
                for stn in data['route']:
                    if stn in station_map:
                        folium.CircleMarker(
                            location=[station_map[stn]['latitude'], station_map[stn]['longitude']],
                            radius=6,
                            color="blue",
                            fill=True,
                            fill_opacity=0.8,
                            popup=f"{stn} - {station_code_to_name.get(stn, '')}"
                        ).add_to(m)
                folium.PolyLine(coords, color="blue", weight=3, opacity=0.6).add_to(m)

                if 'alternate_routes' in data:
                    st.markdown("### 🛤 Alternate Suggestions:")
                    for i, alt in enumerate(islice(data['alternate_routes'], 3), start=1):
                        st.info(f"Alt #{i}: {' ➝ '.join(alt['path'])} (ETA: {alt['time']} min)")
                        coords_alt = [[station_map[st]['latitude'], station_map[st]['longitude']] for st in alt['path'] if st in station_map]
                        folium.PolyLine(coords_alt, color="orange", weight=2, opacity=0.4).add_to(m)

                st.subheader("Optimized Route Map")
                st_folium(m, width=1000, height=600)
                st.caption(f"Generated at {data['timestamp']}")
            else:
                st.error("No route found or error occurred.")
        elif source == destination:
            st.info("Please choose different source and destination.")


elif tabs == "🧑‍🤝‍🧑 Team Contributions":
    st.markdown("""
     ### 👨‍💻 Member 1- Mohammed Naqeeb – Data & Backend
    - Cleaned and preprocessed the gathered data
    - Designed the graph structure and implemented delay propagation
    - Built the project report along with new features that can be added with real-time implementation

    ### 🧑‍🔬 Member 2 - Syed Sami Ahmed – Enhancement & Intelligence
    - Implemented advanced features like alternate route suggestion and session-state handling
    - Added modular UI design, separation of logic, and optimized performance with caching
    - Suggested enhancements like heatmap, dashboard stats, and improved quality of life features during dashboard use

    ### 🧑‍🎓 Member 3 - Naethen Luke Kanichaatil – API and UI implementation
    - Designed and structured the Streamlit dashboard and flast API for simulating real time train delay data
    - Integrated real-time route and alternate path visualizations
    - Created live station table with status-based color coding and delay logic

    ### 🧩 Additional Notes
    - Dataset used: Preprocessed Indian Train Schedule (capstone merged)
    - Libraries: streamlit, folium, networkx, flask, pandas
    - Future work includes API integration with live data from IRCTC (mocked now for simulation)
    """, unsafe_allow_html=True)

elif tabs == "📊 Statistical Dashboard":
    st.markdown("<h2 style='text-align: left;'>📊 Railway Data Statistics</h2>", unsafe_allow_html=True)

    try:
        update_response = requests.get(f"{API_URL}/live/last_update")
        if update_response.status_code == 200:
            last_update = update_response.json().get("last_updated")
            st.markdown(f"**Last Graph Update:** ⏱ {last_update}")
    except:
        st.warning("Could not retrieve last update time from backend.")

    df = pd.read_csv("preprocessed_capstone_merged_train_data.csv")
    df = df.dropna(subset=['from_station_code', 'to_station_code', 'total_duration_min'])

    st.markdown("### 🚉 Top 10 Busiest Departure Stations")
    top_stations = df['from_station_code'].value_counts().head(10)
    fig1, ax1 = plt.subplots()
    sns.barplot(x=top_stations.values, y=top_stations.index, ax=ax1)
    ax1.set_xlabel("Number of Departures")
    ax1.set_ylabel("Station Code")
    st.pyplot(fig1)

    st.markdown("### ⏱ Average Travel Duration by Train Type")
    if 'train_type' in df.columns:
        avg_duration = df.groupby('train_type')['total_duration_min'].mean().sort_values(ascending=False).dropna()
        fig2, ax2 = plt.subplots()
        sns.barplot(x=avg_duration.values, y=avg_duration.index, palette='crest', ax=ax2)
        ax2.set_xlabel("Average Duration (min)")
        ax2.set_ylabel("Train Type")
        st.pyplot(fig2)
    else:
        st.warning("Train type data not available in dataset.")

    st.markdown("### 🔁 Duration Distribution")
    fig3, ax3 = plt.subplots()
    sns.histplot(df['total_duration_min'], bins=50, kde=True, ax=ax3)
    ax3.set_title("Distribution of Travel Times")
    ax3.set_xlabel("Total Duration (min)")
    st.pyplot(fig3)

    st.markdown("### 🚉 In-Degree vs Out-Degree of Stations")
    station_counts = pd.concat([
        df['from_station_code'].value_counts(),
        df['to_station_code'].value_counts()
    ], axis=1, keys=['Departures', 'Arrivals']).fillna(0).astype(int)
    station_counts['Total'] = station_counts.sum(axis=1)
    top_degree = station_counts.sort_values(by='Total', ascending=False).head(10)
    fig4, ax4 = plt.subplots()
    top_degree[['Departures', 'Arrivals']].plot(kind='barh', stacked=True, ax=ax4)
    ax4.set_title("Top Stations by Connectivity")
    ax4.set_xlabel("Number of Trains")
    st.pyplot(fig4)
