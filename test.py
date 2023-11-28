# import os
from flask import Flask, jsonify, request, render_template, redirect, url_for
import requests
import firebase_admin
from firebase_admin import credentials, firestore
# from support import get_vehicle_make_id, get_vehicle_models_id


app = Flask(__name__)

cred = credentials.Certificate("/") # your filestore private key location
firebase_admin.initialize_app(cred)

db = firestore.client()

CARBON_API_BASE_URL = "https://www.carboninterface.com/api/v1"
# API_KEY = os.environ.get("CARBON_API_KEY")

API_KEY = ''## your carbon interface token

# to serve the index.html form
@app.route('/')
def index():
    return render_template('index.html')


# Endpoint to fetch data from Carbon Interface API and display on HTML page
@app.route('/fetch_and_display', methods=['POST'])
def fetch_and_display():
    data_url = f"{CARBON_API_BASE_URL}/estimates"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # print("Form Data:", request.form)
    # input payload from the HTML form
    payload = {
        "type": "vehicle",
        "distance_unit": request.form["distance_unit"],
        "distance_value": int(request.form["distance_value"]),
        "vehicle_model_id": request.form["vehicle_model_id"]
    }
    # print("Payload:", payload)

    response = requests.post(data_url, headers=headers, json=payload)
    
    if response.status_code == 201:
        result = response.json()

        # Storing data in Firestore
        store_in_firestore(result)

        # updating the template of result.html with result
        return render_template('result.html', result=result)
    else:
        print("Error in API request:", response.status_code, response.text)
        return jsonify({"error": "Failed to fetch data from API"}), response.status_code

# Function to store data in Firestore
def store_in_firestore(result):
    # Adding 'results' collection in Firestore database
    results_ref = db.collection('results').document(result["data"]['attributes']['vehicle_model_id'])

    # transforming the data to store in dB
    # new document with the result data
    results_ref.set({
        'carbon_g': result['data']['attributes']['carbon_g'],
        'carbon_kg': result['data']['attributes']['carbon_kg'],
        'carbon_lb': result['data']['attributes']['carbon_lb'],
        'carbon_mt': result['data']['attributes']['carbon_mt'],
        'distance_unit': result['data']['attributes']['distance_unit'],
        'distance_value': result['data']['attributes']['distance_value'],
        'estimated_at': result['data']['attributes']['estimated_at'],
        'vehicle_make': result['data']['attributes']['vehicle_make'],
        'vehicle_model': result['data']['attributes']['vehicle_model'],
        'vehicle_model_id': result['data']['attributes']['vehicle_model_id'],
        'vehicle_year': result['data']['attributes']['vehicle_year'],
        
    })

@app.route('/alldetails', methods=['GET', 'POST'])
def alldetails():
    all_results = []

    if request.method == 'POST':
        # extract vehicle_model_id to be used as primary key
        vehicle_model_id = request.form['vehicle_model_id']

        if request.form.get('action') == 'View Data':
            # Fetching data for the specific vehicle_model_id when clicked on view details
            ids_list = vehicle_model_id.split(';')

            for vehicle_model_id in ids_list:
                result = db.collection('results').document(vehicle_model_id).get()

                if result.exists:
                    
                    all_results.append(result.to_dict())
                else:
                    # Data not found, add a message
                    all_results.append({'message': 'Record not found'})

        elif request.form.get('action') == 'Delete Data':
            # Add your logic for deleting data based on vehicle_model_id --- Ankur is working on it
            # ...

            # just written the structure
            results = db.collection('results').stream()

            # Creating a list to store the data for rendering in the template
            all_results = [result.to_dict() for result in results]
    

    return render_template('alldetails.html', all_results=all_results, show_message=bool(all_results))




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug =True)
