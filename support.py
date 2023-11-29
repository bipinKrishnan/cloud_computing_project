import requests
import os
import concurrent.futures 

# UDF to get vehicle make id
def get_vehicle_make_id (CARBON_API_BASE_URL, API_KEY):

    url = f"{CARBON_API_BASE_URL}/vehicle_makes"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers).json()

    vehicle_make_id = [index["data"]["id"] for index in response]

    return(vehicle_make_id)

# UDF to get vehicle model id for each vehicle make id
def get_vehicle_models_id(CARBON_API_BASE_URL, ids, API_KEY):
    vehicle_models = []
    
    model_url = f"{CARBON_API_BASE_URL}/vehicle_makes/{ids}/vehicle_models"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        test = requests.get(model_url, headers=headers).json()
        for i in test:
            result= {
                'id':i["data"]["id"],
                'vehicle_model':i["data"]["attributes"]["name"],
                'vehicle_make':i["data"]["attributes"]["vehicle_make"]
                }
            vehicle_models.append(result)
    except Exception as e:
        print(f"Error fetching data for ID {id}: {e}")
    
    return(vehicle_models)

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