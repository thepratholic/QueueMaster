from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

MAX = 30
queue_array = [None] * MAX
rear = -1
front = -1
total_served = 0
total_wait_time = 0
start_time = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/insert', methods=['POST'])
def queue_insert():
    global rear, front, start_time
    if rear == MAX - 1:
        return jsonify({"message": "Queue Overflow"})
    else:
        if front == -1:
            front = 0
        if start_time is None:
            start_time = datetime.now()
        rear += 1
        queue_array[rear] = request.form['element']
        return jsonify({"message": "Person inserted into the queue"})

@app.route('/delete', methods=['POST'])
def queue_delete():
    global front, rear, total_served, total_wait_time, start_time
    if front == -1 or front > rear:
        return jsonify({"message": "Queue Underflow"})
    else:
        deleted_element = queue_array[front]
        total_served += 1
        current_time = datetime.now()
        total_wait_time += (current_time - start_time).seconds
        front += 1
        if front > rear:
            front = rear = -1
            start_time = None
        return jsonify({"message": f"Deleted: {deleted_element}"})

@app.route('/display')
def display_queue():
    queue = queue_array[front:rear + 1] if front != -1 else []
    return jsonify({"queue": queue})

@app.route('/analytics')
def analytics():
    if total_served == 0:
        avg_wait_time = 0
    else:
        avg_wait_time = total_wait_time / total_served
    return jsonify({
        "total_served": total_served,
        "avg_wait_time": round(avg_wait_time, 2)
    })

if __name__ == '__main__':
    app.run(debug=True)
