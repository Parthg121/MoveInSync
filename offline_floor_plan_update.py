from flask import Flask, request, jsonify
import sqlite3
import time
import threading

app = Flask(__name__)

# Create SQLite database and table
conn = sqlite3.connect('floorplan.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS floorplan (id INTEGER PRIMARY KEY, data TEXT, version INTEGER DEFAULT 1)')
conn.commit()
conn.close()

offline_changes = []

def sync_changes():
    global offline_changes
    while True:
        time.sleep(5)  # Adjust the interval as needed
        if offline_changes:
            try:
                conn = sqlite3.connect('floorplan.db', check_same_thread=False)
                cursor = conn.cursor()
                for change in offline_changes:
                    cursor.execute('UPDATE floorplan SET data = ?, version = version + 1 WHERE id = 1 AND version = ?', (str(change['data']), change['version']))
                    if cursor.rowcount == 0:
                        raise Exception('Conflict during synchronization')
                    conn.commit()
                conn.close()
                offline_changes = []
                print('Offline changes synchronized successfully.')
            except Exception as e:
                print('Error during synchronization:', str(e))

sync_thread = threading.Thread(target=sync_changes)
sync_thread.daemon = True
sync_thread.start()

@app.route('/floorplan', methods=['GET'])
def get_floorplan():
    try:
        conn = sqlite3.connect('floorplan.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM floorplan')
        data = cursor.fetchone()
        conn.close()
        return jsonify({'data': data[1], 'version': data[2]})
    except Exception as e:
        print('Error fetching floor plan:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/floorplan', methods=['POST'])
def update_floorplan():
    new_data = request.json
    try:
        conn = sqlite3.connect('floorplan.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('UPDATE floorplan SET data = ?, version = version + 1 WHERE id = 1 AND version = ?', (str(new_data['data']), new_data['version']))
        if cursor.rowcount == 0:
            raise Exception('Conflict during update')
        conn.commit()
        conn.close()
        return jsonify({'message': 'Floor plan updated successfully'})
    except Exception as e:
        print('Error updating floor plan:', str(e))
        offline_changes.append(new_data)
        return jsonify({'message': 'Changes saved offline. They will be synchronized when online'}), 500

if __name__ == '__main__':
    app.run(debug=True)
