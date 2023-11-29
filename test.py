import os
from flask import Flask, jsonify, request, render_template, redirect, url_for
import re
import firebase_admin
from firebase_admin import credentials, firestore
from support import get_vehicle_make_id, get_vehicle_models_id, fetch_vehicle_emission

app = Flask(__name__)

# Makes it a little slower when running locally
r = re.compile(".*firebase*") 
# locates the first filestore private key location in root
firebase_cred_file = list(filter(r.match, os.listdir(os.getcwd())))[0]
cred = credentials.Certificate(f"{str(os.getcwd())}\\{firebase_cred_file}")
firebase_admin.initialize_app(cred)

db = firestore.client()

# to serve the index.html form
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint to fetch data from Carbon Interface API and display on HTML page
@app.route('/fetch_and_display', methods=['POST'])
def fetch_and_display():

    emission_response = fetch_vehicle_emission(request.form)

    if not emission_response.ok:
        print("Error in API request:", emission_response.status_code, emission_response.text)
        return jsonify({"error": "Failed to fetch data from API"}), emission_response.status_code
    
    result = emission_response.json()
    # Storing data in Firestore
    store_in_firestore(result, request.form["customer_name"])

    # updating the template of result.html with result
    return render_template('result.html', result=result)

# Function to store data in Firestore
def store_in_firestore(result, cust_name):
    # Adding 'results' collection in Firestore database
    results_ref = db.collection('results').document(cust_name)

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
