import requests
import os
from dotenv import load_dotenv

CARBON_API_BASE_URL = "https://www.carboninterface.com/api/v1"
load_dotenv()
API_KEY = os.environ.get("CARBON_INTERFACE_API_KEY")

# UDF to get vehicle make id for a specified make/brand
def get_vehicle_make_id (brand):
    url = f"{CARBON_API_BASE_URL}/vehicle_makes"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers).json()
    try:
        vehicle_make_id = [index["data"]["id"] for index in response if index["data"]["attributes"]["name"] == brand]
        return(vehicle_make_id[0])
    except:
        return "OOPS"

# UDF to get vehicle model id for a specified model and year given the make/brand
def get_vehicle_models_id(make_id, model_name, model_year):    
    model_url = f"{CARBON_API_BASE_URL}/vehicle_makes/{make_id}/vehicle_models"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        test = requests.get(model_url, headers=headers).json()
        model_id = [index["data"]["id"] for index in test if index["data"]["attributes"]["name"] == model_name and index["data"]["attributes"]["year"]== model_year]
        if model_id:
            return model_id[0]
        print(f"Error fetching data for ID {id}: {e}")
        return "OOPS"
    except Exception as e:
        print(f"Error fetching data for ID {id}: {e}")

# UDF to get emissions given the make/brand, model, year, distance and distance unit
def fetch_vehicle_emission(params):
    make_id = get_vehicle_make_id(params["vehicle_make"])

    mod_id = get_vehicle_models_id(make_id,params["vehicle_model"],int(params["year"]))

    data_url = f"{CARBON_API_BASE_URL}/estimates"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "type": "vehicle",
        "distance_unit": params["distance_unit"],
        "distance_value": float(params["distance_value"]),
        "vehicle_model_id": mod_id
    }

    response = requests.post(data_url, headers=headers, json=payload)
    return response