import sqlite3
import urllib.parse
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import pricing_engine  # Impor modul kalkulasi baru

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

class RegioValHandler(BaseHTTPRequestHandler):

    def read_post_data(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        return urllib.parse.parse_qs(post_data)

    def render_template(self, filename, status_code=200, error_msg="", success_msg="", username="Developer", result_html=""):
        try:
            with open(f'templates/{filename}', 'r', encoding='utf-8') as file:
                content = file.read()

            alert_html = ""
            if error_msg:
                alert_html = f'<div class="alert alert-error">{error_msg}</div>'
            elif success_msg:
                alert_html = f'<div class="alert alert-success">{success_msg}</div>'

            content = content.replace('{{MESSAGE}}', alert_html)
            content = content.replace('{{USERNAME}}', username)
            content = content.replace('{{RESULT_SECTION}}', result_html)

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

        if self.path == '/calculate':
            try:
                base_price = float(params.get('base_price', [0])[0])
                currency = params.get('currency', ['IDR'])[0]

                res = pricing_engine.calculate_regional_price(base_price, currency)
                
                if res:
                    result_html = f'''
                    <div class="result-box">
                        <div class="result-row">
                            <span>Harga Konversi Mentah ({res['currency']}):</span>
                            <span>{res['symbol']} {res['raw_converted']:,}</span>
                        </div>
                        <div class="result-row">
                            <span>Penyesuaian Daya Beli (PPP):</span>
                            <span>-{res['discount_vs_raw_percent']}%</span>
                        </div>
                        <div class="result-row highlight">
                            <span>Rekomendasi Harga RegioVal:</span>
                            <span>{res['symbol']} {res['recommended_price']:,}</span>
                        </div>
                    </div>
                    '''
                else:
                    result_html = '<div class="alert alert-error">Mata uang tidak ditemukan.</div>'
                
                self.render_template('index.html', result_html=result_html)
            except ValueError:
                self.render_template('index.html', error_msg="Input harga tidak valid.")

        elif self.path == '/register':
            username = params.get('username', [''])[0].strip()
            password = params.get('password', [''])[0].strip()
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
                self.render_template('login.html', success_msg="Registrasi berhasil! Silakan masuk.")
            except sqlite3.IntegrityError:
                self.render_template('register.html', status_code=400, error_msg="Username sudah terdaftar. Gunakan username lain!")

        elif self.path == '/login':
            username = params.get('username', [''])[0].strip()
            password = params.get('password', [''])[0].strip()
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
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.render_template('login.html', status_code=401, error_msg="Username atau password yang Anda masukkan salah!")

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