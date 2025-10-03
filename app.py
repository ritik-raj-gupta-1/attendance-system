import os
import psycopg2
from psycopg2.extras import DictCursor
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
from datetime import datetime, timedelta
from geopy.distance import geodesic
import io
import csv

# --- APP CONFIGURATION ---
app = Flask(__name__)
app.secret_key = 'your_very_secret_key_change_this'
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
    return conn

# --- Main Routes ---
@app.route('/')
def index():
    if 'user_type' in session and session['user_type'] == 'student':
        return redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/adminlogin')
def admin_login_page():
    if 'user_type' in session and session['user_type'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect(url_for('admin_login_page'))
    return render_template('admin.html', username=session['username'])

@app.route('/student')
def student_dashboard():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('index'))
    return render_template('student.html', name=session['name'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- API Routes ---
@app.route('/api/student_login', methods=['POST'])
def student_login():
    data = request.json
    identifier, password = data.get('identifier'), data.get('password')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM students WHERE enrollment_number = %s', (identifier,))
        student = cursor.fetchone()
    conn.close()
    
    if student and student['password'] and password == student['password']:
        session['user_id'] = student['id']
        session['enrollment_number'] = student['enrollment_number']
        session['name'] = student['name']
        session['user_type'] = 'student'
        return jsonify({'success': True, 'redirect_url': url_for('student_dashboard')})
    
    return jsonify({'success': False, 'message': 'Invalid credentials, not registered, or device not recognized.'})


@app.route('/api/admin_login', methods=['POST'])
def admin_login():
    data = request.json
    identifier, password = data.get('identifier'), data.get('password')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM admins WHERE username = %s', (identifier,))
        admin = cursor.fetchone()
    conn.close()

    if admin and password == admin['password']:
        session['user_id'] = admin['id']
        session['username'] = admin['username']
        session['user_type'] = 'admin'
        return jsonify({'success': True, 'redirect_url': url_for('admin_dashboard')})
    
    return jsonify({'success': False, 'message': 'Invalid admin credentials.'})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    enrollment_number, password, device_id = data.get('enrollment_number'), data.get('password'), data.get('device_id')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM students WHERE device_id = %s', (device_id,))
        existing_device = cursor.fetchone()
        if existing_device:
            conn.close()
            return jsonify({'success': False, 'message': 'This device is already linked to another account.'})
        
        cursor.execute('SELECT * FROM students WHERE enrollment_number = %s', (enrollment_number,))
        student = cursor.fetchone()
        if student and not student['password']:
            cursor.execute('UPDATE students SET password = %s, device_id = %s WHERE enrollment_number = %s', 
                         (password, device_id, enrollment_number))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Registration successful!'})
            
    conn.close()
    return jsonify({'success': False, 'message': 'Already registered or invalid enrollment number.'})

@app.route('/api/get_active_session')
def get_active_session():
    conn = get_db_connection()
    now = datetime.now()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM attendance_sessions WHERE %s BETWEEN start_time AND end_time ORDER BY start_time DESC LIMIT 1",
            (now,)
        )
        active_session = cursor.fetchone()
    conn.close()
    if active_session:
        return jsonify({'is_active': True, 'end_time': active_session['end_time'].isoformat()})
    else:
        return jsonify({'is_active': False})

# --- ADMIN API ---
@app.route('/api/admin/start_session', methods=['POST'])
def start_session():
    if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = get_db_connection()
    with conn.cursor() as cursor:
        now = datetime.now()
        cursor.execute("SELECT id FROM attendance_sessions WHERE %s BETWEEN start_time AND end_time", (now,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Another session is already in progress.'})

        data = request.json
        lat, lon = data.get('lat'), data.get('lon')
        today, start_time = now.date(), now
        end_time = start_time + timedelta(minutes=5)
        
        cursor.execute(
            'INSERT INTO attendance_sessions (session_date, start_time, end_time, admin_lat, admin_lon) VALUES (%s, %s, %s, %s, %s) RETURNING id',
            (today, start_time, end_time, lat, lon)
        )
        session_id = cursor.fetchone()['id']
        
        cursor.execute('SELECT id FROM students')
        students = cursor.fetchall()
        for student in students:
            cursor.execute('INSERT INTO attendance_records (student_id, session_id, status) VALUES (%s, %s, %s)',
                         (student['id'], session_id, 'Absent'))
        conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Session started for 5 minutes!'})

@app.route('/api/admin/end_session', methods=['POST'])
def end_session():
    if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = get_db_connection()
    with conn.cursor() as cursor:
        now = datetime.now()
        cursor.execute(
            "SELECT id FROM attendance_sessions WHERE %s BETWEEN start_time AND end_time", (now,)
        )
        active_session = cursor.fetchone()

        if active_session:
            cursor.execute("UPDATE attendance_sessions SET end_time = %s WHERE id = %s", (now, active_session['id']))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Session ended successfully.'})
    conn.close()
    return jsonify({'success': False, 'message': 'No active session found to end.'})

@app.route('/api/admin/get_today_attendance')
def get_today_attendance():
    if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM attendance_sessions WHERE session_date = %s ORDER BY start_time DESC LIMIT 1",
            (datetime.now().date(),)
        )
        latest_session = cursor.fetchone()
        
        if not latest_session:
            conn.close()
            return jsonify([])

        cursor.execute('''
            SELECT s.name, s.enrollment_number, ar.status, ar.id as record_id FROM attendance_records ar
            JOIN students s ON ar.student_id = s.id WHERE ar.session_id = %s ORDER BY s.name
        ''', (latest_session['id'],))
        attendance_data = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in attendance_data])

