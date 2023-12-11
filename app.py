import os
from flask import Flask, jsonify, request, render_template, redirect, url_for
import re
import firebase_admin
from firebase_admin import credentials, firestore
from support import fetch_vehicle_emission
from plotly.subplots import make_subplots
import plotly.graph_objects as go

app = Flask(__name__)

# Makes it a little slower when running locally
r = re.compile(".*firebase*") 
# locates the first filestore private key location in root
firebase_cred_file = list(filter(r.match, os.listdir(os.getcwd())))[0]
cred = credentials.Certificate(os.path.join(os.getcwd(), firebase_cred_file))
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
        return render_template('result.html', result="", user_name=""), emission_response.status_code
    
    result = emission_response.json()
    # Storing data in Firestore
    store_in_firestore(result, request.form["customer_name"])
    result = result["data"]["attributes"]
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

@app.route('/fetch_landing', methods=['GET'])
def fetch_land():
    return render_template("fetch_landing.html")

@app.route('/result', methods=['POST'])
def result():

    result = db.collection('results').document(request.form["user_name"]).get()
    if result.exists:
        result = result.to_dict()
    else:
        # Data not found, add a message
        result = ""
    print(result)
    return render_template('result.html', result=result, user_name=request.form["user_name"])

@app.route('/del_landing', methods=['GET'])
def del_land():
    return render_template("delete_landing.html")

@app.route('/delete', methods=['POST'])
def delete_emission():
    fetch = db.collection('results').document(request.form["user_name"]).get()
    db.collection('results').document(request.form["user_name"]).delete()

    return render_template('delete.html', user_name=request.form["user_name"], removed=fetch.exists )


# Route to view plots
@app.route('/view_plots', methods=['GET'])
def view_plots():
    # Retrieve data from Firestore
    results = db.collection('results').stream()
    data = [result.to_dict() for result in results]

    # Check if data is empty
    if not data:
        # Render a template with a message for no data found
        return render_template('no_data_found.html')

    # Extract data for plotting
    carbon_kg = [entry.get('carbon_kg', 0) for entry in data]
    carbon_mt = [entry.get('carbon_mt', 0) for entry in data]
    vehicle_make = [entry.get('vehicle_make', 'Unknown') for entry in data]
    carbon_g = [entry.get('carbon_g', 0) for entry in data]

    # Create a subplot with two scatter plots and one bar chart
    fig = make_subplots(rows=1, cols=3, subplot_titles=['Carbon (kg)', 'Carbon (metric tons)', 'Carbon (grams)'])

    # Add bar chart for carbon_g
    fig.add_trace(go.Bar(x=vehicle_make, y=carbon_g, name='Carbon (g)'), row=1, col=1)

    fig.add_trace(go.Bar(x=vehicle_make, y=carbon_kg, name='Carbon (kg)'), row=1, col=2)

    fig.add_trace(go.Bar(x=vehicle_make, y=carbon_mt, name='Carbon (mt)'), row=1, col=3)

     

    # Update layout
    fig.update_layout(title_text='Carbon Emission Plots', showlegend=True, template='plotly_dark')

    # Convert the plot to HTML
    plot_html = fig.to_html(full_html=False)

    return render_template('view_plots.html', plot_html=plot_html)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug =True)
