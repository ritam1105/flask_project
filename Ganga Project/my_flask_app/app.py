from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey123'  # Replace with a strong secret key in production

# Initialize Firebase
try:
    cred = credentials.Certificate("path_to_your_firebase_credentials.json")  # Update this path
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://gangariver-3965a-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })
    firebase_ref = db.reference('sensor_data')
except Exception as e:
    print(f"Firebase initialization failed: {str(e)}")

# Mock user data (replace with a proper database in production)
users = {
    "admin": "password123",
    "user": "user123"
}

def get_sensor_data(limit=10):
    """Helper function to fetch sensor data from Firebase"""
    try:
        sensor_data = firebase_ref.order_by_key().limit_to_last(limit).get()
        if sensor_data:
            formatted_data = [
                {
                    'id': key,
                    'timestamp': value.get('timestamp', ''),
                    'temperature': value.get('temperature', 0),
                    'turbidity': value.get('turbidity', 0),
                    'ph': value.get('ph', 0),
                    'water_level': value.get('water_level', 0),
                    'dissolved_oxygen': value.get('dissolved_oxygen', 0)  # Added new parameter
                }
                for key, value in sensor_data.items()
            ]
            # Sort by timestamp (newest first)
            formatted_data.sort(key=lambda x: x['timestamp'], reverse=True)
            return formatted_data
        return []
    except Exception as e:
        print(f"Error fetching sensor data: {str(e)}")
        return []

def get_graph_data(parameter, limit=20):
    """Helper function to fetch data for graphs"""
    try:
        sensor_data = firebase_ref.order_by_key().limit_to_last(limit).get()
        if sensor_data:
            graph_data = [
                {
                    'timestamp': value.get('timestamp', ''),
                    'value': value.get(parameter, 0)
                }
                for value in sensor_data.values()
            ]
            graph_data.sort(key=lambda x: x['timestamp'])
            return graph_data
        return []
    except Exception as e:
        print(f"Error in {parameter}_graph: {str(e)}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))
    
    sensor_data = get_sensor_data(10)
    
    # Calculate averages for dashboard cards
    if sensor_data:
        avg_temp = sum(d['temperature'] for d in sensor_data) / len(sensor_data)
        avg_turbidity = sum(d['turbidity'] for d in sensor_data) / len(sensor_data)
        avg_ph = sum(d['ph'] for d in sensor_data) / len(sensor_data)
        avg_water_level = sum(d['water_level'] for d in sensor_data) / len(sensor_data)
    else:
        avg_temp = avg_turbidity = avg_ph = avg_water_level = 0
    
    return render_template('dashboard.html', 
                         sensor_data=sensor_data,
                         avg_temp=round(avg_temp, 2),
                         avg_turbidity=round(avg_turbidity, 2),
                         avg_ph=round(avg_ph, 2),
                         avg_water_level=round(avg_water_level, 2))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        sensor_data = request.json
        firebase_ref.push({
            'temperature': sensor_data.get('temperature', 0),
            'turbidity': sensor_data.get('turbidity', 0),
            'ph': sensor_data.get('ph', 0),
            'water_level': sensor_data.get('water_level', 0),
            'dissolved_oxygen': sensor_data.get('dissolved_oxygen', 0),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        return jsonify({"message": "Data added successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_data', methods=['GET'])
def get_data():
    limit = request.args.get('limit', default=10, type=int)
    sensor_data = get_sensor_data(limit)
    return jsonify(sensor_data)

@app.route('/delete_data/<id>', methods=['DELETE'])
def delete_data(id):
    try:
        firebase_ref.child(id).delete()
        return jsonify({"message": "Data deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Graph routes
@app.route('/temperature_graph')
def temperature_graph():
    limit = request.args.get('limit', default=20, type=int)
    graph_data = get_graph_data('temperature', limit)
    return render_template('temperature_graph.html', 
                         graph_data=json.dumps(graph_data),
                         parameter='Temperature',
                         unit='°C')

@app.route('/turbidity_graph')
def turbidity_graph():
    limit = request.args.get('limit', default=20, type=int)
    graph_data = get_graph_data('turbidity', limit)
    return render_template('turbidity_graph.html', 
                         graph_data=json.dumps(graph_data),
                         parameter='Turbidity',
                         unit='NTU')

@app.route('/ph_graph')
def ph_graph():
    limit = request.args.get('limit', default=20, type=int)
    graph_data = get_graph_data('ph', limit)
    return render_template('ph_graph.html', 
                         graph_data=json.dumps(graph_data),
                         parameter='pH',
                         unit='')

@app.route('/water_level_graph')
def water_level_graph():
    limit = request.args.get('limit', default=20, type=int)
    graph_data = get_graph_data('water_level', limit)
    return render_template('water_level_graph.html', 
                         graph_data=json.dumps(graph_data),
                         parameter='Water Level',
                         unit='cm')

@app.route('/dissolved_oxygen_graph')
def dissolved_oxygen_graph():
    limit = request.args.get('limit', default=20, type=int)
    graph_data = get_graph_data('dissolved_oxygen', limit)
    return render_template('dissolved_oxygen_graph.html', 
                         graph_data=json.dumps(graph_data),
                         parameter='Dissolved Oxygen',
                         unit='mg/L')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)