@app.route('/api/admin/update_attendance', methods=['POST'])
def update_attendance():
    if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    data = request.json
    record_id, new_status = data.get('record_id'), data.get('status')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('UPDATE attendance_records SET status = %s WHERE id = %s', (new_status, record_id))
        conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/get_requests')
def get_requests():
    if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT r.id, s.name, s.enrollment_number, r.request_date FROM reregistration_requests r
            JOIN students s ON r.student_id = s.id WHERE r.status = 'Pending'
        ''')
        requests = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in requests])

@app.route('/api/admin/approve_request', methods=['POST'])
def approve_request():
    if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    request_id = request.json.get('request_id')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT student_id FROM reregistration_requests WHERE id = %s', (request_id,))
        req_data = cursor.fetchone()
        if req_data:
            student_id = req_data['student_id']
            cursor.execute('UPDATE students SET device_id = NULL, password = NULL WHERE id = %s', (student_id,))
            cursor.execute('DELETE FROM reregistration_requests WHERE id = %s', (request_id,))
            conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/generate_csv')
def generate_csv():
    if session.get('user_type') != 'admin': return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT COUNT(id) FROM attendance_sessions')
        total_sessions = cursor.fetchone()[0] or 1
        cursor.execute('''
            SELECT s.name, s.enrollment_number, COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) as days_present
            FROM students s LEFT JOIN attendance_records ar ON s.id = ar.student_id GROUP BY s.id ORDER BY s.name
        ''')
        report_data = cursor.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Enrollment Number', 'Days Present', 'Total Sessions', 'Percentage'])
    for row in report_data:
        percentage = (row['days_present'] / total_sessions) * 100
        writer.writerow([row['name'], row['enrollment_number'], row['days_present'], total_sessions, f"{percentage:.2f}%"])
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=attendance_report.csv"})

# --- STUDENT API ---
@app.route('/api/student/get_status')
def get_student_status():
    if session.get('user_type') != 'student': return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT COUNT(id) FROM attendance_sessions')
        total_sessions = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM attendance_records WHERE student_id = %s AND status = %s',
                                    (session['user_id'], 'Present'))
        days_present = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM attendance_sessions WHERE session_date = %s ORDER BY start_time DESC LIMIT 1", (datetime.now().date(),))
        latest_session_today = cursor.fetchone()
        present_list = []
        if latest_session_today:
            cursor.execute('''
                SELECT s.name FROM students s JOIN attendance_records ar ON s.id = ar.student_id
                WHERE ar.session_id = %s AND ar.status = 'Present' ORDER BY s.name
            ''', (latest_session_today['id'],))
            present_students = cursor.fetchall()
            present_list = [row['name'] for row in present_students]
    conn.close()
    return jsonify({'total_sessions': total_sessions, 'days_present': days_present, 'present_list_today': present_list})

@app.route('/api/student/mark_attendance', methods=['POST'])
def mark_attendance():
    if session.get('user_type') != 'student': return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    data = request.json
    student_lat, student_lon, device_id = data.get('lat'), data.get('lon'), data.get('device_id')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('SELECT device_id FROM students WHERE id = %s', (session['user_id'],))
        student_info = cursor.fetchone()
        if not student_info or student_info['device_id'] != device_id:
            conn.close()
            return jsonify({'success': False, 'message': 'This is not your registered device.'})

        now = datetime.now()
        cursor.execute("SELECT * FROM attendance_sessions WHERE %s BETWEEN start_time AND end_time ORDER BY start_time DESC LIMIT 1", (now,))
        active_session = cursor.fetchone()
        if not active_session:
            conn.close()
            return jsonify({'success': False, 'message': 'No active session right now.'})

        distance = geodesic((active_session['admin_lat'], active_session['admin_lon']), (student_lat, student_lon)).meters
        if distance > 50:
            conn.close()
            return jsonify({'success': False, 'message': f'You are {int(distance)} meters away. Must be within 50 meters.'})

        cursor.execute('UPDATE attendance_records SET status = %s WHERE student_id = %s AND session_id = %s',
                     ('Present', session['user_id'], active_session['id']))
        conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Attendance marked successfully!'})

@app.route('/api/student/request_reregistration', methods=['POST'])
def request_reregistration():
    if session.get('user_type') != 'student': return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Use ON CONFLICT DO NOTHING to prevent errors on duplicate requests
        cursor.execute('INSERT INTO reregistration_requests (student_id) VALUES (%s) ON CONFLICT (student_id) DO NOTHING', (session['user_id'],))
        conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Re-registration request sent to admin.'})

if __name__ == '__main__':
    # Use '0.0.0.0' to be accessible on your network. For Render, this isn't strictly necessary but is good practice.
    # The port will be managed by Render automatically.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))