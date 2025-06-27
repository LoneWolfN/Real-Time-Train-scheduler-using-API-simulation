from flask import Flask, jsonify, request
import pandas as pd
from datetime import datetime, timedelta
import random
import networkx as nx
import heapq
import threading

app = Flask(__name__)

# Load and preprocess dataset
DATA_PATH = "preprocessed_capstone_merged_train_data.csv"
df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=["train_number", "from_station_code", "to_station_code", "train_name_y", "arrival_time", "departure_time", "day", "total_duration_min"])
df['arrival_time'] = pd.to_datetime(df['arrival_time'], format='%H:%M:%S', errors='coerce').dt.time
df['departure_time'] = pd.to_datetime(df['departure_time'], format='%H:%M:%S', errors='coerce').dt.time

# Graph and delay containers
G = nx.DiGraph()
station_coords = df[['from_station_code', 'latitude', 'longitude']].drop_duplicates('from_station_code').set_index('from_station_code').to_dict('index')
train_timetables = {}
train_delays = {}
delays_per_station = {}

# Initialize timetables once
def build_timetables():
    for train_number, group in df.groupby("train_number"):
        timetable = []
        for _, row in group.iterrows():
            today = datetime.now().date()
            arrival_dt = datetime.combine(today + timedelta(days=int(row['day']) - 1), row['arrival_time'])
            departure_dt = datetime.combine(today + timedelta(days=int(row['day']) - 1), row['departure_time'])
            timetable.append({
                "station": row['from_station_code'],
                "arrival": arrival_dt,
                "departure": departure_dt,
                "train_name": row['train_name_y']
            })
        if len(timetable) >= 2:
            train_timetables[str(train_number)] = sorted(timetable, key=lambda x: x['arrival'])

# Dynamic updater
def update_delays_and_graph():
    global G, train_delays, delays_per_station
    train_delays = {str(train_id): random.randint(0, 30) for train_id in train_timetables.keys()}
    delays_per_station = {}
    G.clear()
    for _, row in df.iterrows():
        from_station = row['from_station_code']
        to_station = row['to_station_code']
        train_id = str(row['train_number'])
        delay = train_delays.get(train_id, 0)
        weight = float(row['total_duration_min']) + delay
        G.add_edge(from_station, to_station, weight=weight)
        delays_per_station[from_station] = delay

    # Schedule next run
    threading.Timer(300, update_delays_and_graph).start()

# Shortest path logic
# Dijkstra-based shortest path with delay consideration
def find_fastest_route(graph, delays, start, end):
    visited = set()
    queue = [(0, start, [])]
    while queue:
        current_time, station, path = heapq.heappop(queue)
        if station in visited:
            continue
        visited.add(station)
        path = path + [station]
        if station == end:
            return current_time, path
        for neighbor in graph.neighbors(station):
            edge_weight = graph[station][neighbor]['weight']
            delay = delays.get(station, 0)
            total_cost = current_time + edge_weight + delay
            heapq.heappush(queue, (total_cost, neighbor, path))
    return float('inf'), []

@app.route('/live/train/<train_id>', methods=['GET'])
def get_train_status(train_id):
    if train_id not in train_timetables:
        return jsonify({"error": "Train not found"}), 404
    now = datetime.now()
    delay = train_delays.get(train_id, 0)                            #Returns live status of all stations on the route of that train
    status_list = []
    for stop in train_timetables[train_id]:
        arrival = stop['arrival'] + timedelta(minutes=delay)
        departure = stop['departure'] + timedelta(minutes=delay)
        if now > departure:
            status = "Departed"
        elif arrival <= now <= departure:
            status = "At station"
        elif now < arrival:
            minutes_left = int((arrival - now).total_seconds() // 60)
            status = f"Expected in {minutes_left} min"
        else:
            status = "Unknown"
        status_list.append({
            "station": stop['station'],
            "arrival": arrival.strftime('%Y-%m-%d %H:%M'),
            "departure": departure.strftime('%Y-%m-%d %H:%M'),
            "status": status,
            "delay_min": delay
        })
    return jsonify({
        "train_number": train_id,
        "train_name": train_timetables[train_id][0]["train_name"],
        "route": status_list,
        "last_updated": now.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/live/station/<station_code>', methods=['GET'])
def get_station_status(station_code):
    now = datetime.now()
    station_summary = []                                                      #Loops through all train timetables and filters ones stopping at the station
    for train_id, timetable in train_timetables.items():
        for stop in timetable:
            if stop['station'] == station_code:
                delay = train_delays.get(train_id, 0)
                arrival = stop['arrival'] + timedelta(minutes=delay)
                departure = stop['departure'] + timedelta(minutes=delay)
                if now > departure:
                    status = "Departed"
                elif arrival <= now <= departure:
                    status = "At station"
                elif now < arrival:
                    minutes_left = int((arrival - now).total_seconds() // 60)
                    status = f"Expected in {minutes_left} min"
                else:
                    status = "Unknown"
                station_summary.append({
                    "train_number": train_id,
                    "train_name": stop['train_name'],
                    "arrival": arrival.strftime('%Y-%m-%d %H:%M'),
                    "departure": departure.strftime('%Y-%m-%d %H:%M'),
                    "delay_min": delay,
                    "status": status
                })
                break
    return jsonify({
        "station": station_code,
        "live_status": station_summary,
        "last_updated": now.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/live/all_trains', methods=['GET'])
def get_all_trains():
    summary = []                                         #Simple summary of all trains: number, name and list of stations in route
    for train_id, stops in train_timetables.items():
        summary.append({
            "train_number": train_id,
            "train_name": stops[0]["train_name"],
            "route": [s["station"] for s in stops]
        })
    return jsonify(summary)

@app.route('/live/route', methods=['GET'])
def get_optimized_route():
    source = request.args.get('source')
    destination = request.args.get('destination')                                    #Accepts source and destination via query params
    if not source or not destination:
        return jsonify({"error": "Source and destination are required"}), 400
    if source == destination:
        return jsonify({"error": "Source and destination cannot be the same"}), 400
    time, path = find_fastest_route(G, delays_per_station, source, destination)
    if time == float('inf'):
        return jsonify({"error": "No valid path found"}), 404
    return jsonify({
        "source": source,
        "destination": destination,
        "time_min": int(time),
        "route": path,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    build_timetables()
    update_delays_and_graph()
    app.run()