#%%
"""
Use this script to update the latitude/longitude and GeoJSON data for the countries in WB and MVC datasets.
You may need to manually add some countries to the coordinates/feature dictionary if they are not found by the geocoder.
"""
from geopy.geocoders import Nominatim
import pandas as pd
import os
import pickle
import requests
import time

GEOLOCATOR = Nominatim(user_agent="geo_lookup")

# Names used by the World Bank that the geocoder does not find or finds in the wrong place: search for another name instead.
# "Taiwan, China" was found in Fujian (mainland China) and "Washington" in Washington DC (the instrument is the state's);
# if a name here is already in the local cache with the wrong place, delete it from coords.pkl so it is searched again.
BUSCA_ALTERNATIVA = {"EU27+": "EU", "Taiwan, China": "Taiwan", "Washington": "Washington State"}

# Jurisdictions that are not a single place: fixed point, not geocoded.
# RGGI: simple mean of the coordinates of the 10 participating states, as listed by the World Bank file
# (data/raw/dados_wb.xlsx, edition May 2026, sheet Compliance_Gen Info, RGGI, columns Description and Recent developments:
# Connecticut, Delaware, Maine, Maryland, Massachusetts, New Hampshire, New Jersey, New York, Rhode Island and Vermont;
# Virginia left in December 2023 and Pennsylvania withdrew in November 2025). Coordinates of each state from
# Nominatim/OpenStreetMap ("<state>, United States", featuretype="state"), searched on 01/10/2026:
# CT (41.6500, -72.7342), DE (38.6920, -75.4013), ME (45.7091, -68.8590), MD (39.5162, -76.9382),
# MA (42.3789, -72.0324), NH (43.4849, -71.6554), NJ (40.0757, -74.4042), NY (43.1562, -75.8450),
# RI (41.7962, -71.5992), VT (44.5991, -72.5003).
COORDENADAS_FIXAS = {"RGGI": (42.1058, -73.1969)}

def get_lat_long(locations):
    """
    Get latitude and longitude for a list of locations using Nominatim geocoder.
    
    Args:
        locations (list): List of location names (e.g., countries, cities).

    Returns:
        dict: A dictionary with location names as keys and their corresponding latitude and longitude as values.
    """

    # Load the coordinates dictionary if it exists (it is a local cache, not versioned)
    if os.path.exists('data/processed/coords.pkl'):
        with open('data/processed/coords.pkl', 'rb') as f:
            coords = pickle.load(f)
    else:
        coords = {}

    # Check if the coordinates for the locations are already in the dictionary
    missing_coords = [place for place in locations if place not in coords]

    if len(missing_coords):
        print("Searching coordinates for:", missing_coords)
        new_coords = {}
        for place in missing_coords:
            new_coords[place] = GEOLOCATOR.geocode(BUSCA_ALTERNATIVA.get(place, place))
            time.sleep(1.1)  # Nominatim usage policy: at most 1 request per second

        coords.update(new_coords)

        # Lines to specific locations manually
        # coords.update({'Korea, Rep.':GEOLOCATOR.geocode('korea republic')})
        # coords.update({'Guangdong (except Shenzhen)':GEOLOCATOR.geocode('Guangdong')})

        missing_coords = [place for place in locations if place not in coords]
        print("The following locations could not be found:",missing_coords)

        with open('data/processed/coords.pkl', 'wb') as f:
            pickle.dump(coords, f)

    return coords


def get_geo_json(place_name):
    """
    Fetch the GeoJSON boundary for a given place (country, city, or region) using OpenStreetMap's Nominatim API.
    
    Args:
        place_name (str): The name of the place (e.g., "Brazil", "Paris", "California").
        
    Returns:
        dict: The GeoJSON data for the place.
    """

    url = f"https://nominatim.openstreetmap.org/search?format=json&polygon_geojson=1&q={place_name}"
    response = requests.get(url, headers={'User-Agent': 'geojson-fetcher'})
    
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code}")
    
    data = response.json()
    
    if not data:
        raise ValueError("No data found for the given place name.")
    
    return data[0]['geojson']


def get_geojson(locations,search_names=None):
    """
    Get GeoJSON data for a list of locations using OpenStreetMap's Nominatim API.
    
    Args:
        locations (list): List of location names (e.g., countries, cities).
        search_names (list): Optional list of search names to use instead of locations.
        
    Returns:
        list: A list of GeoJSON features for the locations."""

    features = []

    for cur_id, cur_location in enumerate(locations):

        # Get the GeoJSON for the current location
        try:
            cur_search = search_names[cur_id] if search_names else cur_location
            geometry = get_geo_json(cur_search)

        except Exception as e:
            print(f"Error fetching GeoJSON for {cur_location}: {e}")
            continue

        features.append({'type': 'Feature',
            'geometry': geometry,
            'properties': {"Jurisdiction covered": cur_location, "Country": cur_location},
            'id': cur_id})

    return features


def update_geojson(locations):
    """
    Update the GeoJSON data for a list of locations.
    """

    # Load the coordinates dictionary if it exists
    with open('data/processed/geojson.pkl', 'rb') as f:
        features_list = pickle.load(f)

    missing_features = [i for i in locations if i not in [i['properties']['Country'] for i in features_list]]
    
    if len(missing_features):
        print("Searching for new features:", missing_features)
        new_features = get_geojson(missing_features)

        #use this to add specific locations
        # new_features = get_geojson(locations = ['Guangdong (except Shenzhen)', 'Korea, Rep.'],
        #                               search_names = ['Guangdong',  'Republic of Korea'])

        if len(new_features):

            features_list+=new_features

            with open('data/processed/geojson.pkl', 'wb') as f:
                pickle.dump(features_list, f)
                
        still_missing = [i for i in missing_features if i not in [i['properties']['Country'] for i in new_features]]
        print("Still missing features:", still_missing)



def update_location_data():
    """
    Update WB and MCV datasets with latitude, longitude, and GeoJSON data.
    This function reads the datasets, fetches the required data, and updates the datasets.
    """

    def update_coords(locations):

        # Add latitude column using coords dictionary
        coords = get_lat_long(locations - set(COORDENADAS_FIXAS))

        def lat_lon(place, i):
            if place in COORDENADAS_FIXAS:
                return COORDENADAS_FIXAS[place][i]
            if not coords[place]:
                return None
            return coords[place].latitude if i == 0 else coords[place].longitude

        data_wb['lat'] = data_wb['Jurisdiction covered'].map(lambda x: lat_lon(x, 0))
        data_wb['lon'] = data_wb['Jurisdiction covered'].map(lambda x: lat_lon(x, 1))

        mvc['lat'] = mvc['Country'].map(lambda x: coords[x].latitude if coords[x] else None)
        mvc['lon'] = mvc['Country'].map(lambda x: coords[x].longitude if coords[x] else None)

        data_wb.to_csv("data/processed/wb_info.csv", sep=";", decimal=",", index=False)
        mvc.to_csv("data/processed/mvc_credits_info.csv", sep=";", decimal=",", index=False)
        

    data_wb = pd.read_csv("data/processed/wb_info.csv",sep=";",decimal=",")
    mvc = pd.read_csv("data/processed/mvc_credits_info.csv",sep=";",decimal=",")
    locations = set(data_wb["Jurisdiction covered"].unique()).union(set(mvc["Country"].unique()))

    update_coords(locations)
    # update_geojson(locations)  # the GeoJSON cache is not used by the current pages

    print("Data updated successfully!")


if __name__ == "__main__":
    update_location_data()
