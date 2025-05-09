from flask import Flask, request, render_template, redirect, send_file, abort, Response
import os
import sqlite3
import mimetypes

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
            return render_template('login.html', error="Invalid credentials")

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
            return render_template('upload.html', success=f"Uploaded to {filepath}")
        else:
            return render_template('upload.html', error="Only .jpg allowed")

    # List uploaded images
    images = os.listdir(UPLOAD_FOLDER)
    return render_template('upload.html', images=images)

@app.route('/view')
def view():
    img = request.args.get('img', '')

    # VULN 3: Path Traversal / LFI
    if img.startswith('../../') or '..' in img:
        try:
            base_dir = os.path.abspath(os.path.dirname(__file__))
            full_path = os.path.normpath(os.path.join(base_dir, img))
            with open(full_path, 'r') as f:
                content = f.read()
            return Response(content, mimetype='text/plain')
        except Exception:
            return abort(404)

    # Normal image handling
    try:
        path = os.path.join(UPLOAD_FOLDER, img)
        mime = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        return send_file(path, mimetype=mime)
    except FileNotFoundError:
        return abort(404)

# --- RCE Trigger Route ---
@app.route('/trigger')
def trigger():
    f = request.args.get('f')
    filepath = os.path.join(UPLOAD_FOLDER, f)
    try:
        os.system(f'python3 {filepath}')
        return "Executed"
    except:
        return "Execution failed"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
