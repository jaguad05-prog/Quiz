import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

DIR = os.path.dirname(os.path.abspath(__file__))
F_ESTADO = os.path.join(DIR, 'estado.json')
F_RESP = os.path.join(DIR, 'respuestas.json')
F_PREGUNTAS = os.path.join(DIR, 'preguntas.json')

def init_files():
    if not os.path.exists(F_ESTADO):
        write_json(F_ESTADO, {"fase":"espera","qIdx":0,"pregunta":None,"puntuaciones":{},"equipos":[]})
    if not os.path.exists(F_RESP):
        write_json(F_RESP, {})
    if not os.path.exists(F_PREGUNTAS):
        write_json(F_PREGUNTAS, [])

def read_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def read_raw(path, default='{}'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return default

def write_raw(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_response_data(self, text, content_type='application/json', code=200):
        encoded = text.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(encoded))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(encoded)

    def read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(length).decode('utf-8') if length else ''

    def do_OPTIONS(self):
        self.send_response_data('')

    def do_GET(self):
        path = urlparse(self.path).path

        if path in ('/', '/index.html'):
            html_path = os.path.join(DIR, 'quiz.html')
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()
            self.send_response_data(html, 'text/html; charset=utf-8')
            return

        if path == '/api/info':
            self.send_response_data(json.dumps({"ip": ""}))
            return

        if path == '/api/estado':
            self.send_response_data(read_raw(F_ESTADO, '{}'))
            return

        if path == '/api/respuestas':
            self.send_response_data(read_raw(F_RESP, '{}'))
            return

        if path == '/api/preguntas':
            self.send_response_data(read_raw(F_PREGUNTAS, '[]'))
            return

        self.send_response_data('{"error":"not found"}', code=404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self.read_body()

        if path == '/api/estado':
            try:
                obj = json.loads(body)
                if obj.get('fase') == 'pregunta':
                    write_raw(F_RESP, '{}')
            except:
                pass
            write_raw(F_ESTADO, body)
            self.send_response_data('{"ok":true}')
            return

        if path == '/api/respuesta':
            try:
                nueva = json.loads(body)
                actuales = read_json(F_RESP, {})
                actuales[nueva['equipo']] = {'opcion': nueva['opcion'], 'tiempo': nueva['tiempo']}
                write_json(F_RESP, actuales)
            except:
                pass
            self.send_response_data('{"ok":true}')
            return

        if path == '/api/equipo':
            try:
                data = json.loads(body)
                est = read_json(F_ESTADO, {})
                if 'equipos' not in est or est['equipos'] is None:
                    est['equipos'] = []
                if data['equipo'] not in est['equipos']:
                    est['equipos'].append(data['equipo'])
                    write_json(F_ESTADO, est)
            except:
                pass
            self.send_response_data('{"ok":true}')
            return

        if path == '/api/preguntas':
            write_raw(F_PREGUNTAS, body)
            self.send_response_data('{"ok":true}')
            return

        self.send_response_data('{"error":"not found"}', code=404)

if __name__ == '__main__':
    init_files()
    port = int(os.environ.get('PORT', 3000))
    print(f'Servidor activo en puerto {port}')
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()
