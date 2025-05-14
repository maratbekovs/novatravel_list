from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('tours.db')
    conn.row_factory = sqlite3.Row
    return conn

# Инициализация БД
with app.app_context():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS tours
                    (tour_id INTEGER PRIMARY KEY, 
                     tour_name TEXT, 
                     tour_date TEXT,
                     max_tourists INT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS tourists
                    (tourist_id INTEGER PRIMARY KEY,
                     tour_id INTEGER,
                     full_name TEXT,
                     contacts TEXT,
                     documents TEXT,
                     balance TEXT,
                     is_guide BOOLEAN DEFAULT 0)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tours', methods=['GET'])
def get_tours():
    conn = get_db_connection()
    tours = conn.execute('SELECT * FROM tours').fetchall()
    conn.close()
    return jsonify([dict(tour) for tour in tours])

@app.route('/tours', methods=['POST'])
def create_tour():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tours (tour_name, tour_date, max_tourists) VALUES (?, ?, ?)',
                   (data['name'], data['date'], data['max_tourists']))
    tour_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'tour_id': tour_id}), 201

@app.route('/tourists/<int:tour_id>', methods=['GET', 'POST'])
def manage_tourists(tour_id):
    if request.method == 'POST':
        data = request.json
        conn = get_db_connection()
        try:
            
            # Удаляем старые данные
            conn.execute('DELETE FROM tourists WHERE tour_id = ?', (tour_id,))
            
            # Сохраняем туристов
            for tourist in data['tourists']:
                conn.execute('''INSERT INTO tourists 
                                (tour_id, full_name, contacts, documents, balance, is_guide)
                                VALUES (?, ?, ?, ?, ?, 0)''',
                             (tour_id, 
                              tourist.get('full_name'),
                              tourist.get('contacts'),
                              tourist.get('documents'),
                              tourist.get('balance')))
                
                
            
            # Сохраняем гида
            if data['guide']:
                conn.execute('''INSERT INTO tourists 
                                (tour_id, full_name, contacts, is_guide)
                                VALUES (?, ?, ?, 1)''',
                             (tour_id, 
                              data['guide']['full_name'],
                              data['guide']['contacts']))
            
            conn.commit()
            return jsonify({'status': 'success'}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()
    else:
        conn = get_db_connection()
        tourists = conn.execute('SELECT * FROM tourists WHERE tour_id = ? AND is_guide = 0', (tour_id,)).fetchall()
        guide = conn.execute('SELECT * FROM tourists WHERE tour_id = ? AND is_guide = 1', (tour_id,)).fetchone()
        conn.close()
        return jsonify({
            'tourists': [dict(t) for t in tourists],
            'guide': dict(guide) if guide else None
        })

@app.route('/tours/<int:tour_id>', methods=['DELETE'])
def delete_tour(tour_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM tourists WHERE tour_id = ?', (tour_id,))
        conn.execute('DELETE FROM tours WHERE tour_id = ?', (tour_id,))
        conn.commit()
        return jsonify({'status': 'deleted'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

        
@app.route('/tours/<int:tour_id>', methods=['GET'])
def get_tour(tour_id):
    conn = get_db_connection()
    tour = conn.execute('SELECT * FROM tours WHERE tour_id = ?', (tour_id,)).fetchone()
    conn.close()
    return jsonify(dict(tour)) if tour else ('Тур не найден', 404)

if __name__ == '__main__':
    app.run(debug=True)