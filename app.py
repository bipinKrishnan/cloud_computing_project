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

# Route for retrieve landing, to enter what to retrieve
@app.route('/fetch_landing', methods=['GET'])
def fetch_land():
    return render_template("fetch_landing.html")

# Route for the result page, used by fetch_landing and the home page
@app.route('/result', methods=['POST'])
def result():

    result = db.collection('results').document(request.form["user_name"]).get()
    if result.exists:
        result = result.to_dict()
    else:
        # Data not found, add a message
        result = ""
    return render_template('result.html', result=result, user_name=request.form["user_name"]), 200 if result else 404

# Route for delete landing, to enter what to delete
@app.route('/del_landing', methods=['GET'])
def del_land():
    return render_template("delete_landing.html")

# Route to delete a record
@app.route('/delete', methods=['POST'])
def delete_emission():
    fetch = db.collection('results').document(request.form["user_name"]).get()
    db.collection('results').document(request.form["user_name"]).delete()

    return render_template('delete.html', user_name=request.form["user_name"], removed=fetch.exists ), 200 if fetch.exists else 404


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
    vehicle_model = [entry.get('vehicle_model', 'Unknown') for entry in data]
    carbon_g = [entry.get('carbon_g', 0) for entry in data]

    bar_fig = make_subplots(rows=2, cols=3, subplot_titles=['Carbon (kg)', 'Carbon (metric tons)', 'Carbon (grams)'],specs=[
    [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
    [{"type": "pie"}, {"type": "pie"}, {"type": "pie"}]
])

    make_fig = make_subplots(rows=2, cols=3, subplot_titles=['Carbon (kg)', 'Carbon (metric tons)', 'Carbon (grams)'],specs=[
    [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
    [{"type": "pie"}, {"type": "pie"}, {"type": "pie"}]
])
    # Extract data for plotting
    carbon_kg = [entry.get('carbon_kg', 0) for entry in data]
    carbon_mt = [entry.get('carbon_mt', 0) for entry in data]
    carbon_g = [entry.get('carbon_g', 0) for entry in data]
    vehicle_model = [entry.get('vehicle_model', 'Unknown') for entry in data]
    vehicle_make = [entry.get('vehicle_make', 'Unknown') for entry in data]

    # Add traces for bar chart
    bar_fig.add_trace(go.Bar(x=vehicle_model, y=carbon_g, name='Carbon (g)'), row=1, col=1)
    bar_fig.add_trace(go.Bar(x=vehicle_model, y=carbon_kg, name='Carbon (kg)'), row=1, col=2)
    bar_fig.add_trace(go.Bar(x=vehicle_model, y=carbon_mt, name='Carbon (mt)'), row=1, col=3)

    make_fig.add_trace(go.Bar(x=vehicle_make, y=carbon_g, name='Carbon (g)'), row=1, col=1)
    make_fig.add_trace(go.Bar(x=vehicle_make, y=carbon_kg, name='Carbon (kg)'), row=1, col=2)
    make_fig.add_trace(go.Bar(x=vehicle_make, y=carbon_mt, name='Carbon (mt)'), row=1, col=3)

    vehicle_model_labels = list(set(vehicle_model))
    vehicle_model_values_kg = [sum(carbon_kg[i] for i, model in enumerate(vehicle_model) if model == label) for label in vehicle_model_labels]
    vehicle_model_values_g = [sum(carbon_g[i] for i, model in enumerate(vehicle_model) if model == label) for label in vehicle_model_labels]
    vehicle_model_values_mt = [sum(carbon_mt[i] for i, model in enumerate(vehicle_model) if model == label) for label in vehicle_model_labels]

    bar_fig.add_trace(go.Pie(labels=vehicle_model_labels, values=vehicle_model_values_g, name='Carbon by Vehicle Model'),row=2,col=1)
    bar_fig.add_trace(go.Pie(labels=vehicle_model_labels, values=vehicle_model_values_kg, name='Carbon by Vehicle Model'),row=2,col=2)
    bar_fig.add_trace(go.Pie(labels=vehicle_model_labels, values=vehicle_model_values_mt, name='Carbon by Vehicle Model'),row=2,col=3)

    vehicle_make_labels = list(set(vehicle_make))
    vehicle_make_values_kg = [sum(carbon_kg[i] for i, make in enumerate(vehicle_make) if make == label) for label in vehicle_make_labels]
    vehicle_make_values_g = [sum(carbon_g[i] for i, make in enumerate(vehicle_make) if make == label) for label in vehicle_make_labels]
    vehicle_make_values_mt = [sum(carbon_mt[i] for i, make in enumerate(vehicle_make) if make == label) for label in vehicle_make_labels]
    
    make_fig.add_trace(go.Pie(labels=vehicle_make_labels, values=vehicle_make_values_g, name='Carbon by Vehicle Make'),row=2,col=1)
    make_fig.add_trace(go.Pie(labels=vehicle_make_labels, values=vehicle_make_values_kg, name='Carbon by Vehicle Make'),row=2,col=2)
    make_fig.add_trace(go.Pie(labels=vehicle_make_labels, values=vehicle_make_values_mt, name='Carbon by Vehicle Make'),row=2,col=3)


    bar_fig.update_layout(
        title_text='Carbon Emission [g kg mt] (vs.) Vehicle Model - Plots ',
        showlegend=True,
        template='plotly_dark',
        height=450,
        width=890,
    )


    make_fig.update_layout(
        title_text='Carbon Emission [g kg mt] (vs.) Vehicle Make - Plots ',
        showlegend=True,
        template='plotly_dark',
        height=274,
        width=890,
    
    )

    
    bar_html = bar_fig.to_html(full_html=False),
    make_html = make_fig.to_html(full_html=False)

    return render_template('view_plots.html', bar_html=bar_html, make_html=make_html)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug =True)
