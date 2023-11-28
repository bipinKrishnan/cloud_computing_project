import requests
from concurrent.futures import ThreadPoolExecutor

def get_vehicle_make_id (CARBON_API_BASE_URL, API_KEY):

    url = f"{CARBON_API_BASE_URL}/vehicle_makes"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers).json()

    vehicle_make_id = [index["data"]["id"] for index in response]

    return(vehicle_make_id)


def get_vehicle_models_id(CARBON_API_BASE_URL, vehicle_make_id, API_KEY):

    vehicle_models = []
    for id in vehicle_make_id:
        model_url = f"{CARBON_API_BASE_URL}/vehicle_makes/{id}/vehicle_models"
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
                    'vehicle_make':i["data"]["attributes"]["vehicle_make"]}
                vehicle_models.append(result)
        except Exception as e:
            print(f"Error fetching data for ID {id}: {e}")
    
    return(vehicle_models)

def fetch_data(CARBON_API_BASE_URL, vehicle_make_id, API_KEY):
    with ThreadPoolExecutor(max_workers=10) as executor:
        
        result = list(executor.map(get_vehicle_models_id,CARBON_API_BASE_URL, vehicle_make_id, API_KEY))

        result = [model for sublist in result for model in sublist]
    return result