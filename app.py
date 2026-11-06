import sqlite3
import urllib.parse
import hashlib
import uuid
import datetime
from http.cookies import SimpleCookie
from http.server import HTTPServer, BaseHTTPRequestHandler
import pricing_engine

SESSIONS = {}

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Tabel Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Tabel Histori Kalkulasi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            base_price REAL NOT NULL,
            target_currency TEXT NOT NULL,
            recommended_price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_history(username, base_price, target_currency, recommended_price):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO calculation_history (username, base_price, target_currency, recommended_price)
        VALUES (?, ?, ?, ?)
    ''', (username, base_price, target_currency, recommended_price))
    conn.commit()
    conn.close()

def get_user_history(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT base_price, target_currency, recommended_price, created_at 
        FROM calculation_history 
        WHERE username = ? 
        ORDER BY id DESC LIMIT 5
    ''', (username,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class RegioValHandler(BaseHTTPRequestHandler):

    def get_session_user(self):
        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            cookie = SimpleCookie(cookie_header)
            if 'session_id' in cookie:
                session_id = cookie['session_id'].value
                return SESSIONS.get(session_id)
        return None

    def read_post_data(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        return urllib.parse.parse_qs(post_data)

    def render_template(self, filename, status_code=200, error_msg="", success_msg="", username="Guest", result_html="", history_html=""):
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
            content = content.replace('{{HISTORY_SECTION}}', history_html)

            self.send_response(status_code)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, "Template Not Found")

    def build_history_html(self, username):
        history = get_user_history(username)
        if not history:
            return '<p style="color:#64748b; font-size:14px;">Belum ada riwayat kalkulasi.</p>'
        
        rows = ""
        for item in history:
            rows += f'''
            <tr>
                <td>${item[0]}</td>
                <td>{item[1]}</td>
                <td>{item[2]:,}</td>
                <td>{item[3]}</td>
            </tr>
            '''
        return f'''
        <table>
            <thead>
                <tr>
                    <th>Base Price</th>
                    <th>Target</th>
                    <th>Hasil Rekomendasi</th>
                    <th>Waktu</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        '''

    def do_GET(self):
        current_user = self.get_session_user()

        if self.path == '/' or self.path == '/index':
            if not current_user:
                self.send_response(303)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            
            history_html = self.build_history_html(current_user)
            self.render_template('index.html', username=current_user, history_html=history_html)

        elif self.path == '/logout':
            cookie_header = self.headers.get('Cookie')
            if cookie_header:
                cookie = SimpleCookie(cookie_header)
                if 'session_id' in cookie:
                    session_id = cookie['session_id'].value
                    SESSIONS.pop(session_id, None)

            self.send_response(303)
            self.send_header('Set-Cookie', 'session_id=; expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/')
            self.send_header('Location', '/login')
            self.end_headers()

        elif self.path == '/login':
            if current_user:
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
                return
            self.render_template('login.html')

        elif self.path == '/register':
            self.render_template('register.html')
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        params = self.read_post_data()
        current_user = self.get_session_user()

        if self.path == '/calculate':
            if not current_user:
                self.send_response(303)
                self.send_header('Location', '/login')
                self.end_headers()
                return

            try:
                base_price = float(params.get('base_price', [0])[0])
                currency = params.get('currency', ['ALL'])[0]

                if currency == 'ALL':
                    results = pricing_engine.calculate_all_regional_prices(base_price)
                    rows = ""
                    for res in results:
                        save_history(current_user, base_price, res['currency'], res['recommended_price'])
                        rows += f'''
                        <tr>
                            <td><strong>{res['country_name']}</strong> ({res['currency']})</td>
                            <td>{res['symbol']} {res['raw_converted']:,}</td>
                            <td><span class="badge">-{res['discount_vs_raw_percent']}%</span></td>
                            <td><strong>{res['symbol']} {res['recommended_price']:,}</strong></td>
                        </tr>
                        '''
                    result_html = f'''
                    <div class="result-box">
                        <h3 style="color:#38bdf8; margin-bottom:12px;">Hasil Live API Perbandingan (Base: ${base_price})</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Negara / Mata Uang</th>
                                    <th>Konversi Mentah</th>
                                    <th>Diskon PPP</th>
                                    <th>Rekomendasi RegioVal</th>
                                </tr>
                            </thead>
                            <tbody>{rows}</tbody>
                        </table>
                    </div>
                    '''
                else:
                    res = pricing_engine.calculate_regional_price(base_price, currency)
                    save_history(current_user, base_price, res['currency'], res['recommended_price'])
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

                history_html = self.build_history_html(current_user)
                self.render_template('index.html', username=current_user, result_html=result_html, history_html=history_html)
            except ValueError:
                history_html = self.build_history_html(current_user)
                self.render_template('index.html', username=current_user, error_msg="Input harga tidak valid.", history_html=history_html)

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
                self.render_template('register.html', status_code=400, error_msg="Username sudah terdaftar!")

        elif self.path == '/login':
            username = params.get('username', [''])[0].strip()
            password = params.get('password', [''])[0].strip()

            hashed_pwd = hash_password(password)
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_pwd))
            user = cursor.fetchone()
            conn.close()

            if user:
                session_id = str(uuid.uuid4())
                SESSIONS[session_id] = username

                self.send_response(303)
                self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly')
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.render_template('login.html', status_code=401, error_msg="Username atau password salah!")

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