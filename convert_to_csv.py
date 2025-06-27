import json
import pandas as pd

#Converting stations json file to csv
with open("dataset_2\stations.json", "r", encoding="utf-8") as f:
    stations_data = json.load(f)

stations_list = []
for station in stations_data["features"]:
    properties = station["properties"]
    geometry = station["geometry"]
    
    coordinates = geometry["coordinates"] if geometry else [None, None]
    stations_list.append({
        "station_code": properties.get("code", None),
        "station_name": properties.get("name", None),
        "state": properties.get("state", None),
        "zone": properties.get("zone", None),
        "latitude": coordinates[1],
        "longitude": coordinates[0],
        "address": properties.get("address", None)
    })
df_stations = pd.DataFrame(stations_list)
df_stations.to_csv("dataset_2\csv_format\stations.csv", index=False, encoding="utf-8")

#Converting trains json file to csv
filepath = r"C:\Users\samia\OneDrive\Documents\capstone_project\dataset_2\trains.json"

with open(filepath, "r", encoding="utf-8") as f:
    trains_data = json.load(f)

trains_list = []
for train in trains_data["features"]:
    properties = train["properties"]
    trains_list.append({
        "train_number": properties.get("number", None),
        "train_name": properties.get("name", None),
        "train_type": properties.get("type", None),
        "zone": properties.get("zone", None),
        "departure_time": properties.get("departure", None),                                #converting json files to dataframe/csv using pandas 
        "arrival_time": properties.get("arrival", None),                                    #it iterates through the json files and keeps adding 
        "duration_h": properties.get("duration_h", None),                                   #the flattened featured identified to a list of dictionaries
        "duration_m": properties.get("duration_m", None),                                   #which then is finally converted to a csv file
        "distance_km": properties.get("distance", None),
        "from_station_code": properties.get("from_station_code", None),
        "from_station_name": properties.get("from_station_name", None),
        "to_station_code": properties.get("to_station_code", None),
        "to_station_name": properties.get("to_station_name", None),
        "return_train": properties.get("return_train", None),
        "first_ac": properties.get("first_ac", 0),
        "second_ac": properties.get("second_ac", 0),
        "third_ac": properties.get("third_ac", 0),
        "sleeper": properties.get("sleeper", 0),
        "chair_car": properties.get("chair_car", 0),
        "first_class": properties.get("first_class", 0),
        "classes_available": properties.get("classes", None)
    })
df_trains = pd.DataFrame(trains_list)
df_trains.to_csv("trains.csv", index=False, encoding="utf-8")

#Merging the now converted stations and trains csv file with already existing schedules csv file
fp1 = r"C:\Users\samia\OneDrive\Documents\capstone_project\dataset_2\csv_format\schedules.csv"
fp2 = r"C:\Users\samia\OneDrive\Documents\capstone_project\dataset_2\csv_format\stations.csv"
fp3 = r"C:\Users\samia\OneDrive\Documents\capstone_project\dataset_2\csv_format\trains.csv"
df_schedules = pd.read_csv(fp1)
df_stations = pd.read_csv(fp2)
df_trains = pd.read_csv(fp3)

df_merged = df_schedules.merge(df_trains, on="train_number", how="left")
df_merged = df_merged.merge(df_stations, on="station_code", how="left")

df_merged.to_csv("merged_train_data.csv", index=False, encoding="utf-8")

print("merged")

#Rest of Preprocessing
fp = r"C:\Users\samia\OneDrive\Documents\capstone_project\merged_train_data.csv"
df = pd.read_csv(fp)
df.head()

print("Shape of the dataset:", df.shape)

print("Missing values in each column:")
print(df.isnull().sum())

df_cleaned = df.dropna(subset=["arrival"])

rows_dropped = len(df) - len(df_cleaned)
print(f"Rows dropped: {rows_dropped}")

df_cleaned = df_cleaned.dropna(subset=["return_train"])
df_cleaned = df_cleaned[df_cleaned["return_train"].astype(str).str.isnumeric()]

rows_dropped = len(df) - len(df_cleaned)
print(f"Rows dropped: {rows_dropped}")

drop_columns = ["departure", "station_code", "station_name_x", "train_name_x", "station_name_y", "state", "address", "classes_available", "zone_x", "zone_y"]
df_cleaned = df_cleaned.drop(columns=drop_columns, errors='ignore')

df_cleaned["total_duration_min"] = df_cleaned["duration_h"] * 60 + df_cleaned["duration_m"]

df_cleaned[['duration_h', 'duration_m', 'total_duration_min']].head()

df_cleaned.to_csv('preprocessed_capstone_merged_train_data.csv', index=False)