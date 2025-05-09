from flask import Flask, request, render_template, redirect, send_file
import os
import sqlite3

app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Setup DB (only once) ---
if not os.path.exists('users.db'):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT);")
    c.execute("INSERT INTO users (username, password) VALUES ('admin', 'supersecret')")
    conn.commit()
    conn.close()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # VULN 1: SQL Injection
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        c.execute(query)
        user = c.fetchone()
        conn.close()

        if user:
            return redirect('/upload')
        else:
            return "Invalid credentials"

    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename

        # VULN 2: Extension Bypass (e.g. .php.jpg)
        if filename.endswith('.jpg'):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            return f"Uploaded to {filepath}"
        else:
            return "Only .jpg allowed"

    return render_template('upload.html')

@app.route('/view')
def view():
    img = request.args.get('img', '')

    # VULN 3: Path Traversal / LFI
    filepath = os.path.join(UPLOAD_FOLDER, img)
    return send_file(filepath, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
