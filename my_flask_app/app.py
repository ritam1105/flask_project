from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
import random
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

# Initialize Firebase
try:
    cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://your-project.firebasedatabase.app/'
    })
    firebase_ref = db.reference('sensor_data')
    use_firebase = True
except Exception as e:
    print(f"Firebase initialization failed: {str(e)}")
    use_firebase = False

# Sensor data ranges
sensor_ranges = {
    'temperature': (15, 35),
    'turbidity': (0, 100),
    'ph': (6.0, 8.5),
    'water_level': (0, 10)
}

# Counter for sequential IDs
current_id = 1

def generate_mock_data(count=10):
    global current_id
    mock_data = []
    base_time = datetime.now() - timedelta(hours=2)  # Generate data for last 2 hours
    
    for i in range(count):
        timestamp = (base_time + timedelta(minutes=i*10)).strftime('%Y-%m-%d %H:%M:%S')  # 10 minute intervals
        mock_data.append({
            'id': current_id,  # Use sequential ID
            'timestamp': timestamp,
            'temperature': round(random.uniform(*sensor_ranges['temperature']), 1),
            'turbidity': round(random.uniform(*sensor_ranges['turbidity']), 1),
            'ph': round(random.uniform(*sensor_ranges['ph']), 1),
            'water_level': round(random.uniform(*sensor_ranges['water_level']), 1)
        })
        current_id += 1  # Increment ID for next record
    return mock_data

mock_sensor_data = generate_mock_data(12)  # 12 data points = 2 hours of data

@app.route('/')
def index():
    return render_template('index.html')

# Define a dictionary of users with username-password pairs
users = {
    'admin': 'password123',
    'user1': 'mypassword',
    'user2': 'securepass'
}

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


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))
    
    try:
        if use_firebase:
            sensor_data = firebase_ref.order_by_child('timestamp').limit_to_last(12).get()
            if sensor_data:
                latest_data = []
                # Convert Firebase keys to sequential IDs
                for idx, (key, value) in enumerate(sensor_data.items(), start=1):
                    latest_data.append({
                        'id': idx,  # Use sequential number as ID
                        'timestamp': value.get('timestamp', ''),
                        'temperature': value.get('temperature', 0),
                        'turbidity': value.get('turbidity', 0),
                        'ph': value.get('ph', 0),
                        'water_level': value.get('water_level', 0)
                    })
                # Sort by timestamp (newest first)
                latest_data.sort(key=lambda x: x['timestamp'], reverse=True)
            else:
                latest_data = sorted(mock_sensor_data, key=lambda x: x['timestamp'], reverse=True)[:12]
        else:
            latest_data = sorted(mock_sensor_data, key=lambda x: x['timestamp'], reverse=True)[:12]
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        latest_data = sorted(mock_sensor_data, key=lambda x: x['timestamp'], reverse=True)[:12]
    
    return render_template('dashboard.html', sensor_data=latest_data)

@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        if use_firebase:
            sensor_data = firebase_ref.order_by_child('timestamp').limit_to_last(12).get()
            if sensor_data:
                formatted_data = []
                # Convert Firebase keys to sequential IDs
                for idx, (key, value) in enumerate(sensor_data.items(), start=1):
                    formatted_data.append({
                        'id': idx,  # Use sequential number as ID
                        'timestamp': value.get('timestamp', ''),
                        'temperature': value.get('temperature', 0),
                        'turbidity': value.get('turbidity', 0),
                        'ph': value.get('ph', 0),
                        'water_level': value.get('water_level', 0)
                    })
                # Sort by timestamp (newest first)
                formatted_data.sort(key=lambda x: x['timestamp'], reverse=True)
                return jsonify(formatted_data)
        
        # Fallback to mock data (sorted newest first)
        sorted_data = sorted(mock_sensor_data, key=lambda x: x['timestamp'], reverse=True)[:12]
        return jsonify(sorted_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Graph routes
@app.route('/temperature_graph')
def temperature_graph():
    return render_template('temperature_graph.html')

@app.route('/turbidity_graph')
def turbidity_graph():
    return render_template('turbidity_graph.html')

@app.route('/ph_graph')
def ph_graph():
    return render_template('ph_graph.html')

@app.route('/water_level_graph')
def water_level_graph():
    return render_template('water_level_graph.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)