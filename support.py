import requests
import os
import concurrent.futures 

# UDF to get vehicle make id for a specified make/brand
def get_vehicle_make_id (CARBON_API_BASE_URL, API_KEY, brand):
    url = f"{CARBON_API_BASE_URL}/vehicle_makes"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers).json()

    vehicle_make_id = [index["data"]["id"] for index in response if index["data"]["attributes"]["name"] == brand]
    print("makeID:",vehicle_make_id[0])
    return(vehicle_make_id[0])

# UDF to get vehicle model id for a specified model and year given the make/brand
def get_vehicle_models_id(CARBON_API_BASE_URL,API_KEY,make_id, model_name, model_year):    
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
    except Exception as e:
        print(f"Error fetching data for ID {id}: {e}")
    
    return("ZZ") # error out

# UDF to fetch each vehicle model id concurrently
def fetch_data(CARBON_API_BASE_URL, vehicle_make_id, API_KEY):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures =[]
        responses =[]
        
        for ids in vehicle_make_id:
            futures.append(executor.submit(get_vehicle_models_id, CARBON_API_BASE_URL, ids, API_KEY))
        # flatten the result
        for future in concurrent.futures.as_completed(futures):
            response = future.result()
            
            responses.extend(response)

    return responses