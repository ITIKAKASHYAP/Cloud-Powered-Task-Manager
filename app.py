from flask import Flask, request, jsonify, send_file
from cloudant import Cloudant
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# IBM Cloudant credentials
USERNAME = os.getenv('CLOUDANT_USERNAME')
API_KEY = os.getenv('CLOUDANT_APIKEY')
URL = os.getenv('CLOUDANT_URL')
DB_NAME = os.getenv('DATABASE_NAME')

# Connect to Cloudant
client = Cloudant.iam(USERNAME, API_KEY, connect=True, url=URL)
client.connect()
db = client.create_database(DB_NAME, throw_on_exists=False)
print("✅ Connected to Cloudant")

# Flask app
app = Flask(__name__)

# Serve index.html directly
@app.route('/')
def index():
    return send_file('index.html')

# Get all tasks
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = [doc for doc in db]
    return jsonify(tasks)

# Add a new task
@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    new_task = {
        'title': data['title'],
        'completed': False
    }
    doc = db.create_document(new_task)
    return jsonify(doc), 201

# Update task (title or completed)
@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    doc = db[task_id]
    data = request.get_json()
    if 'title' in data:
        doc['title'] = data['title']
    if 'completed' in data:
        doc['completed'] = data['completed']
    doc.save()
    return jsonify(doc)

# Delete a task
@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    doc = db[task_id]
    doc.delete()
    return '', 204

# FINAL DEPLOY FIX: Required by Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
