# app.py
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'todoapp-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for todos
todos = []

# Priority levels
PRIORITY = {
    "high": 3,
    "medium": 2,
    "low": 1
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/todos', methods=['GET'])
def get_todos():
    # Sort todos by priority (high to low)
    sorted_todos = sorted(todos, key=lambda x: x['priority_value'], reverse=True)
    return jsonify(sorted_todos)

@app.route('/todos', methods=['POST'])
def add_todo():
    data = request.json
    priority = data.get('priority', 'medium')
    
    todo = {
        'id': str(uuid.uuid4()),
        'task': data['task'],
        'priority': priority,
        'priority_value': PRIORITY.get(priority, 2),  # Default to medium if invalid
        'completed': False,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    todos.append(todo)
    
    # Notify all clients about the new todo
    socketio.emit('todo_added', todo)
    
    return jsonify(todo), 201

@app.route('/todos/<todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = request.json
    
    for todo in todos:
        if todo['id'] == todo_id:
            if 'completed' in data:
                todo['completed'] = data['completed']
            if 'task' in data:
                todo['task'] = data['task']
            if 'priority' in data:
                todo['priority'] = data['priority']
                todo['priority_value'] = PRIORITY.get(data['priority'], 2)
                
            # Notify all clients about the updated todo
            socketio.emit('todo_updated', todo)
            return jsonify(todo)
    
    return jsonify({'error': 'Todo not found'}), 404

@app.route('/todos/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    for i, todo in enumerate(todos):
        if todo['id'] == todo_id:
            deleted_todo = todos.pop(i)
            
            # Notify all clients about the deleted todo
            socketio.emit('todo_deleted', {'id': todo_id})
            return jsonify(deleted_todo)
    
    return jsonify({'error': 'Todo not found'}), 404

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)