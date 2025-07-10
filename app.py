from flask import Flask, request, jsonify, send_file
from cloudant.client import Cloudant
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

# Load Cloudant credentials from .env
USERNAME = os.getenv("CLOUDANT_USERNAME")
API_KEY = os.getenv("CLOUDANT_APIKEY")
URL = os.getenv("CLOUDANT_URL")
DB_NAME = os.getenv("DATABASE_NAME")

# Connect to IBM Cloudant
client = Cloudant.iam(USERNAME, API_KEY, connect=True, url=URL)
db = client[DB_NAME] if DB_NAME in client.all_dbs() else client.create_database(DB_NAME)
print("✅ Connected to Cloudant")

# Serve HTML + CSS directly
@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/style.css')
def serve_css():
    return send_file('style.css')

# GET all tasks
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = []
    for doc in db:
        if doc['_id'].startswith('_design/'):
            continue
        tasks.append({
            "id": doc['_id'],
            "title": doc.get("title", ""),
            "completed": doc.get("completed", False)
        })
    return jsonify(tasks)

# POST new task
@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    task = {
        "title": data.get("title", ""),
        "completed": False
    }
    doc = db.create_document(task)
    return jsonify({"id": doc['_id']}), 201

# PUT (update title or completed)
@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    if task_id in db:
        doc = db[task_id]
        data = request.get_json()
        if 'title' in data:
            doc['title'] = data['title']
        if 'completed' in data:
            doc['completed'] = data['completed']
        doc.save()
        return jsonify({"message": "Task updated"})
    return jsonify({"error": "Task not found"}), 404

# DELETE task
@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    if task_id in db:
        db[task_id].delete()
        return jsonify({"message": "Task deleted"})
    return jsonify({"error": "Task not found"}), 404

# DELETE all completed tasks
@app.route('/tasks/clear-completed', methods=['DELETE'])
def clear_completed():
    for doc in db:
        if doc.get("completed"):
            doc.delete()
    return jsonify({"message": "Completed tasks cleared"})

if __name__ == '__main__':
    app.run(debug=True)
