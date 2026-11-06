import sqlite3
import urllib.parse
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- 1. Database Setup ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- 2. Custom HTTP Request Handler ---
class RegioValHandler(BaseHTTPRequestHandler):

    def read_post_data(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        return urllib.parse.parse_qs(post_data)

    def render_template(self, filename, status_code=200, error_msg="", success_msg=""):
        try:
            with open(f'templates/{filename}', 'r', encoding='utf-8') as file:
                content = file.read()

            # Generate elemen HTML Alert jika ada pesan
            alert_html = ""
            if error_msg:
                alert_html = f'<div class="alert alert-error">{error_msg}</div>'
            elif success_msg:
                alert_html = f'<div class="alert alert-success">{success_msg}</div>'

            # Ganti placeholder {{MESSAGE}} di template
            content = content.replace('{{MESSAGE}}', alert_html)

            self.send_response(status_code)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, "Template Not Found")

    def do_GET(self):
        if self.path == '/' or self.path == '/index':
            self.render_template('index.html')
        elif self.path == '/login':
            self.render_template('login.html')
        elif self.path == '/register':
            self.render_template('register.html')
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        params = self.read_post_data()
        username = params.get('username', [''])[0].strip()
        password = params.get('password', [''])[0].strip()

        if self.path == '/register':
            if not username or not password:
                self.render_template('register.html', status_code=400, error_msg="Username dan password wajib diisi!")
                return

            hashed_pwd = hash_password(password)
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pwd))
                conn.commit()
                conn.close()
                
                # Tampilkan halaman login dengan pesan sukses register
                self.render_template('login.html', success_msg="Registrasi berhasil! Silakan masuk.")
            except sqlite3.IntegrityError:
                self.render_template('register.html', status_code=400, error_msg="Username sudah terdaftar. Gunakan username lain!")

        elif self.path == '/login':
            if not username or not password:
                self.render_template('login.html', status_code=400, error_msg="Username dan password wajib diisi!")
                return

            hashed_pwd = hash_password(password)
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_pwd))
            user = cursor.fetchone()
            conn.close()

            if user:
                # Login Berhasil -> Redirect ke Dashboard Utama
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                # Login Gagal -> Render ulang login.html dengan alert error merah
                self.render_template('login.html', status_code=401, error_msg="Username atau password yang Anda masukkan salah!")

# --- 3. Run Server ---
if __name__ == '__main__':
    init_db()
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, RegioValHandler)
    print("Server RegioVal berjalan di http://localhost:8000")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        httpd.server_close()