from flask import Flask, request, jsonify, send_file, send_from_directory
from cloudant import Cloudant
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Credentials
USERNAME = os.getenv('CLOUDANT_USERNAME')
API_KEY = os.getenv('CLOUDANT_APIKEY')
URL = os.getenv('CLOUDANT_URL')
DB_NAME = os.getenv('DATABASE_NAME')

# Connect to Cloudant
client = Cloudant.iam(USERNAME, API_KEY, connect=True, url=URL)
client.connect()
db = client.create_database(DB_NAME, throw_on_exists=False)
print("✅ Connected to Cloudant")

# App start
app = Flask(__name__)

# Serve index.html from same folder
@app.route('/')
def index():
    return send_file('index.html')

# Serve style.css from same folder
@app.route('/style.css')
def css():
    return send_from_directory('.', 'style.css')

# Get tasks
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = [doc for doc in db]
    return jsonify(tasks)

# Add task
@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    doc = db.create_document({
        'title': data['title'],
        'completed': False
    })
    return jsonify(doc), 201

# Update task
@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    doc = db[task_id]
    if 'title' in data:
        doc['title'] = data['title']
    if 'completed' in data:
        doc['completed'] = data['completed']
    doc.save()
    return jsonify(doc)

# Delete task
@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    doc = db[task_id]
    doc.delete()
    return '', 204

# Render-specific port setup
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
